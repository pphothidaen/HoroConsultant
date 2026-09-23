"""
gemini_bridge_client.py - Gemini Web Bridge MCP Client
=======================================================
Client for the Gemini Web Bridge Cloudflare Worker (MCP over JSON-RPC).
Opt-in via GEMINI_WEB_BRIDGE_ENABLED; reads config from env dynamically on
every call so the toggle can flip without a process restart.

Contract (frozen):
  - is_gemini_bridge_enabled() -> bool
  - call_bridge_tool(query, *, tool, birth_context, response_format, scope,
                     timeout_s) -> tuple[Optional[dict], str]
    Success: ({"text": <str>, "pdf_url": <str|None>}, "ok")
    Failure: (None, reason)
    Reasons: "disabled", "no_config", "circuit_open", "http_<status>",
             "timeout", "empty_response", "error:<detail>"
"""

from __future__ import annotations

import itertools
import json
import logging
import os
import time
from typing import Any, Optional

import httpx

logger = logging.getLogger("gemini_bridge_client")

# ---------------------------------------------------------------------------
# Configuration defaults (env vars override at call time, never cached)
# ---------------------------------------------------------------------------

GEMINI_BRIDGE_DEFAULT_URL = "https://gemini-web-bridge.pansakorn-pho.workers.dev"
GEMINI_BRIDGE_DEFAULT_SCOPE = "notebook:b55f1ee0-384e-4bdf-ab1b-e2ee3b0063a0"
GEMINI_BRIDGE_DEFAULT_TOOL = "horo_consult"
GEMINI_BRIDGE_DEFAULT_TIMEOUT_S = 90.0

_TRUE_VALUES = ("true", "1", "yes")


def _bridge_url() -> str:
    """Resolve bridge base URL from env (dynamic read, default fallback).

    An explicitly-set but empty (or whitespace-only) env var yields an empty
    URL (no_config path), distinct from the var being unset (default fallback).
    """
    raw = os.getenv("GEMINI_WEB_BRIDGE_URL")
    if raw is None:
        return GEMINI_BRIDGE_DEFAULT_URL.strip()
    return raw.strip()


def _bridge_token() -> str:
    """Resolve bridge bearer token from env (dynamic read, no default)."""
    return (os.getenv("GEMINI_WEB_BRIDGE_TOKEN", "") or "").strip()


def _bridge_tool() -> str:
    """Resolve MCP tool name from env (dynamic read, default fallback)."""
    return (
        os.getenv("GEMINI_WEB_BRIDGE_TOOL", "") or GEMINI_BRIDGE_DEFAULT_TOOL
    ).strip() or GEMINI_BRIDGE_DEFAULT_TOOL


def _bridge_timeout_s() -> float:
    """Resolve request timeout in seconds from env (dynamic read)."""
    raw = (os.getenv("GEMINI_WEB_BRIDGE_TIMEOUT_S", "") or "").strip()
    try:
        return float(raw) if raw else GEMINI_BRIDGE_DEFAULT_TIMEOUT_S
    except (TypeError, ValueError):
        return GEMINI_BRIDGE_DEFAULT_TIMEOUT_S


# ---------------------------------------------------------------------------
# Toggle check (dynamic - no import-time caching)
# ---------------------------------------------------------------------------

def is_gemini_bridge_enabled() -> bool:
    """
    Return True iff GEMINI_WEB_BRIDGE_ENABLED is truthy AND URL AND TOKEN are
    non-empty. Reads os.getenv dynamically on every call so the toggle can
    flip without a restart.
    """
    if not _bridge_flag_on():
        return False
    return bool(_bridge_url()) and bool(_bridge_token())


def _bridge_flag_on() -> bool:
    """Return True iff GEMINI_WEB_BRIDGE_ENABLED is truthy (dynamic read)."""
    flag = (os.getenv("GEMINI_WEB_BRIDGE_ENABLED", "false") or "").strip().lower()
    return flag in _TRUE_VALUES


