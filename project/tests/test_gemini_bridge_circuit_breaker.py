"""
test_gemini_bridge_circuit_breaker.py
======================================
TDD RED-phase tests for the Gemini Web Bridge MCP client — circuit breaker.

Spec reference (docs/gemini-bridge-mcp-toggle.md §7):
  - Embedded circuit breaker with 60 s cooldown.
  - Trips on failure criteria: 503 / 422 / 429 / timeout ฯลฯ
    ("เมื่อ bridge ล้มเหลงตามเกณฑ์ (503/422/429/timeout ฯลฯ) circuit จะเปิด")
  - After 60 s the circuit closes (half-open probe via normal call).
  - When open, the next call returns ("circuit_open") immediately with ZERO
    HTTP attempts.
  - Does NOT trip on 4xx auth errors (401) — correct, retryable config issue.

Contract (gemini_bridge_client.py docstring):
  Reasons include "circuit_open" and "http_503", "http_422", "http_429".

Mocking discipline — **httpx monkeypatching**:
  - httpx.Client is monkeypatched (via monkeypatch.setattr) to wrap
    httpx.MockTransport so every request is intercepted at the transport
    layer.  No real network calls ever occur.
  - pytest.monkeypatch is the sole patching primitive (no
    unittest.mock.patch).
"""

from __future__ import annotations

import httpx
import pytest

import project.core.gemini_bridge_client as gbc
from project.core.gemini_bridge_client import (
    BRIDGE_CIRCUIT_COOLDOWN_SECONDS,
    call_bridge_tool,
)

QUERY = "คำถามทดสอบวงจรปิด"
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
    yield
    gbc._BRIDGE_CIRCUIT_BREAKER.clear()


@pytest.fixture
def _bridge_on(monkeypatch):
    """Enable the bridge toggle with a synthetic token."""
    monkeypatch.setenv("GEMINI_WEB_BRIDGE_ENABLED", "true")
    monkeypatch.setenv("GEMINI_WEB_BRIDGE_TOKEN", "circuit-test-token")
    return monkeypatch


def _patch_httpx_with_transport(monkeypatch, handler):
    """Monkeypatch httpx.Client to use MockTransport (httpx monkeypatching).

    Saves a reference to the real Client before patching to avoid
    infinite recursion inside the factory lambda.
    """
    transport = httpx.MockTransport(handler)
    real_client = httpx.Client
    monkeypatch.setattr(
        httpx, "Client",
        lambda **kw: real_client(transport=transport, **kw),
    )
    return transport


def _ok_response(text: str = "recovered answer", pdf_url: str | None = None) -> dict:
    result = {"content": [{"type": "text", "text": text}]}
    if pdf_url:
        result["structuredContent"] = {"pdf_url": pdf_url}
    return {"jsonrpc": "2.0", "id": 1, "result": result}


# ---------------------------------------------------------------------------
# Circuit trips → next call returns circuit_open with zero HTTP
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("status_code", [503, 429, 422])
def test_circuit_trips_after_http_failure_blocks_next_call(
    monkeypatch, _bridge_on, status_code
):
    """Per spec §7: 503/422/429 all trip the circuit.

    After the first failing call, the breaker opens and the second call
    must return 'circuit_open' WITHOUT any HTTP attempt.
    """
    call_count = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["n"] += 1
        return httpx.Response(status_code)

    _patch_httpx_with_transport(monkeypatch, handler)

    res1, reason1 = call_bridge_tool(QUERY)
    assert res1 is None
    assert reason1 == f"http_{status_code}"

    # Second call — circuit should be open
    res2, reason2 = call_bridge_tool(QUERY)
    assert res2 is None
    assert reason2 == "circuit_open"
    assert call_count["n"] == 1, (
        f"Expected exactly 1 HTTP call after {status_code} tripped the "
        f"circuit, got {call_count['n']}"
    )


def test_circuit_trips_after_timeout(monkeypatch, _bridge_on):
    """TimeoutException trips the circuit per spec §7 criteria."""
    call_count = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["n"] += 1
        raise httpx.TimeoutException("simulated read timeout")

    _patch_httpx_with_transport(monkeypatch, handler)

    res1, reason1 = call_bridge_tool(QUERY)
    assert res1 is None
    assert reason1 == "timeout"

    res2, reason2 = call_bridge_tool(QUERY)
    assert res2 is None
    assert reason2 == "circuit_open"
    assert call_count["n"] == 1


# ---------------------------------------------------------------------------
# Circuit does NOT trip on non-retryable 4xx (auth errors)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("status_code", [401, 403, 404])
def test_circuit_not_tripped_on_non_retryable_4xx(
    monkeypatch, _bridge_on, status_code
):
    """4xx auth/config errors (401/403/404) do NOT trip the breaker.

    Per blue-red-team verdict: 'does NOT trip on 4xx auth errors
    (correct: retryable config problems)'.
    """
    call_count = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["n"] += 1
        return httpx.Response(status_code)

    _patch_httpx_with_transport(monkeypatch, handler)

    _, reason1 = call_bridge_tool(QUERY)
    assert reason1 == f"http_{status_code}"

    _, reason2 = call_bridge_tool(QUERY)
    assert reason2 == f"http_{status_code}"
    assert call_count["n"] == 2, (
        f"Circuit should NOT trip on {status_code}; expected 2 HTTP calls"
    )


