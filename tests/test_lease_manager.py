"""Unit tests for LeaseManager (AT-07)."""

import pytest

from project.core.execution_identity import StaleFencingTokenError
from project.core.lease_manager import (
    LeaseAlreadyAcquiredError,
    LeaseManager,
    LeaseMismatchError,
    LeaseState,
)


def test_lease_acquire_success():
    lm = LeaseManager(default_ttl_seconds=900)
    lease = lm.acquire_lease(
        ticket_id="KAN-500",
        worker_id="worker-01",
        session_id="sess-01",
        current_time=1000.0,
    )
    assert lease.ticket_id == "KAN-500"
    assert lease.attempt == 1
    assert lease.fencing_token == "fence-KAN-500-1"
    assert lease.state == LeaseState.ACTIVE
    assert lease.is_active(current_time=1050.0) is True
    assert lease.is_active(current_time=2000.0) is False


def test_lease_acquire_duplicate_blocked():
    lm = LeaseManager(default_ttl_seconds=900)
    lm.acquire_lease(
        ticket_id="KAN-501",
        worker_id="worker-01",
        session_id="sess-01",
        current_time=1000.0,
    )

    with pytest.raises(LeaseAlreadyAcquiredError):
        lm.acquire_lease(
            ticket_id="KAN-501",
            worker_id="worker-02",
            session_id="sess-02",
            current_time=1100.0,
        )


def test_lease_renew_and_fencing_token_check():
    lm = LeaseManager(default_ttl_seconds=900)
    lease = lm.acquire_lease(
        ticket_id="KAN-502",
        worker_id="worker-01",
        session_id="sess-01",
        current_time=1000.0,
    )

    # Valid renew
    renewed = lm.renew_lease(
        lease_id=lease.lease_id,
        fencing_token=lease.fencing_token,
        ttl_seconds=600,
        current_time=1500.0,
    )
    assert renewed.expires_at == 2100.0

    # Stale fencing token error
    with pytest.raises(StaleFencingTokenError):
        lm.renew_lease(
            lease_id=lease.lease_id,
            fencing_token="fence-KAN-502-WRONG",
            current_time=1600.0,
        )


def test_lease_fence_and_release():
    lm = LeaseManager(default_ttl_seconds=900)
    lease = lm.acquire_lease(
        ticket_id="KAN-503",
        worker_id="worker-01",
        session_id="sess-01",
        current_time=1000.0,
    )

    assert lm.fence_lease(lease.lease_id) is True
    fenced = lm.get_lease("KAN-503")
    assert fenced.state == LeaseState.FENCED
    assert fenced.is_active(current_time=1050.0) is False

    # Once fenced/expired, new attempt can acquire lease
    lease2 = lm.acquire_lease(
        ticket_id="KAN-503",
        worker_id="worker-02",
        session_id="sess-02",
        current_time=1100.0,
    )
    assert lease2.attempt == 2
    assert lease2.fencing_token == "fence-KAN-503-2"
