"""
San He Feng Shui (三合風水) Core Calculation Engine
==================================================
Deterministic calculation of San He 24 Mountains & 12 Life Stages Water Methods:
- 24 Mountains (二十四山) direction resolution
- 12 Life Stages Water Method (十二長生水法: 生沐冠臨旺衰病死墓絕胎養)
- 4 Water Bureau San He Formations (四大水局: 申子辰水局, 亥卯未木局, 寅午戌火局, 巳酉丑金局)
- Dragon, Sitting, Facing, Water Entry & Exit (龍穴砂水向) Harmony Evaluation
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

STAGES_12 = [
    "長生", "沐浴", "冠帶", "臨官", "帝旺", "衰", 
    "病", "死", "墓", "絕", "胎", "養"
]

STAGE_AUSPICIOUSNESS = {
    "長生": "大吉 (Source of Life/Wealth - 宜來水)",
    "沐浴": "凶 (Leakage/Romance Scandal - 忌來水)",
    "冠帶": "吉 (Honor/Promotion - 宜來水)",
    "臨官": "大吉 (Prosperity/Official - 宜來水)",
    "帝旺": "極吉 (Peak Wealth/Glory - 宜來水)",
    "衰": "平 (Decline Begins)",
    "病": "凶 (Illness/Blockage - 忌來水)",
    "死": "大凶 (Termination - 忌來水)",
    "墓": "吉 (Treasure Storage/Exit - 宜去水/水口)",
    "絕": "大凶 (Extinction - 忌來水)",
    "胎": "平 (Incubation)",
    "養": "吉 (Nurturing/Growth - 宜來水)"
}


class SanHeEngine(AbstractAstrologyEngine):
    """Core San He Feng Shui calculation engine."""

    @property
    def engine_name(self) -> str:
        return "San He Feng Shui Engine"

    @property
    def system_type(self) -> str:
        return "feng_shui"

    def resolve_mountain(self, degree: float) -> int:
        """Resolve degree (0-360) to 24 Mountain Index (0-23)."""
        if HAS_RUST:
            return san_he_resolve_mountain(degree)
        deg = (degree % 360.0 + 360.0) % 360.0
        shifted = (deg + 22.5) % 360.0
        return int(shifted // 15) % 24

    def water_method(self, sitting_idx: int, water_exit_idx: int) -> list[str]:
        """
        Calculate Water Method 12 Life Stage for sitting mountain and water exit.
        """
        if HAS_RUST:
            return san_he_water_method(sitting_idx, water_exit_idx)
        diff = (water_exit_idx + 24 - sitting_idx) % 24
        stage_idx = diff // 2
        return [
            STAGES_12[stage_idx],
            f"Sitting: {MOUNTAINS_24[sitting_idx]}",
            f"Water Exit: {MOUNTAINS_24[water_exit_idx]}"
        ]

    def evaluate_harmony(self, sitting: str, water: str) -> str:
        """Evaluate San He elemental harmony between Sitting mountain and Water branch."""
        for combo, element in SAN_HE_COMBINATIONS.items():
            if sitting in combo and water in combo:
                return f"Harmonious {element} formation"
        return "No San He formation"

    def calculate_12_stages_map(self, sitting_idx: int) -> list[dict[str, Any]]:
        """Compute full 12 life stages water map around all 24 mountains for given sitting."""
        stages_map = []
        for i in range(12):
            mountain_idx = (sitting_idx + i * 2) % 24
            mountain_name = MOUNTAINS_24[mountain_idx]
            stage_name = STAGES_12[i]
            stages_map.append({
                "stage": stage_name,
                "mountain": mountain_name,
                "auspiciousness": STAGE_AUSPICIOUSNESS.get(stage_name, "平")
            })
        return stages_map

    def calculate(
        self,
        sitting_degree: float,
        facing_degree: float | None = None,
        water_entry_degree: float | None = None,
        water_exit_degree: float | None = None
    ) -> EngineChartResult:
        """
        Calculate complete San He Feng Shui chart.
        """
        sitting_idx = self.resolve_mountain(sitting_degree)
        sitting_mountain = MOUNTAINS_24[sitting_idx]
        
        if facing_degree is None:
            facing_degree = (sitting_degree + 180) % 360.0
        facing_idx = self.resolve_mountain(facing_degree)
        facing_mountain = MOUNTAINS_24[facing_idx]

        water_method_res = []
        harmony = "N/A"
        san_he_formation = "None"
        exit_mountain = MOUNTAINS_24[(sitting_idx + 8) % 24]
        
        if water_exit_degree is not None:
            exit_idx = self.resolve_mountain(water_exit_degree)
            water_method_res = self.water_method(sitting_idx, exit_idx)
            exit_mountain = MOUNTAINS_24[exit_idx]
            harmony = self.evaluate_harmony(sitting_mountain, exit_mountain)
            for combo, name in SAN_HE_COMBINATIONS.items():
                if exit_mountain in combo:
                    san_he_formation = combo

        stages_map = self.calculate_12_stages_map(sitting_idx)
        
        raw = {
            "sitting_degree": sitting_degree,
            "facing_degree": facing_degree,
            "sitting_mountain": sitting_mountain,
            "facing_mountain": facing_mountain,
            "water_exit": exit_mountain,
            "san_he_formation": san_he_formation,
            "water_method": water_method_res,
            "harmony_assessment": harmony,
            "twelve_stages_map": stages_map
        }
        
        return EngineChartResult(
            engine_name=self.engine_name,
            system_type=self.system_type,
            chart_data=raw,
        )


if __name__ == "__main__":
    sh = SanHeEngine()
    print(sh.calculate(0.0, water_exit_degree=120.0))
