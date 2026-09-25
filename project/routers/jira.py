"""Jira Webhook & Autonomous Execution Router (FastAPI).

Provides endpoints for Jira Cloud webhook intake, payload deduplication,
prompt injection sanitization, state machine transitions, and lease status queries.
"""

from __future__ import annotations

import hashlib
import logging
import os
import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException, Request, Response
from pydantic import BaseModel, Field

from project.core.evidence_validator import EvidenceValidator
from project.core.jira_sanitizer import JiraContentSanitizer, SanitizedJiraPayload
from project.core.jira_state_machine import JiraStateMachine, TicketContext, TicketState
from project.core.lease_manager import LeaseManager
from project.core.risk_tier_gate import RiskTierGate
from project.core.runtime_selector import RuntimeSelector
from project.core.webhook_dedup import WebhookDeduplicator

logger = logging.getLogger("jira_router")

jira_router = APIRouter(prefix="/api/jira", tags=["Jira Autonomy"])

# Global singleton instances for in-memory state
lease_manager = LeaseManager(default_ttl_seconds=900.0)
evidence_validator = EvidenceValidator()
state_machine = JiraStateMachine(
    lease_manager=lease_manager,
    evidence_validator=evidence_validator,
)
webhook_deduplicator = WebhookDeduplicator(dedup_ttl_seconds=3600.0, coalesce_window_seconds=2.0)
sanitizer = JiraContentSanitizer()
risk_gate = RiskTierGate()
runtime_selector = RuntimeSelector()


class JiraWebhookHeader(BaseModel):
    """Extracted Jira webhook request headers."""

    delivery_id: Optional[str] = None
    event_type: Optional[str] = None
    signature: Optional[str] = None


class ReleaseLeaseRequest(BaseModel):
    """Payload for manual lease release or fencing."""

    lease_id: str
    fencing_token: str
    action: str = Field(default="release", description="'release' or 'fence'")
    reason: Optional[str] = Field(default=None, description="Reason for fencing or releasing")


