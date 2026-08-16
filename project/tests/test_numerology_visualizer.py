"""
Unit test suite for Satta-Lek 7-Base & Chaldean Numerology Visualizer.
Verifies calculation accuracy, letter breakdown, power base mapping, and SVG rendering.
"""

import pytest
from project.core.numerology_engine import NumerologyEngine, PLANETARY_POWER_BASE, CHALDEAN_MAP
from project.core.svg_generator import generate_numerology_svg


@pytest.fixture
def engine():
    return NumerologyEngine()


def test_satta_lek_matrix_calculation(engine):
    """Test 7-base 4-row matrix computation and house names."""
    res = engine.calculate_satta_lek(day_num=2, lunar_month=6, year_zodiac_num=7).to_dict()
    assert res["engine"] == "SattaLekEngine"
    matrix = res["matrix_7_base"]
    assert len(matrix) == 7

    # Check 7 houses
    expected_houses = ["อัตตา", "หินะ", "ธนัง", "ปิตา", "มาตา", "โภคา", "มัชฌิมา"]
    for i, house in enumerate(expected_houses):
        assert matrix[i]["house_name"] == house
        assert "row1_day" in matrix[i]
        assert "row2_month" in matrix[i]
        assert "row3_year" in matrix[i]
        assert "row4_sum" in matrix[i]
        assert matrix[i]["row4_sum"] == matrix[i]["row1_day"] + matrix[i]["row2_month"] + matrix[i]["row3_year"]
        assert "power_name" in matrix[i]
        assert "power_meaning" in matrix[i]


def test_chaldean_scoring_and_char_breakdown(engine):
    """Test Chaldean numerology scoring, character breakdown, and root reduction."""
    score = engine.score_text_or_number("0812345678").to_dict()
    assert score["engine"] == "ChaldeanNumerologyEngine"
    assert score["input_text"] == "0812345678"
    assert score["total_score"] == sum(int(d) for d in "0812345678")
    assert 1 <= score["reduced_root_digit"] <= 9
    assert len(score["char_breakdown"]) == 10
    assert "digit_meaning" in score
    assert "auspicious_tier" in score


def test_chaldean_thai_text_scoring(engine):
    """Test Thai text gematria scoring in Chaldean map."""
    thai_name = "สิริโชค"
    score = engine.score_text_or_number(thai_name).to_dict()
    assert score["total_score"] > 0
    assert 1 <= score["reduced_root_digit"] <= 9
    assert len(score["char_breakdown"]) > 0


def test_generate_numerology_svg(engine):
    """Test SVG rendering for Satta-Lek & Chaldean numerology."""
    satta_lek = engine.calculate_satta_lek(2, 6, 7).to_dict()
    chaldean_score = engine.score_text_or_number("0812345678").to_dict()
    chart = {"satta_lek": satta_lek, "chaldean_score": chaldean_score}

    svg = generate_numerology_svg(chart)
    assert svg.startswith("<svg")
    assert "</svg>" in svg
    assert "สัตตเลข 7 ฐาน" in svg
    assert "Chaldean Score" in svg
    assert "อัตตา" in svg
    assert "มัชฌิมา" in svg
