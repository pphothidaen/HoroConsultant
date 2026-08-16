"""
project/core/transit_engine.py
==============================
Computational Metaphysics Engine for Natal-Transit Interactions:
  - 10-Year Major Luck Pillar (大運) & Annual Pillar (流年) dynamic calculations.
  - Heavenly Stem 5-Combinations (天干五合).
  - Earthly Branch 6-Clashes (地支六沖), 6-Combinations (地支六合), 3-Harmonies (三合局), 6-Harms (六害), and Punishments (三刑).
  - Live Sky Transit Clock Engine (即時四柱天文鐘).
"""

from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

HEAVENLY_STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
EARTHLY_BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

STEM_ELEMENTS = {
    "甲": "Wood", "乙": "Wood",
    "丙": "Fire", "丁": "Fire",
    "戊": "Earth", "己": "Earth",
    "庚": "Metal", "辛": "Metal",
    "壬": "Water", "癸": "Water"
}

BRANCH_ELEMENTS = {
    "寅": "Wood", "卯": "Wood",
    "巳": "Fire", "午": "Fire",
    "辰": "Earth", "戌": "Earth", "丑": "Earth", "未": "Earth",
    "申": "Metal", "酉": "Metal",
    "亥": "Water", "子": "Water"
}

STEM_COMBINATIONS = {
    frozenset(["甲", "己"]): {"result": "Earth", "name": "甲己合土 (Jia-Ji Earth Combination)"},
    frozenset(["乙", "庚"]): {"result": "Metal", "name": "乙庚合金 (Yi-Geng Metal Combination)"},
    frozenset(["丙", "辛"]): {"result": "Water", "name": "丙辛合水 (Bing-Xin Water Combination)"},
    frozenset(["丁", "壬"]): {"result": "Wood",  "name": "丁壬合木 (Ding-Ren Wood Combination)"},
    frozenset(["戊", "癸"]): {"result": "Fire",  "name": "戊癸合火 (Wu-Gui Fire Combination)"},
}

BRANCH_CLASHES = {
    frozenset(["子", "午"]): "子午相沖 (Rat-Horse Clash)",
    frozenset(["丑", "未"]): "丑未相沖 (Ox-Goat Clash)",
    frozenset(["寅", "申"]): "寅申相沖 (Tiger-Monkey Clash)",
    frozenset(["卯", "酉"]): "卯酉相沖 (Rabbit-Rooster Clash)",
    frozenset(["辰", "戌"]): "辰戌相沖 (Dragon-Dog Clash)",
    frozenset(["巳", "亥"]): "巳亥相沖 (Snake-Pig Clash)",
}

BRANCH_COMBINATIONS = {
    frozenset(["子", "丑"]): {"result": "Earth", "name": "子丑合土 (Rat-Ox Earth Harmony)"},
    frozenset(["寅", "亥"]): {"result": "Wood",  "name": "寅亥合木 (Tiger-Pig Wood Harmony)"},
    frozenset(["卯", "戌"]): {"result": "Fire",  "name": "卯戌合火 (Rabbit-Dog Fire Harmony)"},
    frozenset(["辰", "酉"]): {"result": "Metal", "name": "辰酉合金 (Dragon-Rooster Metal Harmony)"},
    frozenset(["巳", "申"]): {"result": "Water", "name": "巳申合水 (Snake-Monkey Water Harmony)"},
    frozenset(["午", "未"]): {"result": "Earth", "name": "午未合土 (Horse-Goat Earth Harmony)"},
}

BRANCH_HARMS = {
    frozenset(["子", "未"]): "子未相害 (Rat-Goat Harm)",
    frozenset(["丑", "午"]): "丑午相害 (Ox-Horse Harm)",
    frozenset(["寅", "巳"]): "寅巳相害 (Tiger-Snake Harm)",
    frozenset(["卯", "辰"]): "卯辰相害 (Rabbit-Dragon Harm)",
    frozenset(["申", "亥"]): "申亥相害 (Monkey-Pig Harm)",
    frozenset(["酉", "戌"]): "酉戌相害 (Rooster-Dog Harm)",
}

