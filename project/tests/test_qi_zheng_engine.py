import pytest
from project.core.qi_zheng_engine import QiZhengSiYuEngine, LUNAR_MANSIONS

def test_engine_metadata():
    engine = QiZhengSiYuEngine()
    assert engine.engine_name == "Qi Zheng Si Yu Engine"
    assert engine.system_type == "chinese_astrology"

def test_get_lunar_mansion_0():
    engine = QiZhengSiYuEngine()
    assert engine.get_lunar_mansion(0.0) == "角"

def test_get_lunar_mansion_350():
    engine = QiZhengSiYuEngine()
    assert engine.get_lunar_mansion(350.0) == "軫"

def test_get_lunar_mansion_180():
    engine = QiZhengSiYuEngine()
    assert engine.get_lunar_mansion(180.0) == "奎"

def test_calculate_basic():
    engine = QiZhengSiYuEngine()
    res = engine.calculate(2025, 1, 1, 12)
    assert "planets" in res.chart_data
    assert "shadow_stars" in res.chart_data

def test_calculate_planets_count():
    engine = QiZhengSiYuEngine()
    res = engine.calculate(2025, 1, 1, 12)
    assert len(res.chart_data["planets"]) == 7

def test_calculate_shadow_stars_count():
    engine = QiZhengSiYuEngine()
    res = engine.calculate(2025, 1, 1, 12)
    assert len(res.chart_data["shadow_stars"]) == 4

def test_calculate_lunar_mansions_count():
    engine = QiZhengSiYuEngine()
    res = engine.calculate(2025, 1, 1, 12)
    # 7 planets + 4 shadow stars = 11
    assert len(res.chart_data["lunar_mansions"]) == 11

def test_calculate_ayanamsa_field():
    engine = QiZhengSiYuEngine()
    res = engine.calculate(2025, 1, 1, 12)
    assert "ayanamsa_degrees" in res.chart_data
    assert res.chart_data["ayanamsa_degrees"] == 24.0

def test_calculate_coordinates():
    engine = QiZhengSiYuEngine()
    res = engine.calculate(2025, 1, 1, 12, 105.0, 20.0)
    assert res.chart_data["coordinates"]["longitude"] == 105.0
    assert res.chart_data["coordinates"]["latitude"] == 20.0

def test_calculate_planets_keys():
    engine = QiZhengSiYuEngine()
    res = engine.calculate(2025, 1, 1, 12)
    planets = res.chart_data["planets"]
    assert "日 (Sun)" in planets
    assert "月 (Moon)" in planets
    assert "木 (Jupiter)" in planets
    assert "火 (Mars)" in planets
    assert "土 (Saturn)" in planets
    assert "金 (Venus)" in planets
    assert "水 (Mercury)" in planets

def test_calculate_shadow_keys():
    engine = QiZhengSiYuEngine()
    res = engine.calculate(2025, 1, 1, 12)
    shadows = res.chart_data["shadow_stars"]
    assert "羅睺 (Rahu)" in shadows
    assert "計都 (Ketu)" in shadows
    assert "月孛 (Yuebei)" in shadows
    assert "紫氣 (Ziqi)" in shadows

def test_deterministic_output_1():
    engine = QiZhengSiYuEngine()
    res1 = engine.calculate(2020, 5, 15, 10)
    res2 = engine.calculate(2020, 5, 15, 10)
    assert res1.chart_data == res2.chart_data

def test_deterministic_output_2():
    engine = QiZhengSiYuEngine()
    res1 = engine.calculate(1990, 8, 8, 8, 110.0, 25.0)
    res2 = engine.calculate(1990, 8, 8, 8, 110.0, 25.0)
    assert res1.chart_data == res2.chart_data

def test_lunar_mansion_mapping():
    engine = QiZhengSiYuEngine()
    res = engine.calculate(2025, 1, 1, 12)
    # Just check it's populated and values are in LUNAR_MANSIONS
    for k, v in res.chart_data["lunar_mansions"].items():
        assert v in LUNAR_MANSIONS
