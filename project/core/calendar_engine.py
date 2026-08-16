"""
project/core/calendar_engine.py
===============================
Interactive Astrological Calendar & Date Selection (擇吉萬年曆 & 每日吉凶) Engine:
  - Daily 60 Jia-Zi Four Pillars calculation.
  - 12 Day Duty Officers (建除十二神).
  - 28 Lunar Mansions (二十八星宿).
  - Auspicious (宜) and Inauspicious (忌) activities recommendation.
  - Personalized Day Compatibility & Activity-Specific Date Finder.
"""

from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional
import calendar

from project.core.transit_engine import (
    HEAVENLY_STEMS, EARTHLY_BRANCHES, STEM_ELEMENTS, BRANCH_ELEMENTS,
    STEM_COMBINATIONS, BRANCH_COMBINATIONS, BRANCH_CLASHES
)

# 12 Duty Officers
DUTY_OFFICERS = [
    "建", "除", "滿", "平", "定", "執",
    "破", "危", "成", "收", "開", "閉"
]

OFFICER_DETAILS = {
    "建": {
        "name": "วันสร้างสรรค์ (建日 - Jian)",
        "rating": "มงคล",
        "suitable": ["เริ่มต้นวางแผน", "ขอพร", "เปิดรับสิ่งใหม่", "ไหว้พระบวงสรวง"],
        "unsuitable": ["ขุดดินก่อสร้าง", "เปิดคลังทรัพย์"],
        "tag": "auspicious"
    },
    "除": {
        "name": "วันปัดเป่า (除日 - Chu)",
        "rating": "มงคลปานกลาง",
        "suitable": ["ชำระล้างสิ่งอัปมงคล", "ทำความสะอาดบ้าน", "รักษาโรค", "ตัดผม"],
        "unsuitable": ["ขอเลื่อนขั้นตำแหน่ง", "เจรจาการค้าสำคัญ"],
        "tag": "neutral"
    },
    "滿": {
        "name": "วันสมบูรณ์พูนสุข (滿日 - Man)",
        "rating": "มงคลยิ่ง",
        "suitable": ["เปิดร้านค้า", "จัดเลี้ยงสังสรรค์", "ทำสัญญา", "รับทรัพย์สะสมทุน"],
        "unsuitable": ["ขุดดินวางรากฐาน", "ผ่าตัดทางการแพทย์"],
        "tag": "auspicious"
    },
    "平": {
        "name": "วันราบรื่นประนีประนอม (平日 - Ping)",
        "rating": "กลางๆ ราบเรียบ",
        "suitable": ["ซ่อมแซมตกแต่ง", "ปรับฮวงจุ้ย", "เจรจาไกล่เกลี่ย"],
        "unsuitable": ["ฟ้องร้องคดีความ", "แข่งขันเดิมพันสูง"],
        "tag": "neutral"
    },
    "定": {
        "name": "วันมั่นคงถาวร (定日 - Ding)",
        "rating": "มงคลยิ่ง",
        "suitable": ["หมั้นหมายมงคลสมรส", "ทำสัญญาซื้อขาย", "ตั้งเตียง", "วางศิลาฤกษ์"],
        "unsuitable": ["เดินทางไกล", "ฟ้องร้องขึ้นศาล"],
        "tag": "auspicious"
    },
    "執": {
        "name": "วันยึดถือกุมอำนาจ (執日 - Zhi)",
        "rating": "มงคลปานกลาง",
        "suitable": ["ก่อสร้าง", "เพาะปลูก", "จัดการพิธีการ"],
        "unsuitable": ["ย้ายบ้าน", "ท่องเที่ยวทางไกล"],
        "tag": "neutral"
    },
    "破": {
        "name": "วันปะทะทำลาย (破日 - Po)",
        "rating": "ควรงดเว้น",
        "suitable": ["รื้อถอนสิ่งปลูกสร้างเก่า", "ผ่าตัดรักษาโรคเรื้อรัง"],
        "unsuitable": ["งานมงคลสมรส", "เปิดร้าน", "เซ็นสัญญา", "ลงทุน"],
        "tag": "inauspicious"
    },
    "危": {
        "name": "วันระมัดระวังภัย (危日 - Wei)",
        "rating": "กลางๆ ต้องรอบคอบ",
        "suitable": ["บวงสรวงขอพร", "ทำบุญสะเดาะเคราะห์"],
        "unsuitable": ["กิจกรรมผาดโผนเสี่ยงอันตราย", "เดินทางทางน้ำ"],
        "tag": "neutral"
    },
    "成": {
        "name": "วันสำเร็จสัมฤทธิผล (成日 - Cheng)",
        "rating": "มงคลสูงสุด",
        "suitable": ["เปิดกิจการร้านค้า", "มงคลสมรส", "รับตำแหน่งใหม่", "เริ่มการศึกษา"],
        "unsuitable": ["ทะเลาะวิวาท", "ขึ้นโรงขึ้นศาล"],
        "tag": "auspicious"
    },
    "收": {
        "name": "วันเก็บเกี่ยวโชคลาภ (收日 - Shou)",
        "rating": "มงคลด้านทรัพย์",
        "suitable": ["รับเงินทวงหนี้", "ซื้ออสังหาริมทรัพย์", "ฝากเงินลงทุน"],
        "unsuitable": ["งานอวมงคล", "เดินทางโยกย้าย"],
        "tag": "auspicious"
    },
    "開": {
        "name": "วันเบิกฟ้าเปิดทาง (開日 - Kai)",
        "rating": "มงคลสูงสุด",
        "suitable": ["เปิดร้านเปิดบริษัท", "มงคลสมรส", "ออกเดินทาง", "เซ็นสัญญาธุรกิจ"],
        "unsuitable": ["ขุดสุสาน", "รื้อถอน"],
        "tag": "auspicious"
    },
    "閉": {
        "name": "วันปิดซ่อนสงบนิ่ง (閉日 - Bi)",
        "rating": "งดเว้นกิจกรรมเปิดเผย",
        "suitable": ["ออมเงิน", "ปิดปรับปรุงซ่อมแซม", "พักผ่อนนั่งสมาธิ"],
        "unsuitable": ["เปิดตัวธุรกิจ", "ขอพบแพทย์รักษา"],
        "tag": "inauspicious"
    }
}

