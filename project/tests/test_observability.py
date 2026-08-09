"""
project/tests/test_observability.py — Test Suite for Grafana Cloud Observability & Metrics
Computational Metaphysics Engine
"""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from project.core.observability import observability_manager
from project.main import app

client = TestClient(app)


class TestObservabilityMetrics:
    """Test Grafana Observability, Prometheus Metrics, and Health Endpoints."""

    def test_metrics_endpoint_loads(self):
        """Verify GET /metrics returns 200 with standard Prometheus text format."""
        res = client.get("/metrics")
        assert res.status_code == 200
        assert "process_uptime_seconds" in res.text or "http_requests_total" in res.text or "HELP" in res.text

    def test_api_health_alias(self):
        """Verify GET /api/health alias for Grafana Synthetic Monitoring pinging."""
        res = client.get("/api/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert "uptime_seconds" in data
        assert data["service"] == "Computational Metaphysics Engine"

    def test_response_time_header_present(self):
        """Verify X-Response-Time header is injected by observability middleware."""
        res = client.get("/health")
        assert res.status_code == 200
        assert "x-response-time" in res.headers

    def test_observability_manager_record_metrics(self):
        """Verify recording RAG search and LLM inference metrics."""
        observability_manager.record_rag_search(duration=0.042, hits=15)
        observability_manager.record_llm_inference(provider="gemini", status="success", duration=0.850)

        metrics_text = observability_manager.generate_metrics_text()
        assert "rag_search" in metrics_text
        assert "llm_inference" in metrics_text

    def test_seed_dummy_metrics_endpoint(self):
        """Verify POST/GET /metrics/seed-dummy seeds dummy metrics and returns 200."""
        res_post = client.post("/metrics/seed-dummy")
        assert res_post.status_code == 200
        assert res_post.json()["status"] == "success"

        res_get = client.get("/metrics/seed-dummy")
        assert res_get.status_code == 200
        assert res_get.json()["status"] == "success"

    def test_metrics_endpoint_with_dummy_data(self):
        """Verify /metrics exposes seeded dummy metrics so Grafana can display them."""
        observability_manager.seed_dummy_metrics()

        res = client.get("/metrics")
        assert res.status_code == 200
        body = res.text

        assert "http_requests_total" in body
        assert "endpoint=\"/dummy\"" in body
        assert "rag_search_total" in body
        assert "llm_inference_total" in body
        assert "provider=\"dummy\"" in body

    def test_generate_metrics_text_fallback_includes_latency_metrics(self, monkeypatch):
        """Verify fallback metrics exposition contains duration count and sum metrics when prometheus_client is unavailable."""
        from project.core import observability

        monkeypatch.setattr(observability, "PROMETHEUS_CLIENT_AVAILABLE", False)
        manager = observability.ObservabilityManager()
        manager.record_request(method="GET", endpoint="/dummy", status_code=200, duration=0.123)

        metrics_text = manager.generate_metrics_text()
        assert "http_request_duration_seconds_count" in metrics_text
        assert "http_request_duration_seconds_sum" in metrics_text
