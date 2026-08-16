"""
project/core/svg_generator.py
==============================
Generates standalone, high-aesthetic SVG vector charts for all Metaphysical Disciplines:
  1. BaZi 4 Pillars Chart (ผังดวง 4 เสาชะตา)
  2. Zodiac Wheel Chart (ผังดวงจักรราศี 12 ราศี)
  3. Zi Wei Dou Shu 12-Palace Chart (ผังดวง紫微斗數)
  4. Qi Men Dun Jia 9-Grid Chart (ผังดวง奇門遁甲)
  5. Xuan Kong Flying Stars Chart (ผังดวง玄空風水)
  6. Da Liu Ren 3 Transmissions Chart (ผังดวง大六壬)
  7. I Ching Liu Yao Line Chart (ผังดวง易經六爻)
  8. Date Selection Ze Ji Rating Chart (ผังดวง擇吉คำนวณฤกษ์)
  9. Thai Suriyayart & Vedic Nakshatra Chart (ผังดวงโหราศาสตร์ไทย & ภารตวิทยา)
  10. Western Tropical & Uranian TNP Chart (ผังดวงโหราศาสตร์สากล & ยูเรเนียน)
  11. Satta-Lek 7-Base Numerology Matrix Chart (ผังดวงสัตตเลข 7 ฐาน)

Uses clean SVG markup with element color themes, traditional Chinese/Thai typography,
and Five Elements harmony indicators.
"""

from __future__ import annotations

from typing import Any

try:
    import rust_core
    RUST_AVAILABLE = True
except ImportError:
    RUST_AVAILABLE = False

# The installed PyO3 SVG call signatures predate the complete-chart contract
# and discard palace/star/element fields.  They remain PARKED at this adapter;
# the PyO3-free render_* candidates must pass public-byte parity separately.
LOSSLESS_NATIVE_SVG_ADAPTER = False

ELEMENT_COLORS = {
    "Wood":  "#10b981",  # Emerald Green
    "Fire":  "#ef4444",  # Crimson Red
    "Earth": "#d97706",  # Amber Ochre
    "Metal": "#38bdf8",  # Celestial Silver Blue
    "Water": "#8b5cf6",  # Deep Sapphire Purple
}

ZODIAC_THAI = [
    "ราศีเมษ (Aries)", "ราศีพฤษภ (Taurus)", "ราศีเมถุน (Gemini)", "ราศีกรกฎ (Cancer)",
    "ราศีสิงห์ (Leo)", "ราศีกันย์ (Virgo)", "ราศีตุลย์ (Libra)", "ราศีพิจิก (Scorpio)",
    "ราศีธนู (Sagittarius)", "ราศีมังกร (Capricorn)", "ราศีกุมภ์ (Aquarius)", "ราศีมีน (Pisces)"
]

SVG_LOCALES: dict[str, dict[str, str]] = {
    "th": {
        "bazi": "ผังดวงชะตา BaZi 4 เสา (Four Pillars of Destiny)",
        "zodiac": "ผังดวงจักรราศี 12 ราศี (Zodiac Wheel)",
        "ziwei": "ผังดวง紫微斗數 (Zi Wei Dou Shu 12 Palaces Chart)",
        "qimen": "ผังดวง奇門遁甲 (Qi Men Dun Jia 4-Plate Grid)",
        "xuankong": "ผังดวง玄空風水 (Xuan Kong Flying Stars 9-Grid)",
        "liuren": "ผังดวง大六壬 (Da Liu Ren 3-Transmission Chart)",
        "iching": "ผังดวง易經六爻 (I Ching Divination Chart)",
        "zeji": "ผังดวง擇吉คำนวณฤกษ์ (Date Selection Chart)",
        "thaivedic": "ผังดวงโหราศาสตร์ไทย & ภารตวิทยา (Thai & Vedic)",
        "western": "ผังดวงโหราศาสตร์สากล & ยูเรเนียน (Western & Uranian)",
        "numerology": "ผังดวงสัตตเลข 7 ฐาน & เลขศาสตร์ (Numerology)",
        "taiyi": "ผังดวง太乙神數 (Tai Yi Shen Shu 16-Path Chart)",
        "liuyao": "ผังดวง六爻預測 (Liu Yao 6-Line Na Jia Chart)",
        "meihua": "ผังดวง梅花易數 (Mei Hua Plum Blossom Numerology)",
        "sanhe": "ผังดวง三合風水 (San He 24-Mountain Water Flow Compass)",
        "qizheng": "ผังดวง七政四餘 (Qi Zheng Si Yu Astrolabe)",
        "mianxiang": "ผังดวง麻衣神相 (Mian Xiang 12 Facial Palaces)",
        "multimodal": "ผังดวงสังเคราะห์ 16 ศาสตร์ (Unified Multimodal Metaphysics Matrix)",
        "hour_pillar": "เสายาม",
        "day_pillar": "เสาวัน",
        "month_pillar": "เสาเดือน",
        "year_pillar": "เสาปี",
        "five_elements": "สมดุล 5 ธาตุ",
    },
    "en": {
        "bazi": "BaZi Four Pillars of Destiny Chart",
        "zodiac": "12 Zodiac Signs Celestial Wheel",
        "ziwei": "Zi Wei Dou Shu 12-Palace Matrix",
        "qimen": "Qi Men Dun Jia 4-Plate Celestial Grid",
        "xuankong": "Xuan Kong Flying Stars 9-Grid Chart",
        "liuren": "Da Liu Ren 3-Transmissions Astrolabe",
        "iching": "I Ching & Liu Yao Hexagram Transformation",
        "zeji": "Ze Ji Auspicious Date & Time Selection",
        "thaivedic": "Thai Vedic & Jyotish 12 Rashi Chart",
        "western": "Western Tropical & Uranian Astrolabe",
        "numerology": "Satta-Lek 7-Base & Chaldean Matrix",
        "taiyi": "Tai Yi Shen Shu 16-Path Celestial Wheel",
        "liuyao": "Liu Yao 6-Line Na Jia Divination Plate",
        "meihua": "Mei Hua Plum Blossom Hexagram Flow",
        "sanhe": "San He 24-Mountain Water Flow Compass",
        "qizheng": "Qi Zheng Si Yu 28-Mansion Astrolabe",
        "mianxiang": "Mian Xiang 12 Facial Palaces Map",
        "multimodal": "Unified 16-Discipline Multimodal Consensus Matrix",
        "hour_pillar": "Hour Pillar",
        "day_pillar": "Day Pillar",
        "month_pillar": "Month Pillar",
        "year_pillar": "Year Pillar",
        "five_elements": "5 Elements Balance",
    },
    "zh": {
        "bazi": "四柱八字命盤 (Four Pillars of Destiny)",
        "zodiac": "十二黃道宮位天盤 (Zodiac Wheel)",
        "ziwei": "紫微斗數十二宮命盤 (Zi Wei Dou Shu)",
        "qimen": "奇門遁甲四盤九宮局 (Qi Men Dun Jia)",
        "xuankong": "玄空九星飛星排盤 (Xuan Kong)",
        "liuren": "大六壬四課三傳天盤 (Da Liu Ren)",
        "iching": "周易六爻動靜變卦盤 (I Ching)",
        "zeji": "協紀辨方擇吉通書盤 (Ze Ji Timing)",
        "thaivedic": "泰國吠陀印度占星盤 (Thai Vedic)",
        "western": "西洋漢堡學派星盤 (Western Uranian)",
        "numerology": "泰國七基數與迦勒底數字矩陣",
        "taiyi": "太乙神數十六神道九宮局 (Tai Yi)",
        "liuyao": "六爻納甲六親六獸卦盤 (Liu Yao)",
        "meihua": "梅花易數體用互變卦流 (Mei Hua)",
        "sanhe": "三合風水二十四山水法羅盤 (San He)",
        "qizheng": "七政四餘二十八宿天星盤 (Qi Zheng)",
        "mianxiang": "麻衣神相十二宮百歲流年圖 (Mian Xiang)",
        "multimodal": "16門術數大一統全息共識羅盤 (Multimodal)",
        "hour_pillar": "時柱",
        "day_pillar": "日柱",
        "month_pillar": "月柱",
        "year_pillar": "年柱",
        "five_elements": "五行平衡度",
    }
}


def _resolve_svg_title(key: str, custom_title: str | None = None, lang: str = "th") -> str:
    if custom_title and not custom_title.startswith("ผังดวง"):
        return custom_title
    loc = SVG_LOCALES.get(lang, SVG_LOCALES["th"])
    return loc.get(key, SVG_LOCALES["th"].get(key, custom_title or key))


