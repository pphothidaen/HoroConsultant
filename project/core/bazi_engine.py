"""
bazi_engine.py — BaZi (四柱命理) Computation Engine v2
======================================================
Computes the Four Pillars of Destiny from a True Solar Time datetime,
returning a fully-structured JSON with all analysis needed to replicate
the fengshuix.com BaZi Chart display:
  • Year / Month / Day / Hour pillars (Heavenly Stem + Earthly Branch)
  • Hidden Stems (藏干) with weights
  • Ten Gods (十神) for every stem in the chart
  • Pillar Phase (十二長生) for each pillar
  • Da Yun (大運) 10-year luck cycles — Ravi formula
  • Annual Luck sub-cycles per Da Yun period
  • Ming Gua (命卦) trigram calculation
  • 5 Structures / 10 Profiles proportions
  • Symbolic Stars (天乙貴人、文昌 etc.)
  • General Stars (將星、驛馬 etc.)
  • Heavenly & Earthly Stars per pillar
  • Day Master Strength (强弱) assessment
  • Favorable / Unfavorable Elements
  • Five Elements strength scores with seasonal multipliers
  • Probabilistic Scenario Matrix for Unknown Birth Hour

Rules implemented
-----------------
  Year  Pillar : Lichun (立春) boundary approx Feb 4
  Month Pillar : Solar month boundaries + Five Tigers (五虎遁)
  Day   Pillar : Julian Day Number modular formula
  Hour  Pillar : Double-hour branches + Five Rats (五鼠遁)
  Da Yun       : Ravi formula — counts to nearest Solar Term div 3 = start age
  Ming Gua     : Male=(10-digitsum)%9, Female=(5+digitsum)%9

Reference: He Luo Li Shu classical BaZi methodology + fengshuix.com Ravi formula
"""

from __future__ import annotations

from datetime import datetime, date
from functools import lru_cache
from typing import Any

from project.core.base_engine import (
    AbstractAstrologyEngine,
    ElementScores,
    EngineChartResult,
)
from project.core.fast_math import (
    cached_julian_day,
    numpy_element_scores,
    numpy_probabilistic_matrix,
)
from project.core.solar_time import SolarTimeResult, calculate_true_solar_time

# ============================================================
# Lookup Tables
# ============================================================

STEMS: list[dict[str, str]] = [
    {"name": "甲", "pinyin": "Jiǎ",  "element": "Wood",  "polarity": "Yang"},
    {"name": "乙", "pinyin": "Yǐ",   "element": "Wood",  "polarity": "Yin"},
    {"name": "丙", "pinyin": "Bǐng", "element": "Fire",  "polarity": "Yang"},
    {"name": "丁", "pinyin": "Dīng", "element": "Fire",  "polarity": "Yin"},
    {"name": "戊", "pinyin": "Wù",   "element": "Earth", "polarity": "Yang"},
    {"name": "己", "pinyin": "Jǐ",   "element": "Earth", "polarity": "Yin"},
    {"name": "庚", "pinyin": "Gēng", "element": "Metal", "polarity": "Yang"},
    {"name": "辛", "pinyin": "Xīn",  "element": "Metal", "polarity": "Yin"},
    {"name": "壬", "pinyin": "Rén",  "element": "Water", "polarity": "Yang"},
    {"name": "癸", "pinyin": "Guǐ",  "element": "Water", "polarity": "Yin"},
]

BRANCHES: list[dict] = [
    {"name": "子", "pinyin": "Zǐ",    "animal": "Rat",     "element": "Water", "polarity": "Yang", "hour_start": 23},
    {"name": "丑", "pinyin": "Chǒu",  "animal": "Ox",      "element": "Earth", "polarity": "Yin",  "hour_start": 1},
    {"name": "寅", "pinyin": "Yín",   "animal": "Tiger",   "element": "Wood",  "polarity": "Yang", "hour_start": 3},
    {"name": "卯", "pinyin": "Mǎo",   "animal": "Rabbit",  "element": "Wood",  "polarity": "Yin",  "hour_start": 5},
    {"name": "辰", "pinyin": "Chén",  "animal": "Dragon",  "element": "Earth", "polarity": "Yang", "hour_start": 7},
    {"name": "巳", "pinyin": "Sì",    "animal": "Snake",   "element": "Fire",  "polarity": "Yin",  "hour_start": 9},
    {"name": "午", "pinyin": "Wǔ",    "animal": "Horse",   "element": "Fire",  "polarity": "Yang", "hour_start": 11},
    {"name": "未", "pinyin": "Wèi",   "animal": "Goat",    "element": "Earth", "polarity": "Yin",  "hour_start": 13},
    {"name": "申", "pinyin": "Shēn",  "animal": "Monkey",  "element": "Metal", "polarity": "Yang", "hour_start": 15},
    {"name": "酉", "pinyin": "Yǒu",   "animal": "Rooster", "element": "Metal", "polarity": "Yin",  "hour_start": 17},
    {"name": "戌", "pinyin": "Xū",    "animal": "Dog",     "element": "Earth", "polarity": "Yang", "hour_start": 19},
    {"name": "亥", "pinyin": "Hài",   "animal": "Pig",     "element": "Water", "polarity": "Yin",  "hour_start": 21},
]

HIDDEN_STEMS: dict[str, list[tuple[str, float]]] = {
    "子": [("癸", 1.00)],
    "丑": [("己", 0.60), ("癸", 0.30), ("辛", 0.10)],
    "寅": [("甲", 0.60), ("丙", 0.30), ("戊", 0.10)],
    "卯": [("乙", 1.00)],
    "辰": [("戊", 0.60), ("乙", 0.30), ("癸", 0.10)],
    "巳": [("丙", 0.60), ("戊", 0.30), ("庚", 0.10)],
    "午": [("丁", 0.70), ("己", 0.30)],
    "未": [("己", 0.60), ("丁", 0.30), ("乙", 0.10)],
    "申": [("庚", 0.60), ("壬", 0.30), ("戊", 0.10)],
    "酉": [("辛", 1.00)],
    "戌": [("戊", 0.60), ("辛", 0.30), ("丁", 0.10)],
    "亥": [("壬", 0.70), ("甲", 0.30)],
}