# ---------------------------------------------------------------------------
# Circuit breaker (mirrors project/api_router.py route breaker pattern)
# ---------------------------------------------------------------------------

_BRIDGE_CIRCUIT_BREAKER: dict[str, float] = {}
BRIDGE_CIRCUIT_COOLDOWN_SECONDS: float = 60.0


def _is_bridge_circuit_open() -> bool:
    """Return True if the bridge recently failed hard and is in cooldown."""
    cooldown_until = _BRIDGE_CIRCUIT_BREAKER.get("bridge", 0.0)
    return time.monotonic() < cooldown_until


def _trip_bridge_circuit(cooldown: float = BRIDGE_CIRCUIT_COOLDOWN_SECONDS) -> None:
    """Trip circuit breaker after a hard failure (429/503/timeout/error)."""
    _BRIDGE_CIRCUIT_BREAKER["bridge"] = time.monotonic() + cooldown
    logger.info(f"[CircuitBreaker] Tripped gemini bridge for {cooldown}s cooldown.")


def _maybe_trip_bridge_circuit(reason: str) -> None:
    """Trip the breaker only on hard failure reasons per contract."""
    if (
        reason == "timeout"
        or reason.startswith("http_422")
        or reason.startswith("http_429")
        or reason.startswith("http_503")
        or reason.startswith("error:")
    ):
        _trip_bridge_circuit()


# ---------------------------------------------------------------------------
# JSON-RPC request id (monotonic int)
# ---------------------------------------------------------------------------

_REQUEST_ID_COUNTER = itertools.count(1)


# ---------------------------------------------------------------------------
# Response parsing helpers
# ---------------------------------------------------------------------------

def _find_pdf_url(obj: Any, depth: int = 0) -> Optional[str]:
    """Recursively search a parsed JSON object for a 'pdf_url' value.

    Depth-bounded and scheme allow-listed (finding GB-RT-001/GB-RT-002):
    only http(s) URLs are surfaced, pathological nesting returns None.
    """
    if depth > 24:
        return None
    if isinstance(obj, dict):
        val = obj.get("pdf_url")
        if isinstance(val, str) and val.strip():
            candidate = val.strip()
            if candidate.startswith(("http://", "https://")):
                return candidate
        for child in obj.values():
            found = _find_pdf_url(child, depth + 1)
            if found:
                return found
    elif isinstance(obj, list):
        for child in obj:
            found = _find_pdf_url(child, depth + 1)
            if found:
                return found
    return None


def _parse_bridge_result(data: Any) -> tuple[Optional[dict], str]:
    """
    Extract ({"text", "pdf_url"}, "ok") from a JSON-RPC success response.
    Returns (None, reason) on parse-level failure.
    """
    if not isinstance(data, dict):
        return None, "error:invalid_jsonrpc_shape"

    err = data.get("error")
    if err is not None:
        if isinstance(err, dict):
            detail = err.get("message") or err.get("code") or "unknown"
        else:
            detail = str(err)
        return None, f"error:{detail}"

    result = data.get("result")
    if not isinstance(result, dict):
        return None, "error:missing_result"

    content_items = result.get("content")
    if not isinstance(content_items, list):
        content_items = []

    # Primary: result.content[0].text (first text item)
    text = ""
    for item in content_items:
        if isinstance(item, dict) and item.get("type") == "text" and item.get("text"):
            text = str(item["text"]).strip()
            break

    # Fallback: scan all content text items for a JSON object with pdf_url
    pdf_url = None
    structured = result.get("structuredContent")
    if isinstance(structured, dict):
        pdf_url = _find_pdf_url(structured)
    if not pdf_url:
        for item in content_items:
            if not (isinstance(item, dict) and item.get("text")):
                continue
            try:
                parsed = json.loads(item["text"])
            except (TypeError, ValueError):
                continue
            pdf_url = _find_pdf_url(parsed)
            if pdf_url:
                break

    if not text:
        return None, "empty_response"

    return {"text": text, "pdf_url": pdf_url}, "ok"


