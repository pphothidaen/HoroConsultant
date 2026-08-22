from pathlib import Path

import pytest

from scripts.mian_xiang_vision import _json_from_text, analyze_image, normalize_features


def test_normalize_features_limits_contract_and_moles():
    result = normalize_features({"face_shape": " ROUND ", "moles": [{"location": "forehead", "size": "small", "extra": "drop"}]})
    assert result["face_shape"] == "round"
    assert result["moles"] == [{"location": "forehead", "size": "small"}]
    assert set(result) == {"face_shape", "forehead", "eyebrows", "eyes", "nose", "mouth", "ears", "chin", "moles"}


def test_json_from_text_accepts_fenced_model_output():
    assert _json_from_text('```json\n{"face_shape":"oval"}\n```')["face_shape"] == "oval"


def test_analyze_image_without_key_is_explicit_and_does_not_call_network(tmp_path: Path, monkeypatch):
    image = tmp_path / "face.png"
    image.write_bytes(b"not-a-real-image")
    monkeypatch.delenv("GOOGLE_AI_STUDIO_API_KEY", raising=False)
    result = analyze_image(image, api_key="")
    assert result["status"] == "needs_api_key"
    assert result["source"] == "none"


def test_analyze_image_rejects_unsupported_type(tmp_path: Path):
    image = tmp_path / "face.txt"
    image.write_text("x", encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported image type"):
        analyze_image(image)
