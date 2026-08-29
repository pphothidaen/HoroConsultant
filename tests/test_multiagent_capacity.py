"""Focused contract tests for the provider-free S3 capacity lease store."""
from __future__ import annotations

import concurrent.futures
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from multiagent_capacity import (  # noqa: E402
    InvalidPolicyError,
    LeaseRejectedError,
    acquire_lease,
    capacity_snapshot,
    clear_backpressure,
    consume_lease,
    drain_queue,
    enqueue_request,
    record_failure,
    record_retry,
    release_lease,
    release_retry,
    reserve_retry,
    reset_circuit,
    set_backpressure,
    validate_capacity_policy,
    validate_capacity_state,
)


@pytest.fixture
def policy() -> dict:
    return json.loads((Path(__file__).parents[1] / ".agents/config/s3_capacity_policy.json").read_text())


def acquire(tmp_path: Path, policy: dict, account: str = "agy1", request_id: str = "request-1", now: int = 100):
    return acquire_lease(tmp_path, account=account, request_id=request_id, owner="root-a", lane=1,
                         request_budget=5, model_quality_floor="flash", policy=policy, now=now)


def test_policy_requires_explicit_five_account_caps(policy: dict) -> None:
    assert policy["reserve_ratio"] == 0.10
    assert policy["quota_basis"] == "verified_quota_only"
    assert policy["unknown_quota_behavior"] == "configured_placeholder"
    assert policy["idempotency_ttl_seconds"] == 86400
    assert policy["retry_max_attempts"] == 3
    validated = validate_capacity_policy(policy)
    assert validated["accounts"]["codex1"]["max_workers"] == 2
    assert validated["accounts"]["codex2"]["max_workers"] == 2
    assert validated["accounts"]["codex3"]["max_workers"] == 2
    assert validated["accounts"]["agy1"]["max_workers"] == 3
    assert validated["accounts"]["agy2"]["max_workers"] == 3
    broken = copy.deepcopy(policy)
    del broken["accounts"]["codex1"]["max_workers"]
    with pytest.raises(InvalidPolicyError, match="ACCOUNT_POLICY_INVALID"):
        validate_capacity_policy(broken)
    broken = copy.deepcopy(policy); broken["accounts"]["agy1"]["max_workers"] = 4
    with pytest.raises(InvalidPolicyError, match="AGY_MAX_WORKERS_MUST_BE_3"):
        validate_capacity_policy(broken)


def test_agy_cap_and_account_isolation_without_borrowing(tmp_path: Path, policy: dict) -> None:
    leases = [acquire(tmp_path, policy, request_id=f"agy-{number}") for number in range(3)]
    with pytest.raises(LeaseRejectedError, match="OVER_CAPACITY"):
        acquire(tmp_path, policy, request_id="agy-over")
    codex = acquire(tmp_path, policy, "codex1", "codex-1")
    assert codex.account == "codex1" and len(leases) == 3
    forged = codex.to_dict(); forged["account"] = forged["pool"] = "agy1"
    with pytest.raises(LeaseRejectedError):
        consume_lease(tmp_path, forged, requests=1, policy=policy, now=101)


def test_live_ttl_atomic_consumption_and_overrun(tmp_path: Path, policy: dict) -> None:
    lease = acquire(tmp_path, policy)
    used = consume_lease(tmp_path, lease, requests=3, policy=policy, now=101)
    assert used.requests_used == 3 and used.remaining_budget == 2
    with pytest.raises(LeaseRejectedError, match="BUDGET_OVERRUN"):
        consume_lease(tmp_path, used, requests=3, policy=policy, now=102)
    with pytest.raises(LeaseRejectedError, match="LEASE_EXPIRED"):
        consume_lease(tmp_path, used, requests=1, policy=policy, now=400)


def test_release_replay_and_tamper_rejection(tmp_path: Path, policy: dict) -> None:
    lease = acquire(tmp_path, policy)
    tampered = lease.to_dict(); tampered["owner"] = "other-owner"
    with pytest.raises(LeaseRejectedError):
        release_lease(tmp_path, tampered, policy=policy, now=101)
    released = release_lease(tmp_path, lease, policy=policy, requests_used=2, now=101)
    assert released.requests_used == 2
    with pytest.raises(LeaseRejectedError, match="REPLAY_REJECTED"):
        release_lease(tmp_path, released, policy=policy, now=102)


