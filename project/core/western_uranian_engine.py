"""
Western Tropical & Uranian Astrology (โหราศาสตร์สากล & ยูเรเนียน) Core Engine
=============================================================================
Deterministic calculations for:
- Western Tropical Planetary Aspects (Conjunction 0°, Sextile 60°, Square 90°, Trine 120°, Opposition 180°)
- Uranian 8 Transneptunian Planets (TNPs: Cupido, Hades, Zeus, Kronos, Apollon, Admetos, Vulkanus, Poseidon)
- Uranian Sensitive Midpoint Formula (A + B - C)
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from project.core.base_engine import AbstractAstrologyEngine, EngineChartResult

WESTERN_ZODIAC_SIGNS = [
    "Aries (เมษ)", "Taurus (พฤษภ)", "Gemini (เมถุน)", "Cancer (กรกฎ)",
    "Leo (สิงห์)", "Virgo (กันย์)", "Libra (ตุลย์)", "Scorpio (พิจิก)",
    "Sagittarius (ธนู)", "Capricorn (มังกร)", "Aquarius (กุมภ์)", "Pisces (มีน)"
]

URANIAN_TNPS = {
    "Cupido (คิวปิโด)": {"symbol": "Cu", "speed_per_year": 0.95, "meaning": "Family, Marriage, Associations"},
    "Hades (ฮาเดส)": {"symbol": "Ha", "speed_per_year": 0.80, "meaning": "Past, Secrets, Antiquity, Poverty"},
    "Zeus (ซูส)": {"symbol": "Ze", "speed_per_year": 0.73, "meaning": "Leadership, Creation, Fire, Targets"},
    "Kronos (โครโนส)": {"symbol": "Kr", "speed_per_year": 0.69, "meaning": "Authority, Bureaucracy, High Quality"},
    "Apollon (อะพอลลอน)": {"symbol": "Ap", "speed_per_year": 0.63, "meaning": "Expansion, Success, Multiplicity, Science"},
    "Admetos (แอดเมตอส)": {"symbol": "Ad", "speed_per_year": 0.58, "meaning": "Depth, Obstacle, Raw Material, Endure"},
    "Vulkanus (วัลคานุส)": {"symbol": "Vu", "speed_per_year": 0.54, "meaning": "Mighty Power, Energy, Supreme Force"},
    "Poseidon (โพไซดอน)": {"symbol": "Po", "speed_per_year": 0.50, "meaning": "Enlightenment, Wisdom, Spirit, Truth"}
}

ASPECT_TYPES = [
    ("Conjunction (กุม)", 0, 8),
    ("Sextile (โยค)", 60, 6),
    ("Square (ฉาก)", 90, 8),
    ("Trine (ตรีโกณ)", 120, 8),
    ("Opposition (เล็ง)", 180, 8)
]


class WesternUranianEngine(AbstractAstrologyEngine):
    """Core Western & Uranian Astrology calculation engine."""

    @property
    def engine_name(self) -> str:
        return "Western & Uranian Astrology Engine"

    @property
    def system_type(self) -> str:
        return "western_astro"

    def resolve_zodiac_sign(self, degree: float) -> tuple[str, float]:
        """Resolve celestial longitude (0-360°) to Zodiac Sign & in-sign degree."""
        deg = degree % 360.0
        sign_idx = int(deg // 30)
        in_sign_deg = deg % 30.0
        return WESTERN_ZODIAC_SIGNS[sign_idx], in_sign_deg

    def calculate_aspects(self, planet_positions: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Calculate Planetary Aspects between pairs of planets.
        """
        aspects = []
        planet_names = list(planet_positions.keys())
        for i in range(len(planet_names)):
            for j in range(i + 1, len(planet_names)):
                p1, p2 = planet_names[i], planet_names[j]
                deg1, deg2 = planet_positions[p1], planet_positions[p2]
                diff = abs(deg1 - deg2) % 360.0
                if diff > 180.0:
                    diff = 360.0 - diff

                for aspect_name, exact_angle, orb in ASPECT_TYPES:
                    actual_orb = abs(diff - exact_angle)
                    if actual_orb <= orb:
                        aspects.append({
                            "planet_1": p1,
                            "planet_2": p2,
                            "aspect_name": aspect_name,
                            "exact_angle": exact_angle,
                            "actual_orb_deg": round(actual_orb, 2)
                        })
        return aspects

    def calculate_uranian_tnps(self, year: int, doy: int) -> Dict[str, float]:
        """
        Calculate celestial longitudes of 8 Transneptunian Planets (TNPs).
        """
        years_elapsed = (year - 2000) + doy / 365.25
        base_positions_2000 = {
            "Cupido (คิวปิโด)": 245.0,
            "Hades (ฮาเดส)": 288.0,
            "Zeus (ซูส)": 155.0,
            "Kronos (โครโนส)": 62.0,
            "Apollon (อะพอลลอน)": 182.0,
            "Admetos (แอดเมตอส)": 128.0,
            "Vulkanus (วัลคานุส)": 210.0,
            "Poseidon (โพไซดอน)": 232.0
        }

        tnp_positions = {}
        for name, base_deg in base_positions_2000.items():
            speed = URANIAN_TNPS[name]["speed_per_year"]
            deg = (base_deg + speed * years_elapsed) % 360.0
            tnp_positions[name] = round(deg, 2)
        return tnp_positions

    def calculate_uranian_midpoint(self, deg_a: float, deg_b: float, deg_c: float) -> tuple[float, str]:
        """
        Calculate Uranian Sensitive Midpoint Formula: A + B - C (Sensitive Point).
        """
        sensitive_deg = (deg_a + deg_b - deg_c) % 360.0
        sign, in_deg = self.resolve_zodiac_sign(sensitive_deg)
        return round(sensitive_deg, 2), f"{sign} {in_deg:.2f}°"

    def calculate_chart(self, year: int, month: int, day: int, hour: int) -> Dict[str, Any]:
        """
        Calculate complete Western Tropical & Uranian Astrology Chart.
        """
        doy = (month - 1) * 30 + day
        sun_deg = (280.460 + 0.9856474 * doy) % 360.0
        moon_deg = (sun_deg + 13.176 * doy) % 360.0
        mars_deg = (sun_deg / 1.88) % 360.0
        jupiter_deg = (sun_deg / 11.86) % 360.0
        saturn_deg = (sun_deg / 29.46) % 360.0

        planets = {
            "Sun (อาทิตย์)": sun_deg,
            "Moon (จันทร์)": moon_deg,
            "Mars (อังคาร)": mars_deg,
            "Jupiter (พฤหัสบดี)": jupiter_deg,
            "Saturn (เสาร์)": saturn_deg,
        }

        aspects = self.calculate_aspects(planets)
        tnps = self.calculate_uranian_tnps(year, doy)
        
        # Example Uranian Midpoint: Sun + Jupiter - Saturn (Career Target Point)
        mid_deg, mid_str = self.calculate_uranian_midpoint(sun_deg, jupiter_deg, saturn_deg)

        raw = {
            "engine": "WesternUranianEngine",
            "datetime": f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:00",
            "planets_tropical": {p: f"{self.resolve_zodiac_sign(d)[0]} {self.resolve_zodiac_sign(d)[1]:.2f}°" for p, d in planets.items()},
            "planetary_aspects": aspects,
            "uranian_tnps": tnps,
            "uranian_midpoint_formula": {
                "formula": "Sun + Jupiter - Saturn (Career Target Axis)",
                "sensitive_longitude_deg": mid_deg,
                "zodiac_position": mid_str
            }
        }
        return EngineChartResult(
            engine_name=self.engine_name,
            system_type=self.system_type,
            chart_data=raw,
        )

    def calculate(self, *args, **kwargs) -> EngineChartResult:
        return self.calculate_chart(*args, **kwargs)


if __name__ == "__main__":
    wu = WesternUranianEngine()
    chart = wu.calculate_chart(1990, 5, 15, 14)
    print(chart)
