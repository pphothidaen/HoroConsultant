#!/usr/bin/env python3
"""
scripts/run_quality_gate.py — Strict Zero-Tolerance Quality Gate (Decision 10)
=============================================================================
Enforces 100% pass mandate across:
  Stage 1: Secret Leakage Scan (0 leaks allowed)
  Stage 2: SDLC & Codex Agent Specification Cross-Platform Sync
  Stage 3: Comprehensive Pytest Unit & Integration Regression Suite
  Stage 4: 25-Button UI & API Contract Regression Suite

Exit Code: 0 on 100% pass, 1 on any failure.
"""

import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run_stage(stage_num: int, stage_name: str, cmd: list[str]) -> bool:
    print(f"\n======================================================================")
    print(f" [STAGE {stage_num}/4] {stage_name}")
    print(f"======================================================================")
    t0 = time.monotonic()
    result = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    elapsed = round((time.monotonic() - t0), 2)

    if result.returncode == 0:
        print(f"[OK] {stage_name} PASSED in {elapsed}s")
        return True
    else:
        print(f"[ERROR] {stage_name} FAILED (Exit Code: {result.returncode})")
        if result.stdout:
            print(result.stdout[-1500:])
        if result.stderr:
            print(result.stderr[-1500:])
        return False


def main() -> int:
    print("🛡️  STARTING STRICT ZERO-TOLERANCE QUALITY GATE VERIFICATION...")

    stages = [
        (1, "Secret Leakage Security Audit", [sys.executable, "project/core/code_reviewer.py", "--scan-secrets"]),
        (2, "SDLC & Codex Agent Cross-Sync Check", [sys.executable, "scripts/sync_sdlc_agents.py", "--check", "--use-python"]),
        (3, "Pytest Core Regression Suite", [sys.executable, "-m", "pytest", "project/tests/test_api_router_external.py", "project/tests/test_telegram_gemini_alert.py", "project/tests/test_observability.py", "project/tests/test_ai_provider_router.py", "-v"]),
        (4, "25-Button UI & API Contract Suite", [sys.executable, "scripts/run_button_regression.py"]),
    ]

    all_passed = True
    for stage_num, stage_name, cmd in stages:
        if not run_stage(stage_num, stage_name, cmd):
            all_passed = False
            break

    print("\n======================================================================")
    if all_passed:
        print("  🎉 QUALITY GATE STATUS: 100% PASSED (READY FOR PRODUCTION RELEASE)")
        print("======================================================================")
        return 0
    else:
        print("  ❌ QUALITY GATE STATUS: FAILED (RELEASE BLOCKED)")
        print("======================================================================")
        return 1


if __name__ == "__main__":
    sys.exit(main())
