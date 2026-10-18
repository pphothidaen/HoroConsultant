"""Contract tests for Vercel DoD Production Gate enforcement (KAN-259).

Ensures that Vercel automatic Git integration deployments are disabled
so that deployments to production cannot bypass the DoD Production Gate.
"""
from __future__ import annotations

import json
from pathlib import Path
import yaml
import pytest

ROOT = Path(__file__).resolve().parents[1]
VERCEL_JSON = ROOT / "vercel.json"
DEPLOY_VERCEL_YML = ROOT / ".github/workflows/deploy-vercel.yml"
DOD_GATE_YML = ROOT / ".github/workflows/dod-production-gate.yml"
WORKERS_BUILDS_YML = ROOT / ".github/workflows/workers-builds.yml"
WRANGLER_TOML = ROOT / "wrangler.toml"


def _read_vercel_config() -> dict:
    assert VERCEL_JSON.is_file(), "vercel.json must exist"
    return json.loads(VERCEL_JSON.read_text(encoding="utf-8"))


def _read_workflow(path: Path) -> dict:
    assert path.is_file(), f"{path} must exist"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if True in data and "on" not in data:
        data["on"] = data[True]
    return data


def test_vercel_git_integration_disabled_in_favor_of_dod_gate():
    """KAN-259: Automatic git deployments must be disabled for all branches including main.

    This ensures Vercel never auto-deploys upon git push, preventing the
    DoD Production Gate from being bypassed.
    """
    config = _read_vercel_config()
    github_config = config.get("github", {})
    assert "deploymentEnabled" in github_config, "github.deploymentEnabled must be configured"
    deploy_enabled = github_config["deploymentEnabled"]
    assert deploy_enabled == {"*": False, "main": False}, (
        f"Expected github.deploymentEnabled to be {{'*': False, 'main': False}}, got {deploy_enabled}"
    )


def test_deploy_vercel_workflow_gated_on_dod_production_gate():
    """KAN-259: deploy-vercel.yml must be triggered by DoD Production Gate."""
    wf = _read_workflow(DEPLOY_VERCEL_YML)
    
    # Check trigger condition
    on_clause = wf.get("on", {})
    assert "workflow_run" in on_clause, "deploy-vercel.yml must trigger on workflow_run"
    assert on_clause["workflow_run"]["workflows"] == ["DoD Production Gate"], (
        "deploy-vercel.yml must be gated specifically on 'DoD Production Gate'"
    )
    assert "completed" in on_clause["workflow_run"]["types"]

    # Check job execution condition
    job = wf["jobs"]["deploy-vercel"]
    job_if = job.get("if", "")
    assert "workflow_run.conclusion == 'success'" in job_if, "deploy-vercel must require success conclusion"
    assert "workflow_run.head_branch == 'main'" in job_if, "deploy-vercel must only deploy main branch"


def test_deploy_vercel_uses_production_flag():
    """KAN-259: deploy-vercel.yml must deploy with --prod --yes."""
    content = DEPLOY_VERCEL_YML.read_text(encoding="utf-8")
    assert "vercel --token=$VERCEL_TOKEN --prod --yes" in content, (
        "deploy-vercel step must run 'vercel --token=$VERCEL_TOKEN --prod --yes'"
    )


def test_workers_builds_points_to_consolidated_worker():
    """KAN-259: Workers configuration must use consolidated project/static/_worker.js."""
    wrangler_content = WRANGLER_TOML.read_text(encoding="utf-8")
    assert 'main = "project/static/_worker.js"' in wrangler_content, (
        "wrangler.toml main entry point must be 'project/static/_worker.js'"
    )
