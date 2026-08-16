"""
project/core/luopan_dream_engine.py
===================================
LuoPan 24-Mountain Compass, Period 9 Flying Star Heatmap & Dream Symbolism Decoder.
"""

from typing import Any, Dict, List, Optional

# 24 Mountains in clockwise order from North (0 deg)
MOUNTAINS_24 = [
    {"name": "子 (Zi)", "element": "Water", "dir": "N", "start": 352.5, "end": 7.5},
    {"name": "癸 (Gui)", "element": "Water", "dir": "N", "start": 7.5, "end": 22.5},
    {"name": "丑 (Chou)", "element": "Earth", "dir": "NE", "start": 22.5, "end": 37.5},
    {"name": "艮 (Gen)", "element": "Earth", "dir": "NE", "start": 37.5, "end": 52.5},
    {"name": "寅 (Yin)", "element": "Wood", "dir": "NE", "start": 52.5, "end": 67.5},
    {"name": "甲 (Jia)", "element": "Wood", "dir": "E", "start": 67.5, "end": 82.5},
    {"name": "卯 (Mao)", "element": "Wood", "dir": "E", "start": 82.5, "end": 97.5},
    {"name": "乙 (Yi)", "element": "Wood", "dir": "E", "start": 97.5, "end": 112.5},
    {"name": "辰 (Chen)", "element": "Earth", "dir": "SE", "start": 112.5, "end": 127.5},
    {"name": "巽 (Xun)", "element": "Wood", "dir": "SE", "start": 127.5, "end": 142.5},
    {"name": "巳 (Si)", "element": "Fire", "dir": "SE", "start": 142.5, "end": 157.5},
    {"name": "丙 (Bing)", "element": "Fire", "dir": "S", "start": 157.5, "end": 172.5},
    {"name": "午 (Wu)", "element": "Fire", "dir": "S", "start": 172.5, "end": 187.5},
    {"name": "丁 (Ding)", "element": "Fire", "dir": "S", "start": 187.5, "end": 202.5},
    {"name": "未 (Wei)", "element": "Earth", "dir": "SW", "start": 202.5, "end": 217.5},
    {"name": "坤 (Kun)", "element": "Earth", "dir": "SW", "start": 217.5, "end": 232.5},
    {"name": "申 (Shen)", "element": "Metal", "dir": "SW", "start": 232.5, "end": 247.5},
    {"name": "庚 (Geng)", "element": "Metal", "dir": "W", "start": 247.5, "end": 262.5},
    {"name": "酉 (You)", "element": "Metal", "dir": "W", "start": 262.5, "end": 277.5},
    {"name": "辛 (Xin)", "element": "Metal", "dir": "W", "start": 277.5, "end": 292.5},
    {"name": "戌 (Xu)", "element": "Earth", "dir": "NW", "start": 292.5, "end": 307.5},
    {"name": "乾 (Qian)", "element": "Metal", "dir": "NW", "start": 307.5, "end": 322.5},
    {"name": "亥 (Hai)", "element": "Water", "dir": "NW", "start": 322.5, "end": 337.5},
    {"name": "壬 (Ren)", "element": "Water", "dir": "N", "start": 337.5, "end": 352.5}
]

