"""
project/schemas/mcp_tools_v1.py — MCP Tool & Router Schemas v1.0
================================================================
Comprehensive Pydantic and Dataclass schema contracts for:
1. 16 Metaphysics Computational Engines (San Shi, Ming Xue, Bu Shi, Xiang Xue, Ze Ji, Expanded Astro, Numerology)
2. 18 SVG Dynamic Visualizer Tools (Charts, Astrolabes, Matrix, Glassmorphism)
3. Question Focus Router Tool (6-Domain Alignment & Intent Classification)
4. 8-Master Multi-Agent Debate & Orchestrator Consensus Synthesis Tool
5. MCP (Model Context Protocol) Server Tool Manifests & API Router Contracts

Pure ASCII logging and RFC-compliant JSON Schema generation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ==============================================================================
# Common Enums & Base Models
# ==============================================================================

class MetaphysicsBranch(str, Enum):
    SAN_SHI = "san_shi"             # Tai Yi, Da Liu Ren, Qi Men Dun Jia
    MING_XUE = "ming_xue"           # BaZi, Zi Wei Dou Shu, Qi Zheng Si Yu
    BU_SHI = "bu_shi"               # I Ching, Liu Yao, Mei Hua Yi Shu
    XIANG_XUE = "xiang_xue"         # Xuan Kong Flying Stars, San He, Mian Xiang
    ZE_JI = "ze_ji"                 # Imperial Calendar Date Selection
    THAI_VEDIC = "thai_vedic"       # Thai Suriyayart & Vedic Nakshatra
    WESTERN_ASTRO = "western_astro" # Western Tropical & Uranian 8 TNPs
    NUMEROLOGY = "numerology"       # Satta-Lek 7-Base & Chaldean Numerology


class QuestionDomain(str, Enum):
    CAREER = "career"
    FINANCE = "finance"
    LOVE = "love"
    HEALTH = "health"
    FAMILY = "family"
    TIMING = "timing"


class SupportedLanguage(str, Enum):
    THAI = "th"
    ENGLISH = "en"
    CHINESE = "zh"


class MasterStance(str, Enum):
    AFFIRM = "affirm"
    CAUTIOUS = "cautious"
    CONDITIONAL = "conditional"
    NEUTRAL = "neutral"


class FiveElementsDistribution(BaseModel):
    """Distribution of the Five Elements (Wood, Fire, Earth, Metal, Water)."""
    wood: float = Field(0.0, ge=0.0, description="Wood (木) score / percentage")
    fire: float = Field(0.0, ge=0.0, description="Fire (火) score / percentage")
    earth: float = Field(0.0, ge=0.0, description="Earth (土) score / percentage")
    metal: float = Field(0.0, ge=0.0, description="Metal (金) score / percentage")
    water: float = Field(0.0, ge=0.0, description="Water (水) score / percentage")
    dominant: Optional[str] = Field(None, description="Dominant element")
    weakest: Optional[str] = Field(None, description="Weakest element")

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class PillarStemBranch(BaseModel):
    """Stem and Branch pair for a single pillar."""
    stem: str = Field(..., description="Heavenly Stem (天干)")
    branch: str = Field(..., description="Earthly Branch (地支)")
    element: Optional[str] = Field(None, description="Five Element of the stem/branch")
    polarity: Optional[str] = Field(None, description="Yin or Yang polarity")
    hidden_stems: List[str] = Field(default_factory=list, description="Hidden Stems (藏干)")
    ten_god: Optional[str] = Field(None, description="Ten God relationship to Day Master")
    na_yin: Optional[str] = Field(None, description="Na Yin sound element")

    model_config = ConfigDict(extra="allow", populate_by_name=True)


# ==============================================================================
# 1. Schemas for 16 Metaphysics Calculation Tools
# ==============================================================================

# --- Tool 1: BaZi (Four Pillars of Destiny) ---
class BaZiCalculateParams(BaseModel):
    """Parameters for BaZi Four Pillars calculation."""
    birth_datetime: str = Field(
        ...,
        description="Local birth datetime string in 'YYYY-MM-DD HH:MM:SS' format",
        json_schema_extra={"example": "1990-05-15 14:30:00"}
    )
    longitude: float = Field(
        100.4930,
        ge=-180.0,
        le=180.0,
        description="Birthplace longitude for True Solar Time (TST) correction",
        json_schema_extra={"example": 100.4930}
    )
    utc_offset_hours: float = Field(
        7.0,
        ge=-12.0,
        le=14.0,
        description="UTC time zone offset in decimal hours",
        json_schema_extra={"example": 7.0}
    )
    unknown_hour: bool = Field(
        False,
        description="Enable probabilistic 3-pillar mode if exact hour is unknown"
    )

    model_config = ConfigDict(extra="allow")


class BaZiCalculateResult(BaseModel):
    """Calculation result payload from BaZiEngine."""
    engine_version: Optional[str] = Field("1.0.0")
    engine_name: Optional[str] = Field("BaZi Four Pillars Engine")
    birth_datetime: Optional[str] = None
    solar_time_info: Any = Field(default_factory=dict, description="True Solar Time details")
    day_master: Any = Field(default_factory=dict, description="Day Master stem and element")
    pillars: Any = Field(default_factory=dict, description="Year, Month, Day, Hour pillars")
    five_elements: Any = Field(default_factory=dict, description="Five element scores and percentages")
    hidden_stems: Any = Field(default_factory=dict, description="Hidden stems per pillar")
    ten_gods: Any = Field(default_factory=dict, description="Ten Gods analysis")
    day_master_strength: Any = Field(None, description="Strong (身強) / Weak (身弱)")
    da_yun: Any = Field(default_factory=list, description="10-year luck pillars")
    favorable_elements: Any = Field(default_factory=dict)
    special_patterns: Any = Field(default_factory=list, description="Special chart patterns (Ge Ju)")

    model_config = ConfigDict(extra="allow")


# --- Tool 2: Zi Wei Dou Shu (Purple Star Astrology) ---
class ZiWeiCalculateParams(BaseModel):
    """Parameters for Zi Wei Dou Shu chart calculation."""
    year: int = Field(..., ge=1900, le=2100, description="Gregorian birth year")
    month: int = Field(..., ge=1, le=12, description="Gregorian birth month")
    day: int = Field(..., ge=1, le=31, description="Gregorian birth day")
    hour: int = Field(..., ge=0, le=23, description="Birth hour (0-23)")
    gender: Literal["male", "female"] = Field("male", description="Gender for Da Xian progression direction")

    model_config = ConfigDict(extra="allow")


class ZiWeiCalculateResult(BaseModel):
    """Calculation result payload from ZiWeiEngine."""
    engine: Optional[str] = Field("ZiWeiDouShuEngine")
    engine_name: Optional[str] = Field("Zi Wei Dou Shu Engine")
    ming_gong_branch: Optional[str] = Field(None, description="Life Palace branch (命宮)")
    shen_gong_branch: Optional[str] = Field(None, description="Body Palace branch (身宮)")
    five_element_bureau: Optional[str] = Field(None, description="Element bureau e.g. 水二局, 木三局, etc.")
    palaces: Any = Field(default_factory=list, description="12 Astrological Palaces")
    si_hua: Any = Field(default_factory=dict, description="4 Transformations: 化祿, 化權, 化科, 化忌")

    model_config = ConfigDict(extra="allow")


# --- Tool 3: Qi Men Dun Jia (Mystical Doors) ---
class QiMenCalculateParams(BaseModel):
    """Parameters for Qi Men Dun Jia 4-Plate chart calculation."""
    year: int = Field(..., ge=1900, le=2100, description="Calculation year")
    month: int = Field(..., ge=1, le=12, description="Calculation month")
    day: int = Field(..., ge=1, le=31, description="Calculation day")
    hour: int = Field(..., ge=0, le=23, description="Calculation hour (0-23)")

    model_config = ConfigDict(extra="allow")


class QiMenCalculateResult(BaseModel):
    """Calculation result payload from QiMenEngine."""
    engine: Optional[str] = Field("QiMenDunJiaEngine")
    engine_name: Optional[str] = Field("Qi Men Dun Jia Engine")
    solar_term: Optional[str] = Field(None, description="Active 24 Solar Term (節氣)")
    dun_type: Optional[str] = Field(None, description="Yang Dun (陽遁) or Yin Dun (陰遁)")
    ju_number: Optional[int] = Field(None, description="Ju number (1-9 局)")
    palaces: Any = Field(default_factory=dict, description="9 Palaces grid")
    nine_palaces: Optional[Any] = None

    model_config = ConfigDict(extra="allow")


# --- Tool 4: Da Liu Ren (Great Liu Ren) ---
class LiuRenCalculateParams(BaseModel):
    """Parameters for Da Liu Ren 3-Transmission & 4-Lesson calculation."""
    day_stem: str = Field("甲", description="Day Heavenly Stem (天干: 甲..癸)")
    day_branch: str = Field("子", description="Day Earthly Branch (地支: 子..亥)")
    month_general: str = Field("正月", description="Month General / Solar Month (月將)")
    hour_branch: str = Field("午", description="Hour Branch (占時地支)")

    model_config = ConfigDict(extra="allow")


class LiuRenCalculateResult(BaseModel):
    """Calculation result payload from LiuRenEngine."""
    engine: Optional[str] = Field("LiuRenEngine")
    engine_name: Optional[str] = Field("Da Liu Ren Engine")
    day_stem_branch: Optional[str] = None
    month_general: Optional[str] = None
    hour_branch: Optional[str] = None
    four_lessons: Any = Field(default_factory=dict, description="Four Lessons (四課)")
    three_transmissions: Any = Field(
        default_factory=dict,
        description="Three Transmissions: 初傳 (Initial), 中傳 (Middle), 末傳 (Final)"
    )
    heaven_plate: Any = Field(default_factory=dict, description="Heaven Plate positions")
    generals_plate: Any = Field(default_factory=dict, description="12 Heavenly Generals (十二天將)")

    model_config = ConfigDict(extra="allow")


# --- Tool 5: Tai Yi Shen Shu (Grand Tai Yi) ---
class TaiYiCalculateParams(BaseModel):
    """Parameters for Tai Yi Shen Shu calculation."""
    year: int = Field(..., ge=1900, le=2100, description="Calculation year")
    month: int = Field(..., ge=1, le=12, description="Calculation month")
    day: int = Field(..., ge=1, le=31, description="Calculation day")
    hour: int = Field(..., ge=0, le=23, description="Calculation hour (0-23)")

    model_config = ConfigDict(extra="allow")


class TaiYiCalculateResult(BaseModel):
    """Calculation result payload from TaiYiEngine."""
    engine: Optional[str] = Field("TaiYiEngine")
    engine_name: Optional[str] = Field("Tai Yi Shen Shu Engine")
    tai_yi_number: Optional[int] = Field(None, description="Tai Yi Ju Number")
    accumulated_years: Optional[int] = Field(None, description="Tai Yi Accumulated Years (太乙積年)")
    star_palace: Any = Field(default_factory=dict, description="16-path celestial star palace")
    strategic_assessment: Any = Field(default_factory=dict, description="Strategic assessment (吉/凶)")
    heaven_plate: Any = Field(default_factory=dict)
    earth_plate: Any = Field(default_factory=dict)
    palaces_16: Any = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")


# --- Tool 6: I Ching Divination (Book of Changes) ---
class IChingCalculateParams(BaseModel):
    """Parameters for I Ching Hexagram casting and calculation."""
    day_stem: str = Field("甲", description="Day Heavenly Stem for Liu Yao alignment")
    seed: Optional[int] = Field(None, description="Optional deterministic random seed")
    lines: Optional[List[int]] = Field(
        None,
        description="Optional pre-determined 6 lines (6=Old Yin, 7=Young Yang, 8=Young Yin, 9=Old Yang)"
    )

    model_config = ConfigDict(extra="allow")


class IChingCalculateResult(BaseModel):
    """Calculation result payload from IChingEngine."""
    engine: Optional[str] = Field("IChingEngine")
    engine_name: Optional[str] = Field("I Ching Engine")
    raw_lines: Optional[List[int]] = None
    primary_hexagram: Any = Field(..., description="Primary Hexagram (本卦)")
    transformed_hexagram: Optional[Any] = Field(None, description="Transformed Hexagram (變卦)")
    six_lines: Any = Field(default_factory=list, description="Six lines breakdown")

    model_config = ConfigDict(extra="allow")


# --- Tool 7: Liu Yao Divination (Six Lines Na Jia) ---
class LiuYaoCalculateParams(BaseModel):
    """Parameters for Liu Yao Na Jia 6-line divination."""
    lines: List[int] = Field(
        [7, 7, 7, 7, 7, 7],
        description="List of 6 line values (6, 7, 8, 9) from Line 1 (bottom) to Line 6 (top)"
    )
    day_stem_idx: int = Field(0, ge=0, le=9, description="Day stem index (0=甲, 1=乙, ..., 9=癸)")

    model_config = ConfigDict(extra="allow")


class LiuYaoCalculateResult(BaseModel):
    """Calculation result payload from LiuYaoEngine."""
    engine_name: Optional[str] = Field("Liu Yao Divination Engine")
    palace: Optional[str] = None
    palace_element: Optional[str] = None
    shi_line: Optional[int] = Field(None, description="Self / Subject line index (世爻 1-6)")
    ying_line: Optional[int] = Field(None, description="Other / Object line index (應爻 1-6)")
    lines: Any = Field(default_factory=list, description="6 Lines with Na Jia stems, branches, Relatives, and Spirits")

    model_config = ConfigDict(extra="allow")


# --- Tool 8: Mei Hua Plum Blossom Numerology ---
class MeiHuaCalculateParams(BaseModel):
    """Parameters for Mei Hua Plum Blossom Numerology calculation."""
    year: int = Field(2026, ge=1900, le=2100, description="Calculation year")
    month: int = Field(5, ge=1, le=12, description="Calculation month")
    day: int = Field(15, ge=1, le=31, description="Calculation day")
    hour: int = Field(14, ge=0, le=23, description="Calculation hour (0-23)")
    num1: Optional[int] = Field(None, description="Optional custom upper trigram number")
    num2: Optional[int] = Field(None, description="Optional custom lower trigram number")
    num3: Optional[int] = Field(None, description="Optional custom moving line number")

    model_config = ConfigDict(extra="allow")


class MeiHuaCalculateResult(BaseModel):
    """Calculation result payload from MeiHuaEngine."""
    engine_name: Optional[str] = Field("Mei Hua Plum Blossom Engine")
    primary_hexagram: Any = Field(..., description="Primary Hexagram (本卦)")
    body_function: Any = Field(default_factory=dict, description="Ti (Body) vs Yong (Function) analysis")
    mutual_hexagram: Any = Field(default_factory=dict, description="Mutual Hexagram (互卦)")
    transformed_hexagram: Any = Field(default_factory=dict, description="Transformed Hexagram (變卦)")

    model_config = ConfigDict(extra="allow")


# --- Tool 9: Xuan Kong Flying Stars (Geomancy) ---
class XuanKongCalculateParams(BaseModel):
    """Parameters for Xuan Kong Flying Stars calculation."""
    facing_degree: float = Field(
        180.0,
        ge=0.0,
        le=360.0,
        description="Compass facing direction degree (0.0 - 360.0)"
    )
    period: int = Field(9, ge=1, le=9, description="Feng Shui Period (1 to 9, currently Period 9: 2024-2043)")

    model_config = ConfigDict(extra="allow")


class XuanKongCalculateResult(BaseModel):
    """Calculation result payload from XuanKongEngine."""
    engine: Optional[str] = Field("XuanKongEngine")
    engine_name: Optional[str] = Field("Xuan Kong Flying Stars Engine")
    period: Optional[int] = None
    facing_degree: Optional[float] = None
    sitting_mountain: Optional[str] = Field(None, description="Sitting mountain (坐山) from 24 Mountains")
    facing_mountain: Optional[str] = Field(None, description="Facing mountain (向山) from 24 Mountains")
    grid_palaces: Any = Field(default_factory=dict, description="9-Grid Palace numbers and stars")

    model_config = ConfigDict(extra="allow")


# --- Tool 10: San He Feng Shui (Three Harmonies) ---
class SanHeCalculateParams(BaseModel):
    """Parameters for San He Feng Shui 24-Mountain & Water Method calculation."""
    sitting_degree: float = Field(0.0, ge=0.0, le=360.0, description="Sitting compass degree")
    facing_degree: float = Field(180.0, ge=0.0, le=360.0, description="Facing compass degree")
    water_incoming_degree: Optional[float] = Field(None, ge=0.0, le=360.0, description="Incoming water degree")
    water_outgoing_degree: Optional[float] = Field(None, ge=0.0, le=360.0, description="Outgoing water degree")

    model_config = ConfigDict(extra="allow")


class SanHeCalculateResult(BaseModel):
    """Calculation result payload from SanHeEngine."""
    engine_name: Optional[str] = Field("San He Feng Shui Engine")
    sitting_mountain: Optional[str] = None
    facing_mountain: Optional[str] = None
    san_he_formation: Any = Field(default_factory=dict, description="San He Trio harmony group")
    water_method: Any = Field(default_factory=dict, description="12 Life Stages Water Method")
    harmony_assessment: Any = Field(default_factory=dict, description="Water flow auspiciousness")
    twelve_stages_map: Any = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")


# --- Tool 11: Imperial Calendar Date Selection (Ze Ji) ---
class ZeJiCalculateParams(BaseModel):
    """Parameters for Date Selection suitability calculation."""
    year_branch: str = Field("午", description="Target Year Branch (e.g. 午 for 2026)")
    month_branch: str = Field("申", description="Target Month Branch")
    day_branch: str = Field("寅", description="Target Day Branch")
    user_birth_branch: Optional[str] = Field("子", description="User birth year branch for clash checking")
    activity: Optional[str] = Field(None, description="Proposed activity (e.g. 'wedding', 'opening', 'moving')")

    model_config = ConfigDict(extra="allow")


class ZeJiCalculateResult(BaseModel):
    """Calculation result payload from ZeJiEngine."""
    engine: Optional[str] = Field("ZeJiEngine")
    engine_name: Optional[str] = Field("Imperial Date Selection Engine")
    duty_officer: Optional[str] = Field(None, description="12 Duty Officer (建除十二神)")
    rating_stars: Optional[int] = Field(None, ge=1, le=5, description="Auspicious rating 1 to 5 stars")
    overall_status: Optional[str] = Field(None, description="Status: 'AUSPICIOUS', 'INAUSPICIOUS', 'NEUTRAL'")
    is_year_breaker: Optional[bool] = Field(None, description="Clashes with Year Branch (歲破)")
    is_month_breaker: Optional[bool] = Field(None, description="Clashes with Month Branch (月破)")
    activities_suitability: Any = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")


# --- Tool 12: Mian Xiang Physiognomy (Face Reading) ---
class MianXiangAnalyzeParams(BaseModel):
    """Parameters for Mian Xiang Physiognomy analysis."""
    features: Dict[str, Any] = Field(
        ...,
        description="Facial features dictionary (e.g. face_shape, forehead, eyes, nose, mouth, ears, chin, age)",
        json_schema_extra={
            "example": {
                "face_shape": "round",
                "forehead": "high_broad",
                "eyes": "clear_bright",
                "nose": "straight_fleshy",
                "mouth": "defined_edges",
                "ears": "thick_lobes",
                "chin": "rounded_firm",
                "age": 35
            }
        }
    )

    model_config = ConfigDict(extra="allow")


class MianXiangAnalyzeResult(BaseModel):
    """Analysis result payload from MianXiangEngine."""
    engine_name: Optional[str] = Field("Mian Xiang Physiognomy Engine")
    face_element: Optional[str] = Field(None, description="5-Element face shape classification")
    twelve_palaces: Any = Field(default_factory=dict, description="12 Facial Palaces assessment")
    five_officials: Any = Field(default_factory=dict, description="5 Facial Officials (五官)")
    overall_assessment: Any = Field(default_factory=dict, description="Comprehensive life reading")

    model_config = ConfigDict(extra="allow")


# --- Tool 13: Thai & Vedic Suriyayart Astrology ---
class ThaiVedicCalculateParams(BaseModel):
    """Parameters for Thai Suriyayart & Vedic Nakshatra calculation."""
    year: int = Field(1990, ge=1900, le=2100, description="Birth year")
    month: int = Field(5, ge=1, le=12, description="Birth month")
    day: int = Field(15, ge=1, le=31, description="Birth day")
    hour: int = Field(14, ge=0, le=23, description="Birth hour (0-23)")
    day_of_week: int = Field(2, ge=0, le=6, description="Day of week (0=Sunday .. 6=Saturday)")
    minute: int = Field(30, ge=0, le=59, description="Birth minute")

    model_config = ConfigDict(extra="allow")


class ThaiVedicCalculateResult(BaseModel):
    """Calculation result payload from ThaiVedicEngine."""
    engine: Optional[str] = Field("ThaiVedicEngine")
    engine_name: Optional[str] = Field("Thai Suriyayart & Vedic Engine")
    thai_lagna: Any = Field(default_factory=dict, description="Suriyayart 12-Rashi Ascendant / Lagna")
    maha_thaksa: Any = Field(default_factory=dict, description="8 Maha Thaksa planetary deities")
    vedic_nakshatra: Any = Field(default_factory=dict, description="27 Vedic Nakshatras")
    vimshottari_dasha: Any = Field(default_factory=dict, description="Vimshottari Dasha period cycle")

    model_config = ConfigDict(extra="allow")


# --- Tool 14: Western Tropical & Uranian Astrology ---
class WesternCalculateParams(BaseModel):
    """Parameters for Western Tropical & Uranian calculation."""
    year: int = Field(1990, ge=1900, le=2100, description="Birth year")
    month: int = Field(5, ge=1, le=12, description="Birth month")
    day: int = Field(15, ge=1, le=31, description="Birth day")
    hour: int = Field(14, ge=0, le=23, description="Birth hour")
    minute: int = Field(30, ge=0, le=59, description="Birth minute")
    latitude: float = Field(13.7563, description="Birth latitude (default Bangkok)")
    longitude: float = Field(100.5018, description="Birth longitude (default Bangkok)")

    model_config = ConfigDict(extra="allow")


class WesternCalculateResult(BaseModel):
    """Calculation result payload from WesternUranianEngine."""
    engine: Optional[str] = Field("WesternUranianEngine")
    engine_name: Optional[str] = Field("Western Tropical & Uranian Astrology Engine")
    planets_tropical: Any = Field(default_factory=dict, description="10 Tropical Planetary Positions")
    uranian_tnps: Any = Field(default_factory=dict, description="8 Uranian Transneptunians")
    planetary_aspects: Any = Field(default_factory=list, description="Planetary aspects")
    uranian_midpoint_formula: Any = Field(default_factory=dict, description="Midpoint Pictures (A+B-C)")

    model_config = ConfigDict(extra="allow")


# --- Tool 15: Satta-Lek 7-Base Numerology & Chaldean ---
class NumerologyCalculateParams(BaseModel):
    """Parameters for Satta-Lek 7-Base matrix and Chaldean numerology scoring."""
    text: str = Field(
        "0812345678",
        description="Phone number, name, car plate, or house number to analyze"
    )
    day_num: int = Field(2, ge=1, le=7, description="Birth day number (1=Sun .. 7=Sat)")
    lunar_month: int = Field(6, ge=1, le=12, description="Thai lunar birth month")
    year_zodiac_num: int = Field(7, ge=1, le=12, description="Thai zodiac year number (1=Rat .. 12=Pig)")

    model_config = ConfigDict(extra="allow")


class NumerologyCalculateResult(BaseModel):
    """Calculation result payload from NumerologyEngine."""
    engine: Optional[str] = Field("NumerologyEngine")
    engine_name: Optional[str] = Field("Numerology & Satta-Lek Engine")
    matrix_7_base: Any = Field(default_factory=dict, description="Satta-Lek 7-Base 4-Row Matrix")
    satta_lek: Optional[Any] = None
    chaldean_score: Optional[Any] = None

    model_config = ConfigDict(extra="allow")


# --- Tool 16: Qi Zheng Si Yu (Seven Governors & Four Shadows) ---
class QiZhengCalculateParams(BaseModel):
    """Parameters for Qi Zheng Si Yu Chinese astrology calculation."""
    year: int = Field(2026, ge=1900, le=2100, description="Calculation year")
    month: int = Field(5, ge=1, le=12, description="Calculation month")
    day: int = Field(15, ge=1, le=31, description="Calculation day")
    hour: int = Field(14, ge=0, le=23, description="Calculation hour (0-23)")

    model_config = ConfigDict(extra="allow")


class QiZhengCalculateResult(BaseModel):
    """Calculation result payload from QiZhengSiYuEngine."""
    engine: Optional[str] = Field("QiZhengSiYuEngine")
    engine_name: Optional[str] = Field("Qi Zheng Si Yu Engine")
    planets: Any = Field(default_factory=dict, description="7 Governors: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn")
    shadow_stars: Any = Field(default_factory=dict, description="4 Shadow Stars: Rahu, Ketu, Yuebei, Ziqi")
    lunar_mansions: Any = Field(default_factory=dict, description="Positions across 28 Lunar Mansions")

    model_config = ConfigDict(extra="allow")


# ==============================================================================
# 2. Schemas for 18 SVG Visualizer Tools
# ==============================================================================

class BaseRenderSVGParams(BaseModel):
    """Base parameter model for SVG rendering tools."""
    chart: Dict[str, Any] = Field(..., description="Structured calculation chart data")
    title: Optional[str] = Field(None, description="Optional custom chart title")
    lang: SupportedLanguage = Field(SupportedLanguage.THAI, description="Interface language code: 'th', 'en', 'zh'")
    save_to_disk: bool = Field(False, description="Whether to write the generated SVG to disk")
    output_filename: Optional[str] = Field(None, description="Custom filename if saving to disk")

    model_config = ConfigDict(extra="allow")


class RenderSVGResult(BaseModel):
    """Standard response payload for all SVG visualizer tools."""
    discipline: str = Field(..., description="Metaphysics discipline name")
    function_name: str = Field(..., description="SVG generator function name")
    svg_content: str = Field(..., description="Full well-formed XML SVG markup string")
    svg_length: int = Field(..., description="Character length of SVG content")
    viewBox: str = Field(..., description="SVG responsive viewBox dimensions (e.g. '0 0 800 600')")
    aspect_ratio: str = Field(..., description="Chart aspect ratio (e.g. '4:3', '1:1')")
    visual_components: List[str] = Field(default_factory=list, description="List of visual UI layers")
    svg_file: Optional[str] = Field(None, description="Relative file path if saved to disk")
    svg_snippet: str = Field(..., description="First 200 characters of SVG content preview")

    model_config = ConfigDict(extra="allow")


# Typed Parameter models for specific SVG visualizers
class RenderBaZiSVGParams(BaseRenderSVGParams):
    """Parameters for BaZi 4-Pillars dynamic SVG generator."""
    pass

class RenderZiWeiSVGParams(BaseRenderSVGParams):
    """Parameters for Zi Wei Dou Shu 12-Palace dynamic SVG generator."""
    pass

class RenderQiMenSVGParams(BaseRenderSVGParams):
    """Parameters for Qi Men Dun Jia 9-Palace matrix dynamic SVG generator."""
    pass

class RenderLiuRenSVGParams(BaseRenderSVGParams):
    """Parameters for Da Liu Ren 3-Transmission & 4-Lesson SVG generator."""
    pass

class RenderTaiYiSVGParams(BaseRenderSVGParams):
    """Parameters for Tai Yi Shen Shu 16-Path star palace SVG generator."""
    pass

class RenderIChingSVGParams(BaseRenderSVGParams):
    """Parameters for I Ching 64-Hexagram & changing lines SVG generator."""
    pass

class RenderLiuYaoSVGParams(BaseRenderSVGParams):
    """Parameters for Liu Yao Na Jia 6-Line & 6 Spirits SVG generator."""
    pass

class RenderMeiHuaSVGParams(BaseRenderSVGParams):
    """Parameters for Mei Hua Plum Blossom Ti/Yong Gua dynamic flow SVG generator."""
    pass

class RenderXuanKongSVGParams(BaseRenderSVGParams):
    """Parameters for Xuan Kong Flying Stars Period 9 9-Grid SVG generator."""
    pass

class RenderSanHeSVGParams(BaseRenderSVGParams):
    """Parameters for San He 24-Mountain & 12 Life Stages Water SVG generator."""
    pass

class RenderZeJiSVGParams(BaseRenderSVGParams):
    """Parameters for Imperial Date Selection 12 Duty Officers SVG generator."""
    pass

class RenderMianXiangSVGParams(BaseRenderSVGParams):
    """Parameters for Mian Xiang 12 Palaces & 5 Officials SVG generator."""
    pass

class RenderThaiVedicSVGParams(BaseRenderSVGParams):
    """Parameters for Thai Suriyayart & 27 Nakshatras SVG generator."""
    pass

class RenderWesternSVGParams(BaseRenderSVGParams):
    """Parameters for Western Tropical & Uranian TNPs SVG generator."""
    pass

class RenderNumerologySVGParams(BaseRenderSVGParams):
    """Parameters for Satta-Lek 7-Base 4-Row matrix SVG generator."""
    pass

class RenderQiZhengSVGParams(BaseRenderSVGParams):
    """Parameters for Qi Zheng Si Yu 7 Governors & 28 Mansions SVG generator."""
    pass

class RenderZodiacWheelSVGParams(BaseRenderSVGParams):
    """Parameters for 12 Zodiac Houses Radial Astrolabe SVG generator."""
    pass

class RenderMultimodalMatrixSVGParams(BaseModel):
    """Parameters for 16-Discipline Multimodal Consensus Matrix SVG generator."""
    data: Dict[str, Any] = Field(..., description="Consensus matrix and multi-discipline synthesis data")
    title: Optional[str] = Field(None, description="Optional custom matrix title")
    lang: SupportedLanguage = Field(SupportedLanguage.THAI, description="Language code")
    save_to_disk: bool = Field(False)
    output_filename: Optional[str] = Field(None)

    model_config = ConfigDict(extra="allow")


# ==============================================================================
# 3. Schemas for Question Focus Router Tool
# ==============================================================================

class QuestionFocusRouteParams(BaseModel):
    """Parameters for routing and classifying user metaphysics questions."""
    query: str = Field(
        ...,
        description="Natural language user query in Thai, English, or Chinese",
        json_schema_extra={"example": "ควรเปลี่ยนงานไปทำธุรกิจส่วนตัวปี 2026 ดีหรือไม่?"}
    )
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional contextual data (e.g. birth_datetime, known chart attributes)"
    )
    language: SupportedLanguage = Field(
        SupportedLanguage.THAI,
        description="Target output language"
    )

    model_config = ConfigDict(extra="allow")


class QuestionFocusRouteResult(BaseModel):
    """Result payload from QuestionFocusRouter."""
    classified_domain: QuestionDomain = Field(
        ...,
        description="Classified primary domain (career, finance, love, health, family, timing)"
    )
    domain_display_name: str = Field(..., description="Localized domain name (e.g. 'การงาน/ธุรกิจ')")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Classification confidence score (0.0 - 1.0)")
    matched_keywords: List[str] = Field(default_factory=list, description="Keywords triggered during classification")
    domain_scores: Dict[str, float] = Field(default_factory=dict, description="Raw scoring across all 6 domains")
    recommended_engines: List[str] = Field(
        default_factory=list,
        description="Ordered list of recommended computational engines for this question"
    )
    focus_directives: Dict[str, str] = Field(
        default_factory=dict,
        description="Engine-specific prompt focus instructions (e.g. bazi, ziwei, qimen)"
    )
    analysis_guide: str = Field(..., description="High-level synthesis guidance for LLM orchestrator")

    model_config = ConfigDict(extra="allow")


# ==============================================================================
# 4. Schemas for 8-Master Debate & Consensus Synthesis Tool
# ==============================================================================

class MasterPerspectiveSchema(BaseModel):
    """Perspective and analysis from one of the 8 Metaphysics Masters."""
    branch: str = Field(..., description="Metaphysical branch label (e.g. '三式 (San Shi)')")
    focus: str = Field(..., description="Specific engine focus")
    analysis: str = Field(..., description="Master's analytical narrative")
    canonical_citations: List[str] = Field(
        default_factory=list,
        description="Classical treatises cited (e.g. ['滴天髓', '子平真詮'])"
    )
    stance: MasterStance = Field(MasterStance.AFFIRM, description="Master's stance: affirm, cautious, conditional, neutral")
    stance_confidence: float = Field(0.8, ge=0.0, le=1.0, description="Confidence in master's recommendation")

    model_config = ConfigDict(extra="allow")


class ConsensusMatrixSchema(BaseModel):
    """Objective consensus matrix calculated across all participating masters."""
    baseline_anchor: str = Field(
        "BaZi Five Elements Distribution & Day Master",
        description="Baseline anchor for cross-system consensus"
    )
    consensus_score: float = Field(..., ge=0.0, le=1.0, description="Unified consensus score (0.0 to 1.0)")
    favorable_elements: List[str] = Field(default_factory=list, description="Consensus favorable elements")
    consonance_factors: List[str] = Field(default_factory=list, description="Points of agreement across masters")
    cautionary_factors: List[str] = Field(default_factory=list, description="Risk factors and points of caution")

    model_config = ConfigDict(extra="allow")


class HITLRoutingSchema(BaseModel):
    """Human-in-the-Loop triage routing decision."""
    status: str = Field(..., description="HITL status (e.g. 'QUEUED_FOR_HUMAN_REVIEW', 'APPROVED')")
    reason: str = Field(..., description="Reason for routing decision")
    review_queue_id: str = Field(..., description="Unique review identifier")
    required_human_review: bool = Field(..., description="Flag if human master review is mandatory")
    conflict_detected: bool = Field(..., description="Flag if significant divergence exists between masters")
    conflicting_domains: List[str] = Field(default_factory=list, description="List of masters with cautious/conditional stances")
    consensus_breakdown: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Breakdown of masters by stance"
    )
    decision_matrix: Dict[str, float] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class OrchestratorSynthesisSchema(BaseModel):
    """Synthesis and executive verdict produced by the Orchestrator."""
    consensus_facts: List[str] = Field(default_factory=list, description="Established canonical facts")
    analytical_counter_queries: List[str] = Field(default_factory=list, description="Cross-system observations")
    consensus_score: float = Field(..., ge=0.0, le=1.0)
    required_human_review: bool = Field(...)
    conflict_detected: bool = Field(...)
    conflicting_domains: List[str] = Field(default_factory=list)
    hitl_routing: Optional[HITLRoutingSchema] = None

    model_config = ConfigDict(extra="allow")


class MetaphysicsDebateParams(BaseModel):
    """Parameters for running the 8-Master Peer Debate & Synthesis."""
    query: str = Field(
        ...,
        description="User question to be evaluated by all 8 Masters",
        json_schema_extra={"example": "วิเคราะห์ดวงชะตาและฤกษ์ยามมงคลในการขยายธุรกิจ"}
    )
    birth_datetime: str = Field(
        "1990-05-15 14:30:00",
        description="Birth datetime in 'YYYY-MM-DD HH:MM:SS' format"
    )
    longitude: float = Field(100.4930, ge=-180.0, le=180.0, description="Birth longitude")
    utc_offset_hours: float = Field(7.0, ge=-12.0, le=14.0, description="UTC offset")
    unknown_hour: bool = Field(False, description="Unknown birth hour flag")
    language: SupportedLanguage = Field(SupportedLanguage.THAI, description="Response language")
    force_hitl: bool = Field(False, description="Force routing into HITL queue for manual master review")
    active_masters: Optional[List[str]] = Field(
        None,
        description="Optional list of specific masters to activate. Defaults to all 8 masters."
    )

    model_config = ConfigDict(extra="allow")


class MetaphysicsDebateResult(BaseModel):
    """Complete result payload from MetaphysicsDebateEngine."""
    status: Literal["DEBATE_COMPLETED", "DEBATE_FAILED"] = Field("DEBATE_COMPLETED")
    query: str
    consensus_matrix: ConsensusMatrixSchema
    domain_perspectives: Dict[str, MasterPerspectiveSchema]
    orchestrator_synthesis: OrchestratorSynthesisSchema

    model_config = ConfigDict(extra="allow")


# ==============================================================================
# 5. MCP Server Protocol Models & Tool Manifest Registry
# ==============================================================================

class MCPToolDefinition(BaseModel):
    """Standard Model Context Protocol tool definition descriptor."""
    name: str = Field(..., description="Unique tool identifier")
    description: str = Field(..., description="Human and LLM readable tool description")
    parameters: Dict[str, Any] = Field(..., description="JSON Schema object for tool parameters")

    model_config = ConfigDict(extra="allow")


class MCPManifestSchema(BaseModel):
    """MCP Server manifest containing all exposed tool contracts."""
    name: str = Field("horo-consultant-mcp")
    version: str = Field("1.0.0")
    description: str = Field("Computational Metaphysics & Dynamic Visualizer MCP Server for thClaws Harness")
    tools: List[MCPToolDefinition] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")


class MCPCallToolRequest(BaseModel):
    """Incoming request to invoke an MCP tool."""
    tool_name: str = Field(..., description="Name of the tool to execute")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Tool input arguments matching schema")

    model_config = ConfigDict(extra="allow")


class MCPCallToolResponse(BaseModel):
    """Response returned from executing an MCP tool."""
    tool_name: str
    success: bool = Field(..., description="Whether tool execution succeeded")
    result: Optional[Dict[str, Any]] = Field(None, description="Structured result output if successful")
    error: Optional[str] = Field(None, description="Error message if execution failed")
    execution_time_ms: Optional[float] = Field(None, description="Execution duration in milliseconds")

    model_config = ConfigDict(extra="allow")


# ------------------------------------------------------------------------------
# Tool Schema Registry & JSON Schema Exporter
# ------------------------------------------------------------------------------

MCP_TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {
    # 16 Metaphysics Calculation Tools
    "bazi_calculate": {
        "description": "Compute BaZi 4 Pillars chart with True Solar Time (TST), Five Elements scores, Day Master strength, and Ten Gods.",
        "param_model": BaZiCalculateParams,
        "result_model": BaZiCalculateResult,
        "category": "calculation",
        "branch": MetaphysicsBranch.MING_XUE,
    },
    "ziwei_calculate": {
        "description": "Compute Zi Wei Dou Shu purple star chart with 12 Palaces, 14 Major Stars, 4 Si Hua transformations, and Five Element Bureau.",
        "param_model": ZiWeiCalculateParams,
        "result_model": ZiWeiCalculateResult,
        "category": "calculation",
        "branch": MetaphysicsBranch.MING_XUE,
    },
    "qimen_calculate": {
        "description": "Compute Qi Men Dun Jia 4-Plate chart (Yang/Yin Dun 1-9 Ju, 8 Doors, 9 Stars, 8 Deities, and 9-Palace Matrix).",
        "param_model": QiMenCalculateParams,
        "result_model": QiMenCalculateResult,
        "category": "calculation",
        "branch": MetaphysicsBranch.SAN_SHI,
    },
    "liuren_calculate": {
        "description": "Compute Da Liu Ren 3-Transmission (Initial/Middle/Final) and 4-Lesson divination chart with 12 Heavenly Generals.",
        "param_model": LiuRenCalculateParams,
        "result_model": LiuRenCalculateResult,
        "category": "calculation",
        "branch": MetaphysicsBranch.SAN_SHI,
    },
    "tai_yi_calculate": {
        "description": "Compute Tai Yi Shen Shu 16-Path celestial star palaces, 72-cycle accumulated years, and strategic assessment.",
        "param_model": TaiYiCalculateParams,
        "result_model": TaiYiCalculateResult,
        "category": "calculation",
        "branch": MetaphysicsBranch.SAN_SHI,
    },
    "iching_calculate": {
        "description": "Cast and compute I Ching 64-Hexagram divination with moving lines, primary hexagram, and transformed hexagram.",
        "param_model": IChingCalculateParams,
        "result_model": IChingCalculateResult,
        "category": "calculation",
        "branch": MetaphysicsBranch.BU_SHI,
    },
    "liu_yao_calculate": {
        "description": "Compute Liu Yao Na Jia 6-line divination with 5 Relatives (五親), 6 Celestial Animals/Spirits (六神), and Shi/Ying lines.",
        "param_model": LiuYaoCalculateParams,
        "result_model": LiuYaoCalculateResult,
        "category": "calculation",
        "branch": MetaphysicsBranch.BU_SHI,
    },
    "mei_hua_calculate": {
        "description": "Compute Mei Hua Plum Blossom Numerology Ti (Body) vs Yong (Function) trigram dynamic interaction and mutual hexagrams.",
        "param_model": MeiHuaCalculateParams,
        "result_model": MeiHuaCalculateResult,
        "category": "calculation",
        "branch": MetaphysicsBranch.BU_SHI,
    },
    "xuankong_calculate": {
        "description": "Compute Xuan Kong Flying Stars Period 9 (2024-2043) 9-Grid Palace chart with 24 Mountains sitting and facing stars.",
        "param_model": XuanKongCalculateParams,
        "result_model": XuanKongCalculateResult,
        "category": "calculation",
        "branch": MetaphysicsBranch.XIANG_XUE,
    },
    "san_he_calculate": {
        "description": "Compute San He 24-Mountain compass and 12 Life Stages Water Method (長生十二宮水法) for landscape geomancy.",
        "param_model": SanHeCalculateParams,
        "result_model": SanHeCalculateResult,
        "category": "calculation",
        "branch": MetaphysicsBranch.XIANG_XUE,
    },
    "zeji_calculate": {
        "description": "Compute Imperial Calendar Date Selection suitability via 12 Duty Officers (建除十二神), Year/Month Breakers, and star ratings.",
        "param_model": ZeJiCalculateParams,
        "result_model": ZeJiCalculateResult,
        "category": "calculation",
        "branch": MetaphysicsBranch.ZE_JI,
    },
    "mian_xiang_analyze": {
        "description": "Analyze 12 Face Palaces, 5 Facial Officials, and 100-Year Age Fortune Flow based on classical physiognomy rules.",
        "param_model": MianXiangAnalyzeParams,
        "result_model": MianXiangAnalyzeResult,
        "category": "calculation",
        "branch": MetaphysicsBranch.XIANG_XUE,
    },
    "thaivedic_calculate": {
        "description": "Compute Thai Suriyayart 10 Lagna, 8 Maha Thaksa planetary deities (Sri/Kalakini), 27 Vedic Nakshatras, and Vimshottari Dasha.",
        "param_model": ThaiVedicCalculateParams,
        "result_model": ThaiVedicCalculateResult,
        "category": "calculation",
        "branch": MetaphysicsBranch.THAI_VEDIC,
    },
    "western_calculate": {
        "description": "Compute Western Tropical planetary positions, aspects, 8 Uranian Transneptunians (TNPs), and Midpoint Pictures (A+B-C).",
        "param_model": WesternCalculateParams,
        "result_model": WesternCalculateResult,
        "category": "calculation",
        "branch": MetaphysicsBranch.WESTERN_ASTRO,
    },
    "numerology_calculate": {
        "description": "Compute Satta-Lek 7-Base 4-Row Matrix, Base 4 planetary power sum, and pure Chaldean numerology scoring.",
        "param_model": NumerologyCalculateParams,
        "result_model": NumerologyCalculateResult,
        "category": "calculation",
        "branch": MetaphysicsBranch.NUMEROLOGY,
    },
    "qi_zheng_calculate": {
        "description": "Compute Qi Zheng Si Yu 7 Governors and 4 Shadow Stars mapped across 28 Lunar Mansions and 12 Zodiac Mansions.",
        "param_model": QiZhengCalculateParams,
        "result_model": QiZhengCalculateResult,
        "category": "calculation",
        "branch": MetaphysicsBranch.MING_XUE,
    },

    # 18 SVG Visualizer Tools
    "render_bazi_svg": {
        "description": "Render BaZi 4-Pillars dynamic SVG chart (viewBox 0 0 800 600) with Five Elements progress bars and glassmorphism styling.",
        "param_model": RenderBaZiSVGParams,
        "result_model": RenderSVGResult,
        "category": "visualizer",
    },
    "render_ziwei_svg": {
        "description": "Render Zi Wei Dou Shu 12-Palace square grid dynamic SVG chart (viewBox 0 0 800 800) with 14 Major Stars and Si Hua badges.",
        "param_model": RenderZiWeiSVGParams,
        "result_model": RenderSVGResult,
        "category": "visualizer",
    },
    "render_qimen_svg": {
        "description": "Render Qi Men Dun Jia 3x3 9-Palace matrix dynamic SVG chart (viewBox 0 0 600 600) with 8 Doors, 9 Stars, and 8 Deities.",
        "param_model": RenderQiMenSVGParams,
        "result_model": RenderSVGResult,
        "category": "visualizer",
    },
    "render_liuren_svg": {
        "description": "Render Da Liu Ren 3-Transmission & 4-Lesson flow dynamic SVG chart (viewBox 0 0 600 400).",
        "param_model": RenderLiuRenSVGParams,
        "result_model": RenderSVGResult,
        "category": "visualizer",
    },
    "render_tai_yi_svg": {
        "description": "Render Tai Yi Shen Shu 16-Path celestial star palace dynamic SVG chart (viewBox 0 0 800 600).",
        "param_model": RenderTaiYiSVGParams,
        "result_model": RenderSVGResult,
        "category": "visualizer",
    },
    "render_iching_svg": {
        "description": "Render I Ching 64-Hexagram primary & transformed hexagram dynamic SVG chart (viewBox 0 0 600 500).",
        "param_model": RenderIChingSVGParams,
        "result_model": RenderSVGResult,
        "category": "visualizer",
    },
    "render_liu_yao_svg": {
        "description": "Render Liu Yao Na Jia 6-Line grid & 6 Celestial Spirits dynamic SVG chart (viewBox 0 0 800 600).",
        "param_model": RenderLiuYaoSVGParams,
        "result_model": RenderSVGResult,
        "category": "visualizer",
    },
    "render_meihua_svg": {
        "description": "Render Mei Hua Plum Blossom Ti/Yong Gua dynamic flow SVG chart (viewBox 0 0 800 600).",
        "param_model": RenderMeiHuaSVGParams,
        "result_model": RenderSVGResult,
        "category": "visualizer",
    },
    "render_xuankong_svg": {
        "description": "Render Xuan Kong Flying Stars Period 9 9-Grid dynamic SVG chart (viewBox 0 0 600 600).",
        "param_model": RenderXuanKongSVGParams,
        "result_model": RenderSVGResult,
        "category": "visualizer",
    },
    "render_sanhe_svg": {
        "description": "Render San He 24-Mountain compass and 12 Life Stages Water Method SVG chart (viewBox 0 0 800 600).",
        "param_model": RenderSanHeSVGParams,
        "result_model": RenderSVGResult,
        "category": "visualizer",
    },
    "render_zeji_svg": {
        "description": "Render Imperial Date Selection 12 Duty Officers & star rating SVG card (viewBox 0 0 600 350).",
        "param_model": RenderZeJiSVGParams,
        "result_model": RenderSVGResult,
        "category": "visualizer",
    },
    "render_mianxiang_svg": {
        "description": "Render Mian Xiang 12 Palaces, 5 Officials, and 100-Year Age Flow SVG chart (viewBox 0 0 800 600).",
        "param_model": RenderMianXiangSVGParams,
        "result_model": RenderSVGResult,
        "category": "visualizer",
    },
    "render_thaivedic_svg": {
        "description": "Render Thai Suriyayart Lagna, 8 Maha Thaksa, and 27 Nakshatras SVG chart (viewBox 0 0 600 450).",
        "param_model": RenderThaiVedicSVGParams,
        "result_model": RenderSVGResult,
        "category": "visualizer",
    },
    "render_western_svg": {
        "description": "Render Western Tropical & Uranian 8 TNPs midpoint reflection SVG chart (viewBox 0 0 600 450).",
        "param_model": RenderWesternSVGParams,
        "result_model": RenderSVGResult,
        "category": "visualizer",
    },
    "render_numerology_svg": {
        "description": "Render Satta-Lek 7-Base 4-Row Matrix & Chaldean score card SVG (viewBox 0 0 760 530).",
        "param_model": RenderNumerologySVGParams,
        "result_model": RenderSVGResult,
        "category": "visualizer",
    },
    "render_qizheng_svg": {
        "description": "Render Qi Zheng Si Yu 7 Governors & 28 Lunar Mansions SVG chart (viewBox 0 0 800 600).",
        "param_model": RenderQiZhengSVGParams,
        "result_model": RenderSVGResult,
        "category": "visualizer",
    },
    "render_zodiac_wheel_svg": {
        "description": "Render 12 Zodiac Houses Radial Astrolabe SVG chart (viewBox 0 0 600 600).",
        "param_model": RenderZodiacWheelSVGParams,
        "result_model": RenderSVGResult,
        "category": "visualizer",
    },
    "render_multimodal_matrix_svg": {
        "description": "Render 16-Discipline Multimodal Consensus Matrix and Radar Hologram SVG (viewBox 0 0 800 600).",
        "param_model": RenderMultimodalMatrixSVGParams,
        "result_model": RenderSVGResult,
        "category": "visualizer",
    },

    # Question Focus Router Tool
    "question_focus_route": {
        "description": "Classify user question into 6 domains (career, finance, love, health, family, timing) and generate engine focus directives.",
        "param_model": QuestionFocusRouteParams,
        "result_model": QuestionFocusRouteResult,
        "category": "router",
    },

    # 8-Master Multi-Agent Debate Tool
    "metaphysics_debate": {
        "description": "Execute peer debate across 8 Metaphysics Masters, calculate consensus score, detect conflicts, and generate orchestrator synthesis.",
        "param_model": MetaphysicsDebateParams,
        "result_model": MetaphysicsDebateResult,
        "category": "debate",
    }
}


def get_mcp_tool_definitions() -> List[MCPToolDefinition]:
    """Generate RFC-compliant MCP Tool Definitions for all registered tools."""
    tools: List[MCPToolDefinition] = []
    for name, spec in MCP_TOOL_REGISTRY.items():
        param_model = spec["param_model"]
        schema = param_model.model_json_schema()
        tools.append(
            MCPToolDefinition(
                name=name,
                description=spec["description"],
                parameters=schema
            )
        )
    return tools


def get_full_mcp_manifest() -> MCPManifestSchema:
    """Generate full MCP server tool manifest containing all 36 tools."""
    return MCPManifestSchema(
        name="horo-consultant-mcp",
        version="1.0.0",
        description="Unified Computational Metaphysics MCP Server (16 Calculation Tools + 18 Visualizer Tools + Focus Router + 8-Master Debate)",
        tools=get_mcp_tool_definitions()
    )
