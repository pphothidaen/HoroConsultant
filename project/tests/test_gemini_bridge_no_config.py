"""
test_gemini_bridge_no_config.py
=================================
TDD RED-phase tests for the Gemini Web Bridge MCP client — NO_CONFIG path.

Contract (project/core/gemini_bridge_client.py docstring):
  - call_bridge_tool(...) -> (None, "no_config") when the toggle is ON but
    the URL or TOKEN is missing. Must happen BEFORE any HTTP attempt.

Spec reference (docs/gemini-bridge-mcp-toggle.md §6, §6.2):
  - no_config = URL หรือ token ไม่ครบ (URL or token incomplete).
  - Fail-closed: zero outbound HTTP calls when not fully configured.
  - Every failure (including no_config) must fall through to the legacy
    HybridRouter chain without side effects.

Mocking discipline:
  - pytest.monkeypatch is the ONLY patching mechanism.
  - httpx.Client is monkeypatched so zero real network calls occur.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import httpx
import pytest

import project.core.gemini_bridge_client as gbc
from project.core.gemini_bridge_client import call_bridge_tool, is_gemini_bridge_enabled

QUERY = "คำถามทดสอบเมื่อ toggle เปิดแต่ไม่มี token"
BRIDGE_ENV_KEYS = (
    "GEMINI_WEB_BRIDGE_ENABLED",
    "GEMINI_WEB_BRIDGE_URL",
    "GEMINI_WEB_BRIDGE_TOKEN",
    "GEMINI_WEB_BRIDGE_SCOPE",
    "GEMINI_WEB_BRIDGE_TOOL",
    "GEMINI_WEB_BRIDGE_TIMEOUT_S",
)


def _clear_bridge_env(monkeypatch) -> None:
    for key in BRIDGE_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def _enable_flag_only(monkeypatch) -> None:
    """Turn the toggle ON but leave URL/TOKEN unset."""
    _clear_bridge_env(monkeypatch)
    monkeypatch.setenv("GEMINI_WEB_BRIDGE_ENABLED", "true")


@pytest.fixture(autouse=True)
def _isolate_env_and_breaker(monkeypatch):
    _clear_bridge_env(monkeypatch)
    gbc._BRIDGE_CIRCUIT_BREAKER.clear()
    yield
    gbc._BRIDGE_CIRCUIT_BREAKER.clear()


def _make_httpx_mock(monkeypatch):
    mock_client = MagicMock()
    mock_instance = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"jsonrpc": "2.0", "id": 1,
                                   "result": {"content": [{"type": "text", "text": "ok"}]}}
    mock_instance.post.return_value = mock_resp
    mock_client.return_value.__enter__.return_value = mock_instance
    monkeypatch.setattr(httpx, "Client", mock_client)
    return mock_client, mock_instance


# ---------------------------------------------------------------------------
# no_config reason — toggle ON but token missing
# ---------------------------------------------------------------------------

def test_no_config_when_enabled_without_token(monkeypatch):
    """Flag on + URL present (default) but TOKEN empty → (None, 'no_config')."""
    _enable_flag_only(monkeypatch)
    mock_client, mock_instance = _make_httpx_mock(monkeypatch)

    res, reason = call_bridge_tool(QUERY)

    assert res is None
    assert reason == "no_config"
    mock_client.assert_not_called()
    mock_instance.post.assert_not_called()


def test_no_config_when_enabled_without_url(monkeypatch):
    """Flag on + TOKEN set but URL explicitly empty → (None, 'no_config')."""
    _clear_bridge_env(monkeypatch)
    monkeypatch.setenv("GEMINI_WEB_BRIDGE_ENABLED", "true")
    monkeypatch.setenv("GEMINI_WEB_BRIDGE_TOKEN", "some-token")
    monkeypatch.setenv("GEMINI_WEB_BRIDGE_URL", "")  # force empty

    mock_client, mock_instance = _make_httpx_mock(monkeypatch)

    res, reason = call_bridge_tool(QUERY)

    assert res is None
    assert reason == "no_config"
    mock_client.assert_not_called()


def test_no_config_when_enabled_but_both_url_and_token_missing(monkeypatch):
    """Flag on but no URL env override + no token → (None, 'no_config')."""
    _enable_flag_only(monkeypatch)
    # URL will fall back to default (non-empty), token is empty → no_config
    mock_client, mock_instance = _make_httpx_mock(monkeypatch)

    res, reason = call_bridge_tool(QUERY)

    assert res is None
    assert reason == "no_config"
    mock_client.assert_not_called()


def test_is_gemini_bridge_enabled_false_without_token(monkeypatch):
    """is_gemini_bridge_enabled() must be False when token is missing
    even if the flag is ON."""
    _enable_flag_only(monkeypatch)
    assert is_gemini_bridge_enabled() is False


def test_is_gemini_bridge_enabled_false_without_url(monkeypatch):
    """is_gemini_bridge_enabled() must be False when URL resolves to empty
    even if the flag and token are set."""
    _clear_bridge_env(monkeypatch)
    monkeypatch.setenv("GEMINI_WEB_BRIDGE_ENABLED", "true")
    monkeypatch.setenv("GEMINI_WEB_BRIDGE_TOKEN", "tok")
    # _bridge_url() falls back to default when env unset, so set a non-empty
    # value then blank it to verify the empty-string path
    monkeypatch.setenv("GEMINI_WEB_BRIDGE_URL", "   ")  # whitespace only
    assert is_gemini_bridge_enabled() is False


# ---------------------------------------------------------------------------
# no_config does not trip circuit breaker
# ---------------------------------------------------------------------------

def test_no_config_does_not_trip_circuit_breaker(monkeypatch):
    """A no_config failure is a configuration problem, not a bridge outage —
    the circuit breaker must NOT trip."""
    _enable_flag_only(monkeypatch)
    _make_httpx_mock(monkeypatch)

    assert gbc._BRIDGE_CIRCUIT_BREAKER == {}
    call_bridge_tool(QUERY)
    assert gbc._BRIDGE_CIRCUIT_BREAKER == {}


def test_no_config_does_not_block_subsequent_disabled_check(monkeypatch):
    """After a no_config failure the breaker is untouched, so a subsequent
    disabled call still returns 'disabled' (not 'circuit_open')."""
    _enable_flag_only(monkeypatch)
    _make_httpx_mock(monkeypatch)

    _, reason1 = call_bridge_tool(QUERY)
    assert reason1 == "no_config"

    # Now turn the toggle fully off
    _clear_bridge_env(monkeypatch)
    _, reason2 = call_bridge_tool(QUERY)
    assert reason2 == "disabled"