def generate_bazi_svg(chart: dict[str, Any], title: str | None = None, lang: str = "th") -> str:
    """Generate clean SVG string for BaZi 4 Pillars Chart."""
    title = _resolve_svg_title("bazi", title, lang)
    loc = SVG_LOCALES.get(lang, SVG_LOCALES["th"])
    dm = chart.get("day_master", {})
    pcts = chart.get("five_elements", {}).get("percentages", {})
    tst  = str(chart.get("solar_time_info", {}).get("tst_datetime", "N/A"))
    pillars = chart.get("pillars", {})

    if LOSSLESS_NATIVE_SVG_ADAPTER and RUST_AVAILABLE and hasattr(rust_core, "build_bazi_svg_rust"):
        try:
            hp = pillars.get("hour", {})
            dp = pillars.get("day", {})
            mp = pillars.get("month", {})
            yp = pillars.get("year", {})
            return rust_core.build_bazi_svg_rust(
                title,
                str(dm.get("stem", "")),
                str(dm.get("element", "")),
                tst,
                float(sum(pcts.values())),
                (str(hp.get("stem", {}).get("char", "")), str(hp.get("branch", {}).get("char", ""))),
                (str(dp.get("stem", {}).get("char", "")), str(dp.get("branch", {}).get("char", ""))),
                (str(mp.get("stem", {}).get("char", "")), str(mp.get("branch", {}).get("char", ""))),
                (str(yp.get("stem", {}).get("char", "")), str(yp.get("branch", {}).get("char", ""))),
            )
        except Exception:
            pass

    order = [
        ("hour", loc.get("hour_pillar", "เสายาม")),
        ("day", loc.get("day_pillar", "เสาวัน")),
        ("month", loc.get("month_pillar", "เสาเดือน")),
        ("year", loc.get("year_pillar", "เสาปี"))
    ]

    svg_parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" width="100%" height="100%">',
        '  <defs>',
        '    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">',
        '      <stop offset="0%" stop-color="#0a0c16"/>',
        '      <stop offset="100%" stop-color="#12182b"/>',
        '    </linearGradient>',
        '    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">',
        '      <feGaussianBlur stdDeviation="4" result="blur"/>',
        '      <feComposite in="SourceGraphic" in2="blur" operator="over"/>',
        '    </filter>',
        '  </defs>',
        '  <rect width="800" height="600" rx="16" fill="url(#bgGrad)" stroke="#334155" stroke-width="2"/>',
        f'  <text x="400" y="45" font-family="Prompt, sans-serif" font-size="22" font-weight="bold" fill="#fbbf24" text-anchor="middle" filter="url(#glow)">☯ {title}</text>',
        f'  <text x="400" y="75" font-family="Prompt, sans-serif" font-size="13" fill="#94a3b8" text-anchor="middle">True Solar Time (TST): {tst} | Day Master: {dm.get("stem","")} ({dm.get("element","")} {dm.get("polarity","")})</text>',
        '  <g transform="translate(60, 100)">'
    ]

    col_width = 160
    for idx, (p_key, p_label) in enumerate(order):
        p_data = pillars.get(p_key, {})
        stem   = p_data.get("stem", {})
        branch = p_data.get("branch", {})
        x_pos  = idx * col_width

        s_elem  = stem.get("element", "Metal")
        b_elem  = branch.get("element", "Water")
        s_color = ELEMENT_COLORS.get(s_elem, "#ffffff")
        b_color = ELEMENT_COLORS.get(b_elem, "#ffffff")

        svg_parts.append(f'    <rect x="{x_pos+10}" y="10" width="140" height="320" rx="12" fill="#1e293b" fill-opacity="0.6" stroke="#475569" stroke-width="1.5"/>')
        svg_parts.append(f'    <text x="{x_pos+80}" y="35" font-family="Prompt, sans-serif" font-size="14" font-weight="bold" fill="#94a3b8" text-anchor="middle">{p_label}</text>')
        svg_parts.append(f'    <rect x="{x_pos+25}" y="50" width="110" height="110" rx="10" fill="{s_color}" fill-opacity="0.15" stroke="{s_color}" stroke-width="2"/>')
        svg_parts.append(f'    <text x="{x_pos+80}" y="115" font-family="sans-serif" font-size="46" font-weight="bold" fill="{s_color}" text-anchor="middle">{stem.get("char","?")}</text>')
        svg_parts.append(f'    <text x="{x_pos+80}" y="145" font-family="Prompt, sans-serif" font-size="12" fill="#e2e8f0" text-anchor="middle">{stem.get("pinyin","")} ({stem.get("element","")})</text>')
        svg_parts.append(f'    <rect x="{x_pos+25}" y="180" width="110" height="110" rx="10" fill="{b_color}" fill-opacity="0.15" stroke="{b_color}" stroke-width="2"/>')
        svg_parts.append(f'    <text x="{x_pos+80}" y="245" font-family="sans-serif" font-size="46" font-weight="bold" fill="{b_color}" text-anchor="middle">{branch.get("char","?")}</text>')
        svg_parts.append(f'    <text x="{x_pos+80}" y="275" font-family="Prompt, sans-serif" font-size="12" fill="#e2e8f0" text-anchor="middle">{branch.get("pinyin","")} ({branch.get("zodiac","")})</text>')

    svg_parts.append('  </g>')
    svg_parts.append('  <g transform="translate(60, 450)">')
    svg_parts.append('    <text x="0" y="0" font-family="Prompt, sans-serif" font-size="15" font-weight="bold" fill="#fbbf24">⚖️ สัดส่วนสมดุล 5 ธาตุ (Five Elements Harmony)</text>')
    
    elems = ["Wood", "Fire", "Earth", "Metal", "Water"]
    bar_x = 0
    for el in elems:
        pct = pcts.get(el, 0.0)
        color = ELEMENT_COLORS.get(el, "#ffffff")
        width = int((pct / 100.0) * 120)
        svg_parts.append(f'    <text x="{bar_x}" y="28" font-family="Prompt, sans-serif" font-size="12" fill="{color}">{el}: {pct:.1f}%</text>')
        svg_parts.append(f'    <rect x="{bar_x}" y="35" width="120" height="10" rx="5" fill="#334155"/>')
        svg_parts.append(f'    <rect x="{bar_x}" y="35" width="{width}" height="10" rx="5" fill="{color}"/>')
        bar_x += 135

    svg_parts.append('  </g>')
    svg_parts.append('</svg>')
    return "\n".join(svg_parts)


def generate_zodiac_wheel_svg(chart: dict[str, Any], title: str | None = None, lang: str = "th") -> str:
    """Generate clean SVG string for 12 Zodiac Wheel Chart."""
    title = _resolve_svg_title("zodiac", title, lang)
    if RUST_AVAILABLE and hasattr(rust_core, "build_zodiac_svg_rust"):
        try:
            return rust_core.build_zodiac_svg_rust(title)
        except Exception:
            pass

    import math
    svg_parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="100%" height="100%">',
        '  <rect width="600" height="600" rx="16" fill="#0b0f19" stroke="#0284c7" stroke-width="2"/>',
        f'  <text x="300" y="40" font-family="Prompt, sans-serif" font-size="20" font-weight="bold" fill="#38bdf8" text-anchor="middle">🌌 {title}</text>',
        '  <g transform="translate(300, 310)">',
        '    <circle r="220" fill="none" stroke="#334155" stroke-width="3"/>',
        '    <circle r="140" fill="none" stroke="#0284c7" stroke-dasharray="4,4" stroke-width="1.5"/>',
        '    <circle r="60" fill="#1e293b" stroke="#38bdf8" stroke-width="2"/>',
        '    <text x="0" y="5" font-family="sans-serif" font-size="22" font-weight="bold" fill="#fbbf24" text-anchor="middle">☯</text>'
    ]

    for i in range(12):
        angle = i * (360.0 / 12.0) - 90.0
        rad   = math.radians(angle)
        x_outer = 220 * math.cos(rad)
        y_outer = 220 * math.sin(rad)
        x_inner = 60 * math.cos(rad)
        y_inner = 60 * math.sin(rad)
        
        mid_angle = angle + 15.0
        mid_rad   = math.radians(mid_angle)
        x_text    = 180 * math.cos(mid_rad)
        y_text    = 180 * math.sin(mid_rad)

        svg_parts.append(f'    <line x1="{x_inner:.1f}" y1="{y_inner:.1f}" x2="{x_outer:.1f}" y2="{y_outer:.1f}" stroke="#334155" stroke-width="1.5"/>')
        svg_parts.append(f'    <text x="{x_text:.1f}" y="{y_text:.1f}" font-family="Prompt, sans-serif" font-size="11" fill="#e2e8f0" text-anchor="middle" dominant-baseline="central">{ZODIAC_THAI[i].split()[0]}</text>')

    svg_parts.append('  </g>')
    svg_parts.append('</svg>')
    return "\n".join(svg_parts)


def generate_ziwei_svg(chart: dict[str, Any], title: str | None = None, lang: str = "th") -> str:
    """Generate clean SVG string for Zi Wei Dou Shu 12 Palaces Chart."""
    title = _resolve_svg_title("ziwei", title, lang)
    palaces = chart.get("palaces", [])
    bureau = str(chart.get("five_element_bureau", "水二局"))
    ming_branch = str(chart.get("ming_gong_branch", "寅"))
    shen_branch = str(chart.get("shen_gong_branch", "申"))

    if LOSSLESS_NATIVE_SVG_ADAPTER and RUST_AVAILABLE and hasattr(rust_core, "build_ziwei_svg_rust"):
        try:
            return rust_core.build_ziwei_svg_rust(title, bureau, ming_branch, shen_branch)
        except Exception:
            pass

    svg_parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 800" width="100%" height="100%">',
        '  <rect width="800" height="800" rx="16" fill="#0c0718" stroke="#a855f7" stroke-width="2"/>',
        f'  <text x="400" y="45" font-family="Prompt, sans-serif" font-size="22" font-weight="bold" fill="#c084fc" text-anchor="middle">🔮 {title}</text>',
        f'  <text x="400" y="75" font-family="Prompt, sans-serif" font-size="13" fill="#e9d5ff" text-anchor="middle">五行局: {bureau} | 命宮: {ming_branch} | 身宮: {shen_branch}</text>',
        '  <rect x="250" y="250" width="300" height="300" rx="12" fill="#180e29" stroke="#9333ea" stroke-width="2"/>',
        '  <text x="400" y="380" font-family="sans-serif" font-size="36" font-weight="bold" fill="#c084fc" text-anchor="middle">紫微斗數</text>',
        '  <text x="400" y="420" font-family="Prompt, sans-serif" font-size="14" fill="#a855f7" text-anchor="middle">Computational Metaphysics Engine</text>',
        '  <g transform="translate(40, 100)">'
    ]

    grid_coords = [
        (3, 0), (2, 0), (1, 0), (0, 0),
        (0, 1), (0, 2), (0, 3), (1, 3),
        (2, 3), (3, 3), (3, 2), (3, 1)
    ]

    box_w, box_h = 170, 150
    for idx, p in enumerate(palaces[:12]):
        col, row = grid_coords[idx % 12]
        x = col * 180
        y = row * 160

        stroke_color = "#eab308" if p.get("is_ming_gong") else ("#ec4899" if p.get("is_shen_gong") else "#4c1d95")
        bg_fill = "#2e1065" if p.get("is_ming_gong") else "#1e1b4b"

        svg_parts.append(f'    <rect x="{x}" y="{y}" width="{box_w}" height="{box_h}" rx="8" fill="{bg_fill}" stroke="{stroke_color}" stroke-width="2"/>')
        svg_parts.append(f'    <text x="{x+10}" y="{y+25}" font-family="Prompt, sans-serif" font-size="14" font-weight="bold" fill="#fef08a">{p.get("palace_name","")} ({p.get("earth_branch","")})</text>')
        stars_str = " ".join(p.get("stars", [])) or "無主星"
        svg_parts.append(f'    <text x="{x+10}" y="{y+65}" font-family="sans-serif" font-size="16" font-weight="bold" fill="#c084fc">{stars_str}</text>')
        mutators = p.get("mutators", [])
        if mutators:
            svg_parts.append(f'    <text x="{x+10}" y="{y+105}" font-family="Prompt, sans-serif" font-size="12" fill="#f43f5e">四化: {" ".join(mutators)}</text>')

    svg_parts.append('  </g>')
    svg_parts.append('</svg>')
    return "\n".join(svg_parts)


