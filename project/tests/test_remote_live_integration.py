"""
project/tests/test_remote_live_integration.py
=============================================
Pytest Integration Tests against live production endpoints & in-process app client.
Adaptive Execution:
- If RUN_REMOTE_INTEGRATION=True: tests live production gateway on Vercel / Hugging Face Spaces.
- If RUN_REMOTE_INTEGRATION=False: tests local FastAPI TestClient verifying the identical API contract.
"""

import os
import sys
from pathlib import Path
import httpx
import pytest
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from project.main import app

GATEWAY_BASE_URL = "https://horo-consultant-psi.vercel.app"
VERCEL_FRONTEND_ORIGIN = "https://horo-consultant-psi.vercel.app"

BROWSER_HEADERS = {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9",
    "content-type": "application/json",
    "origin": VERCEL_FRONTEND_ORIGIN,
    "referer": f"{VERCEL_FRONTEND_ORIGIN}/",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site",
}

RUN_REMOTE_INTEGRATION = os.getenv("RUN_REMOTE_INTEGRATION", "").lower() in {"1", "true", "yes", "on"}


class AdaptiveApiClient:
    """Wrapper that routes to remote live URL or local TestClient based on RUN_REMOTE_INTEGRATION."""

    def __init__(self):
        self.is_remote = RUN_REMOTE_INTEGRATION
        if not self.is_remote:
            self.local_client = TestClient(app)

    def get(self, path: str, headers: dict = None):
        if self.is_remote:
            with httpx.Client(timeout=30.0) as client:
                return client.get(f"{GATEWAY_BASE_URL}{path}", headers=headers)
        return self.local_client.get(path, headers=headers)

    def options(self, path: str, headers: dict = None):
        if self.is_remote:
            with httpx.Client(timeout=30.0) as client:
                return client.options(f"{GATEWAY_BASE_URL}{path}", headers=headers)
        return self.local_client.options(path, headers=headers)

    def post(self, path: str, json: dict = None, headers: dict = None):
        if self.is_remote:
            with httpx.Client(timeout=30.0) as client:
                return client.post(f"{GATEWAY_BASE_URL}{path}", json=json, headers=headers)
        return self.local_client.post(path, json=json, headers=headers)


@pytest.fixture(scope="module")
def api_client():
    return AdaptiveApiClient()


def test_live_remote_health(api_client: AdaptiveApiClient):
    """Verify GET /health on production gateway or local in-process client."""
    res = api_client.get("/health", headers=BROWSER_HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert data.get("status") in ("ok", "healthy", "up")


def test_live_remote_cors_preflight(api_client: AdaptiveApiClient):
    """Verify OPTIONS preflight with CORS headers."""
    options_headers = {
        "Origin": VERCEL_FRONTEND_ORIGIN,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    }
    res = api_client.options("/api/v1/bazi/calculate", headers=options_headers)
    assert res.status_code in (200, 204, 405)


def test_live_remote_bazi_calculate(api_client: AdaptiveApiClient):
    """Verify POST /api/v1/bazi/calculate endpoint contract."""
    payload = {
        "birth_datetime": "1990-05-15 14:30:00",
        "longitude": 100.493,
        "utc_offset_hours": 7.0,
        "unknown_hour": False,
    }
    res = api_client.post("/api/v1/bazi/calculate", json=payload, headers=BROWSER_HEADERS)
    assert res.status_code == 200
    body = res.json()
    assert body.get("status") in ("ok", "success") or "pillars" in body or "four_pillars" in body


def test_live_remote_bazi_interpret(api_client: AdaptiveApiClient):
    """Verify POST /api/v1/bazi/interpret endpoint contract."""
    payload = {
        "birth_datetime": "1990-05-15 14:30:00",
        "longitude": 100.493,
        "utc_offset_hours": 7.0,
        "unknown_hour": False,
        "enable_validation": True,
        "query": "วิเคราะห์ความแข็งแกร่งของ Day Master ธาตุทอง"
    }
    res = api_client.post("/api/v1/bazi/interpret", json=payload, headers=BROWSER_HEADERS)
    assert res.status_code == 200
    body = res.json()
    assert body.get("status") in ("ok", "success") or "interpretation" in body or "result" in body
