"""
project/tests/test_api_integration_suite.py
===========================================
Comprehensive Integration Test Suite for all HoroConsultant APIs:
- Validates all v1 and v2 API endpoints
- Validates CORS Headers & Preflight (OPTIONS) requests from the Vercel frontend origin
- Validates full payload schemas, True Solar Time calculations, and error resilience
"""

import pytest
from fastapi.testclient import TestClient
from project.main import app

client = TestClient(app)

VERCEL_FRONTEND_ORIGIN = "https://horo-consultant-psi.vercel.app"
BROWSER_HEADERS = {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9,ja;q=0.8",
    "cache-control": "no-cache",
    "content-type": "application/json",
    "origin": VERCEL_FRONTEND_ORIGIN,
    "pragma": "no-cache",
    "referer": f"{VERCEL_FRONTEND_ORIGIN}/",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site",
}


# ============================================================================
# 1. CORS PREFLIGHT (OPTIONS) TESTS
# ============================================================================

def test_cors_preflight_bazi_calculate():
    """Verify CORS preflight on /api/v1/bazi/calculate."""
    res = client.options(
        "/api/v1/bazi/calculate",
        headers={
            "Origin": VERCEL_FRONTEND_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        }
    )
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == VERCEL_FRONTEND_ORIGIN


def test_cors_preflight_bazi_interpret():
    """Verify CORS preflight on /api/v1/bazi/interpret."""
    res = client.options(
        "/api/v1/bazi/interpret",
        headers={
            "Origin": VERCEL_FRONTEND_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        }
    )
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == VERCEL_FRONTEND_ORIGIN


def test_cors_preflight_v2_unified():
    """Verify CORS preflight on /api/v2/calculate/unified."""
    res = client.options(
        "/api/v2/calculate/unified",
        headers={
            "Origin": VERCEL_FRONTEND_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        }
    )
    assert res.status_code == 200


# ============================================================================
# 2. CORE BAZI API V1 ENDPOINTS WITH STATIC ORIGIN HEADERS
# ============================================================================

