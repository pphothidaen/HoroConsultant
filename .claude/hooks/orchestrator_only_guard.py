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
ROOT_BASH_BLOCKS = (
    (re.compile(r"\bgit\s+(?:add|commit|push|merge|rebase|reset|restore|checkout|cherry-pick|tag)\b"), "git mutation"),
    (re.compile(r"\b(?:pytest|playwright)\b|\bnode\s+--test\b|\b(?:npm|pnpm|yarn)\s+(?:run\s+)?(?:test|build|lint|typecheck)\b"), "QA or implementation command"),
    (re.compile(r"\b(?:python\d*|uv)\s+-m\s+pytest\b|\b(?:scripts|project/tests|tests)/[^\s]*(?:test|qa|audit|verification|e2e|regression)[^\s]*"), "QA command"),
    (re.compile(r"\b(?:vercel|huggingface-cli|hf\s+upload|kubectl\s+(?:apply|replace|rollout)|helm\s+(?:upgrade|install)|terraform\s+apply|docker\s+push|npm\s+publish|gh\s+workflow\s+run)\b|publish_space_hf\.py"), "deploy or publish command"),
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
    if os.getenv("HORO_ORCHESTRATOR_ONLY") != "1" or has_recorded_waiver():
        return 0

    tool_name = str(event.get("tool_name", ""))
    tool_input = event.get("tool_input", {})
    if tool_name == "Bash":
        command = str(tool_input.get("command", ""))
        for pattern, label in ROOT_BASH_BLOCKS:
            if pattern.search(command):
                deny(f"{label} requires a delegated child or recorded user waiver")
        return 0

    if tool_name in {"Edit", "Write", "MultiEdit"}:
        for path in iter_paths(tool_input):
            if not is_governance_path(path):
                deny(f"implementation edit requires a delegated child: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
