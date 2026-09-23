"""KAN-82: Edge case integration tests (partial/slow/intermittent failures).

Tests verify robust handling of:
  - Intermittent failures (succeed, fail, succeed pattern)
  - Slow responses near timeout boundary
  - Partial/malformed JSON-RPC responses
  - PDF URL extraction from nested structures
  - Toggle flip mid-session (dynamic behavior)
  - Circuit breaker cooldown boundary precision
"""

from __future__ import annotations

import httpx
import pytest

import project.core.gemini_bridge_client as gbc
from project.core.gemini_bridge_client import (
    BRIDGE_CIRCUIT_COOLDOWN_SECONDS,
    call_bridge_tool,
    is_gemini_bridge_enabled,
)

QUERY = "edge case query"
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
def _clean_breaker(monkeypatch):
    _clear_bridge_env(monkeypatch)
    gbc._BRIDGE_CIRCUIT_BREAKER.clear()
    monkeypatch.setenv("GEMINI_WEB_BRIDGE_ENABLED", "true")
    monkeypatch.setenv("GEMINI_WEB_BRIDGE_TOKEN", "edge-tok")
    yield
    gbc._BRIDGE_CIRCUIT_BREAKER.clear()


# ---------------------------------------------------------------------------
# Intermittent failures
# ---------------------------------------------------------------------------

def test_intermittent_failure_succeed_fail_succeed(monkeypatch):
    """Bridge succeeds, then fails, then succeeds — circuit should track state."""
    call_count = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["n"] += 1
        if call_count["n"] == 2:
            return httpx.Response(503)
        return httpx.Response(200, json={
            "jsonrpc": "2.0", "id": 1,
            "result": {"content": [{"type": "text", "text": f"resp-{call_count['n']}"}]},
        })

    real_client = httpx.Client
    monkeypatch.setattr(
        httpx, "Client",
        lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw),
    )

    # Call 1: success
    r1, reason1 = call_bridge_tool(QUERY)
    assert reason1 == "ok"
    assert r1["text"] == "resp-1"

    # Call 2: failure (trips circuit)
    r2, reason2 = call_bridge_tool(QUERY)
    assert reason2 == "http_503"

    # Call 3: circuit open, blocked
    r3, reason3 = call_bridge_tool(QUERY)
    assert reason3 == "circuit_open"
    assert call_count["n"] == 2


def test_intermittent_failure_with_recovery(monkeypatch):
    """After intermittent failure and cooldown, recovery succeeds."""
    clock = {"now": 1000.0}
    monkeypatch.setattr(
        gbc, "time",
        type("FakeTime", (), {"monotonic": staticmethod(lambda: clock["now"])}),
    )

    call_count = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["n"] += 1
        if call_count["n"] == 2:
            return httpx.Response(429)
        return httpx.Response(200, json={
            "jsonrpc": "2.0", "id": 1,
            "result": {"content": [{"type": "text", "text": f"resp-{call_count['n']}"}]},
        })

    real_client = httpx.Client
    monkeypatch.setattr(
        httpx, "Client",
        lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw),
    )

    # Success
    r1, _ = call_bridge_tool(QUERY)
    assert r1["text"] == "resp-1"

    # Intermittent failure
    _, reason2 = call_bridge_tool(QUERY)
    assert reason2 == "http_429"

    # Blocked
    _, reason3 = call_bridge_tool(QUERY)
    assert reason3 == "circuit_open"

    # Advance cooldown
    clock["now"] += BRIDGE_CIRCUIT_COOLDOWN_SECONDS + 1.0

    # Recovery
    r4, reason4 = call_bridge_tool(QUERY)
    assert reason4 == "ok"
    assert r4["text"] == "resp-3"


# ---------------------------------------------------------------------------
# Slow responses / timeout boundary
# ---------------------------------------------------------------------------

def test_timeout_exception_trips_circuit(monkeypatch):
    """TimeoutException trips the breaker even without HTTP status."""
    call_count = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["n"] += 1
        raise httpx.TimeoutException("read timeout")

    real_client = httpx.Client
    monkeypatch.setattr(
        httpx, "Client",
        lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw),
    )

    r1, reason1 = call_bridge_tool(QUERY)
    assert reason1 == "timeout"

    r2, reason2 = call_bridge_tool(QUERY)
    assert reason2 == "circuit_open"
    assert call_count["n"] == 1


def test_connect_error_trips_circuit(monkeypatch):
    """Connection errors trip the circuit."""
    call_count = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["n"] += 1
        raise httpx.ConnectError("connection refused")

    real_client = httpx.Client
    monkeypatch.setattr(
        httpx, "Client",
        lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw),
    )

    r1, reason1 = call_bridge_tool(QUERY)
    assert reason1.startswith("error:")

    r2, reason2 = call_bridge_tool(QUERY)
    assert reason2 == "circuit_open"


# ---------------------------------------------------------------------------
# Partial/malformed JSON-RPC responses
# ---------------------------------------------------------------------------