# Period 9 (2024-2043) 9-Palace Energy Grid
PERIOD_9_SECTORS = {
    "S": {
        "sector": "ทิศใต้ (South - 離)",
        "star": "9 ม่วง (9 Purple Fire)",
        "energy_level": "旺氣 (Maximum Prosperity)",
        "heat_score": 98,
        "advice": "ทิศมงคลประจำยุค 9 เหมาะตั้งห้องทำงาน ประตูใหญ่ หรือเปิดรับแสงสว่าง เสริมชื่อเสียง โอกาส และโชคลาภใหญ่",
        "cure": "เพิ่มโคมไฟสีแดง/ส้ม หรือต้นไม้เสริมธาตุไฟ"
    },
    "N": {
        "sector": "ทิศเหนือ (North - 坎)",
        "star": "8 ขาว (8 White Earth)",
        "energy_level": "生氣 (Wealth Growth)",
        "heat_score": 88,
        "advice": "ทิศดาวทรัพย์และอสังหาริมทรัพย์ เหมาะเก็บสะสมความมั่งคั่งและตั้งโต๊ะทำงาน",
        "cure": "จัดวางหินคริสตัล หรือของตกแต่งสีเอิร์ธโทน"
    },
    "SW": {
        "sector": "ทิศตะวันตกเฉียงใต้ (South-West - 坤)",
        "star": "1 ขาว (1 White Water)",
        "energy_level": "吉氣 (Wisdom & Noble Support)",
        "heat_score": 92,
        "advice": "ดาวทันหลางแห่งสติปัญญาและผู้อุปถัมภ์ เหมาะเจรจาธุรกิจและห้องนอนผู้บริหาร",
        "cure": "ตั้งน้ำพุหรือน้ำตกหมุนเวียนเสริมพลังธาตุน้ำ"
    },
    "E": {
        "sector": "ทิศตะวันออก (East - 震)",
        "star": "4 เขียว (4 Green Wood)",
        "energy_level": "文昌 (Academic & Romance)",
        "heat_score": 85,
        "advice": "ดาวเหวินชาง ส่งเสริมการเรียนรู้ ความคิดสร้างสรรค์ งานวิจัย และความรัก",
        "cure": "ตั้งไผ่กวนอิม 4 ต้น หรือแจกันดอกไม้สด"
    },
    "SE": {
        "sector": "ทิศตะวันออกเฉียงใต้ (South-East - 巽)",
        "star": "2 ดำ (2 Black Earth)",
        "energy_level": "病符 (Sickness Star - Caution)",
        "heat_score": 30,
        "advice": "ดาวโรคภัยไข้เจ็บ ควรเลี่ยงห้องนอนผู้สูงอายุหรือหญิงมีครรภ์ ไม่ควรเคาะเจาะทุบ",
        "cure": "แขวนน้ำเต้าทองเหลือง หรือวางเหรียญจีน 6 เหรียญเพื่อถ่ายเทพลังร้าย"
    },
    "W": {
        "sector": "ทิศตะวันตก (West - 兌)",
        "star": "5 เหลือง (5 Yellow Earth)",
        "energy_level": "五黃廉貞 (Calamity Star - High Caution)",
        "heat_score": 15,
        "advice": "ดาวเบญจภูติวิบัติประจำทิศ ห้ามเคลื่อนไหวหรือเคาะก่อสร้างในโซนนี้",
        "cure": "วางเกลือบริสุทธิ์ในชามน้ำ หรือกระดิ่งลมโลหะ 6 แท่ง"
    },
    "NW": {
        "sector": "ทิศตะวันตกเฉียงเหนือ (North-West - 乾)",
        "star": "6 ขาว (6 White Metal)",
        "energy_level": "武曲 (Authority & Career)",
        "heat_score": 82,
        "advice": "ดาวขุนนางและบารมี เหมาะสำหรับห้องทำงานผู้นำ",
        "cure": "วางลูกแก้วหินอ่อน หรือสัญลักษณ์มังกรโลหะ"
    },
    "NE": {
        "sector": "ทิศตะวันออกเฉียงเหนือ (North-East - 艮)",
        "star": "7 แดง (7 Red Metal)",
        "energy_level": "破軍 (Conflict & Rivalry)",
        "heat_score": 45,
        "advice": "พึงระวังการแข่งขันหรือมีปากเสียงข้อพิพาท",
        "cure": "วางแก้วน้ำสงบนิ่งเพื่อลดทอนพลังโลหะพิฆาต"
    },
    "CENTER": {
        "sector": "ใจกลางพื้นที่ (Center - 中宮)",
        "star": "9 ม่วง (Period 9 Heart)",
        "energy_level": "核心 (Core Heart Energy)",
        "heat_score": 90,
        "advice": "ศูนย์กลางบ้านควรเปิดโล่ง สะอาด สว่างไสว ปราศจากสิ่งกีดขวาง",
        "cure": "รักษาความสะอาดและเปิดแสงไฟโปร่งสบาย"
    }
}

