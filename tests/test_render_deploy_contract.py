"""TDD contract tests for the hardened Render deploy workflow (KAN-131).

Verifies the deploy-render.yml workflow contains the diagnostic, secret-sync,
and failure-capture steps that prevent silent update_failed deploys.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/deploy-render.yml"


@pytest.fixture(scope="module")
def workflow_doc() -> dict:
    text = WORKFLOW.read_text(encoding="utf-8")
    doc = yaml.safe_load(text)
    assert isinstance(doc, dict)
    return doc


def test_workflow_file_exists() -> None:
    assert WORKFLOW.exists(), f"{WORKFLOW} must exist"
    assert WORKFLOW.is_file()


def test_workflow_name_changed() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "production" in text.lower()
    assert "Update failed" not in text


def test_pre_deploy_diagnostics_step_present(workflow_doc: dict) -> None:
    steps = _job_steps(workflow_doc)
    names = [s.get("name", "") for s in steps]
    assert "Pre-deploy diagnostics — verify Render service exists" in names


def test_doppler_secret_sync_step_present(workflow_doc: dict) -> None:
    steps = _job_steps(workflow_doc)
    names = [s.get("name", "") for s in steps]
    assert "Sync Doppler secrets to Render env vars" in names


def test_failure_diagnostics_step_present(workflow_doc: dict) -> None:
    steps = _job_steps(workflow_doc)
    names = [s.get("name", "") for s in steps]
    assert "Capture deploy diagnostics on failure" in names


def test_doppler_fallback_in_env_keys(workflow_doc: dict) -> None:
    """Every RENDER_API_KEY reference should fall back to RENDER_TOKEN."""
    text = WORKFLOW.read_text(encoding="utf-8")
    # Count occurrences of the fallback pattern
    fallback_count = text.count("secrets.RENDER_API_KEY || secrets.RENDER_TOKEN")
    assert fallback_count >= 3, (
        f"Expected at least 3 Doppler fallback references, found {fallback_count}"
    )


def test_deploy_record_fetch_on_failure(workflow_doc: dict) -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "Fetch full deploy record for diagnostics" in text
    assert "deploys/${DEPLOY_ID}" in text


def test_terminal_failure_states_captured(workflow_doc: dict) -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    for state in ("build_failed", "update_failed", "pre_deploy_failed", "canceled"):
        assert state in text


def test_health_check_still_present(workflow_doc: dict) -> None:
    steps = _job_steps(workflow_doc)
    names = [s.get("name", "") for s in steps]
    assert any("Health check" in n for n in names)


def test_vercel_gateway_smoke_test_present(workflow_doc: dict) -> None:
    steps = _job_steps(workflow_doc)
    names = [s.get("name", "") for s in steps]
    assert "Smoke test Vercel gateway to Render primary" in names


def test_workflow_yml_valid() -> None:
    """The workflow file must parse as valid YAML."""
    text = WORKFLOW.read_text(encoding="utf-8")
    doc = yaml.safe_load(text)
    assert doc is not None
    assert "jobs" in doc


def _job_steps(doc: dict) -> list:
    jobs = doc.get("jobs", {})
    assert "deploy-and-verify" in jobs
    return jobs["deploy-and-verify"].get("steps", [])
