#!/usr/bin/env python3
"""Regression contract test for KAN-189: Test isolation without dirtying tracked repo files.

A full or partial test run must not mutate tracked repository data files:
  - plans/evidence/quota-swap-roadmap-20260904/qa-simulation.json
  - project/data/hitl_reviews.json
  - project/data/distillation_checklist.json
  - project/data/bazi_bazi_manual_chatml.jsonl
  - project/static/charts/*.svg
"""

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

TRACKED_DATA_TARGETS = [
    "plans/evidence/quota-swap-roadmap-20260904/qa-simulation.json",
    "project/data/hitl_reviews.json",
    "project/data/distillation_checklist.json",
    "project/data/bazi_bazi_manual_chatml.jsonl",
    "project/static/charts/bazi_chart.svg",
    "project/static/charts/zodiac_wheel.svg",
]


@pytest.fixture(autouse=True)
def clean_isolation_targets():
    """Ensure tracked data targets are at pristine HEAD before and after test."""
    subprocess.run(
        ["git", "checkout", "HEAD", "--"] + TRACKED_DATA_TARGETS,
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
    )
    yield
    subprocess.run(
        ["git", "checkout", "HEAD", "--"] + TRACKED_DATA_TARGETS,
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
    )


def _get_dirty_tracked_files() -> list[str]:
    """Return any tracked data targets currently dirty in git."""
    res = subprocess.run(
        ["git", "status", "--porcelain", "--"] + TRACKED_DATA_TARGETS,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    lines = [line.strip() for line in res.stdout.splitlines() if line.strip()]
    return lines


def test_quota_swap_simulation_leaves_repo_clean():
    """tests/test_quota_swap_simulation.py must not modify qa-simulation.json."""
    res = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "tests/test_quota_swap_simulation.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, f"Subprocess pytest failed:\n{res.stdout}\n{res.stderr}"
    dirty = _get_dirty_tracked_files()
    assert not dirty, f"Test execution dirtied tracked files:\n{dirty}"


def test_button_regression_leaves_hitl_reviews_clean():
    """project/tests/test_button_regression.py must not modify project/data/hitl_reviews.json."""
    res = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "project/tests/test_button_regression.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, f"Subprocess pytest failed:\n{res.stdout}\n{res.stderr}"
    dirty = _get_dirty_tracked_files()
    assert not dirty, f"Test execution dirtied tracked files:\n{dirty}"


def test_distillation_checklist_leaves_checklist_clean():
    """project/tests/test_distillation_checklist.py must not modify distillation_checklist.json or chatml dataset."""
    res = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "project/tests/test_distillation_checklist.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, f"Subprocess pytest failed:\n{res.stdout}\n{res.stderr}"
    dirty = _get_dirty_tracked_files()
    assert not dirty, f"Test execution dirtied tracked files:\n{dirty}"


def test_e2e_mcp_svg_leaves_charts_clean():
    """project/tests/test_e2e_mcp_svg.py must not write SVGs into project/static/charts/."""
    res = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "project/tests/test_e2e_mcp_svg.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, f"Subprocess pytest failed:\n{res.stdout}\n{res.stderr}"
    dirty = _get_dirty_tracked_files()
    assert not dirty, f"Test execution dirtied tracked files:\n{dirty}"