def generate_qimen_svg(chart: dict[str, Any], title: str | None = None, lang: str = "th") -> str:
    """Generate clean SVG string for Qi Men Dun Jia 9-Grid Chart."""
    title = _resolve_svg_title("qimen", title, lang)
    solar_term = str(chart.get("solar_term", "冬至"))
    dun_type = str(chart.get("dun_type", "Yang"))
    ju_num = int(chart.get("ju_number", 1))

    if LOSSLESS_NATIVE_SVG_ADAPTER and RUST_AVAILABLE and hasattr(rust_core, "build_qimen_svg_rust"):
        try:
            return rust_core.build_qimen_svg_rust(title, solar_term, dun_type, ju_num)
        except Exception:
            pass

    palaces = chart.get("palaces", [])
    svg_parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="100%" height="100%">',
        '  <rect width="600" height="600" rx="16" fill="#09131d" stroke="#3b82f6" stroke-width="2"/>',
        f'  <text x="300" y="40" font-family="Prompt, sans-serif" font-size="20" font-weight="bold" fill="#60a5fa" text-anchor="middle">⚡ {title}</text>',
        f'  <text x="300" y="65" font-family="Prompt, sans-serif" font-size="12" fill="#93c5fd" text-anchor="middle">節氣: {solar_term} | 陰陽遁: {dun_type}遁 {ju_num}局</text>',
        '  <g transform="translate(45, 90)">'
    ]

    grid_map = {1: (1, 2), 2: (2, 0), 3: (0, 1), 4: (0, 0), 5: (1, 1), 6: (2, 2), 7: (2, 1), 8: (0, 2), 9: (1, 0)}
    for p in palaces:
        p_num = p.get("palace_number", 5)
        col, row = grid_map.get(p_num, (1, 1))
        x = col * 170
        y = row * 155
        svg_parts.append(f'    <rect x="{x}" y="{y}" width="160" height="145" rx="8" fill="#1e293b" stroke="#1d4ed8" stroke-width="1.5"/>')
        svg_parts.append(f'    <text x="{x+10}" y="{y+25}" font-family="Prompt, sans-serif" font-size="13" font-weight="bold" fill="#93c5fd">宮位 {p_num}</text>')
        svg_parts.append(f'    <text x="{x+10}" y="{y+55}" font-family="sans-serif" font-size="14" fill="#38bdf8">九星: {p.get("star","")}</text>')
        svg_parts.append(f'    <text x="{x+10}" y="{y+85}" font-family="sans-serif" font-size="14" fill="#4ade80">八門: {p.get("door","")}</text>')
        svg_parts.append(f'    <text x="{x+10}" y="{y+115}" font-family="sans-serif" font-size="14" fill="#fbbf24">八神: {p.get("spirit","")}</text>')

    svg_parts.append('  </g>')
    svg_parts.append('</svg>')
    return "\n".join(svg_parts)


def generate_xuankong_svg(chart: dict[str, Any], title: str | None = None, lang: str = "th") -> str:
    """Generate clean SVG string for Xuan Kong Flying Stars 9-Grid Chart."""
    title = _resolve_svg_title("xuankong", title, lang)
    period = int(chart.get("period", 9))
    facing = str(chart.get("facing_mountain", "午"))
    sitting = str(chart.get("sitting_mountain", "子"))
    facing_degree = float(chart.get("facing_degree", 180.0))

    if LOSSLESS_NATIVE_SVG_ADAPTER and RUST_AVAILABLE and hasattr(rust_core, "build_xuankong_svg_rust"):
        try:
            return rust_core.build_xuankong_svg_rust(title, facing_degree, period)
        except Exception:
            pass
    grid_palaces = chart.get("grid_palaces", [])

    svg_parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="100%" height="100%">',
        '  <rect width="600" height="600" rx="16" fill="#1a0914" stroke="#ec4899" stroke-width="2"/>',
        f'  <text x="300" y="40" font-family="Prompt, sans-serif" font-size="20" font-weight="bold" fill="#f472b6" text-anchor="middle">🏯 {title}</text>',
        f'  <text x="300" y="65" font-family="Prompt, sans-serif" font-size="12" fill="#fbcfe8" text-anchor="middle">九運: 第 {period} 運 | 向首: {facing} | 坐山: {sitting}</text>',
        '  <g transform="translate(45, 90)">'
    ]

    grid_map = {4: (0, 0), 9: (1, 0), 2: (2, 0), 3: (0, 1), 5: (1, 1), 7: (2, 1), 8: (0, 2), 1: (1, 2), 6: (2, 2)}
    for p in grid_palaces:
        p_num = p.get("palace_number", 5)
        col, row = grid_map.get(p_num, (1, 1))
        x = col * 170
        y = row * 155
        svg_parts.append(f'    <rect x="{x}" y="{y}" width="160" height="145" rx="8" fill="#2d1222" stroke="#be185d" stroke-width="1.5"/>')
        svg_parts.append(f'    <text x="{x+10}" y="{y+25}" font-family="Prompt, sans-serif" font-size="14" font-weight="bold" fill="#fbcfe8">{p.get("direction","")} ({p.get("palace_name","")})</text>')
        svg_parts.append(f'    <text x="{x+25}" y="{y+75}" font-family="sans-serif" font-size="32" font-weight="bold" fill="#38bdf8">{p.get("sitting_star","")}</text>')
        svg_parts.append(f'    <text x="{x+115}" y="{y+75}" font-family="sans-serif" font-size="32" font-weight="bold" fill="#f43f5e">{p.get("facing_star","")}</text>')
        svg_parts.append(f'    <text x="{x+70}" y="{y+120}" font-family="sans-serif" font-size="22" font-weight="bold" fill="#fbbf24">{p.get("base_star","")}</text>')

    svg_parts.append('  </g>')
    svg_parts.append('</svg>')
    return "\n".join(svg_parts)


def generate_liuren_svg(chart: dict[str, Any], title: str | None = None, lang: str = "th") -> str:
    """Generate SVG string for Da Liu Ren chart."""
    title = _resolve_svg_title("liuren", title, lang)
    trans = chart.get("three_transmissions", {})
    four_lessons = chart.get("four_lessons", [])
    svg_parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 400" width="100%" height="100%">',
        '  <rect width="600" height="400" rx="16" fill="#041812" stroke="#22c55e" stroke-width="2"/>',
        f'  <text x="300" y="40" font-family="Prompt, sans-serif" font-size="20" font-weight="bold" fill="#4ade80" text-anchor="middle">🌊 {title}</text>',
        f'  <text x="300" y="65" font-family="Prompt, sans-serif" font-size="12" fill="#86efac" text-anchor="middle">日干支: {chart.get("day_stem_branch","")} | 月將: {chart.get("month_general","")} | 占時: {chart.get("hour_branch","")}</text>',
        '  <g transform="translate(30, 90)">',
        '    <rect x="0" y="0" width="540" height="110" rx="10" fill="#064e3b" stroke="#10b981" stroke-width="1.5"/>',
        '    <text x="20" y="30" font-family="Prompt, sans-serif" font-size="14" font-weight="bold" fill="#34d399">三傳 (3 Transmissions):</text>',
        f'    <text x="20" y="65" font-family="sans-serif" font-size="16" fill="#fef08a">初傳: {trans.get("初傳 (發端)","")}  |  中傳: {trans.get("中傳 (移革)","")}  |  末傳: {trans.get("末傳 (歸結)","")}</text>',
        '  </g>',
        '  <g transform="translate(30, 220)">',
        '    <rect x="0" y="0" width="540" height="150" rx="10" fill="#022c22" stroke="#059669" stroke-width="1.5"/>',
        '    <text x="20" y="30" font-family="Prompt, sans-serif" font-size="14" font-weight="bold" fill="#34d399">四課 (4 Lessons):</text>'
    ]
    for idx, l in enumerate(four_lessons[:4]):
        x = 20 + idx * 130
        svg_parts.append(f'    <text x="{x}" y="70" font-family="Prompt, sans-serif" font-size="13" fill="#a7f3d0">{l.get("lesson_name","")}:</text>')
        svg_parts.append(f'    <text x="{x}" y="105" font-family="sans-serif" font-size="18" font-weight="bold" fill="#ffffff">{l.get("bottom","")} → {l.get("top","")}</text>')

    svg_parts.append('  </g>')
    svg_parts.append('</svg>')
    return "\n".join(svg_parts)


def generate_iching_svg(chart: dict[str, Any], title: str | None = None, lang: str = "th") -> str:
    """Generate SVG string for I Ching Hexagram chart."""
    title = _resolve_svg_title("iching", title, lang)
    pri = chart.get("primary_hexagram", {})
    trans = chart.get("transformed_hexagram", {})
    six_lines = chart.get("six_lines", [])

    svg_parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 500" width="100%" height="100%">',
        '  <rect width="600" height="500" rx="16" fill="#1b1204" stroke="#f59e0b" stroke-width="2"/>',
        f'  <text x="300" y="40" font-family="Prompt, sans-serif" font-size="20" font-weight="bold" fill="#fbbf24" text-anchor="middle">☯ {title}</text>',
        f'  <text x="300" y="65" font-family="Prompt, sans-serif" font-size="13" fill="#fde68a" text-anchor="middle">本卦: {pri.get("name","")} ({pri.get("nature","")})  ➔  變卦: {trans.get("name","")}</text>',
        '  <g transform="translate(40, 95)">'
    ]

    for idx, line in enumerate(reversed(six_lines)):
        y = idx * 60
        is_moving = line.get("is_moving", False)
        val = line.get("line_value", 7)
        color = "#fbbf24" if is_moving else "#d97706"

        svg_parts.append(f'    <rect x="0" y="{y}" width="520" height="48" rx="8" fill="#291e0a" stroke="{color}" stroke-width="1.5"/>')
        svg_parts.append(f'    <text x="15" y="{y+30}" font-family="Prompt, sans-serif" font-size="14" font-weight="bold" fill="#fef08a">爻 {line.get("line_number","")}: {line.get("line_type","")}</text>')
        svg_parts.append(f'    <text x="180" y="{y+30}" font-family="Prompt, sans-serif" font-size="13" fill="#ffffff">[{line.get("relative","")}]  六神: {line.get("animal","")}</text>')
        if is_moving:
            svg_parts.append(f'    <text x="440" y="{y+30}" font-family="Prompt, sans-serif" font-size="13" font-weight="bold" fill="#ef4444">⚡ 動爻</text>')

    svg_parts.append('  </g>')
    svg_parts.append('</svg>')
    return "\n".join(svg_parts)


def generate_zeji_svg(chart: dict[str, Any], title: str | None = None, lang: str = "th") -> str:
    """Generate SVG string for Ze Ji Date Selection chart."""
    title = _resolve_svg_title("zeji", title, lang)
    officer = chart.get("duty_officer", "建")
    stars = chart.get("rating_stars", "⭐⭐⭐")
    status = chart.get("overall_status", "吉")

    svg_parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 350" width="100%" height="100%">',
        '  <rect width="600" height="350" rx="16" fill="#031620" stroke="#0ea5e9" stroke-width="2"/>',
        f'  <text x="300" y="40" font-family="Prompt, sans-serif" font-size="20" font-weight="bold" fill="#38bdf8" text-anchor="middle">📅 {title}</text>',
        f'  <text x="300" y="70" font-family="Prompt, sans-serif" font-size="14" fill="#bae6fd" text-anchor="middle">建除十二神: {officer} | ระดับความมงคล: {stars} ({status})</text>',
        '  <g transform="translate(40, 100)">',
        '    <rect x="0" y="0" width="520" height="210" rx="12" fill="#072b3e" stroke="#0284c7" stroke-width="1.5"/>',
        f'    <text x="20" y="35" font-family="Prompt, sans-serif" font-size="14" font-weight="bold" fill="#7dd3fc">คำอธิบายฤกษ์: {chart.get("duty_description","")}</text>',
        '    <line x1="20" y1="55" x2="500" y2="55" stroke="#0284c7" stroke-dasharray="3,3"/>'
    ]

    suits = chart.get("activities_suitability", {})
    y = 85
    for act, res in list(suits.items())[:5]:
        icon = "✅ 宜" if res == "宜" else ("❌ 忌" if res == "忌" else "⚖️ 平")
        color = "#4ade80" if res == "宜" else ("#f87171" if res == "忌" else "#fbbf24")
        svg_parts.append(f'    <text x="20" y="{y}" font-family="Prompt, sans-serif" font-size="13" fill="#e0f2fe">{act}:</text>')
        svg_parts.append(f'    <text x="260" y="{y}" font-family="Prompt, sans-serif" font-size="13" font-weight="bold" fill="{color}">{icon}</text>')
        y += 26

    svg_parts.append('  </g>')
    svg_parts.append('</svg>')
    return "\n".join(svg_parts)


