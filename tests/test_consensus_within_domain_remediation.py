"""RED baseline tests for TICKET-HLITE-REVIEW-REMEDIATION-20260907-02.

Cross-domain consensus fix: traditions that agree within each domain must
not be falsely flagged as conflicting. Genuine within-domain disagreement
must still be detected.
"""

from __future__ import annotations

import pytest

from project.debate.consensus_matrix import (
    _default_tradition_claims,
    _monthly_agreement_score,
    arbitrate_monthly_consensus,
)


# ---------------------------------------------------------------------------
# 1. Identical tradition scores → no conflict
# ---------------------------------------------------------------------------
def test_identical_tradition_scores_no_conflict() -> None:
    """When all three traditions report identical scores for every domain
    (career=9, finance=2, love=6), agreement should be 1.0 and no
    conflict detected."""

    months = [
        {
            "month": m,
            "career_score": 9,
            "finance_score": 2,
            "love_score": 6,
        }
        for m in range(1, 13)
    ]

    # Use the default tradition claims path (no fixture override).
    result = arbitrate_monthly_consensus(months, seed=0)

    for claim in result["monthly_consensus"]:
        assert claim["agreement_score"] == 1.0, (
            f"Month {claim['month']}: identical tradition scores must yield "
            f"agreement_score 1.0, got {claim['agreement_score']}"
        )
        assert claim["conflict_detected"] is False, (
            f"Month {claim['month']}: identical tradition scores must NOT "
            f"be flagged as conflict"
        )

    assert result["arbitration_status"] == "ARBITRATED"
    assert result["tradition_conflicts"] == []


# ---------------------------------------------------------------------------
# 2. Genuine within-domain disagreement IS detected
# ---------------------------------------------------------------------------
def test_genuine_within_domain_disagreement_detected() -> None:
    """When traditions genuinely disagree within a domain (e.g. thai
    career=9, bazi career=1), conflict IS detected."""

    claims_per_month = [
        {
            "month": m,
            "tradition_claims": {
                "thai_suriyayart": {
                    "career_score": 9,
                    "finance_score": 5,
                    "love_score": 5,
                    "claim": "strong",
                },
                "bazi_liu_yue": {
                    "career_score": 1,
                    "finance_score": 5,
                    "love_score": 5,
                    "claim": "weak",
                },
                "zi_wei": {
                    "career_score": 2,
                    "finance_score": 5,
                    "love_score": 5,
                    "claim": "cautious",
                },
            },
        }
        for m in range(1, 13)
    ]
    months = [{"month": m} for m in range(1, 13)]

    result = arbitrate_monthly_consensus(
        months, tradition_monthly_claims=claims_per_month
    )

    # With career spread of 8 (9-1) the agreement should be well below 1.0
    for claim in result["monthly_consensus"]:
        assert claim["agreement_score"] < 1.0, (
            f"Month {claim['month']}: genuine career disagreement must "
            f"lower agreement_score"
        )

    # At least some months should flag conflict
    assert result["arbitration_status"] == "ARBITRATED_WITH_CONFLICTS", (
        "Genuine within-domain disagreement must produce conflicts"
    )


# ---------------------------------------------------------------------------
# 3. Missing tradition evidence ≠ perfect agreement
# ---------------------------------------------------------------------------
def test_missing_tradition_evidence_not_perfect_agreement() -> None:
    """When a tradition has missing/None scores, it cannot count as
    perfect agreement."""

    claims_per_month = [
        {
            "month": m,
            "tradition_claims": {
                "thai_suriyayart": {
                    "career_score": 9,
                    "finance_score": 5,
                    "love_score": 6,
                    "claim": "strong",
                },
                "bazi_liu_yue": {
                    "career_score": None,
                    "finance_score": None,
                    "love_score": None,
                    "claim": "no data",
                },
                "zi_wei": {
                    "career_score": 9,
                    "finance_score": 5,
                    "love_score": 6,
                    "claim": "agrees",
                },
            },
        }
        for m in range(1, 13)
    ]
    months = [{"month": m} for m in range(1, 13)]

    result = arbitrate_monthly_consensus(
        months, tradition_monthly_claims=claims_per_month
    )

    for claim in result["monthly_consensus"]:
        assert claim["agreement_score"] < 1.0, (
            f"Month {claim['month']}: missing tradition evidence cannot "
            f"count as perfect agreement (got {claim['agreement_score']})"
        )


# ---------------------------------------------------------------------------
# 4. Default tradition claims have no artificial shifts
# ---------------------------------------------------------------------------
def test_default_tradition_claims_no_artificial_shifts() -> None:
    """The default claims generator must not apply artificial seed-based
    shifts. All traditions should report the same raw scores."""

    month_data = {
        "month": 3,
        "career_score": 7,
        "finance_score": 4,
        "love_score": 8,
    }

    for seed in range(10):
        claims = _default_tradition_claims(month_data, seed)

        thai = claims["thai_suriyayart"]
        bazi = claims["bazi_liu_yue"]
        zi_wei = claims["zi_wei"]

        for domain in ("career_score", "finance_score", "love_score"):
            assert thai[domain] == bazi[domain] == zi_wei[domain], (
                f"seed={seed}, domain={domain}: all traditions must report "
                f"the same score without artificial shifts, got "
                f"thai={thai[domain]}, bazi={bazi[domain]}, zi_wei={zi_wei[domain]}"
            )


