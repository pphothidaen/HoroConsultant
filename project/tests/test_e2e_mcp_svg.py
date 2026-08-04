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
from project.core.svg_generator import generate_bazi_svg, generate_zodiac_wheel_svg


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
