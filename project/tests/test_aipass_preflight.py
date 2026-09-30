"""
project/tests/test_aipass_preflight.py
======================================
KAN-210 (M3): preflight health check for the aipass_bridge provider.

  - gateway.aipass_bridge_preflight() calls the worker MCP endpoint with
    tools/call for check_bridge_health (no Gemini round-trip spent)
  - parses the notebook grounding block and maps it to an ops status
  - exposes GET /api/v2/llm/aipass/preflight with fail-closed semantics:
    unreachable worker or bad auth = status "critical", never a silent OK
"""

import pytest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from project.core.llm_gateway import HORO_NOTEBOOK_SCOPE, llm_gateway
from project.main import app

client = TestClient(app)

HEALTHY_PAYLOAD = {
    "jsonrpc": "2.0", "id": 1,
    "result": {"content": [{"type": "text", "text": "{}"}], "contentIsJson": True},
}


def health_payload(status="grounded", attach="ok"):
    import json
    report = {
        "status": "healthy" if status == "grounded" else "degraded",
        "extension_status": "CONNECTED_AND_READY",
        "notebook": {
            "target_name": "Horo",
            "target_scope": HORO_NOTEBOOK_SCOPE,
            "last_attach_status": attach,
            "last_grounding_status": status,
            "attach_failures": 0,
        },
    }
    return {
        "jsonrpc": "2.0", "id": 1,
        "result": {"content": [{"type": "text", "text": json.dumps(report)}]},
    }


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload
        self.status_code = 200

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


class FakeAsyncClient:
    last_request = None
    next_payload = HEALTHY_PAYLOAD
    raise_error = None

    def __init__(self, **kwargs):
        FakeAsyncClient.last_init_kwargs = kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def post(self, url, headers=None, json=None):
        FakeAsyncClient.last_request = {"url": url, "headers": headers or {}, "json": json}
        if FakeAsyncClient.raise_error:
            raise FakeAsyncClient.raise_error
        return FakeResponse(FakeAsyncClient.next_payload)


@pytest.fixture
def fake_http(monkeypatch):
    FakeAsyncClient.last_request = None
    FakeAsyncClient.next_payload = HEALTHY_PAYLOAD
    FakeAsyncClient.raise_error = None
    monkeypatch.setattr("project.core.llm_gateway.httpx.AsyncClient", FakeAsyncClient)
    monkeypatch.setenv("AIPASS_BRIDGE_BASE_URL", "https://bridge.test")
    monkeypatch.setenv("AIPASS_BRIDGE_API_KEY", "test-client-key")
    return FakeAsyncClient


@pytest.mark.anyio
async def test_preflight_sends_check_bridge_health_and_parses_state(monkeypatch, fake_http):
    fake_http.next_payload = health_payload(status="grounded")
    report = await llm_gateway.aipass_bridge_preflight()
    req = fake_http.last_request
    assert req["url"] == "https://bridge.test/mcp"
    assert req["json"]["method"] == "tools/call"
    assert req["json"]["params"]["name"] == "check_bridge_health"
    assert req["headers"]["Authorization"] == "Bearer test-client-key"
    assert report["status"] == "ok"
    assert report["notebook"]["last_grounding_status"] == "grounded"
    assert report["notebook"]["target_scope"] == HORO_NOTEBOOK_SCOPE


@pytest.mark.anyio
async def test_preflight_maps_ungrounded_to_degraded(monkeypatch, fake_http):
    fake_http.next_payload = health_payload(status="ungrounded", attach="ok")
    report = await llm_gateway.aipass_bridge_preflight()
    assert report["status"] == "degraded"
    assert report["notebook"]["last_grounding_status"] == "ungrounded"


@pytest.mark.anyio
async def test_preflight_fails_closed_on_unreachable_worker(monkeypatch, fake_http):
    fake_http.raise_error = RuntimeError("connect timeout")
    report = await llm_gateway.aipass_bridge_preflight()
    assert report["status"] == "critical"
    assert "connect timeout" in report["error"]


def test_preflight_endpoint_reports_ok(monkeypatch, fake_http):
    fake_http.next_payload = health_payload(status="grounded")
    res = client.get("/api/v2/llm/aipass/preflight")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["data"]["status"] == "ok"


def test_preflight_endpoint_fails_closed(monkeypatch, fake_http):
    fake_http.raise_error = RuntimeError("worker unreachable")
    res = client.get("/api/v2/llm/aipass/preflight")
    assert res.status_code == 200
    data = res.json()
    assert data["data"]["status"] == "critical"
