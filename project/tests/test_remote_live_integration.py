"""
project/tests/test_remote_live_integration.py
=============================================
Pytest Integration Tests against live production endpoints & Hugging Face Spaces.
"""

import os
import httpx
import pytest

GATEWAY_BASE_URL = "https://horo-consultant-psi.vercel.app"
STATIC_SPACE_ORIGIN = "https://pphothidaen-horoconsultant-core-backend.static.hf.space"

BROWSER_HEADERS = {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9",
    "content-type": "application/json",
    "origin": STATIC_SPACE_ORIGIN,
    "referer": f"{STATIC_SPACE_ORIGIN}/",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site",
}


RUN_REMOTE_INTEGRATION = os.getenv("RUN_REMOTE_INTEGRATION", "").lower() in {"1", "true", "yes", "on"}


@pytest.mark.network
@pytest.mark.skipif(not RUN_REMOTE_INTEGRATION, reason="Remote integration requires explicit RUN_REMOTE_INTEGRATION=True")
def test_live_remote_health():
    """Verify live remote GET /health on production gateway."""
    with httpx.Client(timeout=30.0) as client:
        res = client.get(f"{GATEWAY_BASE_URL}/health", headers=BROWSER_HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "service" in data


@pytest.mark.network
@pytest.mark.skipif(not RUN_REMOTE_INTEGRATION, reason="Remote integration requires explicit RUN_REMOTE_INTEGRATION=True")
def test_live_remote_cors_preflight():
    """Verify live remote OPTIONS preflight with CORS headers."""
    options_headers = {
        "Origin": STATIC_SPACE_ORIGIN,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    }
    with httpx.Client(timeout=30.0) as client:
        res = client.options(f"{GATEWAY_BASE_URL}/api/v1/bazi/calculate", headers=options_headers)
    assert res.status_code in (200, 204)
    allow_origin = res.headers.get("access-control-allow-origin")
    assert allow_origin == "*" or allow_origin == STATIC_SPACE_ORIGIN


@pytest.mark.network
@pytest.mark.skipif(not RUN_REMOTE_INTEGRATION, reason="Remote integration requires explicit RUN_REMOTE_INTEGRATION=True")
def test_live_remote_bazi_calculate():
    """Verify live remote POST /api/v1/bazi/calculate on production gateway."""
    payload = {
        "birth_datetime": "1990-05-15 14:30:00",
        "longitude": 100.493,
        "utc_offset_hours": 7.0,
        "unknown_hour": False,
    }
    with httpx.Client(timeout=30.0) as client:
        res = client.post(f"{GATEWAY_BASE_URL}/api/v1/bazi/calculate", json=payload, headers=BROWSER_HEADERS)
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


@pytest.mark.network
@pytest.mark.skipif(not RUN_REMOTE_INTEGRATION, reason="Remote integration requires explicit RUN_REMOTE_INTEGRATION=True")
def test_live_remote_bazi_interpret():
    """Verify live remote POST /api/v1/bazi/interpret on production gateway."""
    payload = {
        "birth_datetime": "1990-05-15 14:30:00",
        "longitude": 100.493,
        "utc_offset_hours": 7.0,
        "unknown_hour": False,
        "enable_validation": True,
        "query": "วิเคราะห์ความแข็งแกร่งของ Day Master ธาตุทอง"
    }
    with httpx.Client(timeout=30.0) as client:
        res = client.post(f"{GATEWAY_BASE_URL}/api/v1/bazi/interpret", json=payload, headers=BROWSER_HEADERS)
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