# ---------------------------------------------------------------------------
# 5. Cross-domain difference is NOT a conflict
# ---------------------------------------------------------------------------
def test_cross_domain_difference_not_conflict() -> None:
    """Different scores across domains (career=9, finance=2) from the
    SAME tradition is NOT a conflict."""

    months = [
        {
            "month": m,
            "career_score": 9,
            "finance_score": 2,
            "love_score": 5,
        }
        for m in range(1, 13)
    ]

    result = arbitrate_monthly_consensus(months, seed=0)

    # Even though career and finance differ by 7, that is cross-domain
    # (not cross-tradition), so agreement should be 1.0 per domain and
    # no conflict should be detected.
    for claim in result["monthly_consensus"]:
        assert claim["agreement_score"] == 1.0, (
            f"Month {claim['month']}: cross-domain score differences "
            f"must not lower within-domain agreement "
            f"(got {claim['agreement_score']})"
        )
        assert claim["conflict_detected"] is False, (
            f"Month {claim['month']}: cross-domain differences must NOT "
            f"be flagged as conflict"
        )

    assert result["arbitration_status"] == "ARBITRATED"


# ---------------------------------------------------------------------------
# 6. Empty claims dictionary → low agreement (CHANGES_REQUESTED P1 #2)
# ---------------------------------------------------------------------------
def test_empty_claims_low_agreement() -> None:
    """With an empty claim dictionary all domains yield unknown agreement.
    Missing evidence must NOT certify high agreement (must be below 0.75)."""

    claims_per_month = [
        {
            "month": m,
            "tradition_claims": {},
        }
        for m in range(1, 13)
    ]
    months = [{"month": m} for m in range(1, 13)]

    result = arbitrate_monthly_consensus(
        months, tradition_monthly_claims=claims_per_month
    )

    for claim in result["monthly_consensus"]:
        # With no traditions at all, domain agreement is unknown (0.5)
        # and the aggregate is 0.5, well below 0.75
        assert claim["agreement_score"] < 0.75, (
            f"Month {claim['month']}: empty claims must NOT produce high "
            f"agreement (got {claim['agreement_score']})"
        )


# ---------------------------------------------------------------------------
# 7. Domain averaging must not mask single-domain conflict
#    (CHANGES_REQUESTED P1 #3)
# ---------------------------------------------------------------------------
def test_single_domain_conflict_not_masked_by_averaging() -> None:
    """One domain with spread=7 (agreement ~0.3) and two domains that fully
    agree (agreement=1.0) must still flag conflict, even though the average
    would be ~0.767 (above 0.75)."""

    claims_per_month = [
        {
            "month": m,
            "tradition_claims": {
                "thai_suriyayart": {
                    "career_score": 9,
                    "finance_score": 5,
                    "love_score": 5,
                    "claim": "strong career",
                },
                "bazi_liu_yue": {
                    "career_score": 2,
                    "finance_score": 5,
                    "love_score": 5,
                    "claim": "weak career",
                },
                "zi_wei": {
                    "career_score": 2,
                    "finance_score": 5,
                    "love_score": 5,
                    "claim": "cautious career",
                },
            },
        }
        for m in range(1, 13)
    ]
    months = [{"month": m} for m in range(1, 13)]

    result = arbitrate_monthly_consensus(
        months, tradition_monthly_claims=claims_per_month
    )

    for claim in result["monthly_consensus"]:
        # career agreement = 1 - 7/10 = 0.3, finance = 1.0, love = 1.0
        # Average = (0.3 + 1.0 + 1.0) / 3 = 0.767, which WOULD pass 0.75
        # But career domain individually is below 0.75, so conflict MUST be
        # detected via per-domain check.
        assert claim["conflict_detected"] is True, (
            f"Month {claim['month']}: single-domain conflict (career) "
            f"must be detected even when averaging would mask it"
        )
        # Verify per-domain detail shows the career conflict
        domain_agr = claim.get("domain_agreements", {})
        assert domain_agr.get("career_score", 1.0) < 0.75, (
            f"Month {claim['month']}: career domain agreement must be "
            f"below threshold"
        )

    assert result["arbitration_status"] == "ARBITRATED_WITH_CONFLICTS"


# ---------------------------------------------------------------------------
# 8. Default tradition claims carry proxy flag (CHANGES_REQUESTED P1 #1)
# ---------------------------------------------------------------------------
def test_default_tradition_claims_carry_proxy_flag() -> None:
    """Default claims are proxy-sourced and must be flagged as such."""

    month_data = {
        "month": 6,
        "career_score": 7,
        "finance_score": 4,
        "love_score": 8,
    }

    claims = _default_tradition_claims(month_data, seed=42)

    for tradition_name, tradition_data in claims.items():
        assert tradition_data.get("proxy") is True, (
            f"Tradition '{tradition_name}': default claims must carry "
            f"proxy=True flag"
        )

