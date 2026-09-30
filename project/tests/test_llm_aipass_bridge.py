"""
project/tests/test_llm_aipass_bridge.py
========================================
Contract tests for the aipass_bridge provider (KAN-208) against the
Gemini Web Bridge api-spec (docs/api-spec.md, invariants G-1/G-2/G-8):

  - tier placement (aipass_bridge = 3, downstream renumbered)
  - consent gate (HORO_BRIDGE_CONSENT) — privacy opt-in per deployment
  - hard guard: only notebook-grounded answers are accepted (G-1),
    including the GCP-fallback leak shape (no notebookGrounding at all)
  - request shape: JSON-RPC tools/call for horo_consult, no `scope`
    argument (G-2), birth_context passthrough, 240s timeout budget
  - failover: every rejection rolls over to the deterministic tier
"""

import pytest
from unittest.mock import patch

from project.core.llm_gateway import (
    AIPASS_BRIDGE_TIMEOUT_S,
    HORO_NOTEBOOK_SCOPE,
    LLMGateway,
)

ENV = {
    "AIPASS_BRIDGE_BASE_URL": "https://bridge.test",
    "AIPASS_BRIDGE_API_KEY": "test-client-key",
    "HORO_BRIDGE_CONSENT": "true",
}


def make_gateway(monkeypatch, env=ENV):
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    gw = LLMGateway()
    # Pin the other tiers off so failover deterministically lands on the
    # deterministic tier instead of touching real external services.
    for key in ("cloudflare", "gemini", "codex", "claude", "ollama"):
        gw.providers[key].is_configured = False
    return gw


def rpc_result(text="คำตอบที่ grounding แล้ว", verified=True, scope=HORO_NOTEBOOK_SCOPE, citations=3):
    result = {
        "content": [{"type": "text", "text": text}],
        "bridgeScope": {"used": scope, "active": "app", "restored": True, "attachedInPlace": True},
    }
    if verified is not None:
        result["notebookGrounding"] = {
            "requested": "Horo", "attached": True, "verified": verified,
            "citationCount": citations, "citedSources": ["notebook://horo/p1"],
        }
    return {"jsonrpc": "2.0", "id": 1, "result": result}


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


class FakeAsyncClient:
    last_request = None
    next_payload = rpc_result()

    def __init__(self, **kwargs):
        FakeAsyncClient.last_init_kwargs = kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def post(self, url, headers=None, json=None):
        FakeAsyncClient.last_request = {"url": url, "headers": headers or {}, "json": json}
        return FakeResponse(FakeAsyncClient.next_payload)


@pytest.fixture
def fake_http(monkeypatch):
    FakeAsyncClient.last_request = None
    FakeAsyncClient.next_payload = rpc_result()
    monkeypatch.setattr("project.core.llm_gateway.httpx.AsyncClient", FakeAsyncClient)
    return FakeAsyncClient


@pytest.mark.anyio
async def test_tiers_renumbered_with_aipass_bridge_at_three(monkeypatch):
    gw = make_gateway(monkeypatch)
    tiers = {k: p.tier for k, p in gw.providers.items()}
    assert tiers == {
        "cloudflare": 1, "gemini": 2, "aipass_bridge": 3,
        "codex": 4, "claude": 5, "ollama": 6, "deterministic": 7,
    }


@pytest.mark.anyio
async def test_consent_gate_blocks_provider_without_opt_in(monkeypatch, fake_http):
    for k, v in ENV.items():
        if k != "HORO_BRIDGE_CONSENT":
            monkeypatch.setenv(k, v)
    monkeypatch.delenv("HORO_BRIDGE_CONSENT", raising=False)
    gw = LLMGateway()
    for key in ("cloudflare", "gemini", "codex", "claude", "ollama"):
        gw.providers[key].is_configured = False
    assert gw.providers["aipass_bridge"].is_configured is False
    # generate_text must skip the unconfigured provider entirely
    res = await gw.generate_text("คำถาม", preferred_provider="aipass_bridge")
    assert res["provider"] == "deterministic"
    assert fake_http.last_request is None, "no HTTP call may be made without consent"


@pytest.mark.anyio
async def test_success_path_returns_grounding_provenance(monkeypatch, fake_http):
    gw = make_gateway(monkeypatch)
    res = await gw.generate_text("อาชีพที่เหมาะกับดวงนี้", preferred_provider="aipass_bridge")
    assert res["provider"] == "aipass_bridge"
    assert res["provenance"]["grounding"] == HORO_NOTEBOOK_SCOPE
    assert res["provenance"]["grounding_verified"] is True
    assert res["provenance"]["citations"] == 3


@pytest.mark.anyio
async def test_request_shape_no_scope_and_birth_context_passthrough(monkeypatch, fake_http):
    gw = make_gateway(monkeypatch)
    birth = {"birth_datetime": "1990-05-14T08:30:00", "day_master": "甲木"}
    await gw.generate_text("คำถาม", system_instruction="[ข้อจำกัด] ตอบเฉพาะ BaZi",
                           preferred_provider="aipass_bridge", birth_context=birth)
    req = fake_http.last_request
    assert req["url"] == "https://bridge.test/mcp"
    assert req["headers"]["Authorization"] == "Bearer test-client-key"
    body = req["json"]
    assert body["method"] == "tools/call"
    assert body["params"]["name"] == "horo_consult"
    args = body["params"]["arguments"]
    assert "scope" not in args, "api-spec invariant G-2: scope disables grounding"
    assert args["response_format"] == "text"
    assert args["birth_context"] == birth
    assert args["query"].startswith("[ข้อจำกัด] ตอบเฉพาะ BaZi")
    assert fake_http.last_init_kwargs["timeout"] == AIPASS_BRIDGE_TIMEOUT_S
    assert AIPASS_BRIDGE_TIMEOUT_S >= 180


@pytest.mark.anyio
async def test_gcp_fallback_leak_is_rejected(monkeypatch, fake_http):
    fake_http.next_payload = rpc_result(verified=None)  # no notebookGrounding field at all
    gw = make_gateway(monkeypatch)
    res = await gw.generate_text("คำถาม", preferred_provider="aipass_bridge")
    assert res["provider"] == "deterministic"
    assert res["fallback_triggered"] is True


@pytest.mark.anyio
async def test_unverified_grounding_is_rejected(monkeypatch, fake_http):
    fake_http.next_payload = rpc_result(verified=False)
    gw = make_gateway(monkeypatch)
    res = await gw.generate_text("คำถาม", preferred_provider="aipass_bridge")
    assert res["provider"] == "deterministic"


@pytest.mark.anyio
async def test_wrong_scope_is_rejected(monkeypatch, fake_http):
    fake_http.next_payload = rpc_result(scope="notebook:some-other-notebook")
    gw = make_gateway(monkeypatch)
    res = await gw.generate_text("คำถาม", preferred_provider="aipass_bridge")
    assert res["provider"] == "deterministic"


@pytest.mark.anyio
async def test_jsonrpc_error_fails_over(monkeypatch, fake_http):
    fake_http.next_payload = {"jsonrpc": "2.0", "id": 1,
                              "error": {"code": -32000, "message": "notebook attach failed"}}
    gw = make_gateway(monkeypatch)
    res = await gw.generate_text("คำถาม", preferred_provider="aipass_bridge")
    assert res["provider"] == "deterministic"
    assert gw.providers["aipass_bridge"].consecutive_failures == 1
