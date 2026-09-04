"""Deterministic annual timing proxies for Horo Lite unified readings."""

from __future__ import annotations

from datetime import date
from typing import Any


_DOMAINS: tuple[str, ...] = ("career", "finance", "love")
_CYCLE_LABELS: tuple[str, ...] = (
    "Wood",
    "Fire",
    "Earth",
    "Metal",
    "Water",
)
_TRADITIONS_CONSIDERED: tuple[str, ...] = (
    "thai_suriyayart",
    "bazi_liu_yue",
    "zi_wei",
)


def _clamp_score(value: int) -> int:
    return max(1, min(10, value))


def _birth_time_minutes(request: Any) -> int:
    birth_time = getattr(request, "birth_time", None)
    if birth_time is None:
        return 12 * 60
    return birth_time.hour * 60 + birth_time.minute


def _birth_date(request: Any) -> date:
    value = getattr(request, "birth_date")
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _request_seed(request: Any) -> int:
    birth = _birth_date(request)
    longitude_bucket = int(round((float(getattr(request, "longitude", 0.0)) + 180.0) * 10))
    latitude_bucket = int(round((float(getattr(request, "latitude", 0.0)) + 90.0) * 10))
    time_bucket = _birth_time_minutes(request) // 30
    gender_seed = sum(ord(ch) for ch in str(getattr(request, "gender_at_birth", "") or ""))
    return (
        birth.year * 37
        + birth.month * 41
        + birth.day * 43
        + int(getattr(request, "target_year")) * 47
        + longitude_bucket
        + latitude_bucket
        + time_bucket * 11
        + gender_seed
    )


def _cycle_index(year: int, month: int, offset: int) -> int:
    return ((year - 1984) * 12 + month - 1 + offset) % 60


def _score(seed: int, year: int, month: int, domain_offset: int) -> int:
    annual_idx = (year - 1984 + domain_offset) % 60
    monthly_idx = _cycle_index(year, month, domain_offset * 7)
    raw = (
        seed
        + annual_idx * (domain_offset + 3)
        + monthly_idx * (domain_offset + 5)
        + month * (domain_offset + 2)
    )
    return _clamp_score((raw % 10) + 1)


def _score_range(score: int, month: int) -> list[int]:
    spread = 1 + (month % 2)
    return [_clamp_score(score - spread), _clamp_score(score + spread)]


def _stable_text_checksum(value: Any) -> int:
    return sum(ord(ch) for ch in str(value or ""))


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


def _build_consensus_metadata(
    request: Any,
    months: list[dict[str, Any]],
    seed: int,
) -> dict[str, Any]:
    fixture_claims = getattr(request, "tradition_monthly_claims", None)
    fixture_by_month: dict[int, dict[str, Any]] = {}
    if isinstance(fixture_claims, list):
        for claim in fixture_claims:
            if not isinstance(claim, dict):
                continue
            try:
                month_number = int(claim.get("month"))
            except (TypeError, ValueError):
                continue
            fixture_by_month[month_number] = claim

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
        "consensus_fixture_id": getattr(request, "consensus_fixture_id", None),
        "consensus_score": consensus_score,
        "arbitration_status": arbitration_status,
        "traditions_considered": list(_TRADITIONS_CONSIDERED),
        "tradition_conflicts": tradition_conflicts,
        "monthly_consensus": arbitrated_claims,
    }


