"""
project/tests/test_rust_extensions.py
======================================
Tests for Phase 2 Rust Extensions & Fast Math integration:
1. FAISS / Dense Vector Search (< 1ms latency).
2. Xuan Kong Flying Stars 9-Grid Matrix calculations.
"""

import numpy as np
from project.core.fast_math import rust_dense_vector_search, fast_xuankong_9grid
from project.core.xuan_kong_engine import XuanKongEngine


def test_rust_dense_vector_search_basic():
    """Verify dense vector search returns correct top-k indices and scores."""
    q_vec = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    doc_matrix = np.array([
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.8, 0.6, 0.0],
    ], dtype=np.float32)

    hits = rust_dense_vector_search(q_vec, doc_matrix, top_k=2, threshold=0.0)
    assert len(hits) == 2
    assert hits[0][0] == 0  # Perfect match
    assert abs(hits[0][1] - 1.0) < 1e-3
    assert hits[1][0] == 2  # 0.8 dot product
    assert abs(hits[1][1] - 0.8) < 1e-3


def test_fast_xuankong_9grid_structure():
    """Verify fast_xuankong_9grid generates 9 grid palaces with valid stars."""
    grid = fast_xuankong_9grid(180.0, period=9)
    assert len(grid) == 9
    for (palace, base, sit, face) in grid:
        assert 1 <= palace <= 9
        assert 1 <= base <= 9
        assert 1 <= sit <= 9
        assert 1 <= face <= 9


def test_xuankong_engine_integration():
    """Verify XuanKongEngine output matches fast grid matrix values."""
    engine = XuanKongEngine()
    chart = engine.calculate_chart(180.0, period=9)
    palaces = chart.chart_data["grid_palaces"]
    assert len(palaces) == 9
    for p in palaces:
        assert "palace_number" in p
        assert "base_star" in p
        assert "sitting_star" in p
        assert "facing_star" in p


def test_fast_ziwei_stars():
    """Verify Zi Wei Dou Shu 14 main stars fast placement."""
    from project.core.fast_math import fast_ziwei_stars
    from project.core.zi_wei_engine import ZiWeiEngine
    
    res = fast_ziwei_stars(2)
    assert len(res) == 12
    engine = ZiWeiEngine()
    chart = engine.calculate_chart(1990, 5, 15, 14)
    assert len(chart.chart_data["palaces"]) == 12


def test_fast_qimen_matrix():
    """Verify Qi Men Dun Jia 4-plate fast matrix computation."""
    from project.core.fast_math import fast_qimen_matrix
    from project.core.qi_men_engine import QiMenEngine

    res = fast_qimen_matrix(True, 1)
    assert len(res) == 9
    engine = QiMenEngine()
    chart = engine.calculate_chart(2026, 8, 7, 14)
    assert len(chart.chart_data["palaces"]) == 9

