"""
Tai Yi Shen Shu (太乙神數) Core Calculation Engine
==================================================
Deterministic calculation of Tai Yi charts:
- Tai Yi Accumulated Years (太乙積年)
- Heaven/Earth Plate (天地盤)
- 16-Path Tai Yi Star positioning (十六神道宮位)
- 8-Direction Strategic Assessment (八方勝負評判)
- Battle/Strategy Matrix Calculation (主將/客將/主參/客參 主客算陣)
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

PATH_16_NAMES = [
    "子 (1)", "丑 (2)", "艮 (3)", "寅 (4)",
    "卯 (5)", "辰 (6)", "巽 (7)", "巳 (8)",
    "午 (9)", "未 (10)", "坤 (11)", "申 (12)",
    "酉 (13)", "戌 (14)", "乾 (15)", "亥 (16)"
]

PATH_16_DIRECTIONS = [
    "正北 (North)", "東北偏北 (NNE)", "東北 (Northeast)", "東北偏東 (ENE)",
    "正東 (East)", "東南偏東 (ESE)", "東南 (Southeast)", "東南偏南 (SSE)",
    "正南 (South)", "西南偏南 (SSW)", "西南 (Southwest)", "西南偏西 (WSW)",
    "正西 (West)", "西北偏西 (WNW)", "西北 (Northwest)", "西北偏北 (NNW)"
]

PATH_16_ELEMENTS = [
    "Water", "Earth", "Earth", "Wood",
    "Wood", "Earth", "Wood", "Fire",
    "Fire", "Earth", "Earth", "Metal",
    "Metal", "Earth", "Metal", "Water"
]

STRATEGIC_OUTCOMES = ["吉", "凶", "平", "大吉", "大凶", "小吉", "小凶", "半吉"]


class TaiYiEngine(AbstractAstrologyEngine):
    """Core Tai Yi Shen Shu engine with 16-path palaces & strategy battle matrix."""

    @property
    def engine_name(self) -> str:
        return "Tai Yi Shen Shu Engine"

    @property
    def system_type(self) -> str:
        return "san_shi"

    def calculate_battle_matrix(self, accumulated_years: int, star_palace: int) -> dict[str, Any]:
        """
        Calculate Tai Yi Host/Guest battle and strategy matrix:
        - Host Calculation (主算) & Host General (主大將)
        - Guest Calculation (客算) & Guest General (客大將)
        - Host Assistant (主參) & Guest Assistant (客參)
        - Battle Advantage Assessment (勝負評判: 主勝/客勝/和局)
        """
        # Host calculation base from accumulated years and palace
        host_count = ((accumulated_years * 3 + star_palace + 1) % 36) + 1
        guest_count = ((accumulated_years * 5 + star_palace + 7) % 36) + 1

        # Host and Guest Generals position (1-16 path palace index)
        host_general_pos = (star_palace + (host_count % 16)) % 16
        guest_general_pos = (star_palace + (guest_count % 16)) % 16

        host_assistant_pos = (host_general_pos + 4) % 16
        guest_assistant_pos = (guest_general_pos + 4) % 16

        # Determine battle advantage based on parity and magnitude of counts
        if host_count > guest_count and (host_count % 2 == 1):
            battle_outcome = "主勝 (Host Advantage)"
            advantage_score = 0.85
        elif guest_count > host_count and (guest_count % 2 == 1):
            battle_outcome = "客勝 (Guest Advantage)"
            advantage_score = 0.80
        elif host_count == guest_count:
            battle_outcome = "和局 (Stalemate / Balanced)"
            advantage_score = 0.50
        else:
            battle_outcome = "主勝 (Host Advantage)" if (host_count >= guest_count) else "客勝 (Guest Advantage)"
            advantage_score = 0.65

        return {
            "host_calculation": host_count,
            "guest_calculation": guest_count,
            "host_general": PATH_16_NAMES[host_general_pos],
            "host_general_palace": host_general_pos + 1,
            "guest_general": PATH_16_NAMES[guest_general_pos],
            "guest_general_palace": guest_general_pos + 1,
            "host_assistant": PATH_16_NAMES[host_assistant_pos],
            "guest_assistant": PATH_16_NAMES[guest_assistant_pos],
            "battle_outcome": battle_outcome,
            "advantage_score": advantage_score,
            "tactical_guidance": "宜固守主陣，以逸待勞" if "主勝" in battle_outcome else "宜先發制人，出奇制勝"
        }

    def calculate_16_palaces(self, star_palace: int) -> list[dict[str, Any]]:
        """Construct detailed 16-path palaces list with occupants."""
        palaces = []
        for i in range(16):
            is_active = (i == (star_palace % 16))
            palaces.append({
                "palace_number": i + 1,
                "palace_name": PATH_16_NAMES[i],
                "direction": PATH_16_DIRECTIONS[i],
                "element": PATH_16_ELEMENTS[i],
                "is_tai_yi_star": is_active,
                "star_occupant": "太乙星 (Tai Yi)" if is_active else "無 (None)"
            })
        return palaces

    def calculate_chart(self, year: int, month: int, day: int, hour: int) -> dict[str, Any]:
        """
        Calculate complete Tai Yi Shen Shu chart for given date & time.
        """
        accumulated_years = tai_yi_accumulated_years(year)
        
        # 16-Path Tai Yi Star positioning
        star_palace = tai_yi_star_palace(accumulated_years)
        
        # Heaven/Earth Plate (天地盤) - 9-palace grid rotation
        earth_plate = [((i + accumulated_years) % 9) + 1 for i in range(9)]
        heaven_plate = [((i + accumulated_years * 2) % 9) + 1 for i in range(9)]
        
        # 8-Direction Strategic Assessment
        strategic_assessment = STRATEGIC_OUTCOMES[star_palace % 8]
        
        # Tai Yi Number (太乙數) - Core cosmic number derivation
        tai_yi_number = (year * month * day * hour + accumulated_years) % 10000

        cycle_info = {
            "epoch_offset": 4,
            "cycle_length": 72,
            "current_cycle_year": accumulated_years + 1
        }

        # Enriched 16 Palaces & Strategy Matrix
        palaces_16 = self.calculate_16_palaces(star_palace)
        battle_matrix = self.calculate_battle_matrix(accumulated_years, star_palace)

        raw = {
            "engine": "TaiYiEngine",
            "datetime": f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:00",
            "tai_yi_number": tai_yi_number,
            "accumulated_years": accumulated_years,
            "heaven_plate": heaven_plate,
            "earth_plate": earth_plate,
            "star_palace": star_palace,
            "strategic_assessment": strategic_assessment,
            "cycle_info": cycle_info,
            "palaces_16": palaces_16,
            "strategy_matrix": battle_matrix,
            "battle_matrix": battle_matrix
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