def _build_hitl_payload(
    request: Any,
    metadata: dict[str, Any],
    unknown_hour: bool,
    seed: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    consensus_score = float(metadata["consensus_score"])
    tradition_conflict = bool(metadata["tradition_conflicts"])
    force_human_review = bool(getattr(request, "force_human_review", False))
    uncertain_birth_time = unknown_hour
    low_consensus = consensus_score < 0.75
    required_human_review = (
        low_consensus
        or tradition_conflict
        or force_human_review
        or uncertain_birth_time
    )

    flags = {
        "required_human_review": required_human_review,
        "low_consensus": low_consensus,
        "tradition_conflict": tradition_conflict,
        "conflict_detected": tradition_conflict,
        "force_human_review": force_human_review,
        "uncertain_birth_time": uncertain_birth_time,
    }
    trigger_reasons = [
        key
        for key in (
            "low_consensus",
            "tradition_conflict",
            "force_human_review",
            "uncertain_birth_time",
        )
        if flags[key]
    ]
    routing = {
        "status": "QUEUED_FOR_HUMAN_REVIEW" if required_human_review else "NOT_REQUIRED",
        "reason": "hitl_triggered" if required_human_review else "consensus_verified",
        "trigger_reasons": trigger_reasons,
        "required_human_review": required_human_review,
        "conflict_detected": tradition_conflict,
        "conflicting_domains": sorted(
            {
                tradition
                for conflict in metadata["tradition_conflicts"]
                for tradition in conflict.get("conflicting_traditions", [])
            }
        ),
        "consensus_score": consensus_score,
        "routing_key": (
            f"horo_v3_consensus_{getattr(request, 'target_year')}_"
            f"{seed}_{_stable_text_checksum(getattr(request, 'consensus_fixture_id', ''))}"
        ),
    }
    return flags, routing


def calculate_annual_timing(request: Any) -> dict[str, Any]:
    """Return deterministic 12-month annual timing scores.

    This is a traceable Phase B proxy. It combines target-year/month sexagenary
    cycle positions with coarse Thai Suriyayart-style transit houses. It does
    not claim precise ephemeris calculation.
    """

    target_year = int(getattr(request, "target_year"))
    unknown_hour = bool(getattr(request, "unknown_hour", False)) or getattr(request, "birth_time", None) is None
    seed = _request_seed(request)
    birth = _birth_date(request)

    months: list[dict[str, Any]] = []
    for month in range(1, 13):
        annual_cycle = (target_year - 1984) % 60
        monthly_cycle = _cycle_index(target_year, month, seed % 12)
        jupiter_house = (target_year - birth.year + month + seed) % 12 + 1
        saturn_house = ((target_year - birth.year) * 2 + month + seed // 3) % 12 + 1
        rahu_house = (12 - ((target_year - birth.year + month + seed // 5) % 12)) or 12

        item: dict[str, Any] = {
            "month": month,
            "confidence": "ESTIMATED" if unknown_hour else "HIGH",
            "score_basis": {
                "thai_suriyayart_proxy": {
                    "jupiter_house": jupiter_house,
                    "saturn_house": saturn_house,
                    "rahu_house": rahu_house,
                    "precision": "coarse deterministic transit-house proxy",
                },
                "bazi_liu_yue_proxy": {
                    "annual_cycle_index": annual_cycle,
                    "monthly_cycle_index": monthly_cycle,
                    "cycle_element": _CYCLE_LABELS[monthly_cycle % len(_CYCLE_LABELS)],
                },
            },
            "reasons": [
                "Thai Suriyayart proxy house positions are present",
                "BaZi monthly cycle proxy is present",
            ],
        }

        for index, domain in enumerate(_DOMAINS):
            score = _score(seed, target_year, month, index)
            if unknown_hour:
                item[f"{domain}_score_range"] = _score_range(score, month)
            else:
                item[f"{domain}_score"] = score

        months.append(item)

    consensus_metadata = _build_consensus_metadata(request, months, seed)
    hitl_flags, hitl_routing = _build_hitl_payload(
        request,
        consensus_metadata,
        unknown_hour,
        seed,
    )

    return {
        "target_year": target_year,
        "overall_confidence": "ESTIMATED" if unknown_hour else "HIGH",
        "monthly_scores": months,
        "engine_version": "annual_timing_proxy.v1",
        "consensus_metadata": consensus_metadata,
        "hitl_flags": hitl_flags,
        "hitl_routing": hitl_routing,
    }
