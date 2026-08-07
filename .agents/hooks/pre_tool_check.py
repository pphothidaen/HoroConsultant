#!/usr/bin/env python3
"""
.agents/hooks/pre_tool_check.py
Pre-Tool Call Audit Hook for AI Agents.
Validates proposed commands to prevent illegal arguments or unapproved actions.
"""

import sys
import re

FORBIDDEN_PATTERNS = [
    (r"--no-progress-bar", "Use '--progress-bar off' with pip instead of invalid '--no-progress-bar'."),
    (r"pip install torch==", "Do NOT reinstall PyTorch in Kaggle environment; use pre-installed native PyTorch."),
    (r"rm -rf /", "Destructive root deletion is forbidden.")
]

def main():
    command_str = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    for pattern, reason in FORBIDDEN_PATTERNS:
        if re.search(pattern, command_str):
            print(f"[REJECTED] Pre-Tool Hook Violation: {reason}", file=sys.stderr)
            sys.exit(1)
    
    print("[OK] Pre-Tool Hook Audit: PASSED")
    sys.exit(0)

if __name__ == "__main__":
    main()