# ---------------------------------------------------------------------------
# Circuit resets after cooldown
# ---------------------------------------------------------------------------

def test_circuit_resets_after_cooldown(monkeypatch, _bridge_on):
    """After BRIDGE_CIRCUIT_COOLDOWN_SECONDS, the circuit closes and HTTP
    is attempted again (half-open probe)."""
    call_count = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["n"] += 1
        if call_count["n"] == 1:
            return httpx.Response(503)
        # After cooldown, return 200 with valid content
        return httpx.Response(200, json=_ok_response("recovered"))

    _patch_httpx_with_transport(monkeypatch, handler)

    # Patch time so we control the cooldown
    clock = {"now": 1000.0}
    monkeypatch.setattr(
        gbc, "time",
        type("FakeTime", (), {"monotonic": staticmethod(lambda: clock["now"])}),
    )

    _, reason1 = call_bridge_tool(QUERY)
    assert reason1 == "http_503"

    # Circuit is open
    _, reason2 = call_bridge_tool(QUERY)
    assert reason2 == "circuit_open"
    assert call_count["n"] == 1

    # Advance past cooldown
    clock["now"] += BRIDGE_CIRCUIT_COOLDOWN_SECONDS + 1.0

    # Circuit should be closed now — HTTP attempted, 200 response
    res3, reason3 = call_bridge_tool(QUERY)
    assert reason3 == "ok"
    assert res3 is not None
    assert res3["text"] == "recovered"
    assert call_count["n"] == 2


# ---------------------------------------------------------------------------
# No HTTP when circuit already open
# ---------------------------------------------------------------------------

def test_no_http_when_circuit_already_open(monkeypatch, _bridge_on):
    """When the circuit is already open (pre-tripped), call_bridge_tool
    must return 'circuit_open' without instantiating httpx.Client at all."""
    # Pre-trip the circuit far into the future
    gbc._BRIDGE_CIRCUIT_BREAKER["bridge"] = 999999.0

    ctor_count = {"n": 0}
    post_called = {"flag": False}

    def handler(request: httpx.Request) -> httpx.Response:
        post_called["flag"] = True
        return httpx.Response(200, json=_ok_response())

    real_client = httpx.Client

    def client_factory(**kw):
        ctor_count["n"] += 1
        return real_client(transport=httpx.MockTransport(handler), **kw)

    monkeypatch.setattr(httpx, "Client", client_factory)

    res, reason = call_bridge_tool(QUERY)
    assert res is None
    assert reason == "circuit_open"
    assert ctor_count["n"] == 0, (
        "httpx.Client must not be instantiated when circuit is open"
    )
    assert post_called["flag"] is False


# ---------------------------------------------------------------------------
# Generic error trips the circuit
# ---------------------------------------------------------------------------

def test_error_reason_trips_circuit(monkeypatch, _bridge_on):
    """A generic error (e.g. connection refused) trips the circuit,
    and the reason is 'error:<detail>'."""
    call_count = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["n"] += 1
        raise httpx.ConnectError("connection refused to internal-bridge.invalid")

    _patch_httpx_with_transport(monkeypatch, handler)

    res1, reason1 = call_bridge_tool(QUERY)
    assert res1 is None
    assert reason1.startswith("error:")

    # Circuit should be tripped
    res2, reason2 = call_bridge_tool(QUERY)
    assert res2 is None
    assert reason2 == "circuit_open"
    assert call_count["n"] == 1


# ---------------------------------------------------------------------------
# Circuit state is module-global and shared across calls
# ---------------------------------------------------------------------------

def test_circuit_state_is_shared_across_calls_within_cooldown(monkeypatch, _bridge_on):
    """The circuit breaker is a module-global dict; trips from one
    call_bridge_tool invocation must affect subsequent invocations."""
    call_count = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["n"] += 1
        return httpx.Response(503)

    _patch_httpx_with_transport(monkeypatch, handler)

    # First call trips
    _, r1 = call_bridge_tool(QUERY)
    assert r1 == "http_503"

    # Second call blocked by circuit
    _, r2 = call_bridge_tool(QUERY)
    assert r2 == "circuit_open"

    # Third call also blocked
    _, r3 = call_bridge_tool(QUERY)
    assert r3 == "circuit_open"

    # Only one HTTP call ever made
    assert call_count["n"] == 1


def test_cooldown_value_matches_spec(monkeypatch):
    """The circuit breaker cooldown must be 60 seconds per spec §7."""
    assert BRIDGE_CIRCUIT_COOLDOWN_SECONDS == 60.0
