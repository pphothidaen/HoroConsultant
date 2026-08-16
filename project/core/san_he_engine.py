"""
San He Feng Shui Engine
"""
from typing import Any
from project.core.base_engine import AbstractAstrologyEngine, EngineChartResult

try:
    from rust_core import san_he_resolve_mountain, san_he_water_method
    HAS_RUST = True
except ImportError:
    HAS_RUST = False

MOUNTAINS_24 = [
    "壬", "子", "癸", "丑", "艮", "寅", "甲", "卯",
    "乙", "辰", "巽", "巳", "丙", "午", "丁", "未",
    "坤", "申", "庚", "酉", "辛", "戌", "乾", "亥"
]

SAN_HE_COMBINATIONS = {
    "申子辰": "Water",
    "亥卯未": "Wood",
    "寅午戌": "Fire",
    "巳酉丑": "Metal",
}

class SanHeEngine(AbstractAstrologyEngine):
    @property
    def engine_name(self) -> str:
        return "San He Feng Shui Engine"

    @property
    def system_type(self) -> str:
        return "feng_shui"

    def resolve_mountain(self, degree: float) -> int:
        if HAS_RUST:
            return san_he_resolve_mountain(degree)
        deg = (degree % 360.0 + 360.0) % 360.0
        shifted = (deg + 22.5) % 360.0
        return int(shifted // 15) % 24

    def water_method(self, sitting_idx: int, water_exit_idx: int) -> list[str]:
        if HAS_RUST:
            return san_he_water_method(sitting_idx, water_exit_idx)
        stages = [
            "長生", "沐浴", "冠帶", "臨官", "帝旺", "衰", 
            "病", "死", "墓", "絕", "胎", "養"
        ]
        diff = (water_exit_idx + 24 - sitting_idx) % 24
        stage_idx = diff // 2
        return [
            stages[stage_idx],
            f"Sitting: {MOUNTAINS_24[sitting_idx]}",
            f"Water Exit: {MOUNTAINS_24[water_exit_idx]}"
        ]

    def evaluate_harmony(self, sitting: str, water: str) -> str:
        for combo, element in SAN_HE_COMBINATIONS.items():
            if sitting in combo and water in combo:
                return f"Harmonious {element} formation"
        return "No San He formation"

    def calculate(self, sitting_degree: float, facing_degree: float = None, water_entry_degree: float = None, water_exit_degree: float = None) -> EngineChartResult:
        sitting_idx = self.resolve_mountain(sitting_degree)
        sitting_mountain = MOUNTAINS_24[sitting_idx]
        
        if facing_degree is None:
            facing_degree = (sitting_degree + 180) % 360.0
        facing_idx = self.resolve_mountain(facing_degree)
        facing_mountain = MOUNTAINS_24[facing_idx]

        water_method_res = []
        harmony = "N/A"
        san_he_formation = "None"
        
        if water_exit_degree is not None:
            exit_idx = self.resolve_mountain(water_exit_degree)
            water_method_res = self.water_method(sitting_idx, exit_idx)
            exit_mountain = MOUNTAINS_24[exit_idx]
            harmony = self.evaluate_harmony(sitting_mountain, exit_mountain)
            for combo, name in SAN_HE_COMBINATIONS.items():
                if exit_mountain in combo:
                    san_he_formation = combo
        
        raw = {
            "sitting_degree": sitting_degree,
            "facing_degree": facing_degree,
            "sitting_mountain": sitting_mountain,
            "facing_mountain": facing_mountain,
            "water_exit": exit_mountain if water_exit_degree is not None else MOUNTAINS_24[(sitting_idx + 8) % 24],
            "san_he_formation": san_he_formation,
            "water_method": water_method_res,
            "harmony_assessment": harmony
        }
        
        return EngineChartResult(
            engine_name=self.engine_name,
            system_type=self.system_type,
            chart_data=raw,
        )
