"""Fail-closed contracts for the retired Fly deployment artifacts."""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path
from types import ModuleType

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
TRIGGER_SCRIPT = ROOT / "scripts" / "trigger_all_github_actions.py"
FLY_WORKFLOW = ROOT / ".github" / "workflows" / "fly_deploy.yml"

EXPECTED_ACTIVE_WORKFLOW_NAMES = {
    "ai_agent_ecosystem_sync.yml",
    "ai_cicd.yml",
    "ci.yml",
    "hf_backend_deploy.yml",
    "kaggle_dataset_auto_sync.yml",
    "kaggle_finetune.yml",
    "kaggle_sync.yml",
    "lint.yml",
    "notebooklm_cookie_heartbeat.yml",
    "production_monitor.yml",
    "scheduled_distill_finetune.yml",
}
EXPECTED_RETIRED_WORKFLOW_NAMES = {
    "azure_cost_guard.yml",
    "azure_deploy.yml",
    "deploy.yml",
    "fly_deploy.yml",
}


@pytest.fixture(scope="module")
def trigger_module() -> ModuleType:
    """Load the trigger helper without executing its CLI entry point."""
    spec = importlib.util.spec_from_file_location(
        "fly_artifact_retirement_trigger",
        TRIGGER_SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_fly_configuration_is_deleted_but_audit_tombstone_remains():
    assert not (ROOT / "fly.toml").exists()
    assert FLY_WORKFLOW.is_file()

    text = FLY_WORKFLOW.read_text(encoding="utf-8")
    workflow = yaml.load(text, Loader=yaml.BaseLoader)
    assert isinstance(workflow, dict)
    assert workflow["on"] == {"workflow_dispatch": ""}
    assert workflow["permissions"] == {}
    assert set(workflow["jobs"]) == {"retired"}

    job = workflow["jobs"]["retired"]
    assert job["if"] == "${{ false }}"
    assert set(job) == {"name", "if", "runs-on", "steps"}
    assert len(job["steps"]) == 1
    assert set(job["steps"][0]) == {"name", "run"}
    assert [
        line.strip()
        for line in job["steps"][0]["run"].splitlines()
        if line.strip()
    ] == [
        'echo "::error::Fly.io is not an approved HoroConsultant deployment target."',
        "exit 1",
    ]


def test_inventory_has_exactly_eleven_active_and_four_retired_workflows(
    trigger_module,
):
    active = trigger_module.active_workflows()
    active_names = [workflow[0] for workflow in active]
    configured_names = [workflow[0] for workflow in trigger_module.WORKFLOWS]

    assert len(active_names) == 11
    assert len(active_names) == len(set(active_names))
    assert set(active_names) == EXPECTED_ACTIVE_WORKFLOW_NAMES
    assert set(configured_names) == EXPECTED_ACTIVE_WORKFLOW_NAMES
    assert trigger_module.RETIRED_WORKFLOW_TOMBSTONES == frozenset(
        EXPECTED_RETIRED_WORKFLOW_NAMES
    )
    assert not set(active_names) & trigger_module.RETIRED_WORKFLOW_TOMBSTONES


def test_fly_tombstone_returns_typed_retired_before_subprocess(
    trigger_module,
    monkeypatch,
    caplog,
):
    calls = []

    def forbidden_subprocess(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("retired Fly tombstone reached subprocess.run")

    monkeypatch.setattr(trigger_module.subprocess, "run", forbidden_subprocess)
    with caplog.at_level("WARNING", logger="gha_trigger"):
        result = trigger_module.trigger_workflow(
            "fly_deploy.yml",
            "[RETIRED] Fly.io Deployment",
            {"force": "true"},
        )

    assert calls == []
    assert result == {
        "file": "fly_deploy.yml",
        "title": "[RETIRED] Fly.io Deployment",
        "status": "RETIRED",
        "error": "retired workflow tombstone",
    }
    assert all(isinstance(value, str) for value in result.values())
    assert caplog.messages == [
        "[WARNING] Refusing retired workflow tombstone: fly_deploy.yml"
    ]


def test_trigger_cli_output_is_ascii_and_uses_the_active_inventory(
    trigger_module,
    monkeypatch,
    capsys,
):
    dispatched = []

    def fake_trigger(file_name, title, inputs):
        dispatched.append(file_name)
        return {
            "file": file_name,
            "title": title,
            "status": "TRIGGERED",
            "error": None,
        }

    monkeypatch.setattr(trigger_module, "trigger_workflow", fake_trigger)
    monkeypatch.setattr(trigger_module.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(
        trigger_module,
        "list_recent_runs",
        lambda: [
            {
                "status": "queued",
                "workflowName": "Unicode \u2014 \U0001f680",
                "url": "https://example.invalid/caf\u00e9",
            }
        ],
    )

    trigger_module.main()
    output = capsys.readouterr().out

    assert output.isascii()
    assert "Total Active Workflows to Trigger: 11" in output
    assert "fly_deploy.yml" not in output
    assert set(dispatched) == EXPECTED_ACTIVE_WORKFLOW_NAMES
    assert len(dispatched) == 11
    assert "Unicode \\u2014 \\U0001f680" in output
    assert "caf\\xe9" in output


def test_retired_fly_behavior_contains_no_credentials_or_deploy_capability(
    trigger_module,
):
    trigger_text = TRIGGER_SCRIPT.read_text(encoding="utf-8")
    workflow_text = FLY_WORKFLOW.read_text(encoding="utf-8")
    owned_behavior = "\n".join((trigger_text, workflow_text))

    assert trigger_text.isascii()
    assert workflow_text.isascii()
    assert "fly_deploy.yml" not in {
        workflow[0] for workflow in trigger_module.active_workflows()
    }
    assert "uses:" not in workflow_text
    assert "env:" not in workflow_text
    assert not re.search(r"\$\{\{\s*(?:secrets|vars|env)\.", workflow_text)
    assert not re.search(
        r"(?:\bflyctl\b|\bFLY_API_TOKEN\b|\bapi\.fly\.io\b|"
        r"\b[a-z0-9.-]+\.fly\.dev\b|\bsuperfly/|\bfly\.toml\b)",
        owned_behavior,
        flags=re.IGNORECASE,
    )
