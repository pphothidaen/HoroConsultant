#!/usr/bin/env python3
"""Agent-label governance enforcement — KAN-105.

Pre-commit hook that validates commit messages contain an agent-* label.
Supports: agent-hermes, agent-codex1-3, agent-agy1-5, agent-default.
Bypass: merge commits, revert commits, and fixup commits.
"""

from __future__ import annotations

import re
import subprocess
import sys
from typing import List, Optional

# Agent label pattern: agent- followed by alphanumeric, underscore, hyphen
LABEL_PATTERN = re.compile(r"\bagent-[a-zA-Z0-9][a-zA-Z0-9_-]*\b")

# Allowed agent prefixes (matches the known agent roster)
ALLOWED_AGENT_PREFIXES = [
    "agy1", "agy2", "agy3", "agy4", "agy5",
    "codex1", "codex2", "codex3",
    "hermes", "default",
]

# Commit types that bypass label requirement
BYPASS_PATTERNS = [
    r"^Merge\s",           # Merge commits
    r"^Revert\s",          # Revert commits
    r"^fixup!\s",          # Fixup commits
    r"^squash!\s",         # Squash commits
    r"^\s*\(#\d+\)\s*$",   # Empty commit messages
]


def get_staged_commit_message() -> Optional[str]:
    """Read commit message from COMMIT_EDITMSG or stdin."""
    if len(sys.argv) > 1:
        try:
            with open(sys.argv[1], "r") as f:
                return f.read()
        except FileNotFoundError:
            pass
    return None


def validate_commit_message(message: str) -> tuple[bool, List[str]]:
    """Validate that a commit message contains an agent-* label.
    
    Returns:
        (is_valid, issues): Whether the message is valid and list of issues.
    """
    issues: List[str] = []
    
    # Strip comments
    lines = message.split("\n")
    clean_lines = [l for l in lines if not l.startswith("#")]
    clean_message = "\n".join(clean_lines).strip()
    
    if not clean_message:
        return False, ["Empty commit message"]
    
    # Check bypass patterns
    for pattern in BYPASS_PATTERNS:
        if re.match(pattern, clean_message, re.IGNORECASE):
            return True, []
    
    # Find agent-* labels
    labels = LABEL_PATTERN.findall(clean_message)
    
    if not labels:
        issues.append(
            f"No agent-* label found. Expected one of: {', '.join(f'agent-{p}' for p in ALLOWED_AGENT_PREFIXES)}"
        )
        return False, issues
    
    # Validate labels are from known agents
    for label in labels:
        agent_name = label.replace("agent-", "", 1)
        if agent_name not in ALLOWED_AGENT_PREFIXES:
            issues.append(f"Unknown agent label: {label}")
    
    if issues:
        return False, issues
    
    return True, []


def main() -> int:
    """Entry point."""
    message = get_staged_commit_message()
    if message is None:
        print("ERROR: No commit message provided", file=sys.stderr)
        return 1
    
    is_valid, issues = validate_commit_message(message)
    
    if not is_valid:
        print("AGENT LABEL CHECK FAILED:", file=sys.stderr)
        for issue in issues:
            print(f"  - {issue}", file=sys.stderr)
        print(
            "\nFix: Add an agent-* label to your commit message, e.g.:",
            file=sys.stderr,
        )
        print('  feat: add new feature [KAN-101] agent-hermes', file=sys.stderr)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
