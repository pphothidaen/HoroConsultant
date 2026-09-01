#!/usr/bin/env python3
"""Claude Code PreToolUse guard for HoroConsultant.

This hook enforces project-level hard constraints before tool execution.
It intentionally prints only ASCII messages because subprocess and notebook
logs in this project must remain surrogate-safe.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR / "scripts"))
from branch_lifecycle_guard import validate_delete_command


SECRET_PATH_PATTERNS = (
    re.compile(r"(^|/)\.env(\..*)?$"),
    re.compile(r"(^|/)(credentials?|secrets?)(\.|/|$)", re.IGNORECASE),
    re.compile(r"(^|/)(id_rsa|id_ed25519|known_hosts)$"),
    re.compile(r"(^|/)\.aws/(credentials|config)$"),
    re.compile(r"(^|/)\.azure(/|$)"),
    re.compile(r"(^|/)\.config/gh/hosts\.yml$"),
)

DESTRUCTIVE_BASH_PATTERNS = (
    (re.compile(r"\brm\s+[^;\n]*-[^\s;\n]*r[^\s;\n]*f\b"), "rm -rf is blocked"),
    (re.compile(r"\bgit\s+push\b[^\n;]*\s--force(?:-with-lease)?\b"), "force push is blocked"),
    (re.compile(r"\bgit\s+reset\s+--hard\b"), "git reset --hard is blocked"),
    (re.compile(r"\bgit\s+clean\b[^\n;]*\s-[^\s;\n]*[fxd]"), "git clean destructive flags are blocked"),
    (re.compile(r"\bdocker\s+system\s+prune\b[^\n;]*\s-[^\s;\n]*f"), "docker system prune -f is blocked"),
    (re.compile(r"\bkubectl\s+delete\b"), "kubectl delete is blocked by project hook"),
)

SECRET_OUTPUT_BASH_PATTERNS = (
    (re.compile(r"\bgh\s+auth\s+token\b"), "gh auth token prints a bearer token"),
    (re.compile(r"\bdoppler\s+secrets\s+get\b[^\n;]*\s--plain\b"), "doppler secrets get --plain prints a secret"),
    (re.compile(r"\b(printenv|env)\b[^\n;]*(TOKEN|SECRET|PASSWORD|KEY)\b", re.IGNORECASE), "printing secret env vars is blocked"),
    (re.compile(r"\baz\s+ad\s+app\s+credential\s+reset\b(?![^\n;]*--query\s+appId)"), "Azure credential reset can print a client secret"),
)

SECRET_READ_COMMAND = re.compile(r"\b(cat|sed|awk|grep|rg|less|more|head|tail|open)\b")
QUOTA_ENV_KEYS = (
    "AGENT_QUOTA_REMAINING_PERCENT",
    "AI_AGENT_QUOTA_REMAINING_PERCENT",
    "CODEX_QUOTA_REMAINING_PERCENT",
    "CODEX_REMAINING_QUOTA_PERCENT",
)


def deny(reason: str) -> None:
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"[BLOCKED] {reason}",
        }
    }
    print(json.dumps(payload, ensure_ascii=True))
    raise SystemExit(0)


def iter_paths(value: Any) -> list[str]:
    paths: list[str] = []
    if isinstance(value, str):
        paths.append(value)
    elif isinstance(value, list):
        for item in value:
            paths.extend(iter_paths(item))
    elif isinstance(value, dict):
        for key in ("file_path", "path", "notebook_path", "pattern"):
            if key in value:
                paths.extend(iter_paths(value[key]))
    return paths


def is_secret_path(raw_path: str) -> bool:
    normalized = raw_path.replace("\\", "/")
    if normalized.startswith("./"):
        normalized = normalized[2:]
    basename = Path(normalized).name.lower()
    if basename in {".env", ".env.local", ".env.production", "credentials.json", "secrets.json"}:
        return True
    return any(pattern.search(normalized) for pattern in SECRET_PATH_PATTERNS)


def inspect_bash(command: str) -> None:
    for pattern, reason in DESTRUCTIVE_BASH_PATTERNS:
        if pattern.search(command):
            deny(reason)

    branch_delete_ok, branch_delete_reason = validate_delete_command(command, repo=ROOT_DIR)
    if not branch_delete_ok:
        deny(branch_delete_reason)

    if re.search(r"\bgit\s+(?:commit|push)\b", command):
        guard = ROOT_DIR / "scripts" / "validate_alias_contract.py"
        if not guard.exists():
            deny("alias contract guard script is missing")
        result = subprocess.run(
            [sys.executable, str(guard)],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if result.returncode != 0:
            reason = (result.stdout or result.stderr or "alias contract guard failed").strip()
            deny(reason)

    for pattern, reason in SECRET_OUTPUT_BASH_PATTERNS:
        if pattern.search(command):
            deny(reason)

    if SECRET_READ_COMMAND.search(command):
        tokens = re.split(r"\s+", command)
        for token in tokens:
            candidate = token.strip("'\";|&()")
            if candidate and is_secret_path(candidate):
                deny(f"reading secret file is blocked: {candidate}")

    lowered = command.lower()
    if any(os.getenv(key) for key in QUOTA_ENV_KEYS) or "/status" in lowered or "/staus" in lowered:
        guard = ROOT_DIR / "scripts" / "agent_quota_status_guard.py"
        if not guard.exists():
            deny("quota status guard script is missing")
        result = subprocess.run(
            [sys.executable, str(guard), "--enforce"],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if result.returncode != 0:
            reason = (result.stdout or result.stderr or "quota status guard failed").strip()
            deny(reason)

    if "git tag" in command or "git push" in command:
        if not (ROOT_DIR / "ReleaseNotes.md").exists():
            deny("ReleaseNotes.md missing! Rule 22 mandate requires updated release notes before tagging or pushing.")
        
        plans_dir = ROOT_DIR / "plans"
        stale_files = []
        if plans_dir.is_dir():
            for file in plans_dir.iterdir():
                if file.is_file() and file.name.endswith(".md"):
                    if file.name not in ["plan.md", "metaphysics_learning_roadmap.md", "question_forecast_alignment_spec.md"]:
                        stale_files.append(file.name)
        if stale_files:
            deny(f"Rule 22 mandate failed: Stale plans found before release push/tag. Archive them first: {', '.join(stale_files)}")


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    tool_name = str(event.get("tool_name", ""))
    tool_input = event.get("tool_input", {})

    if tool_name == "Bash":
        inspect_bash(str(tool_input.get("command", "")))
        return 0

    for raw_path in iter_paths(tool_input):
        if is_secret_path(raw_path):
            deny(f"{tool_name} access to secret path is blocked: {raw_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
