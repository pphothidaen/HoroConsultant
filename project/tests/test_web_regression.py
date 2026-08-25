"""
project/tests/test_web_regression.py
======================================
Web UX/UI & FastAPI Server Full Regression Test Suite.

Verifies:
  - Static Web Dashboard UI routes (HTML, CSS, JS)
  - API Endpoints (/calculate, /interpret, /validate, /eot, /health)
  - True Solar Time & Five Elements calculations
  - Gemini Prediction Validator Agent integration

Usage:
  python -m pytest project/tests/test_web_regression.py -v
"""

from __future__ import annotations

import ast
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import sys
from pathlib import Path
from threading import Thread

from fastapi.testclient import TestClient
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from project.main import app

client = TestClient(app)


class _QuietStaticHandler(SimpleHTTPRequestHandler):
    """Serve the real dashboard assets without emitting test-server noise."""

    def log_message(self, format: str, *args: object) -> None:
        return


@contextmanager
def serve_static_dashboard():
    """Provide the production static assets to a real browser test."""
    handler = partial(_QuietStaticHandler, directory=str(ROOT / "project" / "static"))
    try:
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    except PermissionError as error:
        pytest.skip(f"Local dashboard server bind is restricted in this runtime: {error}")
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/index.html"
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


@contextmanager
def browser_session():
    """Start Chromium when browser dependencies are deliberately installed.

    The core regression suite is run in CI environments that install pytest but
    not Playwright or its browser binaries.  Keeping the import here makes those
    environments report deterministic skips while retaining an explicit browser
    command for the E2E job.
    """
    playwright_api = pytest.importorskip(
        "playwright.sync_api",
        reason="browser-only test; install Playwright and run `playwright install chromium`",
    )
    with playwright_api.sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(headless=True)
        except playwright_api.Error as error:
            pytest.skip(f"Chromium is unavailable for browser-only test: {error}")
        context = browser.new_context(service_workers="block")
        try:
            yield context
        finally:
            context.close()
            browser.close()


