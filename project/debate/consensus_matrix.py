"""Deterministic consensus matrix arbitration for Horo Lite readings."""

from __future__ import annotations

from typing import Any, Sequence


CONSENSUS_MATRIX_SOURCE = "project.debate.consensus_matrix"
DEFAULT_TRADITIONS_CONSIDERED: tuple[str, ...] = (
    "thai_suriyayart",
    "bazi_liu_yue",
    "zi_wei",
)


def _clamp_score(value: int) -> int:
    return max(1, min(10, value))


def _numeric_scores(value: Any) -> list[float]:
    if not isinstance(value, dict):
        return []

    scores: list[float] = []
    for key, item in value.items():
        if key.endswith("_score") and isinstance(item, int | float):
            scores.append(float(item))
        elif isinstance(item, dict):
            scores.extend(_numeric_scores(item))
    return scores


_DOMAIN_KEYS = ("career_score", "finance_score", "love_score")


def _extract_domain_scores(
    tradition_claims: dict[str, dict[str, Any]],
) -> dict[str, list[float]]:
    """Collect per-domain scores across traditions, skipping None/non-numeric."""

    domain_scores: dict[str, list[float]] = {d: [] for d in _DOMAIN_KEYS}
    for _tradition_name, claim in tradition_claims.items():
        if not isinstance(claim, dict):
            continue
        for domain in _DOMAIN_KEYS:
            val = claim.get(domain)
            if isinstance(val, int | float):
                domain_scores[domain].append(float(val))
    return domain_scores


def _domain_agreement(scores: list[float], total_traditions: int) -> float:
    """Agreement for a single domain across traditions.

    * If fewer than 2 numeric scores exist the domain has missing evidence
      and agreement is unknown — returns 0.5 (below the 0.75 HITL threshold)
      to force human review rather than certifying high agreement.
    * If some but not all traditions contributed, agreement is capped at 0.85.
    * Otherwise, 1 - spread/10 (clamped to [0, 1]).
    """
    if len(scores) < 2:
        # Missing evidence: agreement is unknown, not high
        return 0.5
    if len(scores) < total_traditions:
        # Some traditions missing — cap agreement below full certainty
        spread = max(scores) - min(scores)
        return min(0.85, max(0.0, 1.0 - (spread / 10.0)))
    spread = max(scores) - min(scores)
    return max(0.0, min(1.0, 1.0 - (spread / 10.0)))


def _monthly_agreement_score_from_claims(
    tradition_claims: dict[str, dict[str, Any]],
) -> tuple[float, bool, dict[str, float]]:
    """Compute agreement WITHIN each domain separately, then average.

    Returns (aggregate_score, has_per_domain_conflict, domain_agreements).
    A per-domain conflict is flagged if ANY individual domain's agreement
    falls below 0.75, even if the aggregate average is above it.
    """
    total_traditions = len(tradition_claims)
    domain_scores = _extract_domain_scores(tradition_claims)

    domain_agreements: dict[str, float] = {}
    has_per_domain_conflict = False
    for domain, scores in domain_scores.items():
        agreement = _domain_agreement(scores, total_traditions)
        domain_agreements[domain] = agreement
        if agreement < 0.75:
            has_per_domain_conflict = True

    if not domain_agreements:
        return 1.0, False, {}
    aggregate = sum(domain_agreements.values()) / len(domain_agreements)
    return aggregate, has_per_domain_conflict, domain_agreements


def _monthly_agreement_score(scores: list[float]) -> float:
    """Legacy flat agreement (kept for backward compat if called externally)."""
    if len(scores) < 2:
        return 1.0
    spread = max(scores) - min(scores)
    return max(0.0, min(1.0, 1.0 - (spread / 10.0)))


def _default_tradition_claims(month: dict[str, Any], seed: int) -> dict[str, dict[str, Any]]:
    """Generate placeholder tradition claims from month scores.

    These are proxy claims: all traditions receive the same month scores
    because no real tradition engine exists yet.  The ``proxy`` flag marks
    them as manufactured so consumers can distinguish them from genuine
    multi-tradition computation.
    """
    month_number = int(month["month"])
    career_score = int(month.get("career_score", month.get("career_score_range", [5, 5])[0]))
    finance_score = int(month.get("finance_score", month.get("finance_score_range", [5, 5])[0]))
    love_score = int(month.get("love_score", month.get("love_score_range", [5, 5])[0]))

    return {
        "thai_suriyayart": {
            "career_score": career_score,
            "finance_score": finance_score,
            "love_score": love_score,
            "proxy": True,
            "claim": "transit-house proxy supports the monthly score band",
        },
        "bazi_liu_yue": {
            "career_score": career_score,
            "finance_score": finance_score,
            "love_score": love_score,
            "proxy": True,
            "claim": "monthly cycle proxy broadly agrees with the transit proxy",
        },
        "zi_wei": {
            "career_score": career_score,
            "finance_score": finance_score,
            "love_score": love_score,
            "proxy": True,
            "claim": "deterministic star-phase proxy does not create a material conflict",
        },
    }


