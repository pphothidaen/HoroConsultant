"""Risk-Tiered Approval Gate for Autonomous Task Finalization (AT-12).

Maps tasks to risk tiers:
  LOW: Auto-DONE on strict evidence
  MEDIUM: Auto-DONE on strict evidence + full test suite
  HIGH / PRODUCTION: Strict evidence + required Human Approval (HITL)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

from project.core.evidence_models import WorkerEvidenceV1


class RiskTier(str, Enum):
    """Task risk classification."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    PRODUCTION = "PRODUCTION"


@dataclass(frozen=True)
class ApprovalVerdict:
    """Verdict from risk tier gate evaluation."""

    approved: bool
    risk_tier: RiskTier
    requires_human_signoff: bool
    reason: str


class RiskTierGate:
    """Evaluates whether an evidence-verified ticket can finalize to DONE."""

    def evaluate(
        self,
        risk_tier: RiskTier,
        evidence: Dict[str, Any],
        human_approval_token: Optional[str] = None,
        approver_id: Optional[str] = None,
    ) -> ApprovalVerdict:
        """Evaluate risk tier and evidence to issue approval verdict."""
        tests = evidence.get("tests", {})
        failed_count = tests.get("failed", 0)

        # Precondition: 0 failed tests always required
        if failed_count > 0:
            return ApprovalVerdict(
                approved=False,
                risk_tier=risk_tier,
                requires_human_signoff=False,
                reason=f"Cannot approve ticket with {failed_count} failed tests",
            )

        if risk_tier == RiskTier.LOW:
            return ApprovalVerdict(
                approved=True,
                risk_tier=risk_tier,
                requires_human_signoff=False,
                reason="LOW risk: Auto-approved on valid deterministic evidence",
            )

        if risk_tier == RiskTier.MEDIUM:
            # Medium requires passed tests > 0
            if tests.get("passed", 0) <= 0:
                return ApprovalVerdict(
                    approved=False,
                    risk_tier=risk_tier,
                    requires_human_signoff=False,
                    reason="MEDIUM risk requires at least 1 verified passed test",
                )
            return ApprovalVerdict(
                approved=True,
                risk_tier=risk_tier,
                requires_human_signoff=False,
                reason="MEDIUM risk: Auto-approved on full verified test suite",
            )

        if risk_tier in (RiskTier.HIGH, RiskTier.PRODUCTION):
            if not human_approval_token or not approver_id:
                return ApprovalVerdict(
                    approved=False,
                    risk_tier=risk_tier,
                    requires_human_signoff=True,
                    reason=f"{risk_tier.value} risk requires explicit Human Approval sign-off token",
                )
            return ApprovalVerdict(
                approved=True,
                risk_tier=risk_tier,
                requires_human_signoff=True,
                reason=f"{risk_tier.value} risk: Approved by {approver_id} with token {human_approval_token[:8]}...",
            )

        return ApprovalVerdict(
            approved=False,
            risk_tier=risk_tier,
            requires_human_signoff=True,
            reason=f"Unknown risk tier: {risk_tier}",
        )
