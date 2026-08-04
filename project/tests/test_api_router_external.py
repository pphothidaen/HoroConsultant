"""
project/tests/test_api_router_external.py
==========================================
Unit & Integration tests for External AI Provider Routing in HybridRouter.
"""

from unittest.mock import patch, MagicMock
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
