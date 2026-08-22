"""
project/tests/test_architecture_modules.py
==========================================
Unit & Integration Tests for the 10 Architectural Modules implemented from /grill-me.
"""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from project.core.cache_manager import RuntimeCacheManager
from project.core.glossary import MetaphysicsGlossary, glossary
from project.core.multi_agent_debate import MetaphysicsDebateEngine
from project.core.rate_limiter import RateLimiter
from project.main import app
from project.mlops.notifications.telegram_controller import TelegramBotController, telegram_controller


# ---------------------------------------------------------------------------
# 1. Glossary & Multi-Lingual Alignment Tests (Decision 9)
# ---------------------------------------------------------------------------

def test_glossary_language_detection():
    assert glossary.detect_language("วิเคราะห์ดวงชะตา วันนี้") == "th"
    assert glossary.detect_language("庚金生於申月") == "zh"
    assert glossary.detect_language("Four Pillars of Destiny analysis") == "en"


def test_glossary_stem_and_branch_formatting():
    stem_info = glossary.get_stem_info("Geng")
    assert stem_info is not None
    assert stem_info["hanzi"] == "庚"
    assert "ทองหยาง" in stem_info["th"]

    branch_info = glossary.get_branch_info("Wu")
    assert branch_info is not None
    assert branch_info["hanzi"] == "午"

    pair_str = glossary.format_stem_branch_pair("Geng", "Wu", target_lang="th")
    assert "庚午" in pair_str
    assert "Gēng Wǔ" in pair_str


# ---------------------------------------------------------------------------
# 2. 2-Tier Caching & Auto-Eviction Tests (Decision 7)
# ---------------------------------------------------------------------------

def test_2tier_cache_lifecycle_and_eviction():
    cache = RuntimeCacheManager(ttl_seconds=3600, memory_capacity=5)
    cache.clear()

    key_input = {"birth": "1990-05-15", "type": "bazi"}
    data = {"day_master": "Geng Metal", "strength": "balanced"}

    # Cache miss initially
    assert cache.get(key_input) is None

    # Set into 2-tier cache
    cache.set(key_input, data, model_version="v1.0")

    # Tier 1 RAM Cache hit
    hit1 = cache.get(key_input)
    assert hit1 == data
    stats = cache.get_stats()
    assert stats["hits"] >= 1
    assert stats["ram_items"] >= 1

    # Invalidation on new model version release
    evicted = cache.invalidate_on_model_update(new_model_version="v2.0")
    assert evicted == 1
    assert cache.get(key_input) is None


# ---------------------------------------------------------------------------
# 3. Multi-Tier Adaptive Rate Limiter & Burst Guard Tests (Decision 8)
# ---------------------------------------------------------------------------

def test_rate_limiter_anonymous_vs_admin_and_burst():
    limiter = RateLimiter(anonymous_rpm=2, admin_rpm=10, burst_rps=3)
    ip_anon = "192.168.1.100"
    ip_admin = "192.168.1.200"

    # Micro-burst test (Max 3 RPS)
    ok1, r1 = limiter.check_rate_limit(ip_anon, "/api/v1/bazi", role="anonymous")
    ok2, r2 = limiter.check_rate_limit(ip_anon, "/api/v1/bazi", role="anonymous")
    ok3, r3 = limiter.check_rate_limit(ip_anon, "/api/v1/bazi", role="anonymous")
    ok4, r4 = limiter.check_rate_limit(ip_anon, "/api/v1/bazi", role="anonymous")

    assert ok1 is True
    assert ok2 is True
    # 4th rapid request triggers burst limit
    assert ok4 is False
    assert r4 == "micro_burst_exceeded"

    # Admin tier check
    ok_admin, r_admin = limiter.check_rate_limit(ip_admin, "/admin", role="admin")
    assert ok_admin is True
    stats = limiter.get_stats()
    assert stats["recent_violations_count"] >= 1


# ---------------------------------------------------------------------------
# 4. Multi-Discipline Consensus Matrix & Five Elements Anchor (Decision 5)
# ---------------------------------------------------------------------------

def test_metaphysics_consensus_matrix_debate():
    engine = MetaphysicsDebateEngine()
    result = engine.run_peer_debate({
        "birth_datetime": "1990-05-15 14:30:00",
        "query": "วิเคราะห์ความสอดคล้องข้ามศาสตร์"
    })

    assert result["status"] == "DEBATE_COMPLETED"
    assert "consensus_matrix" in result
    cm = result["consensus_matrix"]
    assert cm["consensus_score"] > 0.5
    assert len(cm["consonance_factors"]) >= 2
    assert "Five Elements" in cm["baseline_anchor"]


# ---------------------------------------------------------------------------
# 5. Two-Way Telegram Interactive Controller Tests (Decision 2)
# ---------------------------------------------------------------------------

def test_telegram_controller_commands(monkeypatch):
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123456")
    controller = TelegramBotController()

    resp_start = controller.handle_command("/start", "123456")
    assert "HoroConsultant Operations Controller" in resp_start

    resp_status = controller.handle_command("/status", "123456")
    assert "ONLINE (Healthy)" in resp_status

    resp_cache = controller.handle_command("/cache", "123456")
    assert "2-Tier Cache Performance" in resp_cache

    resp_keys = controller.handle_command("/switch_key", "123456")
    assert "Google AI Studio Key Pool" in resp_keys


def test_telegram_webhook_endpoint(monkeypatch):
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345678")
    client = TestClient(app)
    payload = {
        "update_id": 99999,
        "message": {
            "message_id": 1,
            "text": "/status",
            "chat": {"id": 12345678, "type": "private"}
        }
    }
    res = client.post("/api/v1/telegram/webhook", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "processed"
    assert "ONLINE (Healthy)" in data["response"]
