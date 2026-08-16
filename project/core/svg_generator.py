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


def generate_bazi_svg(chart: dict[str, Any], title: str = "ผังดวงชะตา BaZi 4 เสา (Four Pillars of Destiny)") -> str:
    """Generate clean SVG string for BaZi 4 Pillars Chart."""
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

    order = [("hour", "เสายาม"), ("day", "เสาวัน"), ("month", "เสาเดือน"), ("year", "เสาปี")]

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


def generate_zodiac_wheel_svg(chart: dict[str, Any], title: str = "ผังดวงจักรราศี 12 ราศี (Zodiac Wheel)") -> str:
    """Generate clean SVG string for 12 Zodiac Wheel Chart."""
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


def generate_ziwei_svg(chart: dict[str, Any], title: str = "ผังดวง紫微斗數 (Zi Wei Dou Shu 12 Palaces Chart)") -> str:
    """Generate clean SVG string for Zi Wei Dou Shu 12 Palaces Chart."""
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


def generate_qimen_svg(chart: dict[str, Any], title: str = "ผังดวง奇門遁甲 (Qi Men Dun Jia 4-Plate Grid)") -> str:
    """Generate clean SVG string for Qi Men Dun Jia 9-Grid Chart."""
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


def generate_xuankong_svg(chart: dict[str, Any], title: str = "ผังดวง玄空風水 (Xuan Kong Flying Stars 9-Grid)") -> str:
    """Generate clean SVG string for Xuan Kong Flying Stars 9-Grid Chart."""
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


def generate_liuren_svg(chart: dict[str, Any], title: str = "ผังดวง大六壬 (Da Liu Ren 3-Transmission Chart)") -> str:
    """Generate SVG string for Da Liu Ren chart."""
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


def generate_iching_svg(chart: dict[str, Any], title: str = "ผังดวง易經六爻 (I Ching Divination Chart)") -> str:
    """Generate SVG string for I Ching Hexagram chart."""
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


def generate_zeji_svg(chart: dict[str, Any], title: str = "ผังดวง擇吉คำนวณฤกษ์ (Date Selection Chart)") -> str:
    """Generate SVG string for Ze Ji Date Selection chart."""
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


def generate_thaivedic_svg(chart: dict[str, Any], title: str = "ผังดวงโหราศาสตร์ไทย & ภารตวิทยา (Thai & Vedic)") -> str:
    """Generate SVG string for Thai Suriyayart & Vedic Nakshatra chart."""
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


def generate_western_svg(chart: dict[str, Any], title: str = "ผังดวงโหราศาสตร์สากล & ยูเรเนียน (Western & Uranian)") -> str:
    """Generate SVG string for Western Tropical & Uranian TNP chart."""
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


def generate_numerology_svg(chart: dict[str, Any], title: str = "ผังดวงสัตตเลข 7 ฐาน & เลขศาสตร์ (Numerology)") -> str:
    """Generate SVG string for Satta-Lek 7-Base Numerology chart."""
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