def generate_thaivedic_svg(chart: dict[str, Any], title: str | None = None, lang: str = "th") -> str:
    """Generate SVG string for Thai Suriyayart & Vedic Nakshatra chart."""
    title = _resolve_svg_title("thaivedic", title, lang)
    lagna = chart.get("thai_lagna", "เมษ")
    kala = chart.get("kalakini_planet", "อาทิตย์")
    sri = chart.get("sri_planet", "จันทร์")
    nak = chart.get("vedic_nakshatra", {})

    svg_parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 450" width="100%" height="100%">',
        '  <rect width="600" height="450" rx="16" fill="#1c1603" stroke="#eab308" stroke-width="2"/>',
        f'  <text x="300" y="40" font-family="Prompt, sans-serif" font-size="20" font-weight="bold" fill="#facc15" text-anchor="middle">🐘 {title}</text>',
        f'  <text x="300" y="70" font-family="Prompt, sans-serif" font-size="13" fill="#fef08a" text-anchor="middle">ลัคนาสุริยยาตร์: {lagna} | ศรี: {sri} | กาลกิณี: {kala}</text>',
        '  <g transform="translate(40, 100)">',
        '    <rect x="0" y="0" width="520" height="120" rx="10" fill="#2e2405" stroke="#ca8a04" stroke-width="1.5"/>',
        '    <text x="20" y="35" font-family="Prompt, sans-serif" font-size="14" font-weight="bold" fill="#fef08a">นักษัตร 27 ดารา (Vedic Nakshatra):</text>',
        f'    <text x="20" y="70" font-family="Prompt, sans-serif" font-size="15" fill="#ffffff">นักษัตรที่ {nak.get("number","")} : {nak.get("name","")} (Pada {nak.get("pada","")})</text>',
        f'    <text x="20" y="100" font-family="Prompt, sans-serif" font-size="13" fill="#fde047">วิมโชตตรีทศา: {chart.get("vimshottari_dasha","")}</text>',
        '  </g>',
        '  <g transform="translate(40, 240)">',
        '    <rect x="0" y="0" width="520" height="180" rx="10" fill="#241c03" stroke="#a16207" stroke-width="1.5"/>',
        '    <text x="20" y="35" font-family="Prompt, sans-serif" font-size="14" font-weight="bold" fill="#fef08a">มหาทักษา 8 เทวดาเสวยอายุ:</text>'
    ]

    thaksa = chart.get("maha_thaksa", {})
    y = 70
    for planet, desc in list(thaksa.items())[:4]:
        svg_parts.append(f'    <text x="20" y="{y}" font-family="Prompt, sans-serif" font-size="13" fill="#fef9c3">{planet}: {desc}</text>')
        y += 26

    svg_parts.append('  </g>')
    svg_parts.append('</svg>')
    return "\n".join(svg_parts)


def generate_western_svg(chart: dict[str, Any], title: str | None = None, lang: str = "th") -> str:
    """Generate SVG string for Western Tropical & Uranian TNP chart."""
    title = _resolve_svg_title("western", title, lang)
    planets = chart.get("planets_tropical", {})
    tnps = chart.get("uranian_tnps", {})
    mid = chart.get("uranian_midpoint_formula", {})

    svg_parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 450" width="100%" height="100%">',
        '  <rect width="600" height="450" rx="16" fill="#0b0a1d" stroke="#6366f1" stroke-width="2"/>',
        f'  <text x="300" y="40" font-family="Prompt, sans-serif" font-size="20" font-weight="bold" fill="#818cf8" text-anchor="middle">🌌 {title}</text>',
        f'  <text x="300" y="70" font-family="Prompt, sans-serif" font-size="13" fill="#c7d2fe" text-anchor="middle">จุดอิทธิพลสะท้อนศูนย์ลิขิต: {mid.get("formula","")} ➔ {mid.get("zodiac_position","")}</text>',
        '  <g transform="translate(40, 100)">',
        '    <rect x="0" y="0" width="250" height="310" rx="10" fill="#141332" stroke="#4f46e5" stroke-width="1.5"/>',
        '    <text x="15" y="30" font-family="Prompt, sans-serif" font-size="13" font-weight="bold" fill="#a5b4fc">Tropical Planets:</text>'
    ]

    y = 60
    for p, pos in list(planets.items())[:8]:
        svg_parts.append(f'    <text x="15" y="{y}" font-family="Prompt, sans-serif" font-size="12" fill="#e0e7ff">{p}: {pos}</text>')
        y += 30

    svg_parts.append('  </g>')
    svg_parts.append('  <g transform="translate(310, 100)">')
    svg_parts.append('    <rect x="0" y="0" width="250" height="310" rx="10" fill="#141332" stroke="#4f46e5" stroke-width="1.5"/>')
    svg_parts.append('    <text x="15" y="30" font-family="Prompt, sans-serif" font-size="13" font-weight="bold" fill="#a5b4fc">8 Uranian TNPs:</text>')

    y = 60
    for tnp, deg in list(tnps.items())[:8]:
        svg_parts.append(f'    <text x="15" y="{y}" font-family="Prompt, sans-serif" font-size="12" fill="#e0e7ff">{tnp}: {deg:.1f}°</text>')
        y += 30

    svg_parts.append('  </g>')
    svg_parts.append('</svg>')
    return "\n".join(svg_parts)


def generate_numerology_svg(chart: dict[str, Any], title: str | None = None, lang: str = "th") -> str:
    """Generate SVG string for Satta-Lek 7-Base Numerology chart."""
    title = _resolve_svg_title("numerology", title, lang)
    score = chart.get("chaldean_score", {})
    satta = chart.get("satta_lek", {})
    matrix = satta.get("matrix_7_base", [])

    svg_parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 530" width="100%" height="100%">',
        '  <defs>',
        '    <linearGradient id="bgNum" x1="0%" y1="0%" x2="100%" y2="100%">',
        '      <stop offset="0%" stop-color="#021f1d" />',
        '      <stop offset="100%" stop-color="#0a141a" />',
        '    </linearGradient>',
        '    <linearGradient id="headerGrad" x1="0%" y1="0%" x2="100%" y2="0%">',
        '      <stop offset="0%" stop-color="#14b8a6" />',
        '      <stop offset="100%" stop-color="#38bdf8" />',
        '    </linearGradient>',
        '  </defs>',
        '  <rect width="760" height="530" rx="16" fill="url(#bgNum)" stroke="#0d9488" stroke-width="2"/>',
        f'  <text x="380" y="38" font-family="Prompt, sans-serif" font-size="20" font-weight="bold" fill="#2dd4bf" text-anchor="middle">🔢 {title}</text>',
        f'  <rect x="50" y="55" width="660" height="36" rx="8" fill="rgba(13, 148, 136, 0.2)" stroke="#14b8a6" stroke-width="1"/>',
        f'  <text x="380" y="78" font-family="Prompt, sans-serif" font-size="13" font-weight="500" fill="#99f6e4" text-anchor="middle">Chaldean Score ({score.get("input_text","")}): รวม {score.get("total_score","")} ➔ รากเลข {score.get("reduced_root_digit","")} [{score.get("digit_meaning","")}]</text>',
        '  <g transform="translate(100, 105)">'
    ]

    # Row labels on the left
    row_labels = [
        ("ฐาน ๑ (วัน)", 55),
        ("ฐาน ๒ (เดือน)", 135),
        ("ฐาน ๓ (ปี)", 215),
        ("ฐาน ๔ (กำลังดาว)", 295)
    ]
    for label, y in row_labels:
        svg_parts.append(f'    <text x="-15" y="{y}" font-family="Prompt, sans-serif" font-size="12" font-weight="600" fill="#64748b" text-anchor="end">{label}</text>')

    col_w = 88
    for idx, m in enumerate(matrix[:7]):
        x = idx * col_w
        svg_parts.append(f'    <rect x="{x}" y="0" width="80" height="340" rx="8" fill="#0f2d2a" stroke="#0d9488" stroke-width="1.5"/>')
        # House Name Header
        svg_parts.append(f'    <rect x="{x}" y="0" width="80" height="32" rx="8" fill="rgba(20, 184, 166, 0.3)"/>')
        svg_parts.append(f'    <text x="{x+40}" y="21" font-family="Prompt, sans-serif" font-size="13" font-weight="bold" fill="#2dd4bf" text-anchor="middle">{m.get("house_name","")}</text>')
        svg_parts.append(f'    <line x1="{x+4}" y1="32" x2="{x+76}" y2="32" stroke="#134e4a"/>')
        # Row 1 (Day)
        svg_parts.append(f'    <text x="{x+40}" y="65" font-family="Outfit, sans-serif" font-size="24" font-weight="bold" fill="#f8fafc" text-anchor="middle">{m.get("row1_day","")}</text>')
        svg_parts.append(f'    <line x1="{x+8}" y1="88" x2="{x+72}" y2="88" stroke="#134e4a" stroke-dasharray="3,3"/>')
        # Row 2 (Month)
        svg_parts.append(f'    <text x="{x+40}" y="145" font-family="Outfit, sans-serif" font-size="24" font-weight="bold" fill="#f8fafc" text-anchor="middle">{m.get("row2_month","")}</text>')
        svg_parts.append(f'    <line x1="{x+8}" y1="168" x2="{x+72}" y2="168" stroke="#134e4a" stroke-dasharray="3,3"/>')
        # Row 3 (Year)
        svg_parts.append(f'    <text x="{x+40}" y="225" font-family="Outfit, sans-serif" font-size="24" font-weight="bold" fill="#f8fafc" text-anchor="middle">{m.get("row3_year","")}</text>')
        svg_parts.append(f'    <line x1="{x+4}" y1="248" x2="{x+76}" y2="248" stroke="#0d9488" stroke-width="1.5"/>')
        # Row 4 (Planetary Power Sum)
        p_name = m.get("power_name", "")
        short_p = p_name.split("(")[0].strip() if "(" in p_name else p_name
        svg_parts.append(f'    <rect x="{x+4}" y="254" width="72" height="78" rx="6" fill="rgba(251, 191, 36, 0.12)" stroke="#d97706" stroke-width="1"/>')
        svg_parts.append(f'    <text x="{x+40}" y="288" font-family="Outfit, sans-serif" font-size="26" font-weight="bold" fill="#fbbf24" text-anchor="middle">{m.get("row4_sum","")}</text>')
        svg_parts.append(f'    <text x="{x+40}" y="318" font-family="Prompt, sans-serif" font-size="10" font-weight="500" fill="#fde68a" text-anchor="middle">{short_p[:8]}</text>')

    # Footer note inside SVG
    svg_parts.append('  </g>')
    svg_parts.append('  <text x="380" y="495" font-family="Prompt, sans-serif" font-size="11" fill="#64748b" text-anchor="middle">สัตตเลข 7 ฐาน (ภพ ๗ เรือน) + ถอดรหัสอักษรเลขศาสตร์ Chaldean โบราณ</text>')
    svg_parts.append('</svg>')
    return "\n".join(svg_parts)


