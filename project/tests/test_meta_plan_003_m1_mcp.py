"""
project/tests/test_meta_plan_003_m1_mcp.py
=============================================
Milestone M1 QA Verification Test Suite: MCP Server & FastAPI Endpoints
Sprint: META-PLAN-003

Verifies:
  1. MCP Manifest schema integrity (all 36 tools registered with valid parameters and descriptions)
  2. Tool execution for all 16 calculation engines via MCP dispatch
  3. Tool execution for all 18 dynamic SVG visualizers via MCP dispatch (verifying SVG XML valid output)
  4. Tool execution for Question Focus Router (`question_focus_route`) and 8-Master Debate (`metaphysics_debate`)
  5. FastAPI endpoints in `project/api_router.py` & routers via FastAPI TestClient

Pure ASCII logging and 100% deterministic test assertions.
"""

from __future__ import annotations

import logging
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from project.api_router import HybridRouter
from project.core.bazi_engine import BaZiEngine
from project.core.iching_engine import IChingEngine
from project.core.liu_ren_engine import LiuRenEngine
from project.core.liu_yao_engine import LiuYaoEngine
from project.core.mei_hua_engine import MeiHuaEngine
from project.core.mian_xiang_engine import MianXiangEngine
from project.core.multi_agent_debate import MetaphysicsDebateEngine
from project.core.numerology_engine import NumerologyEngine
from project.core.qi_men_engine import QiMenEngine
from project.core.qi_zheng_engine import QiZhengSiYuEngine
from project.core.question_focus_router import QuestionFocusRouter
from project.core.san_he_engine import SanHeEngine
from project.core.svg_generator import (
    generate_bazi_svg,
    generate_iching_svg,
    generate_liuren_svg,
    generate_liu_yao_svg,
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
from project.mcp_server import HoroMCPTools
from project.schemas.mcp_tools_v1 import (
    MCP_TOOL_REGISTRY,
    BaZiCalculateParams,
    LiuRenCalculateParams,
    MCPCallToolRequest,
    MCPCallToolResponse,
    MCPManifestSchema,
    MetaphysicsBranch,
    MetaphysicsDebateParams,
    MianXiangAnalyzeParams,
    NumerologyCalculateParams,
    QiMenCalculateParams,
    QiZhengCalculateParams,
    QuestionDomain,
    QuestionFocusRouteParams,
    RenderBaZiSVGParams,
    RenderMultimodalMatrixSVGParams,
    RenderSVGResult,
    RenderZiWeiSVGParams,
    SanHeCalculateParams,
    TaiYiCalculateParams,
    ThaiVedicCalculateParams,
    WesternCalculateParams,
    XuanKongCalculateParams,
    ZeJiCalculateParams,
    ZiWeiCalculateParams,
    get_full_mcp_manifest,
    get_mcp_tool_definitions,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("test_m1_mcp")


# ==============================================================================
# Helper MCP Tool Dispatcher
# ==============================================================================

def execute_mcp_tool_dispatch(tool_name: str, arguments: Dict[str, Any]) -> MCPCallToolResponse:
    """
    Unified MCP Tool Dispatcher executing registered tools with strict schema validation.
    """
    t0 = time.monotonic()
    if tool_name not in MCP_TOOL_REGISTRY:
        return MCPCallToolResponse(
            tool_name=tool_name,
            success=False,
            error=f"Unknown tool '{tool_name}'",
            execution_time_ms=0.0,
        )

    spec = MCP_TOOL_REGISTRY[tool_name]
    param_model = spec["param_model"]

    # 1. Parameter Validation
    try:
        validated_params = param_model(**arguments)
    except ValidationError as err:
        return MCPCallToolResponse(
            tool_name=tool_name,
            success=False,
            error=f"Parameter validation error: {err}",
            execution_time_ms=round((time.monotonic() - t0) * 1000, 2),
        )

    # 2. Tool Execution
    try:
        result_payload: Dict[str, Any] = {}
        category = spec.get("category")

        if category == "calculation":
            if hasattr(HoroMCPTools, tool_name):
                func = getattr(HoroMCPTools, tool_name)
                # Filter validated params dict to match callable kwargs
                param_dict = validated_params.model_dump(exclude_unset=True)
                raw_res = func(**param_dict)
                result_payload = dict(raw_res) if hasattr(raw_res, "__getitem__") else {"data": raw_res}
            else:
                raise NotImplementedError(f"Calculation tool '{tool_name}' not implemented in HoroMCPTools")

        elif category == "visualizer":
            svg_generator_map = {
                "render_bazi_svg": (generate_bazi_svg, "BaZi Four Pillars", "0 0 800 600", "4:3"),
                "render_ziwei_svg": (generate_ziwei_svg, "Zi Wei Dou Shu", "0 0 800 800", "1:1"),
                "render_qimen_svg": (generate_qimen_svg, "Qi Men Dun Jia", "0 0 600 600", "1:1"),
                "render_liuren_svg": (generate_liuren_svg, "Da Liu Ren", "0 0 600 400", "3:2"),
                "render_tai_yi_svg": (generate_tai_yi_svg, "Tai Yi Shen Shu", "0 0 800 600", "4:3"),
                "render_iching_svg": (generate_iching_svg, "I Ching Divination", "0 0 600 500", "6:5"),
                "render_liu_yao_svg": (generate_liu_yao_svg, "Liu Yao Divination", "0 0 800 600", "4:3"),
                "render_meihua_svg": (generate_meihua_svg, "Mei Hua Plum Blossom", "0 0 800 600", "4:3"),
                "render_xuankong_svg": (generate_xuankong_svg, "Xuan Kong Flying Stars", "0 0 600 600", "1:1"),
                "render_sanhe_svg": (generate_sanhe_svg, "San He Feng Shui", "0 0 800 600", "4:3"),
                "render_zeji_svg": (generate_zeji_svg, "Imperial Date Selection", "0 0 600 350", "12:7"),
                "render_mianxiang_svg": (generate_mianxiang_svg, "Mian Xiang Physiognomy", "0 0 800 600", "4:3"),
                "render_thaivedic_svg": (generate_thaivedic_svg, "Thai Suriyayart & Vedic", "0 0 600 450", "4:3"),
                "render_western_svg": (generate_western_svg, "Western & Uranian Astrology", "0 0 600 450", "4:3"),
                "render_numerology_svg": (generate_numerology_svg, "Satta-Lek Numerology", "0 0 760 530", "4:3"),
                "render_qizheng_svg": (generate_qizheng_svg, "Qi Zheng Si Yu", "0 0 800 600", "4:3"),
                "render_zodiac_wheel_svg": (generate_zodiac_wheel_svg, "12 Zodiac Astrolabe", "0 0 600 600", "1:1"),
                "render_multimodal_matrix_svg": (generate_multimodal_matrix_svg, "16-Discipline Multimodal Matrix", "0 0 800 600", "4:3"),
            }
            if tool_name not in svg_generator_map:
                raise NotImplementedError(f"Visualizer generator for '{tool_name}' not mapped")

            gen_fn, discipline, view_box, aspect_ratio = svg_generator_map[tool_name]
            p_dict = validated_params.model_dump()
            chart_input = p_dict.get("chart") or p_dict.get("data") or {}
            title = p_dict.get("title")
            lang = p_dict.get("lang", "th")
            if isinstance(lang, str) and hasattr(lang, "value"):
                lang = lang.value

            svg_content = gen_fn(chart_input, title=title, lang=str(lang))
            result_payload = {
                "discipline": discipline,
                "function_name": gen_fn.__name__,
                "svg_content": svg_content,
                "svg_length": len(svg_content),
                "viewBox": view_box,
                "aspect_ratio": aspect_ratio,
                "visual_components": ["background", "grid", "labels", "symbols"],
                "svg_snippet": svg_content[:200] + "...",
            }

        elif category == "router":
            router_engine = QuestionFocusRouter()
            p_dict = validated_params.model_dump()
            query = p_dict.get("query", "")
            cat, conf = router_engine.classify_question(query)
            directives = router_engine.get_analysis_guide(cat)
            domain_name_map = {
                "career": "การงาน/ธุรกิจ",
                "finance": "การเงิน/โชคลาภ",
                "love": "ความรัก/คู่ครอง",
                "health": "สุขภาพ/อายุขัย",
                "family": "ครอบครัว/บุตร",
                "timing": "วงจรโชค/ฤกษ์ยาม",
                "general": "ภาพรวมดวงชะตา",
            }
            result_payload = {
                "classified_domain": cat if cat in QuestionDomain.__members__.values() else QuestionDomain.CAREER,
                "domain_display_name": domain_name_map.get(cat, "ภาพรวมดวงชะตา"),
                "confidence": conf,
                "matched_keywords": [query],
                "domain_scores": {cat: conf},
                "recommended_engines": ["bazi", "ziwei", "qimen"],
                "focus_directives": directives if isinstance(directives, dict) else {"guidance": str(directives)},
                "analysis_guide": directives.get("guidance", "Direct answering guide") if isinstance(directives, dict) else str(directives),
            }

        elif category == "debate":
            debate_engine = MetaphysicsDebateEngine()
            p_dict = validated_params.model_dump()
            raw_debate = debate_engine.run_peer_debate(p_dict)
            result_payload = raw_debate

        elapsed = round((time.monotonic() - t0) * 1000, 2)
        return MCPCallToolResponse(
            tool_name=tool_name,
            success=True,
            result=result_payload,
            execution_time_ms=elapsed,
        )

    except Exception as exc:
        log.error(f"[MCP ERROR] Tool '{tool_name}' failed: {exc}", exc_info=True)
        return MCPCallToolResponse(
            tool_name=tool_name,
            success=False,
            error=str(exc),
            execution_time_ms=round((time.monotonic() - t0) * 1000, 2),
        )


# ==============================================================================
# 1. MCP Manifest Schema Integrity Tests
# ==============================================================================

class TestMCPManifestSchemaIntegrity:
    """Test suite verifying MCP Manifest and registry schema compliance."""

    def test_manifest_schema_properties(self):
        """Verify full MCP server manifest contains exactly 36 tools with proper metadata."""
        manifest = get_full_mcp_manifest()
        assert isinstance(manifest, MCPManifestSchema)
        assert manifest.name == "horo-consultant-mcp"
        assert manifest.version == "1.0.0"
        assert len(manifest.tools) == 36

        tool_names = [t.name for t in manifest.tools]
        assert len(tool_names) == 36
        assert len(set(tool_names)) == 36  # No duplicate tool names

    def test_all_36_tools_in_registry(self):
        """Verify MCP_TOOL_REGISTRY contains all 36 tools across expected categories."""
        assert len(MCP_TOOL_REGISTRY) == 36
        categories = {spec["category"] for spec in MCP_TOOL_REGISTRY.values()}
        assert categories == {"calculation", "visualizer", "router", "debate"}

        calc_tools = [k for k, v in MCP_TOOL_REGISTRY.items() if v["category"] == "calculation"]
        vis_tools = [k for k, v in MCP_TOOL_REGISTRY.items() if v["category"] == "visualizer"]
        router_tools = [k for k, v in MCP_TOOL_REGISTRY.items() if v["category"] == "router"]
        debate_tools = [k for k, v in MCP_TOOL_REGISTRY.items() if v["category"] == "debate"]

        assert len(calc_tools) == 16
        assert len(vis_tools) == 18
        assert len(router_tools) == 1
        assert len(debate_tools) == 1

        for name, spec in MCP_TOOL_REGISTRY.items():
            assert "description" in spec and len(spec["description"]) > 10
            assert "param_model" in spec
            assert "result_model" in spec

    def test_rfc_json_schema_generation(self):
        """Verify every tool exposes valid JSON Schema parameters."""
        definitions = get_mcp_tool_definitions()
        assert len(definitions) == 36
        for tool_def in definitions:
            assert tool_def.name in MCP_TOOL_REGISTRY
            params = tool_def.parameters
            assert isinstance(params, dict)
            assert params.get("type") == "object"
            assert "properties" in params

    def test_pydantic_param_validation(self):
        """Test strict validation constraints on Pydantic parameter schemas."""
        # Valid BaZi params
        bazi_valid = BaZiCalculateParams(birth_datetime="1990-05-15 14:30:00", longitude=100.4930, utc_offset_hours=7.0)
        assert bazi_valid.longitude == 100.4930

        # Invalid BaZi longitude out of bounds
        with pytest.raises(ValidationError):
            BaZiCalculateParams(birth_datetime="1990-05-15 14:30:00", longitude=250.0)

        # Valid ZiWei params
        ziwei_valid = ZiWeiCalculateParams(year=1990, month=5, day=15, hour=14, gender="female")
        assert ziwei_valid.gender == "female"

        # Invalid ZiWei month
        with pytest.raises(ValidationError):
            ZiWeiCalculateParams(year=1990, month=13, day=15, hour=14)


# ==============================================================================
# 2. 16 Metaphysics Calculation Engines Dispatch Tests
# ==============================================================================

class TestMCPCalculationEnginesDispatch:
    """Test suite executing all 16 calculation engines via MCP dispatch."""

    @pytest.mark.parametrize(
        "tool_name,args,expected_keys",
        [
            # 1. BaZi Four Pillars
            ("bazi_calculate", {"birth_datetime": "1990-05-15 14:30:00", "longitude": 100.493, "utc_offset_hours": 7.0}, ["day_master", "pillars", "five_elements", "solar_time_info"]),
            # 2. Zi Wei Dou Shu
            ("ziwei_calculate", {"year": 1990, "month": 5, "day": 15, "hour": 14, "gender": "male"}, ["palaces", "si_hua", "ming_gong_branch"]),
            # 3. Qi Men Dun Jia
            ("qimen_calculate", {"year": 2026, "month": 8, "day": 7, "hour": 14}, ["solar_term", "dun_type", "ju_number", "palaces"]),
            # 4. Da Liu Ren
            ("liuren_calculate", {"day_stem": "甲", "day_branch": "子", "month_general": "正月", "hour_branch": "午"}, ["four_lessons", "three_transmissions", "heaven_plate"]),
            # 5. Tai Yi Shen Shu
            ("tai_yi_calculate", {"year": 2026, "month": 5, "day": 15, "hour": 14}, ["tai_yi_number", "accumulated_years", "star_palace"]),
            # 6. I Ching
            ("iching_calculate", {"day_stem": "甲", "seed": 42}, ["primary_hexagram", "transformed_hexagram", "six_lines"]),
            # 7. Liu Yao
            ("liu_yao_calculate", {"lines": [7, 8, 7, 9, 8, 7], "day_stem_idx": 0}, ["palace", "palace_element", "shi_line", "ying_line", "lines"]),
            # 8. Mei Hua Plum Blossom
            ("mei_hua_calculate", {"year": 2026, "month": 5, "day": 15, "hour": 14}, ["primary_hexagram", "body_function", "mutual_hexagram", "transformed_hexagram"]),
            # 9. Xuan Kong Flying Stars
            ("xuankong_calculate", {"facing_degree": 180.0, "period": 9}, ["period", "facing_degree", "sitting_mountain", "facing_mountain", "grid_palaces"]),
            # 10. San He Feng Shui
            ("san_he_calculate", {"sitting_degree": 0.0, "facing_degree": 180.0}, ["sitting_mountain", "facing_mountain", "san_he_formation", "water_method"]),
            # 11. Imperial Date Selection (Ze Ji)
            ("zeji_calculate", {"year_branch": "午", "month_branch": "申", "day_branch": "寅", "user_birth_branch": "子"}, ["duty_officer", "rating_stars", "overall_status", "is_year_breaker"]),
            # 12. Mian Xiang Physiognomy
            ("mian_xiang_analyze", {"features": {"face_shape": "round", "forehead": "broad", "eyes": "bright", "nose": "straight", "mouth": "defined", "ears": "thick", "chin": "firm", "age": 35}}, ["twelve_palaces", "five_officials", "overall_assessment"]),
            # 13. Thai Suriyayart & Vedic
            ("thaivedic_calculate", {"year": 1990, "month": 5, "day": 15, "hour": 14, "day_of_week": 2}, ["thai_lagna", "maha_thaksa", "vedic_nakshatra", "vimshottari_dasha"]),
            # 14. Western Tropical & Uranian
            ("western_calculate", {"year": 1990, "month": 5, "day": 15, "hour": 14}, ["planets_tropical", "uranian_tnps", "planetary_aspects"]),
            # 15. Satta-Lek Numerology & Chaldean
            ("numerology_calculate", {"text": "0812345678", "day_num": 2, "lunar_month": 6, "year_zodiac_num": 7}, ["satta_lek", "chaldean_score"]),
            # 16. Qi Zheng Si Yu
            ("qi_zheng_calculate", {"year": 2026, "month": 5, "day": 15, "hour": 14}, ["planets", "shadow_stars", "lunar_mansions"]),
        ],
    )
    def test_calculation_tool_dispatch(self, tool_name: str, args: Dict[str, Any], expected_keys: list[str]):
        """Execute calculation tool via MCP dispatch and assert structured dictionary output."""
        response = execute_mcp_tool_dispatch(tool_name, args)
        assert response.success is True, f"Tool {tool_name} failed: {response.error}"
        assert response.result is not None
        for key in expected_keys:
            assert key in response.result, f"Key '{key}' missing from result of {tool_name}"


# ==============================================================================
# 3. 18 Dynamic SVG Visualizers Dispatch Tests
# ==============================================================================

class TestMCPSVGVisualizersDispatch:
    """Test suite executing all 18 dynamic SVG visualizers via MCP dispatch."""

    @pytest.fixture(scope="class")
    @classmethod
    def chart_fixtures(cls) -> Dict[str, Any]:
        """Precompute sample calculation chart results for all visualizers."""
        bazi_c = HoroMCPTools.bazi_calculate("1990-05-15 14:30:00")
        ziwei_c = HoroMCPTools.ziwei_calculate(1990, 5, 15, 14, "male")
        qimen_c = HoroMCPTools.qimen_calculate(2026, 8, 7, 14)
        liuren_c = HoroMCPTools.liuren_calculate("甲", "子", "正月", "午")
        taiyi_c = HoroMCPTools.tai_yi_calculate(2026, 5, 15, 14)
        iching_c = HoroMCPTools.iching_calculate("甲", seed=42)
        liuyao_c = HoroMCPTools.liu_yao_calculate([7, 8, 7, 9, 8, 7], 0)
        meihua_c = HoroMCPTools.mei_hua_calculate(2026, 5, 15, 14)
        xuankong_c = HoroMCPTools.xuankong_calculate(180.0, 9)
        sanhe_c = HoroMCPTools.san_he_calculate(0.0, 180.0)
        zeji_c = HoroMCPTools.zeji_calculate("午", "申", "寅", "子")
        mianxiang_c = HoroMCPTools.mian_xiang_analyze({"face_shape": "round", "age": 35})
        thaivedic_c = HoroMCPTools.thaivedic_calculate(1990, 5, 15, 14, 2)
        western_c = HoroMCPTools.western_calculate(1990, 5, 15, 14)
        numerology_c = HoroMCPTools.numerology_calculate("0812345678", 2, 6, 7)
        qizheng_c = HoroMCPTools.qi_zheng_calculate(2026, 5, 15, 14)

        return {
            "bazi": bazi_c,
            "ziwei": ziwei_c,
            "qimen": qimen_c,
            "liuren": liuren_c,
            "taiyi": taiyi_c,
            "iching": iching_c,
            "liuyao": liuyao_c,
            "meihua": meihua_c,
            "xuankong": xuankong_c,
            "sanhe": sanhe_c,
            "zeji": zeji_c,
            "mianxiang": mianxiang_c,
            "thaivedic": thaivedic_c,
            "western": western_c,
            "numerology": numerology_c.get("satta_lek", numerology_c),
            "qizheng": qizheng_c,
            "zodiac_wheel": bazi_c,
            "multimodal_matrix": {"score": 0.88, "disciplines": {"bazi": "favorable", "ziwei": "affirm"}},
        }

    @pytest.mark.parametrize(
        "tool_name,fixture_key,expected_viewbox",
        [
            ("render_bazi_svg", "bazi", "0 0 800 600"),
            ("render_ziwei_svg", "ziwei", "0 0 800 800"),
            ("render_qimen_svg", "qimen", "0 0 600 600"),
            ("render_liuren_svg", "liuren", "0 0 600 400"),
            ("render_tai_yi_svg", "taiyi", "0 0 800 600"),
            ("render_iching_svg", "iching", "0 0 600 500"),
            ("render_liu_yao_svg", "liuyao", "0 0 800 600"),
            ("render_meihua_svg", "meihua", "0 0 800 600"),
            ("render_xuankong_svg", "xuankong", "0 0 600 600"),
            ("render_sanhe_svg", "sanhe", "0 0 800 600"),
            ("render_zeji_svg", "zeji", "0 0 600 350"),
            ("render_mianxiang_svg", "mianxiang", "0 0 800 600"),
            ("render_thaivedic_svg", "thaivedic", "0 0 600 450"),
            ("render_western_svg", "western", "0 0 600 450"),
            ("render_numerology_svg", "numerology", "0 0 760 530"),
            ("render_qizheng_svg", "qizheng", "0 0 800 600"),
            ("render_zodiac_wheel_svg", "zodiac_wheel", "0 0 600 600"),
            ("render_multimodal_matrix_svg", "multimodal_matrix", "0 0 800 600"),
        ],
    )
    def test_svg_visualizer_tool_dispatch(self, chart_fixtures: Dict[str, Any], tool_name: str, fixture_key: str, expected_viewbox: str):
        """Verify dynamic SVG rendering tool produces well-formed, valid XML with matching viewBox."""
        input_data = chart_fixtures[fixture_key]
        param_arg = "data" if tool_name == "render_multimodal_matrix_svg" else "chart"
        args = {param_arg: input_data, "lang": "th"}

        response = execute_mcp_tool_dispatch(tool_name, args)
        assert response.success is True, f"Visualizer tool {tool_name} failed: {response.error}"
        assert response.result is not None
        svg_content = response.result.get("svg_content", "")
        assert len(svg_content) > 100, f"SVG content for {tool_name} is too short"
        assert response.result.get("viewBox") == expected_viewbox

        # Strictly validate SVG XML well-formedness
        try:
            root = ET.fromstring(svg_content)
            assert root.tag.endswith("svg")
            assert "viewBox" in root.attrib
            assert root.attrib["viewBox"] == expected_viewbox
        except ET.ParseError as err:
            pytest.fail(f"Invalid SVG XML generated by {tool_name}: {err}")


# ==============================================================================
# 4. Question Focus Router & 8-Master Debate Dispatch Tests
# ==============================================================================

class TestMCPRouterAndDebateDispatch:
    """Test suite verifying Question Focus Router and 8-Master Debate MCP tools."""

    def test_question_focus_route_career_domain(self):
        """Test Question Focus Router on career question."""
        args = {"query": "ควรเปลี่ยนงานไปทำธุรกิจส่วนตัวปี 2026 ดีหรือไม่?", "language": "th"}
        res = execute_mcp_tool_dispatch("question_focus_route", args)
        assert res.success is True
        result = res.result or {}
        assert result["classified_domain"] == "career"
        assert result["confidence"] >= 0.5
        assert "bazi" in result["focus_directives"] or "guidance" in result["focus_directives"]

    def test_question_focus_route_finance_domain(self):
        """Test Question Focus Router on finance question."""
        args = {"query": "โชคลาภและการลงทุนในหุ้นปีนี้มีเกณฑ์กำไรไหม?", "language": "th"}
        res = execute_mcp_tool_dispatch("question_focus_route", args)
        assert res.success is True
        result = res.result or {}
        assert result["classified_domain"] == "finance"

    def test_question_focus_route_love_domain(self):
        """Test Question Focus Router on love relationship question."""
        args = {"query": "ความรักกับแฟนคนนี้จะสมพงษ์ได้แต่งงานกันไหม?", "language": "th"}
        res = execute_mcp_tool_dispatch("question_focus_route", args)
        assert res.success is True
        result = res.result or {}
        assert result["classified_domain"] == "love"

    def test_metaphysics_debate_execution(self):
        """Test 8-Master Peer Debate & Consensus Synthesis MCP tool."""
        args = {
            "query": "วิเคราะห์ดวงชะตาและฤกษ์ยามมงคลในการขยายธุรกิจ",
            "birth_datetime": "1990-05-15 14:30:00",
            "longitude": 100.4930,
            "utc_offset_hours": 7.0,
            "language": "th",
        }
        res = execute_mcp_tool_dispatch("metaphysics_debate", args)
        assert res.success is True
        result = res.result or {}
        assert result.get("status") == "DEBATE_COMPLETED"
        assert "consensus_matrix" in result
        matrix = result["consensus_matrix"]
        assert 0.0 <= matrix.get("consensus_score", 0.0) <= 1.0
        assert "domain_perspectives" in result
        perspectives = result["domain_perspectives"]
        assert len(perspectives) == 8
        assert "san_shi_master" in perspectives
        assert "ming_xue_master" in perspectives


# ==============================================================================
# 5. FastAPI Endpoints & HybridRouter Tests
# ==============================================================================

class TestFastAPIRouterAndEndpoints:
    """Test suite verifying FastAPI endpoints and HybridRouter behavior."""

    @pytest.fixture(scope="class")
    @classmethod
    def client(cls) -> TestClient:
        return TestClient(app)

    def test_hybrid_router_configuration(self):
        """Test HybridRouter instance and route fallback initialization."""
        router = HybridRouter(zero_cost_only=True)
        assert router.zero_cost_only is True
        routes = router._build_routes()
        assert isinstance(routes, list)
        # In zero_cost_only mode, paid endpoints must be excluded
        for r in routes:
            assert r["type"] not in ("vertex_ai", "openai")

    def test_fastapi_health_endpoints(self, client: TestClient):
        """Verify core health, API health, and metrics endpoints."""
        r_health = client.get("/health")
        assert r_health.status_code == 200
        assert r_health.json().get("status") == "ok"

        r_api_health = client.get("/api/health")
        assert r_api_health.status_code == 200

        r_metrics = client.get("/metrics")
        assert r_metrics.status_code == 200

    def test_fastapi_bazi_endpoint(self, client: TestClient):
        """Verify POST /api/v1/bazi/calculate endpoint."""
        payload = {
            "birth_datetime": "1990-05-15 14:30:00",
            "longitude": 100.4930,
            "utc_offset_hours": 7.0,
            "unknown_hour": False,
        }
        res = client.post("/api/v1/bazi/calculate", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "day_master" in data
        assert data["day_master"]["stem"] == "庚"
        assert "solar_time_info" in data
        assert "five_elements" in data

    def test_fastapi_astrology_get_endpoints(self, client: TestClient):
        """Verify GET calculation routes mounted under astrology router."""
        endpoints = [
            ("/api/v1/ziwei/calculate", {"year": 1990, "month": 5, "day": 15, "hour": 14, "gender": "male"}),
            ("/api/v1/qimen/calculate", {"year": 2026, "month": 8, "day": 7, "hour": 14}),
            ("/api/v1/liuren/calculate", {"day_stem": "甲", "day_branch": "子", "month_general": "正月", "hour_branch": "午"}),
            ("/api/v1/iching/calculate", {"day_stem": "甲", "seed": 42}),
            ("/api/v1/xuankong/calculate", {"facing_degree": 180.0, "period": 9}),
            ("/api/v1/zeji/calculate", {"year_branch": "午", "month_branch": "申", "day_branch": "寅", "user_birth_branch": "子"}),
            ("/api/v1/thaivedic/calculate", {"year": 1990, "month": 5, "day": 15, "hour": 14, "day_of_week": 2}),
            ("/api/v1/western/calculate", {"year": 1990, "month": 5, "day": 15, "hour": 14}),
            ("/api/v1/numerology/calculate", {"text": "0812345678", "day_num": 2, "lunar_month": 6, "year_zodiac_num": 7}),
        ]

        for path, params in endpoints:
            res = client.get(path, params=params)
            assert res.status_code == 200, f"Endpoint {path} failed with {res.status_code}: {res.text}"

    def test_fastapi_metaphysical_debate_endpoint(self, client: TestClient):
        """Verify POST /api/v1/metaphysical/debate endpoint."""
        payload = {
            "birth_datetime": "1990-05-15 14:30:00",
            "longitude": 100.4930,
            "utc_offset_hours": 7.0,
            "query": "วิเคราะห์ดวงชะตาและฤกษ์ยามมงคลในการขยายธุรกิจ",
            "language": "th",
        }
        res = client.post("/api/v1/metaphysical/debate", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data.get("status") == "DEBATE_COMPLETED"
        assert "consensus_matrix" in data
        assert "domain_perspectives" in data