def _fixture_claims_by_month(
    tradition_monthly_claims: Sequence[dict[str, Any]] | None,
) -> dict[int, dict[str, Any]]:
    fixture_by_month: dict[int, dict[str, Any]] = {}
    if tradition_monthly_claims is None:
        return fixture_by_month

    for claim in tradition_monthly_claims:
        if not isinstance(claim, dict):
            continue
        try:
            month_number = int(claim.get("month"))
        except (TypeError, ValueError):
            continue
        fixture_by_month[month_number] = claim
    return fixture_by_month


def arbitrate_monthly_consensus(
    months: Sequence[dict[str, Any]],
    *,
    tradition_monthly_claims: Sequence[dict[str, Any]] | None = None,
    consensus_fixture_id: str | None = None,
    seed: int = 0,
    traditions_considered: Sequence[str] = DEFAULT_TRADITIONS_CONSIDERED,
) -> dict[str, Any]:
    """Return deterministic monthly consensus metadata for annual timing output."""

    fixture_by_month = _fixture_claims_by_month(tradition_monthly_claims)
    arbitrated_claims: list[dict[str, Any]] = []
    agreement_scores: list[float] = []
    conflict_months: list[int] = []
    conflicting_traditions: set[str] = set()

    for month in months:
        month_number = int(month["month"])
        fixture_claim = fixture_by_month.get(month_number, {})
        tradition_claims = fixture_claim.get("tradition_claims")
        if not isinstance(tradition_claims, dict):
            tradition_claims = _default_tradition_claims(month, seed)

        agreement_score, has_domain_conflict, domain_details = (
            _monthly_agreement_score_from_claims(tradition_claims)
        )
        expected_conflict = bool(fixture_claim.get("expected_conflict"))
        # Conflict when: explicitly expected, aggregate score too low,
        # OR any individual domain has agreement below threshold.
        conflict_detected = (
            expected_conflict
            or agreement_score < 0.75
            or has_domain_conflict
        )
        if conflict_detected:
            conflict_months.append(month_number)
            conflicting_traditions.update(str(name) for name in tradition_claims)

        agreement_scores.append(agreement_score)
        arbitrated_claims.append(
            {
                "month": month_number,
                "agreement_score": round(agreement_score, 3),
                "conflict_detected": conflict_detected,
                "domain_agreements": {k: round(v, 3) for k, v in domain_details.items()},
                "tradition_claims": tradition_claims,
                "arbitrated_claim": (
                    "human review required for conflicting tradition claims"
                    if conflict_detected
                    else "traditions agree within deterministic tolerance"
                ),
            }
        )

    consensus_score = round(sum(agreement_scores) / max(len(agreement_scores), 1), 3)
    tradition_conflicts = [
        {
            "month": month_number,
            "conflicting_traditions": sorted(conflicting_traditions),
            "reason": "tradition monthly score spread exceeds arbitration tolerance",
        }
        for month_number in conflict_months
    ]
    arbitration_status = "ARBITRATED_WITH_CONFLICTS" if tradition_conflicts else "ARBITRATED"

    return {
        "engine_version": "horo_v3_consensus",
        "consensus_matrix_source": CONSENSUS_MATRIX_SOURCE,
        "consensus_fixture_id": consensus_fixture_id,
        "consensus_score": consensus_score,
        "arbitration_status": arbitration_status,
        "traditions_considered": list(traditions_considered),
        "tradition_conflicts": tradition_conflicts,
        "monthly_consensus": arbitrated_claims,
    }


class ConsensusMatrix:
    """Public deterministic consensus matrix interface."""

    def arbitrate_monthly_consensus(
        self,
        months: Sequence[dict[str, Any]],
        *,
        tradition_monthly_claims: Sequence[dict[str, Any]] | None = None,
        consensus_fixture_id: str | None = None,
        seed: int = 0,
        traditions_considered: Sequence[str] = DEFAULT_TRADITIONS_CONSIDERED,
    ) -> dict[str, Any]:
        """Return deterministic monthly consensus metadata for annual timing output."""

        return arbitrate_monthly_consensus(
            months,
            tradition_monthly_claims=tradition_monthly_claims,
            consensus_fixture_id=consensus_fixture_id,
            seed=seed,
            traditions_considered=traditions_considered,
        )