STEM_ELEMENT:   dict[str, str] = {s["name"]: s["element"]  for s in STEMS}
STEM_POLARITY:  dict[str, str] = {s["name"]: s["polarity"] for s in STEMS}
STEM_INDEX:     dict[str, int] = {s["name"]: i             for i, s in enumerate(STEMS)}
BRANCH_INDEX:   dict[str, int] = {b["name"]: i             for i, b in enumerate(BRANCHES)}
BRANCH_ELEMENT: dict[str, str] = {b["name"]: b["element"]  for b in BRANCHES}

FIVE_ELEMENTS = ["Wood", "Fire", "Earth", "Metal", "Water"]

SEASONAL_MULT: dict[str, dict[str, float]] = {
    "Wood":  {"Wood": 1.5, "Fire": 1.2, "Earth": 0.8, "Metal": 0.6, "Water": 1.1},
    "Fire":  {"Fire": 1.5, "Earth": 1.2, "Metal": 0.7, "Water": 0.6, "Wood": 1.1},
    "Earth": {"Earth": 1.5, "Metal": 1.2, "Water": 0.7, "Wood": 0.8, "Fire": 1.1},
    "Metal": {"Metal": 1.5, "Water": 1.2, "Wood": 0.7, "Fire": 0.6, "Earth": 1.1},
    "Water": {"Water": 1.5, "Wood": 1.2, "Fire": 0.6, "Earth": 0.7, "Metal": 1.1},
}

# ============================================================
# Five Element Cycles
# ============================================================

_GENERATES:     dict[str, str] = {"Wood": "Fire", "Fire": "Earth", "Earth": "Metal", "Metal": "Water", "Water": "Wood"}
_CONTROLS:      dict[str, str] = {"Wood": "Earth", "Fire": "Metal", "Earth": "Water", "Metal": "Wood", "Water": "Fire"}
_CONTROLLED_BY: dict[str, str] = {v: k for k, v in _CONTROLS.items()}
_GENERATED_BY:  dict[str, str] = {v: k for k, v in _GENERATES.items()}

# ============================================================
# Ten Gods (十神)
# ============================================================

TEN_GOD_INFO: dict[str, dict[str, str]] = {
    "FR": {"zh": "比肩", "en": "Friend",           "structure": "Companion"},
    "RW": {"zh": "劫財", "en": "Rob Wealth",        "structure": "Companion"},
    "EG": {"zh": "食神", "en": "Eating God",        "structure": "Output"},
    "HO": {"zh": "傷官", "en": "Hurting Officer",   "structure": "Output"},
    "DW": {"zh": "正財", "en": "Direct Wealth",     "structure": "Wealth"},
    "IW": {"zh": "偏財", "en": "Indirect Wealth",   "structure": "Wealth"},
    "DO": {"zh": "正官", "en": "Direct Officer",    "structure": "Influence"},
    "7K": {"zh": "七殺", "en": "Seven Killings",    "structure": "Influence"},
    "DR": {"zh": "正印", "en": "Direct Resource",   "structure": "Resource"},
    "IR": {"zh": "偏印", "en": "Indirect Resource", "structure": "Resource"},
    "DM": {"zh": "日主", "en": "Day Master",        "structure": "Companion"},
}


TENUN_DAYUN_FORMULAS = {"ravi", "traditional", "taiwan"}


def ten_god(dm_stem: str, other_stem: str, formula: str = "ravi") -> str:
    """Compute Ten God relationship between Day Master stem and another stem.

    Parameters
    ----------
    dm_stem    : Day Master Heavenly Stem
    other_stem : Target Heavenly Stem
    formula    : Reserved for parity with UI selectors (kept default to Ravi behavior).
    """
    formula = (formula or "ravi").lower()
    if formula not in TENUN_DAYUN_FORMULAS:
        formula = "ravi"
    if dm_stem == other_stem:
        return "FR"
    dm_elem  = STEM_ELEMENT[dm_stem]
    dm_pol   = STEM_POLARITY[dm_stem]
    oth_elem = STEM_ELEMENT[other_stem]
    same_pol = (dm_pol == STEM_POLARITY[other_stem])

    if dm_elem == oth_elem:
        return "FR" if same_pol else "RW"
    if _GENERATES[dm_elem] == oth_elem:
        return "EG" if same_pol else "HO"
    if _CONTROLS[dm_elem] == oth_elem:
        # Fengshuix-style polarity convention for this implementation keeps
        # "same polarity" as indirect wealth / "opposite polarity" as direct wealth.
        return "IW" if same_pol else "DW"
    if _GENERATES[oth_elem] == dm_elem:
        return "IR" if same_pol else "DR"
    if _CONTROLS[oth_elem] == dm_elem:
        # ...and the mirrored rule for official officer / seven-kill relationship.
        return "7K" if same_pol else "DO"
    return "FR"


def _dayun_direction(formula: str, year_stem: str, month_stem: str, gender: str) -> bool:
    """Resolve Da Yun direction.

    Returns True for forward, False for backward.
    """
    formula = (formula or "ravi").lower()
    is_male = gender.lower() in ("male", "m")
    if formula == "taiwan":
        direction_polarity = STEM_POLARITY[month_stem]
    else:
        direction_polarity = STEM_POLARITY[year_stem]
    return (is_male and direction_polarity == "Yang") or (not is_male and direction_polarity == "Yin")


