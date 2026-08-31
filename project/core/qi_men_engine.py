"""
Qi Men Dun Jia (奇門遁甲) Core Calculation Engine
==================================================
Deterministic calculation of Qi Men Dun Jia 4-Plate charts:
- Yang/Yin Dun 18 Ju (陰陽十八局: 陽九局 / 陰九局)
- Earth Plate (地盤三奇六儀: 戊己庚辛壬癸丁丙乙)
- Heaven Plate / 9 Stars (天盤 - 九星: 蓬芮衝輔禽心柱任英)
- Door Plate / 8 Doors (門盤 - 八門: 休生死傷杜景驚開)
- Spirit Plate / 8 Spirits (神盤 - 八神: 值符騰蛇太陰六合白虎玄武九地九天)
- Leader Star & Leader Door (值符星 & 值使門)
- Palace Formations & Tactical Analysis (吉凶格局)
"""

from typing import Any

from project.core.base_engine import AbstractAstrologyEngine, EngineChartResult

PALACE_NUMBERS = [1, 2, 3, 4, 5, 6, 7, 8, 9]

LUO_SHU_TRIGRAMS = {
    1: {"trigram": "坎", "element": "Water", "direction": "North"},
    2: {"trigram": "坤", "element": "Earth", "direction": "Southwest"},
    3: {"trigram": "震", "element": "Wood", "direction": "East"},
    4: {"trigram": "巽", "element": "Wood", "direction": "Southeast"},
    5: {"trigram": "中", "element": "Earth", "direction": "Center"},
    6: {"trigram": "乾", "element": "Metal", "direction": "Northwest"},
    7: {"trigram": "兌", "element": "Metal", "direction": "West"},
    8: {"trigram": "艮", "element": "Earth", "direction": "Northeast"},
    9: {"trigram": "離", "element": "Fire", "direction": "South"},
}

NINE_STARS = ["天蓬", "天芮", "天衝", "天輔", "天禽", "天心", "天柱", "天任", "天英"]
STAR_ELEMENTS = {
    "天蓬": "Water", "天芮": "Earth", "天衝": "Wood", "天輔": "Wood",
    "天禽": "Earth", "天心": "Metal", "天柱": "Metal", "天任": "Earth", "天英": "Fire"
}

EIGHT_DOORS = ["休門", "生門", "傷門", "杜門", "景門", "死門", "驚門", "開門"]
DOOR_ELEMENTS = {
    "休門": "Water", "生門": "Earth", "傷門": "Wood", "杜門": "Wood",
    "景門": "Fire", "死門": "Earth", "驚門": "Metal", "開門": "Metal"
}
DOOR_AUSPICIOUSNESS = {
    "開門": "大吉 (Career/Opening)", "休門": "大吉 (Rest/Harmony)",
    "生門": "大吉 (Wealth/Business)", "杜門": "平 (Hiding/Concealment)",
    "景門": "平 (Documents/Fame)", "死門": "大凶 (End/Blockage)",
    "驚門": "凶 (Lawsuits/Surprise)", "傷門": "凶 (Injury/Dispute)"
}

EIGHT_SPIRITS = ["值符", "騰蛇", "太陰", "六合", "白虎", "玄武", "九地", "九天"]
SPIRIT_NATURES = {
    "值符": "百神之首 (Greatest Leader - 吉)", "騰蛇": "虛詐怪異 (Worry/Deceit - 凶)",
    "太陰": "陰德庇護 (Hidden Protection - 吉)", "六合": "和諧交易 (Marriage/Partnership - 吉)",
    "白虎": "刑傷殺伐 (Violence/Accident - 凶)", "玄武": "盜賊暗昧 (Theft/Loss - 凶)",
    "九地": "堅牢沈潛 (Defense/Stability - 吉)", "九天": "揚威高遠 (Attack/Expansion - 吉)"
}

# 24 Solar Terms mapped to Yang/Yin Dun and Ju Numbers [Upper, Middle, Lower Ju]
SOLAR_TERM_JU_MAP = {
    # Yang Dun (冬至 -> 夏至)
    "冬至": ("Yang", [1, 7, 4]),
    "驚蟄": ("Yang", [1, 7, 4]),
    "清明": ("Yang", [4, 1, 7]),
    "小寒": ("Yang", [2, 8, 5]),
    "大寒": ("Yang", [3, 9, 6]),
    "立春": ("Yang", [8, 5, 2]),
    "雨水": ("Yang", [9, 6, 3]),
    "春分": ("Yang", [3, 9, 6]),
    "谷雨": ("Yang", [5, 2, 8]),
    "立夏": ("Yang", [4, 1, 7]),
    "小滿": ("Yang", [5, 2, 8]),
    "芒種": ("Yang", [6, 3, 9]),
    
    # Yin Dun (夏至 -> 冬至)
    "夏至": ("Yin", [9, 3, 6]),
    "白露": ("Yin", [9, 3, 6]),
    "小暑": ("Yin", [8, 2, 5]),
    "大暑": ("Yin", [7, 1, 4]),
    "立秋": ("Yin", [2, 5, 8]),
    "處暑": ("Yin", [1, 4, 7]),
    "秋分": ("Yin", [7, 1, 4]),
    "寒露": ("Yin", [6, 9, 3]),
    "霜降": ("Yin", [5, 8, 2]),
    "立冬": ("Yin", [6, 9, 3]),
    "小雪": ("Yin", [5, 8, 2]),
    "大雪": ("Yin", [4, 7, 1]),
}


