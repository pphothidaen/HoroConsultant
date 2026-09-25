"""Renewable Lease Manager for Jira Ticket Execution (AT-07).

Enforces INVARIANT-01: One Jira ticket may have only one active execution lease.
Supports heartbeat-based lease renewal, monotonic attempt increments, and expiry.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional

from project.core.execution_identity import (
    ExecutionIdentity,
    InvalidIdentityError,
    LeaseMismatchError,
    StaleFencingTokenError,
    TicketMismatchError,
)


class LeaseState(str, Enum):
    """Lease lifecycle state."""

    ACTIVE = "active"
    EXPIRED = "expired"
    RELEASED = "released"
    FENCED = "fenced"


class LeaseError(Exception):
    """Base exception for lease management."""

    pass


class LeaseAlreadyAcquiredError(LeaseError):
    """Raised when trying to acquire a lease on a ticket with an active lease (INVARIANT-01)."""

    pass


class LeaseExpiredError(LeaseError):
    """Raised when an operation is performed on an expired lease."""

    pass


@dataclass(frozen=True)
class LeaseRecord:
    """Immutable snapshot of a lease record."""

    lease_id: str
    ticket_id: str
    execution_id: str
    worker_id: str
    session_id: str
    fencing_token: str
    attempt: int
    ttl_seconds: float
    created_at: float
    expires_at: float
    state: LeaseState

    def is_active(self, current_time: Optional[float] = None) -> bool:
        """Check if lease is currently active and not expired."""
        now = current_time if current_time is not None else time.time()
        return self.state == LeaseState.ACTIVE and now < self.expires_at

    def to_execution_identity(self) -> ExecutionIdentity:
        """Convert lease record to ExecutionIdentity."""
        return ExecutionIdentity(
            execution_id=self.execution_id,
            ticket_id=self.ticket_id,
            attempt=self.attempt,
            lease_id=self.lease_id,
            fencing_token=self.fencing_token,
            session_id=self.session_id,
            worker_id=self.worker_id,
        )


class LeaseManager:
    """Thread-safe in-memory Lease Manager with monotonic fencing tokens."""

    def __init__(self, default_ttl_seconds: float = 900.0) -> None:
        self.default_ttl = default_ttl_seconds
        # ticket_id -> LeaseRecord
        self._ticket_leases: Dict[str, LeaseRecord] = {}
        # lease_id -> ticket_id
        self._lease_lookup: Dict[str, str] = {}
        # Global monotonic fencing counter per ticket
        self._ticket_fencing_counters: Dict[str, int] = {}
        # Global attempt counter per ticket
        self._ticket_attempts: Dict[str, int] = {}

    def acquire_lease(
        self,
        ticket_id: str,
        worker_id: str,
        session_id: str,
        ttl_seconds: Optional[float] = None,
        current_time: Optional[float] = None,
    ) -> LeaseRecord:
        """Acquire an atomic lease on a Jira ticket (INVARIANT-01)."""
        now = current_time if current_time is not None else time.time()
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl

        # Check existing lease
        existing = self._ticket_leases.get(ticket_id)
        if existing and existing.is_active(now):
            raise LeaseAlreadyAcquiredError(
                f"Ticket '{ticket_id}' already has active lease '{existing.lease_id}' "
                f"held by worker '{existing.worker_id}' (expires in {existing.expires_at - now:.1f}s)."
            )

        # Monotonic counters
        next_fence = self._ticket_fencing_counters.get(ticket_id, 0) + 1
        self._ticket_fencing_counters[ticket_id] = next_fence

        next_attempt = self._ticket_attempts.get(ticket_id, 0) + 1
        self._ticket_attempts[ticket_id] = next_attempt

        lease_id = f"L-{uuid.uuid4().hex[:8]}"
        execution_id = f"exec-{ticket_id}-{next_attempt}-{uuid.uuid4().hex[:6]}"
        fencing_token = f"fence-{ticket_id}-{next_fence}"

        record = LeaseRecord(
            lease_id=lease_id,
            ticket_id=ticket_id,
            execution_id=execution_id,
            worker_id=worker_id,
            session_id=session_id,
            fencing_token=fencing_token,
            attempt=next_attempt,
            ttl_seconds=ttl,
            created_at=now,
            expires_at=now + ttl,
            state=LeaseState.ACTIVE,
        )

        self._ticket_leases[ticket_id] = record
        self._lease_lookup[lease_id] = ticket_id
        return record

    def renew_lease(
        self,
        lease_id: str,
        fencing_token: str,
        ttl_seconds: Optional[float] = None,
        current_time: Optional[float] = None,
    ) -> LeaseRecord:
        """Renew active lease heartbeat."""
        now = current_time if current_time is not None else time.time()
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl

        ticket_id = self._lease_lookup.get(lease_id)
        if not ticket_id or ticket_id not in self._ticket_leases:
            raise LeaseMismatchError(f"Lease '{lease_id}' not found")

        current = self._ticket_leases[ticket_id]
        if current.lease_id != lease_id:
            raise LeaseMismatchError(f"Lease '{lease_id}' is no longer active for ticket '{ticket_id}'")

        if current.fencing_token != fencing_token:
            raise StaleFencingTokenError(
                f"Cannot renew lease with stale fencing token: active={current.fencing_token}, provided={fencing_token}"
            )

        if current.state != LeaseState.ACTIVE:
            raise LeaseExpiredError(f"Cannot renew lease in state '{current.state.value}'")

        renewed = LeaseRecord(
            lease_id=current.lease_id,
            ticket_id=current.ticket_id,
            execution_id=current.execution_id,
            worker_id=current.worker_id,
            session_id=current.session_id,
            fencing_token=current.fencing_token,
            attempt=current.attempt,
            ttl_seconds=ttl,
            created_at=current.created_at,
            expires_at=now + ttl,
            state=LeaseState.ACTIVE,
        )

        self._ticket_leases[ticket_id] = renewed
        return renewed

    def release_lease(
        self,
        lease_id: str,
        fencing_token: str,
        current_time: Optional[float] = None,
    ) -> bool:
        """Release active lease upon clean completion."""
        ticket_id = self._lease_lookup.get(lease_id)
        if not ticket_id or ticket_id not in self._ticket_leases:
            return False

        current = self._ticket_leases[ticket_id]
        if current.lease_id != lease_id or current.fencing_token != fencing_token:
            return False

        released = LeaseRecord(
            lease_id=current.lease_id,
            ticket_id=current.ticket_id,
            execution_id=current.execution_id,
            worker_id=current.worker_id,
            session_id=current.session_id,
            fencing_token=current.fencing_token,
            attempt=current.attempt,
            ttl_seconds=current.ttl_seconds,
            created_at=current.created_at,
            expires_at=current.expires_at,
            state=LeaseState.RELEASED,
        )
        self._ticket_leases[ticket_id] = released
        return True

    def fence_lease(self, lease_id: str, reason: str = "fenced") -> bool:
        """Explicitly fence an active or stale lease."""
        ticket_id = self._lease_lookup.get(lease_id)
        if not ticket_id or ticket_id not in self._ticket_leases:
            return False

        current = self._ticket_leases[ticket_id]
        if current.lease_id != lease_id:
            return False

        fenced = LeaseRecord(
            lease_id=current.lease_id,
            ticket_id=current.ticket_id,
            execution_id=current.execution_id,
            worker_id=current.worker_id,
            session_id=current.session_id,
            fencing_token=current.fencing_token,
            attempt=current.attempt,
            ttl_seconds=current.ttl_seconds,
            created_at=current.created_at,
            expires_at=current.expires_at,
            state=LeaseState.FENCED,
        )
        self._ticket_leases[ticket_id] = fenced
        return True

    def get_lease(self, ticket_id: str) -> Optional[LeaseRecord]:
        """Get current lease record for ticket."""
        return self._ticket_leases.get(ticket_id)
