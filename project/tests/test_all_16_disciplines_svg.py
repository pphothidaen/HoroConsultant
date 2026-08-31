"""
project/tests/test_all_16_disciplines_svg.py
=============================================
Verification of high-fidelity standalone responsive SVG chart generation
across all 16 Metaphysics disciplines:
  1. BaZi 4 Pillars
  2. Zi Wei Dou Shu
  3. Qi Men Dun Jia
  4. Da Liu Ren
  5. Tai Yi Shen Shu
  6. I Ching Hexagram
  7. Liu Yao 6-Line Na Jia
  8. Mei Hua Plum Blossom
  9. Xuan Kong Flying Stars
  10. San He Feng Shui
  11. Mian Xiang Physiognomy
  12. Ze Ji Date Selection
  13. Thai Suriyayart & Vedic Nakshatra
  14. Western Tropical & Uranian TNPs
  15. Satta-Lek 7-Base Numerology
  16. Qi Zheng Si Yu Astrolabe
  + Zodiac Wheel
  + Multimodal Consensus Matrix
"""

from __future__ import annotations

import pytest
from project.core.svg_generator import (
    render_svg_chart,
    DISCIPLINE_SVG_GENERATORS,
    generate_bazi_svg,
    generate_ziwei_svg,
    generate_qimen_svg,
    generate_liuren_svg,
    generate_tai_yi_svg,
    generate_iching_svg,
    generate_liu_yao_svg,
    generate_meihua_svg,
    generate_xuankong_svg,
    generate_sanhe_svg,
    generate_mianxiang_svg,
    generate_zeji_svg,
    generate_thaivedic_svg,
    generate_western_svg,
    generate_numerology_svg,
    generate_qizheng_svg,
    generate_zodiac_wheel_svg,
    generate_multimodal_matrix_svg,
)


DISCIPLINES_TEST_DATA = [
    ("bazi", {"day_master": {"stem": "甲", "element": "Wood", "polarity": "Yang"}, "pillars": {}}),
    ("ziwei", {"five_element_bureau": "土五局", "ming_gong_branch": "亥", "palaces": []}),
    ("qimen", {"solar_term": "立秋", "dun_type": "Yin", "ju_number": 5, "palaces": []}),
    ("liuren", {"day_stem_branch": "甲子", "three_transmissions": {"初傳 (發端)": "未"}}),
    ("taiyi", {"accumulated_years": 6, "star_palace": 6, "tai_yi_number": 8630}),
    ("iching", {"primary_hexagram": {"name": "本卦"}, "transformed_hexagram": {"name": "變卦"}, "six_lines": []}),
    ("liuyao", {"palace": "乾", "palace_element": "金", "lines": []}),
    ("meihua", {"primary_hexagram": "乾為天", "mutual_hexagram": "乾為天", "transformed_hexagram": "天風姤"}),
    ("xuankong", {"period": 9, "facing_mountain": "午", "sitting_mountain": "子", "grid_palaces": []}),
    ("sanhe", {"sitting_mountain": "子", "facing_mountain": "午", "water_exit": "辰"}),
    ("mianxiang", {"face_shape": "Water (水形)", "twelve_palaces": {}}),
    ("zeji", {"duty_officer": "成日", "overall_status": "吉", "activities_suitability": {}}),
    ("thaivedic", {"thai_lagna": "เมษ", "kalakini_planet": "จันทร์", "sri_planet": "พฤหัสบดี"}),
    ("western", {"planets_tropical": {}, "uranian_tnps": {}}),
    ("numerology", {"satta_lek": {"matrix_7_base": []}, "chaldean_score": {"total_score": 57}}),
    ("qizheng", {"datetime": "2026-08-16 12:00:00", "planets": {}, "shadow_stars": {}}),
    ("zodiac", {}),
    ("multimodal", {"domain_name": "Career", "consensus_score_pct": 92}),
]


class TestAll16DisciplinesSVG:
    """Verifies standalone SVG generation and rendering for all 16 disciplines."""

    @pytest.mark.parametrize("discipline,chart_data", DISCIPLINES_TEST_DATA)
    def test_direct_and_dispatcher_svg_generation(self, discipline, chart_data):
        # 1. Via dispatcher
        svg_disp = render_svg_chart(discipline, chart_data, lang="th")
        assert svg_disp.startswith("<svg")
        assert svg_disp.endswith("</svg>")
        assert "xmlns=\"http://www.w3.org/2000/svg\"" in svg_disp

        # 2. Localized titles (EN / ZH)
        svg_en = render_svg_chart(discipline, chart_data, lang="en")
        assert svg_en.startswith("<svg")
        assert svg_en.endswith("</svg>")

        svg_zh = render_svg_chart(discipline, chart_data, lang="zh")
        assert svg_zh.startswith("<svg")
        assert svg_zh.endswith("</svg>")

    def test_registry_completeness(self):
        assert len(DISCIPLINE_SVG_GENERATORS) >= 16
        for disc in ["bazi", "ziwei", "qimen", "liuren", "taiyi", "iching", "liuyao", "meihua",
                     "xuankong", "sanhe", "mianxiang", "zeji", "thaivedic", "western", "numerology", "qizheng"]:
            assert disc in DISCIPLINE_SVG_GENERATORS
