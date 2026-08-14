"""
project/tests/test_v2_and_rate_limiter.py
=========================================
Unit tests for API v2 Router endpoints and RateLimiter token bucket behavior.
"""

import pytest
from fastapi.testclient import TestClient
from project.main import app
from project.core.rate_limiter import RateLimiter


@pytest.fixture
def client():
    return TestClient(app)


def test_v2_health(client):
    """Verify v2 health endpoint returns 16 supported disciplines."""
    res = client.get("/api/v2/health")
    assert res.status_code == 200
    data = res.json()
    assert data["api_version"] == "v2.0.0"
    assert data["disciplines_count"] == 16
    assert "tai_yi" in data["supported_disciplines"]
    assert "liu_yao" in data["supported_disciplines"]
    assert "mei_hua" in data["supported_disciplines"]
    assert "mian_xiang" in data["supported_disciplines"]


def test_v2_calculate_unified(client):
    """Verify unified multi-discipline calculation."""
    payload = {
        "birth_datetime": "1990-05-15 14:30:00",
        "longitude": 100.493,
        "utc_offset_hours": 7.0,
        "disciplines": ["bazi", "tai_yi", "liu_yao", "mei_hua"]
    }
    res = client.post("/api/v2/calculate/unified", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "bazi" in data["charts"]
    assert "tai_yi" in data["charts"]
    assert "liu_yao" in data["charts"]
    assert "mei_hua" in data["charts"]


def test_v2_mian_xiang_analyze(client):
    """Verify facial analysis endpoint."""
    payload = {
        "features": {
            "face_shape": "round",
            "forehead": "wide",
            "eyebrows": "thick",
            "eyes": "large",
            "nose": "high",
            "mouth": "full",
            "ears": "large",
            "chin": "round",
            "moles": []
        },
        "birth_year": 1990
    }
    res = client.post("/api/v2/mian_xiang/analyze", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "analysis" in data
    assert "twelve_palaces" in data["analysis"]


def test_rate_limiter_allows_under_limit():
    limiter = RateLimiter(default_rpm=60, ai_rpm=10)
    allowed, reason = limiter.check_rate_limit("1.2.3.4", "/api/v1/bazi/calculate")
    assert allowed is True
    assert reason == "ok"


def test_rate_limiter_blocks_burst():
    limiter = RateLimiter(default_rpm=2, ai_rpm=1)
    ip = "9.9.9.9"
    # First 2 requests pass
    limiter.check_rate_limit(ip, "/api/test")
    limiter.check_rate_limit(ip, "/api/test")
    # 3rd request blocked
    allowed, reason = limiter.check_rate_limit(ip, "/api/test")
    assert allowed is False
    assert reason == "rate_limit_exceeded"


def test_rate_limiter_budget_guard():
    limiter = RateLimiter(default_rpm=60, ai_rpm=10, monthly_budget_cap_usd=5.0)
    limiter.record_cost(5.50)
    allowed, reason = limiter.check_rate_limit("5.5.5.5", "/api/v1/bazi/interpret")
    assert allowed is False
    assert reason == "monthly_budget_cap_exceeded"
