"""Contract test: all CI jobs declare timeout-minutes (KAN-303).

M13 of Phase 0 Foundation Hardening (KAN-290, Epic KAN-289).

Red Team CRITICAL-13: CI runs without enforced timeouts can stall indefinitely,
exhausting runner quota and blocking the merge queue. This test freezes the
contract: every job in ci.yml and test_provenance.yml MUST declare a
timeout-minutes value.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
CI_YML = ROOT / ".github" / "workflows" / "ci.yml"
TP_YML = ROOT / ".github" / "workflows" / "test_provenance.yml"


def _load(path: Path) -> dict:
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(doc, dict)
    return doc


def _jobs_without_timeout(workflow: dict) -> list[str]:
    missing: list[str] = []
    for name, jd in workflow.get("jobs", {}).items():
        if "timeout-minutes" not in jd:
            missing.append(name)
    return missing


def test_ci_yml_all_jobs_have_timeout() -> None:
    ci = _load(CI_YML)
    missing = _jobs_without_timeout(ci)
    assert not missing, (
        "ci.yml jobs missing timeout-minutes (M13):\n"
        + "\n".join(f"  - {m}" for m in missing)
    )


def test_test_provenance_yml_all_jobs_have_timeout() -> None:
    tp = _load(TP_YML)
    missing = _jobs_without_timeout(tp)
    assert not missing, (
        "test_provenance.yml jobs missing timeout-minutes (M13):\n"
        + "\n".join(f"  - {m}" for m in missing)
    )


def test_timeout_values_are_positive_integers() -> None:
    for path, label in [(CI_YML, "ci.yml"), (TP_YML, "test_provenance.yml")]:
        wf = _load(path)
        for name, jd in wf.get("jobs", {}).items():
            tm = jd.get("timeout-minutes")
            assert isinstance(tm, int), f"{label}:{name} timeout-minutes must be int, got {type(tm)}"
            assert 1 <= tm <= 360, f"{label}:{name} timeout-minutes={tm} out of range (1..360)"