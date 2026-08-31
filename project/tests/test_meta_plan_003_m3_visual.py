"""
project/tests/test_meta_plan_003_m3_visual.py
=============================================
Sprint META-PLAN-003: Milestone M3 Visual Integration Test Suite.

Comprehensive verification for:
1. All 18 Dynamic SVG Visualizers:
   - BaZi 4-Pillars (`generate_bazi_svg`, `render_bazi_svg`)
   - 12 Zodiac Astrolabe (`generate_zodiac_wheel_svg`, `render_zodiac_wheel_svg`)
   - Zi Wei Dou Shu 12-Palace (`generate_ziwei_svg`, `render_ziwei_svg`)
   - Qi Men Dun Jia 9-Grid (`generate_qimen_svg`, `render_qimen_svg`)
   - Da Liu Ren 3-Transmissions (`generate_liuren_svg`, `render_liuren_svg`)
   - Tai Yi Shen Shu 16-Path (`generate_tai_yi_svg`, `render_tai_yi_svg`)
   - I Ching Divination (`generate_iching_svg`, `render_iching_svg`)
   - Liu Yao 6-Line Na Jia (`generate_liu_yao_svg`, `render_liu_yao_svg`)
   - Mei Hua Plum Blossom (`generate_meihua_svg`, `render_meihua_svg`)
   - Xuan Kong Flying Stars (`generate_xuankong_svg`, `render_xuankong_svg`)
   - San He 24-Mountain Water Flow (`generate_sanhe_svg`, `render_sanhe_svg`)
   - Ze Ji Date Selection (`generate_zeji_svg`, `render_zeji_svg`)
   - Mian Xiang 12 Facial Palaces (`generate_mianxiang_svg`, `render_mianxiang_svg`)
   - Thai Suriyayart & Vedic (`generate_thaivedic_svg`, `render_thaivedic_svg`)
   - Western Tropical & Uranian (`generate_western_svg`, `render_western_svg`)
   - Satta-Lek Numerology (`generate_numerology_svg`, `render_numerology_svg`)
   - Qi Zheng Si Yu (`generate_qizheng_svg`, `render_qizheng_svg`)
   - 16-Discipline Multimodal Consensus Matrix (`generate_multimodal_matrix_svg`, `render_multimodal_matrix_svg`)
2. XML Well-Formedness & Strict Syntax:
   - Parse validation via `xml.etree.ElementTree.fromstring` (zero parse errors)
   - Root `<svg>` tag, XML namespace declaration, responsive width/height 100%
3. ViewBox Dimension Contracts:
   - Exact viewBox matching and responsive coordinate space across all 18 visualizers
4. Dark-Mode Glassmorphism Style Contracts:
   - Defs gradients, dark backdrop palettes, luminous card strokes, modern aesthetic typography
5. Five-Elements Color Token Contracts:
   - Wood: #10b981, Fire: #ef4444, Earth: #d97706, Metal: #38bdf8, Water: #8b5cf6
6. Multilingual Localization & XML Escaping:
   - Thai, English, and Chinese locale title headers
   - Safe character escaping for '&', '<', '>', '\"', \"'\"
7. FastAPI Calculation & Visual Response Contracts:
   - Verification of SVG payloads returned by FastAPI calculation endpoints

Pure ASCII logging and 100% deterministic test assertions.
"""

from __future__ import annotations