def test_persisted_lease_tampering_is_rejected(tmp_path: Path, policy: dict) -> None:
    lease = acquire(tmp_path, policy)
    state_path = tmp_path / ".capacity.json"
    state = json.loads(state_path.read_text())
    state["leases"][lease.lease_id]["requests_used"] = 1
    state_path.write_text(json.dumps(state))
    with pytest.raises(LeaseRejectedError, match="STATE_INVALID"):
        consume_lease(tmp_path, lease, requests=1, policy=policy, now=101)


def test_concurrent_acquire_never_exceeds_account_cap(tmp_path: Path, policy: dict) -> None:
    def worker(index: int) -> str:
        try:
            acquire(tmp_path, policy, request_id=f"parallel-{index}")
            return "acquired"
        except LeaseRejectedError as error:
            return error.code
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        outcomes = list(executor.map(worker, range(8)))
    assert outcomes.count("acquired") == 3
    assert outcomes.count("OVER_CAPACITY") == 5


def test_concurrent_consumption_cannot_overrun_cumulative_budget(tmp_path: Path, policy: dict) -> None:
    lease = acquire(tmp_path, policy)
    def consume_once(_: int) -> str:
        try:
            consume_lease(tmp_path, lease, requests=1, policy=policy, now=101)
            return "consumed"
        except LeaseRejectedError as error:
            return error.code
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        outcomes = list(executor.map(consume_once, range(8)))
    # Stale handles are rejected after the first charge, rather than letting
    # multiple callers borrow the same request budget.
    assert outcomes.count("consumed") == 1
    assert outcomes.count("LEASE_MISMATCH") == 7


def test_burn_rate_blocks_consumption_and_new_account_local_admission(tmp_path: Path, policy: dict) -> None:
    constrained = copy.deepcopy(policy)
    constrained["accounts"]["agy1"]["burn_rate"] = {"max_requests": 2, "window_seconds": 10}
    lease = acquire(tmp_path, constrained)
    consumed = consume_lease(tmp_path, lease, requests=2, policy=constrained, now=101)
    with pytest.raises(LeaseRejectedError, match="BURN_RATE_EXCEEDED"):
        acquire(tmp_path, constrained, request_id="burn-blocked")
    # No cross-account borrowing is implied by pressure in agy1.
    assert acquire(tmp_path, constrained, account="agy2", request_id="agy2-independent").account == "agy2"
    snap = capacity_snapshot(tmp_path, policy=constrained, now=102)
    assert snap["accounts"]["agy1"]["admission_state"] == "S4"
    assert snap["accounts"]["agy1"]["burn_rate"]["requests_in_window"] == consumed.requests_used
    assert acquire(tmp_path, constrained, request_id="burn-window-expired", now=112).account == "agy1"


def test_backpressure_blocks_or_queues_only_the_affected_account(tmp_path: Path, policy: dict) -> None:
    set_backpressure(tmp_path, account="agy1", mode="block", duration_seconds=20, policy=policy, now=100)
    with pytest.raises(LeaseRejectedError, match="BACKPRESSURE_BLOCKED"):
        acquire(tmp_path, policy, request_id="blocked", now=101)
    assert acquire(tmp_path, policy, account="agy2", request_id="other-pool",).account == "agy2"
    snap = capacity_snapshot(tmp_path, policy=policy, now=101)
    assert snap["accounts"]["agy1"]["admission_state"] == "S4"
    assert snap["accounts"]["agy1"]["backpressure"]["mode"] == "block"
    with pytest.raises(LeaseRejectedError, match="BACKPRESSURE_RESET_NOT_ALLOWED"):
        clear_backpressure(tmp_path, account="agy1", policy=policy, now=101)
    assert acquire(tmp_path, policy, request_id="pressure-expired", now=120).account == "agy1"
    set_backpressure(tmp_path, account="agy1", mode="queue", duration_seconds=10, policy=policy, now=130)
    with pytest.raises(LeaseRejectedError, match="BACKPRESSURE_QUEUED"):
        acquire(tmp_path, policy, request_id="queued", now=131)


def test_pool_local_circuit_trips_then_resets_only_by_policy_cooldown(tmp_path: Path, policy: dict) -> None:
    constrained = copy.deepcopy(policy)
    constrained["accounts"]["codex1"]["circuit_breaker"].update({"failure_threshold": 2, "failure_window_seconds": 10, "cooldown_seconds": 20})
    assert not record_failure(tmp_path, account="codex1", failure_type="timeout", policy=constrained, now=100)
    assert record_failure(tmp_path, account="codex1", failure_type="rate_limit", policy=constrained, now=101)
    with pytest.raises(LeaseRejectedError, match="CIRCUIT_OPEN"):
        acquire(tmp_path, constrained, account="codex1", request_id="circuit-blocked", now=102)
    # A trip has no cross-account fallback or downgrade behavior.
    assert acquire(tmp_path, constrained, account="codex2", request_id="codex2-independent", now=102).account == "codex2"
    with pytest.raises(LeaseRejectedError, match="CIRCUIT_RESET_NOT_ALLOWED"):
        reset_circuit(tmp_path, account="codex1", policy=constrained, now=102)
    assert acquire(tmp_path, constrained, account="codex1", request_id="cooled", now=121).account == "codex1"


