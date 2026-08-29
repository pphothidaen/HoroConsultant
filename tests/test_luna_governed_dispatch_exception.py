"""Red contract for the single-use Luna governed-dispatch exception.

The implementation API is deliberately small and public so the source owner has
no design choices left open:

* ``effective_activation_state(config) -> tuple[bool, str]`` returns
  ``(activation_prohibited, dispatcher_execution)`` and defaults to
  ``(True, "CLOSED")`` when either key is absent.
* ``validate_closed_dispatch_exception(...) -> QobsAdmission`` is the only gate
  allowed to admit the exception.  It validates and atomically consumes both the
  QOBS nonce and exception use before any provider process starts.
* ``QobsAdmission`` is an immutable typed value containing the exact QOBS,
  decision, snapshot, route, ticket/attempt, and exception-consumption bindings.

No general dispatcher opening or global decision-schema allowlist is permitted.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import subprocess

import pytest

import scripts.agent_quota_status_guard as quota
import scripts.multiagent_prompt_command as command
import scripts.multiagent_ticket_scheduler as scheduler


ROOT = Path(__file__).resolve().parents[1]
SHARED_CONFIG = ROOT / ".agents/config/multiagent_prompt_command.runtime-readonly-v2.yaml"
EXCEPTION_CONFIG = ROOT / ".agents/config/multiagent_prompt_command.luna-one-shot.yaml"
POLICY_PATH = ROOT / ".agents/config/multiagent_model_policy.yaml"
EXCEPTION_ID = "luna-delegate-001-codex2-attempt-1"
TICKET = "TICKET-LUNA-DELEGATE-001"
NOW = datetime(2026, 8, 28, 12, 0, tzinfo=timezone.utc)
_UNSET = object()


def _signals(remaining: float = 10.0) -> dict[str, object]:
    def values() -> dict[str, object]:
        return {
            "usedPercent": 100.0 - remaining,
            "remainingPercent": remaining,
            "reached": remaining == 0.0,
            "limit": 100.0,
            "spend": 100.0 - remaining,
            "remaining": remaining,
        }

    return {**values(), "buckets": {"primary": values(), "secondary": values()}}


def _qobs_context(**overrides: object) -> dict[str, object]:
    context: dict[str, object] = {
        "alias": "codex2",
        "provider": "codex",
        "account_home": "/private/codex-account-two",
        "resolved_executable": "/opt/local/bin/codex",
        "ticket_id": TICKET,
        "attempt_id": 1,
        "policy_version": "2026-08-26.1",
        "nonce": "ticket-luna-delegate-001-attempt-1-qobs-nonce",
        "observed_at": NOW.isoformat().replace("+00:00", "Z"),
    }
    context.update(overrides)
    return context


def _artifact(
    *, remaining: float = 10.0, context: dict[str, object] | None = None
) -> dict[str, object]:
    return quota.probe_quota_observation(_signals(remaining), context or _qobs_context())


def _decision(**overrides: object) -> dict[str, object]:
    decision: dict[str, object] = {
        "schema_version": 1,
        "ticket": TICKET,
        "phase": "implementation",
        "scope_rank": 1,
        "complexity_rank": 1,
        "risk_rank": 1,
        "ambiguity_rank": 1,
        "evidence_burden_rank": 1,
        "quota_band": "constrained",
        "work_mode": "read_only",
        "selected_alias": "codex2",
        "selected_model": "gpt-5.6-luna",
        "selected_effort": "xhigh",
        "rationale": "Exact one-shot read-only Luna diagnostic approved by the owner.",
        "policy_version": "2026-08-26.1",
        "planning_to_medium_confirmed": True,
        "hitl_approved": True,
    }
    decision.update(overrides)
    return decision


def _config(*, include_exception: bool = True) -> dict[str, object]:
    config: dict[str, object] = {
        "version": 2,
        "model_policy": "multiagent_model_policy.yaml",
        "activation_prohibited": True,
        "dispatcher_execution": "CLOSED",
        "runtime": {"approved_for_execution": True, "protocol_version": 2},
        "accounts": {
            "codex2": {
                "cli": "codex",
                "command": "codex",
                "home_env": "CODEX_HOME",
                "home_path": "${HOME}/.ai-accounts/codex/account2",
            }
        },
        "roles": {
            "codex2_luna_diagnostic": {
                "alias": "codex2",
                "cli": "codex",
                "model": "gpt-5.6-luna",
                "effort": "xhigh",
                "sandbox": "read-only",
            }
        },
        "provider_account_state": None,
        "execution_exceptions": {},
    }
    if include_exception:
        config["execution_exceptions"] = {
            EXCEPTION_ID: {
                "ticket": TICKET,
                "attempt_id": 1,
                "role": "codex2_luna_diagnostic",
                "alias": "codex2",
                "provider": "codex",
                "decision_schema_version": 1,
                "model": "gpt-5.6-luna",
                "effort": "xhigh",
                "work_mode": "read_only",
                "sandbox": "read-only",
                "quota_band": "constrained",
                "maximum_uses": 1,
                "automatic_retry": False,
            }
        }
    return config


def _route(config: dict[str, object] | None = None) -> command.Route:
    return command.resolve_route(config or _config(), "codex2_luna_diagnostic")


def _gate(
    tmp_path: Path,
    *,
    config: dict[str, object] | None = None,
    artifact: object = _UNSET,
    context: dict[str, object] | None = None,
    decision: object = _UNSET,
    exception_id: str = EXCEPTION_ID,
    snapshot_sha256: str = "a" * 64,
    now: datetime = NOW,
):
    selected_config = config or _config()
    return command.validate_closed_dispatch_exception(
        selected_config,
        execution_exception_id=exception_id,
        decision=_decision() if decision is _UNSET else decision,
        route=_route(selected_config),
        quota_observation=_artifact(context=context) if artifact is _UNSET else artifact,
        expected_qobs_context=context or _qobs_context(),
        scheduling_snapshot_sha256=snapshot_sha256,
        qobs_nonce_store=tmp_path / "qobs-nonces",
        exception_store=tmp_path / "exception-uses",
        now=now,
    )


def _forbid_process(monkeypatch: pytest.MonkeyPatch) -> list[object]:
    calls: list[object] = []

    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("invalid exception reached provider process creation")

    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    return calls


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_shared_runtime_is_explicitly_closed_and_ticket_config_is_exact() -> None:
    shared = command.load_config(SHARED_CONFIG)
    assert shared["activation_prohibited"] is True
    assert shared["dispatcher_execution"] == "CLOSED"

    ticket_config = command.load_config(EXCEPTION_CONFIG)
    assert ticket_config["activation_prohibited"] is True
    assert ticket_config["dispatcher_execution"] == "CLOSED"
    assert ticket_config["execution_exceptions"] == _config()["execution_exceptions"]
    assert ticket_config["roles"]["codex2_luna_diagnostic"] == _config()["roles"][
        "codex2_luna_diagnostic"
    ]


def test_missing_activation_fields_default_closed_and_prohibited() -> None:
    assert command.effective_activation_state({}) == (True, "CLOSED")
    assert command.effective_activation_state({"dispatcher_execution": "OPEN"}) == (
        True,
        "OPEN",
    )
    assert command.effective_activation_state({"activation_prohibited": False}) == (
        False,
        "CLOSED",
    )


def test_parser_exposes_qobs_and_exception_flags() -> None:
    destinations = {action.dest for action in command._parser()._actions}
    assert {"quota_observation", "execution_exception_id"} <= destinations


@pytest.mark.parametrize(
    "quota_path,exception_id",
    [(None, EXCEPTION_ID), ("qobs.json", None)],
)
def test_closed_dispatch_requires_qobs_and_exception_flags_together(
    quota_path: str | None, exception_id: str | None
) -> None:
    args = command._parser().parse_args(
        [
            "--config",
            str(EXCEPTION_CONFIG),
            "--role",
            "codex2_luna_diagnostic",
            "--objective",
            "diagnose only",
            "--execute",
            *(["--quota-observation", quota_path] if quota_path else []),
            *(["--execution-exception-id", exception_id] if exception_id else []),
        ]
    )
    with pytest.raises(command.DispatchDecisionError, match="required together"):
        command.validate_closed_dispatch_execution_args(args, _config())


def test_exact_constrained_qobs_returns_typed_admission_without_declared_state(
    tmp_path: Path,
) -> None:
    admission = _gate(tmp_path)
    assert isinstance(admission, command.QobsAdmission)
    assert admission.ticket_id == TICKET
    assert admission.attempt_id == 1
    assert admission.role == "codex2_luna_diagnostic"
    assert admission.alias == "codex2"
    assert admission.provider == "codex"
    assert admission.model == "gpt-5.6-luna"
    assert admission.effort == "xhigh"
    assert admission.quota_band == "constrained"
    assert admission.execution_exception_id == EXCEPTION_ID
    assert len(admission.decision_sha256) == 64
    assert admission.scheduling_snapshot_sha256 == "a" * 64
    assert len(admission.qobs_artifact_sha256) == 64
    assert len(admission.exception_consumption_sha256) == 64


def _capacity_snapshot() -> scheduler.SchedulingSnapshot:
    return scheduler.validate_snapshot(
        {
            "schema_version": 1,
            "tickets": [
                {
                    "ticket_id": TICKET,
                    "severity": "HIGH",
                    "work_effort": "S",
                    "status": "READY",
                    "dependencies": [],
                    "blockers": [],
                    "owner": "codex2_luna_diagnostic",
                    "ownership": ["read-only Luna diagnostic"],
                    "quota_passed": True,
                    "hitl_passed": True,
                    "rule18_decision_valid": True,
                }
            ],
            "reservations": [],
        }
    )


def _admit_capacity(
    tmp_path: Path,
    *,
    provider_account_state: object = None,
    qobs_admission: object = None,
):
    policy = json.loads(
        (ROOT / ".agents/config/s3_capacity_policy.json").read_text(encoding="utf-8")
    )
    return scheduler.admit_dispatch_capacity(
        _capacity_snapshot(),
        ticket_id=TICKET,
        owner="codex2_luna_diagnostic",
        ownership=("read-only Luna diagnostic",),
        decision_valid=True,
        store_path=str(tmp_path / "capacity"),
        account="codex2",
        request_id="luna-one-shot-capacity",
        lane=1,
        request_budget=1,
        model_quality_floor="1",
        policy=policy,
        provider="codex",
        provider_account_state=provider_account_state,
        qobs_admission=qobs_admission,
        attempt=1,
        retry_limit=1,
    )


def test_declared_constrained_state_without_validated_qobs_admission_is_blocked(
    tmp_path: Path,
) -> None:
    declared = {
        "providers": {"codex": {"state": "constrained"}},
        "accounts": {"codex2": {"state": "constrained"}},
    }
    with pytest.raises(scheduler.SchedulingError) as exc:
        _admit_capacity(
            tmp_path,
            provider_account_state=declared,
            qobs_admission=None,
        )
    assert exc.value.code == "PROVIDER_ACCOUNT_STATE_BLOCKED"


def test_provider_account_state_may_be_absent_only_with_validated_qobs_admission(
    tmp_path: Path,
) -> None:
    admission = _gate(tmp_path / "gate")
    lease = _admit_capacity(
        tmp_path,
        provider_account_state=None,
        qobs_admission=admission,
    )
    assert lease.account == "codex2"


@pytest.mark.parametrize(
    "remaining,artifact_builder,context_overrides,now,error_code",
    [
        (10.0, lambda context: quota.probe_quota_observation("not-json", context), {}, NOW, "UNKNOWN_QUOTA"),
        (9.0, lambda context: _artifact(remaining=9.0, context=context), {}, NOW, "QUOTA_NOT_DISPATCHABLE"),
        (10.0, lambda context: _artifact(context=context), {"observed_at": (NOW - timedelta(seconds=61)).isoformat().replace("+00:00", "Z")}, NOW, "STALE_OBSERVATION"),
        (10.0, lambda context: _artifact(context=context), {"observed_at": (NOW + timedelta(seconds=6)).isoformat().replace("+00:00", "Z")}, NOW, "FUTURE_OBSERVATION"),
    ],
)
def test_unsafe_qobs_blocks_before_provider_start(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    remaining: float,
    artifact_builder,
    context_overrides: dict[str, object],
    now: datetime,
    error_code: str,
) -> None:
    del remaining
    calls = _forbid_process(monkeypatch)
    context = _qobs_context(**context_overrides)
    artifact = artifact_builder(context)
    with pytest.raises(quota.QuotaObservationError) as exc:
        _gate(tmp_path, artifact=artifact, context=context, now=now)
    assert exc.value.code == error_code
    assert calls == []


@pytest.mark.parametrize(
    "case",
    [
        "malformed",
        "field_mismatch",
        "digest_mismatch",
        "writable_sandbox",
        "missing_exception",
        "wrong_ticket",
        "wrong_attempt",
        "missing_decision",
        "missing_snapshot",
        "missing_qobs",
    ],
)
def test_mismatch_or_missing_evidence_blocks_before_provider_start(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    case: str,
) -> None:
    calls = _forbid_process(monkeypatch)
    config = _config()
    context = _qobs_context()
    artifact: object = _artifact(context=context)
    decision = _decision()
    exception_id = EXCEPTION_ID
    snapshot = "a" * 64

    if case == "malformed":
        artifact = {"not": "a QOBS artifact"}
    elif case == "field_mismatch":
        context = _qobs_context(alias="codex1")
    elif case == "digest_mismatch":
        artifact = deepcopy(artifact)
        artifact["observation"]["quota_band"] = "unknown"
    elif case == "writable_sandbox":
        config["roles"]["codex2_luna_diagnostic"]["sandbox"] = "workspace-write"
    elif case == "missing_exception":
        exception_id = ""
    elif case == "wrong_ticket":
        decision = _decision(ticket="TICKET-OTHER")
    elif case == "wrong_attempt":
        config["execution_exceptions"][EXCEPTION_ID]["attempt_id"] = 2
    elif case == "missing_decision":
        decision = None
    elif case == "missing_snapshot":
        snapshot = ""
    elif case == "missing_qobs":
        artifact = None

    with pytest.raises((command.ConfigurationError, quota.QuotaObservationError)):
        command.validate_closed_dispatch_exception(
            config,
            execution_exception_id=exception_id,
            decision=decision,
            route=_route(config),
            quota_observation=artifact,
            expected_qobs_context=context,
            scheduling_snapshot_sha256=snapshot,
            qobs_nonce_store=tmp_path / "qobs-nonces",
            exception_store=tmp_path / "exception-uses",
            now=NOW,
        )
    assert calls == []


def test_replayed_qobs_blocks_before_provider_start(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _forbid_process(monkeypatch)
    _gate(tmp_path)
    with pytest.raises(quota.QuotaObservationError) as exc:
        _gate(tmp_path)
    assert exc.value.code in {"REPLAYED_OBSERVATION", "EXECUTION_EXCEPTION_CONSUMED"}
    assert calls == []


def test_schema_v1_is_accepted_only_by_exact_exception_and_global_allowlist_stays_empty(
    tmp_path: Path,
) -> None:
    policy = quota.load_quota_policy(POLICY_PATH)
    assert policy["quota_observation"]["executable_decision_schema_versions"] == []
    assert _gate(tmp_path).decision_schema_version == 1

    with pytest.raises(command.DispatchDecisionError):
        command.validate_quota_bound_dispatch(
            _decision(),
            _artifact(),
            _qobs_context(),
            scheduling_snapshot_sha256="a" * 64,
            nonce_store=tmp_path / "ordinary-qobs-nonces",
            now=NOW,
        )


def test_exception_consumption_is_atomic_with_one_winner(tmp_path: Path) -> None:
    def attempt():
        try:
            return _gate(tmp_path)
        except (command.ConfigurationError, quota.QuotaObservationError) as exc:
            return exc

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(lambda _: attempt(), range(2)))

    winners = [value for value in outcomes if isinstance(value, command.QobsAdmission)]
    blocked = [value for value in outcomes if isinstance(value, Exception)]
    assert len(winners) == 1
    assert len(blocked) == 1


def test_provider_start_failure_after_consumption_has_no_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    admission = _gate(tmp_path)
    starts = 0

    def provider_start_failure(*args, **kwargs):
        nonlocal starts
        starts += 1
        raise OSError("provider start failed")

    monkeypatch.setattr(subprocess, "Popen", provider_start_failure)
    with pytest.raises(OSError, match="provider start failed"):
        subprocess.Popen(["codex"])
    with pytest.raises((command.ConfigurationError, quota.QuotaObservationError)):
        _gate(tmp_path)
    assert admission.execution_exception_id == EXCEPTION_ID
    assert starts == 1


def test_qobs_binding_participates_in_dispatch_identity_and_receipt_validation(
    tmp_path: Path,
) -> None:
    artifact = _artifact()
    admission = _gate(tmp_path, artifact=artifact)
    dispatch_context = admission.dispatch_context()
    identity = command.quota_bound_dispatch_identity(
        artifact, admission.quota_consumption(), dispatch_context
    )
    assert identity == admission.dispatch_identity

    receipt = {
        "protocol_version": 2,
        "quota_status": "constrained",
        "dispatch_identity": identity,
    }
    assert command.validate_quota_receipt_binding(
        receipt,
        artifact,
        admission.quota_consumption(),
        dispatch_context,
        _qobs_context(),
        now=NOW,
    ) is receipt

    tampered = dict(receipt, dispatch_identity="0" * 64)
    with pytest.raises(command.ConfigurationError, match="dispatch identity"):
        command.validate_quota_receipt_binding(
            tampered,
            artifact,
            admission.quota_consumption(),
            dispatch_context,
            _qobs_context(),
            now=NOW,
        )


def test_exception_does_not_modify_existing_rc2_history(tmp_path: Path) -> None:
    history = [
        ROOT / "project/tests/artifacts/priority_scheduling/decision_rc2_004_qobs_contract.json",
        ROOT / "project/tests/artifacts/priority_scheduling/scheduling_snapshot_rc2_004_qobs_contract.json",
    ]
    before = {path: _sha256(path) for path in history}
    _gate(tmp_path)
    assert {path: _sha256(path) for path in history} == before


# Review-remediation API extension (kept on the existing exception framework):
# ``Invocation`` carries qobs_admission, qobs_artifact, qobs_expected_context,
# and qobs_ledger_store.  ``validate_closed_dispatch_exception`` accepts
# ``consume=False`` plus one ``ledger_store`` for side-effect-free preflight;
# the spawn boundary atomically commits the exception and nonce together only
# after ordinary preflight/capacity succeeds.  Receipt validation reuses
# ``validate_quota_receipt_binding`` with the trusted dispatch start timestamp.


def _snapshot_data() -> dict[str, object]:
    return {
        "schema_version": 1,
        "tickets": [
            {
                "ticket_id": TICKET,
                "severity": "HIGH",
                "work_effort": "S",
                "status": "READY",
                "dependencies": [],
                "blockers": [],
                "owner": "codex2_luna_diagnostic",
                "ownership": ["read-only Luna diagnostic"],
                "quota_passed": True,
                "hitl_passed": True,
                "rule18_decision_valid": True,
            }
        ],
        "reservations": [],
    }


def _work_result() -> dict[str, object]:
    return {
        "status": "DONE",
        "scope_owned": ["read-only Luna diagnostic"],
        "evidence": {
            "commands": ["mocked provider invocation"],
            "outcomes": ["typed result returned"],
            "artifacts": [],
        },
        "findings": ["mocked Luna diagnostic completed"],
        "changed_files": [],
        "residual_risk": "provider was mocked",
        "recommended_next_action": "retain the governed receipt",
    }


def _codex_stdout() -> str:
    lines = [
        {"type": "thread.started", "thread_id": "luna-mocked-thread"},
        {
            "type": "item.completed",
            "item": {
                "type": "agent_message",
                "text": json.dumps(_work_result(), separators=(",", ":")),
            },
        },
        {"type": "turn.completed"},
    ]
    return "\n".join(json.dumps(item, separators=(",", ":")) for item in lines) + "\n"


def _qobs_invocation(
    tmp_path: Path,
    *,
    project_dir: Path = ROOT,
    late_binding: bool = True,
):
    executable = tmp_path / "bin" / "codex"
    executable.parent.mkdir(parents=True, exist_ok=True)
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="ascii")
    executable.chmod(0o700)
    account_home = tmp_path / "account2"
    account_home.mkdir(mode=0o700)

    config = _config()
    config["accounts"]["codex2"]["command"] = str(executable)
    config["accounts"]["codex2"]["home_path"] = str(account_home)
    route = _route(config)
    decision = _decision()
    snapshot = _snapshot_data()
    snapshot_digest = scheduler.validate_snapshot(snapshot).digest
    observed = datetime.now(timezone.utc)
    context = _qobs_context(
        account_home=str(account_home),
        resolved_executable=str(executable.resolve()),
        observed_at=observed.isoformat().replace("+00:00", "Z"),
        nonce=f"review-{tmp_path.name}-nonce",
    )
    artifact = _artifact(context=context)
    ledger = tmp_path / "one-shot-ledger"
    if late_binding:
        admission = command.validate_closed_dispatch_exception(
            config,
            execution_exception_id=EXCEPTION_ID,
            decision=decision,
            route=route,
            quota_observation=artifact,
            expected_qobs_context=context,
            scheduling_snapshot_sha256=snapshot_digest,
            qobs_nonce_store=None,
            exception_store=None,
            ledger_store=ledger,
            consume=False,
            now=observed,
        )
    else:
        admission = command.validate_closed_dispatch_exception(
            config,
            execution_exception_id=EXCEPTION_ID,
            decision=decision,
            route=route,
            quota_observation=artifact,
            expected_qobs_context=context,
            scheduling_snapshot_sha256=snapshot_digest,
            qobs_nonce_store=tmp_path / "legacy-qobs",
            exception_store=tmp_path / "legacy-exception",
            now=observed,
        )
    invocation = command.build_invocation(
        route,
        command.render_prompt(objective="Run mocked Luna diagnostic"),
        project_dir,
        decision=decision,
        model_policy=command.load_model_policy(POLICY_PATH),
        attempt_id=1,
        objective="Run mocked Luna diagnostic",
        ownership="read-only Luna diagnostic",
        runtime_config_path=EXCEPTION_CONFIG,
        runtime_config_approved=True,
        work_result_schema_path=(
            ROOT / ".agents/schemas/multiagent-work-result-v2.schema.json"
        ),
        scheduling_snapshot=snapshot,
        claim_store_override=tmp_path / "claims",
        qobs_admission=admission,
        qobs_artifact=artifact,
        qobs_expected_context=context,
        qobs_ledger_store=ledger,
    )
    return invocation, admission, artifact, context, ledger


def _write_main_evidence(tmp_path: Path, artifact: dict[str, object]) -> tuple[Path, Path, Path]:
    decision_path = tmp_path / "decision.json"
    decision_path.write_text(json.dumps(_decision()), encoding="utf-8")
    snapshot_path = tmp_path / "snapshot.json"
    snapshot_path.write_text(json.dumps(_snapshot_data()), encoding="utf-8")
    artifact_path = tmp_path / "qobs.json"
    artifact_path.write_text(json.dumps(artifact), encoding="utf-8")
    return decision_path, snapshot_path, artifact_path


def test_review_main_retains_qobs_binding_on_invocation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    config = command.load_config(EXCEPTION_CONFIG)
    route = command.resolve_route(config, "codex2_luna_diagnostic")
    executable = tmp_path / "codex"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="ascii")
    executable.chmod(0o700)
    monkeypatch.setattr(command.shutil, "which", lambda _: str(executable))
    context = _qobs_context(
        account_home=route.home_path,
        resolved_executable=str(executable.resolve()),
        observed_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        nonce="review-main-binding-nonce",
    )
    artifact = _artifact(context=context)
    admission = command.validate_closed_dispatch_exception(
        config,
        execution_exception_id=EXCEPTION_ID,
        decision=_decision(),
        route=route,
        quota_observation=artifact,
        expected_qobs_context=context,
        scheduling_snapshot_sha256=scheduler.validate_snapshot(_snapshot_data()).digest,
        qobs_nonce_store=tmp_path / "prebuilt-qobs",
        exception_store=tmp_path / "prebuilt-exception",
        now=datetime.now(timezone.utc),
    )
    decision_path, snapshot_path, artifact_path = _write_main_evidence(tmp_path, artifact)
    monkeypatch.setattr(command, "validate_closed_dispatch_exception", lambda *a, **k: admission)
    monkeypatch.setattr(command, "admit_dispatch_capacity", lambda *a, **k: object())

    def execute_bound(invocation):
        assert invocation.qobs_admission is admission
        assert invocation.qobs_artifact == artifact
        assert invocation.qobs_expected_context == context
        assert command._claim_dispatch_identity(invocation) == admission.dispatch_identity
        return command.ExecutionOutcome(
            subprocess.CompletedProcess([], 0, "", ""),
            {"execution_receipt": {}, "work_result": _work_result()},
        )

    monkeypatch.setattr(command, "execute_invocation", execute_bound)
    result = command.main(
        [
            "--config",
            str(EXCEPTION_CONFIG),
            "--role",
            "codex2_luna_diagnostic",
            "--objective",
            "Run mocked Luna diagnostic",
            "--ownership",
            "read-only Luna diagnostic",
            "--project-dir",
            str(ROOT),
            "--decision",
            str(decision_path),
            "--policy",
            str(POLICY_PATH),
            "--scheduling-snapshot",
            str(snapshot_path),
            "--quota-observation",
            str(artifact_path),
            "--execution-exception-id",
            EXCEPTION_ID,
            "--execute",
        ]
    )
    assert result == 0
    assert "[OK] Provider process completed" in capsys.readouterr().out


def test_review_qobs_execute_receipt_is_bound_and_revalidated(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    invocation, admission, artifact, context, _ = _qobs_invocation(tmp_path)
    observed_validation_times: list[datetime | None] = []
    original = command.validate_quota_receipt_binding

    def quota_spy(*args, **kwargs):
        observed_validation_times.append(kwargs.get("now"))
        return original(*args, **kwargs)

    monkeypatch.setattr(command, "validate_quota_receipt_binding", quota_spy)
    monkeypatch.setattr(
        command.subprocess,
        "run",
        lambda argv, **kwargs: subprocess.CompletedProcess(
            argv, 0, stdout=_codex_stdout(), stderr=""
        ),
    )
    outcome = command.execute_invocation(invocation)
    receipt = outcome.completed["execution_receipt"]
    started = datetime.fromisoformat(receipt["started_at"].replace("Z", "+00:00"))

    assert receipt["dispatch_identity"] == admission.dispatch_identity
    assert command._claim_dispatch_identity(invocation) == admission.dispatch_identity
    assert observed_validation_times
    assert observed_validation_times[-1] == started
    assert quota.quota_artifact_sha256(artifact) == admission.qobs_artifact_sha256
    assert context["nonce"]


def test_review_ordinary_dispatch_identity_remains_byte_compatible(tmp_path: Path) -> None:
    config = _config()
    route = _route(config)
    invocation = command.build_invocation(
        route,
        "ordinary dry-run prompt",
        tmp_path,
        objective="ordinary objective",
        ownership="ordinary ownership",
    )
    material = {
        "decision_sha256": invocation.decision_digest,
        "scheduling_snapshot_sha256": invocation.scheduling_snapshot_digest,
        "ticket": None,
        "route": {
            "role": route.role,
            "alias": route.alias,
            "provider": route.cli,
            "model": route.model,
            "effort": route.effort,
        },
        "cwd_sha256": hashlib.sha256(invocation.cwd.encode()).hexdigest(),
        "objective_sha256": hashlib.sha256(invocation.objective.encode()).hexdigest(),
        "ownership_sha256": hashlib.sha256(invocation.ownership.encode()).hexdigest(),
    }
    assert command._claim_dispatch_identity(invocation) == command._canonical_sha256(material)


@pytest.mark.parametrize(
    "field",
    ["decision", "snapshot", "artifact", "nonce", "executable", "exception"],
)
def test_review_real_receipt_validation_blocks_qobs_tampering(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, field: str
) -> None:
    invocation, _, _, _, _ = _qobs_invocation(tmp_path)
    monkeypatch.setattr(
        command.subprocess,
        "run",
        lambda argv, **kwargs: subprocess.CompletedProcess(
            argv, 0, stdout=_codex_stdout(), stderr=""
        ),
    )
    outcome = command.execute_invocation(invocation)
    receipt = outcome.completed["execution_receipt"]
    tampered = invocation
    if field == "decision":
        changed = dict(invocation.decision)
        changed["rationale"] = "tampered"
        tampered = replace(invocation, decision=changed)
    elif field == "snapshot":
        tampered = replace(invocation, scheduling_snapshot_digest="0" * 64)
    elif field == "artifact":
        changed = deepcopy(invocation.qobs_artifact)
        changed["observation"]["quota_band"] = "unknown"
        tampered = replace(invocation, qobs_artifact=changed)
    elif field == "nonce":
        changed = dict(invocation.qobs_expected_context)
        changed["nonce"] = "tampered-nonce"
        tampered = replace(invocation, qobs_expected_context=changed)
    elif field == "executable":
        tampered = replace(
            invocation,
            route=replace(invocation.route, command="/different/codex"),
        )
    else:
        tampered = replace(
            invocation,
            qobs_admission=replace(
                invocation.qobs_admission,
                execution_exception_id="different-exception",
            ),
        )
    with pytest.raises(command.ConfigurationError):
        command.validate_execution_receipt(
            receipt,
            _work_result(),
            tampered,
            _codex_stdout(),
            portable=True,
        )


def test_review_exception_project_dir_is_canonical_and_not_a_replay_namespace(
    tmp_path: Path,
) -> None:
    for alternate in (tmp_path / "one", tmp_path / "two"):
        alternate.mkdir()
        with pytest.raises(command.ConfigurationError, match="repository root"):
            _qobs_invocation(tmp_path / alternate.name / "fixture", project_dir=alternate)


@pytest.mark.parametrize("missing", ["activation_prohibited", "dispatcher_execution"])
def test_review_non_exception_main_uses_effective_activation_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    missing: str,
) -> None:
    config = _config(include_exception=False)
    config.pop(missing)
    config_path = tmp_path / f"normal-{missing}.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    decision_path, snapshot_path, _ = _write_main_evidence(tmp_path, _artifact())

    class ActivationChecked(RuntimeError):
        pass

    monkeypatch.setattr(
        command,
        "effective_activation_state",
        lambda _: (_ for _ in ()).throw(ActivationChecked()),
    )
    with pytest.raises(ActivationChecked):
        command.main(
            [
                "--config",
                str(config_path),
                "--role",
                "codex2_luna_diagnostic",
                "--objective",
                "normal lane activation check",
                "--project-dir",
                str(tmp_path),
                "--decision",
                str(decision_path),
                "--policy",
                str(POLICY_PATH),
                "--scheduling-snapshot",
                str(snapshot_path),
                "--execute",
            ]
        )


def test_review_only_explicit_normal_open_false_activation_passes() -> None:
    command.validate_activation_state(
        activation_prohibited=command.effective_activation_state(
            {"activation_prohibited": False, "dispatcher_execution": "OPEN"}
        )[0],
        dispatcher_execution=command.effective_activation_state(
            {"activation_prohibited": False, "dispatcher_execution": "OPEN"}
        )[1],
    )
    for config in (
        {"dispatcher_execution": "OPEN"},
        {"activation_prohibited": False},
    ):
        with pytest.raises(scheduler.SchedulingError):
            command.validate_activation_state(
                activation_prohibited=command.effective_activation_state(config)[0],
                dispatcher_execution=command.effective_activation_state(config)[1],
            )


@pytest.mark.parametrize(
    "field",
    [
        "decision_sha256",
        "scheduling_snapshot_sha256",
        "qobs_artifact_sha256",
        "qobs_nonce_sha256",
        "resolved_executable_sha256",
        "exception_consumption_sha256",
        "dispatch_identity",
    ],
)
def test_review_scheduler_rejects_forged_or_incoherent_qobs_admission(
    tmp_path: Path, field: str
) -> None:
    admission = _gate(tmp_path / "gate")
    forged = command.QobsAdmission(**admission.__dict__)
    if field != "dispatch_identity":
        forged = replace(forged, **{field: "0" * 64})
    decision_sha256 = command.validate_dispatch_decision(
        _decision(), command.load_model_policy(POLICY_PATH), _route(_config())
    ).digest
    policy = json.loads(
        (ROOT / ".agents/config/s3_capacity_policy.json").read_text(encoding="utf-8")
    )
    with pytest.raises(scheduler.SchedulingError) as exc:
        scheduler.admit_dispatch_capacity(
            _capacity_snapshot(),
            ticket_id=TICKET,
            owner="codex2_luna_diagnostic",
            ownership=("read-only Luna diagnostic",),
            decision_valid=True,
            store_path=str(tmp_path / "capacity"),
            account="codex2",
            request_id=f"forged-{field}",
            lane=1,
            request_budget=1,
            model_quality_floor="1",
            policy=policy,
            provider="codex",
            provider_account_state=None,
            qobs_admission=forged,
            decision_sha256=decision_sha256,
            scheduling_snapshot_sha256="a" * 64,
            route=_route(_config()),
            attempt=1,
            retry_limit=1,
        )
    assert exc.value.code == "QOBS_ADMISSION_INVALID"


def test_review_qobs_pins_exact_absolute_executable_before_consumption(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _config()
    config["accounts"]["codex2"]["command"] = "codex"
    monkeypatch.setattr(command.shutil, "which", lambda _: "/different/bin/codex")
    calls = _forbid_process(monkeypatch)
    with pytest.raises(command.ConfigurationError, match="executable"):
        _gate(tmp_path, config=config)
    assert calls == []
    assert not (tmp_path / "exception-uses").exists()


def test_review_final_spawn_revalidates_exact_qobs_executable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    invocation, _, _, _, ledger = _qobs_invocation(tmp_path)
    calls = _forbid_process(monkeypatch)
    monkeypatch.setattr(command.shutil, "which", lambda _: "/different/bin/codex")
    with pytest.raises(command.ConfigurationError, match="executable"):
        command.execute_invocation(invocation)
    assert calls == []
    assert not ledger.exists()


@pytest.mark.parametrize("failure", ["preflight", "capacity"])
def test_review_preflight_or_capacity_failure_does_not_burn_one_shot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    invocation, _, _, _, ledger = _qobs_invocation(tmp_path)
    calls = _forbid_process(monkeypatch)
    if failure == "preflight":
        monkeypatch.setattr(
            command,
            "validate_execution_preflight",
            lambda _: (_ for _ in ()).throw(command.ConfigurationError("preflight")),
        )
    else:
        monkeypatch.setattr(command, "validate_execution_preflight", lambda _: None)
        monkeypatch.setattr(
            command,
            "_consume_spawn_capacity",
            lambda *a, **k: (_ for _ in ()).throw(
                scheduler.SchedulingError("CAPACITY_BLOCKED", "capacity")
            ),
        )
    with pytest.raises((command.ConfigurationError, scheduler.SchedulingError)):
        command.execute_invocation(invocation)
    assert calls == []
    assert not ledger.exists() or list(ledger.iterdir()) == []


def test_review_provider_start_failure_burns_combined_use_and_never_retries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    invocation, _, _, _, ledger = _qobs_invocation(tmp_path)
    starts = 0

    def start_failure(*args, **kwargs):
        nonlocal starts
        starts += 1
        raise OSError("mocked provider start failure")

    monkeypatch.setattr(command.subprocess, "run", start_failure)
    for _ in range(2):
        with pytest.raises((OSError, command.ConfigurationError, quota.QuotaObservationError)):
            command.execute_invocation(invocation)
    assert starts == 1
    assert ledger.is_dir()
    assert len([path for path in ledger.iterdir() if path.is_file()]) == 1
