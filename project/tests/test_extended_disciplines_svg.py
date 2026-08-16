"""
project/tests/test_extended_disciplines_svg.py
================================================
Comprehensive verification for all 7 Extended Disciplines:
  1. Tai Yi Shen Shu (太乙神數)
  2. Liu Yao Divination (六爻預測)
  3. Mei Hua Yi Shu (梅花易數)
  4. San He Feng Shui (三合風水)
  5. Qi Zheng Si Yu (七政四餘)
  6. Mian Xiang Physiognomy (麻衣神相)
  7. Satta-Lek 7-Base & Chaldean (สัตตเลข 7 ฐาน)
"""

import pytest
from project.core.svg_generator import (
    generate_tai_yi_svg,
    generate_liu_yao_svg,
    generate_meihua_svg,
    generate_sanhe_svg,
    generate_qizheng_svg,
    generate_mianxiang_svg,
    generate_numerology_svg,
)
from project.core.tai_yi_engine import TaiYiEngine
from project.core.liu_yao_engine import LiuYaoEngine
from project.core.mei_hua_engine import MeiHuaEngine
from project.core.san_he_engine import SanHeEngine
from project.core.qi_zheng_engine import QiZhengSiYuEngine
from project.core.mian_xiang_engine import MianXiangEngine
from project.core.numerology_engine import NumerologyEngine


def test_tai_yi_engine_and_svg():
    engine = TaiYiEngine()
    chart = engine.calculate_chart(1990, 5, 15, 14)
    assert "accumulated_years" in chart
    assert "star_palace" in chart
    assert "tai_yi_number" in chart

    svg = generate_tai_yi_svg(chart)
    assert "<svg" in svg
    assert "</svg>" in svg
    assert "太乙神數" in svg
    assert 'viewBox="0 0 800 600"' in svg


def test_liu_yao_engine_and_svg():
    engine = LiuYaoEngine()
    chart = engine.calculate([7, 7, 7, 7, 7, 7]).chart_data
    assert "palace" in chart
    assert "lines" in chart

    svg = generate_liu_yao_svg(chart)
    assert "<svg" in svg
    assert "</svg>" in svg
    assert "六爻" in svg
    assert 'viewBox="0 0 800 600"' in svg


def test_mei_hua_engine_and_svg():
    engine = MeiHuaEngine()
    chart = engine.calculate(1990, 5, 15, 14).chart_data
    assert "primary_hexagram" in chart
    assert "body_function" in chart

    svg = generate_meihua_svg({
        "primary_hexagram": "乾為天",
        "mutual_hexagram": "乾為天",
        "transformed_hexagram": "天風姤",
        "moving_yao": 1,
        "body_trigram": "乾 (金)",
        "use_trigram": "巽 (木)",
        "interaction": "體克用 (Body controls Use - 吉)"
    })
    assert "<svg" in svg
    assert "</svg>" in svg
    assert "梅花易數" in svg
    assert 'viewBox="0 0 800 600"' in svg


def test_san_he_engine_and_svg():
    engine = SanHeEngine()
    res = engine.calculate(0.0, 120.0)
    chart = res.chart_data
    assert "sitting_mountain" in chart
    assert "water_exit" in chart

    svg = generate_sanhe_svg(chart)
    assert "<svg" in svg
    assert "</svg>" in svg
    assert "三合風水" in svg
    assert 'viewBox="0 0 800 600"' in svg


def test_qi_zheng_engine_and_svg():
    engine = QiZhengSiYuEngine()
    chart = engine.calculate(1990, 5, 15, 12).chart_data
    assert "planets" in chart
    assert "shadow_stars" in chart

    svg = generate_qizheng_svg(chart)
    assert "<svg" in svg
    assert "</svg>" in svg
    assert "七政四餘" in svg
    assert 'viewBox="0 0 800 600"' in svg


def test_mian_xiang_engine_and_svg():
    engine = MianXiangEngine()
    chart = engine.analyze_face_shape("oval")
    palaces = engine.analyze_12_palaces({"forehead": "wide", "nose": "high"})
    assert "Metal" in chart
    assert "命宮 (Life Palace)" in palaces

    svg = generate_mianxiang_svg({
        "face_shape": chart,
        "twelve_palaces": palaces
    })
    assert "<svg" in svg
    assert "</svg>" in svg
    assert "麻衣神相" in svg
    assert 'viewBox="0 0 800 600"' in svg


def test_numerology_engine_and_svg():
    engine = NumerologyEngine()
    satta = engine.calculate_satta_lek(day_num=2, lunar_month=6, year_zodiac_num=7).chart_data
    score = engine.score_text_or_number("0812345678").chart_data
    chart = {
        "satta_lek": satta,
        "chaldean_score": score
    }

    svg = generate_numerology_svg(chart)
    assert "<svg" in svg
    assert "</svg>" in svg
    assert "สัตตเลข" in svg
    assert 'viewBox=' in svg
