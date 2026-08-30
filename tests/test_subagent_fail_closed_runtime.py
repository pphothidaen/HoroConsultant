from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.multiagent_prompt_command as command


RUNTIME_CONFIG = ROOT / ".agents/config/multiagent_prompt_command.runtime-readonly-v2.yaml"
MODEL_POLICY = ROOT / ".agents/config/multiagent_model_policy.yaml"


@pytest.fixture(autouse=True)
def _isolated_account_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    account_home = tmp_path / ".codex-one"
    account_home.mkdir(mode=0o700)
    account_home.chmod(0o700)


def _policy() -> dict[str, Any]:
    return dict(command.load_model_policy(MODEL_POLICY))


def _decision(**overrides: object) -> dict[str, object]:
    decision: dict[str, object] = {
        "schema_version": 1,
        "ticket": "TICKET-SUBAGENT-FAIL-CLOSED-20260828",
        "phase": "implementation",
        "scope_rank": 1,
        "complexity_rank": 1,
        "risk_rank": 1,
        "ambiguity_rank": 1,
        "evidence_burden_rank": 1,
        "quota_band": "healthy",
        "work_mode": "mutation",
        "selected_alias": "codex1",
        "selected_model": "gpt-5.6-luna",
        "selected_effort": "medium",
        "rationale": "bounded local fail-closed acceptance test",
        "policy_version": _policy()["policy_version"],
        "planning_to_medium_confirmed": True,
        "hitl_approved": False,
    }
    decision.update(overrides)
    return decision


def _snapshot() -> dict[str, object]:
    return {
        "schema_version": 1,
        "tickets": [
            {
                "ticket_id": "TICKET-SUBAGENT-FAIL-CLOSED-20260828",
                "severity": "CRITICAL",
                "work_effort": "S",
                "status": "READY",
                "dependencies": [],
                "blockers": [],
                "owner": "developer",
                "ownership": [command.DEFAULT_OWNERSHIP],
                "quota_passed": True,
                "hitl_passed": True,
                "rule18_decision_valid": True,
            }
        ],
        "reservations": [],
    }


def _write_yaml(path: Path, value: object) -> Path:
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
    return path


def _config(
    tmp_path: Path,
    *,
    activation: dict[str, object],
    provider_state: bool = True,
) -> Path:
    config: dict[str, object] = {
        "runtime": {"approved_for_execution": True, "protocol_version": 2},
        "accounts": {
            "codex1": {
                "cli": "codex",
                "command": "codex",
                "home_env": "CODEX_HOME",
                "home_path": "${HOME}/.codex-one",
            }
        },
        "roles": {
            "developer": {
                "alias": "codex1",
                "cli": "codex",
                "model": "gpt-5.6-luna",
                "effort": "medium",
                "sandbox": "workspace-write",
            }
        },
    }
    config.update(activation)
    if provider_state:
        config["provider_account_state"] = {
            "providers": {"codex": {"state": "healthy"}},
            "accounts": {"codex1": {"state": "healthy"}},
        }
    return _write_yaml(tmp_path / "routes.yaml", config)


def _execute_args(
    tmp_path: Path,
    config_path: Path,
    *,
    decision: dict[str, object] | None = None,
) -> list[str]:
    decision_path = tmp_path / "decision.yaml"
    snapshot_path = tmp_path / "snapshot.yaml"
    _write_yaml(decision_path, decision or _decision())
    _write_yaml(snapshot_path, _snapshot())
    return [
        "--config",
        str(config_path),
        "--role",
        "developer",
        "--objective",
        "Exercise the local fail-closed boundary",
        "--project-dir",
        str(tmp_path),
        "--decision",
        str(decision_path),
        "--policy",
        str(MODEL_POLICY),
        "--scheduling-snapshot",
        str(snapshot_path),
        "--execute",
    ]


def _json_documents(value: str) -> list[dict[str, Any]]:
    decoder = json.JSONDecoder()
    documents: list[dict[str, Any]] = []
    offset = 0
    while value[offset:].strip():
        offset += len(value[offset:]) - len(value[offset:].lstrip())
        document, offset = decoder.raw_decode(value, offset)
        assert isinstance(document, dict)
        documents.append(document)
    return documents


def _forbid_admission(*_args: object, **_kwargs: object) -> object:
    pytest.fail("capacity admission was reached")


def _forbid_lease(*_args: object, **_kwargs: object) -> object:
    pytest.fail("capacity lease acquisition was reached")


def _forbid_spawn(*_args: object, **_kwargs: object) -> object:
    pytest.fail("subprocess creation was reached")


def test_checked_in_runtime_config_is_explicitly_closed_without_provider_state() -> None:
    config = yaml.safe_load(RUNTIME_CONFIG.read_text(encoding="utf-8"))

    assert config["activation_prohibited"] is True
    assert config["dispatcher_execution"] == "CLOSED"
    assert "provider_account_state" not in config
    assert "dispatch_state" not in config
    assert config["runtime"]["approved_for_execution"] is True


