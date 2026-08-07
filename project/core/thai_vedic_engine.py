"""
Thai & Vedic Astrology (โหราศาสตร์ไทยสุริยยาตร์ & ภารตวิทยา Jyotish) Core Engine
================================================================================
Deterministic calculations for:
- Thai Suriyayart/Nirayana 12 Zodiac Houses & Lagna (ลัคนา)
- Maha Thaksa (มหาทักษา 8 เทวดาเสวยอายุ: บริวาร, อายุ, เดช, ศรี, มูละ, อุตสาหะ, มนตรี, กาลกิณี)
- Vedic 27 Nakshatras (นักษัตร 27 ดารา) & Vimshottari Dasha periods
"""

from typing import Dict, List, Any, Optional
from datetime import datetime

ZODIAC_THAI_NAMES = [
    "เมษ", "พฤษภ", "เมถุน", "กรกฎ", "สิงห์", "กันย์",
    "ตุลย์", "พิจิก", "ธนู", "มังกร", "กุมภ์", "มีน"
]

THAKSA_STEPS = ["บริวาร", "อายุ", "เดช", "ศรี", "มูละ", "อุตสาหะ", "มนตรี", "กาลกิณี"]
PLANET_DAYS = ["อาทิตย์ (1)", "จันทร์ (2)", "อังคาร (3)", "พุธ (4)", "เสาร์ (7)", "พฤหัสบดี (5)", "ราหู (8)", "ศุกร์ (6)"]
DASHA_YEARS = {"อาทิตย์": 6, "จันทร์": 10, "อังคาร": 7, "ราหู": 18, "พฤหัสบดี": 16, "เสาร์": 19, "พุธ": 17, "เกตุ": 7, "ศุกร์": 20}

NAKSHATRAS_27 = [
    "อัศวินี (Ashwini)", "ภรณี (Bharani)", "กฤตติกา (Krittika)", "โรหิณี (Rohini)",
    "มฤคศิระ (Mrigashira)", "อาร์ทรา (Ardra)", "ปุนัพพสุ (Punarvasu)", "ปุษยะ (Pushya)",
    "อาศเลษา (Ashlesha)", "มาฆะ (Magha)", "บุรพผลคุนี (Purva Phalguni)", "อุตตรผลคุนี (Uttara Phalguni)",
    "หัสตะ (Hasta)", "จิตรา (Chitra)", "สวาตี (Swati)", "วิศาขา (Vishakha)",
    "อนุราธะ (Anuradha)", "เชษฐา (Jyeshtha)", "มูละ (Mula)", "บุรพษาฒ (Purva Ashadha)",
    "อุตตราษาฒ (Uttara Ashadha)", "ศรวณะ (Shravana)", "ธนิษฐา (Dhanishta)", "ศตภิษัจ (Shatabhisha)",
    "บุรพภัทรบท (Purva Bhadrapada)", "อุตตรภัทรบท (Uttara Bhadrapada)", "เรวดี (Revati)"
]


class ThaiVedicEngine:
    """Core Thai & Vedic Astrology calculation engine."""

    def calculate_lagna(self, birth_hour: int, birth_month: int) -> tuple[str, int]:
        """
        Calculate Thai Suriyayart Lagna (ลัคนา) based on birth hour & month.
        Sun moves ~1 zodiac house per month (starts Aries in April).
        Lagna rotates 1 house every 2 hours starting at sunrise (~06:00).
        """
        # Sun house index (0 = Aries, April = Month 4)
        sun_house_idx = (birth_month - 4) % 12
        hour_offset = ((birth_hour - 6) // 2) % 12
        lagna_idx = (sun_house_idx + hour_offset) % 12
        return ZODIAC_THAI_NAMES[lagna_idx], lagna_idx

    def calculate_thaksa(self, day_of_week: int) -> Dict[str, str]:
        """
        Calculate Maha Thaksa (มหาทักษา) based on Day of Week (0 = Sunday, 1 = Monday ... 6 = Saturday).
        Sequence order starting from birth day planet.
        """
        # Day index mapping: Sun=0, Mon=1, Tue=2, Wed=3, Sat=4, Thu=5, Rahu=6, Fri=7
        start_planet_idx = day_of_week % 8
        thaksa_map = {}
        for i, step in enumerate(THAKSA_STEPS):
            planet = PLANET_DAYS[(start_planet_idx + i) % 8]
            thaksa_map[step] = planet
        return thaksa_map

    def calculate_nakshatra(self, moon_degree: float) -> tuple[str, int, int]:
        """
        Calculate 27 Nakshatras (นักษัตร) and Pada (4 Padas per Nakshatra).
        Each Nakshatra spans 13°20' (13.3333°).
        """
        nak_span = 13.333333
        nak_idx = int(moon_degree // nak_span) % 27
        rem_deg = moon_degree % nak_span
        pada = int(rem_deg // 3.333333) + 1
        return NAKSHATRAS_27[nak_idx], nak_idx + 1, min(4, pada)

    def calculate_chart(self, year: int, month: int, day: int, hour: int, day_of_week: int = 0) -> Dict[str, Any]:
        """
        Calculate complete Thai & Vedic Astrology Chart.
        """
        lagna_name, lagna_idx = self.calculate_lagna(hour, month)
        thaksa = self.calculate_thaksa(day_of_week)
        
        # Approximate Moon degree for Nakshatra calculation
        doy = (month - 1) * 30 + day
        approx_moon_deg = (doy * 13.176) % 360.0
        nak_name, nak_num, pada = self.calculate_nakshatra(approx_moon_deg)

        # Vimshottari Dasha planet based on Nakshatra index % 9
        dasha_planets = ["กฤตติกา (Sun)", "โรหิณี (Moon)", "มฤคศิระ (Mars)", "อาร์ทรา (Rahu)", "ปุนัพพสุ (Jupiter)", "ปุษยะ (Saturn)", "อาศเลษา (Mercury)", "มาฆะ (Ketu)", "บุรพผลคุนี (Venus)"]
        main_dasha = dasha_planets[(nak_num - 1) % 9]

        return {
            "engine": "ThaiVedicEngine",
            "datetime": f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:00",
            "thai_lagna": f"ราศี{lagna_name} (House {lagna_idx+1})",
            "maha_thaksa": thaksa,
            "kalakini_planet": thaksa.get("กาลกิณี", ""),
            "sri_planet": thaksa.get("ศรี", ""),
            "vedic_nakshatra": {
                "name": nak_name,
                "number": nak_num,
                "pada": pada,
                "moon_degree": round(approx_moon_deg, 2)
            },
            "vimshottari_dasha": main_dasha
        }


if __name__ == "__main__":
    tv = ThaiVedicEngine()
    chart = tv.calculate_chart(1990, 5, 15, 14, day_of_week=2)
    print(chart)
