"""
Tai Yi Shen Shu (太乙神數) Core Calculation Engine
==================================================
Deterministic calculation of Tai Yi charts:
- Tai Yi Accumulated Years (太乙積年)
- Heaven/Earth Plate (天地盤)
- 16-Path Tai Yi Star positioning
- 8-Direction Strategic Assessment
"""

from typing import Any

from project.core.base_engine import AbstractAstrologyEngine, EngineChartResult

# Try to import rust core, fallback to pure python for calculations if needed
try:
    from rust_core import tai_yi_accumulated_years, tai_yi_star_palace
except ImportError:
    def tai_yi_accumulated_years(year: int) -> int:
        return (year - 4) % 72
        
    def tai_yi_star_palace(accumulated: int) -> int:
        return accumulated % 16


class TaiYiEngine(AbstractAstrologyEngine):
    """Core Tai Yi Shen Shu engine."""

    @property
    def engine_name(self) -> str:
        return "Tai Yi Shen Shu Engine"

    @property
    def system_type(self) -> str:
        return "san_shi"

    def calculate_chart(self, year: int, month: int, day: int, hour: int) -> dict[str, Any]:
        """
        Calculate Tai Yi Shen Shu chart for given date & time.
        """
        accumulated_years = tai_yi_accumulated_years(year)
        
        # 16-Path Tai Yi Star positioning
        star_palace = tai_yi_star_palace(accumulated_years)
        
        # Heaven/Earth Plate (天地盤) - 9-palace grid rotation
        # Simplified deterministic generation based on accumulated years
        earth_plate = [((i + accumulated_years) % 9) + 1 for i in range(9)]
        heaven_plate = [((i + accumulated_years * 2) % 9) + 1 for i in range(9)]
        
        # 8-Direction Strategic Assessment
        strategic_outcomes = ["吉", "凶", "平", "大吉", "大凶", "小吉", "小凶", "半吉"]
        strategic_assessment = strategic_outcomes[star_palace % 8]
        
        # Tai Yi Number (太乙數) - Core cosmic number derivation
        tai_yi_number = (year * month * day * hour + accumulated_years) % 10000

        cycle_info = {
            "epoch_offset": 4,
            "cycle_length": 72,
            "current_cycle_year": accumulated_years + 1
        }

        raw = {
            "engine": "TaiYiEngine",
            "datetime": f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:00",
            "tai_yi_number": tai_yi_number,
            "accumulated_years": accumulated_years,
            "heaven_plate": heaven_plate,
            "earth_plate": earth_plate,
            "star_palace": star_palace,
            "strategic_assessment": strategic_assessment,
            "cycle_info": cycle_info
        }
        
        return EngineChartResult(
            engine_name=self.engine_name,
            system_type=self.system_type,
            chart_data=raw,
        )

    def calculate(self, *args, **kwargs) -> EngineChartResult:
        """
        Main entry point. Arguments should be year, month, day, hour.
        """
        return self.calculate_chart(*args, **kwargs)

if __name__ == "__main__":
    ty = TaiYiEngine()
    chart = ty.calculate(2026, 8, 15, 12)
    print(chart)