def generate_tai_yi_svg(chart: dict[str, Any], title: str | None = None, lang: str = "th") -> str:
    """Generate SVG chart for Tai Yi Shen Shu (太乙神數)."""
    title = _resolve_svg_title("taiyi", title, lang)
    """Generate SVG chart for Tai Yi Shen Shu (太乙神數)."""
    acc_years = chart.get("accumulated_years", 0)
    star_palace = chart.get("star_palace", 0)
    strategic = chart.get("strategic_assessment", "吉")
    tai_yi_num = chart.get("tai_yi_number", 0)
    earth_plate = chart.get("earth_plate", [1, 2, 3, 4, 5, 6, 7, 8, 9])
    heaven_plate = chart.get("heaven_plate", [2, 3, 4, 5, 6, 7, 8, 9, 1])

    path_names = [
        "子 (1)", "丑 (2)", "艮 (3)", "寅 (4)",
        "卯 (5)", "辰 (6)", "巽 (7)", "巳 (8)",
        "午 (9)", "未 (10)", "坤 (11)", "申 (12)",
        "酉 (13)", "戌 (14)", "乾 (15)", "亥 (16)"
    ]

    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" width="100%" height="100%">',
        '  <defs>',
        '    <linearGradient id="bgTaiYi" x1="0%" y1="0%" x2="100%" y2="100%">',
        '      <stop offset="0%" stop-color="#0a0f1d"/>',
        '      <stop offset="100%" stop-color="#1e1b4b"/>',
        '    </linearGradient>',
        '    <filter id="glowGoldTY" x="-20%" y="-20%" width="140%" height="140%">',
        '      <feGaussianBlur stdDeviation="4" result="blur"/>',
        '      <feComposite in="SourceGraphic" in2="blur" operator="over"/>',
        '    </filter>',
        '  </defs>',
        '  <rect width="800" height="600" rx="16" fill="url(#bgTaiYi)" stroke="#6366f1" stroke-width="2"/>',
        f'  <text x="400" y="42" font-family="Prompt, sans-serif" font-size="20" font-weight="bold" fill="#fbbf24" text-anchor="middle" filter="url(#glowGoldTY)">📜 {title}</text>',
        f'  <text x="400" y="70" font-family="Prompt, sans-serif" font-size="13" fill="#cbd5e1" text-anchor="middle">太乙積年: {acc_years} ปี | 太乙數: {tai_yi_num} | ยุทธศาสตร์รวม: {strategic}</text>',
        '  <g transform="translate(60, 95)">',
        '    <rect x="0" y="0" width="320" height="340" rx="12" fill="#111827" stroke="#4338ca" stroke-width="1.5"/>',
        '    <text x="160" y="28" font-family="Prompt, sans-serif" font-size="14" font-weight="bold" fill="#a5b4fc" text-anchor="middle">🌌 ผังดาว 16 ทิศ (16-Path Star Palaces)</text>',
    ]

    for idx, p_name in enumerate(path_names):
        r = idx // 4
        c = idx % 4
        x = 18 + c * 72
        y = 45 + r * 68
        is_active = (idx == (star_palace % 16))
        stroke_color = "#fbbf24" if is_active else "#374151"
        fill_color = "rgba(251, 191, 36, 0.2)" if is_active else "rgba(30, 41, 59, 0.6)"
        text_color = "#fbbf24" if is_active else "#94a3b8"
        svg.append(f'    <rect x="{x}" y="{y}" width="68" height="62" rx="8" fill="{fill_color}" stroke="{stroke_color}" stroke-width="{"2" if is_active else "1"}"/>')
        svg.append(f'    <text x="{x+34}" y="{y+26}" font-family="sans-serif" font-size="13" font-weight="bold" fill="{text_color}" text-anchor="middle">{p_name}</text>')
        if is_active:
            svg.append(f'    <text x="{x+34}" y="{y+48}" font-family="Prompt, sans-serif" font-size="11" font-weight="bold" fill="#f59e0b" text-anchor="middle">★ 太乙星</text>')

    svg.append('  </g>')

    svg.extend([
        '  <g transform="translate(420, 95)">',
        '    <rect x="0" y="0" width="320" height="340" rx="12" fill="#111827" stroke="#059669" stroke-width="1.5"/>',
        '    <text x="160" y="28" font-family="Prompt, sans-serif" font-size="14" font-weight="bold" fill="#6ee7b7" text-anchor="middle">☯ 天地二盤 (Heaven &amp; Earth 9-Palace Matrix)</text>',
    ])

    nine_palace_labels = ["四巽", "九離", "二坤", "三震", "五中", "七兌", "八艮", "一坎", "六乾"]
    for idx in range(9):
        r = idx // 3
        c = idx % 3
        x = 22 + c * 92
        y = 48 + r * 90
        ep_val = earth_plate[idx] if idx < len(earth_plate) else idx + 1
        hp_val = heaven_plate[idx] if idx < len(heaven_plate) else idx + 1
        palace_name = nine_palace_labels[idx]
        svg.append(f'    <rect x="{x}" y="{y}" width="86" height="82" rx="8" fill="rgba(15, 23, 42, 0.8)" stroke="#1e293b" stroke-width="1"/>')
        svg.append(f'    <text x="{x+43}" y="{y+20}" font-family="sans-serif" font-size="12" font-weight="bold" fill="#64748b" text-anchor="middle">{palace_name}</text>')
        svg.append(f'    <text x="{x+25}" y="{y+52}" font-family="sans-serif" font-size="18" font-weight="bold" fill="#38bdf8" text-anchor="middle">天{hp_val}</text>')
        svg.append(f'    <text x="{x+62}" y="{y+52}" font-family="sans-serif" font-size="18" font-weight="bold" fill="#10b981" text-anchor="middle">地{ep_val}</text>')

    svg.append('  </g>')

    svg.extend([
        '  <g transform="translate(60, 455)">',
        '    <rect x="0" y="0" width="680" height="95" rx="10" fill="rgba(30, 27, 75, 0.6)" stroke="#4f46e5" stroke-width="1"/>',
        f'    <text x="24" y="32" font-family="Prompt, sans-serif" font-size="15" font-weight="bold" fill="#fbbf24">🎯 การประเมินยุทธศาสตร์太乙神數: {strategic} (ทิศมงคล/ดวงดาวจร ณ วัง {path_names[star_palace % 16]})</text>',
        '    <text x="24" y="60" font-family="Prompt, sans-serif" font-size="12" fill="#94a3b8">อ้างอิง: คัมภีร์ไท่อี่จินจิ้งซื่อจิง (太乙金鏡式經) — วิเคราะห์การเคลื่อนพล การบริหารความเสี่ยง และทิศทางกลยุทธ์แห่งกาลเวลา</text>',
        '  </g>',
        '</svg>'
    ])
    return "\n".join(svg)


def generate_liu_yao_svg(chart: dict[str, Any], title: str | None = None, lang: str = "th") -> str:
    """Generate SVG chart for Liu Yao Divination (六爻預測)."""
    title = _resolve_svg_title("liuyao", title, lang)
    p_name = chart.get("primary_hexagram_name", "乾為天")
    t_name = chart.get("target_hexagram_name", chart.get("transformed_hexagram_name", "同人"))
    palace = chart.get("palace_element", "金 (Metal)")
    day_stem = chart.get("day_stem", "甲")
    lines = chart.get("lines", [])

    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" width="100%" height="100%">',
        '  <defs>',
        '    <linearGradient id="bgLiuYao" x1="0%" y1="0%" x2="100%" y2="100%">',
        '      <stop offset="0%" stop-color="#0f172a"/>',
        '      <stop offset="100%" stop-color="#311042"/>',
        '    </linearGradient>',
        '    <filter id="glowPurpleLY" x="-20%" y="-20%" width="140%" height="140%">',
        '      <feGaussianBlur stdDeviation="4" result="blur"/>',
        '      <feComposite in="SourceGraphic" in2="blur" operator="over"/>',
        '    </filter>',
        '  </defs>',
        '  <rect width="800" height="600" rx="16" fill="url(#bgLiuYao)" stroke="#c084fc" stroke-width="2"/>',
        f'  <text x="400" y="42" font-family="Prompt, sans-serif" font-size="20" font-weight="bold" fill="#fbbf24" text-anchor="middle" filter="url(#glowPurpleLY)">🔮 {title}</text>',
        f'  <text x="400" y="70" font-family="Prompt, sans-serif" font-size="13" fill="#cbd5e1" text-anchor="middle">本卦: {p_name} ➔ 變卦: {t_name} | 宮位: {palace} | 日干: {day_stem}</text>',
        '  <g transform="translate(60, 95)">',
        '    <rect x="0" y="0" width="680" height="360" rx="12" fill="#111827" stroke="#7e22ce" stroke-width="1.5"/>',
        '    <text x="340" y="30" font-family="Prompt, sans-serif" font-size="14" font-weight="bold" fill="#e9d5ff" text-anchor="middle">六爻納甲盤 (Six Lines Na Jia &amp; Six Celestial Spirits)</text>',
        '    <text x="60" y="60" font-family="Prompt, sans-serif" font-size="12" font-weight="bold" fill="#94a3b8">神煞 (Spirits)</text>',
        '    <text x="170" y="60" font-family="Prompt, sans-serif" font-size="12" font-weight="bold" fill="#94a3b8">六親 (Relatives)</text>',
        '    <text x="280" y="60" font-family="Prompt, sans-serif" font-size="12" font-weight="bold" fill="#94a3b8">納甲地支 (Branch)</text>',
        '    <text x="440" y="60" font-family="Prompt, sans-serif" font-size="12" font-weight="bold" fill="#94a3b8">本卦爻象 (Line)</text>',
        '    <text x="600" y="60" font-family="Prompt, sans-serif" font-size="12" font-weight="bold" fill="#94a3b8">動變 (Moving)</text>',
        '    <line x1="20" y1="70" x2="660" y2="70" stroke="#374151" stroke-width="1"/>',
    ]

    default_relatives = ["父母", "兄弟", "子孫", "妻財", "官鬼", "父母"]
    default_branches = ["子水", "寅木", "辰土", "午火", "申金", "戌土"]
    default_spirits = ["青龍", "朱雀", "勾陳", "螣蛇", "白虎", "玄武"]

    for i in range(6):
        line_idx = 5 - i # Line 6 down to Line 1
        y = 95 + i * 44
        line_data = lines[line_idx] if line_idx < len(lines) else {}
        is_yang = bool(line_data.get("is_yang", (line_idx % 2 == 0)))
        is_moving = bool(line_data.get("is_moving", (line_idx == 2)))
        rel = line_data.get("relative", default_relatives[line_idx])
        branch = line_data.get("branch", default_branches[line_idx])
        spirit = line_data.get("spirit", default_spirits[line_idx])

        # Spirit badge
        svg.append(f'    <text x="60" y="{y+16}" font-family="sans-serif" font-size="13" font-weight="bold" fill="#38bdf8">{spirit}</text>')
        # Relative
        svg.append(f'    <text x="170" y="{y+16}" font-family="sans-serif" font-size="14" font-weight="bold" fill="#fbbf24">{rel}</text>')
        # Branch
        svg.append(f'    <text x="280" y="{y+16}" font-family="sans-serif" font-size="14" font-weight="bold" fill="#4ade80">{branch}</text>')

        # Hexagram Line
        line_color = "#ef4444" if is_moving else "#e2e8f0"
        if is_yang:
            # Solid line
            svg.append(f'    <rect x="390" y="{y+6}" width="150" height="12" rx="4" fill="{line_color}"/>')
        else:
            # Broken line
            svg.append(f'    <rect x="390" y="{y+6}" width="68" height="12" rx="4" fill="{line_color}"/>')
            svg.append(f'    <rect x="472" y="{y+6}" width="68" height="12" rx="4" fill="{line_color}"/>')

        # Moving line indicator
        if is_moving:
            svg.append(f'    <text x="600" y="{y+16}" font-family="Prompt, sans-serif" font-size="13" font-weight="bold" fill="#ef4444">● 動 (Moving)</text>')
        else:
            svg.append(f'    <text x="600" y="{y+16}" font-family="Prompt, sans-serif" font-size="13" fill="#64748b">靜 (Static)</text>')

    svg.append('  </g>')
    svg.extend([
        '  <g transform="translate(60, 475)">',
        '    <rect x="0" y="0" width="680" height="75" rx="10" fill="rgba(88, 28, 135, 0.4)" stroke="#9333ea" stroke-width="1"/>',
        f'    <text x="24" y="30" font-family="Prompt, sans-serif" font-size="14" font-weight="bold" fill="#fbbf24">📖 บทวิเคราะห์六爻: 本卦 {p_name} ➔ 變卦 {t_name} (世應相生/剋)</text>',
        '    <text x="24" y="54" font-family="Prompt, sans-serif" font-size="12" fill="#94a3b8">อ้างอิง: คัมภีร์ปู้ซื่อเจิ้งจง (卜筮正宗) &amp; เจิงซานปู้เต้า (增刪卜易) — วิเคราะห์ความสัมพันธ์ 6 ญาติและเทพดารา</text>',
        '  </g>',
        '</svg>'
    ])
    return "\n".join(svg)


