import pytest
from project.core.mei_hua_engine import MeiHuaEngine

def test_calculate_from_time():
    engine = MeiHuaEngine()
    # year=1, month=1, day=1, hour=1
    # upper = (1+1+1) % 8 = 3 (離)
    # lower = (1+1+1+1) % 8 = 4 (震)
    # moving = (4) % 6 = 4
    result = engine.calculate_from_time(year=1, month=1, day=1, hour=1)
    
    assert result.chart_data["primary_hexagram"]["upper_trigram"] == "離"
    assert result.chart_data["primary_hexagram"]["lower_trigram"] == "震"
    assert result.chart_data["primary_hexagram"]["moving_line"] == 4
    
    # Body is lower (moving line 4 is in upper), Function is upper
    assert result.chart_data["body_function"]["body_trigram"] == "震"
    assert result.chart_data["body_function"]["function_trigram"] == "離"
    assert result.chart_data["body_function"]["body_element"] == "木"
    assert result.chart_data["body_function"]["function_element"] == "火"
    # Body (Wood) generates Function (Fire) -> 洩
    assert result.chart_data["body_function"]["interaction"] == "洩"
    
    # Lines: 震 = [1, 0, 0], 離 = [1, 0, 1]
    # Primary: [1, 0, 0, 1, 0, 1]
    # Mutual Lower: [0, 0, 1] (艮)
    # Mutual Upper: [0, 1, 0] (坎)
    assert result.chart_data["mutual_hexagram"]["lower_trigram"] == "艮"
    assert result.chart_data["mutual_hexagram"]["upper_trigram"] == "坎"
    
    # Transformed: Moving line 4 (index 3). Primary index 3 is 1. Flip to 0.
    # New upper lines: [0, 0, 1] -> 艮
    # New lower lines: [1, 0, 0] -> 震
    assert result.chart_data["transformed_hexagram"]["upper_trigram"] == "艮"
    assert result.chart_data["transformed_hexagram"]["lower_trigram"] == "震"

def test_calculate_from_numbers():
    engine = MeiHuaEngine()
    # 8, 8 -> 坤, 坤. Moving line = 16 % 6 = 4
    res = engine.calculate_from_numbers(upper_num=8, lower_num=8)
    assert res.chart_data["primary_hexagram"]["upper_trigram"] == "坤"
    assert res.chart_data["primary_hexagram"]["lower_trigram"] == "坤"
    assert res.chart_data["primary_hexagram"]["moving_line"] == 4

def test_zero_modulo_time():
    engine = MeiHuaEngine()
    # year=4, month=2, day=2, hour=4 -> sum=12
    # upper = 8 -> 坤
    # lower = 12 % 8 = 4 -> 震
    # moving = 12 % 6 = 6
    res = engine.calculate_from_time(year=4, month=2, day=2, hour=4)
    assert res.chart_data["primary_hexagram"]["upper_trigram"] == "坤"
    assert res.chart_data["primary_hexagram"]["lower_trigram"] == "震"
    assert res.chart_data["primary_hexagram"]["moving_line"] == 6

def test_calculate_with_explicit_moving_num():
    engine = MeiHuaEngine()
    # 1, 2, moving=3 -> Upper 乾, Lower 兌, Moving 3
    res = engine.calculate_from_numbers(upper_num=1, lower_num=2, moving_num=3)
    assert res.chart_data["primary_hexagram"]["upper_trigram"] == "乾"
    assert res.chart_data["primary_hexagram"]["lower_trigram"] == "兌"
    assert res.chart_data["primary_hexagram"]["moving_line"] == 3

def test_interaction_same():
    engine = MeiHuaEngine()
    # Body=乾(金), Function=兌(金) -> 比和
    res = engine.calculate_from_numbers(1, 2, 1) 
    assert res.chart_data["body_function"]["interaction"] == "比和"

def test_interaction_hao():
    engine = MeiHuaEngine()
    # Body controls Function (耗): Body=乾(金), Function=震(木)
    res = engine.calculate_from_numbers(1, 4, 1)
    assert res.chart_data["body_function"]["interaction"] == "耗"

def test_interaction_ke():
    engine = MeiHuaEngine()
    # Function controls Body (克): Body=乾(金), Function=離(火)
    res = engine.calculate_from_numbers(1, 3, 1)
    assert res.chart_data["body_function"]["interaction"] == "克"

def test_interaction_sheng():
    engine = MeiHuaEngine()
    # Function generates Body (生): Body=乾(金), Function=坤(土)
    res = engine.calculate_from_numbers(1, 8, 1)
    assert res.chart_data["body_function"]["interaction"] == "生"

def test_interaction_xie():
    engine = MeiHuaEngine()
    # Body generates Function (洩): Body=乾(金), Function=坎(水)
    res = engine.calculate_from_numbers(1, 6, 1)
    assert res.chart_data["body_function"]["interaction"] == "洩"

def test_engine_metadata():
    engine = MeiHuaEngine()
    assert engine.engine_name == "Mei Hua Yi Shu Engine"
    assert engine.system_type == "divination"

def test_calculate_wrapper_time():
    engine = MeiHuaEngine()
    res = engine.calculate(year=1, month=1, day=1, hour=1)
    assert res.chart_data["primary_hexagram"]["upper_trigram"] == "離"

def test_calculate_wrapper_numbers():
    engine = MeiHuaEngine()
    res = engine.calculate(upper_num=1, lower_num=2)
    assert res.chart_data["primary_hexagram"]["upper_trigram"] == "乾"

def test_invalid_calculate():
    engine = MeiHuaEngine()
    with pytest.raises(ValueError):
        engine.calculate(unknown=1)
