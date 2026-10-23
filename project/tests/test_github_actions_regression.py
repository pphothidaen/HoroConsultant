"""project/tests/test_github_actions_regression.py
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
    "ci.yml",
    "cloudflare-worker-monitor.yml",
    "code-review.yml",
    "deploy-render.yml",
    "deploy-vercel.yml",
    "dod-production-gate.yml",
    "gemini-bridge-tests.yml",
    "gitbook-webhook-pr.yml",
    "gitleaks.yml",
    "governance-drift.yml",
    "jira-governance.yml",
    "jira-sync.yml",
    "kaggle_dataset_auto_sync.yml",
    "kaggle_finetune.yml",
    "kaggle_sync.yml",
    "lint.yml",
    "notebooklm_cookie_heartbeat.yml",
    "orchestrator-dispatch.yml",
    "production_monitor.yml",
    "post-deploy-tdd.yml",
    "scheduled_distill_finetune.yml",
    "sync-jira.yml",
    "test_provenance.yml",
    "update-index.yml",
    "workers-aipass.yml",
    "workers-builds.yml",
    "workers-gemini.yml",
    "workers-hermes.yml",
    "workflow-auto-disable.yml",
    "workflow-mttr-monitor.yml",
]

# Archived (retired) workflows — still governed but moved to _archive/
ARCHIVED_WORKFLOW_FILES = [
    "azure_cost_guard.yml",
    "azure_deploy.yml",
    "deploy.yml",
    "fly_deploy.yml",
    "hf_backend_deploy.yml",
]

FROZEN_RELEASE_WORKFLOWS = (
    "azure_cost_guard.yml",
    "azure_deploy.yml",
    "deploy.yml",
    "fly_deploy.yml",
    "hf_backend_deploy.yml",
)


def _load_workflow(filename: str) -> dict[str, Any]:
    """Load one workflow without YAML 1.1 coercing the ``on`` key.
    Checks active workflows first, then _archive/ for retired workflows.
    """
    filepath = WORKFLOWS_DIR / filename
    if not filepath.exists():
        # Try _archive/ for retired workflows
        filepath = WORKFLOWS_DIR / "_archive" / filename
    assert filepath.exists(), f"Workflow file {filename} does not exist in {WORKFLOWS_DIR} or {WORKFLOWS_DIR}/_archive/"
    parsed = yaml.load(filepath.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    assert isinstance(parsed, dict), f"Workflow {filename} did not parse into a dictionary"
    return parsed


def _load_all_workflows() -> dict[str, dict[str, Any]]:
    """Load and parse all workflow YAML files (active + archived)."""
    workflows = {}
    for filename in EXPECTED_WORKFLOW_FILES + ARCHIVED_WORKFLOW_FILES:
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
        """Ensure no 0-byte or corrupted workflow files exist (active + archived)."""
        workflow_files = (
            list(WORKFLOWS_DIR.glob("*.yml")) + list(WORKFLOWS_DIR.glob("*.yaml")) +
            list((WORKFLOWS_DIR / "_archive").glob("*.yml")) + list((WORKFLOWS_DIR / "_archive").glob("*.yaml"))
        )
        expected_all = set(EXPECTED_WORKFLOW_FILES) | set(ARCHIVED_WORKFLOW_FILES)
        assert {path.name for path in workflow_files} == expected_all
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
            "hf_backend_deploy.yml": {},
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
                set(),
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


class TestSpecificWorkflowsIntegrity:
    """Test critical workflows for required steps, actions, and conventions."""

    def test_ai_agent_ecosystem_sync_workflow(self):
        """ai_agent_ecosystem_sync.yml must run scripts/sync_ai_agent_ecosystem.py --check."""
        content = (WORKFLOWS_DIR / "ai_agent_ecosystem_sync.yml").read_text(encoding="utf-8")
        # Verify actions are pinned to immutable SHA-256 (KAN-291 M1)
        import re
        sha_pinned_checkout = re.search(r'actions/checkout@[0-9a-f]{40}', content)
        sha_pinned_setup_python = re.search(r'actions/setup-python@[0-9a-f]{40}', content)
        assert sha_pinned_checkout, "actions/checkout must be pinned to 40-hex SHA"
        assert sha_pinned_setup_python, "actions/setup-python must be pinned to 40-hex SHA"
        assert "scripts/sync_ai_agent_ecosystem.py --check" in content

    def test_hf_backend_deploy_workflow(self):
        """Hugging Face Docker backend deployment is permanently retired as a tombstone (archived)."""
        workflow = _load_workflow("hf_backend_deploy.yml")
        content = yaml.dump(workflow, Dumper=yaml.Dumper)
        assert "[RETIRED]" in content
        assert "permanently retired" in content
        assert "runs-on: ubuntu-latest" in content

    def test_update_index_workflow_is_deterministic(self):
        """update-index.yml must not use non-deterministic datetime timestamps."""
        content = (WORKFLOWS_DIR / "update-index.yml").read_text(encoding="utf-8")
        assert "datetime.utcnow()" not in content

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
        # Verify actions are pinned to immutable SHA-256 (KAN-291 M1)
        import re
        assert re.search(r'actions/upload-artifact@[0-9a-f]{40}', content), "actions/upload-artifact must be pinned to 40-hex SHA"
        assert re.search(r'actions/download-artifact@[0-9a-f]{40}', content), "actions/download-artifact must be pinned to 40-hex SHA"

    def test_production_monitor_workflow(self):
        """The monitor is a GET-only exact-identity audit of Render Docker and Vercel."""
        content = (WORKFLOWS_DIR / "production_monitor.yml").read_text(
            encoding="utf-8"
        )
        workflow = _load_workflow("production_monitor.yml")
        job = workflow["jobs"]["monitor"]

        assert workflow["permissions"] == {"contents": "read"}
        assert job["env"] == {
            "RENDER_BACKEND_URL": "https://horoconsultant-core-backend.onrender.com",
            "VERCEL_STATIC_URL": "https://horo-consultant-psi.vercel.app",
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

    def test_gitbook_webhook_pr_workflow(self):
        """gitbook-webhook-pr.yml must contain webhook signature verification and job gating."""
        workflow = _load_workflow("gitbook-webhook-pr.yml")
        content = (WORKFLOWS_DIR / "gitbook-webhook-pr.yml").read_text(encoding="utf-8")

        assert "GITHUB_TOKEN" in content
        assert "GITBOOK_WEBHOOK_SECRET" in content
        assert "hmac.compare_digest" in content
        assert "sha256=" in content

        job_names = set(workflow["jobs"].keys())
        assert "validate" in job_names
        assert "merge" in job_names
        assert workflow["jobs"]["merge"]["needs"] == ["validate"]

    def test_deploy_render_workflow(self):
        """deploy-render.yml must be a clean CD workflow for the Render backend."""
        workflow = _load_workflow("deploy-render.yml")
        content = (WORKFLOWS_DIR / "deploy-render.yml").read_text(encoding="utf-8")

        assert workflow["permissions"] == {"contents": "read"}
        assert "RENDER_API_KEY" in content
        assert "RENDER_SERVICE_ID" in content
        assert "render.com/deploy" in content
        assert "github.actions/workflow_run" in content

    def test_code_review_workflow(self):
        """code-review.yml must execute the code reviewer agent."""
        content = (WORKFLOWS_DIR / "code-review.yml").read_text(encoding="utf-8")
        assert "project/core/code_reviewer.py" in content
        assert "CODE_REVIEWER_PROMPT" in content

    def test_lint_workflow(self):
        """lint.yml must execute gitleaks and ruff."""
        workflow = _load_workflow("lint.yml")
        content = (WORKFLOWS_DIR / "lint.yml").read_text(encoding="utf-8")
        assert "gitleaks" in content
        assert "ruff" in content

    def test_gemini_bridge_tests_workflow(self):
        """gemini-bridge-tests.yml must execute the bridge test suite."""
        workflow = _load_workflow("gemini-bridge-tests.yml")
        content = (WORKFLOWS_DIR / "gemini-bridge-tests.yml").read_text(encoding="utf-8")
        assert "gemini-web-bridge" in content
        assert "pytest" in content

    def test_scheduled_distill_finetune_workflow(self):
        """scheduled_distill_finetune.yml must have weekly schedule and run distillation."""
        workflow = _load_workflow("scheduled_distill_finetune.yml")
        content = (WORKFLOWS_DIR / "scheduled_distill_finetune.yml").read_text(encoding="utf-8")
        assert "cron" in content
        assert "distill" in content.lower() or "finetune" in content.lower()


class TestGitHubActionsSecretsConventions:
    """Test that secrets follow Doppler 1st Priority convention (no hardcoded secrets)."""

    @pytest.mark.parametrize("workflow_name", EXPECTED_WORKFLOW_FILES)
    def test_no_hardcoded_secrets_in_workflow(self, workflow_name: str):
        """No workflow should contain hardcoded secret values."""
        content = (WORKFLOWS_DIR / workflow_name).read_text(encoding="utf-8")
        lines = content.splitlines()
        for i, line in enumerate(lines, 1):
            if re.search(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*[\"']?[a-zA-Z0-9_\-]{20,}[\"']?", line):
                if "${{" not in line and "env." not in line:
                    pytest.fail(f"Potential hardcoded secret in {workflow_name}:{i}: {line.strip()}")


class TestGitHubActionsJobDependencies:
    """Test job dependency (needs:) integrity across workflows."""

    @pytest.mark.parametrize("workflow_name", EXPECTED_WORKFLOW_FILES)
    def test_job_needs_references_exist(self, workflow_name: str):
        """Every job's needs: must reference existing jobs."""
        workflow = _load_workflow(workflow_name)
        job_names = set(workflow["jobs"].keys())
        for job_id, job in workflow["jobs"].items():
            needs = job.get("needs")
            if needs:
                if isinstance(needs, str):
                    needs = [needs]
                for dep in needs:
                    assert dep in job_names, f"Job '{job_id}' in {workflow_name} needs non-existent job '{dep}'"


class TestScriptInvocationValidity:
    """Test that script invocations in workflows exist and are syntactically valid Python."""

    @pytest.mark.parametrize("workflow_name", EXPECTED_WORKFLOW_FILES)
    def test_python_scripts_exist_and_compile(self, workflow_name: str):
        """Every `python ... .py` invocation must point to an existing, compilable file."""
        content = (WORKFLOWS_DIR / workflow_name).read_text(encoding="utf-8")
        # Find all python script invocations
        script_paths = re.findall(r"python3?\s+([\w/.-]+\.py)", content)
        for script_path in script_paths:
            full_path = ROOT_DIR / script_path
            assert full_path.exists(), f"Script {script_path} referenced in {workflow_name} does not exist"
            try:
                py_compile.compile(full_path.read_text(encoding="utf-8"), doraise=True)
            except py_compile.PyCompileError as e:
                pytest.fail(f"Script {script_path} in {workflow_name} has syntax error: {e}")