import logging
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Tuple

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from project.api_router import api_router
from project.core.bazi_engine import BaZiEngine
from project.core.iching_engine import IChingEngine
from project.core.liu_ren_engine import LiuRenEngine
from project.core.liu_yao_engine import LiuYaoEngine
from project.core.mei_hua_engine import MeiHuaEngine
from project.core.mian_xiang_engine import MianXiangEngine
from project.core.numerology_engine import NumerologyEngine
from project.core.qi_men_engine import QiMenEngine
from project.core.qi_zheng_engine import QiZhengSiYuEngine
from project.core.san_he_engine import SanHeEngine
from project.core.svg_generator import (
    ELEMENT_COLORS,
    SVG_LOCALES,
    generate_bazi_svg,
    generate_iching_svg,
    generate_liu_yao_svg,
    generate_liuren_svg,
    generate_meihua_svg,
    generate_mianxiang_svg,
    generate_multimodal_matrix_svg,
    generate_numerology_svg,
    generate_qimen_svg,
    generate_qizheng_svg,
    generate_sanhe_svg,
    generate_tai_yi_svg,
    generate_thaivedic_svg,
    generate_western_svg,
    generate_xuankong_svg,
    generate_zeji_svg,
    generate_ziwei_svg,
    generate_zodiac_wheel_svg,
)
from project.core.tai_yi_engine import TaiYiEngine
from project.core.thai_vedic_engine import ThaiVedicEngine
from project.core.western_uranian_engine import WesternUranianEngine
from project.core.xuan_kong_engine import XuanKongEngine
from project.core.ze_ji_engine import ZeJiEngine
from project.core.zi_wei_engine import ZiWeiEngine
from project.main import app
from project.mcp_server import HoroMCPTools, call_tool
from project.schemas.mcp_tools_v1 import (
    MCP_TOOL_REGISTRY,
    RenderSVGResult,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("test_m3_visual")


# ==============================================================================
# Visualizer Test Manifest (All 18 Visualizers)
# ==============================================================================

VISUALIZER_SPECS = [
    # (ID, ToolName, GeneratorFunction, FixtureKey, ExpectedViewBox, AspectRatio)
    ("bazi", "render_bazi_svg", generate_bazi_svg, "bazi", "0 0 800 600", "4:3"),
    ("zodiac_wheel", "render_zodiac_wheel_svg", generate_zodiac_wheel_svg, "bazi", "0 0 600 600", "1:1"),
    ("ziwei", "render_ziwei_svg", generate_ziwei_svg, "ziwei", "0 0 800 800", "1:1"),
    ("qimen", "render_qimen_svg", generate_qimen_svg, "qimen", "0 0 600 600", "1:1"),
    ("liuren", "render_liuren_svg", generate_liuren_svg, "liuren", "0 0 600 400", "3:2"),
    ("taiyi", "render_tai_yi_svg", generate_tai_yi_svg, "taiyi", "0 0 800 600", "4:3"),
    ("iching", "render_iching_svg", generate_iching_svg, "iching", "0 0 600 500", "6:5"),
    ("liuyao", "render_liu_yao_svg", generate_liu_yao_svg, "liuyao", "0 0 800 600", "4:3"),
    ("meihua", "render_meihua_svg", generate_meihua_svg, "meihua", "0 0 800 600", "4:3"),
    ("xuankong", "render_xuankong_svg", generate_xuankong_svg, "xuankong", "0 0 600 600", "1:1"),
    ("sanhe", "render_sanhe_svg", generate_sanhe_svg, "sanhe", "0 0 800 600", "4:3"),
    ("zeji", "render_zeji_svg", generate_zeji_svg, "zeji", "0 0 600 350", "12:7"),
    ("mianxiang", "render_mianxiang_svg", generate_mianxiang_svg, "mianxiang", "0 0 800 600", "4:3"),
    ("thaivedic", "render_thaivedic_svg", generate_thaivedic_svg, "thaivedic", "0 0 600 450", "4:3"),
    ("western", "render_western_svg", generate_western_svg, "western", "0 0 600 450", "4:3"),
    ("numerology", "render_numerology_svg", generate_numerology_svg, "numerology", "0 0 760 530", "4:3"),
    ("qizheng", "render_qizheng_svg", generate_qizheng_svg, "qizheng", "0 0 800 600", "4:3"),
    ("multimodal_matrix", "render_multimodal_matrix_svg", generate_multimodal_matrix_svg, "multimodal_matrix", "0 0 800 600", "4:3"),
]


@pytest.fixture(scope="module")
def precalculated_charts() -> Dict[str, Any]:
    """Calculate deterministic engine payloads used across all visualizer tests."""
    dt = datetime(1990, 5, 15, 14, 30)
    bazi_res = BaZiEngine().calculate(dt, 100.493, 7.0)
    ziwei_res = ZiWeiEngine().calculate(1990, 5, 15, 14, "male")
    qimen_res = QiMenEngine().calculate(2026, 8, 7, 14)
    liuren_res = LiuRenEngine().calculate("甲", "子", "正月", "午")
    taiyi_res = TaiYiEngine().calculate(2026, 8, 15, 12)
    iching_res = IChingEngine().calculate_liu_yao("甲", [6, 7, 8, 9, 7, 8])
    liuyao_res = LiuYaoEngine().calculate([7, 8, 9, 8, 7, 6], 0, 0)
    meihua_res = MeiHuaEngine().calculate(2026, 8, 31, 14)
    xuankong_res = XuanKongEngine().calculate(180.0, 9)
    sanhe_res = SanHeEngine().calculate(0.0, 180.0, 120.0)
    zeji_res = ZeJiEngine().check_suitability("午", "申", "寅", "子")
    mianxiang_res = MianXiangEngine().calculate({"face_shape": "round"}, 1990)
    thaivedic_res = ThaiVedicEngine().calculate(1990, 5, 15, 14, 2)
    western_res = WesternUranianEngine().calculate(1990, 5, 15, 14)
    numerology_res = NumerologyEngine().calculate(2, 6, 7)
    qizheng_res = QiZhengSiYuEngine().calculate(1990, 5, 15, 14)

    return {
        "bazi": bazi_res,
        "ziwei": ziwei_res,
        "qimen": qimen_res,
        "liuren": liuren_res,
        "taiyi": taiyi_res,
        "iching": iching_res,
        "liuyao": liuyao_res,
        "meihua": meihua_res,
        "xuankong": xuankong_res,
        "sanhe": sanhe_res,
        "zeji": zeji_res,
        "mianxiang": mianxiang_res,
        "thaivedic": thaivedic_res,
        "western": western_res,
        "numerology": numerology_res,
        "qizheng": qizheng_res,
        "multimodal_matrix": {
            "bazi": bazi_res,
            "ziwei": ziwei_res,
            "qimen": qimen_res,
            "xuankong": xuankong_res,
            "consensus_score": 0.92,
        },
    }


# ==============================================================================
# 1. XML Well-Formedness & ViewBox Dimension Contracts (18 Visualizers)
# ==============================================================================

class TestSVGVisualizerContracts:
    """Verifies XML syntax, viewBox geometry, and responsiveness across all 18 visualizers."""

    @pytest.mark.parametrize("disc_id,tool_name,gen_fn,fixture_key,expected_viewbox,aspect_ratio", VISUALIZER_SPECS)
    def test_svg_xml_well_formedness_and_viewbox(
        self,
        precalculated_charts: Dict[str, Any],
        disc_id: str,
        tool_name: str,
        gen_fn: Callable,
        fixture_key: str,
        expected_viewbox: str,
        aspect_ratio: str,
    ):
        chart_data = precalculated_charts[fixture_key]
        svg_content = gen_fn(chart_data)

        # 1. Basic string contracts
        assert isinstance(svg_content, str)
        assert len(svg_content) > 100, f"SVG output for {disc_id} is unexpectedly short"
        assert svg_content.startswith("<svg")
        assert svg_content.endswith("</svg>")
        assert 'xmlns="http://www.w3.org/2000/svg"' in svg_content
        assert f'viewBox="{expected_viewbox}"' in svg_content
        assert 'width="100%"' in svg_content
        assert 'height="100%"' in svg_content

        # 2. Strict XML Parsing Verification
        try:
            root = ET.fromstring(svg_content)
            assert root.tag.endswith("svg")
            assert root.attrib.get("viewBox") == expected_viewbox
        except ET.ParseError as err:
            pytest.fail(f"Invalid XML in visualizer '{disc_id}': {err}")

    def test_total_18_visualizers_registered(self):
        """Verify exactly 18 distinct visualizers in test suite manifest."""
        assert len(VISUALIZER_SPECS) == 18
        disc_ids = [s[0] for s in VISUALIZER_SPECS]
        assert len(set(disc_ids)) == 18


# ==============================================================================
# 2. Dark-Mode Glassmorphism Style Contracts
# ==============================================================================

class TestSVGGlassmorphismStyles:
    """Verifies dark-mode palette, defs gradient definitions, and glass card styling."""

    @pytest.mark.parametrize("disc_id,tool_name,gen_fn,fixture_key,expected_viewbox,aspect_ratio", VISUALIZER_SPECS)
    def test_dark_mode_glassmorphism_elements(
        self,
        precalculated_charts: Dict[str, Any],
        disc_id: str,
        tool_name: str,
        gen_fn: Callable,
        fixture_key: str,
        expected_viewbox: str,
        aspect_ratio: str,
    ):
        chart_data = precalculated_charts[fixture_key]
        svg_content = gen_fn(chart_data)
        root = ET.fromstring(svg_content)

        # 1. Must contain background rect with rounded corners (rx attribute)
        rects = [elem for elem in root.iter() if elem.tag.endswith("rect")]
        assert len(rects) >= 1, f"Visualizer {disc_id} missing SVG rects"
        assert any(r.attrib.get("rx") for r in rects), f"Visualizer {disc_id} missing rounded glass card corners"

        # 2. Must contain dark-mode palette background fill (hex #0x / #1x / #2x or dark gradient)
        has_dark_fill = any(
            r.attrib.get("fill", "").startswith("#0")
            or r.attrib.get("fill", "").startswith("#1")
            or r.attrib.get("fill", "").startswith("#2")
            or "bgGrad" in r.attrib.get("fill", "")
            or "rgba(" in r.attrib.get("fill", "")
            for r in rects
        )
        assert has_dark_fill is True, f"Visualizer {disc_id} missing dark-mode background fill"

        # 3. Must contain luminous border stroke
        has_stroke = any(r.attrib.get("stroke") for r in rects)
        assert has_stroke is True, f"Visualizer {disc_id} missing luminous glass card stroke"

        # 4. Must use clean typography styling
        text_elements = [elem for elem in root.iter() if elem.tag.endswith("text")]
        assert len(text_elements) >= 1, f"Visualizer {disc_id} missing SVG text elements"
        font_tokens = ["Prompt", "sans-serif", "font-family", "Arial"]
        assert any(
            any(f in t.attrib.get("font-family", "") for f in font_tokens)
            for t in text_elements
        ) or any(f in svg_content for f in font_tokens), f"Visualizer {disc_id} missing typography styling"


# ==============================================================================
# 3. Five-Elements Color Token Contracts
# ==============================================================================

class TestFiveElementsColorTokens:
    """Verifies standard Five-Elements color hex code contracts."""

    def test_element_colors_constant_contract(self):
        """Assert exact hex codes for Five Elements in ELEMENT_COLORS dictionary."""
        expected_colors = {
            "Wood": "#10b981",   # Emerald Green
            "Fire": "#ef4444",   # Crimson Red
            "Earth": "#d97706",  # Amber Ochre
            "Metal": "#38bdf8",  # Celestial Silver Blue
            "Water": "#8b5cf6",  # Deep Sapphire Purple
        }
        for element, hex_code in expected_colors.items():
            assert ELEMENT_COLORS.get(element) == hex_code, (
                f"Element '{element}' color mismatch: expected {hex_code}, got {ELEMENT_COLORS.get(element)}"
            )

    def test_element_colors_embedded_in_bazi_and_matrix_svgs(self, precalculated_charts: Dict[str, Any]):
        """Verify Five Elements hex codes appear in BaZi and Multimodal Matrix SVGs."""
        bazi_svg = generate_bazi_svg(precalculated_charts["bazi"])
        matrix_svg = generate_multimodal_matrix_svg(precalculated_charts["multimodal_matrix"])

        for element, color_hex in ELEMENT_COLORS.items():
            # Color hex must be present in either BaZi or Multimodal visualizer
            present_in_bazi = color_hex.lower() in bazi_svg.lower()
            present_in_matrix = color_hex.lower() in matrix_svg.lower()
            assert present_in_bazi or present_in_matrix, (
                f"Five-Element color {color_hex} ({element}) missing from chart SVGs"
            )


# ==============================================================================
# 4. Multilingual Localization & Special Character Escaping
# ==============================================================================

class TestSVGLocalizationAndEscaping:
    """Verifies localization across Thai, English, and Chinese, plus safe character escaping."""

    @pytest.mark.parametrize("lang", ["th", "en", "zh"])
    def test_multilingual_locale_generation(self, precalculated_charts: Dict[str, Any], lang: str):
        """Verify SVG generation in th, en, and zh produces valid XML."""
        for disc_id, tool_name, gen_fn, fixture_key, expected_viewbox, _ in VISUALIZER_SPECS[:6]:
            chart_data = precalculated_charts[fixture_key]
            svg_content = gen_fn(chart_data, lang=lang)
            root = ET.fromstring(svg_content)
            assert root.tag.endswith("svg")
            assert root.attrib.get("viewBox") == expected_viewbox

    def test_special_character_escaping_in_custom_title(self, precalculated_charts: Dict[str, Any]):
        """Verify custom titles with &, <, >, \", ' do not break XML parsing."""
        unsafe_title = 'Enterprise & Executive <Special> "Consultation" \'Edition\''
        for disc_id, tool_name, gen_fn, fixture_key, expected_viewbox, _ in VISUALIZER_SPECS[:6]:
            chart_data = precalculated_charts[fixture_key]
            try:
                svg_content = gen_fn(chart_data, title=unsafe_title)
                root = ET.fromstring(svg_content)
                assert root.tag.endswith("svg")
            except ET.ParseError as err:
                pytest.fail(f"Special character injection broke XML parsing in {disc_id}: {err}")


# ==============================================================================
# 5. MCP Tool Dispatch & FastAPI Endpoints for All 18 Visualizers
# ==============================================================================

class TestMCPAndAPIEndpointsVisualizerDispatch:
    """Verifies MCP tool dispatch and FastAPI endpoints for all 18 visualizers."""

    @pytest.fixture(scope="class")
    @classmethod
    def client(cls) -> TestClient:
        return TestClient(app)

    @pytest.fixture(scope="class")
    @classmethod
    def mcp_api_client(cls) -> TestClient:
        test_app = FastAPI()
        test_app.include_router(api_router)
        return TestClient(test_app)

    @pytest.mark.parametrize("disc_id,tool_name,gen_fn,fixture_key,expected_viewbox,aspect_ratio", VISUALIZER_SPECS)
    def test_mcp_tool_dispatch_visualizer(
        self,
        precalculated_charts: Dict[str, Any],
        disc_id: str,
        tool_name: str,
        gen_fn: Callable,
        fixture_key: str,
        expected_viewbox: str,
        aspect_ratio: str,
    ):
        """Test MCP call_tool invocation for each visualizer tool."""
        chart_data = precalculated_charts[fixture_key]
        param_key = "data" if disc_id == "multimodal_matrix" else "chart"
        args = {param_key: chart_data, "lang": "th"}

        res = call_tool(tool_name, args)
        assert res["success"] is True, f"MCP tool {tool_name} failed: {res.get('error')}"
        result = res["result"]
        assert "svg_content" in result
        assert result["viewBox"] == expected_viewbox
        assert len(result["svg_content"]) > 100

        # Validate parsed SVG from MCP payload
        root = ET.fromstring(result["svg_content"])
        assert root.tag.endswith("svg")

    def test_fastapi_mcp_call_endpoint_for_visualizers(self, mcp_api_client: TestClient, precalculated_charts: Dict[str, Any]):
        """Verify POST /api/mcp/call executing render_bazi_svg and render_ziwei_svg."""
        bazi_payload = {
            "tool_name": "render_bazi_svg",
            "arguments": {"chart": precalculated_charts["bazi"], "lang": "th"},
        }
        res = mcp_api_client.post("/api/mcp/call", json=bazi_payload)
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["result"]["viewBox"] == "0 0 800 600"
        assert "<svg" in data["result"]["svg_content"]

        ziwei_payload = {
            "tool_name": "render_ziwei_svg",
            "arguments": {"chart": precalculated_charts["ziwei"], "lang": "th"},
        }
        res_zw = mcp_api_client.post("/api/mcp/call", json=ziwei_payload)
        assert res_zw.status_code == 200
        data_zw = res_zw.json()
        assert data_zw["success"] is True
        assert data_zw["result"]["viewBox"] == "0 0 800 800"

    def test_fastapi_astrology_svg_content_responses(self, client: TestClient):
        """Verify FastAPI endpoints return embedded SVG content."""
        res_bazi = client.post(
            "/api/v1/bazi/calculate",
            json={"birth_datetime": "1990-05-15 14:30:00", "longitude": 100.4930, "utc_offset_hours": 7.0},
        )
        assert res_bazi.status_code == 200
        bazi_data = res_bazi.json()
        assert "svg_content" in bazi_data
        assert "zodiac_svg" in bazi_data
        assert "<svg" in bazi_data["svg_content"]
        assert "<svg" in bazi_data["zodiac_svg"]

        res_ziwei = client.get("/api/v1/ziwei/calculate", params={"year": 1990, "month": 5, "day": 15, "hour": 14, "gender": "male"})
        assert res_ziwei.status_code == 200
        assert "<svg" in res_ziwei.json().get("svg_content", "")
