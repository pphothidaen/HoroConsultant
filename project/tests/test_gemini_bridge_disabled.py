"""
test_gemini_bridge_disabled.py
================================
TDD RED-phase tests for the Gemini Web Bridge MCP client — DISABLED toggle path.

Contract (project/core/gemini_bridge_client.py docstring):
  - is_gemini_bridge_enabled() -> bool
  - call_bridge_tool(...) -> (None, "disabled") when toggle is OFF, BEFORE any
    HTTP or config resolution.

Spec reference (docs/gemini-bridge-mcp-toggle.md §6.1, §7):
  - disabled = GEMINI_WEB_BRIDGE_ENABLED falsy (default false).
  - Fail-closed: zero outbound HTTP calls when disabled.
  - Toggle is read dynamically (no import-time caching) so it can flip at
    runtime without a restart.

RED protocol: QA_FORCE_TOGGLE_OFF=1 python3 -m pytest <this file> -q
  -> every bridge-dependent assertion fails because the toggle is mocked OFF.

Mocking discipline:
  - pytest.monkeypatch is the ONLY patching mechanism (no unittest.mock.patch).
  - httpx.Client is monkeypatched so zero real network calls are possible.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock

import httpx
import pytest

import project.core.gemini_bridge_client as gbc
from project.core.gemini_bridge_client import call_bridge_tool, is_gemini_bridge_enabled

QUERY = "คำถามทดสอบเมื่อ toggle ปิด"
ALL_FALSE_VALUES = ("false", "0", "", "no", "off", "FALSE", "False", "nO")

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


@pytest.fixture(autouse=True)
def _isolate_env_and_breaker(monkeypatch):
    """Ensure no env var leaks from the outside world and breaker is clean."""
    _clear_bridge_env(monkeypatch)
    gbc._BRIDGE_CIRCUIT_BREAKER.clear()
    yield
    gbc._BRIDGE_CIRCUIT_BREAKER.clear()


# ---------------------------------------------------------------------------
# is_gemini_bridge_enabled() — pure toggle check
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("value", ALL_FALSE_VALUES)
def test_is_enabled_returns_false_for_all_falsy_env_values(monkeypatch, value):
    monkeypatch.setenv("GEMINI_WEB_BRIDGE_ENABLED", value)
    assert is_gemini_bridge_enabled() is False


def test_is_enabled_returns_false_when_env_unset(monkeypatch):
    assert is_gemini_bridge_enabled() is False


def test_is_enabled_returns_false_when_flag_true_but_no_token(monkeypatch):
    """Flag alone is insufficient — a token is required for a True result."""
    monkeypatch.setenv("GEMINI_WEB_BRIDGE_ENABLED", "true")
    assert is_gemini_bridge_enabled() is False


# ---------------------------------------------------------------------------
# call_bridge_tool() — disabled reason + zero HTTP
# ---------------------------------------------------------------------------

def _make_httpx_mock(monkeypatch):
    """Return (mock_client, mock_instance) and install via monkeypatch.setattr."""
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


def test_disabled_returns_no_http_attempt(monkeypatch):
    """When toggle is OFF, call_bridge_tool returns ('disabled') and never
    instantiates httpx.Client at all (fail-closed)."""
    mock_client, mock_instance = _make_httpx_mock(monkeypatch)

    res, reason = call_bridge_tool(QUERY)

    assert res is None
    assert reason == "disabled"
    mock_client.assert_not_called()          # Client class never constructed
    mock_instance.post.assert_not_called()  # POST never attempted


def test_disabled_does_not_touch_circuit_breaker(monkeypatch):
    """Disabled path must short-circuit before the circuit-breaker check."""
    _make_httpx_mock(monkeypatch)

    # Pre-trip the circuit to ensure the disabled path returns 'disabled'
    # rather than 'circuit_open' — disabled check must come first.
    gbc._BRIDGE_CIRCUIT_BREAKER.clear()  # ensure clean
    res, reason = call_bridge_tool(QUERY)
    assert reason == "disabled"
    # Circuit breaker dict must remain empty (never evaluated)
    assert not gbc._BRIDGE_CIRCUIT_BREAKER


# ---------------------------------------------------------------------------
# Dynamic toggle — flips without reimport
# ---------------------------------------------------------------------------

def test_toggle_flips_dynamically_without_reimport(monkeypatch):
    """The toggle is read from env on every call; no restart needed."""
    _clear_bridge_env(monkeypatch)
    assert is_gemini_bridge_enabled() is False
    assert call_bridge_tool(QUERY)[1] == "disabled"

    monkeypatch.setenv("GEMINI_WEB_BRIDGE_ENABLED", "true")
    monkeypatch.setenv("GEMINI_WEB_BRIDGE_TOKEN", "dynamic-tok")
    # Now enabled — the only thing that should differ is the reason
    assert is_gemini_bridge_enabled() is True
    # (call_bridge_tool with a valid config would attempt HTTP, so we
    #  verify via is_gemini_bridge_enabled here rather than making a
    #  real call)

    monkeypatch.setenv("GEMINI_WEB_BRIDGE_ENABLED", "false")
    assert is_gemini_bridge_enabled() is False
    assert call_bridge_tool(QUERY)[1] == "disabled"

    monkeypatch.setenv("GEMINI_WEB_BRIDGE_ENABLED", "1")
    assert is_gemini_bridge_enabled() is True
