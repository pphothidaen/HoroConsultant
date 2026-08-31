import json
import pytest
from project.core.base_engine import AbstractAstrologyEngine, EngineChartResult
from project.core.qi_zheng_engine import QiZhengSiYuEngine, LUNAR_MANSIONS, MANSION_TABLE


def test_engine_metadata():
    engine = QiZhengSiYuEngine()
    assert isinstance(engine, AbstractAstrologyEngine)
    assert engine.engine_name == "Qi Zheng Si Yu Engine"
    assert engine.system_type == "chinese_astrology"


def test_mansion_table_completeness():
    assert len(LUNAR_MANSIONS) == 28
    assert len(MANSION_TABLE) == 28
    assert MANSION_TABLE[0]["start_deg"] == 0.0
    assert MANSION_TABLE[-1]["end_deg"] == 360.0

    # Verify cumulative continuity
    for i in range(len(MANSION_TABLE) - 1):
        assert MANSION_TABLE[i]["end_deg"] == MANSION_TABLE[i + 1]["start_deg"]

    # Verify 4 directions
    directions = [entry["direction"] for entry in MANSION_TABLE]
    assert directions[:7] == ["East"] * 7
    assert directions[7:14] == ["North"] * 7
    assert directions[14:21] == ["West"] * 7
    assert directions[21:28] == ["South"] * 7


@pytest.mark.parametrize("mansion_name,expected_dir,expected_beast,expected_elem", [
    # East Azure Dragon
    ("角", "East", "Azure Dragon (東方青龍)", "木"),
    ("亢", "East", "Azure Dragon (東方青龍)", "金"),
    ("氐", "East", "Azure Dragon (東方青龍)", "土"),
    ("房", "East", "Azure Dragon (東方青龍)", "日"),
    ("心", "East", "Azure Dragon (東方青龍)", "月"),
    ("尾", "East", "Azure Dragon (東方青龍)", "火"),
    ("箕", "East", "Azure Dragon (東方青龍)", "水"),
    # North Black Tortoise
    ("斗", "North", "Black Tortoise (北方玄武)", "木"),
    ("牛", "North", "Black Tortoise (北方玄武)", "金"),
    ("女", "North", "Black Tortoise (北方玄武)", "土"),
    ("虛", "North", "Black Tortoise (北方玄武)", "日"),
    ("危", "North", "Black Tortoise (北方玄武)", "月"),
    ("室", "North", "Black Tortoise (北方玄武)", "火"),
    ("壁", "North", "Black Tortoise (北方玄武)", "水"),
    # West White Tiger
    ("奎", "West", "White Tiger (西方白虎)", "木"),
    ("婁", "West", "White Tiger (西方白虎)", "金"),
    ("胃", "West", "White Tiger (西方白虎)", "土"),
    ("昴", "West", "White Tiger (西方白虎)", "日"),
    ("畢", "West", "White Tiger (西方白虎)", "月"),
    ("觜", "West", "White Tiger (西方白虎)", "火"),
    ("參", "West", "White Tiger (西方白虎)", "水"),
    # South Vermilion Bird
    ("井", "South", "Vermilion Bird (南方朱雀)", "木"),
    ("鬼", "South", "Vermilion Bird (南方朱雀)", "金"),
    ("柳", "South", "Vermilion Bird (南方朱雀)", "土"),
    ("星", "South", "Vermilion Bird (南方朱雀)", "日"),
    ("張", "South", "Vermilion Bird (南方朱雀)", "月"),
    ("翼", "South", "Vermilion Bird (南方朱雀)", "火"),
    ("軫", "South", "Vermilion Bird (南方朱雀)", "水"),
])
def test_all_28_mansions_associations(mansion_name, expected_dir, expected_beast, expected_elem):
    engine = QiZhengSiYuEngine()
    entry = next(m for m in MANSION_TABLE if m["name"] == mansion_name)
    mid_deg = (entry["start_deg"] + entry["end_deg"]) / 2.0
    detail = engine.get_lunar_mansion_detail(mid_deg)
    assert detail["mansion"] == mansion_name
    assert detail["direction"] == expected_dir
    assert detail["beast_symbol"] == expected_beast
    assert detail["element"] == expected_elem
    assert len(detail["pinyin"]) > 0
    assert len(detail["thai"]) > 0


