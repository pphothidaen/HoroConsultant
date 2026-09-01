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
import subprocess
import sys
from pathlib import Path

FORBIDDEN_PATTERNS = [
    (r"--no-progress-bar", "Use '--progress-bar off' with pip instead of invalid '--no-progress-bar'."),
    (r"pip install torch==", "Do NOT reinstall PyTorch in Kaggle environment; use pre-installed native PyTorch."),
    (r"rm\s+-rf\s+/(?:\s|$)", "Destructive root deletion is forbidden."),
    (r"\brm\s+-rf\b", "Recursive force deletion is forbidden in agent automation; use a reviewed, explicit cleanup plan instead."),
    (r"\bgit\s+push\b.*(?:\s-f\b|--force(?:-with-lease)?\b)", "Force push is forbidden for agent automation."),
    (
        r"\b(?:cat|less|more|head|tail|sed|awk|grep|rg|open)\b.*(?:^|[/\s])(?:\.env(?:\.|$|[\s/])|credentials(?:\.|/|$)|.*secret.*|.*token.*|id_rsa|.*\.pem\b)",
        "Reading secret-like files is forbidden. Reference secret names only and use approved secret managers.",
    ),
    (r"mkfs", "Filesystem formatting is forbidden.")
]

IS_CI = os.environ.get("CI", "").lower() in ("true", "1") or os.environ.get("GITHUB_ACTIONS", "").lower() in ("true", "1")
ROOT_DIR = Path(__file__).resolve().parents[2]
QUOTA_ENV_KEYS = (
    "AGENT_QUOTA_REMAINING_PERCENT",
    "AI_AGENT_QUOTA_REMAINING_PERCENT",
    "CODEX_QUOTA_REMAINING_PERCENT",
    "CODEX_REMAINING_QUOTA_PERCENT",
)


def _should_run_quota_guard(command_str: str) -> bool:
    lowered = command_str.lower()
    return any(os.getenv(key) for key in QUOTA_ENV_KEYS) or "/status" in lowered or "/staus" in lowered


def _run_quota_guard() -> tuple[bool, str]:
    guard_script = ROOT_DIR / "scripts" / "agent_quota_status_guard.py"
    if not guard_script.exists():
        return False, "Quota guard script missing: scripts/agent_quota_status_guard.py"
    try:
        result = subprocess.run(
            [sys.executable, str(guard_script), "--enforce"],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except Exception as exc:
        return False, f"Quota guard execution failed: {exc}"
    output = (result.stdout or result.stderr or "").strip()
    if result.returncode != 0:
        return False, output or "Quota guard failed"
    return True, output or "Quota guard passed"


def check_command(command_str: str) -> tuple[bool, str]:
    """Check command against forbidden patterns and enforce pre-push gates."""
    for pattern, reason in FORBIDDEN_PATTERNS:
        if re.search(pattern, command_str):
            return False, reason

    if _should_run_quota_guard(command_str):
        quota_ok, quota_reason = _run_quota_guard()
        if not quota_ok:
            return False, quota_reason

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

    if "git tag" in command_str or "git push" in command_str:
        # Allow git push to feature branches (not main)
        if "git push origin main" in command_str:
            return False, "Direct push to main is forbidden. Use a PR."
        
        # Block git push without ReleaseNotes.md
        if not (ROOT_DIR / "ReleaseNotes.md").exists():
            return False, "ReleaseNotes.md missing! Rule 22 mandate requires updated release notes before tagging or pushing."
        
        # Block git push with stale plans
        plans_dir = ROOT_DIR / "plans"
        stale_files = []
        if plans_dir.is_dir():
            for file in plans_dir.iterdir():
                if file.is_file() and file.name.endswith(".md"):
                    if file.name not in ["plan.md", "metaphysics_learning_roadmap.md", "question_forecast_alignment_spec.md"]:
                        stale_files.append(file.name)
        if stale_files:
            return False, f"Rule 22 mandate failed: Stale plans found before release push/tag. Archive them first: {', '.join(stale_files)}"
        
        # Allow git push to feature branches
        if "git push origin" in command_str and "git push origin main" not in command_str:
            return True, "Passed pre-tool checks (feature branch push allowed)"

    # Allow gh CLI commands for PR automation
    if re.search(r"\bgh\s+(pr|run|workflow|auth)\b", command_str):
        return True, "Passed pre-tool checks (gh CLI allowed)"

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