# ============================================================
# Pillar Phase — 十二長生
# ============================================================

PILLAR_PHASES:    list[str] = ["Chang Sheng", "Mu Yu",  "Guan Dai", "Lin Guan", "Di Wang", "Shuai", "Bing", "Si", "Mu", "Jue", "Tai", "Yang"]
PILLAR_PHASES_ZH: list[str] = ["長生",        "沐浴",    "冠帶",     "臨官",     "帝旺",    "衰",   "病",   "死",  "墓",  "絕",   "胎",  "養"]

_CHANG_SHENG_BRANCH: dict[tuple[str, str], int] = {
    ("Wood",  "Yang"): 11, ("Wood",  "Yin"): 6,
    ("Fire",  "Yang"): 2,  ("Fire",  "Yin"): 9,
    ("Earth", "Yang"): 2,  ("Earth", "Yin"): 9,
    ("Metal", "Yang"): 5,  ("Metal", "Yin"): 0,
    ("Water", "Yang"): 8,  ("Water", "Yin"): 3,
}


def pillar_phase(dm_stem: str, branch_char: str) -> dict[str, Any]:
    """Compute 十二長生 phase for given Day Master stem and a branch."""
    dm_elem  = STEM_ELEMENT[dm_stem]
    dm_pol   = STEM_POLARITY[dm_stem]
    b_idx    = BRANCH_INDEX[branch_char]
    cs_start = _CHANG_SHENG_BRANCH[(dm_elem, dm_pol)]
    phase_idx = (b_idx - cs_start) % 12 if dm_pol == "Yang" else (cs_start - b_idx) % 12
    return {
        "phase":     PILLAR_PHASES[phase_idx],
        "phase_zh":  PILLAR_PHASES_ZH[phase_idx],
        "phase_idx": phase_idx,
    }


# ============================================================
# Solar Term dates for Da Yun
# ============================================================

_SOLAR_TERMS_APPROX: list[tuple[int, int]] = [
    (1, 6), (2, 4), (3, 6), (4, 5), (5, 6), (6, 6),
    (7, 7), (8, 7), (9, 8), (10, 8), (11, 7), (12, 7),
]


def _nearest_solar_term_date(birth_date: date, forward: bool) -> date:
    year = birth_date.year
    candidates: list[date] = []
    for y in [year - 1, year, year + 1]:
        for m, d in _SOLAR_TERMS_APPROX:
            try:
                candidates.append(date(y, m, d))
            except ValueError:
                pass
    candidates.sort()
    if forward:
        for c in candidates:
            if c > birth_date:
                return c
        return candidates[-1]
    else:
        for c in reversed(candidates):
            if c < birth_date:
                return c
        return candidates[0]


# ============================================================
# Da Yun (大運) — Ravi Formula
# ============================================================

def compute_dayun(
    birth_dt:     datetime,
    year_stem:    str,
    month_stem:   str,
    month_branch: str,
    gender:       str = "male",
    formula:      str = "ravi",
    max_cycles:   int = 12,
) -> dict[str, Any]:
    """Compute Da Yun 10-year luck cycles."""
    formula = (formula or "ravi").lower()
    forward = _dayun_direction(formula, year_stem=year_stem, month_stem=month_stem, gender=gender)

    birth_date = birth_dt.date()
    term_date  = _nearest_solar_term_date(birth_date, forward)
    delta_days = abs((term_date - birth_date).days)

    if formula == "taiwan":
        start_years  = (delta_days + 1) // 3
    else:
        start_years  = delta_days // 3
    start_months = (delta_days % 3) * 4

    m_stem_idx   = STEM_INDEX[month_stem]
    m_branch_idx = BRANCH_INDEX[month_branch]

    cycles: list[dict] = []
    for i in range(1, max_cycles + 1):
        if forward:
            s_idx = (m_stem_idx   + i) % 10
            b_idx = (m_branch_idx + i) % 12
        else:
            s_idx = (m_stem_idx   - i) % 10
            b_idx = (m_branch_idx - i) % 12

        cycle_age  = start_years + (i - 1) * 10
        cycle_year = birth_dt.year + cycle_age
        s = STEMS[s_idx]
        b = BRANCHES[b_idx]

        cycles.append({
            "cycle_num":     i,
            "age_start":     cycle_age,
            "age_end":       cycle_age + 9,
            "year_start":    cycle_year,
            "year_end":      cycle_year + 9,
            "stem":          s["name"],
            "stem_pinyin":   s["pinyin"],
            "stem_element":  s["element"],
            "stem_polarity": s["polarity"],
            "branch":        b["name"],
            "branch_pinyin": b["pinyin"],
            "branch_animal": b["animal"],
            "branch_element":b["element"],
            "stem_idx":      s_idx,
            "branch_idx":    b_idx,
            "hidden_stems":  [{"stem": hs, "element": STEM_ELEMENT[hs], "weight": w} for hs, w in HIDDEN_STEMS[b["name"]]],
        })

    pre_cycle = {
        "cycle_num": 0,
        "label": "Pre Da Yun",
        "age_start": 0,
        "age_end": max(start_years - 1, 0),
        "year_start": birth_dt.year,
        "year_end": birth_dt.year + max(start_years - 1, 0),
    }

    return {
        "direction":        "forward" if forward else "backward",
        "start_age_years":  start_years,
        "start_age_months": start_months,
        "term_date":        term_date.isoformat(),
        "delta_days":       delta_days,
        "formula":          formula,
        "pre_cycle":        pre_cycle,
        "cycles":           cycles,
    }


