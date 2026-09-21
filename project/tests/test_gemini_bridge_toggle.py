"""
project/tests/test_gemini_bridge_toggle.py
==========================================
TDD baseline tests for the Gemini Web Bridge toggle behavior across
HybridRouter (project/api_router.py) and ChatAssistantEngine
(project/core/chat_assistant_engine.py).

Ticket: TICKET-GEMINI-BRIDGE-20260921-A4-QA-PROVENANCE

RED/GREEN protocol (qa-regression-provenance):
  - RED run  : QA_FORCE_BRIDGE_TOGGLE_OFF=1 python3 -m pytest <client-file>
               <this file> -q
               -> bridge-on (toggle-dependent) assertions must FAIL while the
                  toggle stays mocked OFF.
  - GREEN run: python3 -m pytest <client-file> <this file> -q
               -> toggle mocked ON + mocked HTTP, all pass.

The toggle is controlled ONLY via monkeypatch inside each test (runs after
import, so it wins over project/api_router.py's load_dotenv(override=True)).
ALL HTTP is mocked with unittest.mock.patch("httpx.Client") mirroring
project/tests/test_api_router_external.py. No real network calls are made
(Ollama/Gemini/webhook collaborators are stubbed in the autouse fixture).
"""

from __future__ import annotations

import json
import logging
import os
from unittest.mock import MagicMock, patch

import pytest

import project.api_router as api_router_module
import project.core.gemini_bridge_client as gbc
from project.api_router import HybridRouter
from project.core.chat_assistant_engine import ChatAssistantEngine

# ---------------------------------------------------------------------------
# RED/GREEN switch: when set at test-module import time, _enable_bridge()
# leaves the toggle OFF so bridge-on assertions fail (RED baseline).
# ---------------------------------------------------------------------------

QA_FORCE_TOGGLE_OFF = os.getenv("QA_FORCE_BRIDGE_TOGGLE_OFF", "0") == "1"

FAKE_TOKEN = "qa-supersecret-token-9f8e7d6c"
BRIDGE_TEXT = "คำทำนายจาก Gemini Web Bridge"
BRIDGE_PDF = "https://example.com/consultation-report.pdf"
ENGINE_QUERY = "ในปี 2026 ควรเปิดร้านอาหารหรือไม่?"

BRIDGE_ENV_KEYS = (
    "GEMINI_WEB_BRIDGE_ENABLED",
    "GEMINI_WEB_BRIDGE_URL",
    "GEMINI_WEB_BRIDGE_TOKEN",
    "GEMINI_WEB_BRIDGE_SCOPE",
    "GEMINI_WEB_BRIDGE_TOOL",
    "GEMINI_WEB_BRIDGE_TIMEOUT_S",
)
_CLOUD_ENV_KEYS = (
    "VERCEL",
    "VERCEL_ENV",
    "SPACE_ID",
    "FLY_APP_NAME",
    "HF_SPACE_ID",
    "RAILWAY_STATIC_URL",
    "ENVIRONMENT",
)
_EXTRA_ENV_KEYS = (
    "DISABLE_LOCAL_OLLAMA",
    "AI_ZERO_COST_ONLY",
    "CLOUDFLARE_ACCOUNT_ID",
    "CLOUDFLARE_AI_TOKEN",
    "GOOGLE_AI_STUDIO_API_KEY",
    "GOOGLE_AI_STUDIO_API_KEY2",
)
_ALL_ENV_KEYS = BRIDGE_ENV_KEYS + _CLOUD_ENV_KEYS + _EXTRA_ENV_KEYS


def _clear_env(monkeypatch) -> None:
    for key in _ALL_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def _enable_bridge(monkeypatch) -> None:
    """Force local-mode env and enable the bridge (unless RED mode forces off)."""
    _clear_env(monkeypatch)
    if QA_FORCE_TOGGLE_OFF:
        return
    monkeypatch.setenv("GEMINI_WEB_BRIDGE_ENABLED", "true")
    monkeypatch.setenv("GEMINI_WEB_BRIDGE_TOKEN", FAKE_TOKEN)


