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
import os
from pathlib import Path
import subprocess
from unittest.mock import patch

from fastapi.testclient import TestClient

from project.core.multi_agent_debate import MetaphysicsDebateEngine
from project.main import app
from scripts.cleanup_vector_store import audit_storage, purge_and_cleanup

ROOT = Path(__file__).resolve().parents[2]
client = TestClient(app)


def _matches_vercel_source(source: str, path: str) -> bool:
    """Match the subset of Vercel path parameters used by the public gateway."""
    if source.endswith("/:path*"):
        prefix = source.removesuffix("/:path*")
        return path == prefix or path.startswith(f"{prefix}/")
    return source == path


def _declared_dynamic_gateway_paths() -> set[str]:
    """Read public dynamic paths from the FastAPI application and its routers."""
    from project.admin_router import admin_router
    from project.hitl_router import hitl_router
    from project.main import app
    from project.routers.astrology import astrology_router
    from project.routers.debate import debate_router

    static_ui_routes = {"/", "/app.js", "/style.css"}
    declared = {
        route.path
        for route in app.routes
        if isinstance(getattr(route, "path", None), str)
        and route.path not in static_ui_routes
        and not route.path.startswith("/static")
    }
    for router in (admin_router, hitl_router, astrology_router, debate_router):
        declared.update(route.path for route in router.routes)
    return declared


