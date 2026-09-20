"""
project/tests/test_gemini_bridge_client.py
==========================================
TDD baseline tests for the Gemini Web Bridge MCP client
(project/core/gemini_bridge_client.py).

Ticket: TICKET-GEMINI-BRIDGE-20260921-A4-QA-PROVENANCE

RED/GREEN protocol (qa-regression-provenance):
  - RED run  : QA_FORCE_BRIDGE_TOGGLE_OFF=1 python3 -m pytest <this file>
               <toggle-file> -q
               -> the toggle-on (bridge-dependent) assertions must FAIL while
                  the toggle stays mocked OFF.
  - GREEN run: python3 -m pytest <this file> <toggle-file> -q
               -> toggle mocked ON + mocked HTTP, all pass.

The toggle is controlled ONLY via monkeypatch inside each test (runs after
import, so it wins over project/api_router.py's load_dotenv(override=True)).
ALL HTTP is mocked with unittest.mock.patch("httpx.Client") mirroring
project/tests/test_api_router_external.py. No real network calls are made.
"""

from __future__ import annotations

import os
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import httpx
import pytest

import project.core.gemini_bridge_client as gbc
from project.core.gemini_bridge_client import (
    GEMINI_BRIDGE_DEFAULT_SCOPE,
    GEMINI_BRIDGE_DEFAULT_TIMEOUT_S,
    GEMINI_BRIDGE_DEFAULT_URL,
    call_bridge_tool,
    is_gemini_bridge_enabled,
)

# ---------------------------------------------------------------------------
# RED/GREEN switch: when set at test-module import time, _enable_bridge()
# leaves the toggle OFF so bridge-on assertions fail (RED baseline).
# ---------------------------------------------------------------------------

QA_FORCE_TOGGLE_OFF = os.getenv("QA_FORCE_BRIDGE_TOGGLE_OFF", "0") == "1"

FAKE_TOKEN = "qa-fake-bridge-token-1234567890"
BRIDGE_QUERY = "คำถามทดสอบดวงชะตา"

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


def _enable_bridge(monkeypatch, token: str | None = FAKE_TOKEN) -> None:
    """Clear bridge env then enable the toggle (unless RED mode forces off)."""
    _clear_bridge_env(monkeypatch)
    if QA_FORCE_TOGGLE_OFF:
        return
    monkeypatch.setenv("GEMINI_WEB_BRIDGE_ENABLED", "true")
    if token is not None:
        monkeypatch.setenv("GEMINI_WEB_BRIDGE_TOKEN", token)


@pytest.fixture(autouse=True)
def _reset_circuit_breaker():
    """Circuit breaker state is a module-global dict; isolate every test."""
    gbc._BRIDGE_CIRCUIT_BREAKER.clear()
    yield
    gbc._BRIDGE_CIRCUIT_BREAKER.clear()


def _http_mock(json_data=None, status_code: int = 200, post_side_effect=None):
    """Mirror the httpx.Client mock pattern from test_api_router_external.py."""
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


def _rpc_ok(text: str = "bridge answer", structured=None, content=None) -> dict:
    if content is None:
        content = [{"type": "text", "text": text}]
    result: dict = {"content": content}
    if structured is not None:
        result["structuredContent"] = structured
    return {"jsonrpc": "2.0", "id": 1, "result": result}


# ---------------------------------------------------------------------------
# Reason mapping
# ---------------------------------------------------------------------------

def test_disabled_reason_when_toggle_off(monkeypatch):
    _clear_bridge_env(monkeypatch)
    mock_client, mock_instance = _http_mock(json_data=_rpc_ok())
    with patch("httpx.Client", mock_client):
        res, reason = call_bridge_tool(BRIDGE_QUERY)
    assert res is None
    assert reason == "disabled"
    # No HTTP attempt may happen while disabled
    mock_instance.post.assert_not_called()


def test_no_config_reason_when_enabled_without_token(monkeypatch):
    _enable_bridge(monkeypatch, token=None)
    mock_client, mock_instance = _http_mock(json_data=_rpc_ok())
    with patch("httpx.Client", mock_client):
        res, reason = call_bridge_tool(BRIDGE_QUERY)
    assert res is None
    assert reason == "no_config"
    mock_instance.post.assert_not_called()


@pytest.mark.parametrize("status_code", [503, 401, 422, 429])
def test_http_status_reason_mapping(monkeypatch, status_code):
    _enable_bridge(monkeypatch)
    mock_client, _ = _http_mock(json_data=_rpc_ok(), status_code=status_code)
    with patch("httpx.Client", mock_client):
        res, reason = call_bridge_tool(BRIDGE_QUERY)
    assert res is None
    assert reason == f"http_{status_code}"


def test_timeout_reason(monkeypatch):
    _enable_bridge(monkeypatch)
    mock_client, _ = _http_mock(post_side_effect=httpx.TimeoutException("read timed out"))
    with patch("httpx.Client", mock_client):
        res, reason = call_bridge_tool(BRIDGE_QUERY)
    assert res is None
    assert reason == "timeout"


