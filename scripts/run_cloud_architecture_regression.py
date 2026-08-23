#!/usr/bin/env python3
"""
scripts/run_cloud_architecture_regression.py
============================================
Standalone Executable CLI Runner for Cloud Architecture Overview (Full Stack).
Runs and audits all 8 architecture phases:
- Phase 0: Startup & Lifespan Boot
- Phase 1: Request Entry & Edge CDN
- Phase 2: Router Dispatch & Classification
- Phase 3A: Metaphysical Calculation Engines (16 Disciplines)
- Phase 3B: RAG Vector Search
- Phase 3C: LLM 6-Tier Failover & Peer Debate
- Phase 4: Response Assembly & Prometheus Metrics
- Phase 5: MLOps Feedback Loop & Active Model Registry
- Phase 6: Admin Vault & Ingestion
- Phase 7: Observability & Alerting

Usage:
    python scripts/run_cloud_architecture_regression.py
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent


def main():
    print("=" * 70)
    print("🚀 HoroConsultant — Cloud Architecture Overview (Full Stack) Regression")
    print("=" * 70)
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Working Directory: {ROOT_DIR}\n")

    cmd = [
        sys.executable, "-m", "pytest",
        str(ROOT_DIR / "project" / "tests" / "test_cloud_architecture_overview_regression.py"),
        "-v",
        "--no-header",
        "-rA",
    ]

    t0 = time.perf_counter()
    res = subprocess.run(cmd, cwd=str(ROOT_DIR))
    elapsed = time.perf_counter() - t0

    print("\n" + "=" * 70)
    if res.returncode == 0:
        print(f"✅ Cloud Architecture Overview Regression: 100% PASSED ({elapsed:.2f}s)")
    else:
        print(f"❌ Cloud Architecture Overview Regression: FAILED with exit code {res.returncode}")
    print("=" * 70 + "\n")

    sys.exit(res.returncode)


if __name__ == "__main__":
    main()
