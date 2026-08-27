"""Frozen cross-module QOBS probe, dispatch, receipt, and scheduler tests."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import subprocess

import pytest

import scripts.agent_quota_status_guard as quota
import scripts.multiagent_prompt_command as command
import scripts.multiagent_ticket_scheduler as scheduler


NOW = datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc)


def _context(**overrides: object) -> dict[str, object]:
    context: dict[str, object] = {
        "alias": "codex1",
        "provider": "codex",
        "account_home": "/private/account-one",
        "resolved_executable": "/opt/local/bin/codex",
        "ticket_id": "TICKET-QOBS-INTEGRATION",
        "attempt_id": 1,
        "policy_version": "2026-08-26.1",
        "nonce": "qobs-integration-nonce-0001",
        "observed_at": "2026-08-27T12:00:00Z",
    }
    context.update(overrides)
    return context


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

    return {
        **values(),
        "buckets": {"primary": values(), "secondary": values()},
    }


def _artifact(*, remaining: float = 10.0, context: dict[str, object] | None = None):
    return quota.probe_quota_observation(_signals(remaining), context or _context())


def _decision(**overrides: object) -> dict[str, object]:
    decision: dict[str, object] = {
        "schema_version": 1,
        "ticket": "TICKET-QOBS-INTEGRATION",
        "phase": "implementation",
        "scope_rank": 3,
        "complexity_rank": 3,
        "risk_rank": 3,
        "ambiguity_rank": 2,
        "evidence_burden_rank": 3,
        "quota_band": "constrained",
        "work_mode": "mutation",
        "selected_alias": "codex1",
        "selected_model": "gpt-5.6-sol",
        "selected_effort": "high",
        "rationale": "QOBS integration fixture",
        "policy_version": "2026-08-26.1",
        "planning_to_medium_confirmed": True,
        "hitl_approved": True,
    }
    decision.update(overrides)
    return decision


def _snapshot(*, quota_passed: bool = True, reservation: bool = False):
    ticket = {
        "ticket_id": "TICKET-QOBS-INTEGRATION",
        "severity": "CRITICAL",
        "work_effort": "S",
        "status": "READY" if not reservation else "DOING",
        "dependencies": [],
        "blockers": [],
        "owner": "developer",
        "ownership": ["scripts/qobs-owned.py"],
        "quota_passed": quota_passed,
        "hitl_passed": True,
        "rule18_decision_valid": True,
    }
    reservations = []
    if reservation:
        reservations.append(
            {
                "ticket_id": ticket["ticket_id"],
                "owner": ticket["owner"],
                "ownership": ticket["ownership"],
            }
        )
    return scheduler.validate_snapshot(
        {"schema_version": 1, "tickets": [ticket], "reservations": reservations}
    )


def _gate(
    artifact: dict[str, object],
    *,
    context: dict[str, object] | None = None,
    decision: dict[str, object] | None = None,
    reservation_ticket_id: str | None = None,
) -> dict[str, object]:
    return {
        "artifact": artifact,
        "context": context or _context(),
        "decision": decision or _decision(),
        "reservation_ticket_id": reservation_ticket_id,
        "now": NOW,
    }


def test_probe_emits_exactly_one_artifact_and_never_dispatches_or_retries(monkeypatch) -> None:
    calls: list[object] = []

    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("probe attempted execution")

    monkeypatch.setattr(command, "execute_invocation", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)

    artifact = quota.probe_quota_observation(_signals(), _context())

    assert artifact["schema_version"] == 1
    assert artifact["observation"]["quota_band"] == "constrained"
    assert calls == []


@pytest.mark.parametrize(
    "age,accepted,code",
    [
        (timedelta(seconds=60), True, None),
        (timedelta(seconds=60, microseconds=1), False, "STALE_OBSERVATION"),
        (timedelta(seconds=-5), True, None),
        (timedelta(seconds=-5, microseconds=-1), False, "FUTURE_OBSERVATION"),
    ],
)
def test_age_and_future_tolerance_are_exact(
    age: timedelta, accepted: bool, code: str | None
) -> None:
    observed = NOW - age
    context = _context(observed_at=observed.isoformat().replace("+00:00", "Z"))
    artifact = _artifact(context=context)

    if accepted:
        validated = quota.validate_quota_observation(artifact, context, now=NOW)
        assert validated["nonce"] == context["nonce"]
    else:
        with pytest.raises(quota.QuotaObservationError) as exc:
            quota.validate_quota_observation(artifact, context, now=NOW)
        assert exc.value.code == code


@pytest.mark.parametrize(
    "field,replacement",
    [
        ("alias", "codex2"),
        ("provider", "agy"),
        ("account_home", "/private/substituted-home"),
        ("resolved_executable", "/opt/local/bin/substituted"),
        ("ticket_id", "TICKET-SUBSTITUTED"),
        ("attempt_id", 2),
        ("policy_version", "other-policy"),
        ("nonce", "other-nonce"),
    ],
)
def test_expected_nonce_digest_and_provenance_mismatches_are_rejected(
    field: str, replacement: object
) -> None:
    context = _context()
    artifact = _artifact(context=context)
    expected = dict(context)
    expected[field] = replacement

    with pytest.raises(quota.QuotaObservationError) as exc:
        quota.validate_quota_observation(artifact, expected, now=NOW)
    assert exc.value.code == "PROVENANCE_MISMATCH"


def test_malformed_unknown_nonfinite_and_digest_tamper_are_not_dispatchable() -> None:
    valid = _artifact()
    tampered = deepcopy(valid)
    tampered["observation"]["quota_band"] = "below_10_percent"
    unknown = quota.probe_quota_observation("not-json", _context())

    with pytest.raises(quota.QuotaObservationError) as digest_error:
        quota.validate_quota_observation(tampered, _context(), now=NOW)
    assert digest_error.value.code == "DIGEST_MISMATCH"
    with pytest.raises(quota.QuotaObservationError) as unknown_error:
        command.consume_quota_observation(
            unknown, _context(), nonce_store=None, now=NOW
        )
    assert unknown_error.value.code == "UNKNOWN_QUOTA"


def test_dispatch_consumes_the_exact_nonce_once_atomically(tmp_path) -> None:
    artifact = _artifact()
    store = tmp_path / "qobs-nonces"

    def consume():
        try:
            return command.consume_quota_observation(
                artifact, _context(), nonce_store=store, now=NOW
            )
        except quota.QuotaObservationError as exc:
            return exc.code

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(lambda _: consume(), range(2)))

    successes = [item for item in outcomes if isinstance(item, dict)]
    failures = [item for item in outcomes if isinstance(item, str)]
    assert len(successes) == 1
    assert failures == ["REPLAYED_OBSERVATION"]
    assert successes[0]["artifact_sha256"] == quota.quota_artifact_sha256(artifact)
    assert successes[0]["nonce_sha256"] == quota.sha256_text(_context()["nonce"])


def test_dispatch_decision_v1_cannot_execute_even_with_valid_qobs(monkeypatch, tmp_path) -> None:
    calls: list[object] = []

    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("v1 decision reached process creation")

    monkeypatch.setattr(subprocess, "run", forbidden)
    artifact = _artifact()

    with pytest.raises(command.DispatchDecisionError, match="v1.*non-executable"):
        command.validate_quota_bound_dispatch(
            _decision(),
            artifact,
            _context(),
            nonce_store=tmp_path / "qobs-nonces",
            now=NOW,
        )
    assert calls == []


def test_receipt_v2_transitively_binds_exact_artifact_consumption_and_dispatch_context(
    tmp_path,
) -> None:
    artifact = _artifact()
    consumption = command.consume_quota_observation(
        artifact, _context(), nonce_store=tmp_path / "qobs-nonces", now=NOW
    )
    dispatch_context = {
        "decision_sha256": "d" * 64,
        "scheduling_snapshot_sha256": "e" * 64,
        "resolved_executable_sha256": artifact["observation"][
            "resolved_executable_sha256"
        ],
        "policy_version": "2026-08-26.1",
    }
    identity = command.quota_bound_dispatch_identity(
        artifact, consumption, dispatch_context
    )
    receipt = {
        "protocol_version": 2,
        "dispatch_identity": identity,
        "quota_status": "constrained",
    }

    assert command.validate_quota_receipt_binding(
        receipt, artifact, consumption, dispatch_context, _context(), now=NOW
    ) == receipt

    for key in dispatch_context:
        changed_context = dict(dispatch_context)
        changed_context[key] = (
            "f" * 64 if key.endswith("sha256") else "substituted-policy"
        )
        with pytest.raises(command.ConfigurationError):
            command.validate_quota_receipt_binding(
                receipt,
                artifact,
                consumption,
                changed_context,
                _context(),
                now=NOW,
            )

    changed_artifact = deepcopy(artifact)
    changed_artifact["observation"]["reason_code"] = "invalid_signal"
    with pytest.raises(command.ConfigurationError):
        command.validate_quota_receipt_binding(
            receipt,
            changed_artifact,
            consumption,
            dispatch_context,
            _context(),
            now=NOW,
        )
    changed_consumption = dict(consumption, nonce_sha256="0" * 64)
    with pytest.raises(command.ConfigurationError):
        command.validate_quota_receipt_binding(
            receipt,
            artifact,
            changed_consumption,
            dispatch_context,
            _context(),
            now=NOW,
        )


def test_scheduler_validates_qobs_before_rule11_selection_or_reservation() -> None:
    valid = _artifact()
    selected = scheduler.select_tickets_with_quota(
        _snapshot(), _gate(valid), capacity=1
    )
    assert selected[0].ticket.ticket_id == "TICKET-QOBS-INTEGRATION"

    unknown = quota.probe_quota_observation("not-json", _context())
    with pytest.raises(scheduler.SchedulingError) as exc:
        scheduler.select_tickets_with_quota(
            _snapshot(), _gate(unknown), capacity=1
        )
    assert exc.value.code == "INVALID_QUOTA_OBSERVATION"


@pytest.mark.parametrize(
    "snapshot,decision,reservation_ticket_id",
    [
        (_snapshot(quota_passed=False), _decision(), None),
        (_snapshot(), _decision(quota_band="below_10_percent"), None),
        (_snapshot(), _decision(ticket="TICKET-OTHER"), None),
        (_snapshot(), _decision(policy_version="other-policy"), None),
        (_snapshot(reservation=True), _decision(), "TICKET-OTHER"),
    ],
)
def test_scheduler_rejects_ticket_decision_reservation_policy_and_quota_contradictions(
    snapshot, decision: dict[str, object], reservation_ticket_id: str | None
) -> None:
    artifact = _artifact()

    with pytest.raises(scheduler.SchedulingError) as exc:
        scheduler.select_tickets_with_quota(
            snapshot,
            _gate(
                artifact,
                decision=decision,
                reservation_ticket_id=reservation_ticket_id,
            ),
            capacity=1,
        )
    assert exc.value.code == "QUOTA_CONTRADICTION"


def test_below_ten_and_unknown_never_become_executable_by_sorting() -> None:
    for artifact in (
        _artifact(remaining=9.9999),
        quota.probe_quota_observation({"unexpected": True}, _context()),
    ):
        with pytest.raises(scheduler.SchedulingError):
            scheduler.select_tickets_with_quota(
                _snapshot(), _gate(artifact), capacity=1
            )