# 28 Lunar Mansions
LUNAR_MANSIONS = [
    "角木蛟", "亢金龍", "氐土貉", "房日兔", "心月狐", "尾火虎", "箕水豹",
    "斗木獬", "牛金牛", "女土蝠", "虛日鼠", "危月燕", "室火豬", "壁水貐",
    "奎木狼", "婁金狗", "胃土雉", "昴日雞", "畢月烏", "觜火猴", "參水猿",
    "井木犴", "鬼金羊", "柳土獐", "星日馬", "張月鹿", "翼火蛇", "軫水蚓"
]

# 24 Solar Terms (Jie Qi)
SOLAR_TERMS_NAMES = [
    "小寒", "大寒", "立春", "雨水", "驚蟄", "春分",
    "清明", "穀雨", "立夏", "小滿", "芒種", "夏至",
    "小暑", "大暑", "立秋", "處暑", "白露", "秋分",
    "寒露", "霜降", "立冬", "小雪", "大雪", "冬至"
]

# Tian Yi Nobleman mapping
TIAN_YI_NOBLEMAN = {
    "甲": ["丑", "未"], "戊": ["丑", "未"], "庚": ["丑", "未"],
    "乙": ["子", "申"], "己": ["子", "申"],
    "丙": ["亥", "酉"], "丁": ["亥", "酉"],
    "壬": ["巳", "卯"], "癸": ["巳", "卯"],
    "辛": ["午", "寅"]
}


