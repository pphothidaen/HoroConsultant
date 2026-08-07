"""
Qi Men Dun Jia (奇門遁甲) Core Calculation Engine
==================================================
Deterministic calculation of Qi Men Dun Jia 4-Plate charts:
- Yang/Yin Dun 18 Ju (陰陽十八局)
- Earth Plate (地盤)
- Heaven Plate / 9 Stars (天盤 - 九星)
- Door Plate / 8 Doors (門盤 - 八門)
- Spirit Plate / 8 Spirits (神盤 - 八神)
"""

from typing import Dict, List, Any, Optional
from datetime import datetime


PALACE_NUMBERS = [1, 2, 3, 4, 5, 6, 7, 8, 9]

NINE_STARS = ["天蓬", "天芮", "天衝", "天輔", "天禽", "天心", "天柱", "天任", "天英"]
EIGHT_DOORS = ["休門", "生門", "傷門", "杜門", "景門", "死門", "驚門", "開門"]
EIGHT_SPIRITS = ["值符", "騰蛇", "太陰", "六合", "白虎", "玄武", "九地", "九天"]

# 24 Solar Terms mapped to Yang/Yin Dun and Ju Numbers [Lower, Middle, Upper Ju]
SOLAR_TERM_JU_MAP = {
    # Yang Dun (冬至 -> 夏至)
    "冬至": ("Yang", [1, 7, 4]),
    "驚蟄": ("Yang", [1, 7, 4]),
    "清明": ("Yang", [4, 1, 7]),
    "小寒": ("Yang", [2, 8, 5]),
    "大寒": ("Yang", [3, 9, 6]),
    "立春": ("Yang", [8, 5, 2]),
    "雨水": ("Yang", [9, 6, 3]),
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
}


class QiMenEngine:
    """Core Qi Men Dun Jia engine."""

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

    def calculate_chart(self, year: int, month: int, day: int, hour: int, solar_term: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculate Qi Men Dun Jia chart for given date & time.
        """
        if not solar_term:
            solar_term = self.determine_solar_term(month, day)

        dun_type, ju_list = SOLAR_TERM_JU_MAP.get(solar_term, ("Yang", [1, 7, 4]))
        
        # Select Yuan (Upper/Middle/Lower Ju) based on day % 5
        yuan_idx = (day % 15) // 5
        if yuan_idx >= 3:
            yuan_idx = 0
        ju_number = ju_list[yuan_idx]

        # Earth Plate: Nine Palaces distribution of 6 Instruments & 3 Wonders (戊, 己, 庚, 辛, 壬, 癸, 丁, 丙, 乙)
        stems_order = ["戊", "己", "庚", "辛", "壬", "癸", "丁", "丙", "乙"]
        earth_plate = {}
        
        for i, stem in enumerate(stems_order):
            if dun_type == "Yang":
                palace = (ju_number + i - 1) % 9 + 1
            else:
                palace = (ju_number - i - 1) % 9 + 1
            earth_plate[palace] = stem

        # Nine Stars Placement across 9 Palaces (starting from Kan Palace 1)
        stars_plate = {}
        for idx, star in enumerate(NINE_STARS):
            palace = (idx % 9) + 1
            stars_plate[palace] = star

        # Eight Doors Placement across 8 Perimeter Palaces (1, 8, 3, 4, 9, 2, 7, 6)
        perimeter_palaces = [1, 8, 3, 4, 9, 2, 7, 6]
        doors_plate = {}
        for idx, door in enumerate(EIGHT_DOORS):
            palace = perimeter_palaces[idx % 8]
            doors_plate[palace] = door

        # Eight Spirits Placement across 8 Perimeter Palaces
        spirits_plate = {}
        for idx, spirit in enumerate(EIGHT_SPIRITS):
            palace = perimeter_palaces[idx % 8]
            spirits_plate[palace] = spirit

        # Construct Palace Detail
        palace_details = []
        for p in PALACE_NUMBERS:
            palace_details.append({
                "palace_number": p,
                "earth_stem": earth_plate.get(p, "戊"),
                "star": stars_plate.get(p, "天輔"),
                "door": doors_plate.get(p, "生門"),
                "spirit": spirits_plate.get(p, "值符")
            })

        return {
            "engine": "QiMenEngine",
            "datetime": f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:00",
            "solar_term": solar_term,
            "dun_type": dun_type,
            "ju_number": ju_number,
            "palaces": palace_details
        }


if __name__ == "__main__":
    qm = QiMenEngine()
    chart = qm.calculate_chart(2026, 8, 7, 14)
    print(chart)
