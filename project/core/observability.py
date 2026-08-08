"""
project/core/observability.py — Centralized Observability & Prometheus Metrics Engine
Computational Metaphysics Engine
"""

from __future__ import annotations

import os
import time
import logging
from typing import Dict, Any, Optional

from fastapi import FastAPI, Request, Response
from fastapi.responses import PlainTextResponse

logger = logging.getLogger("observability")

# Standard Prometheus metrics storage (pure Python fallback + prometheus_client compatibility)
try:
    import prometheus_client
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
    PROMETHEUS_CLIENT_AVAILABLE = True
except ImportError:
    PROMETHEUS_CLIENT_AVAILABLE = False


class ObservabilityManager:
    """
    All-in-One Observability Manager for Metrics, Tracing, and Health Monitoring.
    Supports native Prometheus export & OpenTelemetry OTLP integration.
    """

    def __init__(self):
        self.enabled = os.getenv("PROMETHEUS_METRICS_ENABLED", "true").lower() in ("true", "1", "yes")
        self.start_time = time.time()

        # Pure Python Fallback Metrics
        self._request_counts: Dict[str, int] = {}
        self._request_latencies: Dict[str, float] = {}
        self._rag_counts = 0
        self._rag_latency_sum = 0.0
        self._llm_counts: Dict[str, int] = {}
        self._llm_latency_sum: Dict[str, float] = {}

        if PROMETHEUS_CLIENT_AVAILABLE:
            try:
                self.reg = prometheus_client.REGISTRY
                self.prom_http_requests = Counter(
                    "http_requests_total",
                    "Total count of HTTP requests",
                    ["method", "endpoint", "status_code"],
                )
                self.prom_http_duration = Histogram(
                    "http_request_duration_seconds",
                    "HTTP request processing duration in seconds",
                    ["method", "endpoint"],
                )
                self.prom_rag_searches = Counter(
                    "rag_search_total",
                    "Total RAG vector store queries",
                )
                self.prom_rag_duration = Histogram(
                    "rag_search_duration_seconds",
                    "RAG vector store retrieval duration",
                )
                self.prom_llm_requests = Counter(
                    "llm_inference_total",
                    "Total LLM inference calls",
                    ["provider", "status"],
                )
                self.prom_llm_duration = Histogram(
                    "llm_inference_duration_seconds",
                    "LLM inference duration",
                    ["provider"],
                )
            except Exception as e:
                logger.warning(f"Failed to register Prometheus metrics: {e}")

    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record an HTTP request metric."""
        if not self.enabled:
            return

        key = f"{method}:{endpoint}:{status_code}"
        self._request_counts[key] = self._request_counts.get(key, 0) + 1
        
        lat_key = f"{method}:{endpoint}"
        self._request_latencies[lat_key] = self._request_latencies.get(lat_key, 0.0) + duration

        if PROMETHEUS_CLIENT_AVAILABLE and hasattr(self, "prom_http_requests"):
            try:
                self.prom_http_requests.labels(method=method, endpoint=endpoint, status_code=str(status_code)).inc()
                self.prom_http_duration.labels(method=method, endpoint=endpoint).observe(duration)
            except Exception:
                pass

    def record_rag_search(self, duration: float, hits: int = 0):
        """Record a RAG vector retrieval metric."""
        if not self.enabled:
            return
        self._rag_counts += 1
        self._rag_latency_sum += duration

        if PROMETHEUS_CLIENT_AVAILABLE and hasattr(self, "prom_rag_searches"):
            try:
                self.prom_rag_searches.inc()
                self.prom_rag_duration.observe(duration)
            except Exception:
                pass

    def record_llm_inference(self, provider: str, status: str, duration: float):
        """Record an LLM model inference call metric."""
        if not self.enabled:
            return
        key = f"{provider}:{status}"
        self._llm_counts[key] = self._llm_counts.get(key, 0) + 1
        self._llm_latency_sum[provider] = self._llm_latency_sum.get(provider, 0.0) + duration

        if PROMETHEUS_CLIENT_AVAILABLE and hasattr(self, "prom_llm_requests"):
            try:
                self.prom_llm_requests.labels(provider=provider, status=status).inc()
                self.prom_llm_duration.labels(provider=provider).observe(duration)
            except Exception:
                pass

    def seed_dummy_metrics(self) -> None:
        """Seed the observability manager with dummy metrics for local display and test coverage."""
        if not self.enabled:
            return

        # Dummy HTTP request metrics
        self.record_request(method="GET", endpoint="/dummy", status_code=200, duration=0.123)
        self.record_request(method="POST", endpoint="/dummy", status_code=201, duration=0.250)

        # Dummy RAG and LLM metrics
        self.record_rag_search(duration=0.042, hits=5)
        self.record_llm_inference(provider="dummy", status="success", duration=0.100)
        self.record_llm_inference(provider="dummy", status="error", duration=0.200)

    def generate_metrics_text(self) -> str:
        """Generate Prometheus exposition text format."""
        if PROMETHEUS_CLIENT_AVAILABLE:
            try:
                return generate_latest(self.reg).decode("utf-8")
            except Exception:
                pass

        # Fallback exposition text format
        uptime = time.time() - self.start_time
        lines = [
            "# HELP process_uptime_seconds Total application uptime in seconds",
            "# TYPE process_uptime_seconds gauge",
            f"process_uptime_seconds {uptime:.2f}",
            "",
            "# HELP http_requests_total Total count of HTTP requests",
            "# TYPE http_requests_total counter",
        ]
        for key, count in self._request_counts.items():
            method, endpoint, status = key.split(":")
            lines.append(f'http_requests_total{{method="{method}",endpoint="{endpoint}",status_code="{status}"}} {count}')

        request_count_by_path: Dict[str, int] = {}
        for key, count in self._request_counts.items():
            method, endpoint, _ = key.split(":", 2)
            path_key = f"{method}:{endpoint}"
            request_count_by_path[path_key] = request_count_by_path.get(path_key, 0) + count

        lines.extend([
            "",
            "# HELP http_request_duration_seconds_count Total number of HTTP request duration observations",
            "# TYPE http_request_duration_seconds_count counter",
        ])
        for path_key, count in request_count_by_path.items():
            method, endpoint = path_key.split(":", 1)
            lines.append(
                f'http_request_duration_seconds_count{{method="{method}",endpoint="{endpoint}"}} {count}'
            )

        lines.extend([
            "",
            "# HELP http_request_duration_seconds_sum Total cumulative HTTP request duration",
            "# TYPE http_request_duration_seconds_sum counter",
        ])
        for path_key, duration_sum in self._request_latencies.items():
            method, endpoint = path_key.split(":", 1)
            lines.append(
                f'http_request_duration_seconds_sum{{method="{method}",endpoint="{endpoint}"}} {duration_sum:.4f}'
            )

        lines.extend([
            "",
            "# HELP rag_search_total Total RAG vector store queries",
            "# TYPE rag_search_total counter",
            f"rag_search_total {self._rag_counts}",
            "",
            "# HELP rag_search_latency_seconds_sum Total RAG vector store retrieval duration",
            "# TYPE rag_search_latency_seconds_sum counter",
            f"rag_search_latency_seconds_sum {self._rag_latency_sum:.4f}",
        ])

        for key, count in self._llm_counts.items():
            provider, status = key.split(":")
            lines.append(f'llm_inference_total{{provider="{provider}",status="{status}"}} {count}')

        return "\n".join(lines) + "\n"


# Global singleton instance
observability_manager = ObservabilityManager()


def setup_observability_middleware(app: FastAPI):
    """
    Configures HTTP timing middleware, `/metrics` endpoint, and `/api/health` ping endpoint on FastAPI.
    """

    @app.middleware("http")
    async def observability_middleware(request: Request, call_next):
        start_time = time.time()
        response: Response = await call_next(request)
        duration = time.time() - start_time

        # Sanitize endpoint path for Prometheus tags
        path = request.url.path
        if path.startswith("/static/"):
            endpoint = "/static/*"
        else:
            endpoint = path

        observability_manager.record_request(
            method=request.method,
            endpoint=endpoint,
            status_code=response.status_code,
            duration=duration,
        )

        response.headers["X-Response-Time"] = f"{duration * 1000:.2f}ms"
        return response

    @app.get("/metrics", include_in_schema=False, tags=["observability"])
    async def metrics_endpoint():
        """Expose standard Prometheus metrics format for Grafana Cloud scraping."""
        content = observability_manager.generate_metrics_text()
        content_type = CONTENT_TYPE_LATEST if PROMETHEUS_CLIENT_AVAILABLE else "text/plain; version=0.0.4; charset=utf-8"
        return PlainTextResponse(content=content, media_type=content_type)

    @app.get("/metrics/seed-dummy", include_in_schema=False, tags=["observability"])
    @app.post("/metrics/seed-dummy", include_in_schema=False, tags=["observability"])
    async def seed_dummy_metrics_endpoint():
        """Trigger dummy metrics generation for testing and Grafana demonstration."""
        observability_manager.seed_dummy_metrics()
        return {
            "status": "success",
            "message": "Dummy metrics seeded successfully into ObservabilityManager engine",
            "timestamp": time.time()
        }

    @app.get("/api/health", include_in_schema=False, tags=["system"])
    async def api_health_alias():
        """Grafana Synthetic Monitoring / Health Alias Endpoint."""
        return {
            "status": "ok",
            "uptime_seconds": round(time.time() - observability_manager.start_time, 2),
            "service": "Computational Metaphysics Engine",
        }

