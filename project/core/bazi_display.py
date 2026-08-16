"""
bazi_display.py — BaZi Chart HTML Display Generator
====================================================
Generates a complete, responsive HTML page replicating the fengshuix.com BaZi Chart display:

Sections:
  1. Top Navbar (BAZI.FENGSHUIX logo, actions, language selector)
  2. TST Correction Alert Banner (offset minutes, location)
  3. Page Title Header ("Bazi Chart & Analysis" with red underline)
  4. Top 3-Panel Layout:
     - Left: Header card (Person info, Life Stem, Ming Gua, Favorable / Unfavorable elements)
             + 5 Structures SVG Radar / Pentagon Spider Chart
     - Center: Four Pillars main chart (Hour, Day, Month, Year) with red vertical banner "四柱八字"
     - Right: Symbolic Stars & General Stars canonical matrix tables
  5. 10 Profiles Horizontal Proportions Bar Chart
  6. Da Yun 10-Year Luck Navigation Row (dark #1f2937 cells, Pre Da Yun + 12 cycles)
  7. Large Annual Cells Grid (12 rows x 13 cols with alternating #dc2626 / #991b1b styling)

Color scheme matching fengshuix.com:
  - Wood: Green (#16a34a)
  - Fire: Red (#dc2626)
  - Earth: Amber (#d97706)
  - Metal: Gray (#6b7280)
  - Water: Blue (#2563eb)
"""

from __future__ import annotations

import html
import math
from typing import Any


# ============================================================
# Style Tokens & Color Constants
# ============================================================

ELEMENT_COLORS: dict[str, str] = {
    "Wood":  "#16a34a",   # green-600
    "Fire":  "#dc2626",   # red-600
    "Earth": "#d97706",   # amber-600
    "Metal": "#6b7280",   # gray-500
    "Water": "#2563eb",   # blue-600
}

# Ten God badge colors: favorable/neutral (red bg) vs other (dark bg)
TG_BADGE_COLORS: dict[str, tuple[str, str]] = {
    "DM": ("#dc2626", "#ffffff"),
    "FR": ("#dc2626", "#ffffff"),
    "RW": ("#1f2937", "#ffffff"),
    "EG": ("#dc2626", "#ffffff"),
    "HO": ("#1f2937", "#ffffff"),
    "DW": ("#1f2937", "#ffffff"),
    "IW": ("#1f2937", "#ffffff"),
    "DO": ("#1f2937", "#ffffff"),
    "7K": ("#dc2626", "#ffffff"),
    "DR": ("#dc2626", "#ffffff"),
    "IR": ("#dc2626", "#ffffff"),
}

PILLAR_PHASE_COLORS: dict[str, str] = {
    "Chang Sheng": "#16a34a",  # green
    "Mu Yu":       "#d97706",  # amber
    "Guan Dai":    "#2563eb",  # blue
    "Lin Guan":    "#7c3aed",  # purple
    "Di Wang":     "#dc2626",  # red
    "Shuai":       "#6b7280",  # gray
    "Bing":        "#6b7280",  # gray
    "Si":          "#1f2937",  # dark
    "Mu":          "#374151",  # dark gray
    "Jue":         "#6b7280",  # gray
    "Tai":         "#16a34a",  # green
    "Yang":        "#16a34a",  # green
}

CE_TO_TH_OFFSET = 543   # Buddhist Era offset


def _th_year(ce_year: int) -> int:
    return ce_year + CE_TO_TH_OFFSET


# ============================================================
# Ten God Badge HTML
# ============================================================

def tg_badge(code: str, size: str = "sm") -> str:
    """Generate a styled Ten God badge."""
    if not code:
        return ""
    code_safe = html.escape(str(code))
    bg, fg = TG_BADGE_COLORS.get(code, ("#374151", "#ffffff"))
    font_size = "10px" if size == "sm" else "11px"
    padding   = "1px 4px" if size == "sm" else "2px 5px"
    return (
        f'<span style="background:{bg};color:{fg};font-size:{font_size};'
        f'font-weight:700;padding:{padding};border-radius:3px;display:inline-block;'
        f'line-height:1.4;letter-spacing:0.5px;font-family:monospace">{code_safe}</span>'
    )


# ============================================================
# Top Navbar
# ============================================================

def render_navbar() -> str:
    """Render top navigation bar."""
    return """
    <nav class="fx-navbar">
      <div class="fx-nav-left">
        <span class="fx-logo">BAZI.FENGSHUIX</span>
      </div>
      <div class="fx-nav-right">
        <button class="fx-nav-btn fx-btn-outline" type="button">ตั้งดวงใหม่</button>
        <button class="fx-nav-btn fx-btn-solid" type="button">เข้าสู่ระบบ</button>
        <span class="fx-lang-badge">TH</span>
      </div>
    </nav>"""


# ============================================================
# Alert Banner
# ============================================================

