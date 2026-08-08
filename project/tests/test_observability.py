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

from project.main import app
from project.core.observability import observability_manager

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