# ---------------------------------------------------------------------------
# Public MCP tool caller
# ---------------------------------------------------------------------------

def call_bridge_tool(
    query: str,
    *,
    tool: Optional[str] = None,
    birth_context: Optional[dict] = None,
    response_format: str = "text",
    scope: Optional[str] = None,
    timeout_s: Optional[float] = None,
) -> tuple[Optional[dict], str]:
    """
    Call the Gemini Web Bridge Worker MCP endpoint (tools/call).

    Returns (None, reason) on failure or ({"text", "pdf_url"}, "ok") on success.
    Callers prepend any system instruction into `query` themselves.
    """
    if not _bridge_flag_on():
        return None, "disabled"

    url = _bridge_url()
    token = _bridge_token()
    if not url or not token:
        return None, "no_config"

    if _is_bridge_circuit_open():
        logger.debug("[Bridge] [CIRCUIT OPEN] Skipping call (cooldown active)")
        return None, "circuit_open"

    tool_name = (tool or _bridge_tool()).strip() or GEMINI_BRIDGE_DEFAULT_TOOL

    if timeout_s is not None:
        effective_timeout = float(timeout_s)
    else:
        effective_timeout = _bridge_timeout_s()

    # scope: explicit arg wins, else env default; omit from body if empty
    effective_scope = scope if scope is not None else (
        os.getenv("GEMINI_WEB_BRIDGE_SCOPE", "") or GEMINI_BRIDGE_DEFAULT_SCOPE
    )
    effective_scope = (effective_scope or "").strip()

    arguments: dict[str, Any] = {
        "query": query,
        "response_format": response_format,
    }
    if birth_context:
        arguments["birth_context"] = birth_context
    if effective_scope:
        arguments["scope"] = effective_scope

    payload: dict[str, Any] = {
        "jsonrpc": "2.0",
        "id": next(_REQUEST_ID_COUNTER),
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }

    try:
        with httpx.Client(timeout=effective_timeout) as client:
            t0 = time.monotonic()
            res = client.post(f"{url.rstrip('/')}/mcp", json=payload, headers=headers)
            elapsed = round((time.monotonic() - t0) * 1000)
    except httpx.TimeoutException:
        logger.warning(f"[Bridge:{tool_name}] Timeout after {effective_timeout}s")
        _trip_bridge_circuit()
        return None, "timeout"
    except Exception as exc:
        logger.warning(f"[Bridge:{tool_name}] Exception: {exc}")
        _trip_bridge_circuit()
        return None, f"error:{exc}"

    if res.status_code != 200:
        reason = f"http_{res.status_code}"
        logger.warning(f"[Bridge:{tool_name}] HTTP {res.status_code}")
        _maybe_trip_bridge_circuit(reason)
        return None, reason

    try:
        data = res.json()
    except Exception as exc:
        logger.warning(f"[Bridge:{tool_name}] Invalid JSON response: {exc}")
        _trip_bridge_circuit()
        return None, f"error:invalid_json:{exc}"

    try:
        parsed, reason = _parse_bridge_result(data)
    except Exception as exc:
        logger.warning(f"[Bridge:{tool_name}] Response parse failure: {exc}")
        return None, f"error:parse_failure:{exc}"

    if parsed is None:
        logger.warning(f"[Bridge:{tool_name}] [FAIL] reason={reason} ({elapsed}ms)")
        _maybe_trip_bridge_circuit(reason)
        return None, reason

    # Success — clear any prior trip so half-open -> closed transition works.
    _BRIDGE_CIRCUIT_BREAKER.pop("bridge", None)
    logger.info(f"[Bridge:{tool_name}] [OK] ({elapsed}ms)")
    return parsed, "ok"


