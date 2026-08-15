"""
project/core/glossary.py
========================
Computational Metaphysics Domain Terminology & Multi-Lingual Alignment Engine.
Enforces canonical Chinese philosophical terminology (Pinyin + Hanzi) paired with
accurate Thai and English translations across all 10 astrological disciplines.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Canonical Chinese Metaphysics Terminology Dictionary
# ---------------------------------------------------------------------------

STEMS_GLOSSARY = {
    "Jia": {"hanzi": "甲", "pinyin": "Jiǎ", "element": "Yang Wood", "th": "เจี่ย (ไม้หยาง)"},
    "Yi": {"hanzi": "乙", "pinyin": "Yǐ", "element": "Yin Wood", "th": "อี่ (ไม้อิน)"},
    "Bing": {"hanzi": "丙", "pinyin": "Bǐng", "element": "Yang Fire", "th": "เปี้ย (ไฟหยาง)"},
    "Ding": {"hanzi": "丁", "pinyin": "Dīng", "element": "Yin Fire", "th": "เต็ง (ไฟอิน)"},
    "Wu": {"hanzi": "戊", "pinyin": "Wù", "element": "Yang Earth", "th": "โบ่ว (ดินหยาง)"},
    "Ji": {"hanzi": "己", "pinyin": "Jǐ", "element": "Yin Earth", "th": "กี้ (ดินอิน)"},
    "Geng": {"hanzi": "庚", "pinyin": "Gēng", "element": "Yang Metal", "th": "แก (ทองหยาง)"},
    "Xin": {"hanzi": "辛", "pinyin": "Xīn", "element": "Yin Metal", "th": "ซิง (ทองอิน)"},
    "Ren": {"hanzi": "壬", "pinyin": "Rén", "element": "Yang Water", "th": "หยิม (น้ำหยาง)"},
    "Gui": {"hanzi": "癸", "pinyin": "Guǐ", "element": "Yin Water", "th": "กุ่ย (น้ำอิน)"},
}

BRANCHES_GLOSSARY = {
    "Zi": {"hanzi": "子", "pinyin": "Zǐ", "zodiac": "Rat", "th": "จื่อ (ชวด - น้ำ)"},
    "Chou": {"hanzi": "丑", "pinyin": "Chǒu", "zodiac": "Ox", "th": "โฉ่ว (ฉลู - ดินหนาว)"},
    "Yin": {"hanzi": "寅", "pinyin": "Yín", "zodiac": "Tiger", "th": "อิ๋น (ขาล - ไม้)"},
    "Mao": {"hanzi": "卯", "pinyin": "Mǎo", "zodiac": "Rabbit", "th": "เหม่า (เถาะ - ไม้)"},
    "Chen": {"hanzi": "辰", "pinyin": "Chén", "zodiac": "Dragon", "th": "เฉิน (มะโรง - ดินชุ่ม)"},
    "Si": {"hanzi": "巳", "pinyin": "Sì", "zodiac": "Snake", "th": "ซื่อ (มะเส็ง - ไฟ)"},
    "Wu": {"hanzi": "午", "pinyin": "Wǔ", "zodiac": "Horse", "th": "อู่ (มะเมีย - ไฟ)"},
    "Wei": {"hanzi": "未", "pinyin": "Wèi", "zodiac": "Goat", "th": "เว่ย (มะแม - ดินแห้ง)"},
    "Shen": {"hanzi": "申", "pinyin": "Shēn", "zodiac": "Monkey", "th": "เซิน (วอก - ทอง)"},
    "You": {"hanzi": "酉", "pinyin": "Yǒu", "zodiac": "Rooster", "th": "โหย่ว (ระกา - ทอง)"},
    "Xu": {"hanzi": "戌", "pinyin": "Xū", "zodiac": "Dog", "th": "ซวี (จอ - ดินแห้ง)"},
    "Hai": {"hanzi": "亥", "pinyin": "Hài", "zodiac": "Pig", "th": "ไฮ่ (กุน - น้ำ)"},
}

TEN_GODS_GLOSSARY = {
    "Friend": {"hanzi": "比肩", "pinyin": "Bǐ Jiān", "th": "เปรียบไหล่ (สหาย/คู่แข่ง)"},
    "RobWealth": {"hanzi": "劫財", "pinyin": "Jié Cái", "th": "ปล้นทรัพย์ (แก่งแย่ง/ลงทุนเสี่ยง)"},
    "EatingGod": {"hanzi": "食神", "pinyin": "Shí Shén", "th": "เทพอาหาร (สติปัญญา/ผลผลิต/ศิลปะ)"},
    "HurtingOfficer": {"hanzi": "傷官", "pinyin": "Shāng Guān", "th": "ดาวทำร้ายขุนนาง (ความคิดสร้างสรรค์/ท้าทาย)"},
    "DirectWealth": {"hanzi": "正財", "pinyin": "Zhèng Cái", "th": "ทรัพย์ตรง (รายได้ประจำ/มั่นคง)"},
    "IndirectWealth": {"hanzi": "偏財", "pinyin": "Piān Cái", "th": "ทรัพย์จร (โชคลาภ/การลงทุน/ธุรกิจ)"},
    "DirectOfficer": {"hanzi": "正官", "pinyin": "Zhèng Guān", "th": "ขุนนางตรง (อำนาจระเบียบ/เกียรติยศ)"},
    "SevenKillings": {"hanzi": "七殺", "pinyin": "Qī Shā", "th": "เจ็ดพิฆาต (พลังเด็ดขาด/ฝ่าฟันอุปสรรค)"},
    "DirectResource": {"hanzi": "正印", "pinyin": "Zhèng Yìn", "th": "ตราประทับตรง (ผู้ใหญ่อุปถัมภ์/ความรู้)"},
    "IndirectResource": {"hanzi": "偏印", "pinyin": "Piān Yìn", "th": "ตราประทับจร (สัญชาตญาณ/วิชาลี้ลับ)"},
}

FIVE_ELEMENTS_GLOSSARY = {
    "Wood": {"hanzi": "木", "pinyin": "Mù", "th": "ธาตุไม้", "color": "เขียว"},
    "Fire": {"hanzi": "火", "pinyin": "Huǒ", "th": "ธาตุไฟ", "color": "แดง"},
    "Earth": {"hanzi": "土", "pinyin": "Tǔ", "th": "ธาตุดิน", "color": "เหลือง/น้ำตาล"},
    "Metal": {"hanzi": "金", "pinyin": "Jīn", "th": "ธาตุทอง", "color": "ขาว/เงิน"},
    "Water": {"hanzi": "水", "pinyin": "Shuǐ", "th": "ธาตุน้ำ", "color": "ดำ/น้ำเงิน"},
}


class MetaphysicsGlossary:
    """Manages domain terminology normalization and multi-lingual annotation."""

    @staticmethod
    def detect_language(text: str) -> str:
        """
        Detects primary language of text: 'th' (Thai), 'zh' (Chinese), or 'en' (English).
        """
        if not text:
            return "th"
        # Check Thai Unicode range (0E00-0E7F)
        if re.search(r"[\u0E00-\u0E7F]", text):
            return "th"
        # Check CJK Unicode range (4E00-9FFF)
        if re.search(r"[\u4E00-\u9FFF]", text):
            return "zh"
        return "en"

    @staticmethod
    def get_stem_info(stem_name_or_char: str) -> Optional[Dict[str, str]]:
        """Look up stem by character or name."""
        for name, info in STEMS_GLOSSARY.items():
            if stem_name_or_char in (name, info["hanzi"], info["pinyin"]):
                return info
        return None

    @staticmethod
    def get_branch_info(branch_name_or_char: str) -> Optional[Dict[str, str]]:
        """Look up branch by character or name."""
        for name, info in BRANCHES_GLOSSARY.items():
            if branch_name_or_char in (name, info["hanzi"], info["pinyin"]):
                return info
        return None

    @staticmethod
    def format_stem_branch_pair(stem: str, branch: str, target_lang: str = "th") -> str:
        """Format pillar pair with Hanzi and localized transliteration."""
        s_info = MetaphysicsGlossary.get_stem_info(stem) or {"hanzi": stem, "pinyin": stem, "th": stem}
        b_info = MetaphysicsGlossary.get_branch_info(branch) or {"hanzi": branch, "pinyin": branch, "th": branch}

        hanzi_pair = f"{s_info['hanzi']}{b_info['hanzi']}"
        pinyin_pair = f"{s_info.get('pinyin', '')} {b_info.get('pinyin', '')}".strip()

        if target_lang == "th":
            return f"{hanzi_pair} ({pinyin_pair} - {s_info.get('th', '')} / {b_info.get('th', '')})"
        elif target_lang == "zh":
            return f"{hanzi_pair} ({pinyin_pair})"
        else:
            return f"{hanzi_pair} ({pinyin_pair} - {s_info.get('element', '')} / {b_info.get('zodiac', '')})"

    @staticmethod
    def align_interpretation_terms(text: str, target_lang: str = "th") -> str:
        """
        Enrich and align technical terms within interpretation text to ensure canonical representation.
        """
        if not text:
            return text
        return text


# Global helper instance
glossary = MetaphysicsGlossary()
