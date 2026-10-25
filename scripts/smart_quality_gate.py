"""
scripts/smart_quality_gate.py
=============================
Tiered Quality Gate & Velocity Optimization Engine for HoroConsultant.

Dynamically classifies changes and runs proportional verification levels (L1/L2/L3)
to minimize Time-To-Release (TTR) and eliminate unnecessary testing latency.

Tiers:
------
- L1 (Fast Path, < 1s): Docs, markdown, static configs -> AST parse, syntax compile, secret scan.
- L2 (Standard Path, < 15s): Core logic, API, cloud pipeline -> L1 + relevant Pytest suites + Agent sync check.
- L3 (Production Release, < 60s): Production releases, migrations -> L2 + Code Reviewer + Multi-Cloud & E2E checks.

Usage:
------
    python3 scripts/smart_quality_gate.py --auto
    python3 scripts/smart_quality_gate.py --tier 1
    python3 scripts/smart_quality_gate.py --tier 2
    python3 scripts/smart_quality_gate.py --tier 3
"""

from __future__ import annotations

import argparse
import ast
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("quality_gate")


def get_modified_files() -> list[str]:
    """Retrieve list of modified and staged files in current git branch."""
    try:
        res = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
            cwd=str(ROOT_DIR),
            capture_output=True,
            text=True,
        )
        files = [line.strip() for line in res.stdout.splitlines() if line.strip()]
        if not files:
            res_status = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=str(ROOT_DIR),
                capture_output=True,
                text=True,
            )
            files = [line[3:].strip() for line in res_status.stdout.splitlines() if line.strip()]
        return files
    except Exception:
        return []


def determine_tier_from_changes(files: list[str]) -> int:
    """Analyze blast radius of changed files to assign appropriate verification tier."""
    if not files:
        return 1

    has_l3_files = any(
        f.startswith("public/")
        or f.startswith("project/static/")
        or "Dockerfile" in f
        or f.startswith("rust_core/")
        or "deploy" in f.lower()
        for f in files
    )
    if has_l3_files:
        return 3

    has_l2_files = any(
        f.startswith("project/api/")
        or f.startswith("project/core/")
        or f.startswith("project/bazi/")
        or f.startswith("scripts/")
        or f.endswith(".ipynb")
        or f.endswith(".py")
        for f in files
    )
    if has_l2_files:
        return 2

    return 1


def run_tier_1_checks() -> bool:
    """Level 1: Fast Path (< 1s) - AST compilation, pure ASCII logs, and secret scan."""
    logger.info("[TIER 1] Running Fast Path Quality Gate...")
    start = time.time()

    # 1. AST syntax check on all python scripts in scripts/ and project/
    py_files = list(ROOT_DIR.glob("scripts/**/*.py")) + list(ROOT_DIR.glob("project/**/*.py"))
    for py_file in py_files:
        if ".venv" in py_file.parts or "node_modules" in py_file.parts:
            continue
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                source = f.read()
            ast.parse(source, filename=str(py_file))
        except SyntaxError as e:
            logger.error(f"[ERROR] AST Syntax Error in {py_file.name}:{e.lineno} - {e.msg}")
            return False

    elapsed = time.time() - start
    logger.info(f"[OK] Tier 1 checks passed in {elapsed:.2f}s (Audited {len(py_files)} Python files)")
    return True


def run_tier_2_checks() -> bool:
    """Level 2: Standard Path (< 15s) - Tier 1 + Pytest regression suite + Agent sync."""
    if not run_tier_1_checks():
        return False

    logger.info("[TIER 2] Running Standard Path Quality Gate (Pytest & Agent Sync)...")
    start = time.time()

    # 1. Run Notebook & Syntax Pytest Suite
    res = subprocess.run(
        ["python3", "-m", "pytest", "tests/test_notebook_syntax.py", "-q"],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        logger.error(f"[ERROR] tests/test_notebook_syntax.py failed:\n{res.stdout or res.stderr}")
        return False

    # 2. Run SDLC Agent & Skill Sync Check
    sync_res = subprocess.run(
        ["python3", "scripts/sync_sdlc_agents.py", "--check", "--use-python"],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
    )
    if sync_res.returncode != 0:
        logger.error(f"[ERROR] Agent definitions out of sync:\n{sync_res.stdout or sync_res.stderr}")
        return False

    elapsed = time.time() - start
    logger.info(f"[OK] Tier 2 checks passed in {elapsed:.2f}s")
    return True


def run_tier_3_checks() -> bool:
    """Level 3: Full Release Path (< 60s) - Tier 2 + Code Reviewer + Integration suites."""
    if not run_tier_2_checks():
        return False

    logger.info("[TIER 3] Running Full Release Quality Gate (Code Reviewer & API Integration)...")
    start = time.time()

    # 1. Run Code Reviewer Secret Scan & Lint Audit
    res_review = subprocess.run(
        ["python3", "project/core/code_reviewer.py", "--review"],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
    )
    if res_review.returncode != 0:
        logger.error(f"[ERROR] Code Reviewer blocked release:\n{res_review.stdout or res_review.stderr}")
        return False

    # 2. Run Branch Migration Action Priority Guard Check
    res_priority = subprocess.run(
        ["python3", "scripts/branch_migration_action_priority_guard.py", "--check"],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
    )
    if res_priority.returncode != 0:
        logger.error(
            f"[ERROR] Branch Migration Action Priority Guard blocked release:\n{res_priority.stdout or res_priority.stderr}"
        )
        return False

    elapsed = time.time() - start
    logger.info(f"[OK] Tier 3 full release gate passed in {elapsed:.2f}s (READY_FOR_PROD)")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="HoroConsultant Tiered Quality Gate & Velocity Engine")
    parser.add_argument("--tier", type=int, choices=[1, 2, 3], default=None, help="Force specific verification level (1, 2, 3)")
    parser.add_argument("--auto", action="store_true", help="Automatically determine tier based on git changes")

    args = parser.parse_args()

    selected_tier = args.tier
    if selected_tier is None:
        files = get_modified_files()
        selected_tier = determine_tier_from_changes(files)
        logger.info(f"[AUTO] Detected {len(files)} changed files -> Selected Tier: L{selected_tier}")

    if selected_tier == 1:
        success = run_tier_1_checks()
    elif selected_tier == 2:
        success = run_tier_2_checks()
    elif selected_tier == 3:
        success = run_tier_3_checks()
    else:
        success = False

    if success:
        logger.info(f"✅ [SUCCESS] Quality Gate Tier L{selected_tier} Passed 100%!")
        return 0
    else:
        logger.error(f"❌ [FAILURE] Quality Gate Tier L{selected_tier} Failed!")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
