"""
project/routers/visual_router.py
================================
Dynamic SVG Visualizer Endpoints & Glassmorphism Chart Gallery (v3.0).

Provides high-performance, dark-mode Glassmorphism SVG rendering for all
18 Metaphysical Disciplines and Visualizers:
  1. BaZi 4 Pillars of Destiny (ผังดวง 4 เสาชะตา)
  2. 12 Zodiac Wheel (ผังดวงจักรราศี 12 ราศี)
  3. Zi Wei Dou Shu 12-Palace Matrix (ผังดวง紫微斗數)
  4. Qi Men Dun Jia 9-Grid (ผังดวง奇門遁甲)
  5. Xuan Kong Flying Stars 9-Grid (ผังดวง玄空風水)
  6. Da Liu Ren 3-Transmission Astrolabe (ผังดวง大六壬)
  7. I Ching Hexagram Transformation (ผังดวง易經六爻)
  8. Ze Ji Auspicious Date Selection (ผังดวง擇吉คำนวณฤกษ์)
  9. Thai Suriyayart & Vedic Nakshatra (ผังดวงโหราศาสตร์ไทย & ภารตวิทยา)
  10. Western Tropical & Uranian TNPs (ผังดวงโหราศาสตร์สากล & ยูเรเนียน)
  11. Satta-Lek 7-Base Numerology Matrix (ผังดวงสัตตเลข 7 ฐาน)
  12. Tai Yi Shen Shu 16-Path Celestial Wheel (ผังดวง太乙神數)
  13. Liu Yao 6-Line Na Jia Plate (ผังดวง六爻預測)
  14. Mei Hua Plum Blossom Hexagram Flow (ผังดวง梅花易數)
  15. San He 24-Mountain Water Flow Compass (ผังดวง三合風水)
  16. Qi Zheng Si Yu 28-Mansion Astrolabe (ผังดวง七政四餘)
  17. Mian Xiang 12 Facial Palaces Map (ผังดวง麻衣神相)
  18. Unified Multimodal Consensus Matrix (ผังดวงสังเคราะห์ 16 ศาสตร์)

Endpoints:
  - GET  /api/visualize/{discipline}
  - POST /api/visualize/{discipline}
  - GET  /api/charts/all
  - Aliases under /api/v1/visuals/*

Pure ASCII logging standard ([INFO], [OK], [WARNING], [ERROR]).
"""

from __future__ import annotations

import html
import json
import logging
import sys
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

from project.core.svg_generator import DISCIPLINE_SVG_GENERATORS, render_svg_chart

