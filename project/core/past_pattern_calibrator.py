"""Deterministic non-sensitive past pattern candidates for calibration."""

from __future__ import annotations

from datetime import date
from typing import Any

from project.core.unified_reading_engine import ALLOWED_FEEDBACK_CHOICES


_THEME_ORDER: tuple[str, ...] = (
    "education",
    "career_shift",
    "relocation",
    "financial_pressure",
    "work_role_change",
)

_BASIS_BY_THEME: dict[str, tuple[str, ...]] = {
    "education": ("bazi_resource_cycle", "thai_jupiter_learning_house"),
    "career_shift": ("bazi_influence_cycle", "thai_saturn_work_house"),
    "relocation": ("bazi_travel_marker_proxy", "thai_rahu_movement_house"),
    "financial_pressure": ("bazi_wealth_cycle", "thai_saturn_resource_house"),
    "work_role_change": ("bazi_output_cycle", "thai_jupiter_role_house"),
}


def _birth_date(request: Any) -> date:
    value = getattr(request, "birth_date")
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _seed(request: Any) -> int:
    birth = _birth_date(request)
    longitude_bucket = int(round((float(getattr(request, "longitude", 0.0)) + 180.0) * 10))
    latitude_bucket = int(round((float(getattr(request, "latitude", 0.0)) + 90.0) * 10))
    unknown_hour = bool(getattr(request, "unknown_hour", False))
    # When birth hour is unknown, ignore any supplied birth_time to ensure
    # past-pattern candidates are time-invariant.
    if unknown_hour:
        time_bucket = 0
    else:
        time_value = getattr(request, "birth_time", None)
        time_bucket = 0 if time_value is None else time_value.hour * 2 + time_value.minute // 30
    gender_seed = sum(ord(ch) for ch in str(getattr(request, "gender_at_birth", "") or ""))
    return (
        birth.year * 29
        + birth.month * 31
        + birth.day * 37
        + int(getattr(request, "target_year")) * 41
        + longitude_bucket
        + latitude_bucket
        + time_bucket
        + gender_seed
    )


def _candidate_years(birth_year: int, target_year: int, seed: int) -> list[int]:
    # Children too young for meaningful past-pattern analysis get no candidates.
    max_age = target_year - birth_year - 1
    if max_age < 8:
        return []

    preferred_ages = (16, 19, 22, 25, 28, 31, 34, 37, 40, 43, 46)
    offset = seed % 3
    years: list[int] = []
    for age in preferred_ages:
        adjusted_age = age + offset
        year = birth_year + adjusted_age
        if 8 <= adjusted_age <= max_age and year < target_year:
            years.append(year)
        if len(years) == 5:
            return years

    fallback_age = max(8, min(max_age, 12))
    while len(years) < 3 and fallback_age <= max_age:
        year = birth_year + fallback_age
        if year < target_year and year not in years:
            years.append(year)
        fallback_age += 2
    return years[:5]


def generate_past_pattern_candidates(request: Any) -> dict[str, Any]:
    """Return 0-5 deterministic, non-sensitive calibration candidates.

    For persons too young for past-pattern analysis (< ~8 years old),
    an empty candidates list is returned.
    """

    birth = _birth_date(request)
    target_year = int(getattr(request, "target_year"))
    seed = _seed(request)
    start_theme = seed % len(_THEME_ORDER)
    years = _candidate_years(birth.year, target_year, seed)

    candidates: list[dict[str, Any]] = []
    for index, start_year in enumerate(years):
        end_year = min(start_year + 1, target_year - 1)
        theme = _THEME_ORDER[(start_theme + index) % len(_THEME_ORDER)]
        year_range = [start_year, end_year]
        age_range = [year_range[0] - birth.year, year_range[1] - birth.year]
        candidates.append(
            {
                "pattern_id": f"{theme}_{year_range[0]}_{year_range[1]}",
                "year_range": year_range,
                "age_range": age_range,
                "theme": theme,
                "deterministic_basis": list(_BASIS_BY_THEME[theme]),
                "sensitive_category": False,
                "allowed_feedback": list(ALLOWED_FEEDBACK_CHOICES),
                "user_feedback": None,
            }
        )

    return {
        "target_year": target_year,
        "candidates": candidates,
        "engine_version": "past_pattern_calibrator.v1",
    }
