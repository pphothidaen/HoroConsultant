"""Jira Event-Driven State Machine with Deterministic Gates (AT-09).

Implements the canonical lifecycle:
  TODO -> DOR_CHECK -> CLAIMED -> IN_PROGRESS -> VERIFYING -> DONE / BLOCKED
Enforces DoR and DoD gates with FencingToken validation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from project.core.evidence_validator import EvidenceValidationResult, EvidenceValidator
from project.core.execution_identity import ExecutionIdentity
from project.core.fencing_token_guard import FencingTokenGuard
from project.core.lease_manager import LeaseManager


class TicketState(str, Enum):
    """Canonical ticket execution state."""

    TODO = "TODO"
    DOR_CHECK = "DOR_CHECK"
    CLAIMED = "CLAIMED"
    IN_PROGRESS = "IN_PROGRESS"
    VERIFYING = "VERIFYING"
    DONE = "DONE"
    BLOCKED = "BLOCKED"


class StateTransitionError(Exception):
    """Raised on invalid state machine transitions."""

    pass


# Allowed state transitions
VALID_TRANSITIONS: Dict[TicketState, Set[TicketState]] = {
    TicketState.TODO: {TicketState.DOR_CHECK, TicketState.BLOCKED},
    TicketState.DOR_CHECK: {TicketState.CLAIMED, TicketState.BLOCKED},
    TicketState.CLAIMED: {TicketState.IN_PROGRESS, TicketState.BLOCKED},
    TicketState.IN_PROGRESS: {TicketState.VERIFYING, TicketState.BLOCKED},
    TicketState.VERIFYING: {TicketState.DONE, TicketState.BLOCKED},
    TicketState.BLOCKED: {TicketState.TODO, TicketState.DOR_CHECK},
    TicketState.DONE: set(),  # Terminal
}


@dataclass(frozen=True)
class TicketContext:
    """State record for an active ticket."""

    ticket_id: str
    current_state: TicketState
    identity: Optional[ExecutionIdentity] = None
    dor_checks: Optional[List[str]] = None
    evidence_receipt: Optional[Dict[str, Any]] = None
    blocked_reason: Optional[str] = None


class JiraStateMachine:
    """Coordinator for ticket execution state transitions."""

    def __init__(
        self,
        lease_manager: LeaseManager,
        evidence_validator: Optional[EvidenceValidator] = None,
    ) -> None:
        self._lm = lease_manager
        self._guard = FencingTokenGuard(lease_manager)
        self._validator = evidence_validator or EvidenceValidator()
        self._tickets: Dict[str, TicketContext] = {}

    def init_ticket(self, ticket_id: str) -> TicketContext:
        """Initialize ticket in TODO state."""
        ctx = TicketContext(ticket_id=ticket_id, current_state=TicketState.TODO)
        self._tickets[ticket_id] = ctx
        return ctx

    def get_context(self, ticket_id: str) -> Optional[TicketContext]:
        """Get context for ticket."""
        return self._tickets.get(ticket_id)

    def transition_to_dor_check(self, ticket_id: str) -> TicketContext:
        """Move TODO -> DOR_CHECK."""
        ctx = self._tickets.get(ticket_id) or self.init_ticket(ticket_id)
        if TicketState.DOR_CHECK not in VALID_TRANSITIONS[ctx.current_state]:
            raise StateTransitionError(
                f"Cannot transition '{ticket_id}' from '{ctx.current_state.value}' to 'DOR_CHECK'"
            )
        new_ctx = TicketContext(ticket_id=ticket_id, current_state=TicketState.DOR_CHECK)
        self._tickets[ticket_id] = new_ctx
        return new_ctx

    def evaluate_dor_and_claim(
        self,
        ticket_id: str,
        dor_passed: bool,
        worker_id: str,
        session_id: str,
        reason: Optional[str] = None,
        ttl_seconds: Optional[float] = None,
        current_time: Optional[float] = None,
    ) -> TicketContext:
        """Evaluate Definition of Ready and acquire lease (CLAIMED) or move to BLOCKED."""
        ctx = self._tickets.get(ticket_id)
        if not ctx or ctx.current_state != TicketState.DOR_CHECK:
            raise StateTransitionError(f"Ticket '{ticket_id}' must be in DOR_CHECK state")

        if not dor_passed:
            blocked_ctx = TicketContext(
                ticket_id=ticket_id,
                current_state=TicketState.BLOCKED,
                blocked_reason=reason or "DoR check failed",
            )
            self._tickets[ticket_id] = blocked_ctx
            return blocked_ctx

        # DoR Passed -> Acquire Lease and move to CLAIMED
        lease = self._lm.acquire_lease(
            ticket_id=ticket_id,
            worker_id=worker_id,
            session_id=session_id,
            ttl_seconds=ttl_seconds,
            current_time=current_time,
        )
        ident = lease.to_execution_identity()
        claimed_ctx = TicketContext(
            ticket_id=ticket_id,
            current_state=TicketState.CLAIMED,
            identity=ident,
        )
        self._tickets[ticket_id] = claimed_ctx
        return claimed_ctx

    def transition_to_in_progress(
        self,
        ticket_id: str,
        fencing_token: str,
        current_time: Optional[float] = None,
    ) -> TicketContext:
        """Move CLAIMED -> IN_PROGRESS after worker spawn."""
        ctx = self._tickets.get(ticket_id)
        if not ctx or ctx.current_state != TicketState.CLAIMED:
            raise StateTransitionError(f"Ticket '{ticket_id}' must be in CLAIMED state")

        self._guard.assert_mutation_authorized(
            ticket_id, fencing_token, "start_work", current_time=current_time
        )
        new_ctx = TicketContext(
            ticket_id=ticket_id,
            current_state=TicketState.IN_PROGRESS,
            identity=ctx.identity,
        )
        self._tickets[ticket_id] = new_ctx
        return new_ctx

    def transition_to_verifying(
        self,
        ticket_id: str,
        fencing_token: str,
        current_time: Optional[float] = None,
    ) -> TicketContext:
        """Move IN_PROGRESS -> VERIFYING upon task execution completion."""
        ctx = self._tickets.get(ticket_id)
        if not ctx or ctx.current_state != TicketState.IN_PROGRESS:
            raise StateTransitionError(f"Ticket '{ticket_id}' must be in IN_PROGRESS state")

        self._guard.assert_mutation_authorized(
            ticket_id, fencing_token, "submit_for_verification", current_time=current_time
        )
        new_ctx = TicketContext(
            ticket_id=ticket_id,
            current_state=TicketState.VERIFYING,
            identity=ctx.identity,
        )
        self._tickets[ticket_id] = new_ctx
        return new_ctx

    def finalize_verification(
        self,
        ticket_id: str,
        fencing_token: str,
        evidence_payload: Dict[str, Any],
        current_time: Optional[float] = None,
    ) -> tuple[TicketContext, EvidenceValidationResult]:
        """Verify evidence and transition to DONE (if PASS) or BLOCKED (if FAIL)."""
        ctx = self._tickets.get(ticket_id)
        if not ctx or ctx.current_state != TicketState.VERIFYING:
            raise StateTransitionError(f"Ticket '{ticket_id}' must be in VERIFYING state")

        self._guard.assert_mutation_authorized(
            ticket_id, fencing_token, "finalize_verification", current_time=current_time
        )

        validation = self._validator.validate(
            evidence_payload=evidence_payload,
            expected_identity=ctx.identity,
        )

        if validation.is_valid:
            # Release lease on successful completion
            if ctx.identity:
                self._lm.release_lease(ctx.identity.lease_id, fencing_token)

            done_ctx = TicketContext(
                ticket_id=ticket_id,
                current_state=TicketState.DONE,
                identity=ctx.identity,
                evidence_receipt=evidence_payload,
            )
            self._tickets[ticket_id] = done_ctx
            return done_ctx, validation

        # Validation failed -> move to BLOCKED
        blocked_ctx = TicketContext(
            ticket_id=ticket_id,
            current_state=TicketState.BLOCKED,
            identity=ctx.identity,
            evidence_receipt=evidence_payload,
            blocked_reason=f"Evidence verification failed: {validation.error_code} - {validation.reasons}",
        )
        self._tickets[ticket_id] = blocked_ctx
        return blocked_ctx, validation