def test_empty_response_reason_when_content_has_no_text(monkeypatch):
    _enable_bridge(monkeypatch)
    mock_client, _ = _http_mock(json_data=_rpc_ok(content=[]))
    with patch("httpx.Client", mock_client):
        res, reason = call_bridge_tool(BRIDGE_QUERY)
    assert res is None
    assert reason == "empty_response"


def test_jsonrpc_error_object_maps_to_error_detail(monkeypatch):
    _enable_bridge(monkeypatch)
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "error": {"code": -32000, "message": "extension not connected"},
    }
    mock_client, _ = _http_mock(json_data=payload)
    with patch("httpx.Client", mock_client):
        res, reason = call_bridge_tool(BRIDGE_QUERY)
    assert res is None
    assert reason == "error:extension not connected"


# ---------------------------------------------------------------------------
# Request shape
# ---------------------------------------------------------------------------

def test_request_shape_jsonrpc_tools_call_and_headers(monkeypatch):
    _enable_bridge(monkeypatch)
    mock_client, mock_instance = _http_mock(json_data=_rpc_ok())
    with patch("httpx.Client", mock_client):
        res, reason = call_bridge_tool(BRIDGE_QUERY)
    assert reason == "ok" and res is not None

    url = mock_instance.post.call_args[0][0]
    assert url == f"{GEMINI_BRIDGE_DEFAULT_URL}/mcp"

    payload = mock_instance.post.call_args[1]["json"]
    assert payload["jsonrpc"] == "2.0"
    assert payload["method"] == "tools/call"
    assert payload["params"]["name"] == "horo_consult"
    args = payload["params"]["arguments"]
    assert args["query"] == BRIDGE_QUERY
    assert args["response_format"] == "text"

    headers = mock_instance.post.call_args[1]["headers"]
    assert headers["Authorization"] == f"Bearer {FAKE_TOKEN}"
    assert "Accept" in headers
    assert headers["Content-Type"] == "application/json"


def test_birth_context_omitted_when_not_provided(monkeypatch):
    _enable_bridge(monkeypatch)
    mock_client, mock_instance = _http_mock(json_data=_rpc_ok())
    with patch("httpx.Client", mock_client):
        call_bridge_tool(BRIDGE_QUERY, birth_context=None)
    args = mock_instance.post.call_args[1]["json"]["params"]["arguments"]
    assert "birth_context" not in args


def test_scope_omitted_when_explicitly_empty(monkeypatch):
    _enable_bridge(monkeypatch)
    mock_client, mock_instance = _http_mock(json_data=_rpc_ok())
    with patch("httpx.Client", mock_client):
        call_bridge_tool(BRIDGE_QUERY, scope="")
    args = mock_instance.post.call_args[1]["json"]["params"]["arguments"]
    assert "scope" not in args


def test_scope_defaults_to_notebook_id_when_unset(monkeypatch):
    _enable_bridge(monkeypatch)
    mock_client, mock_instance = _http_mock(json_data=_rpc_ok())
    with patch("httpx.Client", mock_client):
        call_bridge_tool(BRIDGE_QUERY, scope=None)
    args = mock_instance.post.call_args[1]["json"]["params"]["arguments"]
    assert args["scope"] == GEMINI_BRIDGE_DEFAULT_SCOPE
    assert args["scope"].startswith("notebook:")


def test_birth_context_and_scope_included_when_provided(monkeypatch):
    _enable_bridge(monkeypatch)
    mock_client, mock_instance = _http_mock(json_data=_rpc_ok())
    birth_context = {"birth_datetime": "1990-05-15 14:30:00", "longitude": 100.493}
    with patch("httpx.Client", mock_client):
        call_bridge_tool(BRIDGE_QUERY, birth_context=birth_context, scope="notebook:custom")
    args = mock_instance.post.call_args[1]["json"]["params"]["arguments"]
    assert args["birth_context"] == birth_context
    assert args["scope"] == "notebook:custom"


def test_timeout_env_override_used_for_client(monkeypatch):
    _enable_bridge(monkeypatch)
    monkeypatch.setenv("GEMINI_WEB_BRIDGE_TIMEOUT_S", "7")
    mock_client, _ = _http_mock(json_data=_rpc_ok())
    with patch("httpx.Client", mock_client) as patched_client:
        call_bridge_tool(BRIDGE_QUERY)
    assert patched_client.call_args[1]["timeout"] == 7.0


def test_default_timeout_used_when_env_unset(monkeypatch):
    _enable_bridge(monkeypatch)
    mock_client, _ = _http_mock(json_data=_rpc_ok())
    with patch("httpx.Client", mock_client) as patched_client:
        call_bridge_tool(BRIDGE_QUERY)
    assert patched_client.call_args[1]["timeout"] == GEMINI_BRIDGE_DEFAULT_TIMEOUT_S


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------

