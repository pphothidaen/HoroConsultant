#!/usr/bin/env python3
"""Claude PreToolUse guard for an explicitly marked orchestrator session.

Claude cannot identify a root session by itself. The launcher must set
HORO_ORCHESTRATOR_ONLY=1. A protected tool call then needs a waiver identifier
that is recorded in both active governance documents.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

from adaptive_dispatch_guard import (
    enforce_adaptive_dispatch,
    is_safe_monitoring_command,
    is_standalone_dispatcher_dry_run,
)


ROOT_DIR = Path(__file__).resolve().parents[2]
WAIVER_ID = re.compile(r"^ROOT-WAIVER-[A-Za-z0-9][A-Za-z0-9_-]{2,80}$")
GOVERNANCE_PREFIXES = (
    "PROJECT_TASKS.md",
    "plans/",
    ".agents/rules/",
    ".agents/skills/",
    ".agents/AGENTS.md",
    ".antigravity/skills/",
    ".claude/rules/",
    ".claude/hooks/",
    ".claude/settings.json",
)


def deny(reason: str) -> None:
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": f"[BLOCKED] orchestrator-only: {reason}"}}, ensure_ascii=True))
    raise SystemExit(0)


def iter_paths(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [path for item in value for path in iter_paths(item)]
    if isinstance(value, dict):
        return [path for key in ("file_path", "path", "notebook_path") if key in value for path in iter_paths(value[key])]
    return []


def has_recorded_waiver() -> bool:
    waiver_id = os.getenv("HORO_ROOT_WAIVER_ID", "")
    if not WAIVER_ID.fullmatch(waiver_id):
        return False
    marker = f"ROOT-WAIVER: {waiver_id}"
    for relative in ("PROJECT_TASKS.md", "plans/plan.md"):
        try:
            if marker not in (ROOT_DIR / relative).read_text(encoding="utf-8"):
                return False
        except OSError:
            return False
    return True


def is_governance_path(path: str) -> bool:
    normalized = path.replace("\\", "/").lstrip("./")
    return normalized.startswith(GOVERNANCE_PREFIXES)


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    if os.getenv("HORO_ORCHESTRATOR_ONLY") != "1":
        return 0
    waived = has_recorded_waiver()

    tool_name = str(event.get("tool_name", ""))
    tool_input = event.get("tool_input", {})
    if tool_name == "Bash":
        command = str(tool_input.get("command", ""))
        try:
            dispatch_only = enforce_adaptive_dispatch(event)
        except Exception:
            deny("adaptive multi-agent dispatch rejected: DISPATCH_EVIDENCE_INVALID")
        if dispatch_only or is_standalone_dispatcher_dry_run(event):
            return 0
        if is_safe_monitoring_command(command):
            return 0
        deny("Bash command is outside the standalone read-only allowlist")

    if waived:
        return 0
    if tool_name in {"Edit", "Write", "MultiEdit"}:
        for path in iter_paths(tool_input):
            if not is_governance_path(path):
                deny(f"implementation edit requires a delegated child: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