# Dream Symbolism Archetypes Database
DREAM_ARCHETYPES = [
    {
        "keywords": ["น้ำ", "ทะเล", "แม่น้ำ", "ฝน", "ว่ายน้ำ", "water", "sea", "river", "rain", "ocean"],
        "symbol": "สายน้ำ & มหาสมุทร (坎 - Water Element)",
        "element": "Water",
        "hexagram": "坎為水 (Hexagram 29 - The Abysmal Water)",
        "sattaleka_numbers": [2, 4, 14, 24, 68],
        "omen": "มงคลเรื่องการหมุนเวียนโชคลาภ การปรับตัว และการปลดปล่อยอารมณ์",
        "advice": "เป็นช่วงเวลาที่ทรัพย์จะไหลเวียนคล่องตัว ควรหมั่นทำบุญค่าน้ำหรือปล่อยสัตว์น้ำ"
    },
    {
        "keywords": ["งู", "พญานาค", "มังกร", "snake", "dragon", "serpent", "naga"],
        "symbol": "พญานาค & มังกรสวรรค์ (震 - Dragon & Serpent Transformation)",
        "element": "Wood/Fire",
        "hexagram": "乾為天 (Hexagram 1 - The Creative Dragon)",
        "sattaleka_numbers": [5, 9, 59, 89, 168],
        "omen": "มงคลยิ่งใหญ่ด้านบารมี ผู้ใหญ่เกื้อหนุน หรือมีคู่บุญเข้ามาในชีวิต",
        "advice": "มีเกณฑ์ได้รับโชคลาภก้อนใหญ่หรือการเปลี่ยนแปลงครั้งสำคัญ ควรไปกราบสักการะองค์พญานาคหรือพระแก้วมรกต"
    },
    {
        "keywords": ["ทอง", "เพชร", "แสงสว่าง", "พระพุทธรูป", "วัด", "gold", "diamond", "temple", "buddha", "light"],
        "symbol": "แสงทิพย์ & ทองคำบริสุทธิ์ (乾/離 - Divine Light & Gold)",
        "element": "Metal/Fire",
        "hexagram": "天火同人 (Hexagram 13 - Fellowship with Men)",
        "sattaleka_numbers": [9, 1, 19, 99, 999],
        "omen": "มงคลสูงสุด เทวดาคุ้มครอง สิ่งศักดิ์สิทธิ์เปิดทางสว่าง",
        "advice": "จิตใจผ่องใส จะคิดการสิ่งใดสำเร็จลุล่วง เหมาะแก่การตั้งจิตอธิษฐานทำบุญใหญ่"
    },
    {
        "keywords": ["รถ", "ขับรถ", "เดินทาง", "บิน", "เครื่องบิน", "car", "travel", "fly", "airplane"],
        "symbol": "การก้าวหน้า & ยานพาหนะ (乾/震 - Movement & Elevation)",
        "element": "Metal/Wood",
        "hexagram": "地天泰 (Hexagram 11 - Peace & Ascendance)",
        "sattaleka_numbers": [4, 7, 47, 74, 88],
        "omen": "การเลื่อนขั้น โยกย้ายในทางที่เจริญก้าวหน้า",
        "advice": "ธุรกิจหรือโปรเจกต์จะเร่งสปีดสู่ความสำเร็จ ให้เตรียมพร้อมรับโอกาสใหม่ที่เข้ามาอย่างรวดเร็ว"
    },
    {
        "keywords": ["บ้าน", "อาคาร", "สร้างบ้าน", "ห้องนอน", "house", "building", "home", "room"],
        "symbol": "เคหสถาน & รากฐานชีวิต (坤/艮 - Earth Foundation)",
        "element": "Earth",
        "hexagram": "地山謙 (Hexagram 15 - Humility & Solid Earth)",
        "sattaleka_numbers": [5, 8, 58, 85, 38],
        "omen": "ความมั่นคงในครอบครัวและทรัพย์สิน",
        "advice": "เหมาะแก่การจัดฮวงจุ้ยบ้านใหม่ ลงทุนในอสังหาริมทรัพย์ หรือวางแผนอนาคตระยะยาว"
    },
    {
        "keywords": ["ปลา", "เต่า", "สัตว์น้ำ", "fish", "turtle"],
        "symbol": "ปลาหลีฮื้อ & เต่ามังกร (壽/富 - Longevity & Wealth)",
        "element": "Water/Earth",
        "hexagram": "水地比 (Hexagram 8 - Union & Abundance)",
        "sattaleka_numbers": [8, 3, 38, 83, 108],
        "omen": "โชคลาภการค้าขาย สุขภาพแข็งแรง อายุยืนยาว",
        "advice": "การค้ากำไรคล่องตัว ควรทานอาหารมังสวิรัติหรือไถ่ชีวิตสัตว์เพื่อสะสมบารมี"
    }
]


