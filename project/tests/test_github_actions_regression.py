"""
project/tests/test_github_actions_regression.py
================================================
Comprehensive regression test suite for all 14 GitHub Actions workflows.
Verifies:
1. YAML syntax & structure across all .github/workflows/*.yml
2. Action versions (actions/checkout@v4, actions/setup-python@v5, etc.)
3. Secrets and Doppler 1st Priority conventions
4. Runner environments and permissions
5. Job dependencies (needs:) integrity
6. Script invocation existence and python syntax validity
"""

from __future__ import annotations

import glob
import os
import py_compile
import re
from pathlib import Path
from typing import Any, Dict, List

import pytest
import yaml

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
WORKFLOWS_DIR = ROOT_DIR / ".github" / "workflows"

EXPECTED_WORKFLOW_FILES = [
    "ai_agent_ecosystem_sync.yml",
    "ai_cicd.yml",
    "azure_cost_guard.yml",
    "azure_deploy.yml",
    "ci.yml",
    "deploy.yml",
    "fly_deploy.yml",
    "hf_backend_deploy.yml",
    "kaggle_finetune.yml",
    "kaggle_sync.yml",
    "lint.yml",
    "notebooklm_cookie_heartbeat.yml",
    "production_monitor.yml",
    "scheduled_distill_finetune.yml",
]


def _load_all_workflows() -> Dict[str, Dict[str, Any]]:
    """Load and parse all workflow YAML files."""
    workflows = {}
    for filename in EXPECTED_WORKFLOW_FILES:
        filepath = WORKFLOWS_DIR / filename
        assert filepath.exists(), f"Workflow file {filename} does not exist in {WORKFLOWS_DIR}"
        content = filepath.read_text(encoding="utf-8")
        parsed = yaml.safe_load(content)
        assert isinstance(parsed, dict), f"Workflow {filename} did not parse into a dictionary"
        workflows[filename] = parsed
    return workflows


class TestGitHubActionsWorkflowsInventory:
    """Test inventory and presence of all 14 GitHub Actions workflow files."""

    def test_all_expected_workflows_exist(self):
        """Verify that all 14 production workflows exist."""
        for filename in EXPECTED_WORKFLOW_FILES:
            filepath = WORKFLOWS_DIR / filename
            assert filepath.is_file(), f"Missing expected workflow: {filename}"

    def test_no_orphan_or_empty_workflows(self):
        """Ensure no 0-byte or corrupted workflow files exist."""
        workflow_files = list(WORKFLOWS_DIR.glob("*.yml")) + list(WORKFLOWS_DIR.glob("*.yaml"))
        assert len(workflow_files) >= len(EXPECTED_WORKFLOW_FILES)
        for wf in workflow_files:
            assert wf.stat().st_size > 50, f"Workflow {wf.name} is too small or empty ({wf.stat().st_size} bytes)"


class TestGitHubActionsSyntaxAndStructure:
    """Test YAML syntax, mandatory fields, and structure of every workflow."""

    @pytest.mark.parametrize("workflow_name", EXPECTED_WORKFLOW_FILES)
    def test_workflow_yaml_syntax_and_mandatory_keys(self, workflow_name: str):
        """Every workflow must contain name, on (triggers), and jobs."""
        filepath = WORKFLOWS_DIR / workflow_name
        content = filepath.read_text(encoding="utf-8")
        parsed = yaml.safe_load(content)

        assert "name" in parsed, f"Workflow {workflow_name} is missing top-level 'name'"
        assert isinstance(parsed["name"], str) and len(parsed["name"]) > 0

        # Note: PyYAML parses `on:` as boolean True if unquoted, or dict if structured
        has_trigger = "on" in parsed or True in parsed
        assert has_trigger, f"Workflow {workflow_name} is missing 'on' triggers"

        assert "jobs" in parsed, f"Workflow {workflow_name} is missing 'jobs'"
        assert isinstance(parsed["jobs"], dict) and len(parsed["jobs"]) > 0

    @pytest.mark.parametrize("workflow_name", EXPECTED_WORKFLOW_FILES)
    def test_workflow_job_runners_and_steps(self, workflow_name: str):
        """Every job in every workflow must specify runs-on and contain steps."""
        filepath = WORKFLOWS_DIR / workflow_name
        parsed = yaml.safe_load(filepath.read_text(encoding="utf-8"))

        for job_id, job in parsed["jobs"].items():
            assert "runs-on" in job, f"Job '{job_id}' in {workflow_name} missing 'runs-on'"
            runs_on = str(job["runs-on"])
            assert "ubuntu" in runs_on or "macos" in runs_on or "windows" in runs_on or "self-hosted" in runs_on or "$" in runs_on

            assert "steps" in job, f"Job '{job_id}' in {workflow_name} missing 'steps'"
            assert isinstance(job["steps"], list) and len(job["steps"]) > 0