@pytest.fixture(autouse=True)
def _hermetic_router_env(monkeypatch):
    """Force deterministic local-mode routing and stub all network collaborators."""
    _clear_env(monkeypatch)
    gbc._BRIDGE_CIRCUIT_BREAKER.clear()
    # Module-level globals captured at import time must be neutralized directly
    monkeypatch.setattr(api_router_module, "CLOUDFLARE_ACCOUNT_ID", "")
    monkeypatch.setattr(api_router_module, "CLOUDFLARE_AI_TOKEN", "")
    monkeypatch.setattr(api_router_module, "_gemini_keys", lambda: [])
    # Never touch real Ollama/Gemini HTTP from HybridRouter.generate()
    monkeypatch.setattr(
        api_router_module,
        "_call_ollama",
        lambda model, prompt, system_instruction: (None, "mocked_local"),
    )
    monkeypatch.setattr(
        api_router_module,
        "_call_gemini",
        lambda model, key, prompt, system_instruction: (None, "mocked_gemini"),
    )
    # Never dispatch a real Telegram/webhook outage alert
    monkeypatch.setattr(
        api_router_module, "_trigger_gemini_telegram_alert", MagicMock()
    )
    yield
    gbc._BRIDGE_CIRCUIT_BREAKER.clear()


# ---------------------------------------------------------------------------
# Deterministic engine collaborators (RAG + pills) for byte-identical compares
# ---------------------------------------------------------------------------

FIXED_CITATIONS = [
    {"id": "gc-001", "source": "Test Classic", "snippet": "snippet-for-test", "score": 0.9}
]
FIXED_PILLS = [
    {
        "category": "career_wealth",
        "category_name": "career",
        "id": "pill-1",
        "icon": "*",
        "label": "pill",
        "prompt": "p",
    }
]


@pytest.fixture
def deterministic_engine(monkeypatch):
    monkeypatch.setattr(
        ChatAssistantEngine,
        "retrieve_rag_citations",
        lambda self, query, context, top_k=2: [dict(c) for c in FIXED_CITATIONS],
    )
    monkeypatch.setattr(
        ChatAssistantEngine,
        "generate_dynamic_pills",
        lambda self, context: [dict(p) for p in FIXED_PILLS],
    )
    return ChatAssistantEngine()


def _http_mock(json_data=None, status_code: int = 200):
    """Mirror the httpx.Client mock pattern from test_api_router_external.py."""
    mock_client = MagicMock()
    mock_instance = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = json_data
    mock_instance.post.return_value = mock_resp
    mock_client.return_value.__enter__.return_value = mock_instance
    return mock_client, mock_instance


def _rpc_ok(text: str = BRIDGE_TEXT, structured=None) -> dict:
    result: dict = {"content": [{"type": "text", "text": text}]}
    if structured is not None:
        result["structuredContent"] = structured
    return {"jsonrpc": "2.0", "id": 1, "result": result}


# ---------------------------------------------------------------------------
# HybridRouter._build_routes
# ---------------------------------------------------------------------------

def test_build_routes_bridge_on_first_route_is_gemini_mcp(monkeypatch):
    _enable_bridge(monkeypatch)
    routes = HybridRouter()._build_routes()
    assert routes, "expected non-empty route chain when bridge enabled"
    assert routes[0]["type"] == "gemini_mcp"
    assert routes[0]["model"] == "gemini-mcp:horo_consult"
    assert routes[0]["key"] is None


def test_build_routes_bridge_off_legacy_ordering_intact(monkeypatch):
    routes = HybridRouter()._build_routes()
    types = [r["type"] for r in routes]
    assert "gemini_mcp" not in types
    assert types[:3] == ["ollama", "ollama", "ollama"]
    assert [r["model"] for r in routes[:3]] == [
        "qwen2.5:7b",
        "qwen2.5-coder:7b",
        "llama3:8b",
    ]


# ---------------------------------------------------------------------------
# HybridRouter.generate() dispatch
# ---------------------------------------------------------------------------

def test_generate_dispatch_gemini_mcp_success(monkeypatch):
    _enable_bridge(monkeypatch)
    bridge_mock = MagicMock(return_value=({"text": BRIDGE_TEXT, "pdf_url": None}, "ok"))
    monkeypatch.setattr(api_router_module, "call_bridge_tool", bridge_mock)

    result = HybridRouter().generate("คำถาม", "คำสั่งระบบ")

    assert result["text"] == BRIDGE_TEXT
    assert result["route"] == "gemini_mcp"
    assert result["model_used"] == "gemini-mcp:horo_consult"
    assert result["reason"] == "ok"
    assert result["attempted_routes"] == []
    # System instruction is prepended into the single bridge query argument
    sent_query = bridge_mock.call_args[0][0]
    assert "คำสั่งระบบ" in sent_query
    assert "คำถาม" in sent_query