class CalendarEngine:
    """Calculates daily astrological metadata, 12 officers, and date suitability."""

    @staticmethod
    def get_day_pillar(dt: date) -> tuple[str, str]:
        """Compute 60 Jia-Zi daily stem and branch from Julian Date."""
        a = (14 - dt.month) // 12
        y = dt.year + 4800 - a
        m = dt.month + 12 * a - 3
        jdn = dt.day + ((153 * m + 2) // 5) + 365 * y + (y // 4) - (y // 100) + (y // 400) - 32045
        
        # Reference epoch alignment
        stem_idx = (jdn + 9) % 10
        branch_idx = (jdn + 1) % 12
        return HEAVENLY_STEMS[stem_idx], EARTHLY_BRANCHES[branch_idx]

    @staticmethod
    def calculate_duty_officer(month: int, day_branch: str) -> str:
        """Derive 12 Day Officer from month and day branch."""
        # Month approximate branch (Tiger in 1st lunar month = Feb)
        month_branch_idx = (month) % 12
        day_branch_idx = EARTHLY_BRANCHES.index(day_branch)
        diff = (day_branch_idx - month_branch_idx) % 12
        return DUTY_OFFICERS[diff]

    @staticmethod
    def calculate_lunar_mansion(dt: date) -> str:
        """Derive 28 Lunar Mansion for date."""
        ref = date(2026, 1, 1)
        days = (dt - ref).days
        idx = (days + 15) % 28
        return LUNAR_MANSIONS[idx]

    @staticmethod
    def generate_day_card(dt: date, user_day_master: Optional[str] = None, user_zodiac: Optional[str] = None) -> Dict[str, Any]:
        stem, branch = CalendarEngine.get_day_pillar(dt)
        officer = CalendarEngine.calculate_duty_officer(dt.month, branch)
        mansion = CalendarEngine.calculate_lunar_mansion(dt)
        details = OFFICER_DETAILS.get(officer, OFFICER_DETAILS["平"])

        # Calculate Personalized Match Score (0 - 100)
        base_score = 75
        if details["tag"] == "auspicious":
            base_score += 15
        elif details["tag"] == "inauspicious":
            base_score -= 25

        zodiac_clash = False
        nobleman_day = False
        stem_comb = False

        if user_zodiac and BRANCH_CLASHES.get(frozenset([branch, user_zodiac])):
            base_score -= 30
            zodiac_clash = True

        if user_day_master:
            nobles = TIAN_YI_NOBLEMAN.get(user_day_master, [])
            if branch in nobles:
                base_score += 20
                nobleman_day = True
            if frozenset([stem, user_day_master]) in STEM_COMBINATIONS:
                base_score += 15
                stem_comb = True

        final_score = max(10, min(100, base_score))

        return {
            "date": dt.isoformat(),
            "day_of_week": dt.strftime("%A"),
            "pillar": f"{stem}{branch}",
            "stem": stem,
            "branch": branch,
            "officer": officer,
            "officer_name": details["name"],
            "rating": details["rating"],
            "mansion": mansion,
            "suitable": details["suitable"],
            "unsuitable": details["unsuitable"],
            "tag": details["tag"],
            "score": final_score,
            "zodiac_clash": zodiac_clash,
            "nobleman_day": nobleman_day,
            "stem_combination": stem_comb
        }

    @staticmethod
    def generate_monthly_calendar(year: int, month: int, user_day_master: Optional[str] = None, user_zodiac: Optional[str] = None) -> Dict[str, Any]:
        _, num_days = calendar.monthrange(year, month)
        days_data = []

        for d in range(1, num_days + 1):
            dt = date(year, month, d)
            day_meta = CalendarEngine.generate_day_card(dt, user_day_master, user_zodiac)
            days_data.append(day_meta)

        return {
            "year": year,
            "month": month,
            "total_days": num_days,
            "days": days_data
        }

    @staticmethod
    def find_best_dates(intent: str, start_date: str, days_ahead: int = 30, user_day_master: Optional[str] = None, user_zodiac: Optional[str] = None) -> List[Dict[str, Any]]:
        """Find and rank best dates for specific intent in next N days."""
        target_officers = {
            "business_opening": ["開", "成", "滿", "建"],
            "marriage_ceremony": ["定", "成", "開", "執"],
            "home_moving": ["開", "成", "定"],
            "contract_signing": ["成", "滿", "定", "開"],
            "travel_journey": ["開", "成"],
            "wealth_investment": ["滿", "收", "成", "開"]
        }.get(intent, ["開", "成", "定", "滿"])

        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        candidates = []

        for i in range(days_ahead):
            current_dt = start + timedelta(days=i)
            day_meta = CalendarEngine.generate_day_card(current_dt, user_day_master, user_zodiac)
            if day_meta["officer"] in target_officers and not day_meta["zodiac_clash"]:
                candidates.append(day_meta)

        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates


calendar_engine = CalendarEngine()
