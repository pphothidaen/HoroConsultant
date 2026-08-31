"""
Qi Zheng Si Yu (七政四餘) Engine
=================================
Calculates Qi Zheng Si Yu (7 Governors & 4 Shadow Stars) alongside
the 28 Lunar Mansions (二十八宿) with classical unequal degree boundaries
across the 4 Celestial Directions (East Azure Dragon, North Black Tortoise,
West White Tiger, South Vermilion Bird).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from project.core.base_engine import AbstractAstrologyEngine, EngineChartResult
from project.core.swiss_ephemeris import calculate_qi_zheng_si_yu

LUNAR_MANSIONS = [
    "角", "亢", "氐", "房", "心", "尾", "箕",  # Eastern Azure Dragon (東方青龍)
    "斗", "牛", "女", "虛", "危", "室", "壁",  # Northern Black Tortoise (北方玄武)
    "奎", "婁", "胃", "昴", "畢", "觜", "參",  # Western White Tiger (西方白虎)
    "井", "鬼", "柳", "星", "張", "翼", "軫",  # Southern Vermilion Bird (南方朱雀)
]

# Classical 28 Lunar Mansions Data (name, span_deg, direction, beast_symbol, element, animal, pinyin, thai)
_MANSION_RAW_DATA: list[tuple[str, float, str, str, str, str, str, str]] = [
    # East Azure Dragon (東方青龍) — 7 Mansions (75.0°)
    ("角", 12.0, "East", "Azure Dragon (東方青龍)", "木", "蛟", "Jiǎo Mù Jiāo", "เจี่ยว (มังกรไม้)"),
    ("亢", 9.0,  "East", "Azure Dragon (東方青龍)", "金", "龍", "Kàng Jīn Lóng", "คั่ง (มังกรทอง)"),
    ("氐", 15.0, "East", "Azure Dragon (東方青龍)", "土", "貉", "Dǐ Tǔ Hè", "ตี่ (หมาแบดเจอร์ดั้งดิน)"),
    ("房", 5.0,  "East", "Azure Dragon (東方青龍)", "日", "兔", "Fáng Rì Tù", "ฝาง (กระต่ายสุริยัน)"),
    ("心", 5.0,  "East", "Azure Dragon (東方青龍)", "月", "狐", "Xīn Yuè Hú", "ซิน (จิ้งจอกจันทรา)"),
    ("尾", 18.0, "East", "Azure Dragon (東方青龍)", "火", "虎", "Wěi Huǒ Hǔ", "เหว่ย (เสืออัคคี)"),
    ("箕", 11.0, "East", "Azure Dragon (東方青龍)", "水", "豹", "Jī Shuǐ Bào", "จี (เสือดาววารี)"),

    # North Black Tortoise (北方玄武) — 7 Mansions (98.0°)
    ("斗", 26.0, "North", "Black Tortoise (北方玄武)", "木", "獬", "Dǒu Mù Xiè", "โต่ว (สัตว์ศักดิ์สิทธิ์ไม้)"),
    ("牛", 8.0,  "North", "Black Tortoise (北方玄武)", "金", "牛", "Niú Jīn Niú", "หนิว (วัวทอง)"),
    ("女", 12.0, "North", "Black Tortoise (北方玄武)", "土", "蝠", "Nǚ Tǔ Fú", "หนี่ว์ (ค้างคาวดิน)"),
    ("虛", 10.0, "North", "Black Tortoise (北方玄武)", "日", "鼠", "Xū Rì Shǔ", "ซวี (หนูสุริยัน)"),
    ("危", 17.0, "North", "Black Tortoise (北方玄武)", "月", "燕", "Wēi Yuè Yàn", "เวย (นกนางแอ่นจันทรา)"),
    ("室", 16.0, "North", "Black Tortoise (北方玄武)", "火", "豬", "Shì Huǒ Zhū", "ซื่อ (หมูอัคคี)"),
    ("壁", 9.0,  "North", "Black Tortoise (北方玄武)", "水", "貐", "Bì Shuǐ Yǔ", "ปี้ (สัตว์น้ำวารี)"),

    # West White Tiger (西方白虎) — 7 Mansions (80.0°)
    ("奎", 16.0, "West", "White Tiger (西方白虎)", "木", "狼", "Kuí Mù Láng", "ขุย (หมาป่าไม้)"),
    ("婁", 12.0, "West", "White Tiger (西方白虎)", "金", "狗", "Lóu Jīn Gǒu", "โหลว (สุนัขทอง)"),
    ("胃", 14.0, "West", "White Tiger (西方白虎)", "土", "雉", "Wèi Tǔ Zhì", "เว่ย (ไก่ฟ้าดิน)"),
    ("昴", 11.0, "West", "White Tiger (西方白虎)", "日", "雞", "Mǎo Rì Jī", "เหมา (ไก่สุริยัน)"),
    ("畢", 16.0, "West", "White Tiger (西方白虎)", "月", "烏", "Bì Yuè Wū", "ปี้ (กาดำจันทรา)"),
    ("觜", 2.0,  "West", "White Tiger (西方白虎)", "火", "猴", "Zī Huǒ Hóu", "จือ (ลิงอัคคี)"),
    ("參", 9.0,  "West", "White Tiger (西方白虎)", "水", "猿", "Shēn Shuǐ Yuán", "เซิน (ชะนีวารี)"),

    # South Vermilion Bird (南方朱雀) — 7 Mansions (107.0°)
    ("井", 33.0, "South", "Vermilion Bird (南方朱雀)", "木", "犴", "Jǐng Mù Àn", "จิ่ง (สมเสร็จไม้)"),
    ("鬼", 3.0,  "South", "Vermilion Bird (南方朱雀)", "金", "羊", "Guǐ Jīn Yáng", "กุ่ย (แพะทอง)"),
    ("柳", 15.0, "South", "Vermilion Bird (南方朱雀)", "土", "獐", "Liǔ Tǔ Zhāng", "หลิ่ว (กวางดิน)"),
    ("星", 7.0,  "South", "Vermilion Bird (南方朱雀)", "日", "馬", "Xīng Rì Mǎ", "ซิง (ม้าสุริยัน)"),
    ("張", 18.0, "South", "Vermilion Bird (南方朱雀)", "月", "鹿", "Zhāng Yuè Lù", "จาง (กวางจันทรา)"),
    ("翼", 18.0, "South", "Vermilion Bird (南方朱雀)", "火", "蛇", "Yì Huǒ Shé", "อี้ (งูอัคคี)"),
    ("軫", 13.0, "South", "Vermilion Bird (南方朱雀)", "水", "蚓", "Zhěn Shuǐ Yǐn", "เจิ่น (ไส้เดือนวารี)"),
]

# Build cumulative boundary degree lookup table
MANSION_TABLE: list[dict[str, Any]] = []
_cumulative_deg = 0.0

for name, span, direction, beast, element, animal, pinyin, thai in _MANSION_RAW_DATA:
    start_deg = _cumulative_deg
    end_deg = _cumulative_deg + span
    MANSION_TABLE.append({
        "name": name,
        "full_name": f"{name}{element}{animal}",
        "span": span,
        "start_deg": round(start_deg, 4),
        "end_deg": round(end_deg, 4),
        "direction": direction,
        "beast_symbol": beast,
        "element": element,
        "animal": animal,
        "pinyin": pinyin,
        "thai": thai,
    })
    _cumulative_deg = end_deg


class QiZhengSiYuEngine(AbstractAstrologyEngine):
    """
    Qi Zheng Si Yu (七政四餘) Engine.
    Implements 7 Planetary Governors, 4 Shadow Star Nodes, and
    classical unequal 28 Lunar Mansions resolution.
    """

    @property
    def engine_name(self) -> str:
        return "Qi Zheng Si Yu Engine"

    @property
    def system_type(self) -> str:
        return "chinese_astrology"

    def get_lunar_mansion(self, degree: float) -> str:
        """
        Return the 28 Lunar Mansion name corresponding to a given celestial degree (0.0 - 360.0)
        using classical unequal degree boundaries.
        """
        norm_deg = degree % 360.0
        for entry in MANSION_TABLE:
            if entry["start_deg"] <= norm_deg < entry["end_deg"]:
                return entry["name"]
        return MANSION_TABLE[-1]["name"] if norm_deg >= MANSION_TABLE[-1]["start_deg"] else MANSION_TABLE[0]["name"]

    def get_lunar_mansion_detail(self, degree: float) -> dict[str, Any]:
        """
        Return comprehensive lunar mansion details, including degree offset into the mansion,
        element, direction, beast symbol, and romanized representations.
        """
        norm_deg = degree % 360.0
        selected = MANSION_TABLE[0]
        for entry in MANSION_TABLE:
            if entry["start_deg"] <= norm_deg < entry["end_deg"]:
                selected = entry
                break
        else:
            if norm_deg >= MANSION_TABLE[-1]["start_deg"]:
                selected = MANSION_TABLE[-1]

        offset = norm_deg - selected["start_deg"]
        return {
            "mansion": selected["name"],
            "full_name": selected["full_name"],
            "pinyin": selected["pinyin"],
            "thai": selected["thai"],
            "direction": selected["direction"],
            "beast_symbol": selected["beast_symbol"],
            "element": selected["element"],
            "animal": selected["animal"],
            "start_degree": selected["start_deg"],
            "end_degree": selected["end_deg"],
            "degree_span": selected["span"],
            "degree_offset": round(offset, 4),
            "degree_percentage": round((offset / selected["span"]) * 100.0, 2),
        }

    def calculate(
        self,
        year: int,
        month: int,
        day: int,
        hour: int = 12,
        longitude: float = 100.0,
        latitude: float = 13.0,
        **kwargs: Any,
    ) -> EngineChartResult:
        """
        Calculate complete Qi Zheng Si Yu astrological chart.
        """
        dt = datetime(year, month, day, hour)
        ephemeris_data = calculate_qi_zheng_si_yu(dt, longitude, latitude)
        planets_data = ephemeris_data.get("planets_longitudes", {})

        planets: dict[str, float] = {}
        shadow_stars: dict[str, float] = {}

        planet_keys = [
            "日 (Sun)", "月 (Moon)", "木 (Jupiter)", "火 (Mars)",
            "土 (Saturn)", "金 (Venus)", "水 (Mercury)",
        ]
        shadow_keys = [
            "羅睺 (Rahu)", "計都 (Ketu)", "月孛 (Yuebei)", "紫氣 (Ziqi)",
        ]

        for k in planet_keys:
            if k in planets_data:
                planets[k] = planets_data[k]

        for k in shadow_keys:
            if k in planets_data:
                shadow_stars[k] = planets_data[k]

        ayanamsa_degrees = 24.0  # Classical sidereal degree offset

        all_bodies = {**planets, **shadow_stars}
        lunar_mansions = {
            k: self.get_lunar_mansion((v - ayanamsa_degrees) % 360.0)
            for k, v in all_bodies.items()
        }
        lunar_mansion_details = {
            k: self.get_lunar_mansion_detail((v - ayanamsa_degrees) % 360.0)
            for k, v in all_bodies.items()
        }

        raw = {
            "datetime": dt.isoformat(),
            "coordinates": {"longitude": longitude, "latitude": latitude},
            "planets": planets,
            "shadow_stars": shadow_stars,
            "lunar_mansions": lunar_mansions,
            "lunar_mansion_details": lunar_mansion_details,
            "ayanamsa_degrees": ayanamsa_degrees,
            "source": ephemeris_data.get("source", "unknown"),
        }

        return EngineChartResult(
            engine_name=self.engine_name,
            system_type=self.system_type,
            chart_data=raw,
        )

