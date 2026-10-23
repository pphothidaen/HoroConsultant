"""Contract test: gitleaks secret scan runs in ci.yml lint-and-security job (KAN-297).

M7 of Phase 0 Foundation Hardening (KAN-290, Epic KAN-289).

Red Team CRITICAL-7: no secret scanning in CI pipeline — leaked credentials
in code/history undetected until exploited. This test freezes the contract:
ci.yml MUST run gitleaks in the lint-and-security job on every tier.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
CI_YML = ROOT / ".github" / "workflows" / "ci.yml"

GITLEAKS_ACTION_RE = re.compile(
    r"^gitleaks/gitleaks-action@[0-9a-f]{40}(?:\s+#.*)?$"
)


def _ci() -> dict:
    doc = yaml.safe_load(CI_YML.read_text(encoding="utf-8"))
    assert isinstance(doc, dict)
    return doc


def test_lint_and_security_job_exists() -> None:
    ci = _ci()
    assert "lint-and-security" in ci.get("jobs", {}), "lint-and-security job must exist"


def test_lint_and_security_runs_gitleaks() -> None:
    ci = _ci()
    job = ci["jobs"]["lint-and-security"]
    steps = job.get("steps", [])
    uses_values = [str(s.get("uses", "")) for s in steps if isinstance(s, dict)]

    # Must contain gitleaks action pinned to SHA
    gitleaks_steps = [u for u in uses_values if GITLEAKS_ACTION_RE.match(u)]
    assert gitleaks_steps, (
        "lint-and-security must run gitleaks/gitleaks-action pinned to a 40-hex SHA "
        f"(found: {uses_values})"
    )
    assert len(gitleaks_steps) == 1, f"exactly one gitleaks step expected, got {len(gitleaks_steps)}"


def test_lint_and_security_no_if_guard_runs_on_all_tiers() -> None:
    ci = _ci()
    job = ci["jobs"]["lint-and-security"]
    assert "if" not in job, (
        "lint-and-security must run on ALL tiers (LIGHT/MEDIUM/STRICT) — "
        "no 'if' guard allowed. Found: {job.get('if')}"
    )


def test_gitleaks_uses_github_token() -> None:
    ci = _ci()
    job = ci["jobs"]["lint-and-security"]
    steps = job.get("steps", [])
    for step in steps:
        if isinstance(step, dict) and GITLEAKS_ACTION_RE.match(str(step.get("uses", ""))):
            env = step.get("env", {})
            assert env.get("GITHUB_TOKEN") == "${{ secrets.GITHUB_TOKEN }}", (
                "gitleaks step must use GITHUB_TOKEN from secrets"
            )
            return
    pytest.fail("gitleaks step not found")