def generate_meihua_svg(chart: dict[str, Any], title: str | None = None, lang: str = "th") -> str:
    """Generate SVG chart for Mei Hua Yi Shu (梅花易數)."""
    title = _resolve_svg_title("meihua", title, lang)
    p_name = chart.get("primary_hexagram", "乾為天")
    m_name = chart.get("mutual_hexagram", "乾為天")
    t_name = chart.get("transformed_hexagram", "天風姤")
    moving_yao = chart.get("moving_yao", 1)
    body_trigram = chart.get("body_trigram", "乾 (金)")
    use_trigram = chart.get("use_trigram", "巽 (木)")
    interaction = chart.get("interaction", "體克用 (Body controls Use - 吉)")

    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" width="100%" height="100%">',
        '  <defs>',
        '    <linearGradient id="bgMeiHua" x1="0%" y1="0%" x2="100%" y2="100%">',
        '      <stop offset="0%" stop-color="#140f1a"/>',
        '      <stop offset="100%" stop-color="#4a044e"/>',
        '    </linearGradient>',
        '    <filter id="glowPinkMH" x="-20%" y="-20%" width="140%" height="140%">',
        '      <feGaussianBlur stdDeviation="4" result="blur"/>',
        '      <feComposite in="SourceGraphic" in2="blur" operator="over"/>',
        '    </filter>',
        '  </defs>',
        '  <rect width="800" height="600" rx="16" fill="url(#bgMeiHua)" stroke="#f472b6" stroke-width="2"/>',
        f'  <text x="400" y="42" font-family="Prompt, sans-serif" font-size="20" font-weight="bold" fill="#fbbf24" text-anchor="middle" filter="url(#glowPinkMH)">🌸 {title}</text>',
        f'  <text x="400" y="70" font-family="Prompt, sans-serif" font-size="13" fill="#cbd5e1" text-anchor="middle">體卦: {body_trigram} | 用卦: {use_trigram} | 動爻: 第 {moving_yao} 爻 | ปฏิสัมพันธ์: {interaction}</text>',
        '  <g transform="translate(60, 95)">',
    ]

    # 3 Cards: 本卦 (Primary) ➔ 互卦 (Mutual) ➔ 變卦 (Resulting)
    cards = [
        ("本卦 (Primary)", p_name, "เริ่มต้น / สภาพปัจจุบัน", "#ec4899", 0),
        ("互卦 (Mutual)", m_name, "กระบวนการ / ปัจจัยแฝง", "#a855f7", 240),
        ("變卦 (Resulting)", t_name, "ผลลัพธ์ / บทสรุป", "#38bdf8", 480),
    ]

    for label, h_name, desc, color, x in cards:
        svg.append(f'    <rect x="{x}" y="0" width="200" height="340" rx="12" fill="#18181b" stroke="{color}" stroke-width="1.5"/>')
        svg.append(f'    <rect x="{x}" y="0" width="200" height="38" rx="12" fill="{color}" fill-opacity="0.2"/>')
        svg.append(f'    <text x="{x+100}" y="25" font-family="Prompt, sans-serif" font-size="14" font-weight="bold" fill="{color}" text-anchor="middle">{label}</text>')
        svg.append(f'    <text x="{x+100}" y="70" font-family="sans-serif" font-size="22" font-weight="bold" fill="#f8fafc" text-anchor="middle">{h_name}</text>')
        svg.append(f'    <text x="{x+100}" y="95" font-family="Prompt, sans-serif" font-size="11" fill="#94a3b8" text-anchor="middle">{desc}</text>')
        svg.append(f'    <line x1="{x+15}" y1="110" x2="{x+185}" y2="110" stroke="#3f3f46" stroke-width="1"/>')
        # Hexagram Lines graphic
        for l_idx in range(6):
            ly = 135 + l_idx * 30
            svg.append(f'    <rect x="{x+40}" y="{ly}" width="120" height="10" rx="4" fill="{color}"/>')

    svg.append('  </g>')
    svg.extend([
        '  <g transform="translate(60, 455)">',
        '    <rect x="0" y="0" width="680" height="95" rx="10" fill="rgba(74, 4, 78, 0.4)" stroke="#d946ef" stroke-width="1"/>',
        f'    <text x="24" y="32" font-family="Prompt, sans-serif" font-size="15" font-weight="bold" fill="#fbbf24">🌺 บททำนาย梅花易數: {interaction}</text>',
        '    <text x="24" y="60" font-family="Prompt, sans-serif" font-size="12" fill="#94a3b8">อ้างอิง: คัมภีร์เหมยฮวาอี้ซู่ (梅花易數 - 邵康節) — ศาสตร์ทำนายตามเวลา กาลโยค และการปฏิสัมพันธ์ของธาตุ体用</text>',
        '  </g>',
        '</svg>'
    ])
    return "\n".join(svg)


def generate_sanhe_svg(chart: dict[str, Any], title: str | None = None, lang: str = "th") -> str:
    """Generate SVG chart for San He Feng Shui (三合風水)."""
    title = _resolve_svg_title("sanhe", title, lang)
    sitting = chart.get("sitting_mountain", "壬")
    facing = chart.get("facing_mountain", "丙")
    water_exit = chart.get("water_exit", "辰")
    formation = chart.get("formation", "申子辰 水局 (Water Formation)")
    stage = chart.get("water_method_stage", "長生 (Chang Sheng - Auspicious)")

    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" width="100%" height="100%">',
        '  <defs>',
        '    <linearGradient id="bgSanHe" x1="0%" y1="0%" x2="100%" y2="100%">',
        '      <stop offset="0%" stop-color="#022c22"/>',
        '      <stop offset="100%" stop-color="#064e3b"/>',
        '    </linearGradient>',
        '    <filter id="glowGreenSH" x="-20%" y="-20%" width="140%" height="140%">',
        '      <feGaussianBlur stdDeviation="4" result="blur"/>',
        '      <feComposite in="SourceGraphic" in2="blur" operator="over"/>',
        '    </filter>',
        '  </defs>',
        '  <rect width="800" height="600" rx="16" fill="url(#bgSanHe)" stroke="#10b981" stroke-width="2"/>',
        f'  <text x="400" y="42" font-family="Prompt, sans-serif" font-size="20" font-weight="bold" fill="#fbbf24" text-anchor="middle" filter="url(#glowGreenSH)">🧭 {title}</text>',
        f'  <text x="400" y="70" font-family="Prompt, sans-serif" font-size="13" fill="#cbd5e1" text-anchor="middle">坐山: {sitting} | 向山: {facing} | 水口: {water_exit} | สามสมพงศ์: {formation}</text>',
        '  <g transform="translate(60, 95)">',
        '    <rect x="0" y="0" width="320" height="340" rx="12" fill="#064e3b" stroke="#047857" stroke-width="1.5"/>',
        '    <text x="160" y="28" font-family="Prompt, sans-serif" font-size="14" font-weight="bold" fill="#6ee7b7" text-anchor="middle">二十四山羅盤 (24 Mountains Compass)</text>',
        '    <circle cx="160" cy="180" r="110" fill="none" stroke="#10b981" stroke-width="2"/>',
        '    <circle cx="160" cy="180" r="70" fill="#022c22" stroke="#34d399" stroke-width="1.5"/>',
        '    <circle cx="160" cy="180" r="30" fill="#064e3b" stroke="#fbbf24" stroke-width="2"/>',
        f'    <text x="160" y="186" font-family="sans-serif" font-size="15" font-weight="bold" fill="#fbbf24" text-anchor="middle">坐{sitting}</text>',
        '  </g>',
        '  <g transform="translate(420, 95)">',
        '    <rect x="0" y="0" width="320" height="340" rx="12" fill="#064e3b" stroke="#047857" stroke-width="1.5"/>',
        '    <text x="160" y="28" font-family="Prompt, sans-serif" font-size="14" font-weight="bold" fill="#6ee7b7" text-anchor="middle">十二長生水法 (12 Water Stages)</text>',
    ]

    stages_12 = [
        ("長生", "กำเนิด/เจริญ", True), ("沐浴", "ชำระล้าง/รั่วไหล", False),
        ("冠帶", "สวมหมวก/เกียรติ", False), ("臨官", "ขุนนาง/มั่นคง", True),
        ("帝旺", "รุ่งเรืองสูงสุด", True), ("衰", "เริ่มถดถอย", False),
        ("病", "เจ็บป่วย/ติดขัด", False), ("死", "สิ้นสุด/หยุดนิ่ง", False),
        ("墓", "คลังสมบัติ/กักเก็บ", True), ("絕", "ขาดตอน/แปรผัน", False),
        ("胎", "ก่อกำเนิดใหม่", False), ("養", "ฟูมฟัก/พัฒนา", False)
    ]

    for idx, (st_name, st_desc, is_auspicious) in enumerate(stages_12):
        r = idx // 2
        c = idx % 2
        x = 18 + c * 144
        y = 48 + r * 46
        st_color = "#34d399" if is_auspicious else "#94a3b8"
        svg.append(f'    <rect x="{x}" y="{y}" width="136" height="40" rx="6" fill="rgba(2, 44, 34, 0.7)" stroke="{st_color}" stroke-width="1"/>')
        svg.append(f'    <text x="{x+10}" y="{y+25}" font-family="sans-serif" font-size="14" font-weight="bold" fill="{st_color}">{st_name}</text>')
        svg.append(f'    <text x="{x+50}" y="{y+25}" font-family="Prompt, sans-serif" font-size="10" fill="#cbd5e1">{st_desc}</text>')

    svg.append('  </g>')
    svg.extend([
        '  <g transform="translate(60, 455)">',
        '    <rect x="0" y="0" width="680" height="95" rx="10" fill="rgba(6, 78, 59, 0.6)" stroke="#059669" stroke-width="1"/>',
        f'    <text x="24" y="32" font-family="Prompt, sans-serif" font-size="15" font-weight="bold" fill="#fbbf24">🌊 ขั้นตอนทางน้ำ: {stage} | {formation}</text>',
        '    <text x="24" y="60" font-family="Prompt, sans-serif" font-size="12" fill="#94a3b8">อ้างอิง: คัมภีร์ตี๋หลี่อู่เจว๋ (地理五訣) — หลักวิชาฮวงจุ้ยสามประสาน (ซำฮะ) คำนวณมังกร เขา ทิศทาง และกระแสน้ำ 12 วงจร</text>',
        '  </g>',
        '</svg>'
    ])
    return "\n".join(svg)