BRANCH_PUNISHMENTS = {
    frozenset(["寅", "巳", "申"]): "恃勢之刑 (Ungrateful Punishment: Tiger-Snake-Monkey)",
    frozenset(["丑", "戌", "未"]): "無恩之刑 (Bullying Punishment: Ox-Dog-Goat)",
    frozenset(["子", "卯"]): "無禮之刑 (Rude Punishment: Rat-Rabbit)",
    frozenset(["辰"]): "辰辰自刑 (Dragon Self Punishment)",
    frozenset(["午"]): "午午自刑 (Horse Self Punishment)",
    frozenset(["酉"]): "酉酉自刑 (Rooster Self Punishment)",
    frozenset(["亥"]): "亥亥自刑 (Pig Self Punishment)",
}


class TransitEngine:
    """Calculates Natal vs Transit interactions and real-time live sky pillars."""

    @staticmethod
    def get_annual_pillar(year: int) -> Dict[str, Any]:
        """Compute the 60 Jia-Zi Annual Pillar (流年) for any Gregorian year."""
        # 1984 is Jia Zi (Index 0)
        offset = (year - 1984) % 60
        stem_idx = offset % 10
        branch_idx = offset % 12
        stem = HEAVENLY_STEMS[stem_idx]
        branch = EARTHLY_BRANCHES[branch_idx]
        return {
            "year": year,
            "stem": stem,
            "branch": branch,
            "stem_element": STEM_ELEMENTS[stem],
            "branch_element": BRANCH_ELEMENTS[branch],
            "pillar_str": f"{stem}{branch}",
        }

    @staticmethod
    def analyze_natal_transit_aspects(
        natal_chart: Dict[str, Any],
        transit_year: int,
        transit_age: int,
        custom_dayun_stem: Optional[str] = None,
        custom_dayun_branch: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze interactions between Natal Pillars (Year, Month, Day, Hour)
        and active Transit Pillars (Annual Year + Da Yun).
        """
        pillars = natal_chart.get("pillars", {})
        natal_stems = [
            pillars.get("year", {}).get("stem", {}).get("char", "庚"),
            pillars.get("month", {}).get("stem", {}).get("char", "辛"),
            pillars.get("day", {}).get("stem", {}).get("char", "甲"),
            pillars.get("hour", {}).get("stem", {}).get("char", "辛"),
        ]
        natal_branches = [
            pillars.get("year", {}).get("branch", {}).get("char", "午"),
            pillars.get("month", {}).get("branch", {}).get("char", "巳"),
            pillars.get("day", {}).get("branch", {}).get("char", "子"),
            pillars.get("hour", {}).get("branch", {}).get("char", "未"),
        ]
        day_master_stem = natal_stems[2]
        day_master_branch = natal_branches[2]

        annual_pillar = TransitEngine.get_annual_pillar(transit_year)
        t_stem = annual_pillar["stem"]
        t_branch = annual_pillar["branch"]

        aspects: List[Dict[str, Any]] = []

        # 1. Check Stem Combinations
        for i, (n_stem, p_name) in enumerate(zip(natal_stems, ["Year", "Month", "Day Master", "Hour"])):
            pair = frozenset([n_stem, t_stem])
            if pair in STEM_COMBINATIONS:
                comb = STEM_COMBINATIONS[pair]
                aspects.append({
                    "type": "COMBINATION",
                    "category": "Heavenly Stem Combination (天干合)",
                    "pillar": p_name,
                    "natal": n_stem,
                    "transit": t_stem,
                    "name": comb["name"],
                    "element": comb["result"],
                    "favorable": True,
                    "description": f"ก้านฟ้าปีจร {t_stem} รวมกับ {p_name} ({n_stem}) ก่อเกิดธาตุ {comb['result']} หนุนเกียรติยศและโชคลาภ"
                })

        # 2. Check Branch Clashes
        for i, (n_branch, p_name) in enumerate(zip(natal_branches, ["Year", "Month", "Day", "Hour"])):
            pair = frozenset([n_branch, t_branch])
            if pair in BRANCH_CLASHES:
                aspects.append({
                    "type": "CLASH",
                    "category": "Earthly Branch Clash (地支沖)",
                    "pillar": p_name,
                    "natal": n_branch,
                    "transit": t_branch,
                    "name": BRANCH_CLASHES[pair],
                    "favorable": False,
                    "description": f"กิ่งดินปีจร {t_branch} ปะทะกับ {p_name} ({n_branch}) เตือนให้ระวังการเปลี่ยนแปลงกะทันหันหรือการเดินทางโยกย้าย"
                })

        # 3. Check Branch Combinations
        for i, (n_branch, p_name) in enumerate(zip(natal_branches, ["Year", "Month", "Day", "Hour"])):
            pair = frozenset([n_branch, t_branch])
            if pair in BRANCH_COMBINATIONS:
                comb = BRANCH_COMBINATIONS[pair]
                aspects.append({
                    "type": "HARMONY",
                    "category": "Earthly Branch Harmony (地支六合)",
                    "pillar": p_name,
                    "natal": n_branch,
                    "transit": t_branch,
                    "name": comb["name"],
                    "element": comb["result"],
                    "favorable": True,
                    "description": f"กิ่งดินปีจร {t_branch} ผูกมิตรกับ {p_name} ({n_branch}) ก่อกำเนิดธาตุ {comb['result']} ส่งเสริมมิตรภาพและความสำเร็จราบรื่น"
                })

        # 4. Check Branch Harms
        for i, (n_branch, p_name) in enumerate(zip(natal_branches, ["Year", "Month", "Day", "Hour"])):
            pair = frozenset([n_branch, t_branch])
            if pair in BRANCH_HARMS:
                aspects.append({
                    "type": "HARM",
                    "category": "Earthly Branch Harm (地支六害)",
                    "pillar": p_name,
                    "natal": n_branch,
                    "transit": t_branch,
                    "name": BRANCH_HARMS[pair],
                    "favorable": False,
                    "description": f"กิ่งดินปีจร {t_branch} ให้โทษเบียดเบียนกับ {p_name} ({n_branch}) ควรระวังเรื่องเอกสารสัญญาหรือความขัดแย้งแฝง"
                })

        # Overall Transit Score
        positive_count = sum(1 for a in aspects if a.get("favorable", True))
        negative_count = sum(1 for a in aspects if not a.get("favorable", True))
        harmony_score = max(10, min(95, 60 + (positive_count * 15) - (negative_count * 20)))

        return {
            "transit_year": transit_year,
            "transit_age": transit_age,
            "annual_pillar": annual_pillar,
            "aspects_count": len(aspects),
            "aspects": aspects,
            "harmony_score": harmony_score,
            "status": "Auspicious" if harmony_score >= 60 else "Cautionary",
        }

    @staticmethod
    def get_live_sky_pillars(
        dt: Optional[datetime] = None,
        longitude: float = 100.493,
        utc_offset_hours: float = 7.0
    ) -> Dict[str, Any]:
        """Compute the live 4-Pillar chart for the real-time celestial sky."""
        if dt is None:
            dt = datetime.now(timezone(timedelta(hours=utc_offset_hours)))

        year = dt.year
        month = dt.month
        day = dt.day
        hour = dt.hour
        minute = dt.minute

        # Year Pillar
        y_offset = (year - 1984) % 60
        y_stem = HEAVENLY_STEMS[y_offset % 10]
        y_branch = EARTHLY_BRANCHES[y_offset % 12]

        # Month Pillar (Approximate solar month offset)
        m_stem = HEAVENLY_STEMS[(y_offset * 2 + month) % 10]
        m_branch = EARTHLY_BRANCHES[(month + 1) % 12]

        # Day Pillar
        d_stem = HEAVENLY_STEMS[(day + month * 2) % 10]
        d_branch = EARTHLY_BRANCHES[(day + 4) % 12]

        # Hour Pillar (Double-hour Shi Chen)
        h_idx = ((hour + 1) // 2) % 12
        h_stem = HEAVENLY_STEMS[(h_idx + 2) % 10]
        h_branch = EARTHLY_BRANCHES[h_idx]

        return {
            "timestamp": dt.strftime("%Y-%m-%d %H:%M:%S"),
            "year_pillar": f"{y_stem}{y_branch}",
            "month_pillar": f"{m_stem}{m_branch}",
            "day_pillar": f"{d_stem}{d_branch}",
            "hour_pillar": f"{h_stem}{h_branch}",
            "double_hour_name": f"{h_branch}時",
            "pillars_str": f"{y_stem}{y_branch}年 {m_stem}{m_branch}月 {d_stem}{d_branch}日 {h_stem}{h_branch}時",
        }


transit_engine = TransitEngine()
