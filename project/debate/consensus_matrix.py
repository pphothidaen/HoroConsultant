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


def _default_tradition_claims(month: dict[str, Any], seed: int) -> dict[str, dict[str, Any]]:
    month_number = int(month["month"])
    career_score = int(month.get("career_score", month.get("career_score_range", [5, 5])[0]))
    finance_score = int(month.get("finance_score", month.get("finance_score_range", [5, 5])[0]))
    love_score = int(month.get("love_score", month.get("love_score_range", [5, 5])[0]))

    bazi_shift = ((seed + month_number) % 3) - 1
    zi_wei_shift = ((seed // 3 + month_number) % 3) - 1
    return {
        "thai_suriyayart": {
            "career_score": career_score,
            "finance_score": finance_score,
            "love_score": love_score,
            "claim": "transit-house proxy supports the monthly score band",
        },
        "bazi_liu_yue": {
            "career_score": _clamp_score(career_score + bazi_shift),
            "finance_score": _clamp_score(finance_score + bazi_shift),
            "love_score": _clamp_score(love_score + bazi_shift),
            "claim": "monthly cycle proxy broadly agrees with the transit proxy",
        },
        "zi_wei": {
            "career_score": _clamp_score(career_score + zi_wei_shift),
            "finance_score": _clamp_score(finance_score + zi_wei_shift),
            "love_score": _clamp_score(love_score + zi_wei_shift),
            "claim": "deterministic star-phase proxy does not create a material conflict",
        },
    }


def _monthly_agreement_score(scores: list[float]) -> float:
    if len(scores) < 2:
        return 1.0
    spread = max(scores) - min(scores)
    return max(0.0, min(1.0, 1.0 - (spread / 10.0)))


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

        scores = _numeric_scores(tradition_claims)
        agreement_score = _monthly_agreement_score(scores)
        expected_conflict = bool(fixture_claim.get("expected_conflict"))
        conflict_detected = expected_conflict or agreement_score < 0.75
        if conflict_detected:
            conflict_months.append(month_number)
            conflicting_traditions.update(str(name) for name in tradition_claims)

        agreement_scores.append(agreement_score)
        arbitrated_claims.append(
            {
                "month": month_number,
                "agreement_score": round(agreement_score, 3),
                "conflict_detected": conflict_detected,
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