class TestWebRegressionUI:
    """Regression tests for Web UI Dashboard assets and routes."""

    def test_ui_index_html_loads(self):
        res = client.get("/")
        assert res.status_code == 200
        assert "<title>" in res.text
        assert "horoconsultant" in res.text.lower()
        assert "bazi-form" in res.text
        assert "footer-version-text" in res.text
        assert "v1.0.0" in res.text

    def test_ui_static_css_loads(self):
        res = client.get("/static/style.css")
        assert res.status_code == 200
        assert "--bg-dark" in res.text
        assert "glass-card" in res.text

    def test_ui_static_js_loads(self):
        res = client.get("/static/app.js")
        assert res.status_code == 200
        assert "calculateChart" in res.text
        assert "renderResults" in res.text
        assert "updateVersionFooter" in res.text
        assert "fetchApi('/health" in res.text
        assert "horoconsult-env-new.mangoforest-3a921b17.westus2.azurecontainerapps.io" in res.text
        assert "res.status === 503" in res.text

    def test_browser_regressions_lazy_load_playwright_for_clean_ci(self):
        """A pytest-only job must collect this file without Playwright installed."""
        source = Path(__file__).read_text(encoding="utf-8")
        syntax_tree = ast.parse(source)
        assert not any(
            isinstance(node, ast.ImportFrom) and node.module == "playwright.sync_api"
            for node in ast.walk(syntax_tree)
        )
        assert 'pytest.importorskip(\n        "playwright.sync_api"' in source

    def test_cold_start_browser_gates_a_single_mutation_after_readiness(self):
        """Removing readiness gating must expose a POST before the API is healthy."""
        health_requests = 0
        mutation_requests: list[str] = []

        with serve_static_dashboard() as dashboard_url, browser_session() as browser:
            page = browser.new_page()

            def route_health(route):
                nonlocal health_requests
                health_requests += 1
                status = 503 if health_requests <= 2 else 200
                route.fulfill(
                    status=status,
                    content_type="application/json",
                    body='{"status":"ok"}' if status == 200 else '{"detail":"starting"}',
                )

            def route_interpret(route):
                mutation_requests.append(route.request.post_data or "")
                route.fulfill(
                    status=200,
                    content_type="application/json",
                    body=(
                        '{"chart":{"pillars":{"year":{"stem":{"char":"庚","element":"Metal"},"branch":{"char":"午","element":"Fire"}},'
                        '"month":{"stem":{"char":"辛","element":"Metal"},"branch":{"char":"巳","element":"Fire"}},'
                        '"day":{"stem":{"char":"庚","element":"Metal"},"branch":{"char":"辰","element":"Earth"}},'
                        '"hour":{"stem":{"char":"癸","element":"Water"},"branch":{"char":"未","element":"Earth"}}},'
                        '"day_master":{"stem":"庚","element":"Metal"},'
                        '"five_elements":{"percentages":{"Metal":100}}},'
                        '"interpretation":"A real API interpretation for: preserve this request."}'
                    ),
                )

            def route_all(route):
                url = route.request.url
                if "/health" in url:
                    route_health(route)
                elif "/api/v1/bazi/interpret" in url:
                    route_interpret(route)
                else:
                    route.continue_()

            page.add_init_script(
                """
                window.__coldStartDelays = [];
                const realSetTimeout = window.setTimeout.bind(window);
                window.setTimeout = (callback, delay, ...args) => {
                  if ([1000, 2000, 4000, 8000].includes(delay)) {
                    window.__coldStartDelays.push(delay);
                    return realSetTimeout(callback, 20, ...args);
                  }
                  return realSetTimeout(callback, delay, ...args);
                };
                """
            )
            page.route("**/*", route_all)
            page.goto(dashboard_url, wait_until="domcontentloaded")
            page.fill("#query", "preserve this request")
            page.click("#btn-submit")
            page.wait_for_selector("#backend-status:not(.hidden)")
            page.wait_for_function("() => document.querySelector('#reading-body').textContent.includes('real API')")

            assert health_requests >= 3
            assert len(mutation_requests) == 1
            assert "preserve this request" in mutation_requests[0]
            assert page.input_value("#query") == "preserve this request"
            assert page.locator("#backend-status").get_attribute("aria-live") == "polite"
            assert page.locator("#btn-submit").is_disabled() is False
            assert page.locator("button[onclick='resolveLocation()']").is_disabled() is False
            assert "API is ready" in page.locator("#backend-status").inner_text()
            assert page.locator("#reading-body").is_visible()
            assert page.locator("#interpretation-card .accordion-card-header").get_attribute("aria-expanded") == "true"

    def test_cold_start_browser_preserves_input_and_exposes_retry_on_real_failure(self):
        """Replacing a failed API result with fabricated content must fail this browser contract."""
        mutation_requests = 0

        with serve_static_dashboard() as dashboard_url, browser_session() as browser:
            page = browser.new_page()
            page.route("**/health", lambda route: route.fulfill(status=200, body='{"status":"ok"}'))

            def route_interpret(route):
                nonlocal mutation_requests
                mutation_requests += 1
                route.fulfill(
                    status=503,
                    content_type="application/json",
                    headers={"x-request-id": "upstream-correlation"},
                    body='{"detail":"Azure is waking","correlation_id":"upstream-correlation"}',
                )

            page.route("**/api/v1/bazi/interpret", route_interpret)
            page.goto(dashboard_url, wait_until="domcontentloaded")
            page.fill("#query", "do not replace failed input")
            page.click("#btn-submit")
            page.wait_for_selector("#backend-retry:not(.hidden)")

            assert mutation_requests >= 1
            assert page.input_value("#query") == "do not replace failed input"
            assert page.locator("#interpretation-card").evaluate("node => node.classList.contains('hidden')")
            assert "Azure is waking" in page.locator("#backend-status").inner_text()
            assert "503" in page.locator("#backend-status").inner_text()
            assert page.locator("#backend-retry").is_visible()
            assert page.locator("#btn-submit").is_disabled() is False

    def test_cold_start_browser_aborts_a_hung_health_probe_at_its_deadline(self):
        """Removing AbortController makes a never-settling readiness request block forever."""
        with serve_static_dashboard() as dashboard_url, browser_session() as browser:
            page = browser.new_page()
            page.goto(dashboard_url, wait_until="domcontentloaded")

            result = page.evaluate(
                """
                async () => {
                  const originalFetch = window.fetch;
                  window.fetch = (_url, options = {}) => new Promise((resolve, reject) => {
                    options.signal?.addEventListener(
                      'abort',
                      () => reject(new DOMException('aborted', 'AbortError')),
                      { once: true },
                    );
                  });
                  try {
                    return await Promise.race([
                      wakeBackend({ deadlineMs: 75, delays: [10] }),
                      new Promise(resolve => setTimeout(() => resolve('timed-out'), 250)),
                    ]);
                  } finally {
                    window.fetch = originalFetch;
                  }
                }
                """
            )

            assert result is False
            assert page.locator("#backend-retry").is_visible()

    def test_cold_start_browser_stops_after_sixty_seconds(self):
        """Removing the 60-second bound must make the simulated browser keep probing."""
        with serve_static_dashboard() as dashboard_url, browser_session() as browser:
            page = browser.new_page()
            page.route("**/health", lambda route: route.fulfill(status=503, body='{"detail":"starting"}'))
            page.goto(dashboard_url, wait_until="domcontentloaded")
            state = page.evaluate(
                """
                async () => {
                  let coldStartClock = 0;
                  const delays = [];
                  const result = await wakeBackend({
                    now: () => coldStartClock,
                    waitFor: async (delay) => {
                      delays.push(delay);
                      coldStartClock += delay;
                    },
                  });
                  return { result, delays };
                }
                """
            )
            assert state["result"] is False

            delays = state["delays"]
            assert delays[:5] == [1000, 2000, 4000, 8000, 10000]
            assert sum(delays) == 60000
            assert max(delays) == 10000
            assert page.locator("#backend-retry").is_visible()