def generate_qizheng_svg(chart: dict[str, Any], title: str | None = None, lang: str = "th") -> str:
    """Generate SVG chart for Qi Zheng Si Yu (七政四餘)."""
    title = _resolve_svg_title("qizheng", title, lang)
    dt_str = chart.get("datetime", "2026-08-16 12:00:00")
    planets = chart.get("planets", {})
    shadow_stars = chart.get("shadow_stars", {})

    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" width="100%" height="100%">',
        '  <defs>',
        '    <linearGradient id="bgQiZheng" x1="0%" y1="0%" x2="100%" y2="100%">',
        '      <stop offset="0%" stop-color="#090d16"/>',
        '      <stop offset="100%" stop-color="#1e1b4b"/>',
        '    </linearGradient>',
        '    <filter id="glowBlueQZ" x="-20%" y="-20%" width="140%" height="140%">',
        '      <feGaussianBlur stdDeviation="4" result="blur"/>',
        '      <feComposite in="SourceGraphic" in2="blur" operator="over"/>',
        '    </filter>',
        '  </defs>',
        '  <rect width="800" height="600" rx="16" fill="url(#bgQiZheng)" stroke="#38bdf8" stroke-width="2"/>',
        f'  <text x="400" y="42" font-family="Prompt, sans-serif" font-size="20" font-weight="bold" fill="#fbbf24" text-anchor="middle" filter="url(#glowBlueQZ)">🌌 {title}</text>',
        f'  <text x="400" y="70" font-family="Prompt, sans-serif" font-size="13" fill="#cbd5e1" text-anchor="middle">วันเวลาคำนวณ: {dt_str} | 七政 (7 Governors) + 四餘 (4 Extra Shadows)</text>',
        '  <g transform="translate(60, 95)">',
        '    <rect x="0" y="0" width="320" height="340" rx="12" fill="#0f172a" stroke="#0284c7" stroke-width="1.5"/>',
        '    <text x="160" y="28" font-family="Prompt, sans-serif" font-size="14" font-weight="bold" fill="#7dd3fc" text-anchor="middle">二十八宿天球盤 (28 Lunar Mansions)</text>',
        '    <circle cx="160" cy="180" r="115" fill="none" stroke="#334155" stroke-width="2"/>',
        '    <circle cx="160" cy="180" r="85" fill="none" stroke="#0284c7" stroke-dasharray="4,4" stroke-width="1.5"/>',
        '    <circle cx="160" cy="180" r="45" fill="#1e293b" stroke="#38bdf8" stroke-width="2"/>',
        '    <text x="160" y="186" font-family="sans-serif" font-size="18" font-weight="bold" fill="#fbbf24" text-anchor="middle">七政</text>',
        '  </g>',
        '  <g transform="translate(420, 95)">',
        '    <rect x="0" y="0" width="320" height="340" rx="12" fill="#0f172a" stroke="#0284c7" stroke-width="1.5"/>',
        '    <text x="160" y="28" font-family="Prompt, sans-serif" font-size="14" font-weight="bold" fill="#7dd3fc" text-anchor="middle">ดวงดาว 7 นพเคราะห์ &amp; 4 เงามืด</text>',
    ]

    p_list = list(planets.items()) + list(shadow_stars.items())
    for idx, (p_name, deg) in enumerate(p_list[:8]):
        y = 50 + idx * 34
        deg_val = deg if isinstance(deg, (int, float)) else 0.0
        svg.append(f'    <rect x="18" y="{y}" width="284" height="28" rx="6" fill="rgba(30, 41, 59, 0.6)" stroke="#334155" stroke-width="1"/>')
        svg.append(f'    <text x="30" y="{y+19}" font-family="sans-serif" font-size="13" font-weight="bold" fill="#38bdf8">{p_name}</text>')
        svg.append(f'    <text x="280" y="{y+19}" font-family="sans-serif" font-size="13" font-weight="bold" fill="#f8fafc" text-anchor="end">{deg_val:.2f}°</text>')

    svg.append('  </g>')
    svg.extend([
        '  <g transform="translate(60, 455)">',
        '    <rect x="0" y="0" width="680" height="95" rx="10" fill="rgba(15, 23, 42, 0.7)" stroke="#0369a1" stroke-width="1"/>',
        '    <text x="24" y="32" font-family="Prompt, sans-serif" font-size="15" font-weight="bold" fill="#fbbf24">🔭 โหราศาสตร์ดาราศาสตร์จีนโบราณ 七政四餘 (Guo Lao Xing Zong)</text>',
        '    <text x="24" y="60" font-family="Prompt, sans-serif" font-size="12" fill="#94a3b8">อ้างอิง: คัมภีร์กว๋อเหลาซิงจง (果老星宗) — บูรณาการ 28 นักษัตรจีนโบราณกับตำแหน่งดาวเคราะห์จริงตามจักรราศี</text>',
        '  </g>',
        '</svg>'
    ])
    return "\n".join(svg)


def generate_mianxiang_svg(chart: dict[str, Any], title: str | None = None, lang: str = "th") -> str:
    """Generate SVG chart for Mian Xiang (麻衣神相)."""
    title = _resolve_svg_title("mianxiang", title, lang)
    shape_desc = chart.get("face_shape", "Water (水形) - Round, soft, fleshy")
    palaces = chart.get("twelve_palaces", {})

    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" width="100%" height="100%">',
        '  <defs>',
        '    <linearGradient id="bgMianXiang" x1="0%" y1="0%" x2="100%" y2="100%">',
        '      <stop offset="0%" stop-color="#18181b"/>',
        '      <stop offset="100%" stop-color="#27272a"/>',
        '    </linearGradient>',
        '    <filter id="glowAmberMX" x="-20%" y="-20%" width="140%" height="140%">',
        '      <feGaussianBlur stdDeviation="4" result="blur"/>',
        '      <feComposite in="SourceGraphic" in2="blur" operator="over"/>',
        '    </filter>',
        '  </defs>',
        '  <rect width="800" height="600" rx="16" fill="url(#bgMianXiang)" stroke="#eab308" stroke-width="2"/>',
        f'  <text x="400" y="42" font-family="Prompt, sans-serif" font-size="20" font-weight="bold" fill="#fbbf24" text-anchor="middle" filter="url(#glowAmberMX)">👤 {title}</text>',
        f'  <text x="400" y="70" font-family="Prompt, sans-serif" font-size="13" fill="#cbd5e1" text-anchor="middle">โหงวเฮ้งเบญจธาตุ: {shape_desc}</text>',
        '  <g transform="translate(60, 95)">',
        '    <rect x="0" y="0" width="320" height="340" rx="12" fill="#18181b" stroke="#ca8a04" stroke-width="1.5"/>',
        '    <text x="160" y="28" font-family="Prompt, sans-serif" font-size="14" font-weight="bold" fill="#fde047" text-anchor="middle">百歲流年圖 (100 Age Positions Map)</text>',
        '    <!-- Face Outline Diagram -->',
        '    <ellipse cx="160" cy="185" rx="85" ry="115" fill="rgba(234, 179, 8, 0.08)" stroke="#eab308" stroke-width="2"/>',
        '    <line x1="85" y1="140" x2="235" y2="140" stroke="#71717a" stroke-dasharray="3,3"/>',
        '    <line x1="85" y1="220" x2="235" y2="220" stroke="#71717a" stroke-dasharray="3,3"/>',
        '    <text x="160" y="115" font-family="Prompt, sans-serif" font-size="11" fill="#facc15" text-anchor="middle">上庭 (วัยเยาว์ 15-30)</text>',
        '    <text x="160" y="180" font-family="Prompt, sans-serif" font-size="11" fill="#facc15" text-anchor="middle">中庭 (วัยกลาง 31-50)</text>',
        '    <text x="160" y="260" font-family="Prompt, sans-serif" font-size="11" fill="#facc15" text-anchor="middle">下庭 (วัยชรา 51-100)</text>',
        '  </g>',
        '  <g transform="translate(420, 95)">',
        '    <rect x="0" y="0" width="320" height="340" rx="12" fill="#18181b" stroke="#ca8a04" stroke-width="1.5"/>',
        '    <text x="160" y="28" font-family="Prompt, sans-serif" font-size="14" font-weight="bold" fill="#fde047" text-anchor="middle">面相十二宮 (12 Facial Palaces)</text>',
    ]

    palace_items = [
        ("命宮 (Life)", "หว่างคิ้ว / สติปัญญาและวาสนา"),
        ("財帛 (Wealth)", "จมูก / การเงินและโชคลาภ"),
        ("官祿 (Career)", "หน้าผาก / อำนาจและความสำเร็จ"),
        ("田宅 (Property)", "เปลือกตา / ทรัพย์สินและอสังหาฯ"),
        ("兄弟 (Siblings)", "คิ้ว / มิตรสหายและความสัมพันธ์"),
        ("男女 (Children)", "ใต้ตา / บุตรหลานและบริวาร")
    ]

    for idx, (p_name, p_desc) in enumerate(palace_items):
        y = 48 + idx * 46
        svg.append(f'    <rect x="18" y="{y}" width="284" height="40" rx="6" fill="rgba(39, 39, 42, 0.8)" stroke="#52525b" stroke-width="1"/>')
        svg.append(f'    <text x="30" y="{y+25}" font-family="sans-serif" font-size="13" font-weight="bold" fill="#facc15">{p_name}</text>')
        svg.append(f'    <text x="125" y="{y+25}" font-family="Prompt, sans-serif" font-size="11" fill="#e4e4e7">{p_desc}</text>')

    svg.append('  </g>')
    svg.extend([
        '  <g transform="translate(60, 455)">',
        '    <rect x="0" y="0" width="680" height="95" rx="10" fill="rgba(24, 24, 27, 0.8)" stroke="#a16207" stroke-width="1"/>',
        '    <text x="24" y="32" font-family="Prompt, sans-serif" font-size="15" font-weight="bold" fill="#fbbf24">🔍 ตำราหมาอีเสินเซียง (麻衣神相) &amp; หลิ่วจวงเซินเซียง (柳莊相法)</text>',
        '    <text x="24" y="60" font-family="Prompt, sans-serif" font-size="12" fill="#94a3b8">วิเคราะห์สัดส่วน 3 ส่วน (三庭) 5 ขุนเขา (五嶽) 4 สายน้ำ (四瀆) และ 12 ภพบนใบหน้าเพื่อชี้นำศักยภาพชะตาชีวิต</text>',
        '  </g>',
        '</svg>'
    ])
    return "\n".join(svg)


