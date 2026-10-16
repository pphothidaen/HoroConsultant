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
    TEN_GOD_INFO,
    BaZiEngine,
    _GENERAL_STAR,
    _INTELLIGENCE_BRANCH,
    _KONG_WANG_MAP,
    _NOBLEMAN_BRANCHES,
    _PEACH_BLOSSOM,
    _PROSPERITY_BRANCH,
    _TALENT_STAR,
    _TRAVELLING_HORSE,
    _YANG_REN_BRANCH,
    _day_stem_branch,
    _hour_stem_branch,
    _month_stem_branch,
    _year_stem_branch,
    compute_general_stars,
    compute_pillar_stars,
    compute_symbolic_stars,
    ten_god,
)
from project.core.solar_time import SolarTimeResult, calculate_true_solar_time

TEN_GOD_METADATA: dict[str, dict[str, str]] = {
    "FR": {"code": "FR", "zh": "比肩", "en": "Friend", "th": "เพื่อน/มิตร", "structure": "Companion"},
    "RW": {"code": "RW", "zh": "劫財", "en": "Rob Wealth", "th": "ช่วงชิง/แข่งขัน", "structure": "Companion"},
    "EG": {"code": "EG", "zh": "食神", "en": "Eating God", "th": "ผลผลิต/เทพอาหาร", "structure": "Output"},
    "HO": {"code": "HO", "zh": "傷官", "en": "Hurting Officer", "th": "แสดงออก/สติปัญญา", "structure": "Output"},
    "DW": {"code": "DW", "zh": "正財", "en": "Direct Wealth", "th": "รายได้หลัก/ทรัพย์สิน", "structure": "Wealth"},
    "IW": {"code": "IW", "zh": "偏財", "en": "Indirect Wealth", "th": "โชคลาภจร/การลงทุน", "structure": "Wealth"},
    "DO": {"code": "DO", "zh": "正官", "en": "Direct Officer", "th": "ชื่อเสียง/เกียรติยศ", "structure": "Influence"},
    "7K": {"code": "7K", "zh": "七殺", "en": "Seven Killings", "th": "อำนาจเด็ดขาด/อุปสรรค", "structure": "Influence"},
    "DR": {"code": "DR", "zh": "正印", "en": "Direct Resource", "th": "ผู้อุปถัมภ์/คุณธรรม", "structure": "Resource"},
    "IR": {"code": "IR", "zh": "偏印", "en": "Indirect Resource", "th": "ปัญญาญาณ/วิชาลี้ลับ", "structure": "Resource"},
    "DM": {"code": "DM", "zh": "日主", "en": "Day Master", "th": "ตัวตน/ดิถี", "structure": "Companion"},
}

SHEN_SHA_METADATA: dict[str, dict[str, str]] = {
    "NOBLEMAN": {"code": "NOBLEMAN", "zh": "天乙貴人", "en": "Tian Yi Nobleman", "th": "เทพอุปถัมภ์/ขุนนางสวรรค์", "category": "heavenly"},
    "INTELLIGENCE": {"code": "INTELLIGENCE", "zh": "文昌", "en": "Academic Star / Wen Chang", "th": "ดาวบัณฑิต/ปัญญา", "category": "heavenly"},
    "PROSPERITY": {"code": "PROSPERITY", "zh": "祿神", "en": "Prosperity / Lu Shen", "th": "ดาวลาภยศ/ความมั่งคั่ง", "category": "heavenly"},
    "YANG_REN": {"code": "YANG_REN", "zh": "羊刃", "en": "Yang Blade / Yang Ren", "th": "ดาวมีดแพะ/อำนาจเด็ดขาด", "category": "heavenly"},
    "PEACH_BLOSSOM": {"code": "PEACH_BLOSSOM", "zh": "桃花", "en": "Peach Blossom / Tao Hua", "th": "ดาวเสน่ห์ดอกท้อ", "category": "heavenly"},
    "GENERAL": {"code": "GENERAL", "zh": "將星", "en": "General Star", "th": "ดาวขุนพล/ผู้นำ", "category": "earthly"},
    "TALENT": {"code": "TALENT", "zh": "華蓋", "en": "Canopy / Hua Gai", "th": "ดาวศิลปะ/ปัญญาญาณ", "category": "earthly"},
    "TRAVELLING_HORSE": {"code": "TRAVELLING_HORSE", "zh": "驛馬", "en": "Travelling Horse / Yi Ma", "th": "ดาวม้าศึก/การเดินทาง", "category": "earthly"},
    "KONG_WANG": {"code": "KONG_WANG", "zh": "空亡", "en": "Void / Kong Wang", "th": "ดาวความว่างเปล่า", "category": "void"},
}