def test_get_lunar_mansion_boundaries():
    engine = QiZhengSiYuEngine()
    # East Azure Dragon (0 - 75)
    assert engine.get_lunar_mansion(0.0) == "角"
    assert engine.get_lunar_mansion(11.99) == "角"
    assert engine.get_lunar_mansion(12.0) == "亢"
    assert engine.get_lunar_mansion(21.0) == "氐"
    assert engine.get_lunar_mansion(36.0) == "房"
    assert engine.get_lunar_mansion(41.0) == "心"
    assert engine.get_lunar_mansion(46.0) == "尾"
    assert engine.get_lunar_mansion(64.0) == "箕"

    # North Black Tortoise (75 - 173)
    assert engine.get_lunar_mansion(75.0) == "斗"
    assert engine.get_lunar_mansion(101.0) == "牛"
    assert engine.get_lunar_mansion(109.0) == "女"
    assert engine.get_lunar_mansion(121.0) == "虛"
    assert engine.get_lunar_mansion(131.0) == "危"
    assert engine.get_lunar_mansion(148.0) == "室"
    assert engine.get_lunar_mansion(164.0) == "壁"

    # West White Tiger (173 - 253)
    assert engine.get_lunar_mansion(173.0) == "奎"
    assert engine.get_lunar_mansion(180.0) == "奎"
    assert engine.get_lunar_mansion(189.0) == "婁"
    assert engine.get_lunar_mansion(201.0) == "胃"
    assert engine.get_lunar_mansion(215.0) == "昴"
    assert engine.get_lunar_mansion(226.0) == "畢"
    assert engine.get_lunar_mansion(242.0) == "觜"
    assert engine.get_lunar_mansion(244.0) == "參"

    # South Vermilion Bird (253 - 360)
    assert engine.get_lunar_mansion(253.0) == "井"
    assert engine.get_lunar_mansion(286.0) == "鬼"
    assert engine.get_lunar_mansion(289.0) == "柳"
    assert engine.get_lunar_mansion(304.0) == "星"
    assert engine.get_lunar_mansion(311.0) == "張"
    assert engine.get_lunar_mansion(329.0) == "翼"
    assert engine.get_lunar_mansion(347.0) == "軫"
    assert engine.get_lunar_mansion(350.0) == "軫"
    assert engine.get_lunar_mansion(359.99) == "軫"


def test_degree_offset_and_percentage():
    engine = QiZhengSiYuEngine()
    # 角 span is 12.0 degrees (0 to 12). At 6.0 deg: offset = 6.0, percentage = 50.0%
    detail = engine.get_lunar_mansion_detail(6.0)
    assert detail["mansion"] == "角"
    assert detail["degree_offset"] == 6.0
    assert detail["degree_percentage"] == 50.0
    assert detail["degree_span"] == 12.0

    # 井 span is 33.0 degrees (253 to 286). At 253.0: offset = 0.0, percentage = 0.0%
    detail_jing = engine.get_lunar_mansion_detail(253.0)
    assert detail_jing["mansion"] == "井"
    assert detail_jing["degree_offset"] == 0.0
    assert detail_jing["degree_percentage"] == 0.0


def test_degree_wraparound():
    engine = QiZhengSiYuEngine()
    # 360.0 wraps to 0.0 -> 角
    assert engine.get_lunar_mansion(360.0) == "角"
    # 372.0 wraps to 12.0 -> 亢
    assert engine.get_lunar_mansion(372.0) == "亢"
    # -10.0 wraps to 350.0 -> 軫
    assert engine.get_lunar_mansion(-10.0) == "軫"


def test_calculate_basic():
    engine = QiZhengSiYuEngine()
    res = engine.calculate(2025, 1, 1, 12)
    assert isinstance(res, EngineChartResult)
    assert "planets" in res.chart_data
    assert "shadow_stars" in res.chart_data
    assert "lunar_mansions" in res.chart_data
    assert "lunar_mansion_details" in res.chart_data


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
    assert len(res.chart_data["lunar_mansion_details"]) == 11


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
    for k, v in res.chart_data["lunar_mansions"].items():
        assert v in LUNAR_MANSIONS


def test_json_serialization():
    engine = QiZhengSiYuEngine()
    res = engine.calculate(2026, 8, 15, 12)
    serialized = json.dumps(res)
    deserialized = json.loads(serialized)
    assert deserialized["engine_name"] == "Qi Zheng Si Yu Engine"
    assert deserialized["system_type"] == "chinese_astrology"
    assert "lunar_mansion_details" in deserialized

