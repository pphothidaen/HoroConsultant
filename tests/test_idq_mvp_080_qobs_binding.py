"""RED QOBS-binding contract for the IDQ-MVP-080 fake provider adapter.

The adapter is permitted to use only a genuine, fresh QOBS v1 artifact made by
the local quota guard.  Caller-created ``{"sha256": ...}`` claims are not
QOBS evidence and must fail before either one-shot marker or subprocess seam.
"""

from __future__ import annotations

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
ALIASES = {
    "codex1": "codex",
    "codex2": "codex",
    "codex3": "codex",
    "agy1": "agy",
    "agy2": "agy",
    "agy3": "agy",
    "agy4": "agy",
}


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


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


def _qobs_context(
    alias: str, *, observed_at: datetime | None = None, nonce: str | None = None
) -> dict[str, object]:
    provider = ALIASES[alias]
    timestamp = observed_at or datetime.now(timezone.utc)
    return {
        "alias": alias,
        "provider": provider,
        "account_home": f"/private/idq-mvp-080/{alias}",
        "resolved_executable": f"/opt/idq-mvp-080/{provider}",
        "ticket_id": TICKET,
        "attempt_id": 1,
        "policy_version": "2026-08-26.1",
        "nonce": nonce or f"idq-mvp-080-{alias}-nonce",
        "observed_at": timestamp.isoformat(timespec="seconds").replace("+00:00", "Z"),
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


def _execution_context(
    artifact: dict[str, object], context: dict[str, object], provider: str
) -> dict[str, object]:
    return {
        "qobs_artifact": artifact,
        "qobs_expected_context": context,
        "runtime": (
            {"read_only": True, "sandbox": "read-only"}
            if provider == "codex"
            else {"read_only": True, "mode": "plan", "sandbox": True}
        ),
    }


def _legacy_hash_only_context(request: dict[str, object]) -> dict[str, object]:
    """The unsafe compatibility shape which must no longer be an admission."""

    return {
        "qobs": {"known": True, "quota_band": "constrained", "sha256": request["qobs_artifact_sha256"]},
        "decision": {"fresh": True, "sha256": request["decision_sha256"]},
        "scheduling_snapshot": {"non_placeholder": True, "sha256": request["scheduling_snapshot_sha256"]},
        "resolved_executable": {"safe": True, "sha256": request["resolved_executable_sha256"]},
        "account_identity": {"safe": True, "sha256": request["account_identity_sha256"]},
        "nonce": {"unused": True, "sha256": request["nonce_sha256"]},
        "runtime": {"read_only": True, "sandbox": "read-only"},
    }


def _work_result() -> dict[str, object]:
    return {
        "status": "DONE",
        "scope_owned": ["read-only repository inventory"],
        "evidence": {"commands": [], "outcomes": ["synthetic"], "artifacts": []},
        "findings": ["synthetic QOBS binding result"],
        "changed_files": [],
        "residual_risk": "none",
        "recommended_next_action": "stop",
    }


def _codex_output() -> str:
    return "\n".join(
        json.dumps(event, separators=(",", ":"))
        for event in (
            {"type": "thread.started", "thread_id": "codex-qobs-binding"},
            {"type": "item.completed", "item": {"type": "agent_message", "text": json.dumps(_work_result())}},
            {"type": "turn.completed"},
        )
    ) + "\n"


def _runner(events: list[str]) -> Any:
    def run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        events.append("subprocess")
        return subprocess.CompletedProcess(args[0], 0, stdout=_codex_output(), stderr="")

    return run


def test_adapter_uses_one_genuine_qobs_validation_at_the_final_start_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    context = _qobs_context("codex1")
    artifact = quota.probe_quota_observation(_signals(), context)
    request = _request("codex1", context, artifact)
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
        _config(), request, _execution_context(artifact, context, "codex"), tmp_path, _runner(events)
    )

    assert events == ["qobs", "marker", "subprocess"]
    assert completed["receipt"]["qobs_artifact_sha256"] == quota.quota_artifact_sha256(artifact)
    assert command.effective_activation_state(_config()) == (True, "CLOSED")


@pytest.mark.parametrize("case", ("fabricated", "stale", "unknown", "mismatched"))
def test_adapter_rejects_non_genuine_or_non_matching_qobs_before_marker_or_subprocess(
    tmp_path: Path, case: str
) -> None:
    alias = "codex1"
    context = _qobs_context(alias)
    artifact = quota.probe_quota_observation(_signals(), context)
    request = _request(alias, context, artifact)
    execution_context: dict[str, object] = _execution_context(artifact, context, "codex")
    if case == "fabricated":
        execution_context = _legacy_hash_only_context(request)
    elif case == "stale":
        context = _qobs_context(alias, observed_at=datetime.now(timezone.utc) - timedelta(minutes=5))
        artifact = quota.probe_quota_observation(_signals(), context)
        request = _request(alias, context, artifact)
        execution_context = _execution_context(artifact, context, "codex")
    elif case == "unknown":
        artifact = quota.probe_quota_observation({}, context)
        request = _request(alias, context, artifact)
        execution_context = _execution_context(artifact, context, "codex")
    else:
        source_context = _qobs_context("codex2")
        artifact = quota.probe_quota_observation(_signals(), source_context)
        request = _request(alias, context, artifact)
        execution_context = _execution_context(artifact, context, "codex")

    calls: list[str] = []
    with pytest.raises((command.ConfigurationError, quota.QuotaObservationError)):
        command.execute_idq_mvp_080_provider_adapter(
            _config(), request, execution_context, tmp_path, _runner(calls)
        )
    assert calls == []
    assert not (tmp_path / f"idq-mvp-080-{alias}.used").exists()


def test_adapter_rejects_replayed_qobs_before_a_second_alias_marker_or_subprocess(
    tmp_path: Path
) -> None:
    context = _qobs_context("codex1")
    artifact = quota.probe_quota_observation(_signals(), context)
    request = _request("codex1", context, artifact)
    execution_context = _execution_context(artifact, context, "codex")
    first_calls: list[str] = []
    command.execute_idq_mvp_080_provider_adapter(
        _config(), request, execution_context, tmp_path, _runner(first_calls)
    )
    assert first_calls == ["subprocess"]

    second_calls: list[str] = []
    with pytest.raises((command.ConfigurationError, quota.QuotaObservationError), match="CONSUMED|consumed|nonce|replay"):
        command.execute_idq_mvp_080_provider_adapter(
            _config(), request, execution_context, tmp_path, _runner(second_calls)
        )
    assert second_calls == []
