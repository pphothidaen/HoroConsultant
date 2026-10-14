"""BaZi (Four Pillars of Destiny) computation facade and helper functions.

Provides clean typed access to the underlying BaZi calculation engine,
re-exporting lookup tables, pillar calculation utilities, and helper functions
used across annual timing, transit evaluation, and past pattern calibration.
"""

from __future__ import annotations

from datetime import date, datetime, time, timezone
from typing import Any

from project.core.bazi_engine import (
    BRANCH_ELEMENT,
    BRANCHES,
    HIDDEN_STEMS,
    STEM_ELEMENT,
    STEMS,
    BaZiEngine,
    _day_stem_branch,
    _hour_stem_branch,
    _month_stem_branch,
    _year_stem_branch,
)
from project.core.solar_time import SolarTimeResult, calculate_true_solar_time

__all__ = [
    "BRANCHES",
    "BRANCH_ELEMENT",
    "HIDDEN_STEMS",
    "STEMS",
    "STEM_ELEMENT",
    "BaZiEngine",
    "SolarTimeResult",
    "calculate_true_solar_time",
    "compute_annual_pillar",
    "compute_day_master",
    "compute_monthly_pillar",
    "compute_natal_pillars",
    "get_bazi_engine",
]


_ENGINE_INSTANCE: BaZiEngine | None = None


def get_bazi_engine() -> BaZiEngine:
    """Return a singleton instance of the BaZi calculation engine."""
    global _ENGINE_INSTANCE
    if _ENGINE_INSTANCE is None:
        _ENGINE_INSTANCE = BaZiEngine()
    return _ENGINE_INSTANCE


def compute_annual_pillar(year: int, month: int = 6, day: int = 15) -> dict[str, Any]:
    """Compute the annual Heavenly Stem and Earthly Branch for a target year.

    Args:
        year: Target Western Gregorian year (e.g. 2026).
        month: Month used for Lichun solar term reference (default 6 for mid-year).
        day: Day used for reference (default 15).

    Returns:
        Dict with stem, branch, element, polarity, and cycle index.
    """
    stem_idx, branch_idx = _year_stem_branch(year, month, day)
    stem_meta = STEMS[stem_idx]
    branch_meta = BRANCHES[branch_idx]
    cycle_index = (year - 1984) % 60
    return {
        "stem_index": stem_idx,
        "branch_index": branch_idx,
        "stem": stem_meta["name"],
        "branch": branch_meta["name"],
        "element": stem_meta["element"],
        "polarity": stem_meta["polarity"],
        "animal": branch_meta["animal"],
        "cycle_index": cycle_index,
    }


def compute_monthly_pillar(year: int, month: int, day: int = 15) -> dict[str, Any]:
    """Compute the monthly Heavenly Stem and Earthly Branch (Liu Yue).

    Args:
        year: Gregorian year (e.g. 2026).
        month: Gregorian month (1 through 12).
        day: Day for monthly pillar evaluation (default 15).

    Returns:
        Dict with stem, branch, element, polarity, and animal.
    """
    year_stem_idx, _ = _year_stem_branch(year, month, day)
    stem_idx, branch_idx = _month_stem_branch(year_stem_idx, month, day)
    stem_meta = STEMS[stem_idx]
    branch_meta = BRANCHES[branch_idx]
    return {
        "stem_index": stem_idx,
        "branch_index": branch_idx,
        "stem": stem_meta["name"],
        "branch": branch_meta["name"],
        "element": stem_meta["element"],
        "polarity": stem_meta["polarity"],
        "animal": branch_meta["animal"],
    }


def compute_day_master(birth_dt: datetime) -> dict[str, Any]:
    """Compute the Day Master (natal Day Stem) from birth datetime.

    Args:
        birth_dt: Birth datetime (local or solar time).

    Returns:
        Dict with stem name, element, polarity, and branch details.
    """
    stem_idx, branch_idx = _day_stem_branch(birth_dt)
    stem_meta = STEMS[stem_idx]
    branch_meta = BRANCHES[branch_idx]
    return {
        "stem_index": stem_idx,
        "branch_index": branch_idx,
        "name": stem_meta["name"],
        "element": stem_meta["element"],
        "polarity": stem_meta["polarity"],
        "day_branch": branch_meta["name"],
        "day_branch_animal": branch_meta["animal"],
    }


def compute_natal_pillars(
    birth_date: date,
    birth_time: time | None = None,
) -> dict[str, Any]:
    """Compute basic Four Pillars metadata for natal chart reference.

    When birth_time is None (unknown hour), the hour pillar is flagged as unknown.

    Args:
        birth_date: Date of birth.
        birth_time: Time of birth, or None if unknown.

    Returns:
        Dict containing year, month, day, and optional hour pillars.
    """
    dt_ref = datetime(birth_date.year, birth_date.month, birth_date.day, 12, 0, tzinfo=timezone.utc)
    year_stem_idx, year_branch_idx = _year_stem_branch(birth_date.year, birth_date.month, birth_date.day)
    month_stem_idx, month_branch_idx = _month_stem_branch(year_stem_idx, birth_date.month, birth_date.day)
    day_stem_idx, day_branch_idx = _day_stem_branch(dt_ref)

    result: dict[str, Any] = {
        "year": {
            "stem": STEMS[year_stem_idx]["name"],
            "branch": BRANCHES[year_branch_idx]["name"],
            "element": STEMS[year_stem_idx]["element"],
        },
        "month": {
            "stem": STEMS[month_stem_idx]["name"],
            "branch": BRANCHES[month_branch_idx]["name"],
            "element": STEMS[month_stem_idx]["element"],
        },
        "day": {
            "stem": STEMS[day_stem_idx]["name"],
            "branch": BRANCHES[day_branch_idx]["name"],
            "element": STEMS[day_stem_idx]["element"],
        },
        "day_master": STEMS[day_stem_idx]["name"],
        "day_master_element": STEMS[day_stem_idx]["element"],
        "unknown_hour": birth_time is None,
    }

    if birth_time is not None:
        h_stem_idx, h_branch_idx = _hour_stem_branch(day_stem_idx, birth_time.hour)
        result["hour"] = {
            "stem": STEMS[h_stem_idx]["name"],
            "branch": BRANCHES[h_branch_idx]["name"],
            "element": STEMS[h_stem_idx]["element"],
        }
    else:
        result["hour"] = None

    return result