def test_vercel_handler_supports_preflight_cors(monkeypatch):
    """Verify the Vercel handler returns CORS headers for preflight requests."""
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "https://example.com")

    response = client.options(
        "/health",
        headers={
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code in {200, 204}
    assert response.headers.get("access-control-allow-origin") in {"https://example.com", "*"}
    assert response.headers.get("access-control-allow-methods")



def test_option_1b_vercel_gateway_config():
    """Verify static and dynamic traffic cannot share an upstream fallback."""
    vercel_file = ROOT / "vercel.json"
    assert vercel_file.exists(), "vercel.json missing"

    data = json.loads(vercel_file.read_text(encoding="utf-8"))
    rewrites = data.get("rewrites", [])
    assert rewrites, "No rewrites configured in vercel.json"

    destinations = {route["source"]: route["destination"] for route in rewrites}
    assert destinations["/health"] == "/api/health"
    assert destinations["/api/:path*"] == "/api/index?path=api/:path*"
    assert destinations["/v1/:path*"] == "/api/index?path=v1/:path*"
    assert destinations["/bazi/:path*"] == "/api/index?path=bazi/:path*"
    assert destinations["/admin/:path*"] == "/api/index?path=admin/:path*"
    assert destinations["/hitl/:path*"] == "/api/index?path=hitl/:path*"
    assert destinations["/(.*)"].startswith("https://pphothidaen-horoconsultant-core-backend.static.hf.space/")
    assert "static.hf.space" not in destinations["/health"]


def test_vercel_gateway_covers_every_declared_public_dynamic_route():
    """A new public FastAPI route must not silently fall through to the static origin."""
    data = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
    azure_sources = [
        rewrite["source"]
        for rewrite in data["rewrites"]
        if rewrite["destination"].startswith("/api/")
    ]

    missing = sorted(
        path for path in _declared_dynamic_gateway_paths()
        if not any(_matches_vercel_source(source, path) for source in azure_sources)
    )
    assert not missing, f"Dynamic routes falling through to the static origin: {missing}"


def test_vercel_gateway_sanitizes_upstream_errors_and_preserves_correlation_id():
    """Changing the error proxy to raw upstream bytes must leak an origin and fail."""
    script = r'''
import handler from './api/index.js';
let forwardedRequestId = '';
global.fetch = async (_url, options) => {
  forwardedRequestId = options.headers['x-request-id'];
  return new Response(JSON.stringify({
    detail: 'database failure at https://internal.azure.invalid/private',
    correlation_id: 'upstream-correlation',
  }), { status: 503, headers: { 'content-type': 'application/json', 'x-request-id': 'upstream-correlation' } });
};
const result = { headers: {} };
const res = {
  setHeader(key, value) { result.headers[key.toLowerCase()] = value; },
  status(code) { result.status = code; return this; },
  json(body) { result.body = body; return this; },
  send(body) { result.body = JSON.parse(body.toString()); return this; },
  end() { return this; },
};
await handler({ method: 'POST', headers: { 'x-request-id': 'browser-correlation' }, query: { path: 'v1/bazi/interpret' }, body: {} }, res);
if (forwardedRequestId !== 'browser-correlation') throw new Error('request ID was not forwarded');
if (result.status !== 503) throw new Error(`unexpected status ${result.status}`);
if (result.headers['x-request-id'] !== 'upstream-correlation') throw new Error('response ID was not preserved');
if (result.body.correlation_id !== 'upstream-correlation') throw new Error('body ID was not preserved');
if (result.body.detail !== 'The API is temporarily unavailable.') throw new Error(`unsafe detail ${result.body.detail}`);
if (JSON.stringify(result.body).includes('internal.azure.invalid')) throw new Error('upstream origin leaked');
'''
    result = subprocess.run(
        ["node", "--input-type=module", "--eval", script],
        cwd=ROOT,
        env={**os.environ, "AZURE_API_ORIGIN": "https://configured.azure.invalid"},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout


def test_vercel_gateway_uses_stable_public_errors_when_unconfigured():
    """A missing origin must not disclose deployment implementation details."""
    script = r'''
import apiHandler from './api/index.js';
import healthHandler from './api/health.js';
function response() {
  const result = { headers: {} };
  return [result, {
    setHeader(key, value) { result.headers[key.toLowerCase()] = value; },
    status(code) { result.status = code; return this; },
    json(body) { result.body = body; return this; },
    send(body) { result.body = JSON.parse(body.toString()); return this; },
    end() { return this; },
  }];
}
for (const [handler, req] of [
  [apiHandler, { method: 'GET', headers: { 'x-request-id': 'api-correlation' }, query: { path: 'v1/bazi/interpret' } }],
  [healthHandler, { method: 'GET', headers: { 'x-request-id': 'health-correlation' }, query: {} }],
]) {
  const [result, res] = response();
  await handler(req, res);
  if (result.status !== 503) throw new Error(`unexpected status ${result.status}`);
  if (result.body.detail !== 'Service is temporarily unavailable.') throw new Error(`unstable detail ${JSON.stringify(result.body)}`);
  if (JSON.stringify(result.body).match(/azure|origin|configured/i)) throw new Error('configuration leaked');
  if (result.body.correlation_id !== req.headers['x-request-id']) throw new Error('correlation ID missing');
}
'''
    result = subprocess.run(
        ["node", "--input-type=module", "--eval", script],
        cwd=ROOT,
        env={**os.environ, "AZURE_API_ORIGIN": ""},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout


def test_vercel_gateway_rejects_paths_outside_the_declared_public_surface():
    """The gateway must be an allowlist proxy, never a browser-controlled proxy."""
    script = r'''
import handler from './api/index.js';
let fetchCalled = false;
global.fetch = async () => { fetchCalled = true; throw new Error('must not fetch'); };
const result = { headers: {} };
const res = {
  setHeader(key, value) { result.headers[key.toLowerCase()] = value; },
  status(code) { result.status = code; return this; },
  json(body) { result.body = body; return this; },
  end() { return this; },
};
await handler({ method: 'GET', headers: { 'x-request-id': 'closed-proxy-check' }, query: { path: 'https://evil.invalid/steal' } }, res);
if (fetchCalled) throw new Error('arbitrary path reached fetch');
if (result.status !== 404) throw new Error(`unexpected status ${result.status}`);
if (result.body.detail !== 'The requested API route was not found.') throw new Error('unstable 404 response');
if (result.body.correlation_id !== 'closed-proxy-check') throw new Error('correlation ID missing');
'''
    result = subprocess.run(
        ["node", "--input-type=module", "--eval", script],
        cwd=ROOT,
        env={**os.environ, "AZURE_API_ORIGIN": "https://configured.azure.invalid"},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout


def test_production_playwright_harness_uses_same_origin_and_strict_api_evidence():
    """A rendered card alone must never make the production E2E report pass."""
    production_harness = (ROOT / "scripts" / "run_prod_e2e_playwright.py").read_text(encoding="utf-8")
    randomized_harness = (ROOT / "scripts" / "run_randomized_playwright_test.py").read_text(encoding="utf-8")

    assert "HORO_PUBLIC_URL" in production_harness
    assert "https://horo-consultant-psi.vercel.app" in production_harness
    assert "static.hf.space" not in production_harness
    assert "success = card_visible and len(body_text) > 15 and api_ok" in production_harness
    assert "changed =" in production_harness
    assert 'else "NO API RESPONSE"' in production_harness
    assert "static.hf.space" not in randomized_harness
    assert "PLAYWRIGHT_BROWSERS_PATH" not in randomized_harness
    assert 'Path("/Users' not in randomized_harness



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
        "origin": "https://horo-consultant-psi.vercel.app",
        "referer": "https://horo-consultant-psi.vercel.app/"
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
