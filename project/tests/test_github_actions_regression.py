"""
project/tests/test_github_actions_regression.py
================================================
Comprehensive regression test suite for the complete GitHub Actions inventory.
Verifies:
1. YAML syntax & structure across all .github/workflows/*.yml
2. Action versions (actions/checkout@v4, actions/setup-python@v5, etc.)
3. Secrets and Doppler 1st Priority conventions
4. Runner environments and permissions
5. Job dependencies (needs:) integrity
6. Script invocation existence and python syntax validity
"""

from __future__ import annotations

import py_compile
import re
from pathlib import Path
from typing import Any

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
    "kaggle_dataset_auto_sync.yml",
    "kaggle_finetune.yml",
    "kaggle_sync.yml",
    "lint.yml",
    "notebooklm_cookie_heartbeat.yml",
    "production_monitor.yml",
    "scheduled_distill_finetune.yml",
    "test_provenance.yml",
]

FROZEN_RELEASE_WORKFLOWS = (
    "azure_cost_guard.yml",
    "azure_deploy.yml",
    "deploy.yml",
    "fly_deploy.yml",
    "hf_backend_deploy.yml",
)


def _load_workflow(filename: str) -> dict[str, Any]:
    """Load one workflow without YAML 1.1 coercing the ``on`` key."""
    filepath = WORKFLOWS_DIR / filename
    assert filepath.exists(), f"Workflow file {filename} does not exist in {WORKFLOWS_DIR}"
    parsed = yaml.load(filepath.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    assert isinstance(parsed, dict), f"Workflow {filename} did not parse into a dictionary"
    return parsed


def _load_all_workflows() -> dict[str, dict[str, Any]]:
    """Load and parse all workflow YAML files."""
    workflows = {}
    for filename in EXPECTED_WORKFLOW_FILES:
        workflows[filename] = _load_workflow(filename)
    return workflows


class TestGitHubActionsWorkflowsInventory:
    """Test inventory and presence of every GitHub Actions workflow file."""

    def test_all_expected_workflows_exist(self):
        """Verify that every governed workflow exists."""
        for filename in EXPECTED_WORKFLOW_FILES:
            filepath = WORKFLOWS_DIR / filename
            assert filepath.is_file(), f"Missing expected workflow: {filename}"

    def test_no_orphan_or_empty_workflows(self):
        """Ensure no 0-byte or corrupted workflow files exist."""
        workflow_files = list(WORKFLOWS_DIR.glob("*.yml")) + list(WORKFLOWS_DIR.glob("*.yaml"))
        assert {path.name for path in workflow_files} == set(EXPECTED_WORKFLOW_FILES)
        for wf in workflow_files:
            assert wf.stat().st_size > 50, f"Workflow {wf.name} is too small or empty ({wf.stat().st_size} bytes)"


class TestGitHubActionsSyntaxAndStructure:
    """Test YAML syntax, mandatory fields, and structure of every workflow."""

    @pytest.mark.parametrize("workflow_name", EXPECTED_WORKFLOW_FILES)
    def test_workflow_yaml_syntax_and_mandatory_keys(self, workflow_name: str):
        """Every workflow must contain name, on (triggers), and jobs."""
        parsed = _load_workflow(workflow_name)

        assert "name" in parsed, f"Workflow {workflow_name} is missing top-level 'name'"
        assert isinstance(parsed["name"], str) and len(parsed["name"]) > 0

        assert "on" in parsed, f"Workflow {workflow_name} is missing 'on' triggers"
        assert isinstance(parsed["on"], dict) and parsed["on"]

        assert "jobs" in parsed, f"Workflow {workflow_name} is missing 'jobs'"
        assert isinstance(parsed["jobs"], dict) and len(parsed["jobs"]) > 0

    @pytest.mark.parametrize("workflow_name", EXPECTED_WORKFLOW_FILES)
    def test_workflow_job_runners_and_steps(self, workflow_name: str):
        """Every job in every workflow must specify runs-on and contain steps."""
        parsed = _load_workflow(workflow_name)

        for job_id, job in parsed["jobs"].items():
            assert "runs-on" in job, f"Job '{job_id}' in {workflow_name} missing 'runs-on'"
            runs_on = str(job["runs-on"])
            assert "ubuntu" in runs_on or "macos" in runs_on or "windows" in runs_on or "self-hosted" in runs_on or "$" in runs_on

            assert "steps" in job, f"Job '{job_id}' in {workflow_name} missing 'steps'"
            assert isinstance(job["steps"], list) and len(job["steps"]) > 0


class TestFrozenReleaseWorkflowSecurity:
    """Preserve least privilege and reviewed action identities for release lanes."""

    def test_release_workflow_permissions_are_empty_or_read_only(self):
        expected = {
            "azure_cost_guard.yml": {},
            "azure_deploy.yml": {},
            "deploy.yml": {},
            "fly_deploy.yml": {},
            "hf_backend_deploy.yml": {"contents": "read"},
        }

        for workflow_name in FROZEN_RELEASE_WORKFLOWS:
            workflow = _load_workflow(workflow_name)
            assert workflow["permissions"] == expected[workflow_name]
            for job in workflow["jobs"].values():
                assert "permissions" not in job

    @pytest.mark.parametrize(
        ("workflow_name", "expected_refs"),
        (
            (
                "azure_cost_guard.yml",
                set(),
            ),
            (
                "hf_backend_deploy.yml",
                {
                    "actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683",
                    "dopplerhq/secrets-fetch-action@v1.2.0",
                    "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065",
                    "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
                },
            ),
        ),
    )
    def test_active_release_action_refs_match_the_reviewed_freeze(
        self,
        workflow_name: str,
        expected_refs: set[str],
    ):
        workflow = _load_workflow(workflow_name)
        refs = {
            step["uses"]
            for job in workflow["jobs"].values()
            for step in job["steps"]
            if "uses" in step
        }

        assert refs == expected_refs

    @pytest.mark.parametrize(
        "workflow_name",
        ("azure_deploy.yml", "deploy.yml", "fly_deploy.yml"),
    )
    def test_retired_release_workflows_invoke_no_actions(self, workflow_name: str):
        workflow = _load_workflow(workflow_name)

        assert not any(
            "uses" in step
            for job in workflow["jobs"].values()
            for step in job["steps"]
        )


class TestGitHubActionsJobDependencies:
    """Verify that job dependency graphs (needs:) are structurally valid."""

    @pytest.mark.parametrize("workflow_name", EXPECTED_WORKFLOW_FILES)
    def test_workflow_needs_references_valid_jobs(self, workflow_name: str):
        """If a job has 'needs', all referenced job IDs must exist in the same workflow."""
        parsed = _load_workflow(workflow_name)
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
                except (OSError, py_compile.PyCompileError) as error:
                    compilation_errors.append(f"{target_path}: {error}")

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
        """Docker workflow must publish only HF Docker and verify Vercel static separately."""
        content = (WORKFLOWS_DIR / "hf_backend_deploy.yml").read_text(encoding="utf-8")
        assert "dopplerhq/secrets-fetch-action" in content
        assert "scripts/publish_space_hf.py" in content
        assert "scripts/run_live_health_verification.py" in content
        assert "scripts/synthetic_health_monitor.py" in content
        assert "VERCEL_STATIC_URL" in content
        assert "Enforce Vercel static and HF Docker target separation" in content
        assert "--sdk docker" in content
        assert "--sdk static" not in content
        assert "Publish static frontend" not in content

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
        """The monitor is a GET-only exact-identity audit of HF Docker and Vercel."""
        content = (WORKFLOWS_DIR / "production_monitor.yml").read_text(
            encoding="utf-8"
        )
        workflow = _load_workflow("production_monitor.yml")
        job = workflow["jobs"]["monitor"]

        assert workflow["permissions"] == {"contents": "read"}
        assert job["env"] == {
            "HF_BACKEND_SPACE_ID": "pphothidaen/horoconsultant-core-backend",
            "HF_BACKEND_URL": (
                "https://pphothidaen-horoconsultant-core-backend.hf.space"
            ),
            "VERCEL_STATIC_URL": "https://horo-consultant-psi.vercel.app",
            "HF_STATIC_SPACE_ID": "",
        }

        action_refs = {
            step["uses"] for step in job["steps"] if "uses" in step
        }
        assert action_refs == {
            "actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683",
            "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065",
            "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
        }
        checkout = next(
            step
            for step in job["steps"]
            if step.get("uses", "").startswith("actions/checkout@")
        )
        assert checkout["with"] == {
            "fetch-depth": "0",
            "persist-credentials": "false",
        }

        version_step = next(
            step
            for step in job["steps"]
            if step.get("name") == "Verify exact release identity on backend and UI"
        )
        version_audit = version_step["run"]
        assert 'method="GET"' in version_audit
        assert "object_pairs_hook=reject_duplicate_keys" in version_audit
        assert "committed release metadata mirrors differ" in version_audit
        assert 'if deployed != source:' in version_audit
        assert 'for key in ("commit", "packaging_commit")' in version_audit
        assert "release version and source commit disagree" in version_audit
        assert "hashlib.sha256(canonical).hexdigest()" in version_audit
        assert '["git", "merge-base", "--is-ancestor"' in version_audit
        assert '"packaging_commit": packaging_commit' in version_audit
        assert 'len(report["surfaces"]) != 2' in version_audit
        assert 'report["success"] = True' in version_audit
        assert 'raise SystemExit(0 if report["success"] else 1)' in version_audit
        assert 'report["error_class"] = type(error).__name__' in version_audit
        assert "str(error)" not in version_audit

        assert "scripts/run_live_health_verification.py" in content
        assert "scripts/synthetic_health_monitor.py --dry-run" in content
        assert "scripts/synthetic_health_monitor.py" in content
        assert "scripts/run_luopan_e2e_regression.py" not in content
        assert 'method="POST"' not in content
        assert "${{ secrets." not in content
        assert "${{ vars." not in content
        assert "doppler" not in content.lower()
        assert "azure" not in content.lower()
        assert "fly.io" not in content.lower()
        assert "flyctl" not in content.lower()
        assert "token" not in content.lower()

        upload = next(
            step
            for step in job["steps"]
            if step.get("name") == "Upload sanitized monitor evidence"
        )
        assert upload["if"] == "always()"
        assert upload["with"]["if-no-files-found"] == "warn"
        assert set(upload["with"]["path"].splitlines()) == {
            "production-version-identity.json",
            "production-verification.json",
            "synthetic-health.json",
        }
