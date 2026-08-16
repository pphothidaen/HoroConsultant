"""
project/tests/test_llm_multirouter.py
======================================
Unit & Integration Tests for Phase 4 Multi-Provider LLM Gateway:
  - Dynamic Circuit Breaker
  - Multi-Tier Failover Protocol (Cloudflare ➔ Gemini ➔ OpenAI ➔ Claude ➔ Ollama ➔ Deterministic)
  - Endpoints /api/v2/llm/providers/status and /api/v2/llm/route-test
"""

import pytest
import time
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from project.main import app
from project.core.llm_gateway import LLMGateway, llm_gateway

client = TestClient(app)


def test_llm_providers_status_endpoint():
    res = client.get("/api/v2/llm/providers/status")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "providers" in data["data"]
    providers = data["data"]["providers"]
    assert len(providers) >= 6
    keys = [p["key"] for p in providers]
    assert "cloudflare" in keys
    assert "gemini" in keys
    assert "openai" in keys
    assert "claude" in keys
    assert "ollama" in keys
    assert "deterministic" in keys


def test_llm_route_test_endpoint_deterministic_fallback():
    res = client.post("/api/v2/llm/route-test", json={"prompt": "ทดสอบคำพยากรณ์"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "result" in data
    assert "text" in data["result"]
    assert len(data["result"]["text"]) > 0


@pytest.mark.anyio
async def test_llm_gateway_tier_failover_sequence():
    gw = LLMGateway()

    # Enable all providers
    for p in gw.providers.values():
        p.is_configured = True

    # Mock all remote calls to raise exception
    gw._call_cloudflare = AsyncMock(side_effect=RuntimeError("Cloudflare rate limit"))
    gw._call_gemini = AsyncMock(side_effect=RuntimeError("Gemini quota exceeded"))
    gw._call_openai = AsyncMock(side_effect=RuntimeError("OpenAI timeout"))
    gw._call_claude = AsyncMock(side_effect=RuntimeError("Claude overload"))
    gw._call_ollama = AsyncMock(side_effect=RuntimeError("Ollama connection refused"))

    # When all remote providers fail, it MUST gracefully fallback to deterministic without raising exception
    res = await gw.generate_text("วิเคราะห์ดวงชะตา")
    assert res["provider"] == "deterministic"
    assert "บทสังเคราะห์คำพยากรณ์โหราศาสตร์และเบญจธาตุ" in res["text"]
    assert res["fallback_triggered"] is True


@pytest.mark.anyio
async def test_llm_gateway_circuit_breaker():
    gw = LLMGateway()
    p = gw.providers["cloudflare"]
    p.is_configured = True

    gw._call_cloudflare = AsyncMock(side_effect=RuntimeError("500 Server Error"))

    # Trigger 3 failures
    for _ in range(3):
        await gw.generate_text("Test", preferred_provider="cloudflare")

    # Circuit should now be open
    assert p.consecutive_failures == 3
    assert p.is_healthy is False
    assert gw._is_circuit_open(p) is True
    assert p.circuit_broken_until > time.time()


@pytest.mark.anyio
async def test_llm_gateway_successful_primary():
    gw = LLMGateway()
    gw.providers["gemini"].is_configured = True
    gw._call_gemini = AsyncMock(return_value="คำพยากรณ์จาก Gemini 2.5 Flash สำเร็จ")

    res = await gw.generate_text("คำนวณดิถี", preferred_provider="gemini")
    assert res["provider"] == "gemini"
    assert "Gemini 2.5 Flash" in res["text"]
    assert res["fallback_triggered"] is False
