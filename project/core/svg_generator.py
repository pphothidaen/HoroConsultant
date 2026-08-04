"""
project/core/svg_generator.py
==============================
Generates standalone, high-aesthetic SVG vector charts for:
  1. BaZi 4 Pillars Chart (ผังดวง 4 เสาชะตา)
  2. Zodiac Wheel Chart (ผังดวงจักรราศี 12 ราศี)

Uses clean SVG markup with element color themes, traditional Chinese/Thai typography,
and Five Elements harmony indicators.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

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


def generate_bazi_svg(chart: Dict[str, Any], title: str = "ผังดวงชะตา BaZi 4 เสา (Four Pillars of Destiny)") -> str:
    """Generate clean SVG string for BaZi 4 Pillars Chart."""
    dm = chart.get("day_master", {})
    pcts = chart.get("five_elements", {}).get("percentages", {})
    tst  = chart.get("tst", {}).get("tst_datetime", "N/A")
    pillars = chart.get("pillars", {})

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
        
        # Header
        f'  <text x="400" y="45" font-family="Prompt, sans-serif" font-size="22" font-weight="bold" fill="#fbbf24" text-anchor="middle" filter="url(#glow)">☯ {title}</text>',
        f'  <text x="400" y="75" font-family="Prompt, sans-serif" font-size="13" fill="#94a3b8" text-anchor="middle">True Solar Time (TST): {tst} | Day Master: {dm.get("stem","")} ({dm.get("element","")} {dm.get("polarity","")})</text>',
        
        # 4 Pillars Columns
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

        # Column background box
        svg_parts.append(f'    <rect x="{x_pos+10}" y="10" width="140" height="320" rx="12" fill="#1e293b" fill-opacity="0.6" stroke="#475569" stroke-width="1.5"/>')
        
        # Column title
        svg_parts.append(f'    <text x="{x_pos+80}" y="35" font-family="Prompt, sans-serif" font-size="14" font-weight="bold" fill="#94a3b8" text-anchor="middle">{p_label}</text>')

        # Heavenly Stem Box
        svg_parts.append(f'    <rect x="{x_pos+25}" y="50" width="110" height="110" rx="10" fill="{s_color}" fill-opacity="0.15" stroke="{s_color}" stroke-width="2"/>')
        svg_parts.append(f'    <text x="{x_pos+80}" y="115" font-family="sans-serif" font-size="46" font-weight="bold" fill="{s_color}" text-anchor="middle">{stem.get("char","?")}</text>')
        svg_parts.append(f'    <text x="{x_pos+80}" y="145" font-family="Prompt, sans-serif" font-size="12" fill="#e2e8f0" text-anchor="middle">{stem.get("pinyin","")} ({stem.get("element","")})</text>')

        # Earthly Branch Box
        svg_parts.append(f'    <rect x="{x_pos+25}" y="180" width="110" height="110" rx="10" fill="{b_color}" fill-opacity="0.15" stroke="{b_color}" stroke-width="2"/>')
        svg_parts.append(f'    <text x="{x_pos+80}" y="245" font-family="sans-serif" font-size="46" font-weight="bold" fill="{b_color}" text-anchor="middle">{branch.get("char","?")}</text>')
        svg_parts.append(f'    <text x="{x_pos+80}" y="275" font-family="Prompt, sans-serif" font-size="12" fill="#e2e8f0" text-anchor="middle">{branch.get("pinyin","")} ({branch.get("zodiac","")})</text>')

    svg_parts.append('  </g>')

    # Five Elements Bar Chart Section
    svg_parts.append('  <g transform="translate(60, 450)">')
    svg_parts.append('    <text x="0" y="0" font-family="Prompt, sans-serif" font-size="15" font-weight="bold" fill="#fbbf24">⚖️ สัดส่วนสมดุล 5 ธาตุ (Five Elements Harmony)</text>')
    
    elems = ["Wood", "Fire", "Earth", "Metal", "Water"]
    bar_x = 0
    for el in elems:
        pct   = float(pcts.get(el, 0))
        color = ELEMENT_COLORS.get(el, "#ffffff")
        width = max(10, int(pct * 1.3))

        svg_parts.append(f'    <text x="{bar_x}" y="28" font-family="Prompt, sans-serif" font-size="12" fill="{color}">{el}: {pct:.1f}%</text>')
        svg_parts.append(f'    <rect x="{bar_x}" y="35" width="120" height="10" rx="5" fill="#334155"/>')
        svg_parts.append(f'    <rect x="{bar_x}" y="35" width="{width}" height="10" rx="5" fill="{color}"/>')
        bar_x += 135

    svg_parts.append('  </g>')
    svg_parts.append('</svg>')

    return "\n".join(svg_parts)


def generate_zodiac_wheel_svg(chart: Dict[str, Any], title: str = "ผังดวงจักรราศี 12 ราศี (Zodiac Wheel)") -> str:
    """Generate clean SVG string for Western/Thai Circular Zodiac Wheel Chart."""
    dm = chart.get("day_master", {})
    
    svg_parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="100%" height="100%">',
        '  <defs>',
        '    <radialGradient id="wheelGrad" cx="50%" cy="50%" r="50%">',
        '      <stop offset="0%" stop-color="#1e1b4b"/>',
        '      <stop offset="100%" stop-color="#090d16"/>',
        '    </radialGradient>',
        '  </defs>',
        '  <rect width="600" height="600" rx="16" fill="url(#wheelGrad)" stroke="#475569" stroke-width="2"/>',
        f'  <text x="300" y="40" font-family="Prompt, sans-serif" font-size="20" font-weight="bold" fill="#fbbf24" text-anchor="middle">♈ {title}</text>',
        f'  <text x="300" y="65" font-family="Prompt, sans-serif" font-size="12" fill="#94a3b8" text-anchor="middle">Day Master Center: {dm.get("stem","")} ({dm.get("element","")})</text>',
        '  <g transform="translate(300, 310)">',
        
        # Outer Wheel Circle
        '    <circle r="220" fill="none" stroke="#64748b" stroke-width="3"/>',
        '    <circle r="160" fill="none" stroke="#475569" stroke-width="2"/>',
        '    <circle r="80"  fill="#1e293b" stroke="#fbbf24" stroke-width="2"/>',
        
        # Center Day Master
        f'    <text x="0" y="8" font-family="sans-serif" font-size="32" font-weight="bold" fill="#fbbf24" text-anchor="middle">{dm.get("stem","庚")}</text>',
    ]

    import math
    for i in range(12):
        angle_rad = math.radians(i * 30 - 90)
        x_outer = 220 * math.cos(angle_rad)
        y_outer = 220 * math.sin(angle_rad)
        x_inner = 80 * math.cos(angle_rad)
        y_inner = 80 * math.sin(angle_rad)

        # Spoke line
        svg_parts.append(f'    <line x1="{x_inner:.1f}" y1="{y_inner:.1f}" x2="{x_outer:.1f}" y2="{y_outer:.1f}" stroke="#334155" stroke-width="1.5"/>')

        # House Label
        mid_angle = math.radians(i * 30 + 15 - 90)
        x_text = 190 * math.cos(mid_angle)
        y_text = 190 * math.sin(mid_angle)
        svg_parts.append(f'    <text x="{x_text:.1f}" y="{y_text:.1f}" font-family="Prompt, sans-serif" font-size="11" fill="#e2e8f0" text-anchor="middle" dominant-baseline="central">{ZODIAC_THAI[i].split()[0]}</text>')

    svg_parts.append('  </g>')
    svg_parts.append('</svg>')

    return "\n".join(svg_parts)
