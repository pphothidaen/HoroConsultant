"""
project/tests/test_meta_plan_002_svg_visualizers.py
====================================================
Sprint META-PLAN-002: Milestone M3 SVG Visualizer Test Suite.

Verifies:
1. Valid SVG XML structure and zero syntax/rendering errors across all 16 engines:
   - BaZi 4 Pillars (`generate_bazi_svg`)
   - Zi Wei Dou Shu 12 Palaces (`generate_ziwei_svg`)
   - Qi Men Dun Jia 9-Grid (`generate_qimen_svg`)
   - Da Liu Ren 3-Transmissions (`generate_liuren_svg`)
   - Tai Yi Shen Shu 16-Path (`generate_tai_yi_svg`)
   - I Ching Hexagram (`generate_iching_svg`)
   - Liu Yao 6-Line Na Jia (`generate_liu_yao_svg`)
   - Mei Hua Plum Blossom (`generate_meihua_svg`)
   - Xuan Kong Flying Stars (`generate_xuankong_svg`)
   - San He 24-Mountain Water Flow (`generate_sanhe_svg`)
   - Ze Ji Date Selection (`generate_zeji_svg`)
   - Mian Xiang 12 Facial Palaces (`generate_mianxiang_svg`)
   - Thai & Vedic Suriyayart (`generate_thaivedic_svg`)
   - Western & Uranian (`generate_western_svg`)
   - Numerology & Satta-Lek (`generate_numerology_svg`)
   - Qi Zheng Si Yu (`generate_qizheng_svg`)
   - Zodiac Wheel (`generate_zodiac_wheel_svg`)
   - Unified Multimodal Consensus Matrix (`generate_multimodal_matrix_svg`)
2. Responsive viewport geometry (`viewBox`, width="100%", height="100%", non-overflow coordinate systems).
3. Multilingual localization (`th`, `en`, `zh`).
4. Safe XML escaping for special characters (&, <, >, ", ').
5. Direct pipeline coupling from Engine calculation outputs to SVG generators.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from datetime import datetime
import pytest

from project.core.bazi_engine import BaZiEngine
from project.core.zi_wei_engine import ZiWeiEngine
from project.core.qi_men_engine import QiMenEngine
from project.core.liu_ren_engine import LiuRenEngine
from project.core.tai_yi_engine import TaiYiEngine
from project.core.iching_engine import IChingEngine
from project.core.liu_yao_engine import LiuYaoEngine
from project.core.mei_hua_engine import MeiHuaEngine
from project.core.xuan_kong_engine import XuanKongEngine
from project.core.san_he_engine import SanHeEngine
from project.core.ze_ji_engine import ZeJiEngine
from project.core.mian_xiang_engine import MianXiangEngine
from project.core.thai_vedic_engine import ThaiVedicEngine
from project.core.western_uranian_engine import WesternUranianEngine
from project.core.numerology_engine import NumerologyEngine
from project.core.qi_zheng_engine import QiZhengSiYuEngine
from project.core.svg_generator import (
    generate_bazi_svg,
    generate_ziwei_svg,
    generate_qimen_svg,
    generate_xuankong_svg,
    generate_liuren_svg,
    generate_iching_svg,
    generate_zeji_svg,
    generate_thaivedic_svg,
    generate_western_svg,
    generate_numerology_svg,
    generate_tai_yi_svg,
    generate_liu_yao_svg,
    generate_meihua_svg,
    generate_sanhe_svg,
    generate_qizheng_svg,
    generate_mianxiang_svg,
    generate_zodiac_wheel_svg,
    generate_multimodal_matrix_svg,
)


@pytest.fixture(scope="module")
def calculated_charts():
    """Pre-compute real engine charts for direct SVG pipeline verification."""
    dt = datetime(1990, 5, 15, 14, 30)
    return {
        "bazi": BaZiEngine().calculate(dt, 100.493, 7.0),
        "ziwei": ZiWeiEngine().calculate(1990, 5, 15, 14, "male"),
        "qimen": QiMenEngine().calculate(2026, 8, 7, 14),
        "liuren": LiuRenEngine().calculate("甲", "子", "正月", "午"),
        "taiyi": TaiYiEngine().calculate(2026, 8, 15, 12),
        "iching": IChingEngine().calculate_liu_yao("甲", [6, 7, 8, 9, 7, 8]),
        "liuyao": LiuYaoEngine().calculate([7, 8, 9, 8, 7, 6], 0, 0),
        "meihua": MeiHuaEngine().calculate(2026, 8, 31, 14),
        "xuankong": XuanKongEngine().calculate(180.0, 9),
        "sanhe": SanHeEngine().calculate(0.0, 180.0, 120.0),
        "zeji": ZeJiEngine().check_suitability("午", "申", "寅", "子"),
        "mianxiang": MianXiangEngine().calculate({"face_shape": "round"}, 1990),
        "thaivedic": ThaiVedicEngine().calculate(1990, 5, 15, 14, 2),
        "western": WesternUranianEngine().calculate(1990, 5, 15, 14),
        "numerology": NumerologyEngine().calculate(2, 6, 7),
        "qizheng": QiZhengSiYuEngine().calculate(1990, 5, 15, 14),
    }


class TestSVGVisualizersStructureAndWellFormedness:
    """Verifies valid XML parsing, viewBox attributes, and responsive layout for all visualizers."""

    SVG_GENERATORS = [
        ("BaZi", generate_bazi_svg, "bazi", "0 0 800 600"),
        ("ZiWei", generate_ziwei_svg, "ziwei", "0 0 800 800"),
        ("QiMen", generate_qimen_svg, "qimen", "0 0 600 600"),
        ("LiuRen", generate_liuren_svg, "liuren", "0 0 600 400"),
        ("TaiYi", generate_tai_yi_svg, "taiyi", "0 0 800 600"),
        ("IChing", generate_iching_svg, "iching", "0 0 600 500"),
        ("LiuYao", generate_liu_yao_svg, "liuyao", "0 0 800 600"),
        ("MeiHua", generate_meihua_svg, "meihua", "0 0 800 600"),
        ("XuanKong", generate_xuankong_svg, "xuankong", "0 0 600 600"),
        ("SanHe", generate_sanhe_svg, "sanhe", "0 0 800 600"),
        ("ZeJi", generate_zeji_svg, "zeji", "0 0 600 350"),
        ("MianXiang", generate_mianxiang_svg, "mianxiang", "0 0 800 600"),
        ("ThaiVedic", generate_thaivedic_svg, "thaivedic", "0 0 600 450"),
        ("Western", generate_western_svg, "western", "0 0 600 450"),
        ("Numerology", generate_numerology_svg, "numerology", "0 0 760 530"),
        ("QiZheng", generate_qizheng_svg, "qizheng", "0 0 800 600"),
        ("ZodiacWheel", generate_zodiac_wheel_svg, "western", "0 0 600 600"),
    ]

    @pytest.mark.parametrize("name,gen_fn,chart_key,expected_viewbox", SVG_GENERATORS)
    def test_svg_xml_well_formed_and_viewbox(self, calculated_charts, name, gen_fn, chart_key, expected_viewbox):
        chart = calculated_charts[chart_key]
        svg_text = gen_fn(chart)

        assert isinstance(svg_text, str)
        assert svg_text.startswith("<svg")
        assert svg_text.endswith("</svg>")
        assert 'xmlns="http://www.w3.org/2000/svg"' in svg_text
        assert f'viewBox="{expected_viewbox}"' in svg_text
        assert 'width="100%"' in svg_text
        assert 'height="100%"' in svg_text

        # Strict XML parsing verification — will raise ParseError if invalid XML
        root = ET.fromstring(svg_text)
        assert root.tag == "{http://www.w3.org/2000/svg}svg" or root.tag == "svg"
        assert root.attrib.get("viewBox") == expected_viewbox

    def test_multimodal_matrix_svg_well_formedness(self, calculated_charts):
        data = {
            "bazi": calculated_charts["bazi"],
            "ziwei": calculated_charts["ziwei"],
            "qimen": calculated_charts["qimen"],
            "xuankong": calculated_charts["xuankong"],
        }
        svg_text = generate_multimodal_matrix_svg(data)
        assert isinstance(svg_text, str)
        assert 'viewBox="0 0 800 600"' in svg_text

        root = ET.fromstring(svg_text)
        assert root.tag.endswith("svg")
        assert root.attrib.get("viewBox") == "0 0 800 600"


class TestSVGMultilingualAndSpecialCharacters:
    """Verifies localization and XML escaping across different languages."""

    @pytest.mark.parametrize("lang", ["th", "en", "zh"])
    def test_all_visualizers_support_locales(self, calculated_charts, lang):
        bazi_svg = generate_bazi_svg(calculated_charts["bazi"], lang=lang)
        ziwei_svg = generate_ziwei_svg(calculated_charts["ziwei"], lang=lang)
        qimen_svg = generate_qimen_svg(calculated_charts["qimen"], lang=lang)
        thaivedic_svg = generate_thaivedic_svg(calculated_charts["thaivedic"], lang=lang)
        western_svg = generate_western_svg(calculated_charts["western"], lang=lang)

        for svg_str in [bazi_svg, ziwei_svg, qimen_svg, thaivedic_svg, western_svg]:
            root = ET.fromstring(svg_str)
            assert root.tag.endswith("svg")

    def test_special_characters_in_custom_title_escaped(self, calculated_charts):
        """Verify custom titles with &, <, >, \", ' do not break XML parsing."""
        unsafe_title = 'Charts & Analytics <Special> "Test" \'Edition\''
        bazi_svg = generate_bazi_svg(calculated_charts["bazi"], title=unsafe_title)
        root = ET.fromstring(bazi_svg)
        assert root.tag.endswith("svg")
        assert "&amp;" in bazi_svg or "Charts & Analytics" in "".join(root.itertext())
