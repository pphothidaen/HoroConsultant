"""Background Reconciler and Orphan Worker Reaper (AT-10).

Reconciles active Jira ticket leases against real runtime process health.
Enforces:
  IN_PROGRESS -> LEASE_EXPIRED -> RECONCILING
    ├── worker alive -> RENEW / RECOVER
    ├── worker dead  -> FENCE
    └── state unclear -> RECOVERY_PENDING -> BLOCKED
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

from project.core.jira_state_machine import JiraStateMachine, TicketContext, TicketState
from project.core.lease_manager import LeaseManager, LeaseRecord, LeaseState
from project.core.worker_runtime import ProcessState, RuntimeBackend


class ReconcileAction(str, Enum):
    """Action taken by the reconciler."""

    NO_OP = "NO_OP"
    RENEWED = "RENEWED"
    FENCED = "FENCED"
    RECOVERY_PENDING = "RECOVERY_PENDING"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class ReconcileEvent:
    """Outcome record of a single ticket reconciliation."""

    ticket_id: str
    action: ReconcileAction
    detail: str
    timestamp: float


class Reconciler:
    """Periodic reconciler for orphan worker reaping and lease recovery."""

    def __init__(
        self,
        lease_manager: LeaseManager,
        state_machine: JiraStateMachine,
        runtime_backend: Optional[RuntimeBackend] = None,
    ) -> None:
        self._lm = lease_manager
        self._sm = state_machine
        self._runtime = runtime_backend

    def reconcile_ticket(
        self,
        ticket_id: str,
        current_time: Optional[float] = None,
    ) -> ReconcileEvent:
        """Reconcile a single ticket's lease against process status."""
        now = current_time if current_time is not None else time.time()
        ctx = self._sm.get_context(ticket_id)
        if not ctx or ctx.current_state not in (TicketState.IN_PROGRESS, TicketState.CLAIMED, TicketState.VERIFYING):
            return ReconcileEvent(
                ticket_id=ticket_id,
                action=ReconcileAction.NO_OP,
                detail="Ticket is not in an active execution state",
                timestamp=now,
            )

        lease = self._lm.get_lease(ticket_id)
        if not lease:
            # Ticket in active state but has no lease -> inconsistent, fence and block
            return ReconcileEvent(
                ticket_id=ticket_id,
                action=ReconcileAction.BLOCKED,
                detail="Active state without valid lease record",
                timestamp=now,
            )

        # 1. Lease is still active
        if lease.is_active(now):
            # Check worker health if runtime is connected
            if self._runtime and ctx.identity:
                status = self._runtime.status(ctx.identity)
                if not status.alive and status.state in (ProcessState.FAILED, ProcessState.COMPLETED):
                    # Worker crashed early while lease was active -> Fence
                    self._lm.fence_lease(lease.lease_id, reason="Worker terminated prematurely")
                    return ReconcileEvent(
                        ticket_id=ticket_id,
                        action=ReconcileAction.FENCED,
                        detail="Worker terminated prematurely; lease fenced",
                        timestamp=now,
                    )
            return ReconcileEvent(
                ticket_id=ticket_id,
                action=ReconcileAction.NO_OP,
                detail=f"Lease active (expires in {lease.expires_at - now:.1f}s)",
                timestamp=now,
            )

        # 2. Lease has EXPIRED -> Transition to RECONCILING
        if self._runtime and ctx.identity:
            status = self._runtime.status(ctx.identity)
            if status.alive and status.state in (ProcessState.RUNNING, ProcessState.WORKING):
                # Worker is healthy and working -> Auto-renew lease
                try:
                    self._lm.renew_lease(
                        lease_id=lease.lease_id,
                        fencing_token=lease.fencing_token,
                        current_time=now,
                    )
                    return ReconcileEvent(
                        ticket_id=ticket_id,
                        action=ReconcileAction.RENEWED,
                        detail="Worker healthy; auto-renewed expired lease",
                        timestamp=now,
                    )
                except Exception as exc:
                    return ReconcileEvent(
                        ticket_id=ticket_id,
                        action=ReconcileAction.RECOVERY_PENDING,
                        detail=f"Failed to renew lease for living worker: {exc}",
                        timestamp=now,
                    )

            # Worker is dead -> Fence lease
            self._lm.fence_lease(lease.lease_id, reason="Lease expired and worker dead")
            return ReconcileEvent(
                ticket_id=ticket_id,
                action=ReconcileAction.FENCED,
                detail="Worker dead on expired lease; lease fenced",
                timestamp=now,
            )

        # No runtime attached, lease expired -> Fence
        self._lm.fence_lease(lease.lease_id, reason="Lease expired without worker proof")
        return ReconcileEvent(
            ticket_id=ticket_id,
            action=ReconcileAction.FENCED,
            detail="Lease expired without runtime status; lease fenced",
            timestamp=now,
        )

    def reconcile_all(
        self,
        active_ticket_ids: List[str],
        current_time: Optional[float] = None,
    ) -> List[ReconcileEvent]:
        """Run reconciliation sweep across all active tickets."""
        events: List[ReconcileEvent] = []
        for tid in active_ticket_ids:
            events.append(self.reconcile_ticket(tid, current_time=current_time))
        return events
