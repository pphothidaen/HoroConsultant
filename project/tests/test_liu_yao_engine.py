import pytest

from project.core.liu_yao_engine import LiuYaoEngine, liu_yao_najia, liu_yao_five_relatives

def test_rust_najia_qian():
    # Qian (7) Lower -> Zi(0), Yin(2), Chen(4)
    assert liu_yao_najia(7, False) == [0, 2, 4]
    # Qian (7) Upper -> Wu(6), Shen(8), Xu(10)
    assert liu_yao_najia(7, True) == [6, 8, 10]

def test_rust_najia_kun():
    # Kun (0) Lower -> Wei(7), Si(5), Mao(3)
    assert liu_yao_najia(0, False) == [7, 5, 3]
    # Kun (0) Upper -> Chou(1), Hai(11), You(9)
    assert liu_yao_najia(0, True) == [1, 11, 9]

def test_rust_najia_kan():
    # Kan (2) Lower -> Yin(2), Chen(4), Wu(6)
    assert liu_yao_najia(2, False) == [2, 4, 6]
    # Kan (2) Upper -> Shen(8), Xu(10), Zi(0)
    assert liu_yao_najia(2, True) == [8, 10, 0]

def test_rust_five_relatives_same():
    # Wood(0) and Wood(0) -> Sibling (兄弟)
    assert liu_yao_five_relatives(0, 0) == "兄弟"

def test_rust_five_relatives_generates():
    # Day generates Line: Day Water(4) generates Line Wood(0) -> Offspring (子孫)
    assert liu_yao_five_relatives(0, 4) == "子孫"

def test_rust_five_relatives_generated_by():
    # Line generates Day: Line Fire(1) generates Day Earth(2) -> Parent (父母)
    assert liu_yao_five_relatives(1, 2) == "父母"

def test_rust_five_relatives_controls():
    # Day controls Line: Day Metal(3) controls Line Wood(0) -> Wife-Wealth (妻財)
    assert liu_yao_five_relatives(0, 3) == "妻財"

def test_rust_five_relatives_controlled_by():
    # Line controls Day: Line Fire(1) controls Day Metal(3) -> Officer-Ghost (官鬼)
    assert liu_yao_five_relatives(1, 3) == "官鬼"

def test_liu_yao_engine_basic_qian():
    engine = LiuYaoEngine()
    # All young yang (7) -> 111, 111 (Qian)
    res = engine.calculate([7, 7, 7, 7, 7, 7])
    data = res.chart_data
    assert data["palace"] == "乾"
    assert data["palace_element"] == "金"
    assert data["shi_line"] == 6
    assert data["ying_line"] == 3
    assert data["lines"][0]["branch"] == "子"
    assert data["lines"][5]["branch"] == "戌"
    assert not data["lines"][0]["is_moving"]

def test_liu_yao_engine_moving_line():
    engine = LiuYaoEngine()
    # 6 is old yin -> moving (flips to yang -> Qian lower which starts with Zi(0))
    res = engine.calculate([6, 7, 7, 7, 7, 7])
    data = res.chart_data
    assert data["lines"][0]["is_moving"] is True
    assert data["lines"][0]["transformed"]["branch"] == "子"

def test_liu_yao_engine_six_animals_jia():
    engine = LiuYaoEngine()
    # Jia Day (0) starts with Qing Long
    res = engine.calculate([7, 7, 7, 7, 7, 7], day_stem_idx=0)
    lines = res.chart_data["lines"]
    assert lines[0]["animal"] == "青龍"
    assert lines[1]["animal"] == "朱雀"
    assert lines[2]["animal"] == "勾陳"
    assert lines[3]["animal"] == "螣蛇"
    assert lines[4]["animal"] == "白虎"
    assert lines[5]["animal"] == "玄武"

def test_liu_yao_engine_six_animals_bing():
    engine = LiuYaoEngine()
    # Bing Day (2) starts with Zhu Que
    res = engine.calculate([7, 7, 7, 7, 7, 7], day_stem_idx=2)
    lines = res.chart_data["lines"]
    assert lines[0]["animal"] == "朱雀"
    assert lines[1]["animal"] == "勾陳"
    assert lines[5]["animal"] == "青龍"

def test_liu_yao_engine_palace_youhun():
    engine = LiuYaoEngine()
    # Huo Di Jin: Li (101) over Kun (000) -> Youhun of Qian
    # Lines: 000 101 -> 8, 8, 8, 7, 8, 7
    res = engine.calculate([8, 8, 8, 7, 8, 7])
    data = res.chart_data
    assert data["palace"] == "乾"
    assert data["shi_line"] == 4

def test_liu_yao_engine_palace_guihun():
    engine = LiuYaoEngine()
    # Huo Tian Da You: Li (101) over Qian (111) -> Guihun of Qian
    res = engine.calculate([7, 7, 7, 7, 8, 7])
    data = res.chart_data
    assert data["palace"] == "乾"
    assert data["shi_line"] == 3

def test_liu_yao_engine_five_relatives():
    engine = LiuYaoEngine()
    # Qian palace is Metal (3).
    # Bottom line is Zi(Water=4). Metal generates Water -> Offspring
    res = engine.calculate([7, 7, 7, 7, 7, 7])
    assert res.chart_data["lines"][0]["relative"] == "子孫"
    # 2nd line is Yin(Wood=0). Metal controls Wood -> Wife-Wealth
    assert res.chart_data["lines"][1]["relative"] == "妻財"

def test_liu_yao_engine_validation():
    engine = LiuYaoEngine()
    with pytest.raises(ValueError):
        engine.calculate([7, 7, 7]) # not 6 lines
