"""Focused contract tests for the provider-free S3 capacity lease store."""
from __future__ import annotations

import concurrent.futures
import copy
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
    record_failure,
    release_lease,
    reset_circuit,
    set_backpressure,
    validate_capacity_policy,
)


@pytest.fixture
def policy() -> dict:
    return json.loads((Path(__file__).parents[1] / ".agents/config/s3_capacity_policy.json").read_text())


def acquire(tmp_path: Path, policy: dict, account: str = "agy1", request_id: str = "request-1", now: int = 100):
    return acquire_lease(tmp_path, account=account, request_id=request_id, owner="root-a", lane=1,
                         request_budget=5, model_quality_floor="flash", policy=policy, now=now)


def test_policy_requires_explicit_four_account_caps(policy: dict) -> None:
    assert validate_capacity_policy(policy)["accounts"]["codex1"]["max_workers"] == 2
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
