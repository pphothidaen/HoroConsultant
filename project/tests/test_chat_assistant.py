"""
project/tests/test_chat_assistant.py
====================================
Unit and Integration tests for Metaphysics AI Live Consultant Chat Assistant.
Tests engine context synthesis, RAG citations, dynamic prompt pills,
SSE streaming endpoint, and JSON consultation endpoint.
"""

import pytest
from fastapi.testclient import TestClient

from project.main import app
from project.core.chat_assistant_engine import ChatAssistantEngine, chat_assistant_engine

client = TestClient(app)


def test_chat_engine_default_context():
    engine = ChatAssistantEngine()
    ctx = engine.build_user_context(None)
    assert ctx["day_master"]["stem"] == "丁"
    assert ctx["day_master"]["element"] == "Fire"
    assert "Wood" in ctx["favorable_elements"]
    assert "Metal" in ctx["unfavorable_elements"]
    assert ctx["four_pillars"]["year"] == "乙丑"


def test_chat_engine_custom_birth_context():
    engine = ChatAssistantEngine()
    profile = {
        "birth_datetime": "1990-05-15 14:30:00",
        "longitude": 100.493,
        "utc_offset_hours": 7.0,
        "gender": "male"
    }
    ctx = engine.build_user_context(profile)
    assert "day_master" in ctx
    assert "four_pillars" in ctx
    assert "five_elements_percent" in ctx


def test_chat_engine_rag_citations():
    engine = ChatAssistantEngine()
    ctx = engine.build_user_context(None)
    citations = engine.retrieve_rag_citations("การงานและการเงิน", ctx, top_k=2)
    assert len(citations) >= 1
    assert "id" in citations[0]
    assert "source" in citations[0]
    assert "snippet" in citations[0]
    assert citations[0]["score"] > 0


def test_chat_engine_dynamic_pills():
    engine = ChatAssistantEngine()
    ctx = engine.build_user_context(None)
    pills = engine.generate_dynamic_pills(ctx)
    assert len(pills) == 5
    categories = {p["category"] for p in pills}
    assert "career_wealth" in categories
    assert "romance_peach" in categories
    assert "feng_shui" in categories
    assert "dayun_timing" in categories
    assert "elements_habits" in categories


def test_chat_engine_consultation_sync():
    engine = ChatAssistantEngine()
    resp = engine.generate_consultation_sync(
        query="ในปี 2026 ควรเปิดร้านอาหารหรือไม่?",
        history=[{"role": "user", "content": "สวัสดีครับ"}],
        profile=None
    )
    assert resp["status"] == "success"
    assert "คำชี้แนะจากซินแส AI" in resp["content"]
    assert len(resp["citations"]) >= 1
    assert len(resp["follow_up_chips"]) == 5
    assert resp["context_summary"]["current_year"] == 2026


def test_chat_engine_consultation_stream():
    import asyncio
    engine = ChatAssistantEngine()
    events = []

    async def _collect():
        async for chunk in engine.generate_consultation_stream("ทิศมงคลโต๊ะทำงาน"):
            events.append(chunk)

    asyncio.run(_collect())

    assert len(events) >= 3
    event_str = "".join(events)
    assert "event: citations" in event_str
    assert "event: pills" in event_str
    assert "event: delta" in event_str
    assert "event: done" in event_str


def test_api_chat_consult_success():
    payload = {
        "query": "แนะนำการเสริมดวงธาตุไฟ",
        "history": [],
        "profile": {
            "day_master": {"stem": "丁", "element": "Fire", "strength": "Weak"},
            "favorable_elements": ["Wood", "Water"],
            "unfavorable_elements": ["Metal", "Earth"]
        }
    }
    response = client.post("/api/v2/chat/consult", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "citations" in data
    assert "follow_up_chips" in data
    assert len(data["follow_up_chips"]) == 5


def test_api_chat_consult_empty_query():
    payload = {"query": "   ", "history": []}
    response = client.post("/api/v2/chat/consult", json=payload)
    assert response.status_code == 400


def test_api_chat_stream_success():
    payload = {
        "query": "จังหวะชีวิตปี 2026",
        "history": []
    }
    response = client.post("/api/v2/chat/stream", json=payload)
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")
    content = response.text
    assert "event: citations" in content
    assert "event: delta" in content
    assert "event: done" in content


def test_api_chat_prompt_pills():
    response = client.post("/api/v2/chat/prompt-pills", json={})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["pills"]) == 5


def test_api_chat_anonymized_feedback():
    payload = {
        "query": "ทิศมงคล",
        "response": "คำตอบซินแส",
        "rating": 5,
        "tags": ["excellent"],
        "feedback_text": "คำตอบแม่นยำและละเอียดมาก"
    }
    response = client.post("/api/v2/chat/anonymized-feedback", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