class TestAPIRegressionEndpoints:
    """Regression tests for FastAPI backend routes."""

    def test_health_check(self):
        res = client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert "Computational Metaphysics Engine" in data["service"]

    def test_equation_of_time(self):
        res = client.get("/api/v1/eot?date=2026-08-03")
        assert res.status_code == 200
        data = res.json()
        assert data["date"] == "2026-08-03"
        assert "eot_minutes" in data
        assert isinstance(data["eot_minutes"], float)

    def test_bazi_calculate(self):
        payload = {
            "birth_datetime": "1990-05-15 14:30:00",
            "longitude": 100.4930,
            "utc_offset_hours": 7.0,
            "unknown_hour": False,
        }
        res = client.post("/api/v1/bazi/calculate", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "pillars" in data
        assert "day_master" in data
        assert "five_elements" in data
        assert data["day_master"]["stem"] == "庚"

    def test_bazi_interpret_basic(self):
        from unittest.mock import patch
        payload = {
            "birth_datetime": "1990-05-15 14:30:00",
            "longitude": 100.4930,
            "utc_offset_hours": 7.0,
            "query": "วิเคราะห์การงาน",
            "enable_validation": False,
        }
        mock_ai = {
            "text": "ดวงชะตานี้มี Day Master เป็น 庚金",
            "model_used": "qwen2.5:7b",
            "route": "ollama_primary",
            "latency_ms": 120,
        }
        with patch("project.main.router.generate", return_value=mock_ai):
            res = client.post("/api/v1/bazi/interpret", json=payload)
            assert res.status_code == 200
            data = res.json()
            assert "chart" in data
            assert "interpretation" in data
            assert "ollama" in data["route"]


    def test_bazi_validate_endpoint(self):
        chart = {
            "day_master": {"stem": "庚", "element": "Metal", "polarity": "Yang"},
            "five_elements": {"percentages": {"Metal": 20, "Fire": 30}},
        }
        payload = {
            "bazi_chart": chart,
            "initial_interpretation": "เจ้าชะตามี Day Master เป็น庚金",
            "query": "ตรวจสอบตรรกะธาตุ",
        }
        res = client.post("/api/v1/bazi/validate", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "validation_status" in data
        assert "peer_perspective" in data

    def test_location_resolve_endpoint(self):
        from unittest.mock import MagicMock, patch
        payload = {"location": "บางกะปิ, กรุงเทพ"}
        
        mock_location = MagicMock()
        mock_location.latitude = 13.7667
        mock_location.longitude = 100.6500
        mock_location.address = "Bang Kapi, Bangkok, Thailand"

        with patch("geopy.geocoders.Nominatim.geocode", return_value=mock_location):
            with patch("timezonefinder.TimezoneFinder.timezone_at", return_value="Asia/Bangkok"):
                res = client.post("/api/v1/location/resolve", json=payload)
                assert res.status_code == 200
                data = res.json()
                assert "latitude" in data
                assert "longitude" in data
                assert "timezone" in data
                assert "utc_offset_hours" in data
                assert data["timezone"] == "Asia/Bangkok"

    def test_openapi_docs_endpoints(self):
        """Regression tests for OpenAPI Interactive Documentation routes (/docs, /redoc, /openapi.json)."""
        res_docs = client.get("/docs")
        assert res_docs.status_code == 200
        res_redoc = client.get("/redoc")
        assert res_redoc.status_code == 200
        res_schema = client.get("/openapi.json")
        assert res_schema.status_code == 200
        data = res_schema.json()
        assert "paths" in data
        assert "info" in data
