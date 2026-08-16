"""
Numerology & Satta-Lek (สัตตเลข 7 ฐาน & เลขศาสตร์ประยุกต์) Core Engine
========================================================================
Deterministic calculations for:
- Thai Satta-Lek 7-Base 4-Row Calculation (7 ฐาน 4 แถว: ฐานวัน, ฐานเดือน, ฐานปี, ฐานผลรวม)
- Chaldean & Pythagorean Numerology Scoring (วิเคราะห์เบอร์โทรศัพท์, ทะเบียนรถ, ชื่อ-นามสกุล)
"""

from typing import Any

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


PLANETARY_POWER_BASE = {
    3: {"name": "กำลังพระอังคารเล็ก (3)", "meaning": "ความมุ่งมั่น บากบั่น ต่อสู้ อดทนฝ่าฟัน"},
    4: {"name": "กำลังพระพุธเล็ก (4)", "meaning": "การเจรจา ปฏิภาณไหวพริบ ความคิดสร้างสรรค์"},
    5: {"name": "กำลังพระพฤหัสเล็ก (5)", "meaning": "คุณธรรม ปัญญา ความยุติธรรม จิตใจดีงาม"},
    6: {"name": "กำลังพระอาทิตย์ (6)", "meaning": "เกียรติยศ อำนาจ วาสนา ความเป็นผู้นำโดดเด่น"},
    7: {"name": "กำลังพระเสาร์เล็ก (7)", "meaning": "ความสุขุม รอบคอบ อดทน หนักแน่น"},
    8: {"name": "กำลังพระอังคาร (8)", "meaning": "ความกล้าหาญ เด็ดเดี่ยว ชัยชนะ การแข่งขัน"},
    9: {"name": "กำลังพระเกตุ (9)", "meaning": "สิ่งศักดิ์สิทธิ์คุ้มครอง ลางสังหรณ์แม่นยำ เทคโนโลยี"},
    10: {"name": "กำลังพระเสาร์ (10)", "meaning": "ความมั่นคง มหาอุตม์ อสังหาริมทรัพย์ ความรับผิดชอบสูง"},
    11: {"name": "ราชาโชค (11)", "meaning": "โชคลาภเกื้อหนุน การเดินทาง ความสำเร็จราบรื่น"},
    12: {"name": "กำลังพระราหู (12)", "meaning": "ไหวพริบปฏิภาณ พลิกแพลง โชคลาภกะทันหัน"},
    13: {"name": "มหาอุจจ์ (13)", "meaning": "พลังเข้มแข็ง บารมีสูงเด่น พลิกฟื้นสถานการณ์"},
    14: {"name": "จักรพรรดิ (14)", "meaning": "ความสำเร็จยิ่งใหญ่ วาสนาสูง ผู้นำองค์กร มหาเสน่ห์"},
    15: {"name": "กำลังพระจันทร์ (15)", "meaning": "เสน่ห์เมตตามหานิยม มหาเศรษฐี โภคทรัพย์สมบูรณ์"},
    16: {"name": "โสฬสมงคล (16)", "meaning": "สิริมงคลสูงสุด 16 ชั้นฟ้า ความสำเร็จสมบูรณ์พูนผล"},
    17: {"name": "กำลังพระพุธ (17)", "meaning": "เจรจาค้าขาย ปัญญาเลิศล้ำ วาจาสิทธิ์ การทูต"},
    18: {"name": "มหาจักรพรรดิ (18)", "meaning": "อำนาจบารมีมหาศาล ความยิ่งใหญ่ เกียรติยศสูงสุด"},
    19: {"name": "กำลังพระพฤหัสบดี (19)", "meaning": "ครูบาอาจารย์ ปัญญาญาณ มหาเศรษฐี ผู้ใหญ่เมตตา"},
    20: {"name": "มหาโชค (20)", "meaning": "ความอุดมสมบูรณ์ มั่งคั่ง มั่งมี โภคทรัพย์ไหลมา"},
    21: {"name": "กำลังพระศุกร์ (21)", "meaning": "โภคทรัพย์เงินทอง ศิลปะ ความสุขเกษม เสน่ห์สมบูรณ์"}
}


class NumerologyEngine(AbstractAstrologyEngine):
    """Core Numerology & Satta-Lek calculation engine."""

    @property
    def engine_name(self) -> str:
        return "Numerology & Satta-Lek Engine"

    @property
    def system_type(self) -> str:
        return "numerology"

    def calculate_satta_lek(self, day_num: int, lunar_month: int, year_zodiac_num: int) -> dict[str, Any]:
        """
        Calculate Satta-Lek 7-Base 4-Row Matrix.
        Row 1 (Day Base): starts at day_num % 7 (1..7)
        Row 2 (Month Base): starts at lunar_month % 7 (1..7)
        Row 3 (Year Base): starts at year_zodiac_num % 7 (1..7)
        Row 4 (Sum Base): Row 1 + Row 2 + Row 3
        """
        from project.core.fast_math import fast_satta_lek_matrix
        row1, row2, row3, row4 = fast_satta_lek_matrix(day_num, lunar_month, year_zodiac_num)

        matrix = []
        for i in range(7):
            sum_val = row4[i]
            p_info = PLANETARY_POWER_BASE.get(sum_val, {"name": f"ฐานกำลัง ({sum_val})", "meaning": "พลังงานส่งเสริมดวงชะตา"})
            matrix.append({
                "house_name": SATTA_LEK_HOUSES[i],
                "row1_day": row1[i],
                "row2_month": row2[i],
                "row3_year": row3[i],
                "row4_sum": sum_val,
                "power_name": p_info["name"],
                "power_meaning": p_info["meaning"]
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
        breakdown = []
        for c in text:
            if c.isdigit():
                breakdown.append({"char": c, "val": int(c), "type": "digit"})
            elif c in CHALDEAN_MAP:
                breakdown.append({"char": c, "val": CHALDEAN_MAP[c], "type": "letter"})
            elif c != " ":
                breakdown.append({"char": c, "val": 0, "type": "symbol"})

        total_sum = sum(b["val"] for b in breakdown)

        # Reduce to single digit
        root = total_sum
        while root > 9:
            root = sum(int(d) for d in str(root))

        meaning = NUMBER_MEANINGS.get(root, "เลขมงคลสมดุล")
        auspicious_tier = "มงคลยิ่ง (High Auspicious)" if root in (1, 4, 5, 6, 9) else ("มงคลปานกลาง (Neutral/Progressive)" if root in (2, 8) else "ควรระวัง/รอบคอบ (Cautious)")

        raw = {
            "engine": "ChaldeanNumerologyEngine",
            "input_text": text,
            "char_breakdown": breakdown,
            "total_score": total_sum,
            "reduced_root_digit": root,
            "digit_meaning": meaning,
            "auspicious_tier": auspicious_tier
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
