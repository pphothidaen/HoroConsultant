"""RED baseline for consensus proxy/shared-lineage independence remediation."""

from __future__ import annotations

from project.debate.consensus_matrix import arbitrate_monthly_consensus


def test_proxy_claims_do_not_create_independent_perfect_consensus() -> None:
    """Proxy claims from one lineage are unverified, not corroborating evidence."""

    months = [
        {
            "month": month,
            "career_score": 9,
            "finance_score": 2,
            "love_score": 6,
        }
        for month in range(1, 13)
    ]

    result = arbitrate_monthly_consensus(months, seed=0)

    assert result["consensus_score"] == 0.5
    assert result["arbitration_status"] == "ARBITRATED_WITH_CONFLICTS"
    assert result["tradition_conflicts"]

    for claim in result["monthly_consensus"]:
        assert claim["agreement_score"] == 0.5
        assert claim["conflict_detected"] is True
        assert claim["domain_agreements"] == {
            "career_score": 0.5,
            "finance_score": 0.5,
            "love_score": 0.5,
        }