class LuoPanDreamEngine:
    """Computes 24-mountain directions, flying star sector matrices, and dream decodings."""

    @staticmethod
    def calculate_mountain(facing_degree: float) -> Dict[str, Any]:
        """Find 24-mountain sector and sitting/facing alignment."""
        deg = facing_degree % 360.0
        matched = MOUNTAINS_24[0]

        for m in MOUNTAINS_24:
            if m["start"] > m["end"]:  # wraps around 0/360
                if deg >= m["start"] or deg < m["end"]:
                    matched = m
                    break
            else:
                if m["start"] <= deg < m["end"]:
                    matched = m
                    break

        # Opposite is sitting mountain
        sitting_deg = (deg + 180.0) % 360.0
        sitting_m = MOUNTAINS_24[0]
        for m in MOUNTAINS_24:
            if m["start"] > m["end"]:
                if sitting_deg >= m["start"] or sitting_deg < m["end"]:
                    sitting_m = m
                    break
            else:
                if m["start"] <= sitting_deg < m["end"]:
                    sitting_m = m
                    break

        return {
            "degree": deg,
            "facing_mountain": matched["name"],
            "facing_direction": matched["dir"],
            "facing_element": matched["element"],
            "sitting_mountain": sitting_m["name"],
            "sitting_direction": sitting_m["dir"],
            "sitting_element": sitting_m["element"]
        }

    @staticmethod
    def calculate_luopan_heatmap(facing_degree: float, period: int = 9) -> Dict[str, Any]:
        mountain_meta = LuoPanDreamEngine.calculate_mountain(facing_degree)
        return {
            "period": period,
            "mountain": mountain_meta,
            "sectors": PERIOD_9_SECTORS,
            "summary": f"บ้านทิศหน้า {mountain_meta['facing_mountain']} ({mountain_meta['facing_direction']}) นั่งทิศ {mountain_meta['sitting_mountain']} ประจำยุค {period}"
        }

    @staticmethod
    def interpret_dream(dream_text: str, user_day_master: Optional[str] = None) -> Dict[str, Any]:
        """Semantic decode of dream symbols, connecting with 64 hexagrams and Sattaleka numbers."""
        text_lower = dream_text.lower()
        matched_symbols = []

        for item in DREAM_ARCHETYPES:
            if any(k in text_lower for k in item["keywords"]):
                matched_symbols.append(item)

        if not matched_symbols:
            # Default fallback archetype
            matched_symbols.append({
                "keywords": ["ทั่วไป"],
                "symbol": "ดวงจิตตื่นรู้ & การเดินทางทางวิญญาณ (Spiritual Voyage)",
                "element": "Spirit",
                "hexagram": "雷地豫 (Hexagram 16 - Enthusiasm)",
                "sattaleka_numbers": [1, 7, 17, 71, 99],
                "omen": "จิตใต้สำนึกกำลังประมวลผลประสบการณ์เพื่อนำทางชีวิต",
                "advice": "ฝึกสมาธิก่อนนอน และบันทึกความฝันเพื่อเปิดรับญาณหยั่งรู้"
            })

        lucky_pool = []
        for s in matched_symbols:
            lucky_pool.extend(s["sattaleka_numbers"])
        lucky_pool = sorted(list(set(lucky_pool)))[:6]

        primary = matched_symbols[0]
        return {
            "query_dream": dream_text,
            "symbols_detected": [s["symbol"] for s in matched_symbols],
            "primary_element": primary["element"],
            "hexagram_alignment": primary["hexagram"],
            "lucky_numbers": lucky_pool,
            "omen": primary["omen"],
            "spiritual_advice": primary["advice"],
            "user_day_master": user_day_master
        }


luopan_dream_engine = LuoPanDreamEngine()
