"""Deterministic annual timing proxies for Horo Lite unified readings."""

from __future__ import annotations

from datetime import date
from typing import Any

from project.debate.consensus_matrix import (
    DEFAULT_TRADITIONS_CONSIDERED,
    arbitrate_monthly_consensus,
)


_DOMAINS: tuple[str, ...] = ("career", "finance", "love")
_CYCLE_LABELS: tuple[str, ...] = (
    "Wood",
    "Fire",
    "Earth",
    "Metal",
    "Water",
)
_TRADITIONS_CONSIDERED: tuple[str, ...] = DEFAULT_TRADITIONS_CONSIDERED


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
    unknown_hour = bool(getattr(request, "unknown_hour", False))
    # When birth hour is unknown, ignore any supplied birth_time to ensure
    # scores are time-invariant.  Use the noon default (720 minutes // 30 = 24).
    if unknown_hour:
        time_bucket = 12 * 60 // 30  # noon
    else:
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


def _build_consensus_metadata(
    request: Any,
    months: list[dict[str, Any]],
    seed: int,
) -> dict[str, Any]:
    fixture_claims = getattr(request, "tradition_monthly_claims", None)
    if not isinstance(fixture_claims, list):
        fixture_claims = None

    return arbitrate_monthly_consensus(
        months,
        tradition_monthly_claims=fixture_claims,
        consensus_fixture_id=getattr(request, "consensus_fixture_id", None),
        seed=seed,
        traditions_considered=_TRADITIONS_CONSIDERED,
    )


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
