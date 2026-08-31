"""
project/mcp_server.py — Model Context Protocol (MCP) Unified Server
====================================================================
Unified Computational Metaphysics MCP Server for thClaws (Rust Agent Harness),
AGY Subagents, and Claude Desktop.

Exposes all 36 MCP Tools:
  - 16 Calculation Engines (San Shi, Ming Xue, Bu Shi, Xiang Xue, Ze Ji, Thai-Vedic, Western, Numerology)
  - 18 Dynamic SVG Visualizers (Dark-Mode Glassmorphism Charts, Astrolabes, Matrix)
  - 1 Question Focus Router (6-Domain Alignment & Direct Answering Directive)
  - 1 8-Master Debate & Consensus Synthesis Engine (Five Elements Anchor)
  - Auxiliary Tools: rag_search, bazi_interpret, bazi_validate

Conforms to MCP RFC Specification (JSON-RPC 2.0 & Stdio Transport).
Pure ASCII logging standard ([OK], [ERROR], [INFO], [WARNING]).
"""

from __future__ import annotations

import json
import logging
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


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
from project.core.question_focus_router import question_focus_router
from project.core.san_he_engine import SanHeEngine
from project.core.svg_generator import (
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
from project.rag.vector_store import get_vector_store
from project.schemas.mcp_tools_v1 import (
    MCP_TOOL_REGISTRY,
    MCPCallToolRequest,
    MCPCallToolResponse,
    MCPManifestSchema,
    MCPToolDefinition,
    get_full_mcp_manifest,
)
from project.validator import PredictionValidator

log = logging.getLogger("mcp_server")

# Engine singletons (lightweight pure math computation engines)
bazi_engine = BaZiEngine()
ziwei_engine = ZiWeiEngine()
qimen_engine = QiMenEngine()
liuren_engine = LiuRenEngine()
taiyi_engine = TaiYiEngine()
iching_engine = IChingEngine()
liuyao_engine = LiuYaoEngine()
meihua_engine = MeiHuaEngine()
xuankong_engine = XuanKongEngine()
sanhe_engine = SanHeEngine()
zeji_engine = ZeJiEngine()
mianxiang_engine = MianXiangEngine()
thaivedic_engine = ThaiVedicEngine()
western_engine = WesternUranianEngine()
numerology_engine = NumerologyEngine()
qizheng_engine = QiZhengSiYuEngine()

_debate_engine_instance = None
_vector_store_instance = None
_validator_instance = None
_router_instance = None


def _get_debate_engine() -> MetaphysicsDebateEngine:
    global _debate_engine_instance
    if _debate_engine_instance is None:
        _debate_engine_instance = MetaphysicsDebateEngine()
    return _debate_engine_instance


def _get_vector_store():
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = get_vector_store()
    return _vector_store_instance


def _get_validator() -> PredictionValidator:
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = PredictionValidator()
    return _validator_instance


def _get_router() -> "HybridRouter":
    global _router_instance
    if _router_instance is None:
        from project.api_router import HybridRouter
        _router_instance = HybridRouter()
    return _router_instance


def __getattr__(name: str) -> Any:
    if name == "router":
        return _get_router()
    if name == "validator":
        return _get_validator()
    if name == "vector_store":
        return _get_vector_store()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


CHARTS_DIR = ROOT / "project" / "static" / "charts"


def _format_svg_result(
    discipline: str,
    function_name: str,
    svg_content: str,
    visual_components: list[str],
    save_to_disk: bool = False,
    output_filename: str | None = None,
) -> dict[str, Any]:
    """Helper to structure standardized RenderSVGResult dict."""
    vb_match = re.search(r'viewBox="([^"]+)"', svg_content)
    viewBox = vb_match.group(1) if vb_match else "0 0 800 600"
    parts = viewBox.split()
    aspect = "4:3"
    if len(parts) == 4:
        try:
            w, h = float(parts[2]), float(parts[3])
            if abs(w - h) < 1e-3:
                aspect = "1:1"
            elif abs(w / h - 4 / 3) < 0.05:
                aspect = "4:3"
            elif abs(w / h - 3 / 2) < 0.05:
                aspect = "3:2"
            elif abs(w / h - 6 / 5) < 0.05:
                aspect = "6:5"
            elif abs(w / h - 12 / 7) < 0.05:
                aspect = "12:7"
            elif abs(w / h - 76 / 53) < 0.05:
                aspect = "76:53"
            else:
                aspect = f"{int(w)}:{int(h)}"
        except Exception:
            aspect = "4:3"

    svg_file = None
    if save_to_disk:
        CHARTS_DIR.mkdir(parents=True, exist_ok=True)
        fname = output_filename or f"{discipline.lower().replace(' ', '_')}_chart.svg"
        out_path = CHARTS_DIR / fname
        out_path.write_text(svg_content, encoding="utf-8")
        try:
            svg_file = str(out_path.relative_to(ROOT))
        except ValueError:
            svg_file = str(out_path)

    return {
        "discipline": discipline,
        "function_name": function_name,
        "svg_content": svg_content,
        "svg_length": len(svg_content),
        "viewBox": viewBox,
        "aspect_ratio": aspect,
        "visual_components": visual_components,
        "svg_file": svg_file,
        "svg_snippet": svg_content[:200] + "...",
    }


class HoroMCPTools:
    """MCP Tool Definitions for thClaws, AGY Subagents, and Claude Desktop."""

    # ==========================================================================
    # 1. 16 Metaphysics Calculation Tools
    # ==========================================================================

    @staticmethod
    def bazi_calculate(
        birth_datetime: str = "1990-05-15 14:30:00",
        longitude: float = 100.4930,
        utc_offset_hours: float = 7.0,
        unknown_hour: bool = False,
    ) -> dict[str, Any]:
        """Compute BaZi 4 Pillars chart with True Solar Time (TST) adjustment."""
        try:
            dt = datetime.strptime(birth_datetime, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            dt = datetime.fromisoformat(birth_datetime.replace("Z", "+00:00")).replace(tzinfo=None)
        res = bazi_engine.calculate(
            dt=dt,
            longitude=longitude,
            utc_offset_hours=utc_offset_hours,
            unknown_hour=unknown_hour,
        )
        return dict(res)

    @staticmethod
    def ziwei_calculate(
        year: int = 1990,
        month: int = 5,
        day: int = 15,
        hour: int = 14,
        gender: str = "male",
    ) -> dict[str, Any]:
        """Compute Zi Wei Dou Shu chart (12 Palaces, 14 Stars, Si Hua)."""
        res = ziwei_engine.calculate_chart(year, month, day, hour, gender)
        return dict(res)

    @staticmethod
    def qimen_calculate(
        year: int = 2026,
        month: int = 8,
        day: int = 7,
        hour: int = 14,
    ) -> dict[str, Any]:
        """Compute Qi Men Dun Jia 4-Plate chart."""
        res = qimen_engine.calculate_chart(year, month, day, hour)
        return dict(res)

    @staticmethod
    def liuren_calculate(
        day_stem: str = "甲",
        day_branch: str = "子",
        month_general: str = "正月",
        hour_branch: str = "午",
    ) -> dict[str, Any]:
        """Compute Da Liu Ren 3-Transmission & 4-Lesson chart."""
        res = liuren_engine.calculate_chart(day_stem, day_branch, month_general, hour_branch)
        return dict(res)

    @staticmethod
    def tai_yi_calculate(
        year: int = 2026,
        month: int = 5,
        day: int = 15,
        hour: int = 14,
    ) -> dict[str, Any]:
        """Compute Tai Yi Shen Shu 16-path star and strategic assessment."""
        res = taiyi_engine.calculate(year, month, day, hour)
        return dict(res.chart_data if hasattr(res, "chart_data") else res)

    @staticmethod
    def iching_calculate(
        day_stem: str = "甲",
        seed: int | None = None,
        lines: list[int] | None = None,
    ) -> dict[str, Any]:
        """Cast I Ching Hexagram and compute Liu Yao setup."""
        if lines is None:
            lines = iching_engine.cast_lines(seed=seed)
        res = iching_engine.calculate_liu_yao(day_stem, lines)
        return dict(res)

    @staticmethod
    def liu_yao_calculate(
        lines: list[int] = [7, 7, 7, 7, 7, 7],
        day_stem_idx: int = 0,
    ) -> dict[str, Any]:
        """Compute Liu Yao 6-lines divination with Na Jia and Five Relatives."""
        res = liuyao_engine.calculate(lines, day_stem_idx=day_stem_idx)
        return dict(res.chart_data if hasattr(res, "chart_data") else res)

    @staticmethod
    def mei_hua_calculate(
        year: int = 2026,
        month: int = 5,
        day: int = 15,
        hour: int = 14,
        num1: int | None = None,
        num2: int | None = None,
        num3: int | None = None,
    ) -> dict[str, Any]:
        """Compute Mei Hua Plum Blossom Numerology Body/Function analysis."""
        if num1 is not None and num2 is not None:
            res = meihua_engine.calculate_from_numbers(num1, num2, num3)
        else:
            res = meihua_engine.calculate(year, month, day, hour)
        return dict(res.chart_data if hasattr(res, "chart_data") else res)

    @staticmethod
    def xuankong_calculate(
        facing_degree: float = 180.0,
        period: int = 9,
    ) -> dict[str, Any]:
        """Compute Xuan Kong Flying Stars 9-Grid chart."""
        res = xuankong_engine.calculate_chart(facing_degree, period)
        return dict(res)

    @staticmethod
    def san_he_calculate(
        sitting_degree: float = 0.0,
        facing_degree: float = 180.0,
        water_incoming_degree: float | None = None,
        water_outgoing_degree: float | None = None,
    ) -> dict[str, Any]:
        """Compute San He 12 Life Stages Water Method and 24 Mountains."""
        res = sanhe_engine.calculate(
            sitting_degree=sitting_degree,
            facing_degree=facing_degree,
            water_entry_degree=water_incoming_degree,
            water_exit_degree=water_outgoing_degree,
        )
        return dict(res.chart_data if hasattr(res, "chart_data") else res)

    @staticmethod
    def zeji_calculate(
        year_branch: str = "午",
        month_branch: str = "申",
        day_branch: str = "寅",
        user_birth_branch: str | None = "子",
        activity: str | None = None,
    ) -> dict[str, Any]:
        """Compute Date Selection suitability via 12 Duty Officers."""
        res = zeji_engine.check_suitability(
            year_branch=year_branch,
            month_branch=month_branch,
            day_branch=day_branch,
            user_birth_branch=user_birth_branch,
        )
        data = dict(res)
        if activity:
            act_dict = data.get("activities", {})
            data["selected_activity"] = activity
            data["selected_activity_status"] = act_dict.get(activity, "N/A")
        return data

    @staticmethod
    def mian_xiang_analyze(
        features: dict[str, Any],
    ) -> dict[str, Any]:
        """Analyze 12 Face Palaces and 5 Facial Officials using physiognomy rules."""
        res = mianxiang_engine.analyze(features)
        return dict(res.chart_data if hasattr(res, "chart_data") else res)

    @staticmethod
    def thaivedic_calculate(
        year: int = 1990,
        month: int = 5,
        day: int = 15,
        hour: int = 14,
        day_of_week: int = 2,
        minute: int = 30,
    ) -> dict[str, Any]:
        """Compute Thai Suriyayart 10 Lagna, Maha Thaksa & Vimshottari Dasha."""
        res = thaivedic_engine.calculate_chart(
            year=year,
            month=month,
            day=day,
            hour=hour,
            day_of_week=day_of_week,
        )
        return dict(res)

    @staticmethod
    def western_calculate(
        year: int = 1990,
        month: int = 5,
        day: int = 15,
        hour: int = 14,
        minute: int = 30,
        latitude: float = 13.7563,
        longitude: float = 100.5018,
    ) -> dict[str, Any]:
        """Compute Western Tropical Aspects, Uranian 8 TNPs & Midpoints."""
        res = western_engine.calculate_chart(year, month, day, hour)
        return dict(res)

    @staticmethod
    def numerology_calculate(
        text: str = "0812345678",
        day_num: int = 2,
        lunar_month: int = 6,
        year_zodiac_num: int = 7,
    ) -> dict[str, Any]:
        """Compute Satta-Lek 7-Base 4-Row Matrix & Chaldean Numerology Scoring."""
        satta_lek = numerology_engine.calculate_satta_lek(day_num, lunar_month, year_zodiac_num)
        score = numerology_engine.score_text_or_number(text)
        return {"satta_lek": satta_lek, "chaldean_score": score, "matrix_7_base": satta_lek}

    @staticmethod
    def qi_zheng_calculate(
        year: int = 2026,
        month: int = 5,
        day: int = 15,
        hour: int = 14,
    ) -> dict[str, Any]:
        """Compute Qi Zheng Si Yu 7 Governors and 4 Shadow Stars on 28 Lunar Mansions."""
        res = qizheng_engine.calculate(year, month, day, hour)
        return dict(res.chart_data if hasattr(res, "chart_data") else res)

    # ==========================================================================
    # 2. 18 Dynamic SVG Visualizer Tools
    # ==========================================================================

    @staticmethod
    def render_bazi_svg(
        chart: dict[str, Any] | str | None = None,
        birth_datetime: str | None = None,
        longitude: float = 100.4930,
        utc_offset_hours: float = 7.0,
        title: str | None = None,
        lang: str = "th",
        save_to_disk: bool = False,
        output_filename: str | None = None,
    ) -> dict[str, Any]:
        """Generate BaZi 4 Pillars dynamic SVG chart."""
        if isinstance(chart, str):
            birth_datetime = chart
            chart = None
        if chart is None and birth_datetime is not None:
            chart = HoroMCPTools.bazi_calculate(birth_datetime, longitude, utc_offset_hours)
            save_to_disk = True
            if not output_filename:
                output_filename = "bazi_chart.svg"
        elif chart is None:
            chart = HoroMCPTools.bazi_calculate("1990-05-15 14:30:00", longitude, utc_offset_hours)

        svg_content = generate_bazi_svg(chart, title=title, lang=lang)
        return _format_svg_result(
            discipline="BaZi Four Pillars",
            function_name="generate_bazi_svg",
            svg_content=svg_content,
            visual_components=["Header", "FourPillarsGrid", "FiveElementsBar", "TenGodsBadge"],
            save_to_disk=save_to_disk,
            output_filename=output_filename or "bazi_chart.svg" if save_to_disk else None,
        )

    @staticmethod
    def render_zodiac_wheel_svg(
        chart: dict[str, Any] | str | None = None,
        birth_datetime: str | None = None,
        longitude: float = 100.4930,
        utc_offset_hours: float = 7.0,
        title: str | None = None,
        lang: str = "th",
        save_to_disk: bool = False,
        output_filename: str | None = None,
    ) -> dict[str, Any]:
        """Generate 12 Zodiac Houses Radial Astrolabe SVG chart."""
        if isinstance(chart, str):
            birth_datetime = chart
            chart = None
        if chart is None and birth_datetime is not None:
            chart = HoroMCPTools.bazi_calculate(birth_datetime, longitude, utc_offset_hours)
            save_to_disk = True
            if not output_filename:
                output_filename = "zodiac_wheel.svg"
        elif chart is None:
            chart = HoroMCPTools.bazi_calculate("1990-05-15 14:30:00", longitude, utc_offset_hours)

        svg_content = generate_zodiac_wheel_svg(chart, title=title, lang=lang)
        return _format_svg_result(
            discipline="12 Zodiac Houses Radial Astrolabe",
            function_name="generate_zodiac_wheel_svg",
            svg_content=svg_content,
            visual_components=["Header", "12ZodiacHousesWheel", "AspectHarmonies"],
            save_to_disk=save_to_disk,
            output_filename=output_filename or "zodiac_wheel.svg" if save_to_disk else None,
        )

    render_zodiac_svg = render_zodiac_wheel_svg

    @staticmethod
    def render_ziwei_svg(
        chart: dict[str, Any] | None = None,
        title: str | None = None,
        lang: str = "th",
        save_to_disk: bool = False,
        output_filename: str | None = None,
    ) -> dict[str, Any]:
        """Generate Zi Wei Dou Shu 12-Palace dynamic SVG chart."""
        if chart is None:
            chart = HoroMCPTools.ziwei_calculate()
        svg_content = generate_ziwei_svg(chart, title=title, lang=lang)
        return _format_svg_result(
            discipline="Zi Wei Dou Shu",
            function_name="generate_ziwei_svg",
            svg_content=svg_content,
            visual_components=["Header", "CenterInfoGrid", "12PalacesGrid", "SiHuaBadges"],
            save_to_disk=save_to_disk,
            output_filename=output_filename or "ziwei_chart.svg" if save_to_disk else None,
        )

    @staticmethod
    def render_qimen_svg(
        chart: dict[str, Any] | None = None,
        title: str | None = None,
        lang: str = "th",
        save_to_disk: bool = False,
        output_filename: str | None = None,
    ) -> dict[str, Any]:
        """Generate Qi Men Dun Jia 9-Palace matrix dynamic SVG chart."""
        if chart is None:
            chart = HoroMCPTools.qimen_calculate()
        svg_content = generate_qimen_svg(chart, title=title, lang=lang)
        return _format_svg_result(
            discipline="Qi Men Dun Jia",
            function_name="generate_qimen_svg",
            svg_content=svg_content,
            visual_components=["Header", "3x3PalacesGrid", "DoorsStarsDeitiesPlates", "SolarTermJuInfo"],
            save_to_disk=save_to_disk,
            output_filename=output_filename or "qimen_chart.svg" if save_to_disk else None,
        )

    @staticmethod
    def render_liuren_svg(
        chart: dict[str, Any] | None = None,
        title: str | None = None,
        lang: str = "th",
        save_to_disk: bool = False,
        output_filename: str | None = None,
    ) -> dict[str, Any]:
        """Generate Da Liu Ren 3-Transmission & 4-Lesson SVG chart."""
        if chart is None:
            chart = HoroMCPTools.liuren_calculate()
        svg_content = generate_liuren_svg(chart, title=title, lang=lang)
        return _format_svg_result(
            discipline="Da Liu Ren",
            function_name="generate_liuren_svg",
            svg_content=svg_content,
            visual_components=["Header", "HeavenPlateGrid", "FourLessons", "ThreeTransmissions"],
            save_to_disk=save_to_disk,
            output_filename=output_filename or "liuren_chart.svg" if save_to_disk else None,
        )

    @staticmethod
    def render_tai_yi_svg(
        chart: dict[str, Any] | None = None,
        title: str | None = None,
        lang: str = "th",
        save_to_disk: bool = False,
        output_filename: str | None = None,
    ) -> dict[str, Any]:
        """Generate Tai Yi Shen Shu 16-Path star palace SVG chart."""
        if chart is None:
            chart = HoroMCPTools.tai_yi_calculate()
        svg_content = generate_tai_yi_svg(chart, title=title, lang=lang)
        return _format_svg_result(
            discipline="Tai Yi Shen Shu",
            function_name="generate_tai_yi_svg",
            svg_content=svg_content,
            visual_components=["Header", "16PathStarPalaces", "TaiYiNumberInfo", "BattleStrategyMatrix"],
            save_to_disk=save_to_disk,
            output_filename=output_filename or "taiyi_chart.svg" if save_to_disk else None,
        )

    @staticmethod
    def render_iching_svg(
        chart: dict[str, Any] | None = None,
        title: str | None = None,
        lang: str = "th",
        save_to_disk: bool = False,
        output_filename: str | None = None,
    ) -> dict[str, Any]:
        """Generate I Ching 64-Hexagram & changing lines SVG chart."""
        if chart is None:
            chart = HoroMCPTools.iching_calculate()
        svg_content = generate_iching_svg(chart, title=title, lang=lang)
        return _format_svg_result(
            discipline="I Ching Divination",
            function_name="generate_iching_svg",
            svg_content=svg_content,
            visual_components=["Header", "PrimaryHexagram", "TransformedHexagram", "ChangingLines"],
            save_to_disk=save_to_disk,
            output_filename=output_filename or "iching_chart.svg" if save_to_disk else None,
        )

    @staticmethod
    def render_liu_yao_svg(
        chart: dict[str, Any] | None = None,
        title: str | None = None,
        lang: str = "th",
        save_to_disk: bool = False,
        output_filename: str | None = None,
    ) -> dict[str, Any]:
        """Generate Liu Yao Na Jia 6-Line & 6 Spirits SVG chart."""
        if chart is None:
            chart = HoroMCPTools.liu_yao_calculate()
        svg_content = generate_liu_yao_svg(chart, title=title, lang=lang)
        return _format_svg_result(
            discipline="Liu Yao Na Jia",
            function_name="generate_liu_yao_svg",
            svg_content=svg_content,
            visual_components=["Header", "SixLinesGrid", "NaJiaStemsBranches", "SixSpirits", "ShiYingLines"],
            save_to_disk=save_to_disk,
            output_filename=output_filename or "liuyao_chart.svg" if save_to_disk else None,
        )

    @staticmethod
    def render_meihua_svg(
        chart: dict[str, Any] | None = None,
        title: str | None = None,
        lang: str = "th",
        save_to_disk: bool = False,
        output_filename: str | None = None,
    ) -> dict[str, Any]:
        """Generate Mei Hua Plum Blossom Ti/Yong Gua dynamic flow SVG chart."""
        if chart is None:
            chart = HoroMCPTools.mei_hua_calculate()
        svg_content = generate_meihua_svg(chart, title=title, lang=lang)
        return _format_svg_result(
            discipline="Mei Hua Plum Blossom",
            function_name="generate_meihua_svg",
            svg_content=svg_content,
            visual_components=["Header", "TiYongInteraction", "MutualHexagram", "TransformedHexagram"],
            save_to_disk=save_to_disk,
            output_filename=output_filename or "meihua_chart.svg" if save_to_disk else None,
        )

    @staticmethod
    def render_xuankong_svg(
        chart: dict[str, Any] | None = None,
        title: str | None = None,
        lang: str = "th",
        save_to_disk: bool = False,
        output_filename: str | None = None,
    ) -> dict[str, Any]:
        """Generate Xuan Kong Flying Stars Period 9 9-Grid SVG chart."""
        if chart is None:
            chart = HoroMCPTools.xuankong_calculate()
        svg_content = generate_xuankong_svg(chart, title=title, lang=lang)
        return _format_svg_result(
            discipline="Xuan Kong Flying Stars",
            function_name="generate_xuankong_svg",
            svg_content=svg_content,
            visual_components=["Header", "9PalacesGrid", "SittingFacingStars", "Period9Base"],
            save_to_disk=save_to_disk,
            output_filename=output_filename or "xuankong_chart.svg" if save_to_disk else None,
        )

    @staticmethod
    def render_sanhe_svg(
        chart: dict[str, Any] | None = None,
        title: str | None = None,
        lang: str = "th",
        save_to_disk: bool = False,
        output_filename: str | None = None,
    ) -> dict[str, Any]:
        """Generate San He 24-Mountain & 12 Life Stages Water SVG chart."""
        if chart is None:
            chart = HoroMCPTools.san_he_calculate()
        svg_content = generate_sanhe_svg(chart, title=title, lang=lang)
        return _format_svg_result(
            discipline="San He Feng Shui",
            function_name="generate_sanhe_svg",
            svg_content=svg_content,
            visual_components=["Header", "24MountainsCompass", "12LifeStagesFlow", "HarmonyStatus"],
            save_to_disk=save_to_disk,
            output_filename=output_filename or "sanhe_chart.svg" if save_to_disk else None,
        )

    @staticmethod
    def render_zeji_svg(
        chart: dict[str, Any] | None = None,
        title: str | None = None,
        lang: str = "th",
        save_to_disk: bool = False,
        output_filename: str | None = None,
    ) -> dict[str, Any]:
        """Generate Imperial Date Selection 12 Duty Officers SVG card."""
        if chart is None:
            chart = HoroMCPTools.zeji_calculate()
        svg_content = generate_zeji_svg(chart, title=title, lang=lang)
        return _format_svg_result(
            discipline="Imperial Date Selection",
            function_name="generate_zeji_svg",
            svg_content=svg_content,
            visual_components=["Header", "DutyOfficerCard", "StarRatingStars", "BreakersStatus"],
            save_to_disk=save_to_disk,
            output_filename=output_filename or "zeji_chart.svg" if save_to_disk else None,
        )

    @staticmethod
    def render_mianxiang_svg(
        chart: dict[str, Any] | None = None,
        title: str | None = None,
        lang: str = "th",
        save_to_disk: bool = False,
        output_filename: str | None = None,
    ) -> dict[str, Any]:
        """Generate Mian Xiang 12 Palaces & 5 Officials SVG chart."""
        if chart is None:
            chart = HoroMCPTools.mian_xiang_analyze({"face_shape": "round", "forehead": "high_broad"})
        svg_content = generate_mianxiang_svg(chart, title=title, lang=lang)
        return _format_svg_result(
            discipline="Mian Xiang Physiognomy",
            function_name="generate_mianxiang_svg",
            svg_content=svg_content,
            visual_components=["Header", "12PalacesFacialMap", "5OfficialsAssessment", "Age100Flow"],
            save_to_disk=save_to_disk,
            output_filename=output_filename or "mianxiang_chart.svg" if save_to_disk else None,
        )

    @staticmethod
    def render_thaivedic_svg(
        chart: dict[str, Any] | None = None,
        title: str | None = None,
        lang: str = "th",
        save_to_disk: bool = False,
        output_filename: str | None = None,
    ) -> dict[str, Any]:
        """Generate Thai Suriyayart & 27 Nakshatras SVG chart."""
        if chart is None:
            chart = HoroMCPTools.thaivedic_calculate()
        svg_content = generate_thaivedic_svg(chart, title=title, lang=lang)
        return _format_svg_result(
            discipline="Thai & Vedic Suriyayart",
            function_name="generate_thaivedic_svg",
            svg_content=svg_content,
            visual_components=["Header", "12RashiLagnaWheel", "8MahaThaksaGrid", "27Nakshatras"],
            save_to_disk=save_to_disk,
            output_filename=output_filename or "thaivedic_chart.svg" if save_to_disk else None,
        )

    @staticmethod
    def render_western_svg(
        chart: dict[str, Any] | None = None,
        title: str | None = None,
        lang: str = "th",
        save_to_disk: bool = False,
        output_filename: str | None = None,
    ) -> dict[str, Any]:
        """Generate Western Tropical & Uranian TNPs SVG chart."""
        if chart is None:
            chart = HoroMCPTools.western_calculate()
        svg_content = generate_western_svg(chart, title=title, lang=lang)
        return _format_svg_result(
            discipline="Western & Uranian Astrology",
            function_name="generate_western_svg",
            svg_content=svg_content,
            visual_components=["Header", "TropicalPlanetsWheel", "8UranianTNPs", "MidpointAxis"],
            save_to_disk=save_to_disk,
            output_filename=output_filename or "western_chart.svg" if save_to_disk else None,
        )

    @staticmethod
    def render_numerology_svg(
        chart: dict[str, Any] | None = None,
        title: str | None = None,
        lang: str = "th",
        save_to_disk: bool = False,
        output_filename: str | None = None,
    ) -> dict[str, Any]:
        """Generate Satta-Lek 7-Base 4-Row matrix SVG card."""
        if chart is None:
            chart = HoroMCPTools.numerology_calculate()
        svg_content = generate_numerology_svg(chart, title=title, lang=lang)
        return _format_svg_result(
            discipline="Satta-Lek Numerology",
            function_name="generate_numerology_svg",
            svg_content=svg_content,
            visual_components=["Header", "SattaLek4RowMatrix", "BaseSumStats", "ChaldeanScoreCard"],
            save_to_disk=save_to_disk,
            output_filename=output_filename or "numerology_chart.svg" if save_to_disk else None,
        )

    @staticmethod
    def render_qizheng_svg(
        chart: dict[str, Any] | None = None,
        title: str | None = None,
        lang: str = "th",
        save_to_disk: bool = False,
        output_filename: str | None = None,
    ) -> dict[str, Any]:
        """Generate Qi Zheng Si Yu 7 Governors & 28 Mansions SVG chart."""
        if chart is None:
            chart = HoroMCPTools.qi_zheng_calculate()
        svg_content = generate_qizheng_svg(chart, title=title, lang=lang)
        return _format_svg_result(
            discipline="Qi Zheng Si Yu",
            function_name="generate_qizheng_svg",
            svg_content=svg_content,
            visual_components=["Header", "7GovernorsGrid", "4ShadowStars", "28LunarMansions"],
            save_to_disk=save_to_disk,
            output_filename=output_filename or "qizheng_chart.svg" if save_to_disk else None,
        )

    @staticmethod
    def render_multimodal_matrix_svg(
        data: dict[str, Any] | None = None,
        chart: dict[str, Any] | None = None,
        title: str | None = None,
        lang: str = "th",
        save_to_disk: bool = False,
        output_filename: str | None = None,
    ) -> dict[str, Any]:
        """Generate 16-Discipline Multimodal Consensus Matrix SVG."""
        input_data = data or chart or {"consensus_score": 0.85, "favorable_elements": ["Metal", "Water"]}
        svg_content = generate_multimodal_matrix_svg(input_data, title=title, lang=lang)
        return _format_svg_result(
            discipline="Multimodal Metaphysics Matrix",
            function_name="generate_multimodal_matrix_svg",
            svg_content=svg_content,
            visual_components=["Header", "16DisciplineRadarMatrix", "ConsensusScoreBadge", "HarmonizedSummary"],
            save_to_disk=save_to_disk,
            output_filename=output_filename or "multimodal_matrix.svg" if save_to_disk else None,
        )

    # ==========================================================================
    # 3. Question Focus Router Tool
    # ==========================================================================

    @staticmethod
    def question_focus_route(
        query: str,
        context: dict[str, Any] | None = None,
        language: str = "th",
    ) -> dict[str, Any]:
        """Classify question into 6 domains and generate engine focus directives."""
        domain, confidence = question_focus_router.classify_question(query)
        guide = question_focus_router.get_analysis_guide(domain)
        citations = question_focus_router.get_citation_references(domain)

        domain_names = {
            "career": "การงาน/ธุรกิจ (Career & Business)",
            "finance": "การเงิน/โชคลาภ (Finance & Wealth)",
            "love": "ความรัก/คู่ครอง (Love & Marriage)",
            "health": "สุขภาพ/อายุขัย (Health & Longevity)",
            "family": "ครอบครัว/บุตร (Family & Offspring)",
            "timing": "วงจรโชค/ฤกษ์ยาม (Timing & Auspicious Dates)",
            "general": "ภาพรวมดวงชะตา (General Comprehensive Reading)",
        }

        rec_engines = {
            "career": ["bazi_calculate", "ziwei_calculate", "qimen_calculate"],
            "finance": ["bazi_calculate", "ziwei_calculate", "western_calculate"],
            "love": ["bazi_calculate", "ziwei_calculate", "iching_calculate"],
            "health": ["bazi_calculate", "ziwei_calculate", "mian_xiang_analyze"],
            "family": ["bazi_calculate", "ziwei_calculate", "numerology_calculate"],
            "timing": ["zeji_calculate", "qimen_calculate", "xuankong_calculate"],
            "general": ["bazi_calculate", "ziwei_calculate", "metaphysics_debate"],
        }.get(domain, ["bazi_calculate", "ziwei_calculate"])

        return {
            "classified_domain": domain,
            "domain_display_name": domain_names.get(domain, domain),
            "confidence": confidence,
            "matched_keywords": [],
            "domain_scores": {domain: confidence},
            "recommended_engines": rec_engines,
            "focus_directives": guide,
            "analysis_guide": guide.get("guidance", "Comprehensive astrological synthesis"),
            "canonical_citations": citations,
        }

    # ==========================================================================
    # 4. 8-Master Debate & Consensus Synthesis Tool
    # ==========================================================================

    @staticmethod
    def metaphysics_debate(
        query: str = "วิเคราะห์ดวงชะตาและฤกษ์ยามมงคลในการขยายธุรกิจ",
        birth_datetime: str = "1990-05-15 14:30:00",
        longitude: float = 100.4930,
        utc_offset_hours: float = 7.0,
        unknown_hour: bool = False,
        language: str = "th",
        force_hitl: bool = False,
        active_masters: list[str] | None = None,
    ) -> dict[str, Any]:
        """Execute peer debate across 8 Metaphysics Masters and calculate consensus."""
        input_ctx = {
            "query": query,
            "birth_datetime": birth_datetime,
            "longitude": longitude,
            "utc_offset_hours": utc_offset_hours,
            "unknown_hour": unknown_hour,
            "language": language,
            "force_hitl": force_hitl,
            "active_masters": active_masters,
        }
        return _get_debate_engine().run_peer_debate(input_ctx)

    # ==========================================================================
    # 5. Auxiliary RAG Search & LLM Interpretation Tools
    # ==========================================================================

    @staticmethod
    def rag_search(query: str, top_k: int = 3) -> dict[str, Any]:
        """Search classical BaZi texts & Thai astrology books in FAISS vector store."""
        vs = _get_vector_store()
        results = vs.search(query, top_k=top_k)
        total_count = len(getattr(vs, "_chunks", []))
        return {"query": query, "matches": results, "total_vectors": total_count}

    @staticmethod
    def bazi_interpret(
        birth_datetime: str = "1990-05-15 14:30:00",
        longitude: float = 100.4930,
        utc_offset_hours: float = 7.0,
        query: str = "",
    ) -> dict[str, Any]:
        """Generate full AI interpretation using Local Ollama or Cloud fallback."""
        chart = HoroMCPTools.bazi_calculate(birth_datetime, longitude, utc_offset_hours)
        dm = chart.get("day_master", {})
        fe = chart.get("five_elements", {}).get("percentages", {})
        prompt = (
            f"BaZi Chart for birth: {birth_datetime} "
            f"Day Master: {dm.get('stem', '')} ({dm.get('element', '')}, {dm.get('polarity', '')})\n"
            f"Five Elements: {json.dumps(fe, ensure_ascii=False)}\n"
            f"User Query: {query or 'Provide a comprehensive life reading.'}"
        )
        res = _get_router().generate(
            prompt=prompt,
            system_instruction="You are a master BaZi consultant. Provide insightful reading.",
        )
        return {"chart": chart, "interpretation": res.get("text"), "route": res.get("route")}

    @staticmethod
    def bazi_validate(
        bazi_chart: dict[str, Any] | None = None,
        initial_interpretation: str = "ดวงชะตามีรากฐานมั่นคง",
        query: str = "",
    ) -> dict[str, Any]:
        """Validate astrological chart calculation and interpretation via Gemini Validator."""
        if bazi_chart is None:
            bazi_chart = HoroMCPTools.bazi_calculate("1990-05-15 14:30:00")
        return _get_validator().validate(
            bazi_chart=bazi_chart,
            initial_interpretation=initial_interpretation,
            user_query=query,
        )


# ==============================================================================
# MCP Tool Dispatcher & Invoker
# ==============================================================================

TOOL_METHOD_MAP: Dict[str, Any] = {
    # 16 Calculations
    "bazi_calculate": HoroMCPTools.bazi_calculate,
    "ziwei_calculate": HoroMCPTools.ziwei_calculate,
    "qimen_calculate": HoroMCPTools.qimen_calculate,
    "liuren_calculate": HoroMCPTools.liuren_calculate,
    "tai_yi_calculate": HoroMCPTools.tai_yi_calculate,
    "iching_calculate": HoroMCPTools.iching_calculate,
    "liu_yao_calculate": HoroMCPTools.liu_yao_calculate,
    "mei_hua_calculate": HoroMCPTools.mei_hua_calculate,
    "xuankong_calculate": HoroMCPTools.xuankong_calculate,
    "san_he_calculate": HoroMCPTools.san_he_calculate,
    "zeji_calculate": HoroMCPTools.zeji_calculate,
    "mian_xiang_analyze": HoroMCPTools.mian_xiang_analyze,
    "thaivedic_calculate": HoroMCPTools.thaivedic_calculate,
    "western_calculate": HoroMCPTools.western_calculate,
    "numerology_calculate": HoroMCPTools.numerology_calculate,
    "qi_zheng_calculate": HoroMCPTools.qi_zheng_calculate,
    # 18 Visualizers
    "render_bazi_svg": HoroMCPTools.render_bazi_svg,
    "render_ziwei_svg": HoroMCPTools.render_ziwei_svg,
    "render_qimen_svg": HoroMCPTools.render_qimen_svg,
    "render_liuren_svg": HoroMCPTools.render_liuren_svg,
    "render_tai_yi_svg": HoroMCPTools.render_tai_yi_svg,
    "render_iching_svg": HoroMCPTools.render_iching_svg,
    "render_liu_yao_svg": HoroMCPTools.render_liu_yao_svg,
    "render_meihua_svg": HoroMCPTools.render_meihua_svg,
    "render_xuankong_svg": HoroMCPTools.render_xuankong_svg,
    "render_sanhe_svg": HoroMCPTools.render_sanhe_svg,
    "render_zeji_svg": HoroMCPTools.render_zeji_svg,
    "render_mianxiang_svg": HoroMCPTools.render_mianxiang_svg,
    "render_thaivedic_svg": HoroMCPTools.render_thaivedic_svg,
    "render_western_svg": HoroMCPTools.render_western_svg,
    "render_numerology_svg": HoroMCPTools.render_numerology_svg,
    "render_qizheng_svg": HoroMCPTools.render_qizheng_svg,
    "render_zodiac_wheel_svg": HoroMCPTools.render_zodiac_wheel_svg,
    "render_zodiac_svg": HoroMCPTools.render_zodiac_wheel_svg,
    "render_multimodal_matrix_svg": HoroMCPTools.render_multimodal_matrix_svg,
    # Focus Router & Debate
    "question_focus_route": HoroMCPTools.question_focus_route,
    "metaphysics_debate": HoroMCPTools.metaphysics_debate,
    # Auxiliary Tools
    "rag_search": HoroMCPTools.rag_search,
    "bazi_interpret": HoroMCPTools.bazi_interpret,
    "bazi_validate": HoroMCPTools.bazi_validate,
}


def call_tool(name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    """Execute an MCP tool and return standardized execution result."""
    t0 = time.monotonic()
    args = arguments or {}

    if name not in TOOL_METHOD_MAP:
        elapsed = round((time.monotonic() - t0) * 1000, 2)
        log.error(f"[ERROR] Tool not found in registry: '{name}'")
        return {
            "tool_name": name,
            "success": False,
            "result": None,
            "error": f"Tool '{name}' is not registered in MCP catalog",
            "execution_time_ms": elapsed,
        }

    handler = TOOL_METHOD_MAP[name]
    try:
        res = handler(**args)
        elapsed = round((time.monotonic() - t0) * 1000, 2)
        log.info(f"[OK] Executed tool '{name}' in {elapsed}ms")
        return {
            "tool_name": name,
            "success": True,
            "result": res,
            "error": None,
            "execution_time_ms": elapsed,
        }
    except Exception as exc:
        elapsed = round((time.monotonic() - t0) * 1000, 2)
        log.error(f"[ERROR] Tool execution failed '{name}': {exc}", exc_info=True)
        return {
            "tool_name": name,
            "success": False,
            "result": None,
            "error": str(exc),
            "execution_time_ms": elapsed,
        }


def get_mcp_manifest() -> dict[str, Any]:
    """Return complete MCP server tool manifest containing all 36+ registered tools."""
    manifest = get_full_mcp_manifest()
    manifest_dict = manifest.model_dump()

    # Ensure auxiliary tools (rag_search, bazi_interpret, bazi_validate) are included
    existing_names = {t["name"] for t in manifest_dict.get("tools", [])}
    aux_tools = [
        {
            "name": "rag_search",
            "description": "Search 3,132 vectors of classical BaZi & Thai astrology books",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "top_k": {"type": "integer", "default": 3, "description": "Top-k matches"},
                },
                "required": ["query"],
            },
        },
        {
            "name": "bazi_interpret",
            "description": "Generate natural language interpretation with local qwen2.5:7b",
            "parameters": {
                "type": "object",
                "properties": {
                    "birth_datetime": {"type": "string", "description": "YYYY-MM-DD HH:MM:SS"},
                    "query": {"type": "string", "description": "User question"},
                    "longitude": {"type": "number", "default": 100.493},
                    "utc_offset_hours": {"type": "number", "default": 7.0},
                },
                "required": ["birth_datetime"],
            },
        },
        {
            "name": "bazi_validate",
            "description": "Cross-validate interpretation via Gemini Prediction Validator Agent",
            "parameters": {
                "type": "object",
                "properties": {
                    "bazi_chart": {"type": "object", "description": "BaZi chart dict"},
                    "initial_interpretation": {"type": "string"},
                    "query": {"type": "string"},
                },
                "required": ["bazi_chart", "initial_interpretation"],
            },
        },
    ]
    for aux in aux_tools:
        if aux["name"] not in existing_names:
            manifest_dict.setdefault("tools", []).append(aux)

    return manifest_dict


# ==============================================================================
# JSON-RPC 2.0 Stdio Transport Loop
# ==============================================================================

def run_stdio_server() -> None:
    """Run interactive RFC-compliant JSON-RPC 2.0 stdio transport loop."""
    log.info("[START] Computational Metaphysics MCP Server listening on stdio transport...")
    manifest = get_mcp_manifest()

    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            line_str = line.strip()
            if not line_str:
                continue

            req = json.loads(line_str)
            msg_id = req.get("id")
            method = req.get("method", "")
            params = req.get("params", {})

            if method == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {
                            "name": "horo-consultant-mcp",
                            "version": "1.0.0",
                        },
                    },
                }
            elif method == "notifications/initialized":
                continue
            elif method in ("tools/list", "tools"):
                response = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {"tools": manifest.get("tools", [])},
                }
            elif method == "tools/call":
                t_name = params.get("name", "")
                t_args = params.get("arguments", {})
                tool_res = call_tool(t_name, t_args)
                response = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(tool_res, ensure_ascii=False),
                            }
                        ],
                        "isError": not tool_res.get("success", False),
                    },
                }
            elif method == "ping":
                response = {"jsonrpc": "2.0", "id": msg_id, "result": {}}
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method '{method}' not found",
                    },
                }

            sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
            sys.stdout.flush()

        except json.JSONDecodeError as jde:
            err_resp = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {jde}"},
            }
            sys.stdout.write(json.dumps(err_resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()
        except Exception as exc:
            log.error(f"[ERROR] Stdio transport error: {exc}", exc_info=True)


def run_self_test() -> bool:
    """Execute automated self-test across all 36 MCP tools and print ASCII status."""
    log.info("[START] Running self-test across all 36 MCP tools...")
    sample_bazi = HoroMCPTools.bazi_calculate("1990-05-15 14:30:00")
    sample_ziwei = HoroMCPTools.ziwei_calculate(1990, 5, 15, 14)
    sample_qimen = HoroMCPTools.qimen_calculate(2026, 8, 7, 14)
    sample_liuren = HoroMCPTools.liuren_calculate("甲", "子", "正月", "午")
    sample_taiyi = HoroMCPTools.tai_yi_calculate(2026, 5, 15, 14)
    sample_iching = HoroMCPTools.iching_calculate("甲", seed=42)
    sample_liuyao = HoroMCPTools.liu_yao_calculate([7, 7, 7, 7, 7, 7], 0)
    sample_meihua = HoroMCPTools.mei_hua_calculate(2026, 5, 15, 14)
    sample_xuankong = HoroMCPTools.xuankong_calculate(180.0, 9)
    sample_sanhe = HoroMCPTools.san_he_calculate(0.0, 180.0)
    sample_zeji = HoroMCPTools.zeji_calculate("午", "申", "寅", "子")
    sample_mianxiang = HoroMCPTools.mian_xiang_analyze({"face_shape": "round", "forehead": "high_broad"})
    sample_thaivedic = HoroMCPTools.thaivedic_calculate(1990, 5, 15, 14, 2)
    sample_western = HoroMCPTools.western_calculate(1990, 5, 15, 14)
    sample_numerology = HoroMCPTools.numerology_calculate("0812345678", 2, 6, 7)
    sample_qizheng = HoroMCPTools.qi_zheng_calculate(2026, 5, 15, 14)

    test_matrix: list[tuple[str, dict[str, Any]]] = [
        ("bazi_calculate", {"birth_datetime": "1990-05-15 14:30:00", "longitude": 100.4930, "utc_offset_hours": 7.0}),
        ("ziwei_calculate", {"year": 1990, "month": 5, "day": 15, "hour": 14, "gender": "male"}),
        ("qimen_calculate", {"year": 2026, "month": 8, "day": 7, "hour": 14}),
        ("liuren_calculate", {"day_stem": "甲", "day_branch": "子", "month_general": "正月", "hour_branch": "午"}),
        ("tai_yi_calculate", {"year": 2026, "month": 5, "day": 15, "hour": 14}),
        ("iching_calculate", {"day_stem": "甲", "seed": 42}),
        ("liu_yao_calculate", {"lines": [7, 7, 7, 7, 7, 7], "day_stem_idx": 0}),
        ("mei_hua_calculate", {"year": 2026, "month": 5, "day": 15, "hour": 14}),
        ("xuankong_calculate", {"facing_degree": 180.0, "period": 9}),
        ("san_he_calculate", {"sitting_degree": 0.0, "facing_degree": 180.0}),
        ("zeji_calculate", {"year_branch": "午", "month_branch": "申", "day_branch": "寅", "user_birth_branch": "子"}),
        ("mian_xiang_analyze", {"features": {"face_shape": "round", "forehead": "high_broad"}}),
        ("thaivedic_calculate", {"year": 1990, "month": 5, "day": 15, "hour": 14, "day_of_week": 2}),
        ("western_calculate", {"year": 1990, "month": 5, "day": 15, "hour": 14}),
        ("numerology_calculate", {"text": "0812345678", "day_num": 2, "lunar_month": 6, "year_zodiac_num": 7}),
        ("qi_zheng_calculate", {"year": 2026, "month": 5, "day": 15, "hour": 14}),
        ("render_bazi_svg", {"chart": sample_bazi, "save_to_disk": False}),
        ("render_ziwei_svg", {"chart": sample_ziwei, "save_to_disk": False}),
        ("render_qimen_svg", {"chart": sample_qimen, "save_to_disk": False}),
        ("render_liuren_svg", {"chart": sample_liuren, "save_to_disk": False}),
        ("render_tai_yi_svg", {"chart": sample_taiyi, "save_to_disk": False}),
        ("render_iching_svg", {"chart": sample_iching, "save_to_disk": False}),
        ("render_liu_yao_svg", {"chart": sample_liuyao, "save_to_disk": False}),
        ("render_meihua_svg", {"chart": sample_meihua, "save_to_disk": False}),
        ("render_xuankong_svg", {"chart": sample_xuankong, "save_to_disk": False}),
        ("render_sanhe_svg", {"chart": sample_sanhe, "save_to_disk": False}),
        ("render_zeji_svg", {"chart": sample_zeji, "save_to_disk": False}),
        ("render_mianxiang_svg", {"chart": sample_mianxiang, "save_to_disk": False}),
        ("render_thaivedic_svg", {"chart": sample_thaivedic, "save_to_disk": False}),
        ("render_western_svg", {"chart": sample_western, "save_to_disk": False}),
        ("render_numerology_svg", {"chart": sample_numerology, "save_to_disk": False}),
        ("render_qizheng_svg", {"chart": sample_qizheng, "save_to_disk": False}),
        ("render_zodiac_wheel_svg", {"chart": sample_bazi, "save_to_disk": False}),
        ("render_multimodal_matrix_svg", {"data": {"consensus_score": 0.85, "favorable_elements": ["Metal", "Water"]}, "save_to_disk": False}),
        ("question_focus_route", {"query": "ควรเปลี่ยนงานไปทำธุรกิจส่วนตัวปี 2026 ดีหรือไม่?"}),
        ("metaphysics_debate", {"query": "วิเคราะห์ดวงชะตาและฤกษ์ยามมงคลในการขยายธุรกิจ", "birth_datetime": "1990-05-15 14:30:00"}),
        ("rag_search", {"query": "丙火", "top_k": 2}),
    ]

    all_passed = True
    passed_count = 0

    for name, args in test_matrix:
        res = call_tool(name, args)
        if res.get("success"):
            passed_count += 1
            print(f"[OK] {name:<30} ({res.get('execution_time_ms', 0):.2f}ms)")
        else:
            all_passed = False
            print(f"[ERROR] {name:<30} -> {res.get('error')}")

    if all_passed:
        print(f"\n[OK] All {passed_count}/{len(test_matrix)} MCP tools executed successfully without errors.")
    else:
        print(f"\n[ERROR] MCP self-test completed with failures ({passed_count}/{len(test_matrix)} passed).")

    return all_passed


# ==============================================================================
# CLI Entry Point
# ==============================================================================

if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--manifest":
            print(json.dumps(get_mcp_manifest(), indent=2, ensure_ascii=False))
        elif arg == "--test":
            success = run_self_test()
            sys.exit(0 if success else 1)
        elif arg == "--tool" and len(sys.argv) > 2:
            tool_name = sys.argv[2]
            tool_args = {}
            if "--args" in sys.argv:
                idx = sys.argv.index("--args")
                if idx + 1 < len(sys.argv):
                    tool_args = json.loads(sys.argv[idx + 1])
            res = call_tool(tool_name, tool_args)
            print(json.dumps(res, indent=2, ensure_ascii=False))
        elif arg in ("--help", "-h"):
            print("Computational Metaphysics MCP Server")
            print("Usage:")
            print("  python project/mcp_server.py --manifest   (Dump full tool catalog JSON)")
            print("  python project/mcp_server.py --test       (Execute automated self-test)")
            print("  python project/mcp_server.py --tool <name> --args '<json>' (Execute tool)")
            print("  python project/mcp_server.py              (Run JSON-RPC 2.0 stdio server)")
        else:
            run_stdio_server()
    else:
        run_stdio_server()
