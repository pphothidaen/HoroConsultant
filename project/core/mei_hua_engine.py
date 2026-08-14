"""
Mei Hua Yi Shu (梅花易數) Core Calculation Engine
=================================================
Deterministic calculation for Plum Blossom Numerology.
"""

from typing import Any, Optional
from project.core.base_engine import AbstractAstrologyEngine, EngineChartResult
try:
    from rust_core import mei_hua_hexagram_from_time
except ImportError:
    # Fallback if rust_core isn't built yet
    def mei_hua_hexagram_from_time(year: int, month: int, day: int, hour: int) -> tuple[int, int, int]:
        upper = (year + month + day) % 8
        upper = 8 if upper == 0 else upper
        lower = (year + month + day + hour) % 8
        lower = 8 if lower == 0 else lower
        moving = (year + month + day + hour) % 6
        moving = 6 if moving == 0 else moving
        return upper, lower, moving

# 1: 乾, 2: 兌, 3: 離, 4: 震, 5: 巽, 6: 坎, 7: 艮, 8: 坤
TRIGRAMS = {
    1: {"name": "乾", "element": "金", "lines": [1, 1, 1]},
    2: {"name": "兌", "element": "金", "lines": [1, 1, 0]},
    3: {"name": "離", "element": "火", "lines": [1, 0, 1]},
    4: {"name": "震", "element": "木", "lines": [1, 0, 0]},
    5: {"name": "巽", "element": "木", "lines": [0, 1, 1]},
    6: {"name": "坎", "element": "水", "lines": [0, 1, 0]},
    7: {"name": "艮", "element": "土", "lines": [0, 0, 1]},
    8: {"name": "坤", "element": "土", "lines": [0, 0, 0]},
}

ELEMENT_CYCLE = {
    "木": {"生": "火", "克": "土"},
    "火": {"生": "土", "克": "金"},
    "土": {"生": "金", "克": "水"},
    "金": {"生": "水", "克": "木"},
    "水": {"生": "木", "克": "火"},
}

def determine_interaction(body_element: str, function_element: str) -> str:
    if body_element == function_element:
        return "比和" # Same
    if ELEMENT_CYCLE[function_element]["生"] == body_element:
        return "生" # Function generates Body (生體)
    if ELEMENT_CYCLE[function_element]["克"] == body_element:
        return "克" # Function controls Body (克體)
    if ELEMENT_CYCLE[body_element]["生"] == function_element:
        return "洩" # Body generates Function (洩體)
    if ELEMENT_CYCLE[body_element]["克"] == function_element:
        return "耗" # Body controls Function (耗體)
    return "未知"

class MeiHuaEngine(AbstractAstrologyEngine):
    @property
    def engine_name(self) -> str:
        return "Mei Hua Yi Shu Engine"

    @property
    def system_type(self) -> str:
        return "divination"

    def _get_trigram_from_lines(self, lines: list[int]) -> int:
        for idx, t in TRIGRAMS.items():
            if t["lines"] == lines:
                return idx
        return 8

    def _build_result(self, upper_idx: int, lower_idx: int, moving_line: int, **kwargs) -> EngineChartResult:
        upper_trigram = TRIGRAMS[upper_idx]
        lower_trigram = TRIGRAMS[lower_idx]
        
        # 1. Primary Hexagram
        primary_lines = lower_trigram["lines"] + upper_trigram["lines"]
        
        # 2. Body and Function
        if moving_line <= 3:
            body_idx = upper_idx
            function_idx = lower_idx
            body_pos = "upper"
        else:
            body_idx = lower_idx
            function_idx = upper_idx
            body_pos = "lower"
            
        body_trigram = TRIGRAMS[body_idx]
        function_trigram = TRIGRAMS[function_idx]
        interaction = determine_interaction(body_trigram["element"], function_trigram["element"])
        
        # 3. Mutual Hexagram
        mutual_lower_lines = primary_lines[1:4]
        mutual_upper_lines = primary_lines[2:5]
        mutual_lower_idx = self._get_trigram_from_lines(mutual_lower_lines)
        mutual_upper_idx = self._get_trigram_from_lines(mutual_upper_lines)
        
        # 4. Transformed Hexagram
        transformed_lines = list(primary_lines)
        transformed_lines[moving_line - 1] = 1 - transformed_lines[moving_line - 1]
        transformed_lower_idx = self._get_trigram_from_lines(transformed_lines[0:3])
        transformed_upper_idx = self._get_trigram_from_lines(transformed_lines[3:6])
        
        chart_data = {
            "primary_hexagram": {
                "upper_trigram": upper_trigram["name"],
                "lower_trigram": lower_trigram["name"],
                "moving_line": moving_line
            },
            "body_function": {
                "body_trigram": body_trigram["name"],
                "function_trigram": function_trigram["name"],
                "body_element": body_trigram["element"],
                "function_element": function_trigram["element"],
                "body_position": body_pos,
                "interaction": interaction
            },
            "mutual_hexagram": {
                "upper_trigram": TRIGRAMS[mutual_upper_idx]["name"],
                "lower_trigram": TRIGRAMS[mutual_lower_idx]["name"]
            },
            "transformed_hexagram": {
                "upper_trigram": TRIGRAMS[transformed_upper_idx]["name"],
                "lower_trigram": TRIGRAMS[transformed_lower_idx]["name"]
            },
            **kwargs
        }
        
        return EngineChartResult(
            engine_name=self.engine_name,
            system_type=self.system_type,
            chart_data=chart_data,
        )

    def calculate_from_time(self, year: int, month: int, day: int, hour: int) -> EngineChartResult:
        upper_idx, lower_idx, moving_line = mei_hua_hexagram_from_time(year, month, day, hour)
        return self._build_result(upper_idx, lower_idx, moving_line, method="time", input={"year": year, "month": month, "day": day, "hour": hour})

    def calculate_from_numbers(self, upper_num: int, lower_num: int, moving_num: Optional[int] = None) -> EngineChartResult:
        upper_idx = (upper_num % 8) or 8
        lower_idx = (lower_num % 8) or 8
        if moving_num is None:
            moving_line = ((upper_num + lower_num) % 6) or 6
        else:
            moving_line = (moving_num % 6) or 6
            
        return self._build_result(upper_idx, lower_idx, moving_line, method="numbers", input={"upper_num": upper_num, "lower_num": lower_num, "moving_num": moving_num})

    def calculate(self, *args, **kwargs) -> EngineChartResult:
        if len(args) == 4:
            return self.calculate_from_time(*args)
        if len(args) in (2, 3):
            return self.calculate_from_numbers(*args)
        if "year" in kwargs:
            return self.calculate_from_time(**kwargs)
        if "upper_num" in kwargs:
            return self.calculate_from_numbers(**kwargs)
        raise ValueError("Invalid parameters for MeiHuaEngine")