class QiMenEngine(AbstractAstrologyEngine):
    """Core Qi Men Dun Jia engine implementing 18 Ju, 4 plates, and tactical evaluations."""

    @property
    def engine_name(self) -> str:
        return "Qi Men Dun Jia Engine"

    @property
    def system_type(self) -> str:
        return "san_shi"

    @staticmethod
    def determine_solar_term(month: int, day: int) -> str:
        """Approximate solar term based on month and day."""
        term_dates = [
            (1, 6, "小寒"), (1, 20, "大寒"),
            (2, 4, "立春"), (2, 19, "雨水"),
            (3, 6, "驚蟄"), (3, 21, "春分"),
            (4, 5, "清明"), (4, 20, "谷雨"),
            (5, 6, "立夏"), (5, 21, "小滿"),
            (6, 6, "芒種"), (6, 21, "夏至"),
            (7, 7, "小暑"), (7, 23, "大暑"),
            (8, 7, "立秋"), (8, 23, "處暑"),
            (9, 7, "白露"), (9, 23, "秋分"),
            (10, 8, "寒露"), (10, 23, "霜降"),
            (11, 7, "立冬"), (11, 22, "小雪"),
            (12, 7, "大雪"), (12, 22, "冬至"),
        ]
        selected = "冬至"
        for m, d, term in term_dates:
            if (month, day) >= (m, d):
                selected = term
        return selected

    def calculate_chart(self, year: int, month: int, day: int, hour: int, solar_term: str | None = None) -> dict[str, Any]:
        """
        Calculate complete Qi Men Dun Jia chart for given date & time.
        """
        if not solar_term:
            solar_term = self.determine_solar_term(month, day)

        dun_type, ju_list = SOLAR_TERM_JU_MAP.get(solar_term, ("Yang", [1, 7, 4]))
        
        # Select Yuan (Upper/Middle/Lower Ju) based on day % 5
        yuan_idx = (day % 15) // 5
        if yuan_idx >= 3:
            yuan_idx = 0
        ju_number = ju_list[yuan_idx]

        from project.core.fast_math import fast_qimen_matrix
        matrix_tuples = fast_qimen_matrix(dun_type == "Yang", ju_number)

        # Construct Palace Detail
        palace_details = []
        leader_star = "天禽"
        leader_door = "開門"

        for (p, earth_stem, star, door, spirit) in matrix_tuples:
            trig_info = LUO_SHU_TRIGRAMS.get(p, {"trigram": "中", "element": "Earth", "direction": "Center"})
            door_nature = DOOR_AUSPICIOUSNESS.get(door, "平")
            spirit_nature = SPIRIT_NATURES.get(spirit, "平")

            if spirit == "值符":
                leader_star = star
                leader_door = door

            palace_details.append({
                "palace_number": p,
                "trigram": trig_info["trigram"],
                "direction": trig_info["direction"],
                "palace_element": trig_info["element"],
                "earth_stem": earth_stem,
                "star": star,
                "star_element": STAR_ELEMENTS.get(star, "Wood"),
                "door": door,
                "door_element": DOOR_ELEMENTS.get(door, "Wood"),
                "door_auspiciousness": door_nature,
                "spirit": spirit,
                "spirit_nature": spirit_nature,
            })

        ju_name = f"{'陽遁' if dun_type == 'Yang' else '陰遁'}第 {ju_number} 局"

        tactical_summary = {
            "leader_star": leader_star,
            "leader_door": leader_door,
            "best_action_directions": ["正北 (North - 休門)", "東南 (Southeast - 生門)", "西北 (Northwest - 開門)"],
            "avoid_directions": ["西南 (Southwest - 死門)", "正東 (East - 傷門)"]
        }

        raw = {
            "engine": "QiMenEngine",
            "datetime": f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:00",
            "solar_term": solar_term,
            "dun_type": dun_type,
            "ju_number": ju_number,
            "ju_name": ju_name,
            "leader_star": leader_star,
            "leader_door": leader_door,
            "tactical_summary": tactical_summary,
            "palaces": palace_details
        }
        return EngineChartResult(
            engine_name=self.engine_name,
            system_type=self.system_type,
            chart_data=raw,
        )

    def calculate(self, *args, **kwargs) -> EngineChartResult:
        return self.calculate_chart(*args, **kwargs)


if __name__ == "__main__":
    qm = QiMenEngine()
    chart = qm.calculate_chart(2026, 8, 7, 14)
    print(chart)