def test_parse_content_first_text_item(monkeypatch):
    _enable_bridge(monkeypatch)
    mock_client, _ = _http_mock(
        json_data=_rpc_ok(content=[
            {"type": "image", "data": "zzz"},
            {"type": "text", "text": "  คำทำนายจากบริดจ์  "},
        ])
    )
    with patch("httpx.Client", mock_client):
        res, reason = call_bridge_tool(BRIDGE_QUERY)
    assert reason == "ok"
    assert res == {"text": "คำทำนายจากบริดจ์", "pdf_url": None}


def test_parse_structured_content_pdf_url(monkeypatch):
    _enable_bridge(monkeypatch)
    mock_client, _ = _http_mock(
        json_data=_rpc_ok(text="คำทำนาย", structured={"pdf_url": "https://example.com/r.pdf"})
    )
    with patch("httpx.Client", mock_client):
        res, reason = call_bridge_tool(BRIDGE_QUERY)
    assert reason == "ok"
    assert res["pdf_url"] == "https://example.com/r.pdf"
    assert res["text"] == "คำทำนาย"


def test_parse_content_scan_fallback_pdf_url(monkeypatch):
    _enable_bridge(monkeypatch)
    import json as _json

    nested = _json.dumps(
        {"report": {"pdf_url": "https://example.com/fallback.pdf"}}, ensure_ascii=False
    )
    mock_client, _ = _http_mock(
        json_data=_rpc_ok(content=[{"type": "text", "text": nested}])
    )
    with patch("httpx.Client", mock_client):
        res, reason = call_bridge_tool(BRIDGE_QUERY)
    assert reason == "ok"
    assert res["pdf_url"] == "https://example.com/fallback.pdf"


def test_missing_content_yields_empty_response(monkeypatch):
    _enable_bridge(monkeypatch)
    mock_client, _ = _http_mock(json_data={"jsonrpc": "2.0", "id": 1, "result": {}})
    with patch("httpx.Client", mock_client):
        res, reason = call_bridge_tool(BRIDGE_QUERY)
    assert res is None
    assert reason == "empty_response"


# ---------------------------------------------------------------------------
# Circuit breaker
# ---------------------------------------------------------------------------

def test_breaker_trips_after_http_503_blocks_next_call(monkeypatch):
    _enable_bridge(monkeypatch)
    mock_client, mock_instance = _http_mock(json_data=_rpc_ok(), status_code=503)
    with patch("httpx.Client", mock_client):
        res1, reason1 = call_bridge_tool(BRIDGE_QUERY)
        assert reason1 == "http_503" and res1 is None
        # Second call must be short-circuited by the open breaker
        res2, reason2 = call_bridge_tool(BRIDGE_QUERY)
    assert res2 is None
    assert reason2 == "circuit_open"
    assert mock_instance.post.call_count == 1


def test_breaker_resets_after_cooldown(monkeypatch):
    _enable_bridge(monkeypatch)
    clock = {"now": 1000.0}
    monkeypatch.setattr(gbc, "time", SimpleNamespace(monotonic=lambda: clock["now"]))
    mock_client, mock_instance = _http_mock(json_data=_rpc_ok(), status_code=503)
    with patch("httpx.Client", mock_client):
        _, reason1 = call_bridge_tool(BRIDGE_QUERY)
        assert reason1 == "http_503"
        # Advance past the 60s cooldown -> breaker closes, HTTP attempted again
        clock["now"] += gbc.BRIDGE_CIRCUIT_COOLDOWN_SECONDS + 1.0
        _, reason2 = call_bridge_tool(BRIDGE_QUERY)
    assert reason2 == "http_503"
    assert mock_instance.post.call_count == 2


def test_breaker_not_tripped_on_http_401(monkeypatch):
    _enable_bridge(monkeypatch)
    mock_client, mock_instance = _http_mock(json_data=_rpc_ok(), status_code=401)
    with patch("httpx.Client", mock_client):
        _, reason1 = call_bridge_tool(BRIDGE_QUERY)
        _, reason2 = call_bridge_tool(BRIDGE_QUERY)
    assert reason1 == "http_401"
    assert reason2 == "http_401"
    assert mock_instance.post.call_count == 2


# ---------------------------------------------------------------------------
# Dynamic toggle (no reimport)
# ---------------------------------------------------------------------------

def test_toggle_flips_dynamically_without_reimport(monkeypatch):
    _clear_bridge_env(monkeypatch)
    assert is_gemini_bridge_enabled() is False

    monkeypatch.setenv("GEMINI_WEB_BRIDGE_ENABLED", "true")
    # Flag on but no token -> still disabled
    assert is_gemini_bridge_enabled() is False

    monkeypatch.setenv("GEMINI_WEB_BRIDGE_TOKEN", "tok-dynamic-1")
    assert is_gemini_bridge_enabled() is True

    monkeypatch.setenv("GEMINI_WEB_BRIDGE_ENABLED", "false")
    assert is_gemini_bridge_enabled() is False

    monkeypatch.setenv("GEMINI_WEB_BRIDGE_ENABLED", "1")
    assert is_gemini_bridge_enabled() is True
