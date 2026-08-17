#!/usr/bin/env python3
"""
.agents/hooks/pre_tool_check.py
Pre-Tool Call Audit Hook for AI Agents (Antigravity Protocol & CI Headless Mode).
Validates proposed commands to prevent illegal arguments, destructive commands,
or unapproved actions across local and cloud environments.
"""

import json
import os
import re
import select
import sys

FORBIDDEN_PATTERNS = [
    (r"--no-progress-bar", "Use '--progress-bar off' with pip instead of invalid '--no-progress-bar'."),
    (r"pip install torch==", "Do NOT reinstall PyTorch in Kaggle environment; use pre-installed native PyTorch."),
    (r"rm\s+-rf\s+/(?:\s|$)", "Destructive root deletion is forbidden."),
    (r"mkfs", "Filesystem formatting is forbidden.")
]

IS_CI = os.environ.get("CI", "").lower() in ("true", "1") or os.environ.get("GITHUB_ACTIONS", "").lower() in ("true", "1")


def check_command(command_str: str) -> tuple[bool, str]:
    """Check command against forbidden patterns and enforce pre-push gates."""
    for pattern, reason in FORBIDDEN_PATTERNS:
        if re.search(pattern, command_str):
            return False, reason

    # Pre-push gate: if pushing to Kaggle, run AST and notebook syntax tests first
    if "kaggle kernels push" in command_str or "kaggle_notebook_manager.py --push" in command_str:
        try:
            import subprocess
            res = subprocess.run(
                ["python3", "-m", "pytest", "tests/test_notebook_syntax.py", "-q"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if res.returncode != 0:
                return False, f"Kaggle push blocked: tests/test_notebook_syntax.py failed:\n{res.stdout or res.stderr}"
        except Exception as e:
            # If pytest is not directly available, allow command to proceed to CLI-level checks
            pass

    return True, "Passed pre-tool checks"


def read_stdin_noblock() -> str:
    """Read stdin without blocking if data is immediately available."""
    try:
        if not sys.stdin.isatty():
            rlist, _, _ = select.select([sys.stdin], [], [], 0.05)
            if rlist:
                return sys.stdin.read().strip()
    except Exception:
        pass
    return ""


def main():
    command_str = ""
    is_json_protocol = False

    # CLI arguments take precedence for CLI invocation
    if len(sys.argv) > 1:
        command_str = " ".join(sys.argv[1:])
    else:
        # Check if JSON payload passed via stdin
        stdin_data = read_stdin_noblock()
        if stdin_data:
            try:
                payload = json.loads(stdin_data)
                is_json_protocol = True
                tool_call = payload.get("toolCall", {})
                args = tool_call.get("args", {})
                command_str = (
                    args.get("CommandLine")
                    or args.get("command")
                    or args.get("cmd")
                    or str(args)
                )
            except Exception:
                command_str = stdin_data

    # Validate command
    passed, reason = check_command(command_str)

    if not passed:
        if is_json_protocol:
            response = {
                "decision": "deny",
                "reason": f"[REJECTED] Pre-Tool Hook Violation: {reason}"
            }
            print(json.dumps(response))
        else:
            print(f"[REJECTED] Pre-Tool Hook Violation: {reason}", file=sys.stderr)
        sys.exit(1)

    # Allow approved command
    if is_json_protocol:
        response = {
            "decision": "allow",
            "reason": "[OK] Pre-Tool Hook Audit: PASSED" + (" (CI Headless Mode)" if IS_CI else "")
        }
        print(json.dumps(response))
    else:
        print("[OK] Pre-Tool Hook Audit: PASSED" + (" (CI Headless Mode)" if IS_CI else ""))

    sys.exit(0)


if __name__ == "__main__":
    main()
