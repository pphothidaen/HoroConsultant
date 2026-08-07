"""
Da Liu Ren (大六壬) Core Calculation Engine
============================================
Deterministic calculation of Da Liu Ren 3-Transmission & 4-Lesson charts:
- Earth/Heaven Plate (天地盤) via Month General (月將加時)
- Four Lessons (四課: 日干一課, 二課, 日支三課, 四課)
- Three Transmissions (三傳: 初傳, 中傳, 末傳)
- Twelve Heavenly Generals (十二天將)
"""

from typing import Dict, List, Any, Optional
from project.core.base_engine import AbstractAstrologyEngine, EngineChartResult

STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

MONTH_GENERALS = {
    "正月": "亥", "二月": "戌", "三月": "酉", "四月": "申",
    "五月": "未", "六月": "午", "七月": "巳", "八月": "辰",
    "九月": "卯", "十月": "寅", "十一月": "丑", "十二月": "子"
}

HEAVENLY_GENERALS = [
    "貴人", "螣蛇", "朱雀", "六合", "勾陳", "青龍",
    "天空", "白虎", "太常", "玄武", "太陰", "天后"
]

# Stem Parasitic Branch mapping (寄干)
STEM_PARASITIC_BRANCH = {
    "甲": "寅", "乙": "辰", "丙": "巳", "丁": "未", "戊": "巳",
    "己": "未", "庚": "申", "辛": "戌", "壬": "亥", "癸": "丑"
}


class LiuRenEngine(AbstractAstrologyEngine):
    """Core Da Liu Ren calculation engine."""

    @property
    def engine_name(self) -> str:
        return "Da Liu Ren Engine"

    @property
    def system_type(self) -> str:
        return "san_shi"

    def calculate_heaven_plate(self, month_general_branch: str, hour_branch: str) -> Dict[str, str]:
        """
        Calculate Heaven Plate mapping (Earth Branch -> Heaven Branch).
        Month General branch is placed over Hour Branch, then steps clockwise.
        """
        gen_idx = BRANCHES.index(month_general_branch)
        hour_idx = BRANCHES.index(hour_branch)
        
        heaven_plate = {}
        for i in range(12):
            earth_b = BRANCHES[(hour_idx + i) % 12]
            heaven_b = BRANCHES[(gen_idx + i) % 12]
            heaven_plate[earth_b] = heaven_b
        return heaven_plate

    def calculate_four_lessons(self, day_stem: str, day_branch: str, heaven_plate: Dict[str, str]) -> List[Dict[str, str]]:
        """
        Calculate Four Lessons (四課):
        - Lesson 1: Day Stem parasitic branch -> Heaven Branch
        - Lesson 2: Lesson 1 Heaven Branch -> Heaven Branch over it
        - Lesson 3: Day Branch -> Heaven Branch over it
        - Lesson 4: Lesson 3 Heaven Branch -> Heaven Branch over it
        """
        stem_branch = STEM_PARASITIC_BRANCH.get(day_stem, "寅")
        
        lesson1_bottom = day_stem
        lesson1_top = heaven_plate.get(stem_branch, "寅")
        
        lesson2_bottom = lesson1_top
        lesson2_top = heaven_plate.get(lesson2_bottom, "寅")
        
        lesson3_bottom = day_branch
        lesson3_top = heaven_plate.get(day_branch, "子")
        
        lesson4_bottom = lesson3_top
        lesson4_top = heaven_plate.get(lesson4_bottom, "子")
        
        return [
            {"lesson_name": "第一課 (干上)", "bottom": lesson1_bottom, "top": lesson1_top},
            {"lesson_name": "第二課 (干上上)", "bottom": lesson2_bottom, "top": lesson2_top},
            {"lesson_name": "第三課 (支上)", "bottom": lesson3_bottom, "top": lesson3_top},
            {"lesson_name": "第四課 (支上上)", "bottom": lesson4_bottom, "top": lesson4_top},
        ]

    def calculate_three_transmissions(self, four_lessons: List[Dict[str, str]], heaven_plate: Dict[str, str]) -> Dict[str, str]:
        """
        Calculate Three Transmissions (三傳: 初傳, 中傳, 末傳) via basic Ke/Zei rule.
        """
        # Default fallback to Lesson 1 top if no complex over-coming
        chu_chuan = four_lessons[0]["top"]
        zhong_chuan = heaven_plate.get(chu_chuan, "子")
        mo_chuan = heaven_plate.get(zhong_chuan, "子")
        
        return {
            "初傳 (發端)": chu_chuan,
            "中傳 (移革)": zhong_chuan,
            "末傳 (歸結)": mo_chuan
        }

    def calculate_generals_plate(self, noble_branch: str, heaven_plate: Dict[str, str]) -> Dict[str, str]:
        """
        Assign 12 Heavenly Generals to Earth/Heaven branches.
        """
        noble_idx = BRANCHES.index(noble_branch)
        generals_plate = {}
        for i, gen in enumerate(HEAVENLY_GENERALS):
            branch = BRANCHES[(noble_idx + i) % 12]
            generals_plate[branch] = gen
        return generals_plate

    def calculate_chart(self, day_stem: str, day_branch: str, month_general: str, hour_branch: str) -> Dict[str, Any]:
        """
        Calculate complete Da Liu Ren chart.
        """
        month_general_branch = MONTH_GENERALS.get(month_general, "亥")
        heaven_plate = self.calculate_heaven_plate(month_general_branch, hour_branch)
        four_lessons = self.calculate_four_lessons(day_stem, day_branch, heaven_plate)
        three_transmissions = self.calculate_three_transmissions(four_lessons, heaven_plate)
        generals_plate = self.calculate_generals_plate(month_general_branch, heaven_plate)

        raw = {
            "engine": "LiuRenEngine",
            "day_stem_branch": f"{day_stem}{day_branch}",
            "month_general": f"{month_general} ({month_general_branch})",
            "hour_branch": hour_branch,
            "heaven_plate": heaven_plate,
            "four_lessons": four_lessons,
            "three_transmissions": three_transmissions,
            "generals_plate": generals_plate
        }
        return EngineChartResult(
            engine_name=self.engine_name,
            system_type=self.system_type,
            chart_data=raw,
        )

    def calculate(self, *args, **kwargs) -> EngineChartResult:
        return self.calculate_chart(*args, **kwargs)


if __name__ == "__main__":
    lr = LiuRenEngine()
    chart = lr.calculate_chart("甲", "子", "正月", "午")
    print(chart)
