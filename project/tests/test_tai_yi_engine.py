"""
Tests for Tai Yi Shen Shu Engine
"""
import pytest
from project.core.tai_yi_engine import TaiYiEngine

def test_accumulated_years():
    engine = TaiYiEngine()
    # 2026 - 4 = 2022
    # 2022 % 72 = 6
    chart = engine.calculate(2026, 1, 1, 1)
    assert chart["accumulated_years"] == 6
    
def test_accumulated_years_epoch():
    engine = TaiYiEngine()
    # 4 - 4 = 0
    # 0 % 72 = 0
    chart = engine.calculate(4, 1, 1, 1)
    assert chart["accumulated_years"] == 0
    
def test_accumulated_years_negative():
    engine = TaiYiEngine()
    # 3 - 4 = -1
    # -1 % 72 = 71
    chart = engine.calculate(3, 1, 1, 1)
    assert chart["accumulated_years"] == 71

def test_accumulated_years_boundary():
    engine = TaiYiEngine()
    # 76 - 4 = 72
    # 72 % 72 = 0
    chart = engine.calculate(76, 1, 1, 1)
    assert chart["accumulated_years"] == 0

def test_star_palace():
    engine = TaiYiEngine()
    chart = engine.calculate(2026, 1, 1, 1)
    # acc = 6, 6 % 16 = 6
    assert chart["star_palace"] == 6

def test_star_palace_boundary():
    engine = TaiYiEngine()
    # year = 20, acc = 16, star_palace = 16 % 16 = 0
    chart = engine.calculate(20, 1, 1, 1)
    assert chart["star_palace"] == 0

def test_star_palace_high():
    engine = TaiYiEngine()
    # year = 35, acc = 31, star_palace = 31 % 16 = 15
    chart = engine.calculate(35, 1, 1, 1)
    assert chart["star_palace"] == 15

def test_heaven_earth_plate_generation():
    engine = TaiYiEngine()
    chart = engine.calculate(4, 1, 1, 1) # acc = 0
    assert chart["earth_plate"] == [1, 2, 3, 4, 5, 6, 7, 8, 9]
    assert chart["heaven_plate"] == [1, 2, 3, 4, 5, 6, 7, 8, 9]
    
def test_heaven_earth_plate_rotation():
    engine = TaiYiEngine()
    chart = engine.calculate(5, 1, 1, 1) # acc = 1
    assert chart["earth_plate"] == [2, 3, 4, 5, 6, 7, 8, 9, 1]
    assert chart["heaven_plate"] == [3, 4, 5, 6, 7, 8, 9, 1, 2]

def test_strategic_assessment():
    engine = TaiYiEngine()
    chart = engine.calculate(4, 1, 1, 1) # star_palace = 0
    assert chart["strategic_assessment"] == "吉"
    
def test_strategic_assessment_other():
    engine = TaiYiEngine()
    chart = engine.calculate(5, 1, 1, 1) # star_palace = 1
    assert chart["strategic_assessment"] == "凶"

def test_cycle_info():
    engine = TaiYiEngine()
    chart = engine.calculate(2026, 1, 1, 1)
    cycle = chart["cycle_info"]
    assert cycle["epoch_offset"] == 4
    assert cycle["cycle_length"] == 72
    assert cycle["current_cycle_year"] == 7

def test_tai_yi_number():
    engine = TaiYiEngine()
    chart = engine.calculate(2026, 2, 3, 4)
    # acc = 6
    # 2026 * 2 * 3 * 4 = 48624
    # 48624 + 6 = 48630
    # 48630 % 10000 = 8630
    assert chart["tai_yi_number"] == 8630

def test_full_chart_integration():
    engine = TaiYiEngine()
    chart = engine.calculate(2026, 8, 15, 12)
    assert chart.engine_name == "Tai Yi Shen Shu Engine"
    assert chart.system_type == "san_shi"
    
    data = chart
    assert "tai_yi_number" in data
    assert "accumulated_years" in data
    assert "heaven_plate" in data
    assert "earth_plate" in data
    assert "star_palace" in data
    assert "strategic_assessment" in data
    assert "cycle_info" in data
    assert len(data["heaven_plate"]) == 9
    assert len(data["earth_plate"]) == 9

def test_engine_properties():
    engine = TaiYiEngine()
    assert engine.engine_name == "Tai Yi Shen Shu Engine"
    assert engine.system_type == "san_shi"
