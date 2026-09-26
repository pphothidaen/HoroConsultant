"""Unit tests for JiraStateMachine (AT-09)."""

import json
from pathlib import Path
import pytest

from project.core.jira_state_machine import JiraStateMachine, TicketState
from project.core.lease_manager import LeaseManager

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "evidence"


@pytest.fixture
def state_machine():
    lm = LeaseManager(default_ttl_seconds=900)
    return JiraStateMachine(lease_manager=lm)


def test_state_machine_happy_path(state_machine):
    ticket_id = "KAN-142"

    # 1. Init / TODO -> DOR_CHECK
    state_machine.transition_to_dor_check(ticket_id)
    ctx = state_machine.get_context(ticket_id)
    assert ctx.current_state == TicketState.DOR_CHECK

    # 2. DOR_CHECK -> CLAIMED
    ctx = state_machine.evaluate_dor_and_claim(
        ticket_id=ticket_id,
        dor_passed=True,
        worker_id="worker-herdr-01",
        session_id="session-20260925-abc",
    )
    assert ctx.current_state == TicketState.CLAIMED
    assert ctx.identity is not None
    fence = ctx.identity.fencing_token

    # 3. CLAIMED -> IN_PROGRESS
    ctx = state_machine.transition_to_in_progress(ticket_id, fencing_token=fence)
    assert ctx.current_state == TicketState.IN_PROGRESS

    # 4. IN_PROGRESS -> VERIFYING
    ctx = state_machine.transition_to_verifying(ticket_id, fencing_token=fence)
    assert ctx.current_state == TicketState.VERIFYING

    # 5. VERIFYING -> DONE with valid fixture
    with open(FIXTURES_DIR / "valid.json", "r", encoding="utf-8") as f:
        valid_evidence = json.load(f)

    # Align execution_id / attempt
    valid_evidence["execution_id"] = ctx.identity.execution_id
    valid_evidence["fencing_token"] = fence
    valid_evidence["lease_id"] = ctx.identity.lease_id

    from project.core.evidence_models import WorkerEvidenceV1
    valid_evidence["evidence_hash"] = WorkerEvidenceV1.compute_hash(valid_evidence)

    ctx_done, res = state_machine.finalize_verification(
        ticket_id=ticket_id,
        fencing_token=fence,
        evidence_payload=valid_evidence,
    )
    assert ctx_done.current_state == TicketState.DONE
    assert res.is_valid is True


def test_state_machine_dor_failure_blocks_ticket(state_machine):
    ticket_id = "KAN-999"
    state_machine.transition_to_dor_check(ticket_id)
    ctx = state_machine.evaluate_dor_and_claim(
        ticket_id=ticket_id,
        dor_passed=False,
        worker_id="worker-01",
        session_id="sess-01",
        reason="Missing acceptance criteria",
    )
    assert ctx.current_state == TicketState.BLOCKED
    assert "Missing acceptance criteria" in ctx.blocked_reason


def test_state_machine_invalid_evidence_blocks_ticket(state_machine):
    ticket_id = "KAN-888"
    state_machine.transition_to_dor_check(ticket_id)
    ctx = state_machine.evaluate_dor_and_claim(
        ticket_id=ticket_id,
        dor_passed=True,
        worker_id="worker-01",
        session_id="sess-01",
    )
    fence = ctx.identity.fencing_token
    state_machine.transition_to_in_progress(ticket_id, fence)
    state_machine.transition_to_verifying(ticket_id, fence)

    # Finalize with missing git sha
    with open(FIXTURES_DIR / "missing_git_sha.json", "r", encoding="utf-8") as f:
        bad_evidence = json.load(f)

    ctx_blocked, res = state_machine.finalize_verification(
        ticket_id=ticket_id,
        fencing_token=fence,
        evidence_payload=bad_evidence,
    )
    assert ctx_blocked.current_state == TicketState.BLOCKED
    assert res.is_valid is False
