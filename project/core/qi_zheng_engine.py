"""
Qi Zheng Si Yu (七政四餘) Engine
"""

from typing import Any
from datetime import datetime
from project.core.base_engine import AbstractAstrologyEngine, EngineChartResult
from project.core.swiss_ephemeris import calculate_qi_zheng_si_yu

LUNAR_MANSIONS = [
    "角", "亢", "氐", "房", "心", "尾", "箕",  # Eastern Dragon
    "斗", "牛", "女", "虛", "危", "室", "壁",  # Northern Tortoise
    "奎", "婁", "胃", "昴", "畢", "觜", "參",  # Western Tiger
    "井", "鬼", "柳", "星", "張", "翼", "軫"   # Southern Bird
]

class QiZhengSiYuEngine(AbstractAstrologyEngine):
    @property
    def engine_name(self) -> str:
        return "Qi Zheng Si Yu Engine"

    @property
    def system_type(self) -> str:
        return "chinese_astrology"

    def get_lunar_mansion(self, degree: float) -> str:
        idx = int((degree % 360.0) / (360.0 / 28.0))
        return LUNAR_MANSIONS[idx]

    def calculate(self, year: int, month: int, day: int, hour: int = 12, longitude: float = 100.0, latitude: float = 13.0) -> EngineChartResult:
        dt = datetime(year, month, day, hour)
        ephemeris_data = calculate_qi_zheng_si_yu(dt, longitude, latitude)
        planets_data = ephemeris_data.get("planets_longitudes", {})
        
        planets = {}
        shadow_stars = {}
        
        planet_keys = ["日 (Sun)", "月 (Moon)", "木 (Jupiter)", "火 (Mars)", "土 (Saturn)", "金 (Venus)", "水 (Mercury)"]
        shadow_keys = ["羅睺 (Rahu)", "計都 (Ketu)", "月孛 (Yuebei)", "紫氣 (Ziqi)"]
        
        for k in planet_keys:
            if k in planets_data:
                planets[k] = planets_data[k]
                
        for k in shadow_keys:
            if k in planets_data:
                shadow_stars[k] = planets_data[k]
                
        ayanamsa_degrees = 24.0 # Dummy static for pure deterministic testing without swisseph sidereal
        
        lunar_mansions = {
            k: self.get_lunar_mansion((v - ayanamsa_degrees) % 360.0) 
            for k, v in {**planets, **shadow_stars}.items()
        }
        
        raw = {
            "datetime": dt.isoformat(),
            "coordinates": {"longitude": longitude, "latitude": latitude},
            "planets": planets,
            "shadow_stars": shadow_stars,
            "lunar_mansions": lunar_mansions,
            "ayanamsa_degrees": ayanamsa_degrees,
            "source": ephemeris_data.get("source", "unknown")
        }
        
        return EngineChartResult(
            engine_name=self.engine_name,
            system_type=self.system_type,
            chart_data=raw,
        )
