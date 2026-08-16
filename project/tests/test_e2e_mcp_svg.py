"""
project/tests/test_e2e_mcp_svg.py
===================================
End-to-End (E2E) MCP Integration & SVG Vector Chart Rendering Test Suite.

Verifies:
  - MCP Tool calls (bazi_calculate, rag_search, bazi_interpret, bazi_validate)
  - Standalone SVG Chart generation for BaZi 4 Pillars (bazi_chart.svg)
  - Standalone SVG Chart generation for 12 Zodiac Wheel (zodiac_wheel.svg)
  - File generation and XML/SVG markup validity

Usage:
  python -m pytest project/tests/test_e2e_mcp_svg.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from project.mcp_server import HoroMCPTools, get_mcp_manifest


class TestE2EMCPServerAndSVG:
    """E2E Test cases for MCP tools and SVG chart generators."""

    def test_mcp_manifest_structure(self):
        manifest = get_mcp_manifest()
        assert manifest["name"] == "horo-consultant-mcp"
        assert len(manifest["tools"]) >= 4
        tool_names = [t["name"] for t in manifest["tools"]]
        assert "bazi_calculate" in tool_names
        assert "rag_search" in tool_names

    def test_e2e_bazi_calculate_mcp(self):
        res = HoroMCPTools.bazi_calculate("1990-05-15 14:30:00", longitude=100.4930, utc_offset_hours=7.0)
        assert "day_master" in res
        assert "five_elements" in res
        assert res["day_master"]["stem"] == "庚"

    def test_e2e_rag_search_mcp(self):
        res = HoroMCPTools.rag_search("丙火", top_k=2)
        assert "matches" in res
        assert "total_vectors" in res
        assert res["total_vectors"] > 0

    def test_e2e_render_bazi_svg_mcp(self):
        res = HoroMCPTools.render_bazi_svg("1990-05-15 14:30:00")
        assert "svg_file" in res
        assert "svg_length" in res
        
        svg_path = ROOT / res["svg_file"]
        assert svg_path.exists()
        content = svg_path.read_text(encoding="utf-8")
        assert "<svg" in content
        assert "ผังดวงชะตา BaZi" in content
        assert "</svg>" in content

    def test_e2e_render_zodiac_svg_mcp(self):
        res = HoroMCPTools.render_zodiac_svg("1990-05-15 14:30:00")
        assert "svg_file" in res
        assert "svg_length" in res
        
        svg_path = ROOT / res["svg_file"]
        assert svg_path.exists()
        content = svg_path.read_text(encoding="utf-8")
        assert "<svg" in content
        assert "ผังดวงจักรราศี" in content
        assert "</svg>" in content

    def test_5_branch_svg_generators(self):
        from project.core.qi_men_engine import QiMenEngine
        from project.core.svg_generator import (
            generate_qimen_svg,
            generate_xuankong_svg,
            generate_ziwei_svg,
        )
        from project.core.xuan_kong_engine import XuanKongEngine
        from project.core.zi_wei_engine import ZiWeiEngine

        zw_chart = ZiWeiEngine().calculate_chart(1990, 5, 15, 14)
        zw_svg = generate_ziwei_svg(zw_chart)
        assert "<svg" in zw_svg and "紫微斗數" in zw_svg

        qm_chart = QiMenEngine().calculate_chart(2026, 8, 7, 14)
        qm_svg = generate_qimen_svg(qm_chart)
        assert "<svg" in qm_svg and "奇門遁甲" in qm_svg

        xk_chart = XuanKongEngine().calculate_chart(180.0, 9)
        xk_svg = generate_xuankong_svg(xk_chart)
        assert "<svg" in xk_svg and "玄空風水" in xk_svg

    def test_svg_adapter_never_selects_lossy_native_placeholders(self, monkeypatch):
        from project.core import svg_generator
        from project.core.qi_men_engine import QiMenEngine
        from project.core.xuan_kong_engine import XuanKongEngine
        from project.core.zi_wei_engine import ZiWeiEngine

        monkeypatch.setattr(svg_generator, "RUST_AVAILABLE", True)
        for kernel_name in (
            "build_bazi_svg_rust",
            "build_ziwei_svg_rust",
            "build_qimen_svg_rust",
            "build_xuankong_svg_rust",
        ):
            monkeypatch.setattr(
                svg_generator.rust_core,
                kernel_name,
                lambda *args: "<svg>PLACEHOLDER</svg>",
                raising=False,
            )

        bazi_chart = {
            "day_master": {"stem": "庚", "element": "Metal", "polarity": "Yang"},
            "solar_time_info": {"tst_datetime": "1990-05-15 14:09:13"},
            "five_elements": {"percentages": {"Wood": 12.5, "Metal": 30.0}},
            "pillars": {
                key: {
                    "stem": {"char": "庚", "pinyin": "Gēng", "element": "Metal"},
                    "branch": {"char": "午", "pinyin": "Wǔ", "animal": "Horse", "element": "Fire"},
                }
                for key in ("hour", "day", "month", "year")
            },
        }
        bazi_svg = svg_generator.generate_bazi_svg(bazi_chart)
        assert "Gēng" in bazi_svg and "Wood: 12.5%" in bazi_svg
        assert "1990-05-15 14:09:13" in bazi_svg

        zw_chart = ZiWeiEngine().calculate_chart(1990, 5, 15, 14)
        zw_svg = svg_generator.generate_ziwei_svg(zw_chart)
        assert "天同" in zw_svg and "天同化忌" in zw_svg

        qm_chart = QiMenEngine().calculate_chart(2026, 8, 7, 14)
        qm_svg = svg_generator.generate_qimen_svg(qm_chart)
        assert "天蓬" in qm_svg and "休門" in qm_svg and "值符" in qm_svg

        xk_chart = XuanKongEngine().calculate_chart(180.0, 9)
        xk_svg = svg_generator.generate_xuankong_svg(xk_chart)
        assert "午 (離卦 - 陰)" in xk_svg and ">4</text>" in xk_svg

        assert "PLACEHOLDER" not in bazi_svg + zw_svg + qm_svg + xk_svg