def render_alert_banner(chart: dict) -> str:
    """Render TST offset alert banner."""
    person   = chart.get("person", {})
    tst      = chart.get("solar_time_info", {})
    local_dt = person.get("birth_datetime", "")
    tst_dt   = str(tst.get("tst_datetime", ""))

    local_hm = local_dt[11:16] if len(local_dt) >= 16 else "--:--"
    tst_hm   = tst_dt[11:16] if len(tst_dt) >= 16 else "--:--"
    
    lon_offset = tst.get("longitude_offset_minutes", 0.0)
    eot        = tst.get("eot_minutes", 0.0)
    total_corr = round(lon_offset + eot)

    loc_name = person.get("location", "ราชบุรี (Ratchaburi)")
    if not loc_name:
        loc_name = "ราชบุรี (Ratchaburi)"

    return f"""
    <div class="alert-banner">
      <span class="alert-icon">ℹ️</span>
      <span><strong>[ระบบสมผุสท้องถิ่น]</strong> ปรับเวลาจาก {html.escape(local_hm)} เป็น {html.escape(tst_hm)} น. (ชดเชย {total_corr:+d} นาทีตามภูมิศาสตร์ {html.escape(str(loc_name))})</span>
    </div>"""


# ============================================================
# Page Title Header
# ============================================================

def render_page_title(title: str = "Bazi Chart & Analysis") -> str:
    """Render page title with red underline bar."""
    return f"""
    <div class="page-title">
      <h1>Bazi Chart <span>&</span> Analysis</h1>
      <div class="underline"></div>
    </div>"""


# ============================================================
# Header Info Card (Left Panel Top)
# ============================================================

def render_header_card(chart: dict) -> str:
    person  = chart.get("person", {})
    dm      = chart.get("day_master", {})
    mg      = chart.get("ming_gua", {})
    fav     = chart.get("favorable_elements", {})
    tst     = chart.get("solar_time_info", {})
    
    name    = person.get("name", "")
    surname = person.get("surname", "")
    full_name = f"{name} {surname}".strip() or "ป๋อง กพล"
    gender  = person.get("gender", "male")
    gender_icon = "♂" if str(gender).lower() in ("male", "m") else "♀"
    
    birth   = person.get("birth_datetime", "")[:16]
    birth_display = birth[:10].replace("-", "/") + f" ({birth[11:]} น.)" if len(birth) >= 16 else birth
    
    strength    = dm.get("strength", "WEAK")
    tst_str     = str(tst.get("tst_datetime", ""))[:16]
    tst_display = f"(เวลาท้องถิ่น: {tst_str[11:]} น.)" if len(tst_str) >= 16 else ""

    fav_elements   = fav.get("favorable", ["Wood", "Water", "Fire"])
    unfav_elements = fav.get("unfavorable", ["Metal", "Earth"])

    fav_list   = " → ".join([f"{i+1}. {e}" for i, e in enumerate(fav_elements)])
    unfav_list = " → ".join([f"{i+1}. {e}" for i, e in enumerate(unfav_elements)])

    dm_stem  = dm.get("stem", "丁")
    dm_elem  = dm.get("element", "Fire")
    dm_pol   = dm.get("polarity", "Yin")
    dm_color = ELEMENT_COLORS.get(dm_elem, "#dc2626")

    kua_name = mg.get("trigram_name", "Qian")
    kua_num  = mg.get("kua_number", 6)
    kua_dir  = mg.get("direction", "NORTHWEST")
    kua_zh   = mg.get("trigram_zh", "乾")

    return f"""
    <div class="header-card">
      <div class="person-info">
        <h2>{html.escape(full_name)} <span class="gender-icon">{gender_icon}</span></h2>
        <div class="birth-info">{html.escape(birth_display)}</div>
        <div class="tst-info">{html.escape(tst_display)}</div>
      </div>
      <div class="dm-section">
        <div class="dm-label">LIFE STEM</div>
        <div class="dm-char" style="color:{dm_color}">{html.escape(dm_stem)}</div>
        <div class="dm-detail">{html.escape(dm.get("pinyin", "Ding"))} {html.escape(dm_elem)} {html.escape(dm_pol)}</div>
        <div class="dm-strength">{html.escape(dm_stem)} ({html.escape(strength)})</div>
      </div>
      <div class="mingua-section">
        <div class="mingua-label">MING GUA</div>
        <div class="mingua-num">{kua_num}</div>
        <div class="mingua-name">{html.escape(kua_name)} ({html.escape(kua_zh)})</div>
        <div class="mingua-dir">{html.escape(kua_dir)}</div>
      </div>
      <div class="favorable-section">
        <div class="fav-row"><span class="fav-label">ให้คุณ (Favorable)</span><span class="fav-vals" style="color:#dc2626">{html.escape(fav_list)}</span></div>
        <div class="unfav-row"><span class="fav-label">ให้โทษ (Unfavorable)</span><span class="fav-vals" style="color:#6b7280">{html.escape(unfav_list)}</span></div>
      </div>
    </div>"""


# ============================================================
# Single Pillar Column
# ============================================================