# Configure pure ASCII logger
log = logging.getLogger("visual_router")
if not log.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("[%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    log.addHandler(handler)
    log.setLevel(logging.INFO)

visual_router = APIRouter(tags=["Visualizers & Charts"])

# ---------------------------------------------------------------------------
# Supported Visualizer Disciplines
# ---------------------------------------------------------------------------

ALL_18_VISUALIZERS = [
    "bazi", "zodiac", "ziwei", "qimen", "xuankong", "liuren",
    "iching", "zeji", "thaivedic", "western", "numerology", "taiyi",
    "liuyao", "meihua", "sanhe", "qizheng", "mianxiang", "multimodal"
]

DISCIPLINE_CANONICAL_NAMES: dict[str, str] = {
    "bazi": "BaZi Four Pillars (ผังดวง 4 เสาชะตา)",
    "zodiac": "12 Zodiac Wheel (ผังดวงจักรราศี)",
    "ziwei": "Zi Wei Dou Shu (ผังดวง紫微斗數)",
    "qimen": "Qi Men Dun Jia (ผังดวง奇門遁甲)",
    "xuankong": "Xuan Kong Flying Stars (ผังดวง玄空風水)",
    "liuren": "Da Liu Ren (ผังดวง大六壬)",
    "iching": "I Ching Divination (ผังดวง易經六爻)",
    "zeji": "Ze Ji Auspicious Date (ผังดวง擇吉คำนวณฤกษ์)",
    "thaivedic": "Thai Suriyayart & Vedic (โหราศาสตร์ไทย & ภารตวิทยา)",
    "western": "Western & Uranian TNP (โหราศาสตร์สากล & ยูเรเนียน)",
    "numerology": "Satta-Lek 7-Base (สัตตเลข 7 ฐาน & เลขศาสตร์)",
    "taiyi": "Tai Yi Shen Shu (ผังดวง太乙神數)",
    "liuyao": "Liu Yao Na Jia (ผังดวง六爻預測)",
    "meihua": "Mei Hua Plum Blossom (ผังดวง梅花易數)",
    "sanhe": "San He 24-Mountain (ผังดวง三合風水)",
    "qizheng": "Qi Zheng Si Yu (ผังดวง七政四餘)",
    "mianxiang": "Mian Xiang 12 Palaces (ผังดวง麻衣神相)",
    "multimodal": "Unified 16-Discipline Multimodal Matrix"
}

# ---------------------------------------------------------------------------
# Default Sample Charts for Zero-Config Preview
# ---------------------------------------------------------------------------

DEFAULT_SAMPLE_CHARTS: dict[str, dict[str, Any]] = {
    "bazi": {
        "day_master": {"stem": "甲", "element": "Wood", "polarity": "Yang"},
        "solar_time_info": {"tst_datetime": "2026-08-31 12:30:00"},
        "pillars": {
            "year": {"stem": {"char": "丙", "pinyin": "Bǐng", "element": "Fire"}, "branch": {"char": "午", "pinyin": "Wǔ", "zodiac": "Horse", "element": "Fire"}},
            "month": {"stem": {"char": "丙", "pinyin": "Bǐng", "element": "Fire"}, "branch": {"char": "申", "pinyin": "Shēn", "zodiac": "Monkey", "element": "Metal"}},
            "day": {"stem": {"char": "甲", "pinyin": "Jiǎ", "element": "Wood"}, "branch": {"char": "子", "pinyin": "Zǐ", "zodiac": "Rat", "element": "Water"}},
            "hour": {"stem": {"char": "庚", "pinyin": "Gēng", "element": "Metal"}, "branch": {"char": "午", "pinyin": "Wǔ", "zodiac": "Horse", "element": "Fire"}}
        },
        "five_elements": {"percentages": {"Wood": 25.0, "Fire": 35.0, "Earth": 10.0, "Metal": 15.0, "Water": 15.0}}
    },
    "zodiac": {
        "planets": {"Sun": "Leo 15°", "Moon": "Aries 22°", "Ascendant": "Scorpio 08°"}
    },
    "ziwei": {
        "five_element_bureau": "木三局",
        "ming_gong_branch": "寅",
        "shen_gong_branch": "申",
        "palaces": [
            {"palace_name": "命宮", "earth_branch": "寅", "stars": ["紫微", "天府"], "is_ming_gong": True, "mutators": ["祿"]},
            {"palace_name": "兄弟宮", "earth_branch": "卯", "stars": ["天機"], "mutators": []},
            {"palace_name": "夫妻宮", "earth_branch": "辰", "stars": ["破軍"], "mutators": ["權"]},
            {"palace_name": "子女宮", "earth_branch": "巳", "stars": ["太陽"], "mutators": []},
            {"palace_name": "財帛宮", "earth_branch": "午", "stars": ["武曲", "七殺"], "mutators": ["科"]},
            {"palace_name": "疾厄宮", "earth_branch": "未", "stars": ["天同"], "mutators": []},
            {"palace_name": "遷移宮", "earth_branch": "申", "stars": ["七殺"], "is_shen_gong": True, "mutators": []},
            {"palace_name": "交友宮", "earth_branch": "酉", "stars": ["天梁"], "mutators": []},
            {"palace_name": "官祿宮", "earth_branch": "戌", "stars": ["廉貞", "貪狼"], "mutators": ["忌"]},
            {"palace_name": "田宅宮", "earth_branch": "亥", "stars": ["巨門"], "mutators": []},
            {"palace_name": "福德宮", "earth_branch": "子", "stars": ["天相"], "mutators": []},
            {"palace_name": "父母宮", "earth_branch": "丑", "stars": ["太陰"], "mutators": []}
        ]
    },
    "qimen": {
        "solar_term": "處暑",
        "dun_type": "Yin",
        "ju_number": 4,
        "palaces": [
            {"palace_number": 1, "star": "天蓬", "door": "休門", "spirit": "值符"},
            {"palace_number": 2, "star": "天芮", "door": "死門", "spirit": "九天"},
            {"palace_number": 3, "star": "天沖", "door": "傷門", "spirit": "九地"},
            {"palace_number": 4, "star": "天輔", "door": "杜門", "spirit": "玄武"},
            {"palace_number": 5, "star": "天禽", "door": "中宮", "spirit": "太常"},
            {"palace_number": 6, "star": "天心", "door": "開門", "spirit": "六合"},
            {"palace_number": 7, "star": "天柱", "door": "驚門", "spirit": "白虎"},
            {"palace_number": 8, "star": "天任", "door": "生門", "spirit": "太陰"},
            {"palace_number": 9, "star": "天英", "door": "景門", "spirit": "螣蛇"}
        ]
    },
    "xuankong": {
        "period": 9,
        "facing_mountain": "丙",
        "sitting_mountain": "壬",
        "facing_degree": 165.0,
        "grid_palaces": [
            {"palace_number": 1, "direction": "North", "palace_name": "坎", "sitting_star": "9", "facing_star": "9", "base_star": "1"},
            {"palace_number": 2, "direction": "Southwest", "palace_name": "坤", "sitting_star": "1", "facing_star": "8", "base_star": "2"},
            {"palace_number": 3, "direction": "East", "palace_name": "震", "sitting_star": "2", "facing_star": "7", "base_star": "3"},
            {"palace_number": 4, "direction": "Southeast", "palace_name": "巽", "sitting_star": "3", "facing_star": "6", "base_star": "4"},
            {"palace_number": 5, "direction": "Center", "palace_name": "中", "sitting_star": "4", "facing_star": "5", "base_star": "5"},
            {"palace_number": 6, "direction": "Northwest", "palace_name": "乾", "sitting_star": "5", "facing_star": "4", "base_star": "6"},
            {"palace_number": 7, "direction": "West", "palace_name": "兌", "sitting_star": "6", "facing_star": "3", "base_star": "7"},
            {"palace_number": 8, "direction": "Northeast", "palace_name": "艮", "sitting_star": "7", "facing_star": "2", "base_star": "8"},
            {"palace_number": 9, "direction": "South", "palace_name": "離", "sitting_star": "8", "facing_star": "1", "base_star": "9"}
        ]
    },
    "liuren": {
        "day_stem_branch": "甲子",
        "month_general": "勝光 (午)",
        "hour_branch": "辰",
        "three_transmissions": {
            "初傳 (發端)": "申 (白虎 / 官鬼)",
            "中傳 (移革)": "子 (神后 / 父母)",
            "末傳 (歸結)": "辰 (天罡 / 妻財)"
        },
        "four_lessons": [
            {"lesson_name": "第一課", "bottom": "甲", "top": "寅"},
            {"lesson_name": "第二課", "bottom": "寅", "top": "午"},
            {"lesson_name": "第三課", "bottom": "子", "top": "辰"},
            {"lesson_name": "第四課", "bottom": "辰", "top": "申"}
        ]
    },
    "iching": {
        "primary_hexagram": {"number": 1, "name": "乾為天 (The Creative)", "binary": "111111"},
        "transformed_hexagram": {"number": 14, "name": "火天大有 (Possession in Great Measure)", "binary": "101111"},
        "six_lines": [
            {"line": 6, "val": 7, "type": "Yang (Stable)"},
            {"line": 5, "val": 9, "type": "Yang (Moving)"},
            {"line": 4, "val": 7, "type": "Yang (Stable)"},
            {"line": 3, "val": 7, "type": "Yang (Stable)"},
            {"line": 2, "val": 7, "type": "Yang (Stable)"},
            {"line": 1, "val": 7, "type": "Yang (Stable)"}
        ]
    },
    "zeji": {
        "date": "2026-09-18",
        "rating": "A+",
        "suitability": "開市 (Grand Opening), 嫁娶 (Marriage), 祈福 (Blessing)",
        "clash": "沖猴 (Clash Monkey) 煞北",
        "solar_term": "白露",
        "twenty_eight_mansions": "角木蛟 (Dong Fang Jiao)",
        "twelve_deities": "除 (Chu - Cleansing)"
    },
    "thaivedic": {
        "thai_lagna": "ราศีสิงห์",
        "kalakini_planet": "ดาวจันทร์ (๒)",
        "sri_planet": "ดาวพฤหัสบดี (๕)",
        "vedic_nakshatra": {"number": 10, "name": "มาฆะ (Magha)", "pada": 2},
        "vimshottari_dasha": "เกตุ (Ketu) เสวยอายุ",
        "maha_thaksa": {"อาทิตย์ (๑)": "บริวาร", "จันทร์ (๒)": "อายุ", "อังคาร (๓)": "เดช", "พุธ (๔)": "ศรี"}
    },
    "western": {
        "planets_tropical": {
            "Sun": "15° Leo", "Moon": "22° Aries", "Mercury": "10° Virgo",
            "Venus": "05° Cancer", "Mars": "18° Gemini", "Jupiter": "12° Taurus",
            "Saturn": "28° Pisces", "Uranus": "26° Taurus"
        },
        "uranian_tnps": {
            "Cupido": 45.2, "Hades": 112.4, "Zeus": 210.5, "Kronos": 15.8,
            "Apollon": 180.2, "Admetos": 95.6, "Vulcanus": 320.1, "Poseidon": 135.0
        },
        "uranian_midpoint_formula": {"formula": "Sun / Jupiter = Kronos", "zodiac_position": "13°30' Fixed"}
    },
    "numerology": {
        "chaldean_score": {
            "input_text": "HoroConsultant",
            "total_score": 42,
            "reduced_root_digit": 6,
            "digit_meaning": "Venus / Harmony & Prosperity"
        },
        "satta_lek": {
            "matrix_7_base": [
                {"house_name": "อัตตะ", "row1_day": "1", "row2_month": "7", "row3_year": "6", "row4_sum": "14", "power_name": "จักรพรรดิ"},
                {"house_name": "หินะ", "row1_day": "2", "row2_month": "1", "row3_year": "7", "row4_sum": "10", "power_name": "กำลังเสาร์"},
                {"house_name": "ธนัง", "row1_day": "3", "row2_month": "2", "row3_year": "1", "row4_sum": "6", "power_name": "ศุกร์"},
                {"house_name": "ปิตา", "row1_day": "4", "row2_month": "3", "row3_year": "2", "row4_sum": "9", "power_name": "เกตุ"},
                {"house_name": "มาตา", "row1_day": "5", "row2_month": "4", "row3_year": "3", "row4_sum": "12", "power_name": "ราหู"},
                {"house_name": "โภคา", "row1_day": "6", "row2_month": "5", "row3_year": "4", "row4_sum": "15", "power_name": "มหาลาภ"},
                {"house_name": "มัชฌิมา", "row1_day": "7", "row2_month": "6", "row3_year": "5", "row4_sum": "18", "power_name": "มหาโภคทรัพย์"}
            ]
        }
    },
    "taiyi": {
        "accumulated_years": 10156328,
        "tai_yi_number": 8,
        "star_palace": 3,
        "strategic_assessment": "大吉 (Supreme Auspiciousness for Planning & Expansion)",
        "earth_plate": [1, 2, 3, 4, 5, 6, 7, 8, 9],
        "heaven_plate": [9, 8, 7, 6, 5, 4, 3, 2, 1]
    },
    "liuyao": {
        "primary_hexagram_name": "天火同人",
        "target_hexagram_name": "乾為天",
        "palace_element": "離火 (Fire)",
        "day_stem": "丙",
        "lines": [
            {"line_number": 6, "stem_branch": "戌土", "relative": "父母", "state": "靜", "beast": "玄武"},
            {"line_number": 5, "stem_branch": "申金", "relative": "妻財", "state": "發動 (動)", "beast": "白虎"},
            {"line_number": 4, "stem_branch": "午火", "relative": "官鬼", "state": "靜 (世)", "beast": "螣蛇"},
            {"line_number": 3, "stem_branch": "亥水", "relative": "子孫", "state": "靜", "beast": "勾陳"},
            {"line_number": 2, "stem_branch": "丑土", "relative": "父母", "state": "靜", "beast": "朱雀"},
            {"line_number": 1, "stem_branch": "卯木", "relative": "兄弟", "state": "靜 (應)", "beast": "青龍"}
        ]
    },
    "meihua": {
        "upper_trigram": {"name": "乾 (Heaven)", "element": "Metal", "number": 1},
        "lower_trigram": {"name": "離 (Fire)", "element": "Fire", "number": 3},
        "moving_line": 5,
        "transformed_upper_trigram": {"name": "離 (Fire)", "element": "Fire", "number": 3},
        "ti_yong": {"ti_element": "Metal (乾)", "yong_element": "Fire (離)", "interaction": "克體 (Breakthrough via Strategic Perseverance)"}
    },
    "sanhe": {
        "mountain_24": "壬山丙向",
        "water_exit": "丁未 (Graveyard Water Exiting Auspiciously)",
        "dragon_quality": "生旺龍 (Vigorous Sheng Long)",
        "auspicious_rating": "富貴雙全 (Wealth & Honor Structure)"
    },
    "qizheng": {
        "sun_position": "張宿 (Zhang Mansion 12°)",
        "moon_position": "畢宿 (Bi Mansion 05°)",
        "ascendant": "角宿 (Jiao Mansion 02°)",
        "four_remnants": {"LuoHou": "軫宿 08°", "JiDu": "胃宿 14°", "YueBei": "斗宿 20°", "ZiQi": "危宿 03°"}
    },
    "mianxiang": {
        "palaces": [
            {"name": "命宮 (Life Palace / 印堂)", "quality": "Bright & Smooth", "score": 92},
            {"name": "財帛宮 (Wealth Palace / 鼻)", "quality": "Plump & High Bridge", "score": 88},
            {"name": "官祿宮 (Career Palace / 額)", "quality": "Broad & Clear", "score": 90},
            {"name": "夫妻宮 (Marriage Palace / 奸門)", "quality": "Smooth & Unblemished", "score": 85}
        ],
        "three_stops": {"upper": "Balanced (33%)", "middle": "Strong (37%)", "lower": "Solid (30%)"}
    },
    "multimodal": {
        "consensus_score": 0.94,
        "primary_auspicious_disciplines": ["BaZi", "QiMen", "ZiWei", "XuanKong"],
        "disciplines": [
            {"name": "BaZi", "score": 0.95, "sentiment": "Highly Favorable"},
            {"name": "QiMen", "score": 0.92, "sentiment": "Favorable Window"},
            {"name": "ZiWei", "score": 0.96, "sentiment": "Noble Stars Active"},
            {"name": "XuanKong", "score": 0.91, "sentiment": "Water Flow Prosperous"}
        ]
    }
}

# ---------------------------------------------------------------------------
# Glassmorphism CSS Theme Enhancer
# ---------------------------------------------------------------------------

GLASSMORPHISM_SVG_DEFS = """
  <defs>
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;600;700&amp;family=Inter:wght@400;600;800&amp;family=Noto+Sans+SC:wght@400;700&amp;display=swap');
      svg {
        font-family: 'Prompt', 'Inter', 'Noto Sans SC', system-ui, -apple-system, sans-serif;
        text-rendering: geometricPrecision;
        shape-rendering: geometricPrecision;
      }
      .glass-card {
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        transition: transform 0.25s ease, filter 0.25s ease;
      }
      .glass-card:hover {
        filter: brightness(1.12);
      }
      .glass-glow {
        filter: drop-shadow(0 0 12px rgba(99, 102, 241, 0.45));
      }
    </style>
  </defs>
"""


def enhance_svg_with_glassmorphism(svg_str: str, theme: str = "glassmorphism") -> str:
    """Inject dark-mode glassmorphism styling and responsive metadata into SVG markup."""
    if not svg_str.strip().startswith("<svg"):
        return svg_str

    if "<style>" in svg_str:
        return svg_str

    # Inject glassmorphism defs right after <svg ...>
    idx = svg_str.find(">")
    if idx != -1:
        return svg_str[: idx + 1] + "\n" + GLASSMORPHISM_SVG_DEFS + svg_str[idx + 1 :]
    return svg_str


def normalize_discipline_key(discipline: str) -> str:
    """Normalize discipline URL string to standard lookup key."""
    key = discipline.lower().strip().replace("-", "_")
    alias_map = {
        "zi_wei": "ziwei",
        "qi_men": "qimen",
        "liu_ren": "liuren",
        "tai_yi": "taiyi",
        "i_ching": "iching",
        "liu_yao": "liuyao",
        "mei_hua": "meihua",
        "xuan_kong": "xuankong",
        "san_he": "sanhe",
        "mian_xiang": "mianxiang",
        "ze_ji": "zeji",
        "thai_vedic": "thaivedic",
        "western_uranian": "western",
        "satta_lek": "numerology",
        "qi_zheng": "qizheng",
    }
    return alias_map.get(key, key)


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class VisualizeChartRequest(BaseModel):
    chart: dict[str, Any] | None = Field(
        default=None,
        description="Deterministic chart calculations data. If omitted, default golden sample data will be rendered."
    )
    theme: str = Field(default="glassmorphism", description="Styling theme: 'glassmorphism' | 'dark' | 'neon'")
    lang: str = Field(default="th", description="Chart language: 'th' | 'en'")
    title: str | None = Field(default=None, description="Optional custom title for the SVG chart")
    format: str = Field(default="svg", description="Response format: 'svg' (default, image/svg+xml) or 'json'")


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@visual_router.get(
    "/api/visualize/{discipline}",
    summary="Generate Dynamic Glassmorphism SVG Chart (GET)",
    description="Renders a high-aesthetic, dark-mode Glassmorphism SVG chart for any of the 18 disciplines."
)
@visual_router.get("/api/v1/visuals/{discipline}", include_in_schema=False)
@visual_router.get("/api/v1/visualize/{discipline}", include_in_schema=False)
async def visualize_discipline_get(
    discipline: str,
    theme: str = Query("glassmorphism", description="Styling theme"),
    lang: str = Query("th", description="Chart language: 'th' or 'en'"),
    title: str | None = Query(None, description="Custom chart title"),
    format: str = Query("svg", description="Format: 'svg' or 'json'")
):
    norm_key = normalize_discipline_key(discipline)
    if norm_key not in DISCIPLINE_SVG_GENERATORS:
        raise HTTPException(
            status_code=400,
            detail={
                "error": f"Invalid discipline: '{discipline}'",
                "valid_disciplines": ALL_18_VISUALIZERS,
                "message": f"Supported disciplines are: {', '.join(ALL_18_VISUALIZERS)}"
            }
        )

    chart_data = DEFAULT_SAMPLE_CHARTS.get(norm_key, {})
    raw_svg = render_svg_chart(norm_key, chart_data, title=title, lang=lang)
    styled_svg = enhance_svg_with_glassmorphism(raw_svg, theme=theme)

    if format.lower() == "json":
        return JSONResponse(
            content={
                "status": "ok",
                "discipline": norm_key,
                "discipline_name": DISCIPLINE_CANONICAL_NAMES.get(norm_key, norm_key),
                "theme": theme,
                "lang": lang,
                "title": title,
                "svg": styled_svg
            }
        )

    return Response(content=styled_svg, media_type="image/svg+xml")


@visual_router.post(
    "/api/visualize/{discipline}",
    summary="Generate Dynamic Glassmorphism SVG Chart (POST)",
    description="Renders a high-aesthetic, dark-mode Glassmorphism SVG chart with custom calculation payload."
)
@visual_router.post("/api/v1/visuals/{discipline}", include_in_schema=False)
@visual_router.post("/api/v1/visualize/{discipline}", include_in_schema=False)
async def visualize_discipline_post(
    discipline: str,
    payload: VisualizeChartRequest
):
    norm_key = normalize_discipline_key(discipline)
    if norm_key not in DISCIPLINE_SVG_GENERATORS:
        raise HTTPException(
            status_code=400,
            detail={
                "error": f"Invalid discipline: '{discipline}'",
                "valid_disciplines": ALL_18_VISUALIZERS,
                "message": f"Supported disciplines are: {', '.join(ALL_18_VISUALIZERS)}"
            }
        )

    chart_data = payload.chart if payload.chart is not None else DEFAULT_SAMPLE_CHARTS.get(norm_key, {})
    raw_svg = render_svg_chart(norm_key, chart_data, title=payload.title, lang=payload.lang)
    styled_svg = enhance_svg_with_glassmorphism(raw_svg, theme=payload.theme)

    if payload.format.lower() == "json":
        return JSONResponse(
            content={
                "status": "ok",
                "discipline": norm_key,
                "discipline_name": DISCIPLINE_CANONICAL_NAMES.get(norm_key, norm_key),
                "theme": payload.theme,
                "lang": payload.lang,
                "title": payload.title,
                "svg": styled_svg
            }
        )

    return Response(content=styled_svg, media_type="image/svg+xml")


@visual_router.get(
    "/api/charts/all",
    summary="Preview All 18 Dynamic Visualizers",
    description="Returns all 18 rendered SVG charts in a single unified JSON payload or interactive Glassmorphism HTML gallery."
)
@visual_router.get("/api/v1/charts/all", include_in_schema=False)
async def get_all_charts(
    lang: str = Query("th", description="Chart language: 'th' or 'en'"),
    format: str = Query("json", description="Response format: 'json' or 'html'"),
    theme: str = Query("glassmorphism", description="Theme styling")
):
    charts_dict: dict[str, str] = {}
    for key in ALL_18_VISUALIZERS:
        chart_data = DEFAULT_SAMPLE_CHARTS.get(key, {})
        svg = render_svg_chart(key, chart_data, lang=lang)
        charts_dict[key] = enhance_svg_with_glassmorphism(svg, theme=theme)

    if format.lower() == "html":
        # Render a dark-mode glassmorphism preview gallery
        html_cards = []
        for key in ALL_18_VISUALIZERS:
            c_name = DISCIPLINE_CANONICAL_NAMES.get(key, key)
            svg_content = charts_dict[key]
            card_html = f"""
            <div class="chart-card" id="chart-{key}">
              <div class="chart-header">
                <span class="badge">{key.upper()}</span>
                <h3>{html.escape(c_name)}</h3>
              </div>
              <div class="chart-svg-container">
                {svg_content}
              </div>
            </div>
            """
            html_cards.append(card_html)

        html_doc = f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>HoroConsultant 18-Discipline Visualizers Gallery</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;600;700&family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #0b0f19;
      --card-bg: rgba(18, 24, 38, 0.75);
      --border: rgba(255, 255, 255, 0.12);
      --accent: #6366f1;
      --text: #f1f5f9;
      --text-muted: #94a3b8;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: var(--bg);
      color: var(--text);
      font-family: 'Prompt', 'Inter', sans-serif;
      padding: 2rem;
      min-height: 100vh;
    }}
    .header {{
      text-align: center;
      margin-bottom: 2.5rem;
    }}
    .header h1 {{
      font-size: 2.2rem;
      background: linear-gradient(135deg, #fbbf24 0%, #f43f5e 50%, #818cf8 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 0.5rem;
    }}
    .header p {{
      color: var(--text-muted);
      font-size: 1rem;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(540px, 1fr));
      gap: 2rem;
    }}
    .chart-card {{
      background: var(--card-bg);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 1.5rem;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
      display: flex;
      flex-direction: column;
    }}
    .chart-header {{
      display: flex;
      align-items: center;
      gap: 0.75rem;
      margin-bottom: 1rem;
    }}
    .badge {{
      background: rgba(99, 102, 241, 0.25);
      color: #a5b4fc;
      border: 1px solid #6366f1;
      padding: 0.25rem 0.6rem;
      border-radius: 6px;
      font-size: 0.75rem;
      font-weight: 700;
      letter-spacing: 0.05em;
    }}
    .chart-header h3 {{
      font-size: 1.15rem;
      font-weight: 600;
    }}
    .chart-svg-container {{
      width: 100%;
      min-height: 380px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: rgba(10, 14, 23, 0.6);
      border-radius: 12px;
      overflow: hidden;
      padding: 0.5rem;
    }}
    .chart-svg-container svg {{
      max-width: 100%;
      height: auto;
    }}
  </style>
