"""
project/tests/test_discipline_gate.py
=====================================
KAN-209 (M2): fail-closed discipline gate for notebook-grounded
consultation (gemini-web-bridge api-spec §9.2, invariant G-9).

  - Only notebook-covered question domains may reach aipass_bridge
    (career/finance/love/health/family/timing/guidance/bazi/numerology/
    thai_astrology).
  - Explicit other disciplines (ziwei, qimen, iching, uranian, xuankong,
    zeji) MUST route back to the existing hybrid_router path — silently
    answering an unsupported discipline from the notebook is forbidden.
  - When the provider is not configured (no consent env), even supported
    categories stay on the existing path.
"""

import pytest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from project.core.llm_gateway import HORO_NOTEBOOK_SCOPE, llm_gateway, notebook_grounding_allowed
from project.main import app

client = TestClient(app)


BASE_REQ = {
    "birth_datetime": "1990-05-14 08:30:00",
    "longitude": 100.5018,
    "utc_offset_hours": 7.0,
    "query": "อาชีพที่เหมาะกับดวงนี้คืออะไร",
    "language": "th",
}


def grounded_generate_mock():
    return AsyncMock(return_value={
        "text": "คำตอบจาก notebook",
        "provider": "aipass_bridge",
        "model": "AIPASS Bridge (Notebook-Grounded horo_consult)",
        "latency_ms": 1000.0,
        "fallback_triggered": False,
        "provenance": {
            "grounding": HORO_NOTEBOOK_SCOPE,
            "grounding_verified": True,
            "citations": 3,
            "cited_sources": ["notebook://horo/p1"],
            "model": "gemini-web-notebook",
        },
    })


def configure_aipass():
    llm_gateway.providers["aipass_bridge"].is_configured = True


@pytest.mark.parametrize("category", [
    "career", "finance", "love", "health", "family", "timing", "guidance",
    "bazi", "numerology", "thai_astrology",
])
def test_supported_categories_allow_notebook_grounding(category):
    assert notebook_grounding_allowed(category) is True


@pytest.mark.parametrize("category", [
    "ziwei", "qimen", "iching", "uranian", "xuankong", "zeji", "", None,
    "totally_unknown",
])
def test_unsupported_disciplines_are_rejected(category):
    assert notebook_grounding_allowed(category) is False


def test_supported_category_routes_to_aipass_bridge(monkeypatch):
    configure_aipass()
    mock_generate = grounded_generate_mock()
    monkeypatch.setattr("project.routers.v2.llm_gateway.generate_text", mock_generate)
    mock_hybrid = patch("project.routers.v2.hybrid_router.generate")
    with mock_hybrid as hybrid:
        res = client.post("/api/v2/interpret/focused", json=BASE_REQ)
    assert res.status_code == 200
    data = res.json()
    assert data["metadata"]["routing"] == "aipass_bridge"
    assert data["interpretation"] == "คำตอบจาก notebook"
    assert data["metadata"]["provenance"]["grounding"] == HORO_NOTEBOOK_SCOPE
    mock_generate.assert_awaited_once()
    kwargs = mock_generate.await_args.kwargs
    assert kwargs["preferred_provider"] == "aipass_bridge"
    assert "scope" not in (kwargs.get("birth_context") or {})
    assert kwargs["birth_context"]["day_master"] == data["day_master"]
    hybrid.assert_not_called()


def test_unsupported_discipline_fails_closed_to_hybrid_router(monkeypatch):
    configure_aipass()
    mock_generate = grounded_generate_mock()
    monkeypatch.setattr("project.routers.v2.llm_gateway.generate_text", mock_generate)
    req = dict(BASE_REQ, query="ดูดวงมงคลแบบฉี่หรี่")
    with patch("project.routers.v2.question_focus_router.classify_question",
               return_value=("ziwei", 0.95)), \
         patch("project.routers.v2.hybrid_router.generate",
               return_value={"text": "คำตอบจาก node prompts"}) as hybrid:
        res = client.post("/api/v2/interpret/focused", json=req)
    assert res.status_code == 200
    data = res.json()
    assert data["metadata"]["routing"] == "hybrid_router"
    assert data["interpretation"] == "คำตอบจาก node prompts"
    assert data["metadata"]["provenance"] is None
    mock_generate.assert_not_awaited()
    hybrid.assert_called_once()


def test_unconfigured_provider_stays_on_existing_path(monkeypatch):
    mock_generate = grounded_generate_mock()
    monkeypatch.setattr("project.routers.v2.llm_gateway.generate_text", mock_generate)
    monkeypatch.setattr("project.routers.v2.llm_gateway.providers", {})
    with patch("project.routers.v2.hybrid_router.generate",
               return_value={"text": "คำตอบจาก node prompts"}) as hybrid:
        res = client.post("/api/v2/interpret/focused", json=BASE_REQ)
    assert res.status_code == 200
    assert res.json()["metadata"]["routing"] == "hybrid_router"
    mock_generate.assert_not_awaited()
    hybrid.assert_called_once()
