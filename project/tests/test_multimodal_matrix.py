"""
project/tests/test_multimodal_matrix.py
=========================================
Unit and integration tests for Phase 3 Unified Multimodal Matrix Dashboard:
  - 16-Discipline Consensus Engine
  - 6 Life Domain Configurations (Career, Wealth, Love, Health, Family, Timing)
  - Composite Multimodal Matrix SVG Vector Generator
"""

import pytest
from project.core.svg_generator import generate_multimodal_matrix_svg


def test_generate_multimodal_matrix_svg_default():
    data = {
        "domain_name": "ธุรกิจและการงาน (Career)",
        "consensus_score_pct": 88,
        "favorable_pct": 82,
        "element_harmony": "ธาตุไม้-ธาตุไฟ เกื้อหนุนสมบูรณ์"
    }
    svg = generate_multimodal_matrix_svg(data)
    assert "<svg" in svg
    assert "</svg>" in svg
    assert "ผังดวงสังเคราะห์ 16 ศาสตร์" in svg
    assert "88%" in svg
    assert "viewBox=\"0 0 800 600\"" in svg
    assert "四柱" in svg
    assert "紫微" in svg
    assert "奇門" in svg
    assert "สายโหราศาสตร์คำนวณ" in svg


def test_generate_multimodal_matrix_svg_all_domains():
    domains = [
        ("ธุรกิจและการงาน (Career)", 88, 82),
        ("การเงินและโชคลาภ (Wealth & Finance)", 91, 85),
        ("ความรักและคู่ครอง (Love & Marriage)", 84, 78),
        ("สุขภาพและพลังชีวิต (Health & Vitality)", 86, 80),
        ("ครอบครัวและที่อยู่อาศัย (Home & Property)", 89, 84),
        ("กาลเวลาและฤกษ์มงคล (Timing & Auspicious Periods)", 93, 88),
    ]

    for d_name, c_score, f_score in domains:
        svg = generate_multimodal_matrix_svg({
            "domain_name": d_name,
            "consensus_score_pct": c_score,
            "favorable_pct": f_score,
            "element_harmony": "ทดสอบสมดุลธาตุ"
        })
        assert "<svg" in svg
        assert "</svg>" in svg
        assert f"{c_score}%" in svg
        assert d_name in svg