def compute_annual_luck(birth_year: int, dayun_cycles: list[dict], max_age: int = 120) -> list[dict[str, Any]]:
    """Compute annual luck (流年) for each year from age 1 to max_age."""
    annual: list[dict] = []
    for age in range(1, max_age + 1):
        year_ce = birth_year + age - 1
        offset  = (year_ce - 1984) % 60
        s_idx   = offset % 10
        b_idx   = offset % 12
        s = STEMS[s_idx]
        b = BRANCHES[b_idx]

        dayun_num = None
        for cyc in dayun_cycles:
            if cyc["age_start"] <= age <= cyc["age_end"]:
                dayun_num = cyc["cycle_num"]
                break

        annual.append({
            "age":           age,
            "year_ce":       year_ce,
            "stem":          s["name"],
            "stem_pinyin":   s["pinyin"],
            "stem_element":  s["element"],
            "stem_polarity": s["polarity"],
            "branch":        b["name"],
            "branch_pinyin": b["pinyin"],
            "branch_animal": b["animal"],
            "branch_element":b["element"],
            "stem_idx":      s_idx,
            "branch_idx":    b_idx,
            "dayun_cycle":   dayun_num,
        })
    return annual


# ============================================================
# Ming Gua (命卦)
# ============================================================

_KUA_INFO: dict[int, dict[str, str]] = {
    1: {"trigram": "坎", "name": "Kan",  "direction": "NORTH",     "element": "Water"},
    2: {"trigram": "坤", "name": "Kun",  "direction": "SOUTHWEST", "element": "Earth"},
    3: {"trigram": "震", "name": "Zhen", "direction": "EAST",      "element": "Wood"},
    4: {"trigram": "巽", "name": "Xun",  "direction": "SOUTHEAST", "element": "Wood"},
    5: {"trigram": "中", "name": "Zhong","direction": "CENTER",     "element": "Earth"},
    6: {"trigram": "乾", "name": "Qian", "direction": "NORTHWEST", "element": "Metal"},
    7: {"trigram": "兌", "name": "Dui",  "direction": "WEST",      "element": "Metal"},
    8: {"trigram": "艮", "name": "Gen",  "direction": "NORTHEAST", "element": "Earth"},
    9: {"trigram": "離", "name": "Li",   "direction": "SOUTH",     "element": "Fire"},
}


