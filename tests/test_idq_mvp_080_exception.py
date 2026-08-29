"""Frozen synthetic-only contract for the IDQ-MVP-080 provider exception.

The public API deliberately admits no provider command.  It validates one
preflight record and, separately, the provider-native receipt plus typed
``WorkResult``.  Source work must retain ordinary dispatcher activation as
closed; this exception is only a bounded admission object for the irreversible
start boundary owned elsewhere.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess

import pytest

import scripts.multiagent_prompt_command as command


TICKET = "IDQ-MVP-080"
ALIASES = {
    "codex1": "codex",
    "codex2": "codex",
    "agy1": "agy",
    "agy2": "agy",
}


def _digest(label: str) -> str:
    return hashlib.sha256(label.encode("ascii")).hexdigest()


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


def _request(alias: str = "codex1", **overrides: object) -> dict[str, object]:
    request: dict[str, object] = {
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
    request.update(overrides)
    return request


def _canonical_work_result_sha256(work_result: dict[str, object]) -> str:
    """The receipt binds the canonical normalized typed result, never a label."""

    material = json.dumps(
        work_result, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def _receipt(admission: object) -> tuple[dict[str, object], dict[str, object]]:
    result = {
        "status": "DONE",
        "scope_owned": ["read-only repository inventory"],
        "evidence": {"commands": [], "outcomes": ["synthetic"], "artifacts": []},
        "findings": ["synthetic typed result"],
        "changed_files": [],
        "residual_risk": "none",
        "recommended_next_action": "stop",
    }
    receipt = {
        "protocol_version": 2,
        "ticket": TICKET,
        "alias": admission.alias,
        "provider": admission.provider,
        "attempt": 1,
        "decision_sha256": admission.decision_sha256,
        "qobs_artifact_sha256": admission.qobs_artifact_sha256,
        "nonce_sha256": admission.nonce_sha256,
        "scheduling_snapshot_sha256": admission.scheduling_snapshot_sha256,
        "resolved_executable_sha256": admission.resolved_executable_sha256,
        "account_identity_sha256": admission.account_identity_sha256,
        "work_result_sha256": _canonical_work_result_sha256(result),
    }
    return receipt, result


def _forbid_provider_processes(monkeypatch: pytest.MonkeyPatch) -> list[object]:
    calls: list[object] = []

    def forbidden(*args: object, **kwargs: object) -> None:
        calls.append((args, kwargs))
        raise AssertionError("synthetic admission must not invoke a provider")

    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    return calls


def test_idq_mvp_080_is_exactly_four_read_only_one_shot_aliases_and_keeps_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _forbid_provider_processes(monkeypatch)
    config = _config()
    assert command.effective_activation_state(config) == (True, "CLOSED")

    admissions = [
        command.validate_idq_mvp_080_admission(config, _request(alias), tmp_path)
        for alias in ALIASES
    ]

    assert {admission.alias for admission in admissions} == set(ALIASES)
    assert {(admission.alias, admission.provider, admission.attempt) for admission in admissions} == {
        (alias, provider, 1) for alias, provider in ALIASES.items()
    }
    assert all(admission.work_mode == "read_only" for admission in admissions)
    assert calls == []


def test_idq_mvp_080_consumes_independent_one_use_alias_marker_without_retry_or_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _forbid_provider_processes(monkeypatch)
    config = _config()
    codex1 = command.validate_idq_mvp_080_admission(config, _request("codex1"), tmp_path)
    agy1 = command.validate_idq_mvp_080_admission(config, _request("agy1"), tmp_path)
    assert codex1.alias == "codex1"
    assert agy1.alias == "agy1"

    with pytest.raises(command.ConfigurationError, match="consumed|one.use|retry|fallback"):
        command.validate_idq_mvp_080_admission(config, _request("codex1"), tmp_path)
    with pytest.raises(command.ConfigurationError, match="attempt|retry|fallback"):
        command.validate_idq_mvp_080_admission(
            config, _request("codex2", attempt=2), tmp_path
        )
    assert calls == []


def test_idq_mvp_080_rejects_every_non_allowlisted_or_unbound_preflight(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _forbid_provider_processes(monkeypatch)
    config = _config()
    invalid_requests = [
        _request(ticket="IDQ-MVP-081"),
        _request(alias="codex3", provider="codex"),
        _request(attempt=0),
        _request(work_mode="workspace_write"),
        _request(automatic_retry=True),
        _request(fallback=True),
        _request(qobs_quota_band="healthy"),
        _request(decision_sha256="not-a-digest"),
        _request(nonce_sha256=""),
        _request(scheduling_snapshot_sha256=None),
        _request(resolved_executable_sha256=None),
        _request(account_identity_sha256=None),
    ]
    for request in invalid_requests:
        with pytest.raises(command.ConfigurationError):
            command.validate_idq_mvp_080_admission(config, request, tmp_path)
    assert calls == []


def test_idq_mvp_080_requires_receipt_v2_and_typed_workresult_to_rebind_all_digests(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _forbid_provider_processes(monkeypatch)
    admission = command.validate_idq_mvp_080_admission(_config(), _request(), tmp_path)
    receipt, work_result = _receipt(admission)

    validated = command.validate_idq_mvp_080_receipt(admission, receipt, work_result)
    assert validated["ticket"] == TICKET
    assert "raw_stream" not in validated
    for field in (
        "decision_sha256", "qobs_artifact_sha256", "nonce_sha256",
        "scheduling_snapshot_sha256", "resolved_executable_sha256",
        "account_identity_sha256", "work_result_sha256",
    ):
        tampered = deepcopy(receipt)
        tampered[field] = _digest(f"tampered:{field}")
        with pytest.raises(command.ConfigurationError):
            command.validate_idq_mvp_080_receipt(admission, tampered, work_result)
    substituted_result = deepcopy(work_result)
    substituted_result["findings"] = ["substituted typed result"]
    with pytest.raises(command.ConfigurationError):
        command.validate_idq_mvp_080_receipt(admission, receipt, substituted_result)
    with pytest.raises(command.ConfigurationError):
        command.validate_idq_mvp_080_receipt(
            admission, dict(receipt, raw_stream="forbidden"), work_result
        )
    assert calls == []