def test_generate_bridge_failure_falls_through_to_next_route(monkeypatch):
    _enable_bridge(monkeypatch)
    monkeypatch.setattr(
        api_router_module,
        "call_bridge_tool",
        MagicMock(return_value=(None, "http_503")),
    )
    monkeypatch.setattr(
        api_router_module,
        "_call_ollama",
        lambda model, prompt, system_instruction: ("ollama text", "ok"),
    )

    result = HybridRouter().generate("คำถาม")

    assert result["text"] == "ollama text"
    assert result["route"] == "ollama"
    assert result["attempted_routes"], "bridge failure must be recorded"
    assert result["attempted_routes"][0]["reason"] == "http_503"
    assert "gemini-mcp" in result["attempted_routes"][0]["route"]


# ---------------------------------------------------------------------------
# ChatAssistantEngine.generate_consultation_sync toggle behavior
# ---------------------------------------------------------------------------

def test_engine_bridge_on_success_uses_bridge_output(deterministic_engine, monkeypatch):
    _enable_bridge(monkeypatch)
    monkeypatch.setattr(
        gbc,
        "call_bridge_tool",
        MagicMock(return_value=({"text": BRIDGE_TEXT, "pdf_url": BRIDGE_PDF}, "ok")),
    )

    resp = deterministic_engine.generate_consultation_sync(ENGINE_QUERY)

    assert resp["status"] == "success"
    assert resp["content"] == BRIDGE_TEXT
    assert resp["meta"]["model"].startswith("gemini-web-bridge:")
    assert resp["meta"]["route"] == "gemini_mcp"
    assert resp["meta"]["pdf_url"] == BRIDGE_PDF
    assert resp["citations"] == FIXED_CITATIONS


def test_engine_bridge_failure_output_byte_identical_to_toggle_off(
    deterministic_engine, monkeypatch
):
    # Baseline run: toggle OFF
    _clear_env(monkeypatch)
    result_off = deterministic_engine.generate_consultation_sync(ENGINE_QUERY)
    assert result_off["meta"]["model"] == "HoroConsultant-Metaphysics-Pro"

    # Toggle ON but bridge fails -> must fall back byte-identically
    _enable_bridge(monkeypatch)
    monkeypatch.setattr(
        gbc,
        "call_bridge_tool",
        MagicMock(return_value=(None, "http_503")),
    )
    result_on = deterministic_engine.generate_consultation_sync(ENGINE_QUERY)

    assert result_on == result_off
    assert (
        json.dumps(result_on, ensure_ascii=False, sort_keys=True)
        == json.dumps(result_off, ensure_ascii=False, sort_keys=True)
    )
    assert result_on["meta"]["model"] == "HoroConsultant-Metaphysics-Pro"
    assert "route" not in result_on["meta"]
    assert "pdf_url" not in result_on["meta"]


def test_engine_toggle_off_template_output_unchanged(deterministic_engine):
    resp = deterministic_engine.generate_consultation_sync(ENGINE_QUERY)
    assert resp["status"] == "success"
    assert resp["meta"]["model"] == "HoroConsultant-Metaphysics-Pro"
    assert "route" not in resp["meta"]
    assert "pdf_url" not in resp["meta"]
    assert resp["content"].startswith("### 🔮 คำชี้แนะจากซินแส AI")
    assert resp["citations"] == FIXED_CITATIONS
    assert resp["follow_up_chips"] == FIXED_PILLS


# ---------------------------------------------------------------------------
# Security / adversarial: bearer token must never leak to logs or responses
# ---------------------------------------------------------------------------

def test_no_token_leakage_in_logs_or_returned_dicts(caplog, deterministic_engine, monkeypatch):
    _enable_bridge(monkeypatch)
    mock_client, _ = _http_mock(
        json_data=_rpc_ok(structured={"pdf_url": BRIDGE_PDF})
    )
    with caplog.at_level(logging.DEBUG):
        with patch("httpx.Client", mock_client):
            router_result = HybridRouter().generate("คำถาม")
        with patch("httpx.Client", mock_client):
            engine_result = deterministic_engine.generate_consultation_sync(ENGINE_QUERY)

    # Sanity: bridge path actually exercised with the fake token configured
    assert router_result["text"] == BRIDGE_TEXT
    assert engine_result["content"] == BRIDGE_TEXT

    assert FAKE_TOKEN not in caplog.text
    assert FAKE_TOKEN not in json.dumps(router_result, ensure_ascii=False, default=str)
    assert FAKE_TOKEN not in json.dumps(engine_result, ensure_ascii=False, default=str)