def compute_ming_gua(birth_year: int, gender: str) -> dict[str, Any]:
    """Compute Ming Gua (命卦) Kua number."""
    yr2  = birth_year % 100
    dsum = (yr2 // 10) + (yr2 % 10)
    while dsum > 9:
        dsum = sum(int(d) for d in str(dsum))

    is_male = gender.lower() in ("male", "m")
    kua = ((10 - dsum) % 9) if is_male else ((5 + dsum) % 9)
    if kua == 0:
        kua = 9

    effective_kua = 2 if (kua == 5 and is_male) else (8 if (kua == 5 and not is_male) else kua)
    info = _KUA_INFO[effective_kua]
    return {
        "kua_number":    kua,
        "effective_kua": effective_kua,
        "trigram_zh":    info["trigram"],
        "trigram_name":  info["name"],
        "direction":     info["direction"],
        "element":       info["element"],
    }


# ============================================================
# 10 Profiles / 5 Structures
# ============================================================

TEN_GOD_HIDDEN_WEIGHT = 1.25


def compute_ten_profiles(dm_stem: str, pillars: dict) -> dict[str, Any]:
    """Count weighted Ten God proportions across all stems in the 4-pillar chart."""
    weights: dict[str, float] = {k: 0.0 for k in TEN_GOD_INFO if k != "DM"}

    for pk in ("year", "month", "day", "hour"):
        p = pillars.get(pk)
        if not p:
            continue
        sc   = p["stem"]["char"]
        code = "FR" if sc == dm_stem else ten_god(dm_stem, sc)
        stem_weight = 1.2 if (pk == "day" and sc == dm_stem) else 1.0
        weights[code] = weights.get(code, 0.0) + stem_weight

        for hs in p.get("hidden_stems", []):
            hsc   = hs["stem"]
            base_w = hs.get("weight", 1.0)
            if pk == "month":
                hs_w = base_w * 2.0
            elif pk == "year" and p["branch"]["char"] in ("丑", "辰", "未", "戌"):
                if base_w >= 0.5:
                    hs_w = 1.0
                elif base_w >= 0.2:
                    hs_w = 0.6
                else:
                    hs_w = 0.1
            else:
                hs_w = base_w
            code2 = "FR" if hsc == dm_stem else ten_god(dm_stem, hsc)
            weights[code2] = weights.get(code2, 0.0) + hs_w

    total = 9.0
    ten_profiles = {
        code: {
            "code": code, "zh": TEN_GOD_INFO[code]["zh"], "en": TEN_GOD_INFO[code]["en"],
            "structure": TEN_GOD_INFO[code]["structure"],
            "stem_char": next((s["name"] for s in STEMS if ten_god(dm_stem, s["name"]) == code or (code == "FR" and s["name"] == dm_stem)), ""),
            "weight": round(w, 4), "percentage": round(w / total * 100, 2),
        }
        for code, w in weights.items()
    }

    struct_w: dict[str, float] = {"Companion": 0.0, "Output": 0.0, "Wealth": 0.0, "Influence": 0.0, "Resource": 0.0}
    for code, data in ten_profiles.items():
        s = data["structure"]
        if s in struct_w:
            struct_w[s] += data["weight"]

    dm_elem = STEM_ELEMENT[dm_stem]
    struct_elem_map = {
        "Companion": dm_elem, "Output": _GENERATES[dm_elem], "Wealth": _CONTROLS[dm_elem],
        "Influence": _CONTROLLED_BY[dm_elem], "Resource": _GENERATED_BY[dm_elem],
    }
    five_structures = {
        sname: {
            "structure": sname, "element": struct_elem_map.get(sname, ""),
            "weight": round(sw, 4), "percentage": round(sw / total * 100, 2),
        }
        for sname, sw in struct_w.items()
    }
    return {"ten_profiles": ten_profiles, "five_structures": five_structures}


# ============================================================
# Day Master Strength
# ============================================================

def assess_daymaster_strength(dm_stem: str, month_branch: str, elem_scores: dict) -> str:
    dm_elem    = STEM_ELEMENT[dm_stem]
    dm_pct     = elem_scores.get("percentages", {}).get(dm_elem, 0.0)
    season_elem = BRANCH_ELEMENT.get(month_branch, "")
    in_season  = (season_elem == dm_elem or _GENERATES.get(season_elem) == dm_elem)
    return "STRONG" if (dm_pct >= 25.0 or in_season) else "WEAK"


def compute_favorable_elements(dm_stem: str, strength: str) -> dict[str, list[str]]:
    dm_elem = STEM_ELEMENT[dm_stem]
    if strength == "WEAK":
        favorable   = [_GENERATED_BY[dm_elem], _CONTROLLED_BY[dm_elem], dm_elem]
        unfavorable = [_CONTROLS[dm_elem], _GENERATES[dm_elem]]
    else:
        favorable   = [_GENERATES[dm_elem], _CONTROLS[dm_elem], _CONTROLLED_BY[dm_elem]]
        unfavorable = [_GENERATED_BY[dm_elem], dm_elem]

    def dedup(lst: list[str]) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for e in lst:
            if e not in seen:
                seen.add(e)
                out.append(e)
        return out

    return {"favorable": dedup(favorable), "unfavorable": dedup(unfavorable)}


# ============================================================
# Symbolic Stars
# ============================================================

_NOBLEMAN_BRANCHES: dict[str, list[str]] = {
    "甲": ["丑", "未"], "戊": ["丑", "未"],
    "乙": ["子", "申"], "己": ["子", "申"],
    "丙": ["亥", "酉"], "庚": ["亥", "酉"],
    "丁": ["亥", "酉"], "辛": ["寅", "午"],
    "壬": ["卯", "巳"], "癸": ["卯", "巳"],
}
_INTELLIGENCE_BRANCH: dict[str, str] = {
    "甲": "巳", "乙": "午", "丙": "申", "丁": "酉",
    "戊": "申", "己": "酉", "庚": "亥", "辛": "子",
    "壬": "寅", "癸": "卯",
}
_PROSPERITY_BRANCH: dict[str, str] = {
    "甲": "寅", "乙": "卯", "丙": "巳", "丁": "午",
    "戊": "巳", "己": "午", "庚": "申", "辛": "酉",
    "壬": "亥", "癸": "子",
}
_PEACH_BLOSSOM: dict[str, str] = {
    "子": "酉", "丑": "午", "寅": "卯", "卯": "子",
    "辰": "酉", "巳": "午", "午": "卯", "未": "子",
    "申": "酉", "酉": "午", "戌": "卯", "亥": "子",
}
_YANG_REN_BRANCH: dict[str, str] = {
    "甲": "卯", "乙": "辰", "丙": "午", "丁": "未",
    "戊": "午", "己": "未", "庚": "酉", "辛": "戌",
    "壬": "子", "癸": "丑",
}
_KONG_WANG_MAP: dict[int, list[str]] = {
    0: ["戌", "亥"], 1: ["申", "酉"], 2: ["午", "未"],
    3: ["辰", "巳"], 4: ["寅", "卯"], 5: ["子", "丑"],
}


def compute_symbolic_stars(day_stem: str, year_branch: str, day_stem_idx: int, day_branch_idx: int) -> dict[str, Any]:
    day_60       = (day_stem_idx * 12 + day_branch_idx) % 60
    kong_branches = _KONG_WANG_MAP.get(day_60 // 10, [])
    return {
        "Kong Wang":     {"branches": kong_branches,                                                                          "note": "空亡"},
        "Nobleman":      {"branches": _NOBLEMAN_BRANCHES.get(day_stem, []),                                                   "note": "天乙貴人"},
        "Tian Yi Noble": {"branches": _NOBLEMAN_BRANCHES.get(day_stem, []),                                                   "note": "天乙貴人"},
        "Intelligence":  {"branches": [b for b in [_INTELLIGENCE_BRANCH.get(day_stem, "")] if b],                            "note": "文昌"},
        "Sword":         {"branches": [BRANCHES[(BRANCH_INDEX.get(year_branch, 0) + 6) % 12]["name"]],                       "note": "劫煞"},
        "Prosperity":    {"branches": [b for b in [_PROSPERITY_BRANCH.get(day_stem, "")] if b],                              "note": "祿神"},
        "Fu Xing":       {"branches": ["亥"],                                                                                 "note": "福星"},
        "Peach Blossom": {"branches": [b for b in [_PEACH_BLOSSOM.get(year_branch, "")] if b],                               "note": "桃花"},
        "Tao Hua":       {"branches": [b for b in [_PEACH_BLOSSOM.get(year_branch, "")] if b],                               "note": "桃花"},
        "Yang Ren":      {"branches": [b for b in [_YANG_REN_BRANCH.get(day_stem, "")] if b],                                "note": "羊刃"},
    }


# ============================================================
# General Stars
# ============================================================

_GENERAL_STAR:     dict[str, str] = {"子": "子", "午": "子", "卯": "子", "酉": "子", "寅": "午", "申": "午", "巳": "午", "亥": "午", "辰": "酉", "戌": "酉", "丑": "酉", "未": "酉"}
_TALENT_STAR:      dict[str, str] = {"子": "辰", "丑": "丑", "寅": "戌", "卯": "未", "辰": "辰", "巳": "丑", "午": "戌", "未": "未", "申": "辰", "酉": "丑", "戌": "戌", "亥": "未"}
_TRAVELLING_HORSE: dict[str, str] = {"子": "寅", "丑": "亥", "寅": "申", "卯": "巳", "辰": "寅", "巳": "亥", "午": "申", "未": "巳", "申": "寅", "酉": "亥", "戌": "申", "亥": "巳"}
_ROBBING_STAR:     dict[str, str] = {"子": "巳", "丑": "寅", "寅": "亥", "卯": "申", "辰": "巳", "巳": "寅", "午": "亥", "未": "申", "申": "巳", "酉": "寅", "戌": "亥", "亥": "申"}
_DEATH_STAR:       dict[str, str] = {"子": "申", "丑": "巳", "寅": "寅", "卯": "亥", "辰": "申", "巳": "巳", "午": "寅", "未": "亥", "申": "申", "酉": "巳", "戌": "寅", "亥": "亥"}
_SOLITARY_STAR:    dict[str, str] = {"子": "寅", "丑": "寅", "寅": "巳", "卯": "巳", "辰": "巳", "巳": "申", "午": "申", "未": "申", "申": "亥", "酉": "亥", "戌": "亥", "亥": "寅"}
_LONESOME_STAR:    dict[str, str] = {"子": "戌", "丑": "戌", "寅": "丑", "卯": "丑", "辰": "丑", "巳": "辰", "午": "辰", "未": "辰", "申": "未", "酉": "未", "戌": "未", "亥": "戌"}


def compute_general_stars(day_branch: str, year_branch: str) -> dict[str, Any]:
    return {
        "General":          {"day": _GENERAL_STAR.get(day_branch, ""),     "year": _GENERAL_STAR.get(year_branch, ""),     "note": "將星"},
        "Talent":           {"day": _TALENT_STAR.get(day_branch, ""),      "year": _TALENT_STAR.get(year_branch, ""),      "note": "華蓋"},
        "Travelling Horse": {"day": _TRAVELLING_HORSE.get(day_branch, ""), "year": _TRAVELLING_HORSE.get(year_branch, ""), "note": "驛馬"},
        "Robbing":          {"day": _ROBBING_STAR.get(day_branch, ""),     "year": _ROBBING_STAR.get(year_branch, ""),     "note": "劫煞"},
        "Death":            {"day": _DEATH_STAR.get(day_branch, ""),       "year": _DEATH_STAR.get(year_branch, ""),       "note": "亡神"},
        "Solitary":         {"day": _SOLITARY_STAR.get(day_branch, ""),    "year": _SOLITARY_STAR.get(year_branch, ""),    "note": "孤辰"},
        "Lonesome":         {"day": _LONESOME_STAR.get(day_branch, ""),    "year": _LONESOME_STAR.get(year_branch, ""),    "note": "寡宿"},
    }


def compute_pillar_stars(pillar_branch: str, day_stem: str, year_branch: str, day_branch: str) -> dict[str, Any]:
    """Compute Heavenly and Earthly stars for a single pillar."""
    heavenly: list[str] = []
    earthly:  list[str] = []
    if pillar_branch in _NOBLEMAN_BRANCHES.get(day_stem, []):
        heavenly.append("Nobleman")
    if pillar_branch == _INTELLIGENCE_BRANCH.get(day_stem, ""):
        heavenly.append("Intelligence")
    if pillar_branch == _PROSPERITY_BRANCH.get(day_stem, ""):
        heavenly.append("Prosperity")
    if pillar_branch == _YANG_REN_BRANCH.get(day_stem, ""):
        heavenly.append("Yang Ren")
    if pillar_branch == _PEACH_BLOSSOM.get(year_branch, ""):
        heavenly.append("Peach Blossom")
    if pillar_branch == _GENERAL_STAR.get(day_branch, ""):
        earthly.append("General Star")
    if pillar_branch == _TALENT_STAR.get(day_branch, ""):
        earthly.append("Talent Star")
    if pillar_branch == _TRAVELLING_HORSE.get(day_branch, ""):
        earthly.append("Travelling Horse")
    if pillar_branch == _ROBBING_STAR.get(day_branch, ""):
        earthly.append("Robbing Star")
    if pillar_branch == _DEATH_STAR.get(day_branch, ""):
        earthly.append("Death Star")
    if pillar_branch == _GENERAL_STAR.get(year_branch, "") and "General Star" not in earthly:
        earthly.append("General Star")
    if pillar_branch == _TALENT_STAR.get(year_branch, "") and "Talent Star" not in earthly:
        earthly.append("Talent Star")
    return {"heavenly": heavenly, "earthly": earthly}


# ============================================================
# Helper utilities
# ============================================================

def _stem_d(idx: int) -> dict[str, str]:
    return STEMS[idx % 10]


def _branch_d(idx: int) -> dict:
    return BRANCHES[idx % 12]


def _julian_day(dt: datetime) -> int:
    return cached_julian_day(dt.year, dt.month, dt.day)


# ============================================================
# Pillar Calculations (LRU Cached)
# ============================================================

@lru_cache(maxsize=4096)
def _year_stem_branch(year: int, month: int, day: int) -> tuple[int, int]:
    eff = year - (1 if (month < 2 or (month == 2 and day < 4)) else 0)
    return (eff - 4) % 10, (eff - 4) % 12


_SOLAR_MONTH_STARTS: list[tuple[int, int]] = [
    (1, 6), (2, 4), (3, 6), (4, 5), (5, 6), (6, 7),
    (7, 7), (8, 8), (9, 8), (10, 8), (11, 7), (12, 7),
]


@lru_cache(maxsize=2048)
def _month_branch_idx(month: int, day: int) -> int:
    for i in range(len(_SOLAR_MONTH_STARTS) - 1, -1, -1):
        sm, sd = _SOLAR_MONTH_STARTS[i]
        if month > sm or (month == sm and day >= sd):
            return (i + 1) % 12
    return 1


@lru_cache(maxsize=4096)
def _month_stem_branch(year_stem_idx: int, month: int, day: int) -> tuple[int, int]:
    m_branch   = _month_branch_idx(month, day)
    tiger_base = {0: 2, 1: 4, 2: 6, 3: 8, 4: 0}
    base       = tiger_base[year_stem_idx % 5]
    m_stem     = (base + (m_branch - 2) % 12) % 10
    return m_stem, m_branch


def _day_stem_branch(dt: datetime) -> tuple[int, int]:
    jdn = _julian_day(dt)
    return (jdn + 9) % 10, (jdn + 1) % 12


def _hour_branch_from_tst(tst_hour: int) -> int:
    if tst_hour == 23:
        return 0
    return (tst_hour + 1) // 2


def _hour_stem_branch(day_stem_idx: int, tst_hour: int) -> tuple[int, int]:
    h_branch = _hour_branch_from_tst(tst_hour)
    rat_base = {0: 0, 1: 2, 2: 4, 3: 6, 4: 8}
    h_stem   = (rat_base[day_stem_idx % 5] + h_branch) % 10
    return h_stem, h_branch


def _compute_element_scores(stem_indices: list[int], branch_indices: list[int], season_element: str) -> dict[str, Any]:
    return numpy_element_scores(stem_indices, branch_indices, season_element)


def _pillar_dict(stem_idx: int, branch_idx: int, label: str) -> dict[str, Any]:
    s = _stem_d(stem_idx)
    b = _branch_d(branch_idx)
    return {
        "label":  label,
        "stem":   {"char": s["name"], "pinyin": s["pinyin"], "element": s["element"], "polarity": s["polarity"]},
        "branch": {"char": b["name"], "pinyin": b["pinyin"], "animal": b["animal"], "element": b["element"], "polarity": b["polarity"], "hour_start": b["hour_start"]},
        "hidden_stems": [{"stem": hs, "element": STEM_ELEMENT[hs], "weight": w} for hs, w in HIDDEN_STEMS[b["name"]]],
    }


# ============================================================
# Main Engine
# ============================================================

class BaZiEngine(AbstractAstrologyEngine):
    """
    Deterministic BaZi computation engine v2 — fengshuix.com feature parity.
    """

    @property
    def engine_name(self) -> str:
        return "BaZi Engine"

    @property
    def system_type(self) -> str:
        return "ming_xue"

    def calculate(
        self,
        dt:               datetime,
        longitude:        float,
        utc_offset_hours: float,
        unknown_hour:     bool = False,
        gender:           str  = "male",
        name:             str  = "",
        surname:          str  = "",
        include_dayun:    bool = True,
        include_annual:   bool = True,
        dayun_max_cycles: int  = 12,
        annual_max_age:   int  = 120,
        dayun_formula:    str  = "ravi",
    ) -> EngineChartResult:
        """
        Compute complete BaZi chart.

        Parameters
        ----------
        dt               : Local clock datetime
        longitude        : Geographic longitude (deg, + east)
        utc_offset_hours : Timezone offset hours
        unknown_hour     : If True, generate Probabilistic Scenario Matrix
        gender           : "male" / "female" — affects Da Yun direction & Ming Gua
        dayun_formula    : One of "ravi", "traditional", "taiwan" for Da Yun direction/start-age style
        name / surname   : For display
        include_dayun    : Compute Da Yun cycles
        include_annual   : Compute Annual Luck sub-cycles
        dayun_max_cycles : Number of 10-yr cycles
        annual_max_age   : Max age for annual luck
        """
        # 1. True Solar Time
        tst: SolarTimeResult = calculate_true_solar_time(dt, longitude, utc_offset_hours)
        tst_dt = datetime.strptime(tst.tst_datetime, "%Y-%m-%d %H:%M:%S")

        # 2. Pillars
        ys, yb = _year_stem_branch(tst_dt.year, tst_dt.month, tst_dt.day)
        ms, mb = _month_stem_branch(ys, tst_dt.month, tst_dt.day)
        ds, db = _day_stem_branch(tst_dt)

        year_p  = _pillar_dict(ys, yb, "Year")
        month_p = _pillar_dict(ms, mb, "Month")
        day_p   = _pillar_dict(ds, db, "Day")

        season_element  = BRANCHES[mb % 12]["element"]
        dm_stem         = STEMS[ds % 10]["name"]

        day_master = {
            "stem":     dm_stem,
            "element":  STEMS[ds % 10]["element"],
            "polarity": STEMS[ds % 10]["polarity"],
            "pinyin":   STEMS[ds % 10]["pinyin"],
        }

        base_result = {
            "engine_version":  "1.0.0",
            "solar_time_info": tst.to_dict(),
            "day_master":      day_master,
            "person": {"name": name, "surname": surname, "gender": gender, "birth_datetime": dt.isoformat()},
        }

        # 3a. Deterministic (known hour)
        if not unknown_hour:
            hs, hb = _hour_stem_branch(ds, tst_dt.hour)
            hour_p = _pillar_dict(hs, hb, "Hour")

            elem_scores = _compute_element_scores([ys, ms, ds, hs], [yb, mb, db, hb], season_element)

            pillars = {"year": year_p, "month": month_p, "day": day_p, "hour": hour_p}

            # Annotate each pillar with Ten God, Phase, Stars
            for pk, p in pillars.items():
                sc = p["stem"]["char"]
                bc = p["branch"]["char"]
                p["ten_god"]      = "DM" if sc == dm_stem else ten_god(dm_stem, sc, formula="ravi")
                p["ten_god_info"] = TEN_GOD_INFO.get(p["ten_god"], {})
                for hs_item in p["hidden_stems"]:
                    hsc = hs_item["stem"]
                    hs_item["ten_god"] = "DM" if hsc == dm_stem else ten_god(dm_stem, hsc, formula="ravi")
                p["pillar_phase"] = pillar_phase(dm_stem, bc)
                p["stars"]        = compute_pillar_stars(bc, dm_stem, year_p["branch"]["char"], day_p["branch"]["char"])

            # Strength + Favorable
            strength       = assess_daymaster_strength(dm_stem, month_p["branch"]["char"], elem_scores)
            day_master["strength"] = strength
            favorable_info = compute_favorable_elements(dm_stem, strength)

            # Ming Gua
            ming_gua = compute_ming_gua(tst_dt.year, gender)

            # Profiles / Structures
            profiles = compute_ten_profiles(dm_stem, pillars)

            # Stars
            sym_stars = compute_symbolic_stars(dm_stem, year_p["branch"]["char"], ds, db)
            gen_stars = compute_general_stars(day_p["branch"]["char"], year_p["branch"]["char"])

            # Da Yun
            dayun_data  = None
            annual_data = None
            if include_dayun:
                dayun_data = compute_dayun(
                    birth_dt=dt, year_stem=year_p["stem"]["char"],
                    month_stem=month_p["stem"]["char"], month_branch=month_p["branch"]["char"],
                    gender=gender, formula=dayun_formula, max_cycles=dayun_max_cycles,
                )
                for cyc in dayun_data["cycles"]:
                    cyc["ten_god_stem"] = ten_god(dm_stem, cyc["stem"], formula="ravi")
                    cyc["pillar_phase"] = pillar_phase(dm_stem, cyc["branch"])
                    for hs_item in cyc["hidden_stems"]:
                        hs_item["ten_god"] = ten_god(dm_stem, hs_item["stem"], formula="ravi")

                if include_annual:
                    annual_data = compute_annual_luck(dt.year, dayun_data["cycles"], annual_max_age)
                    for ann in annual_data:
                        ann["ten_god_stem"] = ten_god(dm_stem, ann["stem"], formula="ravi")
                        ann["pillar_phase"] = pillar_phase(dm_stem, ann["branch"])

            res_dict = {
                **base_result,
                "pillars":             pillars,
                "five_elements":       elem_scores,
                "day_master_strength": strength,
                "favorable_elements":  favorable_info,
                "ming_gua":            ming_gua,
                "ten_profiles":        profiles["ten_profiles"],
                "five_structures":     profiles["five_structures"],
                "dayun_formula":       dayun_formula,
                "symbolic_stars":      sym_stars,
                "general_stars":       gen_stars,
                "dayun":               dayun_data,
                "annual_luck":         annual_data,
                "is_probabilistic":    False,
            }
            return EngineChartResult(
                engine_name   = self.engine_name,
                system_type   = self.system_type,
                chart_data    = res_dict,
                element_scores= ElementScores(**elem_scores) if isinstance(elem_scores, dict) else None,
            )

        # 3b. Probabilistic Scenario Matrix
        scenario_data = numpy_probabilistic_matrix(ys, yb, ms, mb, ds, db, season_element)
        ANIMAL_NAMES  = [b["animal"]    for b in BRANCHES]
        BRANCH_CHARS  = [b["name"]      for b in BRANCHES]
        BRANCH_PINYIN = [b["pinyin"]    for b in BRANCHES]
        BRANCH_HOURS  = [b["hour_start"] for b in BRANCHES]

        scenarios = []
        for sd in scenario_data:
            hb2 = sd["h_branch_idx"]
            hs2 = sd["h_stem_idx"]
            hour_pillar = _pillar_dict(hs2, hb2, "Hour")
            scenarios.append({
                "hour_branch":        BRANCH_CHARS[hb2],
                "hour_branch_pinyin": BRANCH_PINYIN[hb2],
                "animal":             ANIMAL_NAMES[hb2],
                "hour_window":        f"{BRANCH_HOURS[hb2]:02d}:00-{(BRANCH_HOURS[hb2]+2)%24:02d}:00",
                "probability_weight": sd["probability_weight"],
                "hour_pillar":        hour_pillar,
                "five_elements":      sd["five_elements"],
            })

        res_dict = {
            **base_result,
            "pillars": {"year": year_p, "month": month_p, "day": day_p, "hour": None},
            "is_probabilistic": True,
            "probabilistic_matrix": scenarios,
        }
        return EngineChartResult(engine_name=self.engine_name, system_type=self.system_type, chart_data=res_dict)


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="BaZi Four Pillars Engine v2")
    parser.add_argument("--dt",           required=True, help="YYYY-MM-DD HH:MM:SS")
    parser.add_argument("--longitude",    required=True, type=float)
    parser.add_argument("--utc",          required=True, type=float)
    parser.add_argument("--gender",       default="male")
    parser.add_argument("--name",         default="")
    parser.add_argument("--surname",      default="")
    parser.add_argument("--unknown-hour", action="store_true")
    args = parser.parse_args()

    engine = BaZiEngine()
    dt_obj = datetime.strptime(args.dt, "%Y-%m-%d %H:%M:%S")
    result = engine.calculate(
        dt=dt_obj, longitude=args.longitude, utc_offset_hours=args.utc,
        unknown_hour=args.unknown_hour, gender=args.gender,
        name=args.name, surname=args.surname,
    )
    print(json.dumps(result.chart_data, indent=2, ensure_ascii=False))
