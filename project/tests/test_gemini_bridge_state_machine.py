"""KAN-80: Circuit breaker state machine verification (closed -> open -> half-open -> closed).

States per spec (docs/gemini-bridge-mcp-toggle.md §7):
  - CLOSED  : normal operation, calls go through.
  - OPEN    : after a hard failure (503/422/429/timeout/error), breaker opens.
              All calls return circuit_open without HTTP.
  - HALF_OPEN: after cooldown expires, the next call is allowed through
              as a probe. The state transitions based on probe outcome:
              success -> CLOSED, failure -> OPEN (re-tripped).

Tests verify every state transition explicitly with monkeypatched time
so we control the cooldown boundary precisely.
"""

from __future__ import annotations

import httpx
import pytest

import project.core.gemini_bridge_client as gbc
from project.core.gemini_bridge_client import (
    BRIDGE_CIRCUIT_COOLDOWN_SECONDS,
    call_bridge_tool,
)

QUERY = "state-machine query"
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
    monkeypatch.setenv("GEMINI_WEB_BRIDGE_TOKEN", "state-machine-tok")
    yield
    gbc._BRIDGE_CIRCUIT_BREAKER.clear()


# ---------------------------------------------------------------------------
# CLOSED state
# ---------------------------------------------------------------------------

def test_closed_state_allows_http_call(monkeypatch):
    """CLOSED: call goes through, circuit dict is empty (no cooldown)."""
    assert gbc._BRIDGE_CIRCUIT_BREAKER == {}
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

    res, reason = call_bridge_tool(QUERY)
    assert reason == "ok"
    assert res is not None
    assert call_count["n"] == 1
    # Success leaves breaker closed (still empty)
    assert gbc._BRIDGE_CIRCUIT_BREAKER == {}


def test_closed_to_open_transition_on_hard_failure(monkeypatch):
    """CLOSED -> OPEN: first hard failure trips the circuit."""
    call_count = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["n"] += 1
        return httpx.Response(503)

    real_client = httpx.Client
    monkeypatch.setattr(
        httpx, "Client",
        lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw),
    )

    # First call: CLOSED, HTTP attempted, failure, breaker trips -> OPEN
    _, reason1 = call_bridge_tool(QUERY)
    assert reason1 == "http_503"
    assert "bridge" in gbc._BRIDGE_CIRCUIT_BREAKER
    assert call_count["n"] == 1

    # Second call: OPEN, no HTTP
    _, reason2 = call_bridge_tool(QUERY)
    assert reason2 == "circuit_open"
    assert call_count["n"] == 1


# ---------------------------------------------------------------------------
# OPEN state
# ---------------------------------------------------------------------------

def test_open_state_blocks_all_calls_without_http(monkeypatch):
    """OPEN: repeated calls all return circuit_open, zero HTTP."""
    # Force circuit open far into the future
    gbc._BRIDGE_CIRCUIT_BREAKER["bridge"] = 999999.0

    post_called = {"flag": False}

    def handler(request: httpx.Request) -> httpx.Response:
        post_called["flag"] = True
        return httpx.Response(200, json={
            "jsonrpc": "2.0", "id": 1,
            "result": {"content": [{"type": "text", "text": "ok"}]},
        })

    real_client = httpx.Client
    monkeypatch.setattr(
        httpx, "Client",
        lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw),
    )

    for _ in range(5):
        _, reason = call_bridge_tool(QUERY)
        assert reason == "circuit_open"
    assert post_called["flag"] is False


# ---------------------------------------------------------------------------
# HALF-OPEN state (cooldown just expired)
# ---------------------------------------------------------------------------

def test_open_to_half_open_after_cooldown(monkeypatch):
    """OPEN -> HALF_OPEN: after cooldown expires, one call is allowed through."""
    clock = {"now": 1000.0}
    monkeypatch.setattr(
        gbc, "time",
        type("FakeTime", (), {"monotonic": staticmethod(lambda: clock["now"])}),
    )

    call_count = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["n"] += 1
        if call_count["n"] == 1:
            return httpx.Response(503)  # initial trip
        return httpx.Response(200, json={
            "jsonrpc": "2.0", "id": 1,
            "result": {"content": [{"type": "text", "text": "recovered"}]},
        })

    real_client = httpx.Client
    monkeypatch.setattr(
        httpx, "Client",
        lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw),
    )

    # Trip the circuit
    _, reason1 = call_bridge_tool(QUERY)
    assert reason1 == "http_503"
    assert call_count["n"] == 1

    # OPEN: blocked
    _, reason2 = call_bridge_tool(QUERY)
    assert reason2 == "circuit_open"
    assert call_count["n"] == 1

    # Advance past cooldown -> HALF_OPEN probe
    clock["now"] += BRIDGE_CIRCUIT_COOLDOWN_SECONDS + 1.0
    res3, reason3 = call_bridge_tool(QUERY)
    assert reason3 == "ok"
    assert res3 is not None
    assert call_count["n"] == 2


