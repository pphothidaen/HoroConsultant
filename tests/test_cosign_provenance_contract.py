"""Contract test: cosign SLSA provenance for version.json (KAN-292).

M2/M10 of Phase 0 Foundation Hardening (KAN-290, Epic KAN-289).

Red Team CRITICAL-2: provenance enforcement gaps — builds and artifacts can be
tampered without detection. M10: artifact integrity verification via signatures.
This test freezes the contract: CI MUST sign version.json with cosign and
deploy-render.yml MUST verify the signature before deploying.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
CI_YML = ROOT / ".github" / "workflows" / "ci.yml"
DEPLOY_YML = ROOT / ".github" / "workflows" / "deploy-render.yml"

COSIGN_INSTALL_RE = re.compile(
    r"^sigstore/cosign-installer@[0-9a-f]{40}(?:\s+#.*)?$"
)
COSIGN_SIGN_RE = re.compile(r"cosign\s+sign(?:-blob)?\b")
COSIGN_VERIFY_RE = re.compile(r"cosign\s+verify(?:-blob)?\b")


def _load(path: Path) -> dict:
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(doc, dict)
    return doc


def _find_step_with_uses(workflow: dict, pattern: re.Pattern) -> list[dict]:
    """Find all steps where `uses` matches the pattern."""
    found: list[dict] = []
    for job_name, job in workflow.get("jobs", {}).items():
        for step in job.get("steps", []):
            if isinstance(step, dict) and pattern.match(str(step.get("uses", ""))):
                found.append({"job": job_name, "step": step})
    return found


def _find_run_commands(workflow: dict, pattern: re.Pattern) -> list[dict]:
    """Find all `run` steps matching the pattern."""
    found: list[dict] = []
    for job_name, job in workflow.get("jobs", {}).items():
        for step in job.get("steps", []):
            if isinstance(step, dict) and pattern.search(step.get("run", "")):
                found.append({"job": job_name, "step": step})
    return found


# ── ci.yml: sign version.json ────────────────────────────────────────────

def test_ci_yml_installs_cosign() -> None:
    ci = _load(CI_YML)
    installs = _find_step_with_uses(ci, COSIGN_INSTALL_RE)
    assert installs, (
        "ci.yml must install cosign via sigstore/cosign-installer pinned to SHA "
        "(M2/M10)"
    )
    assert len(installs) >= 1


def test_ci_yml_signs_version_json() -> None:
    ci = _load(CI_YML)
    signs = _find_run_commands(ci, COSIGN_SIGN_RE)
    assert signs, (
        "ci.yml must run 'cosign sign-blob' or 'cosign sign' on version.json "
        "after stamping (M2/M10). Found run commands: "
        f"{[s['step'].get('run', '')[:80] for s in _find_run_commands(ci, re.compile(r'cosign'))]}"
    )


def test_ci_yml_uploads_signature_artifact() -> None:
    ci = _load(CI_YML)
    uploads = _find_step_with_uses(ci, re.compile(
        r"^actions/upload-artifact@[0-9a-f]{40}(?:\s+#.*)?$"
    ))
    # Must have an upload for version.json + signature (or combined)
    sig_uploads = [
        u for u in uploads
        if "version" in str(u["step"].get("with", {}).get("path", "")).lower()
        or "sig" in str(u["step"].get("with", {}).get("path", "")).lower()
        or "cosign" in str(u["step"].get("name", "")).lower()
    ]
    assert sig_uploads, (
        "ci.yml must upload version.json signature artifact via "
        "actions/upload-artifact (M2/M10)"
    )


# ── deploy-render.yml: verify signature ──────────────────────────────────

def test_deploy_render_verifies_cosign_signature() -> None:
    deploy = _load(DEPLOY_YML)
    verifies = _find_run_commands(deploy, COSIGN_VERIFY_RE)
    assert verifies, (
        "deploy-render.yml must run 'cosign verify-blob' or 'cosign verify' "
        "on version.json before triggering Render deploy (M2/M10)"
    )


def test_deploy_render_verifies_before_deploy() -> None:
    deploy = _load(DEPLOY_YML)
    jobs = deploy.get("jobs", {})
    for job_name, job in jobs.items():
        steps = job.get("steps", [])
        verify_idx = None
        deploy_idx = None
        for idx, step in enumerate(steps):
            if isinstance(step, dict):
                run = step.get("run", "")
                if COSIGN_VERIFY_RE.search(run):
                    verify_idx = idx
                if "Trigger Render deploy" in str(step.get("name", "")) or \
                   "curl.*api.render.com.*deploys" in run:
                    deploy_idx = idx
        if verify_idx is not None and deploy_idx is not None:
            assert verify_idx < deploy_idx, (
                f"{job_name}: cosign verify must run BEFORE Render deploy trigger"
            )
            return
    pytest.fail("deploy-render.yml: cosign verify step not found before deploy step")


# ── key management ───────────────────────────────────────────────────────

def test_github_secret_for_cosign_public_key_exists() -> None:
    """The COSIGN_PUBLIC_KEY secret must be configured in repo settings.

    This is a runtime check; we only verify the workflow references it.
    """
    deploy = _load(DEPLOY_YML)
    for job in deploy.get("jobs", {}).values():
        for step in job.get("steps", []):
            if isinstance(step, dict):
                env = step.get("env", {})
                for val in env.values():
                    if "COSIGN_PUBLIC_KEY" in str(val):
                        return
    pytest.fail(
        "deploy-render.yml must reference COSIGN_PUBLIC_KEY from secrets "
        "(M2/M10 key management)"
    )


def test_ci_yml_references_cosign_private_key() -> None:
    """CI must reference COSIGN_PRIVATE_KEY (or COSIGN_KEY) for signing."""
    ci = _load(CI_YML)
    for job in ci.get("jobs", {}).values():
        for step in job.get("steps", []):
            if isinstance(step, dict):
                env = step.get("env", {})
                for val in env.values():
                    if "COSIGN_PRIVATE_KEY" in str(val) or "COSIGN_KEY" in str(val):
                        return
    pytest.fail(
        "ci.yml must reference COSIGN_PRIVATE_KEY or COSIGN_KEY from secrets "
        "for signing version.json (M2/M10 key management)"
    )