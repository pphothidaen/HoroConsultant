#!/usr/bin/env python3
"""Hermes pre_dispatch Hook — KAN-118 / KAN-105.

Validates that any task dispatch has:
1. Valid Jira Ticket ID (KAN-<ID>)
2. Valid authorized specialist agent label (agent-*)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Add scripts directory to path
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

try:
    from runtime_guardrails_gate import validate_dispatch
except ImportError:
    # If module cannot be loaded, fail closed
    print("[ERROR] Failed to load runtime_guardrails_gate module.", file=sys.stderr)
    sys.exit(1)


def main() -> int:
    # Read prompt from arguments or stdin
    prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else sys.stdin.read()
    agent_label = os.environ.get("HERMES_AGENT_LABEL", "agent-hermes")

    ok, reason = validate_dispatch(prompt, agent_label)
    if not ok:
        print(f"❌ [GOVERNANCE DENIED] {reason}", file=sys.stderr)
        return 1

    print(f"✅ [GOVERNANCE APPROVED] {reason}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
