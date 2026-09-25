"""Unit tests for RiskTierGate (AT-12)."""

import pytest

from project.core.risk_tier_gate import ApprovalVerdict, RiskTier, RiskTierGate


@pytest.fixture
def gate():
    return RiskTierGate()


@pytest.fixture
def base_evidence():
    return {
        "tests": {"total": 5, "passed": 5, "failed": 0, "skipped": 0},
        "acceptance_checks": [{"check_id": "AC-1", "status": "passed", "detail": "OK"}],
    }


def test_low_risk_auto_approves(gate, base_evidence):
    verdict = gate.evaluate(RiskTier.LOW, base_evidence)
    assert verdict.approved is True
    assert verdict.requires_human_signoff is False


def test_medium_risk_auto_approves_with_tests(gate, base_evidence):
    verdict = gate.evaluate(RiskTier.MEDIUM, base_evidence)
    assert verdict.approved is True
    assert verdict.requires_human_signoff is False


def test_high_risk_requires_human_token(gate, base_evidence):
    # Without token -> Blocked
    verdict = gate.evaluate(RiskTier.HIGH, base_evidence)
    assert verdict.approved is False
    assert verdict.requires_human_signoff is True

    # With token and approver -> Approved
    verdict_approved = gate.evaluate(
        RiskTier.HIGH,
        base_evidence,
        human_approval_token="token-abc-123456",
        approver_id="lead-engineer",
    )
    assert verdict_approved.approved is True


def test_production_risk_with_failed_tests_blocked(gate):
    bad_evidence = {
        "tests": {"total": 5, "passed": 4, "failed": 1, "skipped": 0},
    }
    verdict = gate.evaluate(
        RiskTier.PRODUCTION,
        bad_evidence,
        human_approval_token="token-abc",
        approver_id="lead-engineer",
    )
    assert verdict.approved is False
    assert "1 failed tests" in verdict.reason
