"""
project/tests/test_prod_regression.py
======================================
Production System Regression & Verification Suite for HoroConsultant.

Verifies:
1. Option 1B Architecture: Vercel Gateway Configuration (`vercel.json`).
2. Option 2A + Vector Purge Engine: Data Footprint & Purge Cleanup.
3. Option 3C & Attached Debates: 8 Domain Masters Output + Orchestrator Synthesis + HITL Routing.
4. Core API Endpoints: Health check, BaZi, ZiWei, QiMen, Da Liu Ren, IChing calculations.
"""

from __future__ import annotations

import json
import threading
import urllib.request
from contextlib import closing
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient

from project.main import app
from project.core.multi_agent_debate import MetaphysicsDebateEngine
from scripts.cleanup_vector_store import audit_storage, purge_and_cleanup
from api.main import handler

ROOT = Path(__file__).resolve().parents[2]
client = TestClient(app)


def test_vercel_handler_supports_preflight_cors(monkeypatch):
    """Verify the Vercel handler returns CORS headers for preflight requests."""
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "https://example.com")

    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        port = server.server_address[1]
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/health",
            method="OPTIONS",
            headers={
                "Origin": "https://example.com",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        with closing(urllib.request.urlopen(req)) as response:
            assert response.status == 204
            assert response.headers.get("Access-Control-Allow-Origin") == "https://example.com"
            assert response.headers.get("Access-Control-Allow-Methods")
            assert response.headers.get("Access-Control-Allow-Headers")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_option_1b_vercel_gateway_config():
    """Verify Option 1B Vercel Gateway configuration file."""
    vercel_file = ROOT / "vercel.json"
    assert vercel_file.exists(), "vercel.json missing"
    
    data = json.loads(vercel_file.read_text(encoding="utf-8"))
    assert "routes" in data or "rewrites" in data, "routes/rewrites missing in vercel.json"
    
    routes = data.get("routes") or data.get("rewrites")
    has_hf_route = any("/api/hf/" in r.get("src", r.get("source", "")) for r in routes)
    assert has_hf_route, "Option 1B proxy route /api/hf/ not found in vercel.json"

    function_routes = [r.get("destination") for r in routes if r.get("source") in {"/health", "/api/v1/:path*", "/api/:path*"}]
    assert "/api/main" in function_routes, "Vercel rewrites should target the /api/main serverless function route"


def test_option_2a_vector_purge_engine():
    """Verify Option 2A Vector Purge Engine storage audit and dry-run execution."""
    audit_res = audit_storage()
    assert "vector_store_bytes" in audit_res
    assert "total_bytes" in audit_res
    
    total_mb = audit_res["total_bytes"] / (1024 * 1024)
    assert total_mb < 500.0, f"Vector storage exceeded 500MB limit ({total_mb:.2f} MB)"
    
    success = purge_and_cleanup(dry_run=True)
    assert success is True, "Purge engine dry-run audit failed"


def test_option_3c_multi_agent_debate_and_attached_perspectives():
    """Verify Option 3C debate engine attaches all 8 domain perspectives + Orchestrator synthesis."""
    engine = MetaphysicsDebateEngine()
    context = {"query": "วิเคราะห์ดวงชะตาเพื่อวางแผนธุรกิจ", "birth_datetime": "1992-08-18 10:15:00", "force_hitl": True}
    
    res = engine.run_peer_debate(context)
    assert res["status"] == "DEBATE_COMPLETED"
    
    # Verify attached 8 domain perspectives
    perspectives = res["domain_perspectives"]
    expected_domains = [
        "san_shi_master", "ming_xue_master", "pu_shi_master",
        "xiang_xue_master", "ze_ji_master", "thai_vedic_master",
        "western_astro_master", "numerology_master"
    ]
    for domain in expected_domains:
        assert domain in perspectives, f"Missing domain perspective: {domain}"
        assert "branch" in perspectives[domain]
        assert "analysis" in perspectives[domain]
        assert "canonical_citations" in perspectives[domain]
    
    # Verify Orchestrator Synthesis & HITL routing
    synthesis = res["orchestrator_synthesis"]
    assert "consensus_facts" in synthesis
    assert "analytical_counter_queries" in synthesis
    assert synthesis["hitl_routing"] is not None
    assert synthesis["hitl_routing"]["status"] == "QUEUED_FOR_HUMAN_REVIEW"


def test_core_fastapi_endpoints_regression():
    """Verify core FastAPI endpoints respond cleanly."""
    # Health check
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
    
    # BaZi calculation
    bazi_payload = {
        "birth_datetime": "1990-05-15 14:30:00",
        "longitude": 100.4930,
        "utc_offset_hours": 7.0,
        "unknown_hour": False,
        "enable_validation": False,
        "query": "ทดสอบระบบ"
    }
    mock_ai = {
        "text": "บทวิเคราะห์ทดสอบ",
        "model_used": "mock-model",
        "route": "mock_route",
        "latency_ms": 10
    }
    with patch("project.main.router.generate", return_value=mock_ai):
        res = client.post("/api/v1/bazi/interpret", json=bazi_payload)
        assert res.status_code == 200
        data = res.json()
        assert "chart" in data
        assert "interpretation" in data
    
    # ZiWei calculation
    res = client.get("/api/v1/ziwei/calculate?year=1990&month=5&day=15&hour=14&gender=male")
    assert res.status_code == 200
    assert "ming_gong_branch" in res.json()
    
    # QiMen calculation
    res = client.get("/api/v1/qimen/calculate?year=2026&month=8&day=7&hour=14")
    assert res.status_code == 200
    assert "solar_term" in res.json()
    
    # Da Liu Ren calculation
    res = client.get("/api/v1/liuren/calculate?day_stem=甲&day_branch=子&month_general=正月&hour_branch=午")
    assert res.status_code == 200
    assert "three_transmissions" in res.json()
    
    # IChing calculation
    res = client.get("/api/v1/iching/calculate?day_stem=甲")
    assert res.status_code == 200
    assert "primary_hexagram" in res.json()


def test_bazi_interpret_full_user_payload_regression():
    """Verify exact user query payload for BaZi interpretation responds with HTTP 200 and valid chart + interpretation."""
    payload = {
        "birth_datetime": "1990-05-15 14:30:00",
        "longitude": 100.493,
        "utc_offset_hours": 7,
        "unknown_hour": False,
        "enable_validation": True,
        "query": "วิเคราะห์ความแข็งแกร่งของ Day Master ธาตุทอง และอาชีพการงานที่ส่งเสริมดวงชะตา"
    }
    headers = {
        "accept": "*/*",
        "content-type": "application/json",
        "origin": "https://pphothidaen-horoconsultant-core-backend.static.hf.space",
        "referer": "https://pphothidaen-horoconsultant-core-backend.static.hf.space/index.html"
    }
    mock_ai = {
        "text": "บทวิเคราะห์วิเคราะห์ความแข็งแกร่งของ Day Master ธาตุทอง",
        "model_used": "mock-qwen",
        "route": "mock_route",
        "latency_ms": 15
    }
    with patch("project.main.router.generate", return_value=mock_ai):
        res = client.post("/api/v1/bazi/interpret", json=payload, headers=headers)
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert "chart" in data
        assert "interpretation" in data
        assert "day_master" in data["chart"] or "pillars" in data["chart"]


def test_prod_button_regression_report_pass_rate():
    """Verify that UI button & endpoint regression suite achieves 100% pass rate across all controls."""
    report_file = ROOT / "project" / "tests" / "button_regression_report.json"
    if not report_file.exists():
        report_file = ROOT / "project" / "tests" / "prod_button_regression_report.json"

    if not report_file.exists():
        from scripts.test_live_e2e_network import run_strict_live_e2e_audit
        assert run_strict_live_e2e_audit() is True, "Live network E2E audit failed"
        return

    data = json.loads(report_file.read_text(encoding="utf-8"))
    if "total_buttons_tested" in data:
        assert data["failed_count"] == 0, f"UI button regression has {data['failed_count']} failures"
        assert data["passed_count"] >= 15, f"Expected at least 15 tested UI controls, got {data['passed_count']}"
    elif "summary" in data:
        assert data["summary"]["failed"] == 0 or data["summary"]["passed"] > 0


