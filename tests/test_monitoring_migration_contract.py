"""TDD contract tests for the HF→Render monitoring migration (KAN-131).

Verifies that the monitoring scripts prefer RENDER_BACKEND_URL over the
deprecated HF_BACKEND_URL, have a Render default, and reject retired
host suffixes for all roles (not just UI).
"""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HEALTH_MONITOR = ROOT / "scripts/synthetic_health_monitor.py"
LIVE_VERIFY = ROOT / "scripts/run_live_health_verification.py"
MONITOR_WORKFLOW = ROOT / ".github/workflows/production_monitor.yml"


@pytest.fixture(scope="module")
def health_text() -> str:
    return HEALTH_MONITOR.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def verify_text() -> str:
    return LIVE_VERIFY.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def workflow_text() -> str:
    return MONITOR_WORKFLOW.read_text(encoding="utf-8")


# ── synthetic_health_monitor.py ──────────────────────────────────────────

def test_health_monitor_has_render_default(health_text: str) -> None:
    assert "DEFAULT_RENDER_BACKEND_URL" in health_text
    assert "DEFAULT_HF_BACKEND_URL" in health_text  # backward compat


def test_health_monitor_prefers_render_env(health_text: str) -> None:
    """RENDER_BACKEND_URL must be consulted before HF_BACKEND_URL."""
    render_pos = health_text.find("RENDER_BACKEND_URL")
    hf_pos = health_text.find("HF_BACKEND_URL")
    assert render_pos != -1, "RENDER_BACKEND_URL lookup missing"
    assert hf_pos != -1, "HF_BACKEND_URL fallback missing"
    assert render_pos < hf_pos, "RENDER_BACKEND_URL must be checked first"


def test_health_monitor_check_name_updated(health_text: str) -> None:
    assert "Render backend /health" in health_text


def test_health_monitor_no_hf_in_check_names(health_text: str) -> None:
    assert "Hugging Force Docker Backend /health" not in health_text


# ── run_live_health_verification.py ──────────────────────────────────────

def test_verify_has_render_default(verify_text: str) -> None:
    assert "DEFAULT_RENDER_BACKEND_URL" in verify_text


def test_verify_prefers_render_env(verify_text: str) -> None:
    render_pos = verify_text.find("RENDER_BACKEND_URL")
    hf_pos = verify_text.find("HF_BACKEND_URL")
    assert render_pos != -1, "RENDER_BACKEND_URL lookup missing"
    assert hf_pos != -1, "HF_BACKEND_URL fallback missing"
    assert render_pos < hf_pos, "RENDER_BACKEND_URL must be checked first"


def test_verify_rejects_hf_space_for_all_roles(verify_text: str) -> None:
    """RETIRED_HOST_SUFFIXES must include .hf.space (not role-gated)."""
    assert ".hf.space" in verify_text
    # The old role-gated check must be gone
    assert "role == \"ui\" and hostname.endswith" not in verify_text


def test_verify_backend_check_names_updated(verify_text: str) -> None:
    assert "Render backend health" in verify_text
    assert "Render backend version metadata" in verify_text


def test_verify_no_hf_in_check_names(verify_text: str) -> None:
    assert "Hugging Force Docker backend health" not in verify_text
    assert "Hugging Force Docker backend version" not in verify_text


# ── production_monitor.yml ────────────────────────────────────────────────

def test_monitor_env_var_uses_render(workflow_text: str) -> None:
    assert "RENDER_BACKEND_URL:" in workflow_text
    assert "RENDER_BACKEND_URL: https://horoconsultant-core-backend.onrender.com" in workflow_text


def test_monitor_no_hf_env_vars(workflow_text: str) -> None:
    assert "HF_BACKEND_SPACE_ID" not in workflow_text
    assert "HF_STATIC_SPACE_ID" not in workflow_text


def test_monitor_no_hf_urls(workflow_text: str) -> None:
    assert "pphothidaen-horoconsultant-core-backend.hf.space" not in workflow_text


def test_monitor_renders_renders_url(workflow_text: str) -> None:
    assert "horoconsultant-core-backend.onrender.com" in workflow_text


def test_monitor_job_name_updated(workflow_text: str) -> None:
    assert "Verify Render backend and Vercel UI" in workflow_text
    assert "Verify HF Docker backend" not in workflow_text