__all__ = [
    "BRANCHES",
    "BRANCH_ELEMENT",
    "HIDDEN_STEMS",
    "SHEN_SHA_METADATA",
    "STEMS",
    "STEM_ELEMENT",
    "TEN_GOD_INFO",
    "TEN_GOD_METADATA",
    "BaZiEngine",
    "SolarTimeResult",
    "calculate_true_solar_time",
    "compute_annual_pillar",
    "compute_day_master",
    "compute_general_stars",
    "compute_monthly_pillar",
    "compute_natal_pillars",
    "compute_pillar_stars",
    "compute_shen_sha",
    "compute_symbolic_stars",
    "compute_ten_gods",
    "get_bazi_engine",
    "ten_god",
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

    result["ten_gods"] = compute_ten_gods(result)
    result["shen_sha"] = compute_shen_sha(result)
    return result


def compute_ten_gods(pillars: dict[str, Any]) -> dict[str, Any]:
    """Compute Ten Gods (Shi Shen) for Four Pillars stems and branch hidden stems.

    Provides Python dual-engine parity with calculateBaZiTenGods in unified_reading_engine.js.

    Args:
        pillars: Four pillars dictionary (accepts nested pillars dict, natal pillars result,
                 or flat dict with year_stem, month_stem, day_stem, etc.)

    Returns:
        Dict with day_master, stems, and hidden_stems mappings.
    """
    if not pillars or not isinstance(pillars, dict):
        return {"day_master": None, "stems": {}, "hidden_stems": {}}

    def _extract_stem(val: Any) -> str | None:
        if not val:
            return None
        if isinstance(val, str):
            return val
        if isinstance(val, dict):
            return val.get("char") or val.get("stem") or val.get("name")
        return None

    def _extract_branch(val: Any) -> str | None:
        if not val:
            return None
        if isinstance(val, str):
            return val
        if isinstance(val, dict):
            return val.get("char") or val.get("branch") or val.get("name")
        return None

    dm_stem = (
        _extract_stem(pillars.get("day_master"))
        or _extract_stem(pillars.get("day_stem"))
        or _extract_stem((pillars.get("day") or {}).get("stem") if isinstance(pillars.get("day"), dict) else None)
    )

    year_stem = _extract_stem(pillars.get("year_stem")) or _extract_stem(
        (pillars.get("year") or {}).get("stem") if isinstance(pillars.get("year"), dict) else None
    )
    month_stem = _extract_stem(pillars.get("month_stem")) or _extract_stem(
        (pillars.get("month") or {}).get("stem") if isinstance(pillars.get("month"), dict) else None
    )
    day_stem = _extract_stem(pillars.get("day_stem")) or dm_stem
    hour_stem = _extract_stem(pillars.get("hour_stem")) or _extract_stem(
        (pillars.get("hour") or {}).get("stem") if isinstance(pillars.get("hour"), dict) else None
    )

    year_branch = _extract_branch(pillars.get("year_branch")) or _extract_branch(
        (pillars.get("year") or {}).get("branch") if isinstance(pillars.get("year"), dict) else None
    )
    month_branch = _extract_branch(pillars.get("month_branch")) or _extract_branch(
        (pillars.get("month") or {}).get("branch") if isinstance(pillars.get("month"), dict) else None
    )
    day_branch = _extract_branch(pillars.get("day_branch")) or _extract_branch(
        (pillars.get("day") or {}).get("branch") if isinstance(pillars.get("day"), dict) else None
    )
    hour_branch = _extract_branch(pillars.get("hour_branch")) or _extract_branch(
        (pillars.get("hour") or {}).get("branch") if isinstance(pillars.get("hour"), dict) else None
    )

    def _resolve_god(target: str | None, is_dm: bool = False) -> dict[str, str] | None:
        if not dm_stem:
            return None
        if is_dm:
            return TEN_GOD_METADATA["DM"]
        if not target:
            return None
        code = ten_god(dm_stem, target)
        return TEN_GOD_METADATA.get(code)

    stems = {
        "year": _resolve_god(year_stem),
        "month": _resolve_god(month_stem),
        "day": _resolve_god(day_stem, is_dm=True),
        "hour": _resolve_god(hour_stem),
        "year_stem": _resolve_god(year_stem),
        "month_stem": _resolve_god(month_stem),
        "day_stem": _resolve_god(day_stem, is_dm=True),
        "hour_stem": _resolve_god(hour_stem),
    }

    def _map_hidden(branch: str | None) -> list[dict[str, Any]]:
        if not branch or branch not in HIDDEN_STEMS or not dm_stem:
            return []
        out = []
        for hs_stem, weight in HIDDEN_STEMS[branch]:
            code = ten_god(dm_stem, hs_stem)
            meta = TEN_GOD_METADATA.get(code, {})
            out.append({
                "stem": hs_stem,
                "weight": weight,
                "element": STEM_ELEMENT.get(hs_stem, ""),
                "ten_god": meta,
                "ten_god_code": code,
                "code": code,
                "zh": meta.get("zh", ""),
                "en": meta.get("en", ""),
                "th": meta.get("th", ""),
            })
        return out

    hidden_stems = {
        "year": _map_hidden(year_branch),
        "month": _map_hidden(month_branch),
        "day": _map_hidden(day_branch),
        "hour": _map_hidden(hour_branch),
        "year_branch": _map_hidden(year_branch),
        "month_branch": _map_hidden(month_branch),
        "day_branch": _map_hidden(day_branch),
        "hour_branch": _map_hidden(hour_branch),
    }

    return {
        "day_master": dm_stem,
        "stems": stems,
        "hidden_stems": hidden_stems,
    }


class StarList(list):
    """List subclass that supports string membership checks by star code or name."""

    def __contains__(self, item: Any) -> bool:
        if super().__contains__(item):
            return True
        for elem in self:
            if isinstance(elem, dict) and (
                elem.get("code") == item
                or elem.get("zh") == item
                or elem.get("en") == item
                or elem.get("th") == item
            ):
                return True
        return False


def compute_shen_sha(chart: dict[str, Any]) -> dict[str, Any]:
    """Compute Shen Sha (Auxiliary Stars) for Four Pillars chart.

    Provides Python dual-engine parity with calculateBaZiShenSha in unified_reading_engine.js.

    Args:
        chart: BaZi chart dictionary (flat or nested with pillars).

    Returns:
        Dict with pillars (year, month, day, hour) star lists and active_stars list.
    """
    if not chart or not isinstance(chart, dict):
        return {
            "pillars": {
                "year": StarList(),
                "month": StarList(),
                "day": StarList(),
                "hour": StarList(),
            },
            "active_stars": StarList(),
        }

    def _extract_stem(val: Any) -> str | None:
        if not val:
            return None
        if isinstance(val, str):
            return val
        if isinstance(val, dict):
            return val.get("char") or val.get("stem") or val.get("name")
        return None

    def _extract_branch(val: Any) -> str | None:
        if not val:
            return None
        if isinstance(val, str):
            return val
        if isinstance(val, dict):
            return val.get("char") or val.get("branch") or val.get("name")
        return None

    p_source = chart.get("pillars") if isinstance(chart.get("pillars"), dict) else chart

    dm_stem = (
        _extract_stem(chart.get("day_master"))
        or _extract_stem(chart.get("day_stem"))
        or _extract_stem(p_source.get("day", {}).get("stem") if isinstance(p_source.get("day"), dict) else None)
    )
    year_branch = _extract_branch(chart.get("year_branch")) or _extract_branch(
        p_source.get("year", {}).get("branch") if isinstance(p_source.get("year"), dict) else None
    )
    month_branch = _extract_branch(chart.get("month_branch")) or _extract_branch(
        p_source.get("month", {}).get("branch") if isinstance(p_source.get("month"), dict) else None
    )
    day_branch = _extract_branch(chart.get("day_branch")) or _extract_branch(
        p_source.get("day", {}).get("branch") if isinstance(p_source.get("day"), dict) else None
    )
    is_unknown_hour = bool(chart.get("unknown_hour"))
    hour_branch = None if is_unknown_hour else (
        _extract_branch(chart.get("hour_branch"))
        or _extract_branch(p_source.get("hour", {}).get("branch") if isinstance(p_source.get("hour"), dict) else None)
    )

    stem_index_map = {s["name"]: i for i, s in enumerate(STEMS)}
    branch_index_map = {b["name"]: i for i, b in enumerate(BRANCHES)}

    day_stem_idx = stem_index_map.get(dm_stem, -1) if dm_stem else -1
    day_branch_idx = branch_index_map.get(day_branch, -1) if day_branch else -1

    kong_wang_branches: list[str] = []
    if day_stem_idx >= 0 and day_branch_idx >= 0:
        day_60 = (day_stem_idx * 12 + day_branch_idx) % 60
        kong_wang_branches = _KONG_WANG_MAP.get(day_60 // 10, [])

    def _match_stars(b: str | None, pillar_key: str) -> StarList:
        if not b:
            return StarList()
        stars = StarList()

        # 1. Nobleman (天乙貴人)
        if dm_stem and b in _NOBLEMAN_BRANCHES.get(dm_stem, []):
            stars.append({**SHEN_SHA_METADATA["NOBLEMAN"], "pillar": pillar_key})
        # 2. Intelligence (文昌)
        if dm_stem and b == _INTELLIGENCE_BRANCH.get(dm_stem, ""):
            stars.append({**SHEN_SHA_METADATA["INTELLIGENCE"], "pillar": pillar_key})
        # 3. Prosperity (祿神)
        if dm_stem and b == _PROSPERITY_BRANCH.get(dm_stem, ""):
            stars.append({**SHEN_SHA_METADATA["PROSPERITY"], "pillar": pillar_key})
        # 4. Yang Ren (羊刃)
        if dm_stem and b == _YANG_REN_BRANCH.get(dm_stem, ""):
            stars.append({**SHEN_SHA_METADATA["YANG_REN"], "pillar": pillar_key})
        # 5. Peach Blossom (桃花)
        if year_branch and b == _PEACH_BLOSSOM.get(year_branch, ""):
            stars.append({**SHEN_SHA_METADATA["PEACH_BLOSSOM"], "pillar": pillar_key})
        # 6. General Star (將星)
        if (day_branch and b == _GENERAL_STAR.get(day_branch, "")) or (year_branch and b == _GENERAL_STAR.get(year_branch, "")):
            stars.append({**SHEN_SHA_METADATA["GENERAL"], "pillar": pillar_key})
        # 7. Talent (華蓋)
        if (day_branch and b == _TALENT_STAR.get(day_branch, "")) or (year_branch and b == _TALENT_STAR.get(year_branch, "")):
            stars.append({**SHEN_SHA_METADATA["TALENT"], "pillar": pillar_key})
        # 8. Travelling Horse (驛馬)
        if day_branch and b == _TRAVELLING_HORSE.get(day_branch, ""):
            stars.append({**SHEN_SHA_METADATA["TRAVELLING_HORSE"], "pillar": pillar_key})
        # 9. Kong Wang (空亡)
        if b in kong_wang_branches:
            stars.append({**SHEN_SHA_METADATA["KONG_WANG"], "pillar": pillar_key})

        return stars

    pillars = {
        "year": _match_stars(year_branch, "year"),
        "month": _match_stars(month_branch, "month"),
        "day": _match_stars(day_branch, "day"),
        "hour": _match_stars(hour_branch, "hour"),
    }

    active_stars = StarList([
        *pillars["year"],
        *pillars["month"],
        *pillars["day"],
        *pillars["hour"],
    ])

    return {
        "pillars": pillars,
        "active_stars": active_stars,
    }