def generate_multimodal_matrix_svg(data: dict[str, Any], title: str | None = None, lang: str = "th") -> str:
    """Generate Composite 16-Discipline Multimodal Matrix SVG chart."""
    title = _resolve_svg_title("multimodal", title, lang)
    """Generate Composite 16-Discipline Multimodal Matrix SVG chart."""
    domain_name = data.get("domain_name", "ธุรกิจและการงาน (Career)")
    consensus_pct = data.get("consensus_score_pct", 88)
    favorable_pct = data.get("favorable_pct", 82)
    cautious_pct = 100 - favorable_pct
    element_harmony = data.get("element_harmony", "ธาตุไม้-ธาตุไฟ เกื้อหนุนสมบูรณ์")

    disciplines = [
        ("四柱 BaZi", 0.90), ("紫微 ZiWei", 0.85), ("奇門 QiMen", 0.92), ("六壬 LiuRen", 0.80),
        ("易經 IChing", 0.88), ("玄空 XuanKong", 0.84), ("擇吉 ZeJi", 0.90), ("โหรไทย Thai", 0.86),
        ("สากล Western", 0.82), ("สัตตเลข 7Base", 0.88), ("太乙 TaiYi", 0.85), ("六爻 LiuYao", 0.87),
        ("梅花 MeiHua", 0.89), ("三合 SanHe", 0.83), ("七政 QiZheng", 0.86), ("麻衣 MianXiang", 0.85)
    ]

    import math
    cx, cy, r_max = 200, 260, 130
    radar_points = []

    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" width="100%" height="100%">',
        '  <defs>',
        '    <linearGradient id="bgMultiGrad" x1="0%" y1="0%" x2="100%" y2="100%">',
        '      <stop offset="0%" stop-color="#080d1a"/>',
        '      <stop offset="100%" stop-color="#1e1b4b"/>',
        '    </linearGradient>',
        '    <filter id="glowMulti" x="-20%" y="-20%" width="140%" height="140%">',
        '      <feGaussianBlur stdDeviation="4" result="blur"/>',
        '      <feComposite in="SourceGraphic" in2="blur" operator="over"/>',
        '    </filter>',
        '  </defs>',
        '  <rect width="800" height="600" rx="16" fill="url(#bgMultiGrad)" stroke="#6366f1" stroke-width="2"/>',
        f'  <text x="400" y="40" font-family="Prompt, sans-serif" font-size="20" font-weight="bold" fill="#fbbf24" text-anchor="middle" filter="url(#glowMulti)">🌐 {title}</text>',
        f'  <text x="400" y="68" font-family="Prompt, sans-serif" font-size="13" fill="#cbd5e1" text-anchor="middle">หมวดคำถาม: <tspan fill="#38bdf8" font-weight="bold">[{domain_name}]</tspan> | ดัชนีความสอดคล้อง 16 ศาสตร์: <tspan fill="#34d399" font-weight="bold">{consensus_pct}%</tspan></text>',
        
        # Left Panel: 16-Spoke Radar Chart
        f'  <circle cx="{cx}" cy="{cy}" r="{r_max}" fill="rgba(15, 23, 42, 0.6)" stroke="#334155" stroke-width="1.5"/>',
        f'  <circle cx="{cx}" cy="{cy}" r="{r_max*0.75:.1f}" fill="none" stroke="#1e293b" stroke-dasharray="3,3"/>',
        f'  <circle cx="{cx}" cy="{cy}" r="{r_max*0.5:.1f}" fill="none" stroke="#1e293b" stroke-dasharray="3,3"/>',
        f'  <circle cx="{cx}" cy="{cy}" r="{r_max*0.25:.1f}" fill="none" stroke="#1e293b" stroke-dasharray="3,3"/>',
    ]

    for idx, (d_name, score) in enumerate(disciplines):
        angle = (idx * 2 * math.pi / 16) - (math.pi / 2)
        sx = cx + r_max * math.cos(angle)
        sy = cy + r_max * math.sin(angle)
        svg.append(f'  <line x1="{cx}" y1="{cy}" x2="{sx:.1f}" y2="{sy:.1f}" stroke="#334155" stroke-width="1"/>')
        # Label outside
        lx = cx + (r_max + 22) * math.cos(angle)
        ly = cy + (r_max + 22) * math.sin(angle)
        svg.append(f'  <text x="{lx:.1f}" y="{ly+4:.1f}" font-family="sans-serif" font-size="9" fill="#94a3b8" text-anchor="middle">{d_name.split()[0]}</text>')
        # Radar point
        px = cx + (r_max * score) * math.cos(angle)
        py = cy + (r_max * score) * math.sin(angle)
        radar_points.append(f'{px:.1f},{py:.1f}')

    points_str = " ".join(radar_points)
    svg.append(f'  <polygon points="{points_str}" fill="rgba(45, 212, 191, 0.25)" stroke="#2dd4bf" stroke-width="2"/>')
    svg.append(f'  <circle cx="{cx}" cy="{cy}" r="28" fill="#0f172a" stroke="#fbbf24" stroke-width="2"/>')
    svg.append(f'  <text x="{cx}" y="{cy+6}" font-family="Outfit, sans-serif" font-size="14" font-weight="bold" fill="#fbbf24" text-anchor="middle">{consensus_pct}%</text>')

    # Right Panel: 4 Metaphysics Super-Families Cards
    families = [
        ("🏛️ สายโหราศาสตร์คำนวณ (Astrological)", "BaZi • ZiWei • QiZheng • ThaiVedic", "สอดคล้อง 89% — ดาวเกื้อหนุนดิถีแข็งแกร่ง", "#38bdf8", 95),
        ("🔮 สายพยากรณ์ & ไตรวิชา (Divination/San Shi)", "QiMen • LiuRen • TaiYi • IChing • LiuYao • MeiHua", "สอดคล้อง 92% — ทิศมงคลเปิด ประตูส่งเสริม", "#c084fc", 185),
        ("🏯 สายฮวงจุ้ย & ฤกษ์ยาม (Geomancy & Timing)", "XuanKong • SanHe • ZeJi", "สอดคล้อง 85% — ชัยภูมิน้ำเข้า องศามงคลยุค 9", "#34d399", 275),
        ("🔢 สายเลขศาสตร์ & นรลักษณ์ (Numerology/Face)", "Satta-Lek • MianXiang • WesternUranian", "สอดคล้อง 86% — โหงวเฮ้งสมดุล รากเลขดาวศุภเคราะห์", "#fbbf24", 365)
    ]

    for f_title, f_sub, f_detail, f_color, y_pos in families:
        svg.append(f'  <g transform="translate(410, {y_pos})">')
        svg.append(f'    <rect x="0" y="0" width="340" height="78" rx="8" fill="rgba(15, 23, 42, 0.85)" stroke="{f_color}" stroke-width="1"/>')
        svg.append(f'    <text x="12" y="22" font-family="Prompt, sans-serif" font-size="12" font-weight="bold" fill="{f_color}">{f_title}</text>')
        svg.append(f'    <text x="12" y="42" font-family="sans-serif" font-size="10" fill="#94a3b8">{f_sub}</text>')
        svg.append(f'    <text x="12" y="62" font-family="Prompt, sans-serif" font-size="11" fill="#f8fafc">{f_detail}</text>')
        svg.append('  </g>')

    # Bottom Panel: Polarity Balance Bar & Synthesis Guidance
    svg.extend([
        '  <g transform="translate(50, 465)">',
        '    <rect x="0" y="0" width="700" height="95" rx="10" fill="rgba(15, 23, 42, 0.9)" stroke="#4f46e5" stroke-width="1"/>',
        f'    <text x="20" y="26" font-family="Prompt, sans-serif" font-size="13" font-weight="bold" fill="#f8fafc">⚖️ ดุลยภาพมงคล (Polarity Balance): มงคลเกื้อหนุน {favorable_pct}% | พึงระวัง {cautious_pct}%</text>',
        # Progress Bar
        f'    <rect x="20" y="36" width="660" height="14" rx="7" fill="#334155"/>',
        f'    <rect x="20" y="36" width="{660 * favorable_pct / 100:.1f}" height="14" rx="7" fill="url(#barGradMulti)"/>',
        f'    <text x="20" y="74" font-family="Prompt, sans-serif" font-size="12" fill="#cbd5e1">💡 บทสรุปสังเคราะห์: {element_harmony} — ทั้ง 16 ศาสตร์เห็นพ้องต้องกันในทิศทางเติบโตมั่นคง</text>',
        '  </g>',
        '  <defs>',
        '    <linearGradient id="barGradMulti" x1="0%" y1="0%" x2="100%" y2="0%">',
        '      <stop offset="0%" stop-color="#10b981"/>',
        '      <stop offset="100%" stop-color="#38bdf8"/>',
        '    </linearGradient>',
        '  </defs>',
        '</svg>'
    ])
    return "\n".join(svg)


