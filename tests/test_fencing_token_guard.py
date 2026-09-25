"""Unit tests for FencingTokenGuard (AT-08)."""

import pytest

from project.core.execution_identity import StaleFencingTokenError
from project.core.fencing_token_guard import FencingTokenGuard
from project.core.lease_manager import LeaseManager


def test_fencing_token_guard_mutation_allowed():
    lm = LeaseManager(default_ttl_seconds=900)
    guard = FencingTokenGuard(lm)

    lease = lm.acquire_lease(
        ticket_id="KAN-600",
        worker_id="worker-01",
        session_id="sess-01",
        current_time=1000.0,
    )

    # Valid check
    assert guard.is_mutation_allowed("KAN-600", lease.fencing_token, current_time=1050.0) is True
    guard.assert_mutation_authorized("KAN-600", lease.fencing_token, "update_status", current_time=1050.0)


def test_fencing_token_guard_stale_token_blocked():
    lm = LeaseManager(default_ttl_seconds=900)
    guard = FencingTokenGuard(lm)

    lease = lm.acquire_lease(
        ticket_id="KAN-601",
        worker_id="worker-01",
        session_id="sess-01",
        current_time=1000.0,
    )

    # Fence and re-acquire with attempt 2
    lm.fence_lease(lease.lease_id)
    lease2 = lm.acquire_lease(
        ticket_id="KAN-601",
        worker_id="worker-02",
        session_id="sess-02",
        current_time=1100.0,
    )

    # Worker 1 attempts mutation with old fencing token -> BLOCKED (INVARIANT-02)
    assert guard.is_mutation_allowed("KAN-601", lease.fencing_token, current_time=1150.0) is False
    with pytest.raises(StaleFencingTokenError, match="Fencing token mismatch"):
        guard.assert_mutation_authorized(
            "KAN-601",
            lease.fencing_token,
            "transition_done",
            current_time=1150.0,
        )

    # Worker 2 attempts mutation with active fencing token -> PASS
    assert guard.is_mutation_allowed("KAN-601", lease2.fencing_token, current_time=1150.0) is True
