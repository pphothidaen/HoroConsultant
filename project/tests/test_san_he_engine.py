import pytest
from project.core.san_he_engine import SanHeEngine

def test_engine_metadata():
    engine = SanHeEngine()
    assert engine.engine_name == "San He Feng Shui Engine"
    assert engine.system_type == "feng_shui"

def test_resolve_mountain_ren():
    engine = SanHeEngine()
    assert engine.resolve_mountain(340.0) == 0  # 壬

def test_resolve_mountain_zi():
    engine = SanHeEngine()
    assert engine.resolve_mountain(0.0) == 1    # 子

def test_resolve_mountain_gui():
    engine = SanHeEngine()
    assert engine.resolve_mountain(10.0) == 2   # 癸

def test_resolve_mountain_wu():
    engine = SanHeEngine()
    assert engine.resolve_mountain(180.0) == 13 # 午

def test_resolve_mountain_kun():
    engine = SanHeEngine()
    assert engine.resolve_mountain(225.0) == 16 # 坤

def test_resolve_mountain_qian():
    engine = SanHeEngine()
    assert engine.resolve_mountain(315.0) == 22 # 乾

def test_water_method():
    engine = SanHeEngine()
    # sitting 1 (子), water exit 13 (午) -> diff = 12 -> stage_idx 6 (病)
    res = engine.water_method(1, 13)
    assert res[0] == "病"

def test_water_method_2():
    engine = SanHeEngine()
    res = engine.water_method(0, 0)
    assert res[0] == "長生"

def test_evaluate_harmony_water():
    engine = SanHeEngine()
    assert "Water" in engine.evaluate_harmony("申", "辰")
    assert "Water" in engine.evaluate_harmony("子", "申")

def test_evaluate_harmony_fire():
    engine = SanHeEngine()
    assert "Fire" in engine.evaluate_harmony("寅", "午")

def test_evaluate_harmony_none():
    engine = SanHeEngine()
    assert engine.evaluate_harmony("甲", "辰") == "No San He formation"

def test_calculate_no_water():
    engine = SanHeEngine()
    res = engine.calculate(0.0)
    assert res.chart_data["sitting_mountain"] == "子"
    assert res.chart_data["facing_mountain"] == "午"
    assert res.chart_data["harmony_assessment"] == "N/A"

def test_calculate_with_water():
    engine = SanHeEngine()
    res = engine.calculate(180.0, water_exit_degree=295.0)  # Sitting 午 (13), water exit 戌 (21)
    assert res.chart_data["sitting_mountain"] == "午"
    assert "Fire" in res.chart_data["harmony_assessment"]
    assert res.chart_data["san_he_formation"] == "寅午戌"