def render_pillar_col(p: dict, is_day_master: bool = False) -> str:
    if not p:
        return "<div class='pillar-col empty'>—</div>"

    stem   = p.get("stem", {})
    branch = p.get("branch", {})
    tg_code  = p.get("ten_god", "")
    phase    = p.get("pillar_phase", {})
    stars    = p.get("stars", {})
    hs_list  = p.get("hidden_stems", [])

    stem_char    = stem.get("char", "")
    stem_elem    = stem.get("element", "Fire")
    stem_pol     = stem.get("polarity", "Yang")
    stem_color   = ELEMENT_COLORS.get(stem_elem, "#374151")

    branch_char  = branch.get("char", "")
    branch_elem  = branch.get("element", "Fire")
    branch_pol   = branch.get("polarity", "Yang")
    branch_color = ELEMENT_COLORS.get(branch_elem, "#374151")
    branch_animal= branch.get("animal", "")

    phase_name   = phase.get("phase", "")
    phase_zh     = phase.get("phase_zh", "")
    phase_color  = PILLAR_PHASE_COLORS.get(phase_name, "#6b7280")

    tg_html   = tg_badge(tg_code, "sm")
    dm_badge  = '<span class="dm-indicator" style="background:#dc2626;color:#fff;font-size:9px;padding:1px 3px;border-radius:2px;font-weight:700">DM</span>' if is_day_master else ""

    # Hidden stems section
    hs_chars_html = ""
    hs_tg_badges  = []
    for hs in hs_list:
        hsc  = hs.get("stem", "")
        hse  = hs.get("element", "")
        hstg = hs.get("ten_god", "")
        hs_clr = ELEMENT_COLORS.get(hse, "#374151")
        hs_chars_html += f'<span style="color:{hs_clr};font-weight:700;font-size:15px;margin:0 2px">{html.escape(hsc)}</span>'
        hs_tg_badges.append(tg_badge(hstg, "sm"))
    
    hs_tg_html = " ".join(hs_tg_badges)

    # Stars
    hvn_stars = stars.get("heavenly", [])
    eth_stars = stars.get("earthly", [])
    hvn_html  = "".join(f'<div class="star-item heavenly">{html.escape(s)}</div>' for s in hvn_stars) if hvn_stars else "<div class='star-none'>—</div>"
    eth_html  = "".join(f'<div class="star-item earthly">{html.escape(s)}</div>' for s in eth_stars) if eth_stars else "<div class='star-none'>—</div>"

    return f"""
    <div class="pillar-col {'day-master' if is_day_master else ''}">
      <div class="pillar-header">
        <div class="tg-badge-row">{tg_html} {dm_badge}</div>
      </div>
      <div class="stem-char" style="color:{stem_color}">{html.escape(stem_char)}</div>
      <div class="stem-info">{html.escape(stem.get("pinyin", ""))} {"+" if stem_pol=="Yang" else "-"}</div>
      <div class="branch-char" style="color:{branch_color}">{html.escape(branch_char)}</div>
      <div class="branch-info">{html.escape(branch.get("pinyin", ""))} {"+" if branch_pol=="Yang" else "-"}</div>
      <div class="branch-animal">{html.escape(branch_animal)}</div>
      <div class="hidden-stems">
        <div class="hs-chars">{hs_chars_html}</div>
        <div class="hs-tg">{hs_tg_html}</div>
      </div>
      <div class="phase-row">
        <span class="phase-zh">{html.escape(phase_zh)}</span>
        <span class="phase-en" style="color:{phase_color}">{html.escape(phase_name)}</span>
      </div>
      <div class="stars-section">
        <div class="stars-label">Heavenly Star</div>
        <div class="stars-content">{hvn_html}</div>
        <div class="stars-label">Earthly Star</div>
        <div class="stars-content">{eth_html}</div>
      </div>
    </div>"""


# ============================================================
# Main 4-Pillars Chart (Center Panel)
# ============================================================

def render_pillars_chart(chart: dict) -> str:
    pillars = chart.get("pillars", {})
    dm_stem = chart.get("day_master", {}).get("stem", "")

    order = ["hour", "day", "month", "year"]
    labels = {
        "hour": "Hour / ยาม",
        "day": "Day / วัน",
        "month": "Month / เดือน",
        "year": "Year / ปี",
    }

    cols_html = ""
    for key in order:
        p = pillars.get(key)
        is_dm = (key == "day") or (p and p.get("stem", {}).get("char", "") == dm_stem)
        header = f'<div class="pillar-col-header">{labels[key]}</div>'
        cols_html += f'<div class="pillar-wrapper">{header}{render_pillar_col(p, is_dm)}</div>'

    banner = '<div class="vertical-banner"><span>四柱八字 BAZI CHART</span></div>'

    return f"""
    <div class="pillars-section">
      <div class="pillars-grid">
        {cols_html}
        {banner}
      </div>
    </div>"""


# ============================================================
# 5 Structures Radar (SVG Spider Chart)
# ============================================================