def test_half_open_to_closed_on_success(monkeypatch):
    """HALF_OPEN -> CLOSED: successful probe returns breaker to closed state."""
    clock = {"now": 1000.0}
    monkeypatch.setattr(
        gbc, "time",
        type("FakeTime", (), {"monotonic": staticmethod(lambda: clock["now"])}),
    )

    call_count = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["n"] += 1
        if call_count["n"] == 1:
            return httpx.Response(503)  # initial trip
        # Subsequent calls succeed
        return httpx.Response(200, json={
            "jsonrpc": "2.0", "id": 1,
            "result": {"content": [{"type": "text", "text": "ok"}]},
        })

    real_client = httpx.Client
    monkeypatch.setattr(
        httpx, "Client",
        lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw),
    )

    # Trip then advance past cooldown
    call_bridge_tool(QUERY)
    clock["now"] += BRIDGE_CIRCUIT_COOLDOWN_SECONDS + 1.0

    # HALF_OPEN probe succeeds -> CLOSED
    res, reason = call_bridge_tool(QUERY)
    assert reason == "ok"
    assert res is not None

    # Breaker should now be cleared/empty (closed state)
    assert gbc._BRIDGE_CIRCUIT_BREAKER == {}

    # Next call goes through normally (CLOSED)
    res2, reason2 = call_bridge_tool(QUERY)
    assert reason2 == "ok"
    assert call_count["n"] == 3  # trip-call + probe + normal


def test_half_open_to_open_on_failure(monkeypatch):
    """HALF_OPEN -> OPEN: failed probe re-trips the breaker."""
    clock = {"now": 1000.0}
    monkeypatch.setattr(
        gbc, "time",
        type("FakeTime", (), {"monotonic": staticmethod(lambda: clock["now"])}),
    )

    call_count = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["n"] += 1
        return httpx.Response(503)  # always fail

    real_client = httpx.Client
    monkeypatch.setattr(
        httpx, "Client",
        lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw),
    )

    # Trip
    _, r1 = call_bridge_tool(QUERY)
    assert r1 == "http_503"

    # Advance cooldown -> HALF_OPEN probe
    clock["now"] += BRIDGE_CIRCUIT_COOLDOWN_SECONDS + 1.0
    _, r2 = call_bridge_tool(QUERY)
    assert r2 == "http_503"  # probe failed

    # Breaker should be re-tripped (OPEN again)
    assert "bridge" in gbc._BRIDGE_CIRCUIT_BREAKER
    assert gbc._BRIDGE_CIRCUIT_BREAKER["bridge"] > clock["now"]

    # Next call is blocked again (OPEN)
    _, r3 = call_bridge_tool(QUERY)
    assert r3 == "circuit_open"
    assert call_count["n"] == 2  # trip-call + probe (blocked)


# ---------------------------------------------------------------------------
# Full cycle: CLOSED -> OPEN -> HALF_OPEN -> CLOSED
# ---------------------------------------------------------------------------

def test_full_cycle_closed_open_half_open_closed(monkeypatch):
    """End-to-end: CLOSED -> OPEN -> HALF_OPEN -> CLOSED."""
    clock = {"now": 5000.0}
    monkeypatch.setattr(
        gbc, "time",
        type("FakeTime", (), {"monotonic": staticmethod(lambda: clock["now"])}),
    )

    call_count = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["n"] += 1
        # First call fails (trip), rest succeed
        if call_count["n"] == 1:
            return httpx.Response(429)
        return httpx.Response(200, json={
            "jsonrpc": "2.0", "id": 1,
            "result": {"content": [{"type": "text", "text": "recovered"}]},
        })

    real_client = httpx.Client
    monkeypatch.setattr(
        httpx, "Client",
        lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw),
    )

    # 1. CLOSED -> hard failure -> OPEN
    _, r1 = call_bridge_tool(QUERY)
    assert r1 == "http_429"
    assert "bridge" in gbc._BRIDGE_CIRCUIT_BREAKER  # OPEN

    # 2. OPEN -> blocked
    _, r2 = call_bridge_tool(QUERY)
    assert r2 == "circuit_open"

    # 3. Advance cooldown -> HALF_OPEN probe -> success -> CLOSED
    clock["now"] += BRIDGE_CIRCUIT_COOLDOWN_SECONDS + 1.0
    res3, r3 = call_bridge_tool(QUERY)
    assert r3 == "ok"
    assert res3 is not None
    assert gbc._BRIDGE_CIRCUIT_BREAKER == {}  # CLOSED

    # 4. CLOSED -> next call goes through
    res4, r4 = call_bridge_tool(QUERY)
    assert r4 == "ok"
    assert call_count["n"] == 3  # trip + probe + normal + normal