def test_explicit_resets_require_and_honor_policy_authorization(tmp_path: Path, policy: dict) -> None:
    authorized = copy.deepcopy(policy)
    authorized["backpressure"]["allow_manual_reset"] = True
    authorized["accounts"]["agy1"]["circuit_breaker"].update({"allow_manual_reset": True, "failure_threshold": 1})
    set_backpressure(tmp_path, account="agy1", mode="block", policy=authorized, now=100)
    clear_backpressure(tmp_path, account="agy1", policy=authorized, now=101)
    assert acquire(tmp_path, authorized, request_id="pressure-reset", now=101).account == "agy1"
    assert record_failure(tmp_path, account="agy1", failure_type="timeout", policy=authorized, now=102)
    reset_circuit(tmp_path, account="agy1", policy=authorized, now=103)
    assert acquire(tmp_path, authorized, request_id="circuit-reset", now=103).account == "agy1"


def test_pressure_state_tampering_rejected_and_concurrent_failures_are_atomic(tmp_path: Path, policy: dict) -> None:
    lease = acquire(tmp_path, policy)
    state_path = tmp_path / ".capacity.json"
    state = json.loads(state_path.read_text())
    state["backpressure"]["agy1"] = {"mode": "not-a-mode", "set_at": 100, "until": 200}
    state_path.write_text(json.dumps(state))
    with pytest.raises(LeaseRejectedError, match="STATE_INVALID"):
        consume_lease(tmp_path, lease, requests=1, policy=policy, now=101)

    fresh = tmp_path / "fresh"
    constrained = copy.deepcopy(policy)
    constrained["accounts"]["agy1"]["circuit_breaker"]["failure_threshold"] = 3
    def fail_once(_: int) -> bool:
        return record_failure(fresh, account="agy1", failure_type="timeout", policy=constrained, now=100)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        outcomes = list(executor.map(fail_once, range(8)))
    assert outcomes.count(True) >= 1
    with pytest.raises(LeaseRejectedError, match="CIRCUIT_OPEN"):
        acquire(fresh, constrained, request_id="concurrent-circuit", now=101)


def test_daily_ledger_is_local_calendar_and_request_idempotent(tmp_path: Path, policy: dict) -> None:
    lease = acquire(tmp_path, policy, request_id="daily-lease", now=100)
    charged = consume_lease(tmp_path, lease, requests=2, request_id="charge-1", policy=policy, now=100)
    repeated = consume_lease(tmp_path, lease, requests=2, request_id="charge-1", policy=policy, now=101)
    assert repeated.to_dict() == charged.to_dict()
    snap = capacity_snapshot(tmp_path, policy=policy, now=101)
    assert snap["accounts"]["agy1"]["daily_ledger"]["requests"] == 2
    # The local calendar day rolls over without carrying yesterday's count.
    next_day = capacity_snapshot(tmp_path, policy=policy, now=86400 + 100)
    assert next_day["accounts"]["agy1"]["daily_ledger"]["requests"] == 0


def test_daily_ledger_rolls_over_at_bangkok_midnight(tmp_path: Path, policy: dict) -> None:
    before_midnight = datetime(2026, 1, 1, 16, 59, tzinfo=timezone.utc).timestamp()
    midnight = datetime(2026, 1, 1, 17, 0, tzinfo=timezone.utc).timestamp()
    lease = acquire(tmp_path, policy, request_id="bangkok-midnight", now=before_midnight)
    consume_lease(tmp_path, lease, requests=1, request_id="bangkok-charge", policy=policy, now=before_midnight)

    before = capacity_snapshot(tmp_path, policy=policy, now=before_midnight)
    after = capacity_snapshot(tmp_path, policy=policy, now=midnight)

    assert before["accounts"]["agy1"]["daily_ledger"]["local_day"] == "2026-01-01"
    assert after["accounts"]["agy1"]["daily_ledger"]["local_day"] == "2026-01-02"
    assert after["accounts"]["agy1"]["daily_ledger"]["requests"] == 0