def render_radar_chart(five_structures: dict) -> str:
    """Generate SVG spider/radar chart for 5 Structures."""
    struct_order = ["Companion", "Output", "Wealth", "Influence", "Resource"]
    labels_zh = {
        "Companion": "Companion (Fire)\nConnector",
        "Output":    "Output (Earth)\nCreator",
        "Wealth":    "Wealth (Metal)\nManager",
        "Influence": "Influence (Water)\nSupporter",
        "Resource":  "Resource (Wood)\nThinker",
    }

    cx, cy = 120, 120
    r_max  = 80
    n      = len(struct_order)

    svg_parts = ['<svg width="240" height="240" viewBox="0 0 240 240" class="radar-svg">']

    # Grid rings at 20%, 40%, 60%, 80%, 100%
    for pct in [0.2, 0.4, 0.6, 0.8, 1.0]:
        pts = []
        for i in range(n):
            angle = math.pi / 2 - (2 * math.pi * i / n)
            px    = cx + r_max * pct * math.cos(angle)
            py    = cy - r_max * pct * math.sin(angle)
            pts.append(f"{px:.1f},{py:.1f}")
        svg_parts.append(f'<polygon points="{" ".join(pts)}" fill="none" stroke="#e5e7eb" stroke-width="1"/>')

    # Spoke axes
    for i in range(n):
        angle = math.pi / 2 - (2 * math.pi * i / n)
        px    = cx + r_max * math.cos(angle)
        py    = cy - r_max * math.sin(angle)
        svg_parts.append(f'<line x1="{cx}" y1="{cy}" x2="{px:.1f}" y2="{py:.1f}" stroke="#e5e7eb" stroke-width="1"/>')

    # Data polygon
    data_pts = []
    for i, sname in enumerate(struct_order):
        val = min(max(five_structures.get(sname, {}).get("percentage", 0.0) / 40.0, 0.05), 1.0)
        angle = math.pi / 2 - (2 * math.pi * i / n)
        px    = cx + r_max * val * math.cos(angle)
        py    = cy - r_max * val * math.sin(angle)
        data_pts.append(f"{px:.1f},{py:.1f}")
    
    svg_parts.append(f'<polygon points="{" ".join(data_pts)}" fill="rgba(37,99,235,0.25)" stroke="#2563eb" stroke-width="2"/>')

    # Data circles
    for pt in data_pts:
        x, y = pt.split(",")
        svg_parts.append(f'<circle cx="{x}" cy="{y}" r="3" fill="#2563eb"/>')

    # Vertex labels
    for i, sname in enumerate(struct_order):
        angle = math.pi / 2 - (2 * math.pi * i / n)
        px    = cx + (r_max + 22) * math.cos(angle)
        py    = cy - (r_max + 22) * math.sin(angle)
        elem  = five_structures.get(sname, {}).get("element", "")
        color = ELEMENT_COLORS.get(elem, "#374151")
        pct_val = five_structures.get(sname, {}).get("percentage", 0.0)
        label_text = f"{sname} ({pct_val:.1f}%)"
        svg_parts.append(f'<text x="{px:.1f}" y="{py:.1f}" text-anchor="middle" dominant-baseline="middle" font-size="8.5" font-weight="700" fill="{color}">{html.escape(label_text)}</text>')

    svg_parts.append("</svg>")

    return f"""
    <div class="structures-section">
      <h3 class="section-title">5 Structures</h3>
      <div class="radar-container">
        {"".join(svg_parts)}
      </div>
    </div>"""


# ============================================================
# 10 Profiles Horizontal Bar Chart
# ============================================================

def render_ten_profiles(ten_profiles: dict) -> str:
    """Render horizontal bar chart for 10 Profiles."""
    sorted_tp = sorted(ten_profiles.items(), key=lambda x: -x[1]["percentage"])
    rows = []
    for code, data in sorted_tp:
        pct = data.get("percentage", 0.0)
        zh  = data.get("zh", "")
        sc  = data.get("stem_char", "")
        stem_str = f" ({sc})" if sc else ""
        bg, _ = TG_BADGE_COLORS.get(code, ("#1f2937", "#fff"))
        bar_w = min(max(pct * 2.8, 2), 220)
        rows.append(f"""
        <div class="profile-row">
          <div class="profile-badge-col">{tg_badge(code, "sm")}</div>
          <span class="profile-zh">{html.escape(zh)}{html.escape(stem_str)}</span>
          <div class="profile-bar-bg">
            <div class="profile-bar" style="width:{bar_w:.0f}px;background:{bg}"></div>
          </div>
          <span class="profile-pct">{pct:.2f}%</span>
        </div>""")

    return f"""
    <div class="profiles-section">
      <h3 class="section-title">10 Profiles Proportions</h3>
      <div class="profiles-list">
        {"".join(rows)}
      </div>
    </div>"""


# ============================================================
# Symbolic Stars Table (Right Panel Top)
# ============================================================

def render_symbolic_stars(sym_stars: dict) -> str:
    red_stars = {"Nobleman", "Intelligence", "Peach Blossom", "Fu Xing"}
    rows = ""
    for star_name, data in sym_stars.items():
        branches = data.get("branches", [])
        br_html  = " ".join(f'<span class="branch-chip">{html.escape(b)}</span>' for b in branches) if branches else "—"
        is_red   = star_name in red_stars
        note     = data.get("note", "")
        label    = f"{star_name} ({note})" if note else star_name
        rows += f"""
        <tr>
          <td class="star-name {'red' if is_red else ''}">{html.escape(label)}</td>
          <td class="star-branches">{br_html}</td>
        </tr>"""

    return f"""
    <div class="stars-table-section">
      <h3 class="section-title">Symbolic Stars (神煞)</h3>
      <table class="stars-table">
        <thead>
          <tr><th>Star</th><th>Zodiacs / Branches</th></tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
    </div>"""


# ============================================================
# General Stars Table (Right Panel Bottom)
# ============================================================

