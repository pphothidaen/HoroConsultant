#!/usr/bin/env python3
"""Hermes pre_tool_use Hook — KAN-118 / KAN-105.

Validates proposed tool calls:
1. Rejects synthetic/mock command strings that bypass real execution.
2. Enforces Jira ticket context on state mutation tools.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Add scripts directory to path
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

try:
    from runtime_guardrails_gate import detect_synthetic_mock, validate_tool_call
except ImportError:
    print("[ERROR] Failed to load runtime_guardrails_gate module.", file=sys.stderr)
    sys.exit(1)


def main() -> int:
    tool_name = sys.argv[1] if len(sys.argv) > 1 else ""
    args_json = sys.argv[2] if len(sys.argv) > 2 else "{}"

    try:
        args = json.loads(args_json)
    except json.JSONDecodeError:
        args = {"raw": args_json}

    # Check synthetic mock patterns
    detected, mock_reason = detect_synthetic_mock(args_json)
    if detected:
        print(f"❌ [GOVERNANCE DENIED] Synthetic/mock execution pattern detected: {mock_reason}", file=sys.stderr)
        return 1

    # Check tool permissions
    ok, tool_reason = validate_tool_call(tool_name, args)
    if not ok:
        print(f"❌ [GOVERNANCE DENIED] {tool_reason}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
