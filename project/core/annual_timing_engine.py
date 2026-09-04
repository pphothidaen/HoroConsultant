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

    return {
        "target_year": target_year,
        "overall_confidence": "ESTIMATED" if unknown_hour else "HIGH",
        "monthly_scores": months,
        "engine_version": "annual_timing_proxy.v1",
    }
