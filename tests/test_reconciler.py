"""Unit tests for Reconciler (AT-10)."""

from unittest.mock import MagicMock
import pytest

from project.core.jira_state_machine import JiraStateMachine, TicketState
from project.core.lease_manager import LeaseManager
from project.core.reconciler import ReconcileAction, Reconciler
from project.core.worker_runtime import ProcessState, ProcessStatus


def test_reconciler_active_lease_worker_alive():
    lm = LeaseManager(default_ttl_seconds=900)
    sm = JiraStateMachine(lease_manager=lm)
    mock_runtime = MagicMock()

    reconciler = Reconciler(lease_manager=lm, state_machine=sm, runtime_backend=mock_runtime)

    ticket_id = "KAN-701"
    sm.transition_to_dor_check(ticket_id)
    ctx = sm.evaluate_dor_and_claim(ticket_id, True, "worker-01", "sess-01", current_time=100.0)
    sm.transition_to_in_progress(ticket_id, ctx.identity.fencing_token, current_time=100.0)

    mock_runtime.status.return_value = ProcessStatus(
        identity=ctx.identity,
        backend_name="herdr",
        state=ProcessState.WORKING,
        pid=1234,
        alive=True,
    )

    ev = reconciler.reconcile_ticket(ticket_id, current_time=150.0)
    assert ev.action == ReconcileAction.NO_OP
    assert "Lease active" in ev.detail


def test_reconciler_expired_lease_worker_alive_auto_renews():
    lm = LeaseManager(default_ttl_seconds=100)
    sm = JiraStateMachine(lease_manager=lm)
    mock_runtime = MagicMock()

    reconciler = Reconciler(lease_manager=lm, state_machine=sm, runtime_backend=mock_runtime)

    ticket_id = "KAN-702"
    sm.transition_to_dor_check(ticket_id)
    ctx = sm.evaluate_dor_and_claim(ticket_id, True, "worker-01", "sess-01", current_time=100.0)
    sm.transition_to_in_progress(ticket_id, ctx.identity.fencing_token, current_time=100.0)

    # Worker is still alive at time 500 (lease expired at 200)
    mock_runtime.status.return_value = ProcessStatus(
        identity=ctx.identity,
        backend_name="herdr",
        state=ProcessState.WORKING,
        pid=1234,
        alive=True,
    )

    ev = reconciler.reconcile_ticket(ticket_id, current_time=500.0)
    assert ev.action == ReconcileAction.RENEWED
    assert "auto-renewed" in ev.detail


def test_reconciler_expired_lease_worker_dead_fences():
    lm = LeaseManager(default_ttl_seconds=100)
    sm = JiraStateMachine(lease_manager=lm)
    mock_runtime = MagicMock()

    reconciler = Reconciler(lease_manager=lm, state_machine=sm, runtime_backend=mock_runtime)

    ticket_id = "KAN-703"
    sm.transition_to_dor_check(ticket_id)
    ctx = sm.evaluate_dor_and_claim(ticket_id, True, "worker-01", "sess-01", current_time=100.0)
    sm.transition_to_in_progress(ticket_id, ctx.identity.fencing_token, current_time=100.0)

    # Worker is dead at time 500
    mock_runtime.status.return_value = ProcessStatus(
        identity=ctx.identity,
        backend_name="herdr",
        state=ProcessState.COMPLETED,
        pid=1234,
        alive=False,
    )

    ev = reconciler.reconcile_ticket(ticket_id, current_time=500.0)
    assert ev.action == ReconcileAction.FENCED
    assert "fenced" in ev.detail
