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



def calculate_dynamic_period9_sectors(facing_degree: float, period: int = 9) -> Dict[str, Any]:
    """
    Computes dynamic Xuan Kong Flying Star 9-palace sector distribution for Period 9.
    Maps facing star (向星), sitting star (山星), energy levels, heat scores, and cures
    according to building orientation (24-mountains / 8 directions).
    """
    deg = ((facing_degree % 360.0) + 360.0) % 360.0
    
    # Identify primary facing sector key and sitting sector key
    # Sectors: N (0°), NE (45°), E (90°), SE (135°), S (180°), SW (225°), W (270°), NW (315°)
    if deg >= 337.5 or deg < 22.5:
        facing_sec, sitting_sec = "N", "S"
    elif deg < 67.5:
        facing_sec, sitting_sec = "NE", "SW"
    elif deg < 112.5:
        facing_sec, sitting_sec = "E", "W"
    elif deg < 157.5:
        facing_sec, sitting_sec = "SE", "NW"
    elif deg < 202.5:
        facing_sec, sitting_sec = "S", "N"
    elif deg < 247.5:
        facing_sec, sitting_sec = "SW", "NE"
    elif deg < 292.5:
        facing_sec, sitting_sec = "W", "E"
    else:
        facing_sec, sitting_sec = "NW", "SE"

    # Base sector descriptions with localized palace names
    palace_names = {
        "S": "ทิศใต้ (South - 離)",
        "N": "ทิศเหนือ (North - 坎)",
        "E": "ทิศตะวันออก (East - 震)",
        "W": "ทิศตะวันตก (West - 兌)",
        "SE": "ทิศตะวันออกเฉียงใต้ (Southeast - 巽)",
        "SW": "ทิศตะวันตกเฉียงใต้ (Southwest - 坤)",
        "NE": "ทิศตะวันออกเฉียงเหนือ (Northeast - 艮)",
        "NW": "ทิศตะวันตกเฉียงเหนือ (Northwest - 乾)",
        "CENTER": "ใจกลางอาคาร (Center - 中宮)"
    }

    # Direction-specific 9-palace flying star templates
    star_templates = {
        "S": {
            "S": {"star": "9 ม่วง (向星 - ดาวโชคลาภหน้าอาคาร)", "heat_score": 98, "advice": "ประตูหน้าบ้านรับโชคลาภการค้า ยุค 9 พลังหยางรุ่งเรือง", "cure": "เปิดไฟสว่าง ประดับโคมไฟสีแดง/ม่วง หรือตั้งคริสตัล"},
            "N": {"star": "9 ม่วง (山星 - ภูเขาพิงหลังบารมี)", "heat_score": 94, "advice": "ตำแหน่งประธานหนุนบารมี ผู้ใหญ่อุปถัมภ์ สุขภาพแข็งแรง", "cure": "ตั้งรูปภาพภูเขา หรือหินตั้งมงคลเสริมความมั่นคง"},
            "SE": {"star": "2 ดำ (ดาวโรคภัยไข้เจ็บ)", "heat_score": 35, "advice": "ระวังเรื่องสุขภาพทางเดินอาหาร เลี่ยงห้องนอนผู้ป่วย", "cure": "แขวนน้ำเต้าทองเหลือง หรือเหรียญ 6 จักรพรรดิ"},
            "SW": {"star": "6 ขาว (ดาวขุนนางบารมี)", "heat_score": 82, "advice": "หนุนอำนาจการบริหารงานและการตัดสินใจทางธุรกิจ", "cure": "ตั้งวัตถุโลหะกลมแวววาว หรือลูกแก้วคริสตัล"},
            "E": {"star": "8 ขาว (ดาวการเงินมั่นคง)", "heat_score": 90, "advice": "ส่งเสริมทรัพย์สินอสังหาริมทรัพย์และการออมเงินระยะยาว", "cure": "วางคริสตัลสีเหลือง หรือลูกแก้วดินเพื่อสะสมทรัพย์"},
            "W": {"star": "4 เขียว (ดาวบัณฑิตและเสน่ห์)", "heat_score": 86, "advice": "เกื้อหนุนการสอบแข่งขัน ความคิดสร้างสรรค์ และความรัก", "cure": "ตั้งไผ่กวนอิม 4 กิ่งในแจกันน้ำ"},
            "NE": {"star": "7 แดง (ดาววิวาทและของมีคม)", "heat_score": 42, "advice": "ระวังการเจรจาขัดแย้ง คดีความ หรือของมีคม", "cure": "วางอ่างน้ำนิ่งเพื่อถ่ายเทพลังโลหะพิฆาต"},
            "NW": {"star": "5 เหลือง (ดาวเบญจสูญ)", "heat_score": 25, "advice": "ดาววิบัติประจำทิศ ห้ามเคาะเจาะทุบหรือต่อเติม", "cure": "แขวนกระดิ่งลมโลหะ 6 หลอด หรือพัดลมทองเหลือง"},
            "CENTER": {"star": "3 มรกต (ดาวข้อพิพาท)", "heat_score": 55, "advice": "ศูนย์กลางบ้านควรเปิดโล่ง สะอาด สว่างไสว", "cure": "ใช้พรมหรือโคมไฟสีแดงเพื่อลดทอนดาวไม้ 3"}
        },
        "N": {
            "N": {"star": "1 ขาว (向星 - ประตูหน้าปัญญารับทรัพย์)", "heat_score": 98, "advice": "ประตูหน้าบ้านรับกระแสเงินสดและโอกาสธุรกิจดิจิทัลใหม่", "cure": "ตั้งน้ำพุหมุนเวียน หรือต้นไม้น้ำเสริมการเงิน"},
            "S": {"star": "9 ม่วง (山星 - ภูเขาพิงหลังชื่อเสียง)", "heat_score": 95, "advice": "ภูเขาพิงหลังทิศใต้หนุนเกียรติยศและตำแหน่งหน้าที่การงาน", "cure": "ประดับรูปมังกรทอง หรือภาพทิวทัศน์พระอาทิตย์ขึ้น"},
            "NW": {"star": "6 ขาว (ดาวขุนนางและผู้อุปถัมภ์)", "heat_score": 88, "advice": "เหมาะเป็นห้องทำงานผู้บริหาร หนุนการตัดสินใจเด็ดขาด", "cure": "ตั้งวัตถุโลหะกลม หรือลูกโลกคริสตัล"},
            "NE": {"star": "8 ขาว (ดาวทรัพย์สมบัติมั่นคง)", "heat_score": 90, "advice": "เสริมความมั่งคั่งระยะยาวและการลงทุนอสังหาริมทรัพย์", "cure": "วางหินหยก หรือกระปุกออมสินทองคำ"},
            "W": {"star": "2 ดำ (ดาวโรคภัยไข้เจ็บ)", "heat_score": 35, "advice": "ควรดูแลความสะอาด เลี่ยงเตียงนอนผู้สูงอายุในทิศนี้", "cure": "แขวนน้ำเต้าทองเหลืองถ่ายเทพลังลบ"},
            "E": {"star": "5 เหลือง (ดาวเบญจสูญ)", "heat_score": 25, "advice": "ดาววิบัติ ห้ามจัดกิจกรรมส่งเสียงดังหรือทุบรื้อ", "cure": "วางชามน้ำเกลือบริสุทธิ์ หรือกระดิ่งลมโลหะ 6 หลอด"},
            "SW": {"star": "4 เขียว (ดาวบัณฑิตและวิชาการ)", "heat_score": 85, "advice": "ส่งเสริมการศึกษา การวิจัย และเสน่ห์เจรจาการค้า", "cure": "วางพู่กันจีน 4 ด้าม หรือต้นไผ่กวนอิม"},
            "SE": {"star": "7 แดง (ดาววิวาทแย่งชิง)", "heat_score": 45, "advice": "ระวังการถูกเอาเปรียบทางการค้าและการมีปากเสียง", "cure": "วางแก้วน้ำสงบนิ่งเพื่อถ่ายเทพลัง"},
            "CENTER": {"star": "3 มรกต (ดาวข้อพิพาท)", "heat_score": 55, "advice": "รักษาพื้นที่กลางบ้านให้สะอาดและอากาศถ่ายเท", "cure": "ตกแต่งโทนสีแดง หรือส้มเพื่อปรับสมดุล"}
        },
        "E": {
            "E": {"star": "8 ขาว (向星 - ประตูหน้ามหาเศรษฐี)", "heat_score": 98, "advice": "ประตูหน้าบ้านรับโชคลาภการเงินและความเจริญก้าวหน้า", "cure": "วางหินคริสตัลสีทอง หรืออ่างน้ำไหลเสริมกระแสทรัพย์"},
            "W": {"star": "4 เขียว (山星 - ภูเขาพิงบัณฑิตปัญญา)", "heat_score": 92, "advice": "หนุนการศึกษา เกียรติยศ และความสามัคคีในครอบครัว", "cure": "ตั้งชั้นหนังสือ หรือภาพเขียนธรรมชาติสีเขียว"},
            "S": {"star": "1 ขาว (ดาวปัญญาและมิตรภาพ)", "heat_score": 88, "advice": "หนุนการเจรจา พันธมิตรธุรกิจ และการเดินทางข้ามชาติ", "cure": "ตั้งน้ำพุหรือลูกแก้วน้ำคริสตัล"},
            "SE": {"star": "9 ม่วง (ดาวอนาคตโชคลาภยุค 9)", "heat_score": 94, "advice": "เสริมชื่อเสียง ธุรกิจออนไลน์ และความคิดสร้างสรรค์", "cure": "ติดไฟสว่าง หรือวางต้นไม้มงคลใบเขียวสด"},
            "N": {"star": "6 ขาว (ดาวอำนาจบารมี)", "heat_score": 82, "advice": "เหมาะแก่การวางโต๊ะทำงานผู้บริหารและบัญชีการเงิน", "cure": "ตั้งวัตถุโลหะสีทอง หรือนาฬิกาลูกตุ้ม"},
            "NE": {"star": "2 ดำ (ดาวโรคภัย)", "heat_score": 35, "advice": "ระวังสุขภาพระบบกระดูกและทางเดินหายใจ", "cure": "แขวนน้ำเต้าโลหะ หรือเหรียญ 6 จักรพรรดิ"},
            "SW": {"star": "5 เหลือง (ดาวเบญจสูญ)", "heat_score": 25, "advice": "ทิศอัปมงคล ห้ามเคาะเจาะตอกเสาเข็ม", "cure": "วางกระดิ่งลมโลหะ 6 แท่งถ่ายเทพลัง"},
            "NW": {"star": "7 แดง (ดาวขัดแย้ง)", "heat_score": 42, "advice": "ระวังเรื่องเอกสารสัญญาและคู่แข่งทางธุรกิจ", "cure": "วางอ่างน้ำนิ่งเพื่อดับธาตุทองพิฆาต"},
            "CENTER": {"star": "3 มรกต (ดาวข้อพิพาท)", "heat_score": 55, "advice": "ศูนย์กลางบ้านควรเปิดโล่ง ไม่วางของรก", "cure": "ใช้แสงไฟวอร์มไวท์ปรับสมดุลธาตุ"}
        },
        "W": {
            "W": {"star": "4 เขียว (向星 - ประตูหน้าเสน่ห์การค้าสร้างสรรค์)", "heat_score": 98, "advice": "ประตูหน้าบ้านรับความคิดสร้างสรรค์ นวัตกรรม และลูกค้าอุดหนุน", "cure": "ตั้งต้นไม้มงคล หรือแจกันดอกไม้สดรับพลังหยาง"},
            "E": {"star": "8 ขาว (山星 - ภูเขาพิงหลังทรัพย์สมบัติ)", "heat_score": 95, "advice": "พิงหลังด้วยพลังดาว 8 ขาว หนุนทรัพย์สินที่ดินมั่นคง", "cure": "วางก้อนหินธรรมชาติ หรือภาพภูเขาทึบตัน"},
            "N": {"star": "9 ม่วง (ดาวชื่อเสียงและโอกาสใหม่)", "heat_score": 92, "advice": "เปิดรับธุรกิจดิจิทัลและชื่อเสียงแบรนด์ขยายตัว", "cure": "ติดไฟกิ่งสีสว่าง หรือวางพีระมิดคริสตัล"},
            "NW": {"star": "8 ขาว (ดาวการเงินงอกเงย)", "heat_score": 88, "advice": "เสริมความมั่งคั่งและกระแสเงินสดหมุนเวียน", "cure": "วางกระปุกเซรามิก หรือหินนำโชค"},
            "SW": {"star": "6 ขาว (ดาวผู้นำบารมี)", "heat_score": 84, "advice": "หนุนการควบคุมบริวารและเจรจาธุรกิจสำเร็จ", "cure": "วางลูกโลกโลหะ หรือตราประทับทองเหลือง"},
            "S": {"star": "7 แดง (ดาววิวาทข้อพิพาท)", "heat_score": 42, "advice": "ระวังการผิดใจกันในเรื่องผลประโยชน์", "cure": "ตั้งแก้วน้ำสะอาดนิ่งเพื่อลดทอน"},
            "SE": {"star": "5 เหลือง (ดาวเบญจสูญ)", "heat_score": 25, "advice": "เลี่ยงการกระแทก ทุบ หรือปรับปรุงพื้นที่โซนนี้", "cure": "แขวนกระดิ่งลมโลหะ 6 หลอด"},
            "NE": {"star": "2 ดำ (ดาวโรคภัย)", "heat_score": 35, "advice": "ระวังสุขภาพกล้ามเนื้อและระบบทางเดินอาหาร", "cure": "วางน้ำเต้าทองเหลืองคู่"},
            "CENTER": {"star": "3 มรกต (ดาวข้อพิพาท)", "heat_score": 55, "advice": "กลางบ้านควรสว่างไสว สะอาดสะอ้าน", "cure": "ตกแต่งด้วยโคมไฟสีแดง"}
        },
        "SE": {
            "SE": {"star": "9 ม่วง (向星 - ประตูมงคลยุค 9 โชคลาภการค้า)", "heat_score": 96, "advice": "ประตูหน้าบ้านรับพลังดาว 9 โดยตรง หนุนการค้าและชื่อเสียงโดดเด่น", "cure": "วางโคมไฟสีแดง/ม่วง หรือน้ำพุหมุนเวียน"},
            "NW": {"star": "6 ขาว (山星 - ภูเขาพิงขุนนางบารมี)", "heat_score": 94, "advice": "พิงหลังด้วยดาว 6 ขาว หนุนบารมีผู้ใหญ่และความมั่นคง", "cure": "วางภาพภูเขาสีทอง หรือรูปปั้นมังกรโลหะ"},
            "S": {"star": "1 ขาว (ดาวปัญญาและโอกาสการงาน)", "heat_score": 88, "advice": "เสริมความคิดสร้างสรรค์และโอกาสเดินทางต่างแดน", "cure": "ตั้งต้นไม้น้ำ หรือลูกแก้วใส"},
            "E": {"star": "8 ขาว (ดาวการเงินอุดมสมบูรณ์)", "heat_score": 90, "advice": "ส่งเสริมการออม การลงทุน และผลกำไรระยะยาว", "cure": "วางคริสตัลสีเหลือง หรือโถสมบัติ"},
            "SW": {"star": "4 เขียว (ดาวบัณฑิตและศิลปะ)", "heat_score": 84, "advice": "เหมาะสำหรับห้องทำงานออกแบบและห้องเรียน", "cure": "ตั้งแจกันดอกไม้สด หรือไผ่กวนอิม"},
            "N": {"star": "7 แดง (ดาววิวาท)", "heat_score": 42, "advice": "ระวังการถูกนินทาว่าร้าย หรือขัดแย้งกับหุ้นส่วน", "cure": "วางแก้วน้ำสงบนิ่ง"},
            "W": {"star": "5 เหลือง (ดาวเบญจสูญ)", "heat_score": 25, "advice": "ดาววิบัติ ห้ามขุดเจาะหรือต่อเติมเด็ดขาด", "cure": "แขวนกระดิ่งลมโลหะ 6 แท่ง"},
            "NE": {"star": "2 ดำ (ดาวโรคภัย)", "heat_score": 35, "advice": "ควรดูแลสุขอนามัยให้ดี เลี่ยงห้องนอนคนชรา", "cure": "แขวนน้ำเต้าทองเหลือง"},
            "CENTER": {"star": "3 มรกต (ดาวข้อพิพาท)", "heat_score": 55, "advice": "จัดกึ่งกลางบ้านให้โปร่งสบาย แสงสว่างพอเหมาะ", "cure": "ใช้พรมสีแดงหรือส้ม"}
        },
        "NW": {
            "NW": {"star": "6 ขาว (向星 - ประตูหน้ามหาอำนาจบารมี)", "heat_score": 98, "advice": "ประตูหน้าบ้านรับพลังผู้นำ การค้ากับองค์กรใหญ่ และต่างประเทศ", "cure": "ตั้งวัตถุโลหะสีทอง หรือโคมไฟระย้าคริสตัล"},
            "SE": {"star": "9 ม่วง (山星 - ภูเขาพิงหลังอนาคตโชคลาภ)", "heat_score": 95, "advice": "พิงหลังด้วยดาว 9 ยุค ครอบครัวอบอุ่น มั่งคั่ง สุขภาพสมบูรณ์", "cure": "ติดภาพทิวทัศน์ภูเขาสีเขียว หรือวางโคมไฟมงคล"},
            "W": {"star": "1 ขาว (ดาวปัญญาและโอกาสธุรกิจ)", "heat_score": 92, "advice": "หนุนการเจรจาการค้า การตลาด และสภาพคล่องการเงิน", "cure": "ตั้งน้ำพุหมุน หรือแจกันน้ำใส"},
            "N": {"star": "8 ขาว (ดาวทรัพย์สมบัติ)", "heat_score": 88, "advice": "เสริมความมั่นคงทางการเงินและผลตอบแทนการลงทุน", "cure": "วางหินคริสตัลสีทอง หรือกระปุกออมสิน"},
            "NE": {"star": "4 เขียว (ดาววิชาการและความคิด)", "heat_score": 86, "advice": "เกื้อหนุนการสอบแข่งขัน งานวิจัย และความรัก", "cure": "ตั้งต้นไผ่กวนอิม 4 ต้น"},
            "S": {"star": "2 ดำ (ดาวโรคภัย)", "heat_score": 35, "advice": "ระวังเรื่องสุขภาพหัวใจและสายตา", "cure": "แขวนน้ำเต้าทองเหลือง หรือเหรียญจีน 6 เหรียญ"},
            "E": {"star": "7 แดง (ดาววิวาท)", "heat_score": 42, "advice": "ระวังการมีปากเสียงกับเพื่อนร่วมงานหรือญาติมิตร", "cure": "วางอ่างน้ำนิ่งเพื่อถ่ายเทพลัง"},
            "SW": {"star": "5 เหลือง (ดาวเบญจสูญ)", "heat_score": 25, "advice": "ดาววิบัติ ห้ามเคาะเจาะตอกเสาเข็ม", "cure": "แขวนกระดิ่งลมโลหะ 6 แท่ง"},
            "CENTER": {"star": "3 มรกต (ดาวข้อพิพาท)", "heat_score": 55, "advice": "รักษาพื้นที่กลางบ้านให้สะอาดเรียบร้อย", "cure": "ใช้ของตกแต่งโทนสีแดงเพื่อปรับสมดุล"}
        },
        "NE": {
            "NE": {"star": "7 แดง (向星 - ประตูหน้าวาจารับทรัพย์)", "heat_score": 96, "advice": "ประตูหน้าบ้านรับโชคลาภด้านการพูด การตลาด สื่อสาร และออนไลน์", "cure": "วางอ่างบัว หรือน้ำพุนิ่งเพื่อเปลี่ยนพลังเป็นโภคทรัพย์"},
            "SW": {"star": "1 ขาว (山星 - ภูเขาพิงหลังปัญญามั่นคง)", "heat_score": 94, "advice": "พิงหลังด้วยดาว 1 ขาว หนุนสติปัญญา สุขภาพ และที่พึ่งพิงปลอดภัย", "cure": "วางก้อนหินมงคล หรือภาพธรรมชาติสงบนิ่ง"},
            "E": {"star": "9 ม่วง (ดาวอนาคตมงคล)", "heat_score": 92, "advice": "เปิดรับธุรกิจใหม่ ความคิดสร้างสรรค์ และเกียรติยศ", "cure": "ติดไฟสว่าง หรือวางต้นไม้มงคล"},
            "SE": {"star": "8 ขาว (ดาวการเงินมั่งคั่ง)", "heat_score": 90, "advice": "หนุนทรัพย์สินสะสมและรายได้มั่นคง", "cure": "วางคริสตัลสีเหลือง หรือโถทองคำ"},
            "N": {"star": "4 เขียว (ดาวบัณฑิต)", "heat_score": 85, "advice": "ส่งเสริมการเรียนรู้ ความก้าวหน้า และความสัมพันธ์", "cure": "ตั้งต้นไผ่กวนอิม 4 กิ่ง"},
            "NW": {"star": "6 ขาว (ดาวขุนนางบารมี)", "heat_score": 82, "advice": "หนุนตำแหน่งหน้าที่การงานและการบริหาร", "cure": "ตั้งวัตถุโลหะกลมสีทอง"},
            "S": {"star": "5 เหลือง (ดาวเบญจสูญ)", "heat_score": 25, "advice": "ดาววิบัติ ห้ามก่อสร้างหรือเปิดใช้งานเสียงดัง", "cure": "แขวนกระดิ่งลมโลหะ 6 หลอด"},
            "W": {"star": "2 ดำ (ดาวโรคภัย)", "heat_score": 35, "advice": "ระวังสุขภาพระบบทางเดินอาหารและปอด", "cure": "วางน้ำเต้าทองเหลือง"},
            "CENTER": {"star": "3 มรกต (ดาวข้อพิพาท)", "heat_score": 55, "advice": "ศูนย์กลางบ้านควรโปร่งโล่ง แสงแดดส่องถึง", "cure": "ใช้พรมสีแดงเพื่อดูดซับพลังไม้ 3"}
        },
        "SW": {
            "SW": {"star": "1 ขาว (向星 - ประตูหน้าปัญญามหาลาภ)", "heat_score": 98, "advice": "ประตูหน้าบ้านรับโชคลาภใหญ่ ผู้อุปถัมภ์ และความสัมพันธ์ราบรื่น", "cure": "ตั้งน้ำพุ หรือลูกแก้วน้ำคริสตัล"},
            "NE": {"star": "7 แดง (山星 - ภูเขาพิงยุทธศาสตร์มั่นคง)", "heat_score": 92, "advice": "พิงหลังด้วยความเฉียบคม ป้องกันศัตรูคู่แข่งทางธุรกิจ", "cure": "วางหินธรรมชาติสีเข้ม หรือรูปปั้นเต่ามังกร"},
            "S": {"star": "8 ขาว (ดาวทรัพย์สินอสังหาฯ)", "heat_score": 92, "advice": "ส่งเสริมความมั่งคั่งทางการเงินและที่ดิน", "cure": "วางหินคริสตัลสีทอง หรือแจกันเซรามิก"},
            "W": {"star": "6 ขาว (ดาวอำนาจบารมี)", "heat_score": 88, "advice": "หนุนความเป็นผู้นำและการสั่งการราบรื่น", "cure": "ตั้งวัตถุโลหะสีทองแวววาว"},
            "SE": {"star": "9 ม่วง (ดาวชื่อเสียงยุค 9)", "heat_score": 90, "advice": "เสริมชื่อเสียง ความคิดก้าวหน้า และธุรกิจดิจิทัล", "cure": "ติดไฟวอร์มไวท์ หรือวางพีระมิดคริสตัล"},
            "NW": {"star": "4 เขียว (ดาวบัณฑิตและวิชาการ)", "heat_score": 84, "advice": "เหมาะสำหรับห้องทำงานสร้างสรรค์และห้องอ่านหนังสือ", "cure": "ตั้งไผ่กวนอิม 4 กิ่งในแจกันน้ำ"},
            "N": {"star": "2 ดำ (ดาวโรคภัย)", "heat_score": 35, "advice": "ระวังสุขภาพระบบไตและทางเดินปัสสาวะ", "cure": "แขวนน้ำเต้าทองเหลือง หรือเหรียญ 6 จักรพรรดิ"},
            "E": {"star": "5 เหลือง (ดาวเบญจสูญ)", "heat_score": 25, "advice": "ดาววิบัติ เลี่ยงการขุดเจาะหรือกระแทกเสียงดัง", "cure": "วางชามน้ำเกลือบริสุทธิ์ หรือกระดิ่งลม 6 หลอด"},
            "CENTER": {"star": "3 มรกต (ดาวข้อพิพาท)", "heat_score": 55, "advice": "กลางบ้านควรสว่าง สะอาด ปราศจากสิ่งกีดขวาง", "cure": "ตกแต่งด้วยโคมไฟสีแดง"}
        }
    }

    # Select mapped template or fallback to South
    chosen_template = star_templates.get(facing_sec, star_templates["S"])
    
    result_sectors = {}
    for key, data in chosen_template.items():
        result_sectors[key] = {
            "sector": palace_names.get(key, key),
            "star": data["star"],
            "heat_score": data["heat_score"],
            "advice": data["advice"],
            "cure": data["cure"]
        }

    return result_sectors


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
        dynamic_sectors = calculate_dynamic_period9_sectors(facing_degree, period)
        return {
            "facing_degree": mountain_meta["degree"],
            "period": period,
            "mountain": mountain_meta,
            "sectors": dynamic_sectors,
            "summary": f"บ้านทิศหน้า {mountain_meta['facing_mountain']} ({mountain_meta['facing_direction']}) นั่งทิศ {mountain_meta['sitting_mountain']} ในยุค {period} (2024-2043) รับพลังผังดาวบิน 9 วังตามองศาหล่อแก"
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
