from __future__ import annotations

from typing import Any

from project.core.base_engine import AbstractAstrologyEngine, EngineChartResult
try:
    from rust_core import liu_yao_najia, liu_yao_five_relatives
except (ImportError, AttributeError):
    def liu_yao_najia(trigram_idx: int, is_upper: bool) -> list[int]:
        if trigram_idx in (7, 1): # Qian & Zhen
            return [6, 8, 10] if is_upper else [0, 2, 4]
        elif trigram_idx == 2: # Kan
            return [8, 10, 0] if is_upper else [2, 4, 6]
        elif trigram_idx == 4: # Gen
            return [10, 0, 2] if is_upper else [4, 6, 8]
        elif trigram_idx == 0: # Kun
            return [1, 11, 9] if is_upper else [7, 5, 3]
        elif trigram_idx == 6: # Xun
            return [7, 5, 3] if is_upper else [1, 11, 9]
        elif trigram_idx == 5: # Li
            return [9, 7, 5] if is_upper else [3, 1, 11]
        elif trigram_idx == 3: # Dui
            return [11, 9, 7] if is_upper else [5, 3, 1]
        return [0, 0, 0]

    def liu_yao_five_relatives(line_element: int, day_master_element: int) -> str:
        if line_element == day_master_element:
            return "兄弟"
        elif (day_master_element + 1) % 5 == line_element:
            return "子孫"
        elif (line_element + 1) % 5 == day_master_element:
            return "父母"
        elif (day_master_element + 2) % 5 == line_element:
            return "妻財"
        elif (line_element + 2) % 5 == day_master_element:
            return "官鬼"
        return "未知"


TRIGRAM_NAMES = ["坤", "震", "坎", "兌", "艮", "離", "巽", "乾"]
BRANCH_NAMES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
ELEMENT_NAMES = ["木", "火", "土", "金", "水"]
STEM_NAMES = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]

# Trigram Elements: 0=Kun(Earth), 1=Zhen(Wood), 2=Kan(Water), 3=Dui(Metal), 4=Gen(Earth), 5=Li(Fire), 6=Xun(Wood), 7=Qian(Metal)
PALACE_ELEMENTS = [2, 0, 4, 3, 2, 1, 0, 3]

# Branch Elements
BRANCH_ELEMENTS = [4, 2, 0, 0, 2, 1, 1, 2, 3, 3, 2, 4]

SIX_ANIMALS = ["青龍", "朱雀", "勾陳", "螣蛇", "白虎", "玄武"]
DAY_STEM_ANIMAL_START = [0, 0, 1, 1, 2, 3, 4, 4, 5, 5]


class LiuYaoEngine(AbstractAstrologyEngine):
    """
    Liu Yao (六爻) Six Lines Divination Engine.
    Implements Na Jia, Five Relatives, Six Animals, and moving lines.
    """

    @property
    def engine_name(self) -> str:
        return "Liu Yao Divination Engine"

    @property
    def system_type(self) -> str:
        return "pu_shi"

    def get_palace_and_shi(self, upper_idx: int, lower_idx: int) -> tuple[int, int]:
        """
        Calculates Palace trigram index and World (Shi) line index (0-5).
        Returns (palace_idx, shi_idx)
        """
        m1 = (upper_idx & 1) == (lower_idx & 1)
        m2 = (upper_idx & 2) == (lower_idx & 2)
        m3 = (upper_idx & 4) == (lower_idx & 4)

        if m1 and m2 and m3: return upper_idx, 5
        if not m1 and m2 and m3: return upper_idx, 0
        if not m1 and not m2 and m3: return upper_idx, 1
        if not m1 and not m2 and not m3: return upper_idx, 2
        if m1 and not m2 and not m3: return upper_idx ^ 1, 3
        if m1 and m2 and not m3: return upper_idx ^ 3, 4
        if not m1 and m2 and not m3: return upper_idx ^ 2, 3
        if m1 and not m2 and m3: return upper_idx ^ 2, 2
        return upper_idx, 0 # Fallback

    def lines_to_binary(self, lines: list[int]) -> list[int]:
        """Convert lines (6,7,8,9) to binary 0/1 (bottom to top). 7/9=1, 6/8=0."""
        return [1 if x in (7, 9) else 0 for x in lines]

    def lines_to_trigrams(self, lines_bin: list[int]) -> tuple[int, int]:
        """Convert binary lines to lower and upper trigram indices."""
        lower = lines_bin[0] | (lines_bin[1] << 1) | (lines_bin[2] << 2)
        upper = lines_bin[3] | (lines_bin[4] << 1) | (lines_bin[5] << 2)
        return lower, upper

    def calculate(self, lines: list[int], day_stem_idx: int = 0, month_branch_idx: int = 0) -> EngineChartResult:
        if len(lines) != 6:
            raise ValueError("Lines must be exactly 6 values (6, 7, 8, 9).")

        primary_bin = self.lines_to_binary(lines)
        transformed_bin = [
            (0 if x == 9 else 1 if x == 6 else primary_bin[i])
            for i, x in enumerate(lines)
        ]

        lower_idx, upper_idx = self.lines_to_trigrams(primary_bin)
        palace_idx, shi_idx = self.get_palace_and_shi(upper_idx, lower_idx)
        ying_idx = (shi_idx + 3) % 6
        palace_element = PALACE_ELEMENTS[palace_idx]

        # Na Jia for primary hexagram
        lower_branches = liu_yao_najia(lower_idx, False)
        upper_branches = liu_yao_najia(upper_idx, True)
        primary_branches = lower_branches + upper_branches

        # Transformed trigrams
        t_lower_idx, t_upper_idx = self.lines_to_trigrams(transformed_bin)
        t_lower_branches = liu_yao_najia(t_lower_idx, False)
        t_upper_branches = liu_yao_najia(t_upper_idx, True)
        transformed_branches = t_lower_branches + t_upper_branches

        animal_start = DAY_STEM_ANIMAL_START[day_stem_idx % 10]

        six_lines_detail = []
        for i in range(6):
            val = lines[i]
            is_moving = val in (6, 9)
            branch = primary_branches[i]
            branch_element = BRANCH_ELEMENTS[branch]
            relative = liu_yao_five_relatives(branch_element, palace_element)
            animal = SIX_ANIMALS[(animal_start + i) % 6]
            
            line_detail = {
                "line_number": i + 1,
                "value": val,
                "is_moving": is_moving,
                "is_shi": i == shi_idx,
                "is_ying": i == ying_idx,
                "branch": BRANCH_NAMES[branch],
                "element": ELEMENT_NAMES[branch_element],
                "relative": relative,
                "animal": animal,
            }

            if is_moving:
                t_branch = transformed_branches[i]
                t_element = BRANCH_ELEMENTS[t_branch]
                t_relative = liu_yao_five_relatives(t_element, palace_element)
                line_detail["transformed"] = {
                    "branch": BRANCH_NAMES[t_branch],
                    "element": ELEMENT_NAMES[t_element],
                    "relative": t_relative,
                }
            six_lines_detail.append(line_detail)

        chart_data = {
            "palace": TRIGRAM_NAMES[palace_idx],
            "palace_element": ELEMENT_NAMES[palace_element],
            "day_stem": STEM_NAMES[day_stem_idx % 10],
            "month_branch": BRANCH_NAMES[month_branch_idx % 12],
            "shi_line": shi_idx + 1,
            "ying_line": ying_idx + 1,
            "lines": six_lines_detail,
        }

        return EngineChartResult(
            engine_name=self.engine_name,
            system_type=self.system_type,
            chart_data=chart_data,
        )