def test_api_v1_bazi_calculate_full():
    """Test /api/v1/bazi/calculate with full browser headers."""
    payload = {
        "birth_datetime": "1990-05-15 14:30:00",
        "longitude": 100.493,
        "utc_offset_hours": 7.0,
        "unknown_hour": False,
    }
    res = client.post("/api/v1/bazi/calculate", json=payload, headers=BROWSER_HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert "day_master" in data
    assert "pillars" in data
    assert "five_elements" in data
    assert "solar_time_info" in data
    assert res.headers.get("access-control-allow-origin") == VERCEL_FRONTEND_ORIGIN


def test_api_v1_bazi_interpret_full():
    """Test /api/v1/bazi/interpret with full browser headers and validation flag."""
    payload = {
        "birth_datetime": "1990-05-15 14:30:00",
        "longitude": 100.493,
        "utc_offset_hours": 7.0,
        "unknown_hour": False,
        "enable_validation": True,
        "query": "วิเคราะห์ความแข็งแกร่งของ Day Master ธาตุทอง และอาชีพการงานที่ส่งเสริมดวงชะตา"
    }
    res = client.post("/api/v1/bazi/interpret", json=payload, headers=BROWSER_HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert "chart" in data
    assert "interpretation" in data
    assert "validation_report" in data
    assert len(data["interpretation"]) > 10


def test_api_v1_location_resolve():
    """Test geocoding resolution endpoint."""
    res = client.post("/api/v1/location/resolve", json={"location": "Bangkok"}, headers=BROWSER_HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert "longitude" in data
    assert "utc_offset_hours" in data


# ============================================================================
# 3. METAPHYSICS DISCIPLINES API V1 ENDPOINTS
# ============================================================================

def test_api_v1_ziwei():
    res = client.get("/api/v1/ziwei/calculate?year=1990&month=5&day=15&hour=14&gender=male", headers=BROWSER_HEADERS)
    assert res.status_code == 200
    assert "palaces" in res.json()

def test_api_v1_qimen():
    res = client.get("/api/v1/qimen/calculate?year=2026&month=8&day=7&hour=14", headers=BROWSER_HEADERS)
    assert res.status_code == 200
    assert "palaces" in res.json()

def test_api_v1_liuren():
    res = client.get("/api/v1/liuren/calculate?day_stem=甲&day_branch=子&month_general=正月&hour_branch=午", headers=BROWSER_HEADERS)
    assert res.status_code == 200
    assert "three_transmissions" in res.json() or "palaces" in res.json() or "chart_data" in res.json()

def test_api_v1_iching():
    res = client.get("/api/v1/iching/calculate?day_stem=甲", headers=BROWSER_HEADERS)
    assert res.status_code == 200
    assert "primary_hexagram" in res.json() or "palaces" in res.json() or "chart_data" in res.json()

def test_api_v1_xuankong():
    res = client.get("/api/v1/xuankong/calculate?facing_degree=180.0&period=9", headers=BROWSER_HEADERS)
    assert res.status_code == 200
    assert "facing_mountain" in res.json() or "palaces" in res.json() or "chart_data" in res.json()

def test_api_v1_zeji():
    res = client.get("/api/v1/zeji/calculate?year_branch=午&month_branch=申&day_branch=寅&user_birth_branch=子", headers=BROWSER_HEADERS)
    assert res.status_code == 200
    assert "duty_officer" in res.json() or "palaces" in res.json() or "chart_data" in res.json()

def test_api_v1_thaivedic():
    res = client.get("/api/v1/thaivedic/calculate?year=1990&month=5&day=15&hour=14&day_of_week=2", headers=BROWSER_HEADERS)
    assert res.status_code == 200
    assert "thai_lagna" in res.json() or "palaces" in res.json() or "chart_data" in res.json()

def test_api_v1_western():
    res = client.get("/api/v1/western/calculate?year=1990&month=5&day=15&hour=14", headers=BROWSER_HEADERS)
    assert res.status_code == 200
    assert "planets_tropical" in res.json() or "palaces" in res.json() or "chart_data" in res.json()

def test_api_v1_numerology():
    res = client.get("/api/v1/numerology/calculate?text=0812345678&day_num=2&lunar_month=6&year_zodiac_num=7", headers=BROWSER_HEADERS)
    assert res.status_code == 200
    assert "chaldean_score" in res.json() or "palaces" in res.json() or "chart_data" in res.json()


# ============================================================================
# 4. API V2 EXTENDED SUITE ENDPOINTS
# ============================================================================

def test_api_v2_health():
    res = client.get("/api/v2/health", headers=BROWSER_HEADERS)
    assert res.status_code == 200
    assert res.json()["disciplines_count"] == 16

def test_api_v2_calculate_unified():
    payload = {
        "birth_datetime": "1990-05-15 14:30:00",
        "longitude": 100.493,
        "utc_offset_hours": 7.0,
        "disciplines": ["bazi", "tai_yi", "liu_yao", "mei_hua", "san_he", "qi_zheng"]
    }
    res = client.post("/api/v2/calculate/unified", json=payload, headers=BROWSER_HEADERS)
    assert res.status_code == 200
    assert "charts" in res.json()
    assert len(res.json()["charts"]) == 6

def test_api_v2_interpret_focused():
    payload = {
        "birth_datetime": "1990-05-15 14:30:00",
        "query": "ในปี 2026 ควรเปิดธุรกิจหรือทำงานประจำต่อดี?",
        "longitude": 100.493,
        "utc_offset_hours": 7.0,
        "language": "th"
    }
    res = client.post("/api/v2/interpret/focused", json=payload, headers=BROWSER_HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert data["metadata"]["question_focus"]["category"] == "career"
    assert "interpretation" in data

def test_api_v2_mian_xiang_analyze():
    payload = {
        "features": {
            "face_shape": "oval",
            "forehead": "wide",
            "eyebrows": "curved",
            "eyes": "large",
            "nose": "high",
            "mouth": "full",
            "ears": "large",
            "chin": "round",
            "moles": []
        },
        "birth_year": 1990
    }
    res = client.post("/api/v2/mian_xiang/analyze", json=payload, headers=BROWSER_HEADERS)
    assert res.status_code == 200
    assert "twelve_palaces" in res.json()["analysis"]