@jira_router.post("/webhook", status_code=200)
async def handle_jira_webhook(
    request: Request,
    x_atlassian_webhook_identifier: Optional[str] = Header(None, alias="X-Atlassian-Webhook-Identifier"),
    x_jira_event_type: Optional[str] = Header(None, alias="X-Jira-Event-Type"),
    x_hub_signature: Optional[str] = Header(None, alias="X-Hub-Signature"),
) -> Dict[str, Any]:
    """Idempotent Webhook Intake Endpoint for Jira Cloud.

    Processes incoming issue updates, sanitizes untrusted input, asserts deduplication,
    evaluates Definition of Ready (DoR), and claims execution lease if ready.
    """
    try:
        body_bytes = await request.body()
        payload: Dict[str, Any] = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid JSON payload: {exc}")

    # Optional Webhook Secret Validation
    webhook_secret = os.getenv("JIRA_WEBHOOK_SECRET")
    if webhook_secret and x_hub_signature:
        expected_sig = "sha256=" + hashlib.hmac.new(
            webhook_secret.encode("utf-8"),
            body_bytes,
            hashlib.sha256,
        ).hexdigest()
        if not hashlib.compare_digest(expected_sig, x_hub_signature):
            logger.warning("Jira webhook HMAC signature mismatch")
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    # Extract issue payload data
    issue_data = payload.get("issue") or payload
    key = str(issue_data.get("key") or payload.get("ticket_id") or payload.get("issue_key") or "").strip()

    if not key:
        return {
            "status": "ignored",
            "reason": "missing_issue_key",
            "detail": "Payload does not contain a valid Jira issue key.",
        }

    # Generate or extract delivery ID
    delivery_id = (
        x_atlassian_webhook_identifier
        or str(payload.get("webhookEvent") or payload.get("timestamp") or "")
        + "_" + key
    )
    if not delivery_id or len(delivery_id) < 3:
        delivery_id = "delivery-" + hashlib.sha256(body_bytes).hexdigest()[:16]

    # 1. Deduplication & Burst Coalescing Check
    is_dup, dup_reason = webhook_deduplicator.check_and_record(
        delivery_id=delivery_id,
        ticket_id=key,
        payload=payload,
    )
    if is_dup:
        logger.info(f"[DEDUP] Dropping duplicate webhook for ticket '{key}': {dup_reason}")
        return {
            "status": "ignored",
            "ticket_id": key,
            "reason": "duplicate_or_coalesced",
            "detail": dup_reason,
        }

    # 2. Content Sanitization & Prompt Injection Defense (INVARIANT-07)
    sanitized: SanitizedJiraPayload = sanitizer.sanitize(issue_data)
    if sanitized.is_suspicious:
        logger.warning(
            f"[SECURITY] Suspicious content neutralized in ticket '{key}': "
            f"stripped={sanitized.stripped_patterns}"
        )

    # 3. State Machine Transition & DoR Evaluation
    ctx = state_machine.get_context(key)
    if not ctx:
        ctx = state_machine.init_ticket(key)

    # Transition TODO -> DOR_CHECK
    if ctx.current_state == TicketState.TODO:
        ctx = state_machine.transition_to_dor_check(key)

    # Evaluate DoR and Claim Lease if ready
    # Check if description/summary has mandatory fields or acceptance criteria
    dor_passed = bool(sanitized.summary) and not sanitized.is_suspicious

    worker_id = os.getenv("WORKER_ID", "worker-hermes-01")
    session_id = os.getenv("SESSION_ID", f"session-{int(time.time())}")

    if ctx.current_state == TicketState.DOR_CHECK:
        claimed_ctx = state_machine.evaluate_dor_and_claim(
            ticket_id=key,
            dor_passed=dor_passed,
            worker_id=worker_id,
            session_id=session_id,
            reason="DoR passed via webhook intake" if dor_passed else "DoR failed (suspicious or empty content)",
        )
        ctx = claimed_ctx

    lease_info = lease_manager.get_lease(key)
    identity_dict = ctx.identity.to_dict() if ctx.identity else None

    # Detect Runtime capabilities
    backend_info = None
    if ctx.current_state == TicketState.CLAIMED:
        try:
            backend = runtime_selector.get_backend()
            backend_info = {
                "name": backend.name,
                "healthy": backend.health().healthy,
            }
        except Exception as exc:
            logger.warning(f"Runtime selector notice for '{key}': {exc}")

    return {
        "status": "success",
        "ticket_id": key,
        "state": ctx.current_state.value,
        "delivery_id": delivery_id,
        "execution_identity": identity_dict,
        "lease": {
            "lease_id": lease_info.lease_id,
            "fencing_token": lease_info.fencing_token,
            "expires_at": lease_info.expires_at,
        } if lease_info else None,
        "backend": backend_info,
        "sanitized": {
            "summary": sanitized.summary,
            "is_suspicious": sanitized.is_suspicious,
            "stripped_patterns": sanitized.stripped_patterns,
        },
    }


@jira_router.get("/tickets/{ticket_id}")
async def get_ticket_status(ticket_id: str) -> Dict[str, Any]:
    """Get active state machine context and lease record for a ticket."""
    ctx = state_machine.get_context(ticket_id)
    if not ctx:
        raise HTTPException(status_code=404, detail=f"Ticket '{ticket_id}' not found")

    lease = lease_manager.get_lease(ticket_id)
    return {
        "ticket_id": ticket_id,
        "state": ctx.current_state.value,
        "identity": ctx.identity.to_dict() if ctx.identity else None,
        "blocked_reason": ctx.blocked_reason,
        "lease": {
            "lease_id": lease.lease_id,
            "worker_id": lease.worker_id,
            "fencing_token": lease.fencing_token,
            "state": lease.state.value,
            "expires_at": lease.expires_at,
            "is_active": lease.is_active(),
        } if lease else None,
    }


@jira_router.post("/tickets/{ticket_id}/lease/release")
async def release_or_fence_lease(ticket_id: str, req: ReleaseLeaseRequest) -> Dict[str, Any]:
    """Explicitly release or fence an active execution lease."""
    if req.action == "fence":
        success = lease_manager.fence_lease(req.lease_id, reason=req.reason or "manual_fence")
        state_str = "fenced"
    else:
        success = lease_manager.release_lease(req.lease_id, req.fencing_token)
        state_str = "released"

    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to {req.action} lease '{req.lease_id}' for ticket '{ticket_id}'. Invalid token or state.",
        )

    return {
        "status": "success",
        "ticket_id": ticket_id,
        "lease_id": req.lease_id,
        "action": req.action,
        "result_state": state_str,
    }
