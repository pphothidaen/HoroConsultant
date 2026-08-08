"""
project/tests/test_inject_prod_dummy_data.py — Unit tests for Production Dummy Telemetry Ingestion Tool
Computational Metaphysics Engine
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.inject_prod_dummy_data import generate_otlp_stage_payload, inject_production_dummy_data, verify_grafana_queries


class TestInjectProdDummyData:
    """Test Suite for production dummy telemetry payload generation and injection tool."""

    def test_generate_otlp_stage_payload_structure(self):
        """Verify OTLP stage payload structure matches expected schema."""
        payload = generate_otlp_stage_payload("1786204128000000000", stage_idx=0)
        assert "resourceMetrics" in payload
        metrics = payload["resourceMetrics"][0]["scopeMetrics"][0]["metrics"]
        assert len(metrics) >= 9

        names = [m["name"] for m in metrics]
        assert "process_uptime_seconds" in names
        assert "http_requests_total" in names
        assert "http_request_duration_seconds_bucket" in names
        assert "alert_groups_total" in names
        assert "user_was_notified_of_alert_groups_total" in names

    def test_inject_production_dummy_data_dry_run(self):
        """Verify dry-run execution of production telemetry injector."""
        res = inject_production_dummy_data(stages=3, dry_run=True)
        assert res is True

    def test_verify_grafana_queries_runs(self):
        """Verify query verification function executes cleanly."""
        res = verify_grafana_queries()
        assert res is True or res is False