def test_partial_jsonrpc_response_missing_result(monkeypatch):
    """JSON-RPC response with missing result field → empty_response."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={
            "jsonrpc": "2.0", "id": 1,
            "result": {},  # empty result
        })

    real_client = httpx.Client
    monkeypatch.setattr(
        httpx, "Client",
        lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw),
    )

    r, reason = call_bridge_tool(QUERY)
    assert r is None
    assert reason == "empty_response"


def test_malformed_json_response(monkeypatch):
    """Invalid JSON response body → error:invalid_json."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="not-json")

    real_client = httpx.Client
    monkeypatch.setattr(
        httpx, "Client",
        lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw),
    )

    r, reason = call_bridge_tool(QUERY)
    assert r is None
    assert "error:" in reason


def test_jsonrpc_error_response(monkeypatch):
    """JSON-RPC error object → error:<detail>."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={
            "jsonrpc": "2.0", "id": 1,
            "error": {"code": -32000, "message": "session not verified"},
        })

    real_client = httpx.Client
    monkeypatch.setattr(
        httpx, "Client",
        lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw),
    )

    r, reason = call_bridge_tool(QUERY)
    assert r is None
    assert reason == "error:session not verified"


# ---------------------------------------------------------------------------
# PDF URL extraction
# ---------------------------------------------------------------------------

def test_pdf_url_extracted_from_structured_content(monkeypatch):
    """PDF URL extracted from structuredContent.pdf_url."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={
            "jsonrpc": "2.0", "id": 1,
            "result": {
                "content": [{"type": "text", "text": "consultation"}],
                "structuredContent": {"pdf_url": "https://example.com/report.pdf"},
            },
        })

    real_client = httpx.Client
    monkeypatch.setattr(
        httpx, "Client",
        lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw),
    )

    r, reason = call_bridge_tool(QUERY)
    assert reason == "ok"
    assert r["pdf_url"] == "https://example.com/report.pdf"


def test_pdf_url_extracted_from_nested_json_text(monkeypatch):
    """PDF URL extracted from JSON-encoded text content."""
    import json
    nested = json.dumps({"report": {"pdf_url": "https://example.com/nested.pdf"}})

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={
            "jsonrpc": "2.0", "id": 1,
            "result": {
                "content": [{"type": "text", "text": nested}],
            },
        })

    real_client = httpx.Client
    monkeypatch.setattr(
        httpx, "Client",
        lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw),
    )

    r, reason = call_bridge_tool(QUERY)
    assert reason == "ok"
    assert r["pdf_url"] == "https://example.com/nested.pdf"


def test_pdf_url_non_http_scheme_rejected(monkeypatch):
    """Non-http(s) PDF URL schemes are rejected (security)."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={
            "jsonrpc": "2.0", "id": 1,
            "result": {
                "content": [{"type": "text", "text": "consultation"}],
                "structuredContent": {"pdf_url": "javascript:alert(1)"},
            },
        })

    real_client = httpx.Client
    monkeypatch.setattr(
        httpx, "Client",
        lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw),
    )

    r, reason = call_bridge_tool(QUERY)
    assert reason == "ok"
    assert r["pdf_url"] is None


# ---------------------------------------------------------------------------
# Toggle flip mid-session
# ---------------------------------------------------------------------------

def test_toggle_flip_mid_session(monkeypatch):
    """Toggle can flip at runtime without restart."""
    call_count = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["n"] += 1
        return httpx.Response(200, json={
            "jsonrpc": "2.0", "id": 1,
            "result": {"content": [{"type": "text", "text": "ok"}]},
        })

    real_client = httpx.Client
    monkeypatch.setattr(
        httpx, "Client",
        lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw),
    )

    # Enabled
    assert is_gemini_bridge_enabled() is True
    r1, reason1 = call_bridge_tool(QUERY)
    assert reason1 == "ok"

    # Flip off
    monkeypatch.setenv("GEMINI_WEB_BRIDGE_ENABLED", "false")
    assert is_gemini_bridge_enabled() is False
    r2, reason2 = call_bridge_tool(QUERY)
    assert reason2 == "disabled"

    # Flip back on
    monkeypatch.setenv("GEMINI_WEB_BRIDGE_ENABLED", "true")
    assert is_gemini_bridge_enabled() is True
    r3, reason3 = call_bridge_tool(QUERY)
    assert reason3 == "ok"


# ---------------------------------------------------------------------------
# Circuit breaker cooldown boundary
# ---------------------------------------------------------------------------

def test_circuit_breaker_boundary_exact(monkeypatch):
    """At exactly cooldown boundary, circuit should close."""
    clock = {"now": 1000.0}
    monkeypatch.setattr(
        gbc, "time",
        type("FakeTime", (), {"monotonic": staticmethod(lambda: clock["now"])}),
    )

    call_count = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["n"] += 1
        if call_count["n"] == 1:
            return httpx.Response(503)
        return httpx.Response(200, json={
            "jsonrpc": "2.0", "id": 1,
            "result": {"content": [{"type": "text", "text": "ok"}]},
        })

    real_client = httpx.Client
    monkeypatch.setattr(
        httpx, "Client",
        lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw),
    )

    # Trip
    call_bridge_tool(QUERY)

    # Just before cooldown expires → still open
    clock["now"] += BRIDGE_CIRCUIT_COOLDOWN_SECONDS - 0.001
    _, reason = call_bridge_tool(QUERY)
    assert reason == "circuit_open"

    # Just after cooldown expires → closed
    clock["now"] += 0.002
    r, reason = call_bridge_tool(QUERY)
    assert reason == "ok"
    assert r is not None
