"""
Xuan Kong Flying Stars (玄空風水) Core Calculation Engine
=========================================================
Deterministic calculation of Xuan Kong Flying Stars 9-Grid Charts:
- 24 Mountains (二十四山) compass direction lookup
- Period 9 (九運 2024-2043) Base Chart (運盤)
- Sitting Star (山星) and Facing Star (向星) flying tracks (顺飞 / 逆飞)
"""

from typing import Dict, List, Any, Optional


MOUNTAINS_24 = [
    ("壬", 337.5, 352.5, "坎", "陽"),
    ("子", 352.5, 7.5, "坎", "陰"),
    ("癸", 7.5, 22.5, "坎", "陰"),
    ("丑", 22.5, 37.5, "艮", "陰"),
    ("艮", 37.5, 52.5, "艮", "陽"),
    ("寅", 52.5, 67.5, "艮", "陽"),
    ("甲", 67.5, 82.5, "震", "陽"),
    ("卯", 82.5, 97.5, "震", "陰"),
    ("乙", 97.5, 112.5, "震", "陰"),
    ("辰", 112.5, 127.5, "巽", "陰"),
    ("巽", 127.5, 142.5, "巽", "陽"),
    ("巳", 142.5, 157.5, "巽", "陽"),
    ("丙", 157.5, 172.5, "離", "陽"),
    ("午", 172.5, 187.5, "離", "陰"),
    ("丁", 187.5, 202.5, "離", "陰"),
    ("未", 202.5, 217.5, "坤", "陰"),
    ("坤", 217.5, 232.5, "坤", "陽"),
    ("申", 232.5, 247.5, "坤", "陽"),
    ("庚", 247.5, 262.5, "兌", "陽"),
    ("酉", 262.5, 277.5, "兌", "陰"),
    ("辛", 277.5, 292.5, "兌", "陰"),
    ("戌", 292.5, 307.5, "乾", "陰"),
    ("乾", 307.5, 322.5, "乾", "陽"),
    ("亥", 322.5, 337.5, "乾", "陽")
]

# Nine Palaces Grid Layout (Luo Shu order: 1 Kan, 2 Kun, 3 Zhen, 4 Xun, 5 Center, 6 Qian, 7 Dui, 8 Gen, 9 Li)
LUO_SHU_PALACES = [
    (1, "坎", "北"), (2, "坤", "西南"), (3, "震", "東"),
    (4, "巽", "東南"), (5, "中宮", "中央"), (6, "乾", "西北"),
    (7, "兌", "西"), (8, "艮", "東北"), (9, "離", "南")
]

# Period 9 Base Chart (九運運盤) - Center is 9
PERIOD_9_BASE_CHART = {
    1: 5, 2: 6, 3: 7,
    4: 8, 5: 9, 6: 1,
    7: 2, 8: 3, 9: 4
}

STAR_NAMES = {
    1: "一白貪狼星 (水)",
    2: "二黑巨門星 (土)",
    3: "三碧祿存星 (木)",
    4: "四綠文曲星 (木)",
    5: "五黃廉貞星 (土)",
    6: "六白武曲星 (金)",
    7: "七赤破軍星 (金)",
    8: "八白左輔星 (土)",
    9: "九紫右弼星 (火)"
}

from typing import Dict, List, Any, Optional
from project.core.base_engine import AbstractAstrologyEngine, EngineChartResult


class XuanKongEngine(AbstractAstrologyEngine):
    """Core Xuan Kong Flying Stars engine."""

    @property
    def engine_name(self) -> str:
        return "Xuan Kong Flying Stars Engine"

    @property
    def system_type(self) -> str:
        return "xiang_xue"

    def resolve_mountain(self, degree: float) -> tuple[str, str, str]:
        """Resolve facing degree (0-360) to Mountain Name, Trigram, and Yin/Yang."""
        deg = degree % 360
        for name, start, end, trigram, yinyang in MOUNTAINS_24:
            if start > end:  # Across 0° boundary
                if deg >= start or deg < end:
                    return name, trigram, yinyang
            else:
                if start <= deg < end:
                    return name, trigram, yinyang
        return "子", "坎", "陰"

    def fly_stars(self, center_star: int, is_forward: bool) -> Dict[int, int]:
        """
        Fly stars forward (順飛) or backward (逆飛) from center star through Luo Shu sequence.
        Luo Shu sequence of palaces: 5 -> 6 -> 7 -> 8 -> 9 -> 1 -> 2 -> 3 -> 4
        """
        palace_sequence = [5, 6, 7, 8, 9, 1, 2, 3, 4]
        result = {}
        for idx, palace in enumerate(palace_sequence):
            if is_forward:
                star = (center_star + idx - 1) % 9 + 1
            else:
                star = (center_star - idx - 1) % 9 + 1
            result[palace] = star
        return result

    def calculate_chart(self, facing_degree: float, period: int = 9) -> Dict[str, Any]:
        """
        Calculate complete Xuan Kong Flying Stars 9-Grid chart for a given facing degree.
        """
        facing_name, facing_trigram, facing_yy = self.resolve_mountain(facing_degree)
        sitting_degree = (facing_degree + 180) % 360
        sitting_name, sitting_trigram, sitting_yy = self.resolve_mountain(sitting_degree)

        base_chart = PERIOD_9_BASE_CHART if period == 9 else PERIOD_9_BASE_CHART

        # Determine center Sitting Star & Facing Star
        # Facing mountain corresponds to its palace base star in Period Chart
        center_sitting_star = base_chart.get(5, 9)
        center_facing_star = base_chart.get(9, 4)

        sitting_stars = self.fly_stars(center_sitting_star, is_forward=(sitting_yy == "陽"))
        facing_stars = self.fly_stars(center_facing_star, is_forward=(facing_yy == "陽"))

        from project.core.fast_math import fast_xuankong_9grid
        grid_matrix = fast_xuankong_9grid(facing_degree, period)
        matrix_map = {p[0]: (p[1], p[2], p[3]) for p in grid_matrix}

        palaces_grid = []
        for palace_num, palace_name, direction in LUO_SHU_PALACES:
            base_s, sit_s, face_s = matrix_map.get(palace_num, (base_chart[palace_num], sitting_stars[palace_num], facing_stars[palace_num]))
            palaces_grid.append({
                "palace_number": palace_num,
                "palace_name": palace_name,
                "direction": direction,
                "base_star": base_s,
                "sitting_star": sit_s,
                "facing_star": face_s,
                "facing_star_name": STAR_NAMES[face_s]
            })


        raw = {
            "engine": "XuanKongEngine",
            "period": period,
            "facing_degree": facing_degree,
            "facing_mountain": f"{facing_name} ({facing_trigram}卦 - {facing_yy})",
            "sitting_mountain": f"{sitting_name} ({sitting_trigram}卦 - {sitting_yy})",
            "grid_palaces": palaces_grid
        }
        return EngineChartResult(
            engine_name=self.engine_name,
            system_type=self.system_type,
            chart_data=raw,
        )

    def calculate(self, *args, **kwargs) -> EngineChartResult:
        return self.calculate_chart(*args, **kwargs)


if __name__ == "__main__":
    xk = XuanKongEngine()
    chart = xk.calculate_chart(180.0, period=9)
    print(chart)
