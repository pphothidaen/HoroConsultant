"""
Numerology & Satta-Lek (สัตตเลข 7 ฐาน & เลขศาสตร์ประยุกต์) Core Engine
========================================================================
Deterministic calculations for:
- Thai Satta-Lek 7-Base 4-Row Calculation (7 ฐาน 4 แถว: ฐานวัน, ฐานเดือน, ฐานปี, ฐานผลรวม)
- Chaldean & Pythagorean Numerology Scoring (วิเคราะห์เบอร์โทรศัพท์, ทะเบียนรถ, ชื่อ-นามสกุล)
"""

from typing import Dict, List, Any, Optional
from project.core.base_engine import AbstractAstrologyEngine, EngineChartResult

SATTA_LEK_HOUSES = ["อัตตา", "หินะ", "ธนัง", "ปิตา", "มาตา", "โภคา", "มัชฌิมา"]

# Chaldean Letter to Number Value Mapping
CHALDEAN_MAP = {
    # English
    'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 8, 'G': 3, 'H': 5, 'I': 1,
    'J': 1, 'K': 2, 'L': 3, 'M': 4, 'N': 5, 'O': 7, 'P': 8, 'Q': 1, 'R': 2,
    'S': 3, 'T': 4, 'U': 6, 'V': 6, 'W': 6, 'X': 5, 'Y': 1, 'Z': 7,
    # Thai Consonants & Vowels
    'ก': 1, 'ข': 2, 'ค': 3, 'ฆ': 4, 'ง': 5, 'จ': 6, 'ฉ': 7, 'ช': 8, 'ซ': 9,
    'ฌ': 2, 'ญ': 4, 'ฎ': 1, 'ฏ': 8, 'ฐ': 9, 'ฑ': 4, 'ฒ': 1, 'ณ': 5, 'ด': 1,
    'ต': 2, 'ถ': 3, 'ท': 4, 'ธ': 5, 'น': 5, 'บ': 2, 'ป': 2, 'ผ': 3, 'ฝ': 7,
    'พ': 4, 'ฟ': 7, 'ภ': 4, 'ม': 5, 'ย': 8, 'ร': 4, 'ล': 6, 'ว': 6, 'ศ': 7,
    'ษ': 7, 'ส': 3, 'ห': 5, 'ฬ': 6, 'อ': 6, 'ฮ': 9,
    'ะ': 1, 'ั': 4, 'า': 1, 'ำ': 2, 'ิ': 1, 'ี': 2, 'ึ': 1, 'ื': 2, 'ุ': 1,
    'ู': 2, 'เ': 2, 'แ': 2, 'โ': 2, 'ใ': 2, 'ไ': 2, '็': 8, '่': 1, '้': 2,
    '๊': 3, '๋': 4, '์': 9
}

NUMBER_MEANINGS = {
    1: "อาทิตย์ (1) - ความเป็นผู้นำ เกียรติยศ อำนาจ การเปิิดโลก",
    2: "จันทร์ (2) - เสน่ห์ เมตตา ความอ่อนโยน ความรู้สึก ไวต่ออารมณ์",
    3: "อังคาร (3) - ความกล้าหาญ ขยัน ลุย ปฏิกิริยาไว การแข่งขัน",
    4: "พุธ (4) - การสื่อสาร เจรจา วาจาเป็นทรัพย์ ความคิดสร้างสรรค์",
    5: "พฤหัสบดี (5) - ปัญญา คุณธรรม การเรียนรู้ ความยุติธรรม ผู้ใหญ่เมตตา",
    6: "ศุกร์ (6) - ความสุข ความรัก ศิลปะ ความอุดมสมบูรณ์ ทรัพย์สิน",
    7: "เสาร์ (7) - ความอดทน รอบคอบ โครงสร้าง อสังหาริมทรัพย์ ความรับผิดชอบ",
    8: "ราหู (8) - ความชาญฉลาด พลิกผัน โชคลาภกะทันหัน ความทะเยอทะยาน",
    9: "เกตุ (9) - สิ่งศักดิ์สิทธิ์ คุ้มครอง ลางสังหรณ์ เทคโนโลยี ทางนวัตกรรม"
}


class NumerologyEngine(AbstractAstrologyEngine):
    """Core Numerology & Satta-Lek calculation engine."""

    @property
    def engine_name(self) -> str:
        return "Numerology & Satta-Lek Engine"

    @property
    def system_type(self) -> str:
        return "numerology"

    def calculate_satta_lek(self, day_num: int, lunar_month: int, year_zodiac_num: int) -> Dict[str, Any]:
        """
        Calculate Satta-Lek 7-Base 4-Row Matrix.
        Row 1 (Day Base): starts at day_num % 7 (1..7)
        Row 2 (Month Base): starts at lunar_month % 7 (1..7)
        Row 3 (Year Base): starts at year_zodiac_num % 7 (1..7)
        Row 4 (Sum Base): Row 1 + Row 2 + Row 3
        """
        def make_row(start_val: int) -> List[int]:
            s = start_val if start_val > 0 else 7
            return [((s + i - 1) % 7) + 1 for i in range(7)]

        row1 = make_row(day_num)
        row2 = make_row(lunar_month)
        row3 = make_row(year_zodiac_num)
        row4 = [row1[i] + row2[i] + row3[i] for i in range(7)]

        matrix = []
        for i in range(7):
            matrix.append({
                "house_name": SATTA_LEK_HOUSES[i],
                "row1_day": row1[i],
                "row2_month": row2[i],
                "row3_year": row3[i],
                "row4_sum": row4[i]
            })

        raw = {
            "engine": "SattaLekEngine",
            "day_num": day_num,
            "lunar_month": lunar_month,
            "year_zodiac_num": year_zodiac_num,
            "matrix_7_base": matrix
        }
        return EngineChartResult(
            engine_name=self.engine_name,
            system_type=self.system_type,
            chart_data=raw,
        )

    def score_text_or_number(self, text: str) -> EngineChartResult:
        """
        Score any text, name, phone number, or license plate using Chaldean Numerology.
        Sum digits/char values and reduce to single digit & root sum.
        """
        digits = [int(c) for c in text if c.isdigit()]
        text_chars = [c for c in text if not c.isdigit() and c in CHALDEAN_MAP]

        total_sum = sum(digits) + sum(CHALDEAN_MAP[c] for c in text_chars)
        
        # Reduce to single digit
        root = total_sum
        while root > 9:
            root = sum(int(d) for d in str(root))

        meaning = NUMBER_MEANINGS.get(root, "เลขมงคลสมดุล")

        raw = {
            "engine": "ChaldeanNumerologyEngine",
            "input_text": text,
            "total_score": total_sum,
            "reduced_root_digit": root,
            "digit_meaning": meaning
        }
        return EngineChartResult(
            engine_name=self.engine_name,
            system_type=self.system_type,
            chart_data=raw,
        )

    def calculate(self, *args, **kwargs) -> EngineChartResult:
        if "text" in kwargs or (len(args) > 0 and isinstance(args[0], str)):
            return self.score_text_or_number(*args, **kwargs)
        return self.calculate_satta_lek(*args, **kwargs)


if __name__ == "__main__":
    ne = NumerologyEngine()
    sl = ne.calculate_satta_lek(day_num=2, lunar_month=6, year_zodiac_num=7)
    score = ne.score_text_or_number("0812345678")
    print(sl)
    print(score)