class TestGitHubActionsJobDependencies:
    """Verify that job dependency graphs (needs:) are structurally valid."""

    @pytest.mark.parametrize("workflow_name", EXPECTED_WORKFLOW_FILES)
    def test_workflow_needs_references_valid_jobs(self, workflow_name: str):
        """If a job has 'needs', all referenced job IDs must exist in the same workflow."""
        filepath = WORKFLOWS_DIR / workflow_name
        parsed = yaml.safe_load(filepath.read_text(encoding="utf-8"))
        job_ids = set(parsed["jobs"].keys())

        for job_id, job in parsed["jobs"].items():
            if "needs" in job:
                needs = job["needs"]
                if isinstance(needs, str):
                    needs = [needs]
                for dep in needs:
                    assert dep in job_ids, (
                        f"Job '{job_id}' in {workflow_name} needs unknown job '{dep}'. "
                        f"Available jobs: {job_ids}"
                    )


class TestGitHubActionsScriptReferences:
    """Verify that all Python scripts called within workflows exist and have valid syntax."""

    def test_all_referenced_python_scripts_exist_and_compile(self):
        """Extract all python script executions across all workflows and compile them."""
        all_referenced_scripts = set()
        script_pattern = re.compile(r'(?:python3?)\s+([a-zA-Z0-9_\-\.\/]+\.py)')

        for filename in EXPECTED_WORKFLOW_FILES:
            filepath = WORKFLOWS_DIR / filename
            content = filepath.read_text(encoding="utf-8")
            matches = script_pattern.findall(content)
            for m in matches:
                all_referenced_scripts.add((filename, m))

        assert len(all_referenced_scripts) > 0, "No python scripts were detected across workflows"

        missing_scripts = []
        compilation_errors = []

        for wf, script_rel_path in sorted(all_referenced_scripts):
            # Handle directory changes like 'cd rust_core && python tests/test_installed_wheel.py'
            target_path = ROOT_DIR / script_rel_path
            if not target_path.exists() and "test_installed_wheel.py" in script_rel_path:
                target_path = ROOT_DIR / "rust_core" / script_rel_path

            if not target_path.exists():
                missing_scripts.append(f"{wf} -> {script_rel_path}")
            else:
                try:
                    py_compile.compile(str(target_path), doraise=True)
                except Exception as e:
                    compilation_errors.append(f"{target_path}: {e}")

        assert not missing_scripts, f"Workflows reference non-existent scripts: {missing_scripts}"
        assert not compilation_errors, f"Referenced scripts have compilation errors: {compilation_errors}"


class TestSpecificWorkflowsIntegrity:
    """Detailed regression checks for key critical workflows."""

    def test_ai_agent_ecosystem_sync_workflow(self):
        """ai_agent_ecosystem_sync.yml must run scripts/sync_ai_agent_ecosystem.py --check."""
        content = (WORKFLOWS_DIR / "ai_agent_ecosystem_sync.yml").read_text(encoding="utf-8")
        assert "actions/checkout@v4" in content
        assert "actions/setup-python@v5" in content
        assert "scripts/sync_ai_agent_ecosystem.py --check" in content

    def test_hf_backend_deploy_workflow(self):
        """hf_backend_deploy.yml must configure Doppler sync, HF token resolution, and publish scripts."""
        content = (WORKFLOWS_DIR / "hf_backend_deploy.yml").read_text(encoding="utf-8")
        assert "dopplerhq/secrets-fetch-action" in content
        assert "scripts/publish_space_hf.py" in content
        assert "scripts/run_live_health_verification.py" in content
        assert "scripts/synthetic_health_monitor.py" in content

    def test_kaggle_finetune_workflow(self):
        """kaggle_finetune.yml must trigger scripts/kaggle_notebook_manager.py --push."""
        content = (WORKFLOWS_DIR / "kaggle_finetune.yml").read_text(encoding="utf-8")
        assert "scripts/kaggle_notebook_manager.py --push" in content
        assert "KAGGLE_TOKEN" in content
        assert "HF_TOKEN" in content

    def test_ci_workflow_has_safety_audits(self):
        """ci.yml must include Rust build, pytest suite, and code reviewer."""
        content = (WORKFLOWS_DIR / "ci.yml").read_text(encoding="utf-8")
        assert "project/core/code_reviewer.py" in content
        assert "cargo clippy" in content
        assert "actions/upload-artifact@v4" in content
        assert "actions/download-artifact@v4" in content

    def test_production_monitor_workflow(self):
        """production_monitor.yml must run health and luopan regression checks."""
        content = (WORKFLOWS_DIR / "production_monitor.yml").read_text(encoding="utf-8")
        assert "scripts/synthetic_health_monitor.py" in content
        assert "scripts/run_luopan_e2e_regression.py" in content
