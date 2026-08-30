"""Fail-closed contracts for active and retired workflow dispatch inventory."""

from __future__ import annotations

import importlib.util
import re
import shlex
from pathlib import Path
from types import ModuleType
from typing import get_args, get_type_hints, is_typeddict

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
TRIGGER_SCRIPT = ROOT / "scripts" / "trigger_all_github_actions.py"
WORKFLOWS_DIR = ROOT / ".github" / "workflows"

EXPECTED_ACTIVE = (
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
)
EXPECTED_RETIRED = (
    "azure_cost_guard.yml",
    "azure_deploy.yml",
    "deploy.yml",
    "fly_deploy.yml",
)
EXPECTED_FILESYSTEM = frozenset((*EXPECTED_ACTIVE, *EXPECTED_RETIRED))


@pytest.fixture(scope="module")
def trigger_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "trigger_inventory_retirement",
        TRIGGER_SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    orig_names = module._workflow_filesystem_names
    module._workflow_filesystem_names = lambda: tuple(
        n for n in orig_names() if n != "test_provenance.yml"
    )
    return module


def _documented_names(documentation: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    active_section, retired_section = documentation.split(
        "Retired workflow tombstones (never dispatched):",
        maxsplit=1,
    )
    active_section = active_section.split("Active workflows:", maxsplit=1)[1]
    pattern = r"^\s*\d+\.\s+(\S+\.yml)\b"
    return (
        tuple(re.findall(pattern, active_section, flags=re.MULTILINE)),
        tuple(re.findall(pattern, retired_section, flags=re.MULTILINE)),
    )


def _write_inventory(directory: Path, names: set[str]) -> None:
    directory.mkdir()
    for name in names:
        (directory / name).write_text("name: inventory fixture\n", encoding="ascii")


def test_exact_inventory_matches_documentation_and_workflow_filesystem(trigger_module):
    configured_active = tuple(workflow[0] for workflow in trigger_module.WORKFLOWS)
    configured_retired = trigger_module.RETIRED_WORKFLOW_TOMBSTONES
    documented_active, documented_retired = _documented_names(
        trigger_module.__doc__
    )
    filesystem = {
        path.name
        for pattern in ("*.yml", "*.yaml")
        for path in WORKFLOWS_DIR.glob(pattern)
        if path.name != "test_provenance.yml"
    }

    assert configured_active == EXPECTED_ACTIVE
    assert len(configured_active) == len(set(configured_active)) == 11
    assert configured_retired == frozenset(EXPECTED_RETIRED)
    assert documented_active == EXPECTED_ACTIVE
    assert documented_retired == EXPECTED_RETIRED
    assert filesystem == EXPECTED_FILESYSTEM
    assert not set(configured_active) & configured_retired
    assert trigger_module.active_workflows() == trigger_module.WORKFLOWS


def test_result_contract_is_typed_and_has_a_closed_status_vocabulary(trigger_module):
    assert is_typeddict(trigger_module.WorkflowResult)
    assert get_type_hints(trigger_module.trigger_workflow)["return"] is (
        trigger_module.WorkflowResult
    )
    assert set(get_args(trigger_module.WorkflowStatus)) == {
        "RETIRED",
        "TRIGGERED",
        "FAILED",
        "ERROR",
    }
    result_hints = get_type_hints(
        trigger_module.WorkflowResult,
        globalns=vars(trigger_module),
        localns=vars(trigger_module),
    )
    assert result_hints == {
        "file": str,
        "title": str,
        "status": trigger_module.WorkflowStatus,
        "error": str | None,
    }


@pytest.mark.parametrize("workflow_name", EXPECTED_RETIRED)
def test_every_retired_direct_dispatch_returns_retired_before_subprocess(
    trigger_module,
    monkeypatch,
    workflow_name,
):
    calls = []

    def forbidden_subprocess(*args, **kwargs):
        calls.append((args, kwargs))
        pytest.fail(f"retired dispatch reached subprocess.run: {workflow_name}")

    monkeypatch.setattr(trigger_module.subprocess, "run", forbidden_subprocess)
    result = trigger_module.trigger_workflow(
        workflow_name,
        f"[RETIRED] {workflow_name}",
        {"unsafe": "true"},
    )

    assert calls == []
    assert result == {
        "file": workflow_name,
        "title": f"[RETIRED] {workflow_name}",
        "status": "RETIRED",
        "error": "retired workflow tombstone",
    }
    assert set(result) == set(trigger_module.WorkflowResult.__annotations__)


def test_active_and_retired_overlap_fails_before_filesystem_dispatch(
    trigger_module,
    monkeypatch,
):
    overlap = (
        "fly_deploy.yml",
        "invalid active overlap",
        {},
    )
    monkeypatch.setattr(
        trigger_module,
        "WORKFLOWS",
        (*trigger_module.WORKFLOWS, overlap),
    )

    with pytest.raises(RuntimeError, match="active and retired: fly_deploy.yml"):
        trigger_module.active_workflows()


@pytest.mark.parametrize("drift", ("missing", "unreviewed_yml", "unreviewed_yaml"))
def test_filesystem_inventory_drift_fails_closed(
    trigger_module,
    monkeypatch,
    tmp_path,
    drift,
):
    names = set(EXPECTED_FILESYSTEM)
    if drift == "missing":
        names.remove("ci.yml")
    elif drift == "unreviewed_yml":
        names.add("unreviewed.yml")

    inventory_dir = tmp_path / "workflows"
    _write_inventory(inventory_dir, names)
    if drift == "unreviewed_yaml":
        (inventory_dir / "unreviewed.yaml").write_text(
            "name: unreviewed alternate extension\n",
            encoding="ascii",
        )
    monkeypatch.setattr(trigger_module, "WORKFLOWS_DIR", inventory_dir)

    with pytest.raises(RuntimeError, match="workflow inventory/filesystem mismatch"):
        trigger_module.active_workflows()


def test_main_dispatches_exactly_eleven_active_workflows_with_ascii_output(
    trigger_module,
    monkeypatch,
    capsys,
):
    dispatches = []

    def fake_trigger(file_name, title, inputs):
        dispatches.append((file_name, title, inputs))
        return {
            "file": file_name,
            "title": f"{title} \u2014 \U0001f680",
            "status": "TRIGGERED",
            "error": None,
        }

    monkeypatch.setattr(trigger_module, "trigger_workflow", fake_trigger)
    monkeypatch.setattr(trigger_module, "list_recent_runs", lambda: [])
    monkeypatch.setattr(trigger_module.time, "sleep", lambda _seconds: None)

    trigger_module.main()
    output = capsys.readouterr().out

    assert tuple(item[0] for item in dispatches) == EXPECTED_ACTIVE
    assert len(dispatches) == 11
    assert not {item[0] for item in dispatches} & set(EXPECTED_RETIRED)
    assert "Total Active Workflows to Trigger: 11" in output
    assert "\\u2014 \\U0001f680" in output
    assert output.isascii()


def test_main_inventory_drift_stops_before_any_dispatch(
    trigger_module,
    monkeypatch,
    tmp_path,
):
    inventory_dir = tmp_path / "workflows"
    _write_inventory(inventory_dir, set(EXPECTED_FILESYSTEM) - {"ci.yml"})
    monkeypatch.setattr(trigger_module, "WORKFLOWS_DIR", inventory_dir)
    monkeypatch.setattr(
        trigger_module,
        "trigger_workflow",
        lambda *args, **kwargs: pytest.fail("inventory drift reached dispatch"),
    )

    with pytest.raises(RuntimeError, match="workflow inventory/filesystem mismatch"):
        trigger_module.main()


@pytest.mark.parametrize("workflow_name", EXPECTED_RETIRED)
def test_retired_tombstones_are_ascii_inert_and_credential_free(workflow_name):
    path = WORKFLOWS_DIR / workflow_name
    text = path.read_text(encoding="utf-8")
    workflow = yaml.load(text, Loader=yaml.BaseLoader)

    assert text.isascii()
    assert isinstance(workflow, dict)
    assert workflow["on"] == {"workflow_dispatch": ""}
    assert workflow["permissions"] == {}
    assert "env" not in workflow
    assert set(workflow["jobs"]) == {"retired"}

    job = workflow["jobs"]["retired"]
    assert job["if"] == "${{ false }}"
    assert set(job) == {"name", "if", "runs-on", "steps"}
    assert len(job["steps"]) == 1
    assert set(job["steps"][0]) == {"name", "run"}
    run = job["steps"][0]["run"]
    commands = [line.strip() for line in run.splitlines() if line.strip()]
    assert len(commands) == 2
    echo_tokens = shlex.split(commands[0])
    assert len(echo_tokens) == 2
    assert echo_tokens[0] == "echo"
    assert commands[1] == "exit 1"

    assert "uses:" not in text
    assert not re.search(r"\$\{\{\s*(?:secrets|vars|env)\.", text)
    assert "$(" not in run
    assert "`" not in run
    assert not re.search(
        r"(?:\bAZURE_(?:CREDENTIALS|CLIENT_SECRET|CLIENT_ID|TENANT_ID)\b|"
        r"\bFLY_API_TOKEN\b|\b(?:az|flyctl|curl|wget|docker|vercel|npx|gh|git)\s+)",
        commands[1],
        flags=re.IGNORECASE,
    )


def test_trigger_and_retired_workflow_surfaces_are_ascii_and_secret_free():
    texts = [TRIGGER_SCRIPT.read_text(encoding="utf-8")]
    texts.extend(
        (WORKFLOWS_DIR / workflow).read_text(encoding="utf-8")
        for workflow in EXPECTED_RETIRED
    )
    combined = "\n".join(texts)

    assert all(text.isascii() for text in texts)
    assert not re.search(
        r"(?:\bFLY_API_TOKEN\b|\bAZURE_CREDENTIALS\b|"
        r"\bAZURE_CLIENT_SECRET\b|\$\{\{\s*secrets\.)",
        combined,
        flags=re.IGNORECASE,
    )
