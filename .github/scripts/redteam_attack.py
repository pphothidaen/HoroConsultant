#!/usr/bin/env python3
"""Team Red security validation.

Run by the ``teamred`` job in .github/workflows/post-deploy-tdd.yml.

Performs security checks against the FastAPI app and asserts:

1. Circuit breaker bypass prevention  -- once tripped, circuits must
   remain open and skip the failing provider with zero latency.
2. Fail-closed on 503 / 429 / timeout  -- when upstream providers are
   unavailable, the system must fall through to a deterministic safe net
   and never return upstream content from a failed call.
3. No-secret leakage  -- API responses, error messages, attempted-route
   labels, and provider-status output must never expose API keys, tokens,
   or other credentials.

This script is intentionally dependency-light.  It boots the FastAPI app
in-process via ``TestClient`` and uses only the standard library for
assertions, so it runs in a fresh GitHub Actions runner with no extra
installs (besides ``uv run`` which is available after setup-python).

Output:
    plans/test_provenance/teamred-results.json  (structured JSON report)

Exit code:
    0 = all checks passed
    1 = one or more checks failed (triggers auto_create_jira.py + fail step)
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
import time
import unittest.mock as mock
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Environment setup MUST run before any project import so that no real
# credentials are loaded from .env or the environment.
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("HORO_ALLOW_PYTHON_FALLBACK", "1")
os.environ.setdefault("SKIP_FAISS_WARMUP", "true")
os.environ.setdefault("LOG_LEVEL", "WARNING")

_SENSITIVE_ENV_VARS = [
    "GOOGLE_AI_STUDIO_API_KEY", "GOOGLE_AI_STUDIO_API_KEY2",
    "GOOGLE_API_KEY", "GEMINI_API_KEY", "ANTHROPIC_API_KEY",
    "CLAUDE_API_KEY", "CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_AI_TOKEN",
    "CLOUDFLARE_API_TOKEN", "HF_TOKEN", "HUGGINGFACE_TOKEN",
    "SECRET_KEY", "TELEGRAM_BOT_TOKEN", "NINE_ROUTER_API_KEY",
    "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY",
    "NINEROUTER_API_KEY", "REASONING_API_KEY", "VERCEL_TOKEN",
]
for _v in _SENSITIVE_ENV_VARS:
    os.environ[_v] = ""

with mock.patch("dotenv.load_dotenv", return_value=False):
    from project.main import app  # noqa: E402
    from project.core.llm_gateway import LLMGateway  # noqa: E402
    from project.core.ai_provider_router import (  # noqa: E402
        AIProviderRouter,
        CircuitBreakerState,
    )
    from project.api_router import (  # noqa: E402
        HybridRouter,
        _ROUTE_CIRCUIT_BREAKER,
        _is_route_circuit_open,
        _trip_route_circuit,
        CIRCUIT_BREAKER_COOLDOWN_SECONDS,
    )

from fastapi.testclient import TestClient  # noqa: E402

RESULTS_PATH = _ROOT / "plans" / "test_provenance" / "teamred-results.json"
_client = TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Secret-detection patterns.
# ---------------------------------------------------------------------------
_SECRET_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"AIza[0-9A-Za-z_\-]{35}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"eyJ[A-Za-z0-9_\-]*\.eyJ[A-Za-z0-9_\-]*\.[A-Za-z0-9_\-]"),
    re.compile(r"xox[baprs]-[A-Za-z0-9\-]{10,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9._\-]{20,}"),
]

# A recognisable fake key planted in the environment to prove it never leaks.
_FAKE_KEY = "RED_TEAM_FAKE_KEY_aBcDeFgHiJkLmNoPqRsTuVwXyZ0123456789"
os.environ["GOOGLE_AI_STUDIO_API_KEY"] = _FAKE_KEY
os.environ["GOOGLE_AI_STUDIO_API_KEY2"] = _FAKE_KEY


class TestRunner:
    """Collects pass/fail results for a suite of assertion-based tests."""

    def __init__(self) -> None:
        self.results: list[dict[str, str]] = []

    def test(self, test_id: str, name: str) -> "TestRunner":
        self._current = {"id": test_id, "name": name, "status": "PASSED", "details": ""}
        return self

    def __enter__(self) -> "TestRunner":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if self._current is not None:
            if exc_type is not None:
                if issubclass(exc_type, AssertionError):
                    self._current["status"] = "FAILED"
                    self._current["details"] = str(exc_val)
                else:
                    self._current["status"] = "ERROR"
                    self._current["details"] = f"{exc_type.__name__}: {exc_val}"
            self.results.append(self._current)
            self._current = None
        return True


runner = TestRunner()


# ---------------------------------------------------------------------------
# Helper utilities.
# ---------------------------------------------------------------------------
def _scan_for_secrets(text: str) -> list[str]:
    if not isinstance(text, str):
        text = str(text)
    found: list[str] = []
    for pattern in _SECRET_PATTERNS:
        matches = pattern.findall(text)
        found.extend(matches)
    if _FAKE_KEY in text:
        found.append("RED_TEAM_FAKE_KEY (environment value leak)")
    for var in _SENSITIVE_ENV_VARS:
        val = os.environ.get(var, "")
        if len(val) > 8 and val in text:
            found.append(f"[ENV_LEAK:{var}]")
    return found


def _reset_hybrid_router_circuits() -> None:
    _ROUTE_CIRCUIT_BREAKER.clear()


def _make_gateway() -> LLMGateway:
    gw = LLMGateway()
    for key in ("cloudflare", "gemini", "codex", "claude", "ollama"):
        gw.providers[key].is_configured = True
    return gw


def _make_ai_router() -> AIProviderRouter:
    return AIProviderRouter(zero_cost_only=False)


def _fail_all_providers(gw: LLMGateway, exc_msg: str = "upstream_failure") -> None:
    def _raiser(*args, **kwargs):
        raise Exception(exc_msg)

    for key in ("cloudflare", "gemini", "codex", "claude", "ollama"):
        setattr(gw, f"_call_{key}", _raiser)


def _async_return(value: str):
    """Create an async function that returns *value* (for mocking async _call_*)."""
    async def _fn(*args, **kwargs):
        return value
    return _fn


def _async_raise(exc: BaseException):
    """Create an async function that raises *exc* (for mocking async _call_*)."""
    async def _fn(*args, **kwargs):
        raise exc
    return _fn


# ============================================================================
# 1. CIRCUIT BREAKER BYPASS PREVENTION  (TC-CB-*)
# ============================================================================

def test_cb_001() -> None:
    """CircuitBreakerState trips to OPEN on 429 rate-limit failure."""
    cb = CircuitBreakerState(name="test_provider")
    assert cb.state == "CLOSED", "Circuit should start CLOSED"
    cb.record_failure(is_rate_limit=True)
    assert cb.state == "OPEN", "Circuit should be OPEN after 429 rate-limit"
    assert cb.failure_count == 1, "Failure count should be 1 after one rate-limit"


def test_cb_002() -> None:
    """is_open() returns True immediately after tripping (0ms instant bypass)."""
    cb = CircuitBreakerState(name="test_provider", cooldown_seconds=60.0)
    cb.trip()
    assert cb.state == "OPEN"
    assert cb.is_open()
    t0 = time.monotonic()
    result = cb.is_open()
    elapsed = time.monotonic() - t0
    assert result, "is_open() must return True"
    assert elapsed < 0.01, f"is_open() took {elapsed * 1000:.2f}ms; expected <10ms"


def test_cb_003() -> None:
    """Rapid repeated is_open() checks do not reset or close the circuit."""
    cb = CircuitBreakerState(name="test_provider", cooldown_seconds=60.0)
    cb.trip()
    for i in range(100):
        assert cb.is_open(), f"Circuit must remain OPEN on rapid check #{i + 1}"
    assert cb.state == "OPEN", "State must still be OPEN after 100 rapid checks"


def test_cb_004() -> None:
    """Circuit cooldown expiry transitions OPEN -> HALF_OPEN -> CLOSED."""
    cb = CircuitBreakerState(name="test_provider", cooldown_seconds=1.0)
    cb.trip()
    assert cb.is_open()
    time.sleep(1.15)
    assert not cb.is_open(), "Circuit should become HALF_OPEN after cooldown"
    assert cb.state == "HALF_OPEN"
    cb.record_success()
    assert cb.state == "CLOSED", "Success in HALF_OPEN should close the circuit"


def test_cb_005() -> None:
    """LLMGateway trips circuit after 3 failures and bypasses on the 4th call."""
    gw = _make_gateway()
    call_log: list[str] = []

    def _cf_fail(prompt: str, system_instruction: str = "") -> str:
        call_log.append("cloudflare")
        raise Exception("503 service unavailable")

    def _other_fail(**_):
        raise Exception("downstream failure")

    gw._call_cloudflare = _cf_fail
    for k in ("gemini", "codex", "claude", "ollama"):
        setattr(gw, f"_call_{k}", _other_fail)

    for _ in range(3):
        result = asyncio.run(gw.generate_text(prompt="t"))
        assert result["provider"] == "deterministic"
        assert result["fallback_triggered"] is True

    cb = gw.providers["cloudflare"]
    assert cb.consecutive_failures >= 3, f"Expected >=3 failures, got {cb.consecutive_failures}"
    assert cb.circuit_broken_until > 0, "circuit_broken_until must be set"

    before = len(call_log)
    result = asyncio.run(gw.generate_text(prompt="t"))
    assert len(call_log) == before, "Cloudflare must be bypassed when circuit OPEN"
    assert result["provider"] == "deterministic"


def test_cb_006() -> None:
    """AIProviderRouter skips an open-tier provider entirely (0ms bypass)."""
    router = _make_ai_router()
    # Trip codex circuit so it must be bypassed
    router.circuit_breakers["codex_chatgpt"].trip()
    assert router.circuit_breakers["codex_chatgpt"].is_open()
    # Trip remaining cloud tiers so flow reaches deterministic safe net
    router.circuit_breakers["gemini"].trip()
    router.circuit_breakers["reasoning_proxy"].trip()
    router.reasoning_base_url = ""

    router.invoke_codex_chatgpt = mock.Mock(
        return_value={"status": "success", "content": "must_not_appear"}
    )
    router.invoke_deterministic_safe_net = mock.Mock(return_value={
        "status": "fallback", "provider": "DETERMINISTIC_SAFE_NET",
        "content": "deterministic content", "route_used": "deterministic_safe_net",
    })

    result = router.call_ai(prompt="test prompt")
    assert not router.invoke_codex_chatgpt.called, \
        "Codex must not be invoked when circuit is OPEN"
    assert result.get("route_used") == "deterministic_safe_net", \
        f"Expected deterministic_safe_net, got {result.get('route_used')}"
    assert "must_not_appear" not in json.dumps(result), \
        "No content from bypassed provider should appear in result"


def test_cb_007() -> None:
    """HybridRouter circuit breaker skips tripped route on subsequent generate()."""
    _reset_hybrid_router_circuits()
    hr = HybridRouter()
    ollama_mock = mock.Mock(return_value=(None, "429"))

    with mock.patch("project.api_router._call_ollama", ollama_mock), \
         mock.patch("project.api_router._call_gemini", mock.Mock(side_effect=Exception("no_gemini"))), \
         mock.patch("project.api_router._call_cloudflare_ai", mock.Mock(side_effect=Exception("no_cf"))):
        result1 = hr.generate(prompt="test", system_instruction="")
        assert result1["route"] == "exhausted"

    assert len(_ROUTE_CIRCUIT_BREAKER) > 0, "Circuit must be tripped after 429"

    calls_before = ollama_mock.call_count
    with mock.patch("project.api_router._call_ollama", ollama_mock), \
         mock.patch("project.api_router._call_gemini", mock.Mock(side_effect=Exception("no_gemini"))), \
         mock.patch("project.api_router._call_cloudflare_ai", mock.Mock(side_effect=Exception("no_cf"))):
        result2 = hr.generate(prompt="test", system_instruction="")

    assert ollama_mock.call_count == calls_before, \
        "Ollama must be bypassed when circuit is OPEN"
    _reset_hybrid_router_circuits()


def test_cb_008() -> None:
    """Circuit breaker is per-provider: tripping one does not block others."""
    gw = _make_gateway()
    gw.providers["cloudflare"].is_configured = True
    gw.providers["gemini"].is_configured = True
    gw.providers["cloudflare"].consecutive_failures = 3
    gw.providers["cloudflare"].circuit_broken_until = time.time() + 60.0
    assert gw._is_circuit_open(gw.providers["cloudflare"]), "Cloudflare must be open"
    assert not gw._is_circuit_open(gw.providers["gemini"]), "Gemini must remain closed"

    gw._call_cloudflare = _async_raise(Exception("cf_down"))
    gw._call_gemini = _async_return("gemini_ok_text")
    result = asyncio.run(gw.generate_text(prompt="test"))
    assert result["provider"] == "gemini", \
        f"Expected gemini after cloudflare bypass, got {result['provider']}"
    assert result["fallback_triggered"] is True
    assert "gemini_ok_text" in result["text"]


# ============================================================================
# 2. FAIL-CLOSED ON 503 / 429 / TIMEOUT  (TC-FC-*)
# ============================================================================

def test_fc_001() -> None:
    """All providers return 503 -> system fails closed to deterministic safe net."""
    gw = _make_gateway()
    _fail_all_providers(gw, "503 Service Unavailable")
    result = asyncio.run(gw.generate_text(prompt="test"))
    assert result["provider"] == "deterministic"
    assert result["text"] and len(result["text"].strip()) > 0
    assert "503" not in result["text"], "503 error text must not leak into response"
    assert "Service Unavailable" not in result["text"]


def test_fc_002() -> None:
    """All providers return 429 -> circuit breakers trip, deterministic fallback."""
    gw = _make_gateway()
    _fail_all_providers(gw, "429 Too Many Requests")
    asyncio.run(gw.generate_text(prompt="t"))
    asyncio.run(gw.generate_text(prompt="t"))
    result = asyncio.run(gw.generate_text(prompt="t"))
    for key in ("cloudflare", "gemini", "codex", "claude", "ollama"):
        cb = gw.providers[key]
        assert cb.consecutive_failures >= 3 or cb.circuit_broken_until > 0, \
            f"Provider {key} circuit must be tripped after 429s"
    assert result["provider"] == "deterministic"
    assert "429" not in result["text"]
    assert "Too Many" not in result["text"]


def test_fc_003() -> None:
    """All providers timeout -> system fails closed to deterministic safe net."""
    gw = _make_gateway()
    _fail_all_providers(gw, "TimeoutError: upstream timed out after 30s")
    result = asyncio.run(gw.generate_text(prompt="test"))
    assert result["provider"] == "deterministic"
    assert result["text"] and len(result["text"].strip()) > 0
    assert "timeout" not in result["text"].lower(), "Timeout details must not leak"
    assert "timed out" not in result["text"].lower()


def test_fc_004() -> None:
    """503 from primary does not leak upstream response content into output."""
    gw = _make_gateway()
    leaked_content = "INTERNAL_SERVER_RESPONSE_BODY_secret=leaked"
    _fail_all_providers(gw, leaked_content)
    result = asyncio.run(gw.generate_text(prompt="test"))
    assert result["provider"] == "deterministic"
    assert leaked_content not in result["text"], \
        "Upstream content must not leak into deterministic response"
    assert leaked_content not in json.dumps(result), \
        "Upstream content must not appear in any result field"


def test_fc_005() -> None:
    """429 from primary does not leak upstream error details into output."""
    gw = _make_gateway()
    _fail_all_providers(gw, "HTTP 429 rate limit exceeded, retry-after: 60")
    result = asyncio.run(gw.generate_text(prompt="test"))
    assert result["provider"] == "deterministic"
    assert "429" not in json.dumps(result), "Rate-limit error code must not appear in result"
    assert "retry-after" not in json.dumps(result).lower()
    assert result["text"] != "", "Must return deterministic content, not error"


def test_fc_006() -> None:
    """Timeout from primary does not leak internal error messages."""
    gw = _make_gateway()
    _fail_all_providers(gw, "ConnectionError: http://internal:8080/api failed after 30s")
    result = asyncio.run(gw.generate_text(prompt="test"))
    assert result["provider"] == "deterministic"
    assert "internal:8080" not in json.dumps(result), "Internal endpoint must not leak"
    assert "ConnectionError" not in json.dumps(result), "Exception type must not leak"
    assert result["text"] is not None and len(result["text"]) > 0


def test_fc_007() -> None:
    """Deterministic safe net always returns non-empty content (absolute guarantee)."""
    gw = _make_gateway()
    _fail_all_providers(gw, "total_system_failure")
    for _ in range(5):
        result = asyncio.run(gw.generate_text(prompt="emergency test"))
        assert result["text"] is not None
        assert len(result["text"].strip()) > 0, "Deterministic net must always return content"
        assert result["provider"] == "deterministic"


def test_fc_008() -> None:
    """AIProviderRouter fails closed: all tiers exhausted -> deterministic safe net."""
    router = _make_ai_router()
    router.invoke_codex_chatgpt = mock.Mock(return_value={
        "status": "error", "provider": "CODEX_CHATGPT", "content": "",
        "error_message": "429 quota exceeded", "error_type": "rate_limit_exceeded",
        "route_used": "codex_chatgpt",
    })
    router.circuit_breakers["gemini"].trip()
    router.circuit_breakers["reasoning_proxy"].trip()
    router.invoke_deterministic_safe_net = mock.Mock(return_value={
        "status": "fallback", "provider": "DETERMINISTIC_SAFE_NET",
        "content": "deterministic fallback text", "route_used": "deterministic_safe_net",
    })
    result = router.call_ai(prompt="test")
    assert result.get("route_used") == "deterministic_safe_net", \
        f"Expected deterministic_safe_net, got {result}"
    assert result["content"], "Deterministic net must return content"
    assert "429" not in result.get("content", ""), "Error details must not leak"


# ============================================================================
# 3. NO-SECRET LEAKAGE  (TC-NS-*)
# ============================================================================

def test_ns_001() -> None:
    """providers/status response contains no API keys or secret patterns."""
    resp = _client.get("/api/v2/llm/providers/status")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    body = resp.text
    leaks = _scan_for_secrets(body)
    assert not leaks, f"Secret patterns found in providers/status: {leaks}"
    assert "api_key" not in body.lower() or "key_index" in body.lower(), \
        "Response should not contain raw api_key fields"


def test_ns_002() -> None:
    """providers/status response contains no tokens, passwords, or credentials."""
    resp = _client.get("/api/v2/llm/providers/status")
    assert resp.status_code == 200
    data = resp.json()
    body_str = json.dumps(data)
    leaks = _scan_for_secrets(body_str)
    assert not leaks, f"Secret tokens found in providers/status: {leaks}"
    for provider in data.get("data", {}).get("providers", []):
        for key_name in provider:
            assert "token" not in key_name.lower() or key_name == "circuit_open_remaining_s", \
                f"Provider field '{key_name}' may expose token data"
            assert "secret" not in key_name.lower(), \
                f"Provider field '{key_name}' may expose secret data"
            assert "password" not in key_name.lower(), \
                f"Provider field '{key_name}' may expose password"


def test_ns_003() -> None:
    """API error responses do not contain secret patterns."""
    resp = _client.post("/api/v2/llm/route-test", json={})
    body = resp.text
    leaks = _scan_for_secrets(body)
    assert not leaks, f"Secrets found in error response: {leaks}"
    resp = _client.get("/api/nonexistent-endpoint-12345")
    body = resp.text
    leaks = _scan_for_secrets(body)
    assert not leaks, f"Secrets found in 404 response: {leaks}"


def test_ns_004() -> None:
    """HybridRouter attempted_routes do not expose full API key values."""
    _reset_hybrid_router_circuits()
    hr = HybridRouter()
    with mock.patch("project.api_router._call_ollama", mock.Mock(side_effect=Exception("fail"))), \
         mock.patch("project.api_router._call_gemini", mock.Mock(return_value=(None, "429"))), \
         mock.patch("project.api_router._call_cloudflare_ai", mock.Mock(side_effect=Exception("fail"))):
        result = hr.generate(prompt="test", system_instruction="")
    attempted_str = json.dumps(result.get("attempted_routes", []))
    leaks = _scan_for_secrets(attempted_str)
    assert not leaks, f"Secrets found in attempted_routes: {leaks}"
    assert _FAKE_KEY not in attempted_str, "Full API key must not appear in attempted_routes"
    _reset_hybrid_router_circuits()


def test_ns_005() -> None:
    """OpenAPI schema does not contain secret values."""
    resp = _client.get("/openapi.json")
    assert resp.status_code == 200
    body = resp.text
    leaks = _scan_for_secrets(body)
    assert not leaks, f"Secrets found in OpenAPI schema: {leaks}"
    schema = resp.json()
    for path in schema.get("paths", {}):
        assert "secret" not in path.lower(), f"Suspicious path in schema: {path}"


def test_ns_006() -> None:
    """No response body across all standard endpoints contains known secret formats."""
    endpoints = [
        ("/api/v2/health", "GET", None),
        ("/api/v3/health", "GET", None),
        ("/api/health", "GET", None),
        ("/health", "GET", None),
        ("/api/v2/llm/providers/status", "GET", None),
        ("/api/v3/schema", "GET", None),
    ]
    all_leaks: list[str] = []
    for path, method, payload in endpoints:
        try:
            if method == "GET":
                resp = _client.get(path, timeout=10)
            else:
                resp = _client.post(path, json=payload, timeout=10)
            body = resp.text
            leaks = _scan_for_secrets(body)
            if leaks:
                all_leaks.append(f"{method} {path}: {leaks}")
        except Exception as exc:
            all_leaks.append(f"{method} {path}: EXCEPTION {exc}")
    assert not all_leaks, f"Secret patterns found across endpoints: {all_leaks}"


def test_ns_007() -> None:
    """AIProviderRouter.get_provider_health() does not expose credentials."""
    router = _make_ai_router()
    health = router.get_provider_health()
    health_str = json.dumps(health)
    leaks = _scan_for_secrets(health_str)
    assert not leaks, f"Secrets found in provider health: {leaks}"
    assert "api_key" not in health_str.lower()
    assert "token" not in health_str.lower()
    assert "secret" not in health_str.lower()


def test_ns_008() -> None:
    """CircuitBreakerState and ProviderState do not store or expose secrets."""
    cb = CircuitBreakerState(name="gemini")
    cb_str = json.dumps(cb.__dict__)
    leaks = _scan_for_secrets(cb_str)
    assert not leaks, f"Secrets found in CircuitBreakerState: {leaks}"
    assert "api_key" not in cb_str.lower()
    assert "token" not in cb_str.lower()
    assert "secret" not in cb_str.lower()


# ============================================================================
# Main entry point.
# ============================================================================

def _collect_tests() -> list:
    return [
        # Circuit breaker bypass prevention
        test_cb_001, test_cb_002, test_cb_003, test_cb_004,
        test_cb_005, test_cb_006, test_cb_007, test_cb_008,
        # Fail-closed on 503/429/timeout
        test_fc_001, test_fc_002, test_fc_003, test_fc_004,
        test_fc_005, test_fc_006, test_fc_007, test_fc_008,
        # No-secret leakage
        test_ns_001, test_ns_002, test_ns_003, test_ns_004,
        test_ns_005, test_ns_006, test_ns_007, test_ns_008,
    ]


def main() -> int:
    tests = _collect_tests()
    for test_fn in tests:
        try:
            test_fn()
        except AssertionError as e:
            runner.results.append({
                "id": test_fn.__name__,
                "name": test_fn.__doc__ or test_fn.__name__,
                "status": "FAILED",
                "details": str(e),
            })
            continue
        except Exception as e:
            runner.results.append({
                "id": test_fn.__name__,
                "name": test_fn.__doc__ or test_fn.__name__,
                "status": "ERROR",
                "details": f"{type(e).__name__}: {e}",
            })
            continue
        runner.results.append({
            "id": test_fn.__name__,
            "name": test_fn.__doc__ or test_fn.__name__,
            "status": "PASSED",
            "details": "",
        })

    passed = sum(1 for r in runner.results if r["status"] == "PASSED")
    failed = sum(1 for r in runner.results if r["status"] in ("FAILED", "ERROR"))
    report = {
        "schema_version": "redteam-v1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total": len(runner.results),
            "passed": passed,
            "failed": failed,
        },
        "test_cases": runner.results,
    }
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="ascii")
    print(json.dumps(report["summary"], indent=2))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