@pytest.mark.parametrize(
    "activation",
    [
        pytest.param({}, id="missing-both"),
        pytest.param({"activation_prohibited": False}, id="missing-execution-state"),
        pytest.param({"dispatcher_execution": "OPEN"}, id="missing-prohibition-state"),
        pytest.param(
            {"activation_prohibited": 0, "dispatcher_execution": "OPEN"},
            id="integer-prohibition-state",
        ),
        pytest.param(
            {"activation_prohibited": "false", "dispatcher_execution": "OPEN"},
            id="string-prohibition-state",
        ),
        pytest.param(
            {"activation_prohibited": False, "dispatcher_execution": None},
            id="null-execution-state",
        ),
        pytest.param(
            {"activation_prohibited": False, "dispatcher_execution": "open"},
            id="lowercase-execution-state",
        ),
        pytest.param(
            {"activation_prohibited": False, "dispatcher_execution": 1},
            id="integer-execution-state",
        ),
    ],
)
def test_invalid_activation_metadata_blocks_before_admission_or_spawn(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    activation: dict[str, object],
) -> None:
    monkeypatch.setattr(command, "admit_dispatch_capacity", _forbid_admission)
    monkeypatch.setattr(command, "execute_invocation", _forbid_spawn)

    result = command.main(_execute_args(tmp_path, _config(tmp_path, activation=activation)))
    captured = capsys.readouterr()

    assert result == 5
    assert captured.out == ""
    assert captured.err.strip() == "[ERROR] BLOCKED: ACTIVATION_STATE_INVALID"


@pytest.mark.parametrize(
    "activation",
    [
        pytest.param(
            {"activation_prohibited": True, "dispatcher_execution": "CLOSED"},
            id="explicitly-closed",
        ),
        pytest.param(
            {"activation_prohibited": True, "dispatcher_execution": "OPEN"},
            id="explicitly-prohibited",
        ),
        pytest.param(
            {"activation_prohibited": False, "dispatcher_execution": "CLOSED"},
            id="closed-dispatcher",
        ),
    ],
)
def test_explicit_closed_or_prohibited_state_blocks_before_admission_or_spawn(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    activation: dict[str, object],
) -> None:
    monkeypatch.setattr(command, "admit_dispatch_capacity", _forbid_admission)
    monkeypatch.setattr(command, "execute_invocation", _forbid_spawn)

    result = command.main(_execute_args(tmp_path, _config(tmp_path, activation=activation)))
    captured = capsys.readouterr()

    assert result == 5
    assert captured.out == ""
    assert captured.err.strip() == "[ERROR] BLOCKED: ACTIVATION_PROHIBITED"


def test_missing_provider_state_blocks_before_lease_or_subprocess(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(command.capacity, "acquire_lease", _forbid_lease)
    monkeypatch.setattr(command.subprocess, "run", _forbid_spawn)
    config_path = _config(
        tmp_path,
        activation={"activation_prohibited": False, "dispatcher_execution": "OPEN"},
        provider_state=False,
    )

    result = command.main(_execute_args(tmp_path, config_path))
    captured = capsys.readouterr()

    assert result == 5
    assert captured.out == ""
    assert captured.err.strip() == "[ERROR] BLOCKED: PROVIDER_ACCOUNT_STATE_UNKNOWN"
    assert not (tmp_path / ".horo-capacity").exists()


@pytest.mark.parametrize(
    ("decision", "expected_status"),
    [
        pytest.param(
            _decision(
                risk_rank=3,
                selected_model="gpt-5.6-sol",
                selected_effort="high",
                hitl_approved=False,
            ),
            "NEEDS_HITL",
            id="needs-hitl",
        ),
        pytest.param(_decision(unsupported_field="invalid"), "BLOCKED", id="blocked"),
    ],
)
def test_initial_decision_boundary_preserves_typed_status_and_exit_code(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    decision: dict[str, object],
    expected_status: str,
) -> None:
    monkeypatch.setattr(command, "admit_dispatch_capacity", _forbid_admission)
    monkeypatch.setattr(command, "execute_invocation", _forbid_spawn)
    config_path = _config(
        tmp_path,
        activation={"activation_prohibited": True, "dispatcher_execution": "CLOSED"},
    )

    result = command.main(_execute_args(tmp_path, config_path, decision=decision))
    captured = capsys.readouterr()

    assert result == 2
    assert captured.out == ""
    assert captured.err.strip() == f"[ERROR] {expected_status}: DISPATCH_DECISION_INVALID"
    assert "critical risk" not in captured.err
    assert "unsupported_field" not in captured.err


@pytest.mark.parametrize("expected_status", ["NEEDS_HITL", "BLOCKED"])
def test_spawn_decision_boundary_preserves_typed_status_reason_and_exit_code(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    expected_status: str,
) -> None:
    private_detail = "PRIVATE-DISPATCH-DECISION-DETAIL"

    def reject_at_spawn(_invocation: object) -> object:
        raise command.DispatchDecisionError(private_detail, status=expected_status)

    monkeypatch.setattr(command, "execute_invocation", reject_at_spawn)
    config_path = _config(
        tmp_path,
        activation={"activation_prohibited": False, "dispatcher_execution": "OPEN"},
    )

    result = command.main(_execute_args(tmp_path, config_path))
    captured = capsys.readouterr()
    documents = _json_documents(captured.out)

    assert result == 4
    assert len(documents) == 2
    assert documents[1]["status"] == expected_status
    assert documents[1]["execution_evidence"]["failure_class"] == (
        "dispatch-decision-revalidation-failed"
    )
    assert documents[1]["execution_evidence"]["reason_code"] == (
        "DISPATCH_DECISION_INVALID"
    )
    assert captured.err.strip() == f"[ERROR] {expected_status}: DISPATCH_DECISION_INVALID"
    assert private_detail not in captured.out + captured.err
