"""
project/tests/test_api_router_external.py
==========================================
Unit & Integration tests for External AI Provider Routing in HybridRouter.
"""

from unittest.mock import MagicMock, patch

from project.api_router import HybridRouter, _call_openai_compatible


def test_build_routes_includes_external_providers():
    with patch("project.api_router.OPENAI_API_KEY", "sk-mock-openai-key"), \
         patch("project.api_router.TOGETHER_API_KEY", "mock-together-key"):
        router = HybridRouter()
        routes = router._build_routes()
        
        provider_types = [r["type"] for r in routes]
        assert "openai" in provider_types
        assert "together" in provider_types


def test_call_openai_compatible_success():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {"message": {"content": "Hello from OpenAI compatible endpoint!"}}
        ]
    }

    with patch("httpx.Client") as mock_client:
        mock_instance = MagicMock()
        mock_instance.post.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_instance

        text, reason = _call_openai_compatible(
            provider_name="TestProvider",
            base_url="https://api.test.com/v1",
            api_key="test-key",
            model="test-model",
            prompt="Hello"
        )
        assert text == "Hello from OpenAI compatible endpoint!"
        assert reason == "ok"


def test_gemini_model_rotation_and_candidate_fallback():
    from project.api_router import _call_gemini, _gemini_keys, GEMINI_MODELS_ROTATION

    assert "gemini-3.5-flash-lite" in GEMINI_MODELS_ROTATION
    assert "gemini-flash-latest" in GEMINI_MODELS_ROTATION
    assert "gemini-3.6-flash" in GEMINI_MODELS_ROTATION

    # Mock candidate fallback: first attempt (gemini-3.5-flash-lite) returns 404, second attempt (gemini-2.0-flash) returns 200
    mock_resp_404 = MagicMock()
    mock_resp_404.status_code = 404

    mock_resp_200 = MagicMock()
    mock_resp_200.status_code = 200
    mock_resp_200.json.return_value = {
        "candidates": [
            {"content": {"parts": [{"text": "คำทำนายจากโมเดล Gemini สำเร็จ"}]}}
        ]
    }

    with patch("httpx.Client") as mock_client:
        mock_instance = MagicMock()
        mock_instance.post.side_effect = [mock_resp_404, mock_resp_200]
        mock_client.return_value.__enter__.return_value = mock_instance

        text, reason = _call_gemini(
            model="gemini-3.5-flash-lite",
            api_key="AIzaSyValidMockKey123456",
            prompt="ทดสอบดวงชะตา"
        )

        assert text == "คำทำนายจากโมเดล Gemini สำเร็จ"
        assert reason == "ok"
        assert mock_instance.post.call_count == 2


def test_gemini_key_rotation_filters_invalid_keys(monkeypatch):
    from project.api_router import _gemini_keys

    monkeypatch.setenv("GOOGLE_AI_STUDIO_API_KEY", "REPLACE_WITH_KEY")
    monkeypatch.setenv("GOOGLE_AI_STUDIO_API_KEY2", "AIzaSyStudioKey2_987654321")

    valid = _gemini_keys()
    assert valid == ["AIzaSyStudioKey2_987654321"]


def test_google_ai_studio_api_keys_in_router_and_validator(monkeypatch):
    from project.api_router import _gemini_keys
    from project.validator import _get_api_keys

    monkeypatch.setenv("GOOGLE_AI_STUDIO_API_KEY", "AIzaSyStudioKey1_123456789")
    monkeypatch.setenv("GOOGLE_AI_STUDIO_API_KEY2", "AIzaSyStudioKey2_987654321")

    valid_router = _gemini_keys()
    valid_validator = _get_api_keys()

    assert valid_router == ["AIzaSyStudioKey1_123456789", "AIzaSyStudioKey2_987654321"]
    assert valid_validator == ["AIzaSyStudioKey1_123456789", "AIzaSyStudioKey2_987654321"]


def test_call_vertex_ai_success():
    from project.api_router import _call_vertex_ai

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "candidates": [
            {"content": {"parts": [{"text": "คำทำนายจากโมเดล Vertex AI สำเร็จ"}]}}
        ]
    }

    with patch("httpx.Client") as mock_client:
        mock_instance = MagicMock()
        mock_instance.post.return_value = mock_resp
        mock_client.return_value.__enter__.return_value = mock_instance

        text, reason = _call_vertex_ai(
            model="gemini-1.5-flash",
            project_id="gen-lang-client-0821704500",
            bearer_token="ya29.mock_token_123456",
            prompt="ทดสอบคำนวณดวง"
        )

        assert text == "คำทำนายจากโมเดล Vertex AI สำเร็จ"
        assert reason == "ok"
        assert mock_instance.post.call_count == 1
        call_kwargs = mock_instance.post.call_args[1]
        assert "Bearer ya29.mock_token_123456" in call_kwargs["headers"]["Authorization"]


def test_call_vertex_ai_no_auth():
    from project.api_router import _call_vertex_ai
    text, reason = _call_vertex_ai("gemini-1.5-flash", "", "", "hi")
    assert text is None
    assert reason == "no_auth"