def test_daily_limit_is_fail_closed_and_account_local(tmp_path: Path, policy: dict, monkeypatch: pytest.MonkeyPatch) -> None:
    policy["daily_request_limit"] = 2
    lease = acquire(tmp_path, policy, request_id="daily-limit")
    charged = consume_lease(tmp_path, lease, requests=2, policy=policy, now=100)
    with pytest.raises(LeaseRejectedError, match="DAILY_LIMIT_EXCEEDED"):
        consume_lease(tmp_path, charged, requests=1, policy=policy, now=101)
    other = acquire(tmp_path, policy, account="agy2", request_id="daily-other")
    assert consume_lease(tmp_path, other, requests=1, policy=policy, now=101).requests_used == 1


def test_queue_is_fifo_bounded_and_drain_fails_closed_under_pressure(tmp_path: Path, policy: dict) -> None:
    enqueue_request(tmp_path, account="agy1", request_id="q-2", owner="root-a", lane=1, policy=policy, now=102)
    enqueue_request(tmp_path, account="agy1", request_id="q-1", owner="root-a", lane=1, policy=policy, now=101)
    assert [item["request_id"] for item in drain_queue(tmp_path, account="agy1", policy=policy, max_items=1, now=103)] == ["q-1"]
    set_backpressure(tmp_path, account="agy1", mode="queue", policy=policy, now=104)
    with pytest.raises(LeaseRejectedError, match="BACKPRESSURE_QUEUED"):
        drain_queue(tmp_path, account="agy1", policy=policy, now=105)
    assert capacity_snapshot(tmp_path, policy=policy, now=105)["accounts"]["agy1"]["queue_depth"] == 1


def test_state_invariant_validator_rejects_daily_queue_and_retry_tampering(tmp_path: Path, policy: dict) -> None:
    acquire(tmp_path, policy, request_id="invariant")
    state_path = tmp_path / ".capacity.json"
    state = json.loads(state_path.read_text())
    state["daily_ledger"]["agy1"]["requests"] = 1
    state_path.write_text(json.dumps(state))
    with pytest.raises(LeaseRejectedError, match="STATE_INVALID"):
        capacity_snapshot(tmp_path, policy=policy, now=101)
    with pytest.raises(LeaseRejectedError, match="STATE_INVALID"):
        validate_capacity_state(state, policy)


def test_retry_reservation_is_bounded_idempotent_and_expiry_is_terminal(tmp_path: Path, policy: dict) -> None:
    reservation = reserve_retry(tmp_path, account="agy1", request_id="retry-1", owner="root-a", policy=policy, max_attempts=2, ttl_seconds=10, now=100)
    assert record_retry(tmp_path, account="agy1", request_id="retry-1", policy=policy, now=101)["attempts"] == 1
    assert record_retry(tmp_path, account="agy1", request_id="retry-1", policy=policy, now=102)["attempts"] == 2
    with pytest.raises(LeaseRejectedError, match="RETRY_LIMIT_EXCEEDED"):
        record_retry(tmp_path, account="agy1", request_id="retry-1", policy=policy, now=103)
    release_retry(tmp_path, account="agy1", request_id="retry-1", policy=policy, now=103)
    assert reserve_retry(tmp_path, account="agy1", request_id="retry-expired", owner="root-a", policy=policy, ttl_seconds=1, now=100) ["expires_at"] == 101
    with pytest.raises(LeaseRejectedError, match="RETRY_RESERVATION_EXPIRED"):
        record_retry(tmp_path, account="agy1", request_id="retry-expired", policy=policy, now=101)


def test_hitl2_quota_source_is_explicit_and_retry_budget_is_total_attempts(tmp_path: Path, policy: dict) -> None:
    assert capacity_snapshot(tmp_path, policy=policy, now=100)["accounts"]["agy1"]["daily_ledger"]["quota_source"] == "configured_placeholder"
    with pytest.raises(LeaseRejectedError, match="RETRY_LIMIT_EXCEEDED"):
        reserve_retry(tmp_path, account="agy1", request_id="retry-over", owner="root-a", policy=policy, max_attempts=4, now=100)
    state = json.loads((tmp_path / ".capacity.json").read_text())
    state["daily_ledger"]["agy1"]["quota_source"] = "verified"
    (tmp_path / ".capacity.json").write_text(json.dumps(state))
    with pytest.raises(LeaseRejectedError, match="STATE_INVALID"):
        capacity_snapshot(tmp_path, policy=policy, now=101)