def render_general_stars(gen_stars: dict) -> str:
    red_stars = {"Travelling Horse"}
    rows = ""
    for star_name, data in gen_stars.items():
        day_b   = data.get("day", "—")
        year_b  = data.get("year", "—")
        is_red  = star_name in red_stars
        note    = data.get("note", "")
        label   = f"{star_name} ({note})" if note else star_name
        rows += f"""
        <tr>
          <td class="star-name {'red' if is_red else ''}">{html.escape(label)}</td>
          <td class="star-day"><span class="branch-chip">{html.escape(day_b)}</span></td>
          <td class="star-year"><span class="branch-chip">{html.escape(year_b)}</span></td>
        </tr>"""

    return f"""
    <div class="gen-stars-section">
      <h3 class="section-title">General Stars (十二星神)</h3>
      <table class="stars-table">
        <thead>
          <tr><th>Star</th><th>Day Branch</th><th>Year Branch</th></tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
    </div>"""


# ============================================================
# Da Yun Navigation & Annual Cells Grid
# ============================================================

def render_dayun_section(dayun: dict, annual_luck: list | None, birth_year: int) -> str:
    """Render Da Yun Navigation Row + Large Annual Grid."""
    if not dayun:
        return "<div class='dayun-empty'>—</div>"

    cycles     = dayun.get("cycles", [])
    pre_cycle  = dayun.get("pre_cycle", {})
    direction  = dayun.get("direction", "backward")
    start_age  = dayun.get("start_age_years", 6)
    formula    = dayun.get("formula", "ravi")
    annual     = annual_luck or []

    # Map annual luck entries by (cycle_num, offset_0_to_9)
    # Pre-Da Yun (cycle 0) covers ages 1 to (start_age - 1)
    ann_by_cycle: dict[int, list[dict]] = {}
    for ann in annual:
        cn = ann.get("dayun_cycle")
        if cn is not None:
            ann_by_cycle.setdefault(cn, []).append(ann)
        elif ann.get("age", 0) < start_age:
            ann_by_cycle.setdefault(0, []).append(ann)

    # 1. Navigation Row Headers
    nav_cols_html = ""

    # Pre Da Yun nav column
    pre_start_yr = pre_cycle.get("year_start", birth_year)
    nav_cols_html += f"""
    <div class="dayun-header-col pre-dayun">
      <div class="dayun-age">Pre Da Yun</div>
      <div class="dayun-yr">{pre_start_yr}/{_th_year(pre_start_yr)}</div>
      <div class="dayun-badge-ph">—</div>
      <div class="dayun-stem" style="color:#6b7280">—</div>
      <div class="dayun-branch" style="color:#6b7280">—</div>
      <div class="dayun-phase">Mu (0-{max(start_age-1, 0)} yrs)</div>
    </div>"""

    for cyc in cycles[:12]:
        age_lbl = f"{cyc['age_start']} yrs."
        yr_lbl  = f"{cyc['year_start']}/{_th_year(cyc['year_start'])}"
        tg_html = tg_badge(cyc.get("ten_god_stem", ""), "sm")
        phase   = cyc.get("pillar_phase", {})
        sc      = ELEMENT_COLORS.get(cyc.get("stem_element", ""), "#374151")
        bc      = ELEMENT_COLORS.get(cyc.get("branch_element", ""), "#374151")
        ph_name = phase.get("phase", "")
        ph_clr  = PILLAR_PHASE_COLORS.get(ph_name, "#6b7280")

        nav_cols_html += f"""
        <div class="dayun-header-col">
          <div class="dayun-age">{html.escape(age_lbl)}</div>
          <div class="dayun-yr">{html.escape(yr_lbl)}</div>
          <div class="dayun-badge-ph">{tg_html}</div>
          <div class="dayun-stem" style="color:{sc}">{html.escape(cyc.get("stem", ""))}</div>
          <div class="dayun-branch" style="color:{bc}">{html.escape(cyc.get("branch", ""))}</div>
          <div class="dayun-phase" style="color:{ph_clr}">{html.escape(ph_name)}</div>
        </div>"""

    # 2. Annual Cells Grid (10 rows for 10 years per cycle)
    ann_grid_rows_html = ""
    max_sub_rows = 10
    for row_idx in range(max_sub_rows):
        cells_html = ""
        # Pre Da Yun cell for this row
        pre_entries = ann_by_cycle.get(0, [])
        if row_idx < len(pre_entries):
            a       = pre_entries[row_idx]
            sc2     = ELEMENT_COLORS.get(a.get("stem_element", ""), "#ffffff")
            bc2     = ELEMENT_COLORS.get(a.get("branch_element", ""), "#ffffff")
            ph2     = a.get("pillar_phase", {})
            tg2     = tg_badge(a.get("ten_god_stem", ""), "sm")
            cells_html += f"""
            <div class="ann-cell pre-cell">
              <div class="ann-top-row">{tg2} <span class="ann-age">Age {a.get('age', '')}</span></div>
              <div class="ann-yr">{a.get('year_ce', '')}/{_th_year(a.get('year_ce', 0))}</div>
              <div class="ann-chars"><span style="color:{sc2}">{html.escape(a.get('stem',''))}</span><span style="color:{bc2}">{html.escape(a.get('branch',''))}</span></div>
              <div class="ann-phase">{html.escape(ph2.get('phase',''))}</div>
            </div>"""
        else:
            cells_html += '<div class="ann-cell empty"></div>'

        # Cycle cells
        for cyc in cycles[:12]:
            cn = cyc.get("cycle_num")
            c_entries = ann_by_cycle.get(cn, [])
            if row_idx < len(c_entries):
                a       = c_entries[row_idx]
                sc2     = ELEMENT_COLORS.get(a.get("stem_element", ""), "#ffffff")
                bc2     = ELEMENT_COLORS.get(a.get("branch_element", ""), "#ffffff")
                ph2     = a.get("pillar_phase", {})
                tg2     = tg_badge(a.get("ten_god_stem", ""), "sm")
                cells_html += f"""
                <div class="ann-cell">
                  <div class="ann-top-row">{tg2} <span class="ann-age">Age {a.get('age', '')}</span></div>
                  <div class="ann-yr">{a.get('year_ce', '')}/{_th_year(a.get('year_ce', 0))}</div>
                  <div class="ann-chars"><span style="color:{sc2}">{html.escape(a.get('stem',''))}</span><span style="color:{bc2}">{html.escape(a.get('branch',''))}</span></div>
                  <div class="ann-phase">{html.escape(ph2.get('phase',''))}</div>
                </div>"""
            else:
                cells_html += '<div class="ann-cell empty"></div>'

        ann_grid_rows_html += f'<div class="ann-row">{cells_html}</div>'

    return f"""
    <div class="dayun-section">
      <div class="dayun-title-bar">
        <h3 class="section-title">Da Yun — 大運 ({html.escape(direction.capitalize())}, starts age {start_age}, Formula: {html.escape(formula.upper())})</h3>
        <div class="dayun-meta-tags">
          <span class="dayun-tag">Pre Da Yun: 0-{max(start_age-1,0)} yrs</span>
          <span class="dayun-tag">120 Years Lifespan Matrix</span>
        </div>
      </div>
      <div class="dayun-scroll-wrapper">
        <div class="dayun-header-row">{nav_cols_html}</div>
        <div class="ann-grid-container">{ann_grid_rows_html}</div>
      </div>
    </div>"""


