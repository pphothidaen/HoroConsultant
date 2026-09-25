"""Monotonic Fencing Token Guard and Mutation Boundary (AT-08).

Enforces INVARIANT-02: Only the current fencing token may mutate execution state.
Prevents zombie, partitioned, or delayed worker processes from corrupting state.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from project.core.execution_identity import StaleFencingTokenError
from project.core.lease_manager import LeaseManager, LeaseState


class FencingTokenGuard:
    """Enforces atomic mutation validation using active lease fencing tokens."""

    def __init__(self, lease_manager: LeaseManager) -> None:
        self._lm = lease_manager

    def assert_mutation_authorized(
        self,
        ticket_id: str,
        fencing_token: str,
        mutation_name: str,
        current_time: Optional[float] = None,
    ) -> None:
        """Validate that the given fencing token matches the active lease for the ticket."""
        lease = self._lm.get_lease(ticket_id)
        if not lease:
            raise StaleFencingTokenError(
                f"Cannot perform mutation '{mutation_name}': No lease found for ticket '{ticket_id}'"
            )

        if lease.state != LeaseState.ACTIVE:
            raise StaleFencingTokenError(
                f"Cannot perform mutation '{mutation_name}': Lease '{lease.lease_id}' "
                f"is in '{lease.state.value}' state"
            )

        if not lease.is_active(current_time=current_time):
            raise StaleFencingTokenError(
                f"Cannot perform mutation '{mutation_name}': Lease '{lease.lease_id}' has expired"
            )

        if lease.fencing_token != fencing_token:
            raise StaleFencingTokenError(
                f"Cannot perform mutation '{mutation_name}': Fencing token mismatch "
                f"(active='{lease.fencing_token}', attempted='{fencing_token}')"
            )

    def is_mutation_allowed(
        self,
        ticket_id: str,
        fencing_token: str,
        current_time: Optional[float] = None,
    ) -> bool:
        """Check if mutation is allowed without raising an exception."""
        try:
            self.assert_mutation_authorized(ticket_id, fencing_token, "check", current_time)
            return True
        except Exception:
            return False
