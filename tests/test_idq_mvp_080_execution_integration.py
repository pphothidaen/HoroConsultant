"""Red synthetic execution contract for the bounded IDQ-MVP-080 exception.

This deliberately requires a separate execution assembler, rather than
widening the pure validator API frozen in the r2 baseline.  The assembler
accepts only its injected synthetic ``provider_runner``; it must not read or
retain a provider stream and it must never select a retry or fallback route.

Required public seam::

    execute_idq_mvp_080_execution(config, request, execution_context,
                                  marker_store, provider_runner)

The source owner must call ``validate_idq_mvp_080_execution_admission`` as the
last validation immediately before the one-use-marker/start boundary.  The
runner returns exactly ``{"receipt": ..., "work_result": ...}``; its output
is validated through the frozen receipt-v2 and typed WorkResult contract.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import pytest

import scripts.multiagent_prompt_command as command
import scripts.agent_quota_status_guard as quota


TICKET = "IDQ-MVP-080"
ALIASES = {"codex1": "codex", "codex2": "codex", "agy1": "agy", "agy2": "agy"}


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("ascii")).hexdigest()


def _config() -> dict[str, object]:
    return {
        "activation_prohibited": True,
        "dispatcher_execution": "CLOSED",
        "idq_mvp_080": {
            "ticket": TICKET,
            "aliases": {
                alias: {
                    "provider": provider,
                    "attempt": 1,
                    "work_mode": "read_only",
                    "automatic_retry": False,
                    "fallback": False,
                }
                for alias, provider in ALIASES.items()
            },
        },
    }


def _request(alias: str) -> dict[str, object]:
    return {
        "ticket": TICKET,
        "alias": alias,
        "provider": ALIASES.get(alias, "codex"),
        "attempt": 1,
        "work_mode": "read_only",
        "automatic_retry": False,
        "fallback": False,
        "decision_sha256": _digest(f"decision:{alias}"),
        "qobs_artifact_sha256": _digest(f"qobs:{alias}"),
        "qobs_quota_band": "constrained",
        "nonce_sha256": _digest(f"nonce:{alias}"),
        "scheduling_snapshot_sha256": _digest(f"snapshot:{alias}"),
        "resolved_executable_sha256": _digest(f"executable:{alias}"),
        "account_identity_sha256": _digest(f"account:{alias}"),
        "lease_risk_sha256": _digest(f"lease:{alias}"),
    }


def _signals() -> dict[str, object]:
    values = {"usedPercent": 90.0, "remainingPercent": 10.0, "reached": False,
              "limit": 100.0, "spend": 90.0, "remaining": 10.0}
    return {**values, "buckets": {"primary": dict(values), "secondary": dict(values)}}


def _fixture(alias: str) -> tuple[dict[str, object], dict[str, object]]:
    """Build a genuine synthetic QOBS artifact through the quota guard."""

    request = _request(alias)
    provider = str(request["provider"])
    qobs_context: dict[str, object] = {
        "alias": alias, "provider": provider, "account_home": f"/private/idq/{alias}",
        "resolved_executable": f"/opt/idq/{provider}", "ticket_id": TICKET,
        "attempt_id": 1, "policy_version": "2026-08-26.1",
        "nonce": f"idq-mvp-080-{alias}-nonce",
        "observed_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }
    artifact = quota.probe_quota_observation(_signals(), qobs_context)
    request.update({
        "qobs_artifact_sha256": quota.quota_artifact_sha256(artifact),
        "nonce_sha256": quota.sha256_text(str(qobs_context["nonce"])),
        "resolved_executable_sha256": quota.sha256_text(str(qobs_context["resolved_executable"])),
        "account_identity_sha256": quota.sha256_text(str(qobs_context["account_home"])),
    })
    return {
        "qobs_artifact": artifact,
        "qobs_expected_context": qobs_context,
        "runtime": (
            {"read_only": True, "mode": "plan", "sandbox": True}
            if provider == "agy"
            else {"read_only": True, "sandbox": "read-only"}
        ),
    }, request


def _work_result() -> dict[str, object]:
    return {
        "status": "DONE",
        "scope_owned": ["read-only repository inventory"],
        "evidence": {"commands": [], "outcomes": ["synthetic"], "artifacts": []},
        "findings": ["synthetic integration result"],
        "changed_files": [],
        "residual_risk": "none",
        "recommended_next_action": "stop",
    }


def _receipt(request: dict[str, object], result: dict[str, object]) -> dict[str, object]:
    return {
        "protocol_version": 2,
        "ticket": TICKET,
        "alias": request["alias"],
        "provider": request["provider"],
        "attempt": 1,
        "decision_sha256": request["decision_sha256"],
        "qobs_artifact_sha256": request["qobs_artifact_sha256"],
        "nonce_sha256": request["nonce_sha256"],
        "scheduling_snapshot_sha256": request["scheduling_snapshot_sha256"],
        "resolved_executable_sha256": request["resolved_executable_sha256"],
        "account_identity_sha256": request["account_identity_sha256"],
        "work_result_sha256": hashlib.sha256(
            json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        ).hexdigest(),
    }


def _payload(request: dict[str, object]) -> dict[str, object]:
    result = _work_result()
    return {"receipt": _receipt(request, result), "work_result": result}


def test_execution_uses_the_new_admission_gate_at_the_atomic_spawn_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    context, request = _fixture("codex1")
    events: list[str] = []
    original_gate = command.validate_idq_mvp_080_execution_admission
    original_consume = command._consume_idq_mvp_080_marker

    def observe_gate(*args: object, **kwargs: object) -> object:
        events.append("admission")
        return original_gate(*args, **kwargs)

    def observe_consume(*args: object, **kwargs: object) -> None:
        events.append("marker")
        original_consume(*args, **kwargs)

    monkeypatch.setattr(command, "validate_idq_mvp_080_execution_admission", observe_gate)
    monkeypatch.setattr(command, "_consume_idq_mvp_080_marker", observe_consume)

    def runner(admission: object) -> dict[str, object]:
        assert getattr(admission, "alias") == "codex1"
        events.append("spawn")
        return _payload(request)

    completed = command.execute_idq_mvp_080_execution(
        _config(), request, context, tmp_path, runner
    )
    assert events == ["admission", "marker", "spawn"]
    assert completed["receipt"]["alias"] == "codex1"
    assert completed["work_result"] == _work_result()
    assert command.effective_activation_state(_config()) == (True, "CLOSED")


def test_execution_accepts_only_the_four_one_shot_read_only_routes_and_safe_preflight(
    tmp_path: Path,
) -> None:
    calls: list[str] = []
    requests: dict[str, dict[str, object]] = {}

    def runner(admission: object) -> dict[str, object]:
        alias = str(getattr(admission, "alias"))
        calls.append(alias)
        return _payload(requests[alias])

    for alias in ALIASES:
        context, request = _fixture(alias)
        requests[alias] = request
        completed = command.execute_idq_mvp_080_execution(
            _config(), request, context, tmp_path, runner
        )
        assert completed["receipt"]["provider"] == ALIASES[alias]
    assert calls == list(ALIASES)

    rejected = [
        (lambda c, r: (dict(r, alias="codex3"), c))(*_fixture("codex1")),
        (lambda c, r: (dict(r, attempt=2), c))(*_fixture("codex1")),
        (lambda c, r: (dict(r, qobs_quota_band="unknown"), c))(*_fixture("codex2")),
        (lambda c, r: (r, dict(c, runtime={"read_only": True, "mode": "plan", "sandbox": False})))(*_fixture("agy1")),
    ]
    for request, context in rejected:
        with pytest.raises(command.ConfigurationError):
            command.execute_idq_mvp_080_execution(_config(), request, context, tmp_path, runner)
    assert calls == list(ALIASES)


@pytest.mark.parametrize("malformation", ["raw_stream", "no_receipt", "no_result", "bad_receipt"])
def test_execution_rejects_raw_or_unbound_provider_payloads(
    tmp_path: Path, malformation: str
) -> None:
    context, request = _fixture("codex1")

    def runner(_admission: object) -> dict[str, object]:
        payload = _payload(request)
        if malformation == "raw_stream":
            return dict(payload, raw_stream="forbidden")
        if malformation == "no_receipt":
            return {"work_result": payload["work_result"]}
        if malformation == "no_result":
            return {"receipt": payload["receipt"]}
        receipt = deepcopy(payload["receipt"])
        receipt["nonce_sha256"] = _digest("substituted-nonce")
        return {"receipt": receipt, "work_result": payload["work_result"]}

    with pytest.raises(command.ConfigurationError):
        command.execute_idq_mvp_080_execution(
            _config(), request, context, tmp_path, runner
        )


def test_execution_consumes_only_after_complete_preflight_and_never_retries(
    tmp_path: Path,
) -> None:
    context, request = _fixture("agy2")
    marker = tmp_path / "idq-mvp-080-agy2.used"
    calls: list[object] = []

    with pytest.raises(command.ConfigurationError):
        command.execute_idq_mvp_080_execution(
            _config(), request, dict(context, qobs_artifact={}), tmp_path,
            lambda admission: calls.append(admission),
        )
    assert not marker.exists()
    assert calls == []

    def failing_runner(admission: object) -> dict[str, object]:
        calls.append(admission)
        raise command.ConfigurationError("synthetic provider failure")

    with pytest.raises(command.ConfigurationError, match="synthetic provider failure"):
        command.execute_idq_mvp_080_execution(
            _config(), request, context, tmp_path, failing_runner
        )
    assert marker.exists()
    with pytest.raises(command.ConfigurationError, match="consumed|one.use"):
        command.execute_idq_mvp_080_execution(
            _config(), request, context, tmp_path, failing_runner
        )
    assert len(calls) == 1
