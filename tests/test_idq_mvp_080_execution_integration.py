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
import hashlib
import json
from pathlib import Path

import pytest

import scripts.multiagent_prompt_command as command


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


def _context(request: dict[str, object]) -> dict[str, object]:
    provider = str(request["provider"])
    return {
        "qobs": {"known": True, "quota_band": "constrained", "sha256": request["qobs_artifact_sha256"]},
        "decision": {"fresh": True, "sha256": request["decision_sha256"]},
        "scheduling_snapshot": {"non_placeholder": True, "sha256": request["scheduling_snapshot_sha256"]},
        "resolved_executable": {"safe": True, "sha256": request["resolved_executable_sha256"]},
        "account_identity": {"safe": True, "sha256": request["account_identity_sha256"]},
        "nonce": {"unused": True, "sha256": request["nonce_sha256"]},
        "runtime": (
            {"read_only": True, "mode": "plan", "sandbox": True}
            if provider == "agy"
            else {"read_only": True, "sandbox": "read-only"}
        ),
    }


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
    request = _request("codex1")
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
        _config(), request, _context(request), tmp_path, runner
    )
    assert events == ["admission", "marker", "spawn"]
    assert completed["receipt"]["alias"] == "codex1"
    assert completed["work_result"] == _work_result()
    assert command.effective_activation_state(_config()) == (True, "CLOSED")


def test_execution_accepts_only_the_four_one_shot_read_only_routes_and_safe_preflight(
    tmp_path: Path,
) -> None:
    calls: list[str] = []

    def runner(admission: object) -> dict[str, object]:
        alias = str(getattr(admission, "alias"))
        calls.append(alias)
        return _payload(_request(alias))

    for alias in ALIASES:
        request = _request(alias)
        completed = command.execute_idq_mvp_080_execution(
            _config(), request, _context(request), tmp_path, runner
        )
        assert completed["receipt"]["provider"] == ALIASES[alias]
    assert calls == list(ALIASES)

    rejected = [
        (_request("codex3"), _context(_request("codex3"))),
        (dict(_request("codex1"), attempt=2), _context(_request("codex1"))),
        (dict(_request("codex2"), qobs_quota_band="unknown"), _context(_request("codex2"))),
        (_request("agy1"), dict(_context(_request("agy1")), runtime={"read_only": True, "mode": "plan", "sandbox": False})),
    ]
    for request, context in rejected:
        with pytest.raises(command.ConfigurationError):
            command.execute_idq_mvp_080_execution(_config(), request, context, tmp_path, runner)
    assert calls == list(ALIASES)


@pytest.mark.parametrize("malformation", ["raw_stream", "no_receipt", "no_result", "bad_receipt"])
def test_execution_rejects_raw_or_unbound_provider_payloads(
    tmp_path: Path, malformation: str
) -> None:
    request = _request("codex1")

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
            _config(), request, _context(request), tmp_path, runner
        )


def test_execution_consumes_only_after_complete_preflight_and_never_retries(
    tmp_path: Path,
) -> None:
    request = _request("agy2")
    marker = tmp_path / "idq-mvp-080-agy2.used"
    calls: list[object] = []

    with pytest.raises(command.ConfigurationError):
        command.execute_idq_mvp_080_execution(
            _config(), request, dict(_context(request), qobs={"known": False}), tmp_path,
            lambda admission: calls.append(admission),
        )
    assert not marker.exists()
    assert calls == []

    def failing_runner(admission: object) -> dict[str, object]:
        calls.append(admission)
        raise command.ConfigurationError("synthetic provider failure")

    with pytest.raises(command.ConfigurationError, match="synthetic provider failure"):
        command.execute_idq_mvp_080_execution(
            _config(), request, _context(request), tmp_path, failing_runner
        )
    assert marker.exists()
    with pytest.raises(command.ConfigurationError, match="consumed|one.use"):
        command.execute_idq_mvp_080_execution(
            _config(), request, _context(request), tmp_path, failing_runner
        )
    assert len(calls) == 1
