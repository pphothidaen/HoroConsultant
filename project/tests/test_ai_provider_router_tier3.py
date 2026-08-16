"""
project/tests/test_ai_provider_router_tier3.py
==============================================
Unit tests for Tier 3 Reasoning Proxy & Multi-Tier Routing in AIProviderRouter.
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from project.core.ai_provider_router import AIProviderRouter


def test_provider_health_includes_reasoning_proxy():
    router = AIProviderRouter(reasoning_base_url="https://api.9router.com/v1", reasoning_model="deepseek-r1")
    health = router.get_provider_health()

    assert "REASONING_PROXY" in health
    assert health["REASONING_PROXY"]["configured"] is True
    assert health["REASONING_PROXY"]["available"] is True
    assert health["REASONING_PROXY"]["model"] == "deepseek-r1"
    assert health["REASONING_PROXY"]["base_url"] == "https://api.9router.com/v1"
    assert health["routing"]["reasoning"] == "reasoning_proxy"


def test_invoke_reasoning_proxy_unconfigured():
    router = AIProviderRouter(reasoning_base_url="")
    res = router.invoke_reasoning_proxy(prompt="Analyze BaZi chart")
    assert res["status"] == "error"
    assert res["error_type"] == "unconfigured"


def test_invoke_reasoning_proxy_success():
    router = AIProviderRouter(reasoning_base_url="https://api.9router.com/v1", reasoning_model="deepseek-r1")

    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps({
        "choices": [{
            "message": {
                "role": "assistant",
                "content": "DeepSeek-R1 CoT Domain Synthesis: Balanced 5-Elements.",
            }
        }]
    }).encode("utf-8")
    mock_response.__enter__.return_value = mock_response

    with patch("urllib.request.urlopen", return_value=mock_response):
        res = router.invoke_reasoning_proxy(prompt="Analyze BaZi chart", system_prompt="Expert Astrologer")
        assert res["status"] == "success"
        assert res["provider"] == "REASONING_PROXY"
        assert res["model"] == "deepseek-r1"
        assert "DeepSeek-R1" in res["content"]


def test_call_ai_prefer_reasoning():
    router = AIProviderRouter(reasoning_base_url="https://api.9router.com/v1", reasoning_model="deepseek-r1")

    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps({
        "choices": [{
            "message": {
                "role": "assistant",
                "content": "Tier 3 Reasoning Synthesis Output",
            }
        }]
    }).encode("utf-8")
    mock_response.__enter__.return_value = mock_response

    with patch("urllib.request.urlopen", return_value=mock_response):
        res = router.call_ai(prompt="Deep inquiry", prefer_reasoning=True)
        assert res["status"] == "success"
        assert res["provider"] == "REASONING_PROXY"
        assert res["content"] == "Tier 3 Reasoning Synthesis Output"


def test_call_ai_codex_fail_routes_to_reasoning_proxy():
    router = AIProviderRouter(
        primary_provider="codex_chatgpt",
        reasoning_base_url="https://api.9router.com/v1",
        reasoning_model="deepseek-r1",
    )

    # Mock codex failure
    def mock_codex_fail(*args, **kwargs):
        return {
            "status": "error",
            "provider": "CODEX_CHATGPT",
            "model": "codex_chatgpt",
            "content": "",
            "raw_response": None,
            "error_message": "Codex CLI unavailable",
            "error_type": "command_not_found",
            "route_used": "codex_chatgpt",
        }

    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps({
        "choices": [{
            "message": {
                "role": "assistant",
                "content": "Reasoning Proxy Fallback Output",
            }
        }]
    }).encode("utf-8")
    mock_response.__enter__.return_value = mock_response

    with patch.object(router, "invoke_codex_chatgpt", mock_codex_fail):
        with patch("urllib.request.urlopen", return_value=mock_response):
            res = router.call_ai(prompt="Query")
            assert res["status"] == "success"
            assert res["provider"] == "REASONING_PROXY"
            assert res["content"] == "Reasoning Proxy Fallback Output"
