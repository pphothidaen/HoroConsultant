"""Unified red contract for the bounded IDQ-MVP-080 QOBS exception.

This is a fake-runner-only compatibility baseline.  It does not authorize a
provider process, network call, account login, retry, or fallback.  The source
seam must keep ordinary activation CLOSED while admitting only the four named,
one-shot, read-only routes after a genuine fresh QOBS v1 validation.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

import pytest

import scripts.agent_quota_status_guard as quota
import scripts.multiagent_prompt_command as command


TICKET = "IDQ-MVP-080"
ALIASES = {"codex1": "codex", "codex2": "codex", "agy1": "agy", "agy2": "agy"}


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


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


def _signals(remaining: float = 10.0) -> dict[str, object]:
    values = {
        "usedPercent": 100.0 - remaining,
        "remainingPercent": remaining,
        "reached": remaining == 0.0,
        "limit": 100.0,
        "spend": 100.0 - remaining,
        "remaining": remaining,
    }
    return {**values, "buckets": {"primary": dict(values), "secondary": dict(values)}}


def _qobs_context(alias: str, *, observed_at: datetime | None = None) -> dict[str, object]:
    instant = observed_at or datetime.now(timezone.utc)
    provider = ALIASES[alias]
    return {
        "alias": alias,
        "provider": provider,
        "account_home": f"/private/idq-mvp-080/{alias}",
        "resolved_executable": f"/opt/idq-mvp-080/{provider}",
        "ticket_id": TICKET,
        "attempt_id": 1,
        "policy_version": "2026-08-26.1",
        "nonce": f"idq-mvp-080-{alias}-nonce",
        "observed_at": instant.isoformat(timespec="seconds").replace("+00:00", "Z"),
    }


def _request(alias: str, context: dict[str, object], artifact: dict[str, object]) -> dict[str, object]:
    return {
        "ticket": TICKET,
        "alias": alias,
        "provider": ALIASES[alias],
        "attempt": 1,
        "work_mode": "read_only",
        "automatic_retry": False,
        "fallback": False,
        "decision_sha256": _digest(f"decision:{alias}"),
        "qobs_artifact_sha256": quota.quota_artifact_sha256(artifact),
        "qobs_quota_band": "constrained",
        "nonce_sha256": quota.sha256_text(str(context["nonce"])),
        "scheduling_snapshot_sha256": _digest(f"snapshot:{alias}"),
        "resolved_executable_sha256": quota.sha256_text(str(context["resolved_executable"])),
        "account_identity_sha256": quota.sha256_text(str(context["account_home"])),
        "lease_risk_sha256": _digest(f"lease:{alias}"),
    }


def _context(artifact: dict[str, object], qobs: dict[str, object]) -> dict[str, object]:
    provider = str(qobs["provider"])
    return {
        "qobs_artifact": artifact,
        "qobs_expected_context": qobs,
        "runtime": (
            {"read_only": True, "sandbox": "read-only"}
            if provider == "codex"
            else {"read_only": True, "mode": "plan", "sandbox": True}
        ),
    }


def _result(status: str = "DONE") -> dict[str, object]:
    return {
        "status": status,
        "scope_owned": ["read-only repository inventory"],
        "evidence": {"commands": [], "outcomes": ["synthetic"], "artifacts": []},
        "findings": ["synthetic QOBS compatibility result"],
        "changed_files": [],
        "residual_risk": "none",
        "recommended_next_action": "stop",
    }


def _codex_output(result: dict[str, object]) -> str:
    return "\n".join(json.dumps(item, separators=(",", ":")) for item in (
        {"type": "thread.started", "thread_id": "codex-idq-080"},
        {"type": "item.completed", "item": {"type": "agent_message", "text": json.dumps(result)}},
        {"type": "turn.completed"},
    )) + "\n"


def _agy_output(result: dict[str, object]) -> str:
    return "\n".join(json.dumps(item, separators=(",", ":")) for item in (
        {"event": "init", "conversation_id": "agy-idq-080", "init": {}},
        {"event": "result", "result": {"conversation_id": "agy-idq-080", "status": "SUCCESS", "structured_output": result}},
    )) + "\n"


def _runner(events: list[str], payload: str) -> Any:
    def run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        events.append("subprocess")
        return subprocess.CompletedProcess(args[0], 0, stdout=payload, stderr="")

    return run


def _fixture(alias: str = "codex1") -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    qobs = _qobs_context(alias)
    artifact = quota.probe_quota_observation(_signals(), qobs)
    return artifact, qobs, _request(alias, qobs, artifact)


def test_exception_is_exactly_four_closed_read_only_one_shot_routes(tmp_path: Path) -> None:
    artifact, qobs, request = _fixture()
    assert command.effective_activation_state(_config()) == (True, "CLOSED")
    admissions = [
        command.validate_idq_mvp_080_admission(
            _config(), _request(alias, *_fixture(alias)[:2][::-1]), tmp_path
        )
        for alias in ALIASES
    ]
    assert {(item.alias, item.provider, item.attempt) for item in admissions} == {
        (alias, provider, 1) for alias, provider in ALIASES.items()
    }
    with pytest.raises(command.ConfigurationError):
        command.validate_idq_mvp_080_admission(_config(), dict(request, attempt=2), tmp_path)
    assert artifact and qobs


def test_receipt_rebinds_every_identity_digest_and_canonical_work_result(tmp_path: Path) -> None:
    artifact, qobs, request = _fixture()
    admission = command.validate_idq_mvp_080_admission(_config(), request, tmp_path)
    result = _result()
    receipt = {
        "protocol_version": 2, "ticket": TICKET, "alias": "codex1", "provider": "codex", "attempt": 1,
        **{field: request[field] for field in (
            "decision_sha256", "qobs_artifact_sha256", "nonce_sha256", "scheduling_snapshot_sha256",
            "resolved_executable_sha256", "account_identity_sha256",
        )},
        "work_result_sha256": _digest(json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=True)),
    }
    assert command.validate_idq_mvp_080_receipt(admission, receipt, result)["ticket"] == TICKET
    for field in ("nonce_sha256", "qobs_artifact_sha256", "work_result_sha256"):
        tampered = deepcopy(receipt)
        tampered[field] = _digest(f"tampered:{field}")
        with pytest.raises(command.ConfigurationError):
            command.validate_idq_mvp_080_receipt(admission, tampered, result)
    assert artifact and qobs


def test_adapter_validates_genuine_qobs_before_marker_and_fake_subprocess(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    artifact, qobs, request = _fixture()
    events: list[str] = []
    original_validate = quota.validate_quota_observation
    original_marker = command._consume_idq_mvp_080_marker

    def observe_validate(*args: Any, **kwargs: Any) -> dict[str, object]:
        events.append("qobs")
        return original_validate(*args, **kwargs)

    def observe_marker(*args: Any, **kwargs: Any) -> None:
        events.append("marker")
        original_marker(*args, **kwargs)

    monkeypatch.setattr(quota, "validate_quota_observation", observe_validate)
    monkeypatch.setattr(command, "_consume_idq_mvp_080_marker", observe_marker)
    completed = command.execute_idq_mvp_080_provider_adapter(
        _config(), request, _context(artifact, qobs), tmp_path, _runner(events, _codex_output(_result()))
    )
    assert events == ["qobs", "marker", "subprocess"]
    assert completed["receipt"]["qobs_artifact_sha256"] == quota.quota_artifact_sha256(artifact)


@pytest.mark.parametrize("case", ("digest_only", "stale", "unknown", "mismatched", "replayed"))
def test_adapter_rejects_invalid_qobs_before_marker_or_fake_subprocess(tmp_path: Path, case: str) -> None:
    artifact, qobs, request = _fixture()
    context: dict[str, object] = _context(artifact, qobs)
    if case == "digest_only":
        context = {"qobs": {"known": True, "sha256": request["qobs_artifact_sha256"]}, "runtime": {"read_only": True, "sandbox": "read-only"}}
    elif case == "stale":
        artifact, qobs, request = _fixture_with_time("codex1", datetime.now(timezone.utc) - timedelta(minutes=5))
        context = _context(artifact, qobs)
    elif case == "unknown":
        artifact = quota.probe_quota_observation({}, qobs)
        request = _request("codex1", qobs, artifact)
        context = _context(artifact, qobs)
    elif case == "mismatched":
        other_artifact, other_qobs, _ = _fixture("codex2")
        context = _context(other_artifact, other_qobs)
    elif case == "replayed":
        command.execute_idq_mvp_080_provider_adapter(_config(), request, context, tmp_path, _runner([], _codex_output(_result())))
    calls: list[str] = []
    with pytest.raises((command.ConfigurationError, quota.QuotaObservationError)):
        command.execute_idq_mvp_080_provider_adapter(_config(), request, context, tmp_path, _runner(calls, _codex_output(_result())))
    assert calls == []


def _fixture_with_time(alias: str, observed_at: datetime) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    qobs = _qobs_context(alias, observed_at=observed_at)
    artifact = quota.probe_quota_observation(_signals(), qobs)
    return artifact, qobs, _request(alias, qobs, artifact)


@pytest.mark.parametrize("alias", tuple(ALIASES))
def test_adapter_uses_exact_read_only_native_argv_and_never_persists_raw_output(tmp_path: Path, alias: str) -> None:
    artifact, qobs, request = _fixture(alias)
    payload = _codex_output(_result()) if ALIASES[alias] == "codex" else _agy_output(_result())
    calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

    def runner(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append((args, kwargs))
        return subprocess.CompletedProcess(args[0], 0, stdout=payload, stderr="")

    completed = command.execute_idq_mvp_080_provider_adapter(_config(), request, _context(artifact, qobs), tmp_path, runner)
    argv = tuple(calls[0][0][0])
    if ALIASES[alias] == "codex":
        assert argv == ("codex", "exec", "-C", str(command.REPOSITORY_ROOT), "-s", "read-only", "--json", "-")
    else:
        assert argv == ("agy", "--mode", "plan", "--sandbox", "--print", "--input-format", "stream-json", "--output-format", "stream-json")
    assert calls[0][1]["shell"] is False
    assert completed["work_result"] == _result()
    assert not any(payload.encode() in path.read_bytes() for path in tmp_path.rglob("*") if path.is_file())
