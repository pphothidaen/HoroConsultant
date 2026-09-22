"""KAN-81: Failover chain verification (Gemini Bridge -> Cloudflare AI -> local model).

Per spec (docs/gemini-bridge-mcp-toggle.md §6.2), the bridge is route 1 — every
failure must fall through to the legacy chain:
  1. gemini_mcp route (call_bridge_tool)
  2. Ollama qwen2.5:7b
  3. Gemini API
  4. Cloudflare AI
  5. chat template path (fail-closed)

Tests verify that a bridge failure produces the correct attempted_routes and
that the next route in the chain is selected.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

import project.api_router as api_router_module
import project.core.gemini_bridge_client as gbc
from project.api_router import HybridRouter

QUERY = "ถามดวงวันเกิด"
BRIDGE_ENV_KEYS = (
    "GEMINI_WEB_BRIDGE_ENABLED",
    "GEMINI_WEB_BRIDGE_URL",
    "GEMINI_WEB_BRIDGE_TOKEN",
    "GEMINI_WEB_BRIDGE_SCOPE",
    "GEMINI_WEB_BRIDGE_TOOL",
    "GEMINI_WEB_BRIDGE_TIMEOUT_S",
)
_CLEAR_ENV_KEYS = (
    "VERCEL", "VERCEL_ENV", "SPACE_ID", "FLY_APP_NAME",
    "HF_SPACE_ID", "RAILWAY_STATIC_URL", "ENVIRONMENT",
    "DISABLE_LOCAL_OLLAMA", "AI_ZERO_COST_ONLY",
    "CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_AI_TOKEN",
    "GOOGLE_AI_STUDIO_API_KEY", "GOOGLE_AI_STUDIO_API_KEY2",
)
ALL_ENV_KEYS = BRIDGE_ENV_KEYS + _CLEAR_ENV_KEYS


def _clear_env(monkeypatch) -> None:
    for key in ALL_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    # Clear module-level cloud env vars captured at import
    monkeypatch.setattr(api_router_module, "CLOUDFLARE_ACCOUNT_ID", "")
    monkeypatch.setattr(api_router_module, "CLOUDFLARE_AI_TOKEN", "")
    monkeypatch.setattr(api_router_module, "_gemini_keys", lambda: [])


def _enable_bridge(monkeypatch) -> None:
    _clear_env(monkeypatch)
    monkeypatch.setenv("GEMINI_WEB_BRIDGE_ENABLED", "true")
    monkeypatch.setenv("GEMINI_WEB_BRIDGE_TOKEN", "failover-test-tok")


@pytest.fixture(autouse=True)
def _hermetic_env(monkeypatch):
    _clear_env(monkeypatch)
    gbc._BRIDGE_CIRCUIT_BREAKER.clear()
    yield
    gbc._BRIDGE_CIRCUIT_BREAKER.clear()


def _http_mock(json_data=None, status_code: int = 200, post_side_effect=None):
    mock_client = MagicMock()
    mock_instance = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = json_data
    if post_side_effect is not None:
        mock_instance.post.side_effect = post_side_effect
    else:
        mock_instance.post.return_value = mock_resp
    mock_client.return_value.__enter__.return_value = mock_instance
    return mock_client, mock_instance


# ---------------------------------------------------------------------------
# Bridge failure -> falls through to next route
# ---------------------------------------------------------------------------

def test_bridge_failure_falls_through_to_ollama(monkeypatch):
    """Bridge 503 -> next route (Ollama) is selected."""
    _enable_bridge(monkeypatch)
    monkeypatch.setattr(
        api_router_module,
        "call_bridge_tool",
        MagicMock(return_value=(None, "http_503")),
    )
    monkeypatch.setattr(
        api_router_module,
        "_call_ollama",
        lambda model, prompt, system_instruction: ("ollama-response", "ok"),
    )

    result = HybridRouter().generate(QUERY, "system")

    assert result["text"] == "ollama-response"
    assert result["route"] == "ollama"
    assert len(result["attempted_routes"]) == 1
    assert result["attempted_routes"][0]["reason"] == "http_503"
    assert "gemini-mcp" in result["attempted_routes"][0]["route"]


def test_bridge_timeout_falls_through(monkeypatch):
    """Bridge timeout -> falls through to next route."""
    _enable_bridge(monkeypatch)
    monkeypatch.setattr(
        api_router_module,
        "call_bridge_tool",
        MagicMock(return_value=(None, "timeout")),
    )
    monkeypatch.setattr(
        api_router_module,
        "_call_ollama",
        lambda model, prompt, system_instruction: ("ollama-after-timeout", "ok"),
    )

    result = HybridRouter().generate(QUERY)
    assert result["text"] == "ollama-after-timeout"
    assert result["route"] == "ollama"
    assert result["attempted_routes"][0]["reason"] == "timeout"


def test_bridge_circuit_open_falls_through(monkeypatch):
    """Bridge circuit_open reason -> falls through."""
    _enable_bridge(monkeypatch)
    monkeypatch.setattr(
        api_router_module,
        "call_bridge_tool",
        MagicMock(return_value=(None, "circuit_open")),
    )
    monkeypatch.setattr(
        api_router_module,
        "_call_ollama",
        lambda model, prompt, system_instruction: ("local-fallback", "ok"),
    )

    result = HybridRouter().generate(QUERY)
    assert result["text"] == "local-fallback"
    assert result["route"] == "ollama"


# ---------------------------------------------------------------------------
# Bridge failure with multiple fallback routes
# ---------------------------------------------------------------------------

def test_bridge_failure_with_cloudflare_ai_fallback(monkeypatch):
    """Bridge fails -> Ollama fails -> Cloudflare AI succeeds."""
    _enable_bridge(monkeypatch)

    # Configure cloudflare env
    monkeypatch.setattr(api_router_module, "CLOUDFLARE_ACCOUNT_ID", "fake-account")
    monkeypatch.setattr(api_router_module, "CLOUDFLARE_AI_TOKEN", "fake-cf-token")
    # Enable cloudflare routes
    monkeypatch.setenv("CLOUDFLARE_ACCOUNT_ID", "fake-account")
    monkeypatch.setenv("CLOUDFLARE_AI_TOKEN", "fake-cf-token")

    monkeypatch.setattr(
        api_router_module,
        "call_bridge_tool",
        MagicMock(return_value=(None, "http_503")),
    )
    monkeypatch.setattr(
        api_router_module,
        "_call_ollama",
        lambda model, prompt, system_instruction: (None, "error"),
    )
    monkeypatch.setattr(
        api_router_module,
        "_call_cloudflare_ai",
        lambda account_id, key, model, prompt, system_instruction: ("cloudflare-response", "ok"),
    )

    result = HybridRouter().generate(QUERY)
    assert result["text"] == "cloudflare-response"
    assert result["route"] == "cloudflare_ai"
    # Should have bridge + all 3 ollama routes in attempted
    assert len(result["attempted_routes"]) == 4
    reasons = [r["reason"] for r in result["attempted_routes"]]
    assert "http_503" in reasons
    assert reasons.count("error") == 3


# ---------------------------------------------------------------------------
# All routes fail -> exhausted
# ---------------------------------------------------------------------------

def test_all_routes_fail_returns_exhausted(monkeypatch):
    """When bridge + all fallbacks fail, result is exhausted."""
    _enable_bridge(monkeypatch)
    monkeypatch.setattr(
        api_router_module,
        "call_bridge_tool",
        MagicMock(return_value=(None, "http_503")),
    )
    monkeypatch.setattr(
        api_router_module,
        "_call_ollama",
        lambda model, prompt, system_instruction: (None, "error"),
    )

    result = HybridRouter().generate(QUERY)
    assert result["route"] == "exhausted"
    assert result["reason"] == "all_routes_failed"
    assert result["text"] is None


# ---------------------------------------------------------------------------
# Bridge success -> no fallback attempted
# ---------------------------------------------------------------------------

def test_bridge_success_no_fallback_attempted(monkeypatch):
    """Bridge succeeds -> route is gemini_mcp, no attempted_routes."""
    _enable_bridge(monkeypatch)
    bridge_mock = MagicMock(return_value=({"text": "bridge-text", "pdf_url": None}, "ok"))
    monkeypatch.setattr(api_router_module, "call_bridge_tool", bridge_mock)

    result = HybridRouter().generate(QUERY, "sys")

    assert result["text"] == "bridge-text"
    assert result["route"] == "gemini_mcp"
    assert result["attempted_routes"] == []


# ---------------------------------------------------------------------------
# Attempted routes record chain order
# ---------------------------------------------------------------------------

def test_attempted_routes_record_full_chain_order(monkeypatch):
    """Bridge fails -> Ollama fails -> Cloudflare AI fails -> exhausted.
    attempted_routes records each failure in order."""
    _enable_bridge(monkeypatch)
    monkeypatch.setattr(api_router_module, "CLOUDFLARE_ACCOUNT_ID", "fake-account")
    monkeypatch.setattr(api_router_module, "CLOUDFLARE_AI_TOKEN", "fake-cf-token")
    monkeypatch.setenv("CLOUDFLARE_ACCOUNT_ID", "fake-account")
    monkeypatch.setenv("CLOUDFLARE_AI_TOKEN", "fake-cf-token")

    monkeypatch.setattr(
        api_router_module,
        "call_bridge_tool",
        MagicMock(return_value=(None, "http_429")),
    )
    monkeypatch.setattr(
        api_router_module,
        "_call_ollama",
        lambda model, prompt, system_instruction: (None, "error"),
    )
    monkeypatch.setattr(
        api_router_module,
        "_call_cloudflare_ai",
        lambda account_id, key, model, prompt, system_instruction: (None, "error"),
    )

    result = HybridRouter().generate(QUERY)
    assert result["route"] == "exhausted"
    # Should have bridge + ollama + cloudflare in attempted
    assert len(result["attempted_routes"]) >= 2
    # First attempted is bridge
    assert "gemini-mcp" in result["attempted_routes"][0]["route"]
    assert result["attempted_routes"][0]["reason"] == "http_429"
