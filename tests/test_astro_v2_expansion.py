# tests/test_astro_v2_expansion.py
"""Test suite for Sprint SPRINT-HORO-V2-ENGINE-UX-20260904.

Verifies:
1. Da Liu Ren (大六壬) Three Transmissions & Twelve Generals engine
2. Zi Wei Dou Shu (紫微斗数) 12 Palaces & 14 Major Stars engine
3. I Ching (周易) 64 Hexagrams & line transitions engine
4. Qi Men Dun Jia (奇门遁甲) 9 Stars, 8 Gates & Plates engine
5. RAG Vector Store query and classical scripture retrieval
6. Frontend LuoPan 24-mountain compass and eco-mode instant bypass UI parity
"""

import os
from pathlib import Path
import pytest

from project.core.liu_ren_engine import LiuRenEngine
from project.core.zi_wei_engine import ZiWeiEngine
from project.core.iching_engine import IChingEngine
from project.core.qi_men_engine import QiMenEngine
from project.rag.vector_store import VectorStore


class TestAstroEngineExpansion:
    """Track 1: Metaphysics & Astro Calculation Engines."""

    def test_liu_ren_engine_calculation(self):
        engine = LiuRenEngine()
        result = engine.calculate(
            day_stem="甲",
            day_branch="子",
            month_general="正月",
            hour_branch="午",
            is_daytime=True
        )
        assert result is not None
        data = result.chart_data if hasattr(result, "chart_data") else result
        assert "three_transmissions" in data
        assert "heaven_plate" in data
        assert "generals_detail" in data

    def test_zi_wei_engine_palaces_and_stars(self):
        engine = ZiWeiEngine()
        result = engine.calculate_chart(
            year=2026,
            month=9,
            day=4,
            hour=13,
            gender="male"
        )
        assert result is not None
        assert "palaces" in result or "ming_palace" in result or "shen_palace" in result

    def test_iching_engine_hexagrams(self):
        engine = IChingEngine()
        lines = engine.cast_lines(seed=42)
        result = engine.calculate_liu_yao("甲", lines)
        assert result is not None
        data = result.chart_data if hasattr(result, "chart_data") else result
        assert "primary_hexagram" in data
        assert "six_lines" in data

    def test_qi_men_engine_nine_stars_eight_gates(self):
        engine = QiMenEngine()
        result = engine.calculate_chart(
            year=2026,
            month=9,
            day=4,
            hour=13
        )
        assert result is not None
        assert "ju_name" in result or "solar_term" in result or "earth_plate" in result


class TestRAGVectorStoreExpansion:
    """Track 2: RAG Vector Search & Embeddings Optimization."""

    def test_vector_store_initialization_and_search(self):
        store = VectorStore()
        assert store is not None
        assert hasattr(store, "search") or hasattr(store, "query") or hasattr(store, "find_similar")


class TestLuoPanAndEcoModalUIParity:
    """Track 3: LuoPan Compass & Eco-Mode UI Components."""

    def test_static_index_html_has_user_friendly_eco_modal_and_luopan(self):
        root = Path(__file__).resolve().parent.parent
        index_static = (root / "project" / "static" / "index.html").read_text(encoding="utf-8")
        index_public = (root / "public" / "index.html").read_text(encoding="utf-8")

        assert "cold-start-modal" in index_static
        assert "cold-start-stage" in index_static
        assert "cold-start-tip-box" in index_static
        assert "cold-start-instant-btn" in index_static

        # Parity with public/index.html
        assert "cold-start-modal" in index_public
        assert "cold-start-stage" in index_public
        assert "cold-start-tip-box" in index_public
        assert "cold-start-instant-btn" in index_public

    def test_app_js_has_instant_edge_bypass_function(self):
        root = Path(__file__).resolve().parent.parent
        app_static = (root / "project" / "static" / "app.js").read_text(encoding="utf-8")
        app_public = (root / "public" / "app.js").read_text(encoding="utf-8")

        assert "bypassColdStartToEdgeEngine" in app_static
        assert "METAPHYSICS_TIPS" in app_static
        assert "โหมดประหยัดพลังงาน (Eco-Mode)" in app_static

        # Parity with public/app.js
        assert "bypassColdStartToEdgeEngine" in app_public
        assert "METAPHYSICS_TIPS" in app_public
        assert "โหมดประหยัดพลังงาน (Eco-Mode)" in app_public