# ============================================================
# CSS Styles
# ============================================================

CSS = """
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: 'Noto Sans TC', 'Segoe UI', system-ui, -apple-system, sans-serif;
  background: #f3f4f6;
  color: #111827;
  font-size: 13px;
  line-height: 1.5;
}

.page-wrapper {
  max-width: 1440px;
  min-width: 1024px;
  margin: 0 auto;
  padding: 16px 24px;
}

/* Navbar */
.fx-navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #ffffff;
  padding: 12px 20px;
  border-radius: 10px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  margin-bottom: 16px;
}
.fx-logo {
  font-size: 18px;
  font-weight: 900;
  letter-spacing: 1px;
  color: #111827;
}
.fx-logo-dot { color: #dc2626; }
.fx-nav-right { display: flex; align-items: center; gap: 10px; }
.fx-nav-btn {
  font-size: 12px;
  font-weight: 600;
  padding: 6px 14px;
  border-radius: 6px;
  cursor: pointer;
  border: none;
}
.fx-btn-outline { background: #f3f4f6; color: #374151; border: 1px solid #d1d5db; }
.fx-btn-solid { background: #dc2626; color: #ffffff; }
.fx-lang-badge {
  background: #e5e7eb;
  color: #374151;
  font-weight: 700;
  font-size: 11px;
  padding: 4px 8px;
  border-radius: 4px;
}

/* Alert banner */
.alert-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #eff6ff;
  border-left: 4px solid #3b82f6;
  padding: 10px 16px;
  margin-bottom: 18px;
  border-radius: 0 8px 8px 0;
  font-size: 13px;
  color: #1e40af;
}

/* Page title */
.page-title { text-align: center; margin-bottom: 20px; }
.page-title h1 { font-size: 26px; font-weight: 800; color: #111827; }
.page-title h1 span { color: #dc2626; }
.page-title .underline { width: 60px; height: 3px; background: #dc2626; margin: 8px auto 0; border-radius: 2px; }

/* Top row 3-panel layout */
.top-row {
  display: grid;
  grid-template-columns: 290px 1fr 310px;
  gap: 16px;
  margin-bottom: 20px;
}
.left-panel { display: flex; flex-direction: column; gap: 14px; }
.center-panel {
  background: #ffffff;
  border-radius: 12px;
  padding: 14px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.right-panel { display: flex; flex-direction: column; gap: 14px; }

/* Header card */
.header-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.header-card h2 { font-size: 17px; font-weight: 700; color: #111827; }
.gender-icon { color: #2563eb; font-weight: 700; }
.birth-info { font-size: 12px; color: #4b5563; margin-top: 2px; }
.tst-info { font-size: 11px; color: #dc2626; margin-bottom: 10px; }
.dm-section { margin: 8px 0; }
.dm-label { font-size: 9px; text-transform: uppercase; color: #9ca3af; letter-spacing: 1px; font-weight: 700; }
.dm-char { font-size: 38px; font-weight: 800; line-height: 1; margin: 2px 0; }
.dm-detail { font-size: 11px; color: #6b7280; }
.dm-strength { font-size: 11px; color: #dc2626; font-weight: 700; margin-bottom: 6px; }
.mingua-section { margin: 8px 0; border-top: 1px solid #f3f4f6; padding-top: 8px; }
.mingua-label { font-size: 9px; text-transform: uppercase; color: #9ca3af; letter-spacing: 1px; font-weight: 700; }
.mingua-num { font-size: 26px; font-weight: 800; color: #111827; line-height: 1.1; }
.mingua-name { font-size: 12px; color: #374151; font-weight: 600; }
.mingua-dir { font-size: 11px; font-weight: 700; color: #2563eb; }
.favorable-section { margin-top: 8px; border-top: 1px solid #f3f4f6; padding-top: 8px; }
.fav-row, .unfav-row { display: flex; gap: 6px; flex-wrap: wrap; align-items: baseline; margin-bottom: 3px; }
.fav-label { font-size: 10px; color: #9ca3af; white-space: nowrap; font-weight: 600; }
.fav-vals { font-size: 11px; font-weight: 700; }

/* Pillars grid */
.pillars-section { width: 100%; }
.pillars-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr) 30px;
  gap: 0;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  overflow: hidden;
}
.pillar-wrapper { border-right: 1px solid #e5e7eb; }
.pillar-col-header {
  background: #f9fafb;
  text-align: center;
  padding: 8px 4px;
  font-size: 11px;
  font-weight: 700;
  border-bottom: 1px solid #e5e7eb;
  color: #374151;
}
.pillar-col {
  padding: 10px 6px;
  text-align: center;
  min-height: 380px;
  display: flex;
  flex-direction: column;
  gap: 3px;
  align-items: center;
  background: #ffffff;
}
.pillar-col.day-master { background: #fef2f2; }
.tg-badge-row { margin-bottom: 2px; display: flex; gap: 3px; justify-content: center; }
.stem-char { font-size: 46px; font-weight: 800; line-height: 1; }
.stem-info { font-size: 10px; color: #6b7280; }
.branch-char { font-size: 38px; font-weight: 700; line-height: 1; margin-top: 2px; }
.branch-info { font-size: 10px; color: #6b7280; }
.branch-animal { font-size: 11px; color: #374151; font-weight: 700; }
.hidden-stems { margin-top: 6px; padding: 4px; background: #f9fafb; border-radius: 6px; width: 100%; }
.hs-chars { font-size: 15px; font-weight: 700; margin-bottom: 2px; }
.hs-tg { display: flex; gap: 2px; justify-content: center; flex-wrap: wrap; }
.phase-row { margin-top: 6px; }
.phase-zh { font-size: 10px; color: #9ca3af; margin-right: 3px; }
.phase-en { font-size: 10px; font-weight: 700; }
.stars-section { margin-top: 6px; border-top: 1px solid #f3f4f6; padding-top: 4px; width: 100%; }
.stars-label { font-size: 8.5px; text-transform: uppercase; color: #9ca3af; letter-spacing: 0.5px; font-weight: 700; margin: 3px 0 1px; }
.stars-content { min-height: 18px; }
.star-item { font-size: 9.5px; padding: 1px 2px; margin: 1px 0; font-weight: 600; }
.star-item.heavenly { color: #dc2626; }
.star-item.earthly  { color: #2563eb; }
.star-none { font-size: 9px; color: #d1d5db; }

/* Vertical banner */
.vertical-banner {
  background: #dc2626;
  writing-mode: vertical-rl;
  text-orientation: mixed;
  color: #ffffff;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px 2px;
}
.vertical-banner span { writing-mode: vertical-rl; }

/* Section title */
.section-title {
  font-size: 13px;
  font-weight: 800;
  color: #111827;
  margin-bottom: 10px;
  border-bottom: 2px solid #dc2626;
  padding-bottom: 3px;
}

/* Radar */
.structures-section {
  background: #ffffff;
  border-radius: 12px;
  padding: 14px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.radar-container { display: flex; justify-content: center; overflow: visible; }
.radar-svg { overflow: visible; }

/* 10 Profiles */
.profiles-section {
  background: #ffffff;
  border-radius: 12px;
  padding: 14px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.profiles-list { display: flex; flex-direction: column; gap: 4px; }
.profile-row { display: flex; align-items: center; gap: 6px; }
.profile-badge-col { min-width: 26px; }
.profile-zh { font-size: 10.5px; color: #374151; font-weight: 600; min-width: 76px; }
.profile-bar-bg { flex: 1; background: #f3f4f6; border-radius: 3px; height: 7px; max-width: 140px; }
.profile-bar { height: 7px; border-radius: 3px; }
.profile-pct { font-size: 10.5px; color: #6b7280; font-weight: 700; min-width: 44px; text-align: right; }

/* Middle Layout */
.middle-row {
  display: grid;
  grid-template-columns: 340px 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

/* Stars tables */
.stars-table-section, .gen-stars-section {
  background: #ffffff;
  border-radius: 12px;
  padding: 14px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.stars-table { width: 100%; border-collapse: collapse; font-size: 11px; }
.stars-table th {
  padding: 5px 6px;
  background: #f9fafb;
  border-bottom: 2px solid #e5e7eb;
  text-align: left;
  font-size: 10px;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.stars-table td { padding: 4px 6px; border-bottom: 1px solid #f3f4f6; }
.star-name { font-weight: 600; color: #374151; }
.star-name.red { color: #dc2626; font-weight: 700; }
.branch-chip {
  background: #f3f4f6;
  border-radius: 3px;
  padding: 1px 4px;
  margin-right: 2px;
  font-size: 10.5px;
  font-weight: 600;
  display: inline-block;
}

/* Da Yun Section */
.dayun-section {
  background: #ffffff;
  border-radius: 12px;
  padding: 16px;
  margin-top: 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.dayun-title-bar {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 10px;
}
.dayun-meta-tags { display: flex; gap: 8px; }
.dayun-tag {
  background: #f3f4f6;
  color: #4b5563;
  font-size: 10px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
}
.dayun-scroll-wrapper {
  overflow-x: auto;
  padding-bottom: 6px;
}
.dayun-header-row {
  display: flex;
  gap: 4px;
  min-width: 1200px;
  margin-bottom: 6px;
}
.dayun-header-col {
  flex: 1 1 0;
  min-width: 88px;
  background: #1f2937;
  border-radius: 6px;
  padding: 6px 4px;
  text-align: center;
  color: #ffffff;
}
.dayun-header-col.pre-dayun {
  background: #374151;
}
.dayun-age { font-size: 10px; font-weight: 700; color: #f9fafb; }
.dayun-yr  { font-size: 9px; color: #9ca3af; margin-bottom: 2px; }
.dayun-badge-ph { min-height: 18px; margin: 1px 0; }
.dayun-stem, .dayun-branch { font-size: 24px; font-weight: 800; line-height: 1; }
.dayun-phase { font-size: 9px; font-weight: 700; margin-top: 2px; }

/* Annual Grid */
.ann-grid-container {
  min-width: 1200px;
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.ann-row {
  display: flex;
  gap: 4px;
}
.ann-cell {
  flex: 1 1 0;
  min-width: 88px;
  background: #dc2626;
  border-radius: 4px;
  padding: 4px 3px;
  text-align: center;
  color: #ffffff;
}
.ann-row:nth-child(even) .ann-cell { background: #991b1b; }
.ann-cell.pre-cell { background: #4b5563; }
.ann-row:nth-child(even) .ann-cell.pre-cell { background: #374151; }
.ann-cell.empty { background: transparent; }

.ann-top-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 2px;
  margin-bottom: 1px;
}
.ann-age { font-size: 8.5px; font-weight: 700; color: rgba(255,255,255,0.9); }
.ann-yr { font-size: 7.5px; color: rgba(255,255,255,0.7); line-height: 1; }
.ann-chars {
  font-size: 15px;
  font-weight: 800;
  line-height: 1.1;
  margin: 1px 0;
}
.ann-phase { font-size: 8px; color: rgba(255,255,255,0.85); font-weight: 600; }
</style>
"""


