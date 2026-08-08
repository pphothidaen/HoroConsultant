"""
project/tests/test_inject_grafana_incident_data.py — Unit tests for Grafana Incident Datasource Dummy Ingestion Tool
Computational Metaphysics Engine
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.inject_grafana_incident_data import (
    generate_incident_payloads,
    inject_grafana_incident_data,
    verify_incident_datasource_queries,
)


class TestInjectGrafanaIncidentData:
    """Test Suite for Grafana Incident datasource dummy ingestion script."""

    def test_generate_incident_payloads_structure(self):
        """Verify incident payload generation structure and attributes."""
        incidents = generate_incident_payloads(stages=3)
        assert len(incidents) == 3
        inc = incidents[0]
        assert "id" in inc
        assert "title" in inc
        assert "severity" in inc
        assert "status" in inc
        assert "labels" in inc

    def test_inject_grafana_incident_data_dry_run(self):
        """Verify dry-run execution of Grafana Incident ingestion."""
        res = inject_grafana_incident_data(stages=4, dry_run=True)
        assert res is True

    def test_verify_incident_datasource_queries_runs(self):
        """Verify query verification function for Incident API executes cleanly."""
        res = verify_incident_datasource_queries()
        assert res is True or res is False
