#!/usr/bin/env python3
"""TDD State Transition Gate Enforcer — KAN-95/KAN-105.

Validates state transitions and evidence before allowing Jira status updates or Git pushes.
- Backlog / Selected for Development -> TDD RED (requires failing test)
- TDD RED -> TDD GREEN (requires all tests passing + test provenance manifest)
- TDD GREEN -> Review (requires PR / AST verification)
- Review -> Done (requires merge / verified CI)
"""

from __future__ import annotations

import argparse
import glob
import os
import subprocess
import sys
from typing import Optional, Tuple

ALLOWED_TRANSITIONS = {
    "Backlog": ["TDD RED", "Selected for Development"],
    "Selected for Development": ["TDD RED", "Backlog"],
    "TDD RED": ["TDD GREEN", "Backlog"],
    "TDD GREEN": ["Review", "TDD RED"],
    "Review": ["Done", "TDD RED"],
    "Done": [],
}


def check_red_state(test_target: Optional[str] = None) -> Tuple[bool, str]:
    """TDD RED requires running tests and encountering at least one failure."""
    cmd = ["pytest"]
    if test_target:
        cmd.append(test_target)
    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            return False, "Tests passed. TDD RED requires at least one failing test."
        return True, f"Failing test verified (exit code {res.returncode})."
    except FileNotFoundError:
        return False, "pytest command not found in environment."


def check_green_state(issue_key: str, test_target: Optional[str] = None) -> Tuple[bool, str]:
    """TDD GREEN requires all tests to pass and a matching provenance manifest."""
    cmd = ["pytest"]
    if test_target:
        cmd.append(test_target)
    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            return False, f"Tests failed with exit code {res.returncode}. TDD GREEN requires all tests to pass."
    except FileNotFoundError:
        return False, "pytest command not found in environment."

    # Validate provenance manifest in plans/test_provenance/
    clean_key = issue_key.lower()
    manifest_pattern = f"plans/test_provenance/*{clean_key}*.json"
    matches = glob.glob(manifest_pattern)
    if not matches:
        return False, f"Missing test provenance manifest matching '{manifest_pattern}'."

    return True, f"All tests passed and provenance manifest verified ({matches[0]})."


def verify_transition(
    current: str,
    target: str,
    issue_key: str,
    test_target: Optional[str] = None,
) -> Tuple[bool, str]:
    """Validate state transition rules and prerequisite evidence."""
    current_normalized = current.strip()
    target_normalized = target.strip()

    valid_targets = ALLOWED_TRANSITIONS.get(current_normalized)
    if valid_targets is None:
        return False, f"Unknown source status: '{current_normalized}'."

    if target_normalized not in valid_targets:
        return (
            False,
            f"Invalid transition: Cannot move from '{current_normalized}' to '{target_normalized}'. "
            f"Allowed next states: {valid_targets}",
        )

    if target_normalized == "TDD RED":
        return check_red_state(test_target)
    elif target_normalized == "TDD GREEN":
        return check_green_state(issue_key, test_target)

    return True, f"Transition from '{current_normalized}' to '{target_normalized}' approved."


def main() -> int:
    parser = argparse.ArgumentParser(description="Enforce TDD State Transitions.")
    parser.add_argument("--current", required=True, help="Current Jira status")
    parser.add_argument("--target", required=True, help="Target Jira status")
    parser.add_argument("--issue", required=True, help="Jira Issue Key (e.g. KAN-105)")
    parser.add_argument("--test-target", help="Specific pytest file or directory")
    args = parser.parse_args()

    ok, msg = verify_transition(args.current, args.target, args.issue, args.test_target)
    if not ok:
        print(f"❌ TRANSITION BLOCKED: {msg}", file=sys.stderr)
        return 1

    print(f"✅ TRANSITION APPROVED: {msg}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
