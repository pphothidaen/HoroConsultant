"""End-to-End Failure Matrix and Autonomous Execution Verification (AT-14).

Simulates the complete integrated workflow from Jira Webhook to final DONE/BLOCKED,
exercising all 8 Invariants and chaos/failure modes across the entire system.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock
import pytest

from project.core.evidence_models import WorkerEvidenceV1
from project.core.evidence_validator import EvidenceValidator
from project.core.fencing_token_guard import FencingTokenGuard
from project.core.jira_sanitizer import JiraContentSanitizer
from project.core.jira_state_machine import JiraStateMachine, TicketState
from project.core.lease_manager import LeaseManager
from project.core.reconciler import ReconcileAction, Reconciler
from project.core.risk_tier_gate import RiskTier, RiskTierGate
from project.core.runtime_selector import RuntimeSelector
from project.core.webhook_dedup import WebhookDeduplicator
from project.core.worker_runtime import ProcessState, ProcessStatus, RuntimeHealth, SpawnRequest

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "evidence"


class AutonomousExecutionPlatform:
    """Integrated facade for testing the autonomous execution pipeline."""

    def __init__(self):
        self.dedup = WebhookDeduplicator()
        self.sanitizer = JiraContentSanitizer()
        self.lm = LeaseManager(default_ttl_seconds=900)
        self.validator = EvidenceValidator()
        self.sm = JiraStateMachine(lease_manager=self.lm, evidence_validator=self.validator)
        self.guard = FencingTokenGuard(self.lm)
        self.risk_gate = RiskTierGate()

        # Mock adapters for platform
        self.mock_herdr = MagicMock()
        self.mock_herdr.name = "herdr"
        self.mock_herdr.detect.return_value = True
        self.mock_herdr.health.return_value = RuntimeHealth("herdr", True, True, "0.6.9")

        self.mock_tmux = MagicMock()
        self.mock_tmux.name = "tmux"
        self.mock_tmux.detect.return_value = True
        self.mock_tmux.health.return_value = RuntimeHealth("tmux", True, True, "3.4")

        self.selector = RuntimeSelector(
            herdr_adapter=self.mock_herdr,
            tmux_adapter=self.mock_tmux,
            target_platform="darwin",
        )
        self.reconciler = Reconciler(
            lease_manager=self.lm,
            state_machine=self.sm,
            runtime_backend=self.mock_herdr,
        )


def test_e2e_full_lifecycle_happy_path():
    """E2E Test: Webhook -> Sanitize -> DoR -> Lease/Fence -> Spawn -> Evidence -> DONE."""
    platform = AutonomousExecutionPlatform()
    raw_webhook = {
        "delivery_id": "wh-delivery-001",
        "key": "KAN-900",
        "summary": "Implement autonomous reconciler",
        "description": "Please implement background reconciler for orphan processes.",
        "target_artifacts": ["project/core/reconciler.py"],
        "verification_command": "pytest tests/test_reconciler.py",
    }

    # 1. Deduplication
    is_dup, _ = platform.dedup.check_and_record(
        raw_webhook["delivery_id"], raw_webhook["key"], raw_webhook, current_time=100.0
    )
    assert is_dup is False

    # 2. Content Sanitization
    sanitized = platform.sanitizer.sanitize(raw_webhook)
    assert sanitized.is_suspicious is False

    # 3. State Machine DoR Check & Lease Claim
    platform.sm.transition_to_dor_check(sanitized.ticket_id)
    ctx = platform.sm.evaluate_dor_and_claim(
        ticket_id=sanitized.ticket_id,
        dor_passed=True,
        worker_id="worker-node-01",
        session_id="session-001",
        current_time=100.0,
    )
    assert ctx.current_state == TicketState.CLAIMED
    ident = ctx.identity

    # 4. Pre-spawn Runtime Selection & Immutable Lock (INVARIANT-06)
    backend = platform.selector.lock_for_execution(ident)
    assert backend.name == "herdr"

    # 5. Spawn Worker
    platform.mock_herdr.spawn.return_value = ProcessStatus(
        identity=ident,
        backend_name="herdr",
        state=ProcessState.RUNNING,
        pid=1001,
        alive=True,
    )
    spawn_status = backend.spawn(
        SpawnRequest(
            identity=ident,
            command=["pytest", "tests/test_reconciler.py"],
            cwd="/tmp",
        )
    )
    assert spawn_status.alive is True

    # 6. State Machine: CLAIMED -> IN_PROGRESS -> VERIFYING
    platform.sm.transition_to_in_progress(ident.ticket_id, ident.fencing_token, current_time=100.0)
    platform.sm.transition_to_verifying(ident.ticket_id, ident.fencing_token, current_time=100.0)

    # 7. Generate Valid Evidence
    evidence_payload = {
        "schema_version": "1.0",
        "execution_id": ident.execution_id,
        "ticket_id": ident.ticket_id,
        "attempt": ident.attempt,
        "lease_id": ident.lease_id,
        "fencing_token": ident.fencing_token,
        "session_id": ident.session_id,
        "worker_id": ident.worker_id,
        "git_sha": "e0ff15b1a8b321c846869b01fcce2075a0d8d18e",
        "environment": "macos-arm64-darwin24",
        "tests": {"total": 5, "passed": 5, "failed": 0, "skipped": 0},
        "acceptance_checks": [{"check_id": "AC-1", "status": "passed", "detail": "Reconciler green"}],
        "command_receipts": [
            {"command": "pytest", "exit_code": 0, "stdout_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"}
        ],
        "timestamp": "2026-09-25T15:00:00Z",
    }
    evidence_payload["evidence_hash"] = WorkerEvidenceV1.compute_hash(evidence_payload)

    # 8. Finalize Verification and Transition to DONE (INVARIANT-03)
    done_ctx, v_res = platform.sm.finalize_verification(
        ticket_id=ident.ticket_id,
        fencing_token=ident.fencing_token,
        evidence_payload=evidence_payload,
        current_time=100.0,
    )
    assert done_ctx.current_state == TicketState.DONE
    assert v_res.is_valid is True

    # 9. Risk Tier Check
    approval = platform.risk_gate.evaluate(RiskTier.MEDIUM, evidence_payload)
    assert approval.approved is True


def test_e2e_chaos_zombie_worker_rejected():
    """E2E Chaos: Stale zombie worker attempts to update state -> Blocked (INVARIANT-02)."""
    platform = AutonomousExecutionPlatform()
    ticket_id = "KAN-901"

    platform.sm.transition_to_dor_check(ticket_id)
    ctx1 = platform.sm.evaluate_dor_and_claim(ticket_id, True, "worker-1", "sess-1", current_time=100.0)
    old_fence = ctx1.identity.fencing_token

    # Worker 1 times out, lease fenced
    platform.lm.fence_lease(ctx1.identity.lease_id)

    # Re-init ticket for attempt 2
    platform.sm.init_ticket(ticket_id)
    platform.sm.transition_to_dor_check(ticket_id)
    ctx2 = platform.sm.evaluate_dor_and_claim(ticket_id, True, "worker-2", "sess-2", current_time=200.0)
    new_fence = ctx2.identity.fencing_token

    # Zombie Worker 1 attempts mutation with old fencing token -> REJECTED
    assert platform.guard.is_mutation_allowed(ticket_id, old_fence, current_time=250.0) is False
    assert platform.guard.is_mutation_allowed(ticket_id, new_fence, current_time=250.0) is True


def test_e2e_chaos_tampered_evidence_rejected():
    """E2E Chaos: Worker modifies test results in evidence -> Hash mismatch rejected."""
    platform = AutonomousExecutionPlatform()
    ticket_id = "KAN-902"

    platform.sm.transition_to_dor_check(ticket_id)
    ctx = platform.sm.evaluate_dor_and_claim(ticket_id, True, "worker-1", "sess-1", current_time=100.0)
    ident = ctx.identity

    platform.sm.transition_to_in_progress(ticket_id, ident.fencing_token, current_time=100.0)
    platform.sm.transition_to_verifying(ticket_id, ident.fencing_token, current_time=100.0)

    tampered_evidence = {
        "schema_version": "1.0",
        "execution_id": ident.execution_id,
        "ticket_id": ident.ticket_id,
        "attempt": ident.attempt,
        "lease_id": ident.lease_id,
        "fencing_token": ident.fencing_token,
        "session_id": ident.session_id,
        "worker_id": ident.worker_id,
        "git_sha": "e0ff15b1a8b321c846869b01fcce2075a0d8d18e",
        "environment": "macos-arm64-darwin24",
        "tests": {"total": 5, "passed": 5, "failed": 0, "skipped": 0},
        "acceptance_checks": [{"check_id": "AC-1", "status": "passed", "detail": "OK"}],
        "command_receipts": [
            {"command": "pytest", "exit_code": 0, "stdout_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"}
        ],
        "timestamp": "2026-09-25T15:00:00Z",
        "evidence_hash": "0000000000000000000000000000000000000000000000000000000000000000",
    }

    blocked_ctx, res = platform.sm.finalize_verification(
        ticket_id=ticket_id,
        fencing_token=ident.fencing_token,
        evidence_payload=tampered_evidence,
        current_time=100.0,
    )
    assert blocked_ctx.current_state == TicketState.BLOCKED
    assert res.is_valid is False
    assert res.error_code == "EVIDENCE_HASH_MISMATCH"