# ============================================================
# Full Standalone HTML Generator
# ============================================================

def generate_bazi_html(chart: dict, title: str = "Bazi Chart & Analysis") -> str:
    """
    Generate complete standalone HTML page replicating fengshuix.com layout.

    Parameters
    ----------
    chart : dict — output from BaZiEngine.calculate().chart_data
    title : str  — page title

    Returns
    -------
    str — complete HTML page as string
    """
    navbar_html   = render_navbar()
    banner_html   = render_alert_banner(chart)
    title_html    = render_page_title(title)
    header_html   = render_header_card(chart)
    pillars_html  = render_pillars_chart(chart)
    radar_html    = render_radar_chart(chart.get("five_structures", {}))
    profiles_html = render_ten_profiles(chart.get("ten_profiles", {}))
    sym_html      = render_symbolic_stars(chart.get("symbolic_stars", {}))
    gen_html      = render_general_stars(chart.get("general_stars", {}))

    person   = chart.get("person", {})
    birth_yr = int(str(person.get("birth_datetime", "1985"))[:4]) if person.get("birth_datetime") else 1985
    dayun_html = render_dayun_section(chart.get("dayun", {}), chart.get("annual_luck"), birth_yr)

    return f"""<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(title)}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;600;700;800;900&display=swap" rel="stylesheet">
  {CSS}
</head>
<body>
<div class="page-wrapper">

  <!-- Top Navbar -->
  {navbar_html}

  <!-- Alert banner -->
  {banner_html}

  <!-- Page title -->
  {title_html}

  <!-- Top row: Header | Pillars | Stars -->
  <div class="top-row">
    <div class="left-panel">
      {header_html}
      {radar_html}
    </div>
    <div class="center-panel">
      {pillars_html}
    </div>
    <div class="right-panel">
      {sym_html}
      {gen_html}
    </div>
  </div>

  <!-- Middle row: 10 Profiles Bar Chart -->
  <div class="middle-row">
    {profiles_html}
    <div></div>
  </div>

  <!-- Bottom Da Yun Navigation + Annual Grid (Full Width) -->
  {dayun_html}

</div>
</body>
</html>"""


# ============================================================
# CLI entry-point
# ============================================================

if __name__ == "__main__":
    import sys
    import json
    from datetime import datetime
    from project.core.bazi_engine import BaZiEngine

    engine = BaZiEngine()
    result = engine.calculate(
        dt=datetime(1985, 8, 26, 23, 3, 0),
        longitude=99.91,
        utc_offset_hours=7.0,
        gender="male",
        name="ป๋อง",
        surname="กพล",
        dayun_formula="ravi",
    )
    html_out = generate_bazi_html(result.chart_data)
    if len(sys.argv) > 1 and sys.argv[1] == "--save":
        out_path = sys.argv[2] if len(sys.argv) > 2 else "bazi_chart.html"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html_out)
        print(f"[OK] Saved to {out_path}")
    else:
        print(html_out[:500] + "...")
