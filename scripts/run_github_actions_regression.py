#!/usr/bin/env python3
"""
scripts/run_github_actions_regression.py
========================================
Standalone Executable CLI Runner for all 14 GitHub Actions Workflows Regression.
Validates:
- All 14 workflow YAML files syntax & structural correctness
- Action version standards (actions/checkout@v4, actions/setup-python@v5, etc.)
- Doppler 1st Priority secrets conventions
- Job dependencies (needs:) graphs
- Script invocation targets existence and py_compile validity

Usage:
    python scripts/run_github_actions_regression.py
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent


def main():
    print("=" * 70)
    print("🐙 HoroConsultant — GitHub Actions Workflows Full Regression")
    print("=" * 70)
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Working Directory: {ROOT_DIR}\n")

    cmd = [
        sys.executable, "-m", "pytest",
        str(ROOT_DIR / "project" / "tests" / "test_github_actions_regression.py"),
        "-v",
        "--no-header",
        "-rA",
    ]

    t0 = time.perf_counter()
    res = subprocess.run(cmd, cwd=str(ROOT_DIR))
    elapsed = time.perf_counter() - t0

    print("\n" + "=" * 70)
    if res.returncode == 0:
        print(f"✅ GitHub Actions Workflows Regression: 100% PASSED ({elapsed:.2f}s)")
    else:
        print(f"❌ GitHub Actions Workflows Regression: FAILED with exit code {res.returncode}")
    print("=" * 70 + "\n")

    sys.exit(res.returncode)


if __name__ == "__main__":
    main()
