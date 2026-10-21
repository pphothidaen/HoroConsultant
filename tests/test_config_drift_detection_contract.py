"""Contract test: Config drift detection job in CI (KAN-299).

M11 of Phase 0 Foundation Hardening (KAN-290, Epic KAN-289).

Red Team CRITICAL-11: config drift — critical configuration files (workflows,
dependabot, branch protection, Dockerfile, render.yaml) can drift from the
reviewed state without detection. This test freezes the contract: CI MUST
include a scheduled job that verifies config files against a known-good baseline.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
CI_YML = ROOT / ".github" / "workflows" / "ci.yml"


def _load(path: Path) -> dict:
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(doc, dict)
    return doc


# ── Config files to monitor (baseline) ──────────────────────────────────

CRITICAL_CONFIGS = [
    ".github/workflows/ci.yml",
    ".github/workflows/deploy-render.yml",
    ".github/workflows/test_provenance.yml",
    ".github/workflows/production_monitor.yml",
    ".github/workflows/gitbook-webhook-pr.yml",
    ".github/dependabot.yml",
    "Dockerfile.render",
    "render.yaml",
    "wrangler.toml",
    "wrangler.jsonc",
]


def _config_files_exist() -> list[str]:
    """Return list of existing critical config files."""
    return [f for f in CRITICAL_CONFIGS if (ROOT / f).exists()]


def test_critical_configs_inventoried() -> None:
    """At least the core configs should exist."""
    existing = _config_files_exist()
    assert len(existing) >= 5, f"Expected >=5 critical configs, found: {existing}"


# ── ci.yml has config-drift-detection job ───────────────────────────────

def test_ci_has_config_drift_detection_job() -> None:
    ci = _load(CI_YML)
    jobs = ci.get("jobs", {})
    assert "config-drift-detection" in jobs, (
        "ci.yml must have a 'config-drift-detection' job (M11)"
    )
    job = jobs["config-drift-detection"]
    assert job.get("runs-on") == "ubuntu-latest"
    assert "timeout-minutes" in job


def test_config_drift_detection_runs_on_schedule() -> None:
    ci = _load(CI_YML)
    on_config = ci.get("on", ci.get(True, {}))
    schedule = on_config.get("schedule", [])
    assert any(
        "config-drift" in str(s.get("cron", "")).lower() or "0 6 * * *" in str(s.get("cron", ""))
        for s in schedule
    ), "ci.yml must have a daily schedule trigger for config drift detection (M11)"


def test_config_drift_detection_computes_baseline_hashes() -> None:
    ci = _load(CI_YML)
    job = ci.get("jobs", {}).get("config-drift-detection", {})
    steps = job.get("steps", [])
    
    has_checkout = False
    has_baseline = False
    has_diff = False
    
    for step in steps:
        if isinstance(step, dict):
            name = step.get("name", "").lower()
            run = step.get("run", "").lower()
            uses = str(step.get("uses", "")).lower()
            
            if "checkout" in uses:
                has_checkout = True
            if "baseline" in name or "hash" in name or "sha256" in run:
                has_baseline = True
            if "diff" in name or "drift" in name or "compare" in name:
                has_diff = True
    
    assert has_checkout, "Must checkout repository"
    assert has_baseline, "Must compute/verify file hashes against baseline"
    assert has_diff, "Must compare current state to baseline and report drift"


def test_config_drift_detection_fails_on_drift() -> None:
    ci = _load(CI_YML)
    job = ci.get("jobs", {}).get("config-drift-detection", {})
    steps = job.get("steps", [])
    
    found_fail = False
    for step in steps:
        if isinstance(step, dict):
            run = step.get("run", "")
            if "exit 1" in run and ("drift" in run.lower() or "mismatch" in run.lower() or "diff" in run.lower()):
                found_fail = True
                break
    
    assert found_fail, "Config drift detection must fail the job when drift detected (M11)"


def test_config_drift_detection_uploads_report() -> None:
    ci = _load(CI_YML)
    job = ci.get("jobs", {}).get("config-drift-detection", {})
    steps = job.get("steps", [])
    
    found_upload = False
    for step in steps:
        if isinstance(step, dict):
            uses = str(step.get("uses", ""))
            if "upload-artifact" in uses:
                name = str(step.get("with", {}).get("name", "")).lower()
                if "drift" in name or "config" in name:
                    found_upload = True
                    break
    
    assert found_upload, "Must upload drift report artifact (M11)"