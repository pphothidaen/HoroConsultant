import pytest
from project.core.mian_xiang_engine import MianXiangEngine

def test_face_shape_classification():
    engine = MianXiangEngine()
    assert "Water" in engine.analyze_face_shape("round")
    assert "Metal" in engine.analyze_face_shape("oval")
    assert "Earth" in engine.analyze_face_shape("square")
    assert "Wood" in engine.analyze_face_shape("long")
    assert "Fire" in engine.analyze_face_shape("pointed")

def test_12_palaces_assessment_wide():
    engine = MianXiangEngine()
    features = {"forehead": "wide", "nose": "high", "eyebrows": "thick", "chin": "round"}
    palaces = engine.analyze_12_palaces(features)
    assert "Broad and open" in palaces["命宮 (Life Palace)"]
    assert "High nose bridge" in palaces["財帛宮 (Wealth Palace)"]
    assert "thick" in palaces["兄弟宮 (Siblings Palace)"]
    assert "round" in palaces["奴僕宮 (Servants Palace)"]

def test_12_palaces_assessment_narrow():
    engine = MianXiangEngine()
    features = {"forehead": "narrow", "nose": "wide"}
    palaces = engine.analyze_12_palaces(features)
    assert "Narrow or obstructed" in palaces["命宮 (Life Palace)"]
    assert "Wide nose" in palaces["財帛宮 (Wealth Palace)"]

def test_5_officials_analysis():
    engine = MianXiangEngine()
    features = {"ears": "large", "eyebrows": "thick", "eyes": "large", "nose": "high", "mouth": "full"}
    officials = engine.analyze_5_officials(features)
    assert "Good for listening" in officials["採聽官 (Ears)"]
    assert "Strong longevity" in officials["保壽官 (Eyebrows)"]
    assert "Good observation" in officials["監察官 (Eyes)"]
    assert "Good discernment" in officials["審辨官 (Nose)"]
    assert "Good expression" in officials["出納官 (Mouth)"]

def test_fortune_flow_age_mapping():
    engine = MianXiangEngine()
    flow = engine.get_fortune_flow(1990)
    assert "Ears" in flow["1-14"]
    assert "Forehead" in flow["15-30"]
    assert "Eyebrows" in flow["31-34"]
    assert "Eyes" in flow["35-40"]
    assert "Nose" in flow["41-50"]

def test_mole_significance():
    engine = MianXiangEngine()
    features = {"moles": [{"location": "chin", "size": "small"}, {"location": "nose", "size": "large"}]}
    result = engine.analyze(features).chart_data
    assert len(result["moles"]) == 2
    assert "chin (small)" in result["moles"][0]
    assert "nose (large)" in result["moles"][1]

def test_overall_assessment_structure():
    engine = MianXiangEngine()
    features = {"face_shape": "round"}
    result = engine.analyze(features).chart_data
    assert "Water" in result["overall_assessment"]
    assert result["face_element"] == "Water (水形) - Round, soft, fleshy"
    assert "twelve_palaces" in result
    assert "five_officials" in result

def test_calculate_with_args():
    engine = MianXiangEngine()
    result = engine.calculate({"face_shape": "oval"})
    assert "Metal" in result.chart_data["face_element"]

def test_calculate_with_kwargs():
    engine = MianXiangEngine()
    result = engine.calculate(features_dict={"face_shape": "square"}, birth_year=2000)
    assert "Earth" in result.chart_data["face_element"]
    assert "fortune_flow" in result.chart_data

def test_missing_features():
    engine = MianXiangEngine()
    result = engine.calculate({})
    assert "Unknown" in result.chart_data["face_element"]
    
def test_12_palaces_all_keys_exist():
    engine = MianXiangEngine()
    palaces = engine.analyze_12_palaces({})
    expected_keys = [
        "命宮 (Life Palace)", "財帛宮 (Wealth Palace)", "兄弟宮 (Siblings Palace)",
        "夫妻宮 (Spouse Palace)", "子女宮 (Children Palace)", "疾厄宮 (Health Palace)",
        "遷移宮 (Travel Palace)", "奴僕宮 (Servants Palace)", "官祿宮 (Career Palace)",
        "田宅宮 (Property Palace)", "福德宮 (Fortune Palace)", "父母宮 (Parents Palace)"
    ]
    for key in expected_keys:
        assert key in palaces

def test_engine_metadata():
    engine = MianXiangEngine()
    assert engine.engine_name == "Mian Xiang Physiognomy Engine"
    assert engine.system_type == "mian_xiang"