</head>
<body>
  <div class="header">
    <h1>HoroConsultant Visual Engine (v3.0)</h1>
    <p>18-Discipline Glassmorphism Computational Metaphysics SVG Suite</p>
  </div>
  <div class="grid">
    {''.join(html_cards)}
  </div>
</body>
</html>"""
        return HTMLResponse(content=html_doc)

    return JSONResponse(
        content={
            "status": "ok",
            "total_visualizers": len(ALL_18_VISUALIZERS),
            "theme": theme,
            "lang": lang,
            "disciplines": ALL_18_VISUALIZERS,
            "charts": charts_dict
        }
    )

class ExportRequest(BaseModel):
    discipline: str
    format: str = "svg"
    chart: dict = {}

class BundleRequest(BaseModel):
    disciplines: list[str]
    title: str = "Consultation Report"
    lang: str = "th"

@visual_router.post("/api/v1/charts/export", summary="Export Chart")
async def export_chart(payload: ExportRequest):
    norm_key = normalize_discipline_key(payload.discipline)
    chart_data = payload.chart if payload.chart else DEFAULT_SAMPLE_CHARTS.get(norm_key, {})
    raw_svg = render_svg_chart(norm_key, chart_data, lang="th")
    styled_svg = enhance_svg_with_glassmorphism(raw_svg, theme="glassmorphism")
    
    from project.core.chart_bundler import ChartBundler
    bundler = ChartBundler()
    
    if payload.format.lower() == "png":
        png_bytes = bundler.export_png(styled_svg)
        return Response(content=png_bytes, media_type="image/png")
    elif payload.format.lower() == "pdf":
        pdf_bytes = bundler.export_pdf({payload.discipline: styled_svg}, "Export")
        return Response(content=pdf_bytes, media_type="application/pdf")
    else:
        return Response(content=styled_svg, media_type="image/svg+xml")

@visual_router.post("/api/v1/charts/bundle", summary="Bundle Charts")
async def bundle_charts(payload: BundleRequest):
    charts = {}
    for d in payload.disciplines:
        norm_key = normalize_discipline_key(d)
        chart_data = DEFAULT_SAMPLE_CHARTS.get(norm_key, {})
        raw_svg = render_svg_chart(norm_key, chart_data, lang=payload.lang)
        charts[norm_key] = enhance_svg_with_glassmorphism(raw_svg, theme="glassmorphism")
    
    from project.core.chart_bundler import ChartBundler
    bundler = ChartBundler()
    html_report = bundler.bundle_consultation(charts, payload.title, payload.lang)
    return HTMLResponse(content=html_report)
