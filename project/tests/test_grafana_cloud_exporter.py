"""
project/tests/test_grafana_cloud_exporter.py — Test Suite for Grafana Cloud Free Tier Exporter & Dashboard Schema
Computational Metaphysics Engine
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add repository root to python sys.path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.grafana_cloud_exporter import (
    export_dashboard_to_grafana,
    format_grafana_payload,
    load_dashboard_schema,
)
from scripts.grafana_cloud_exporter import (
    main as exporter_main,
)

DASHBOARD_FILE_PATH = ROOT / "project" / "grafana" / "horoconsultant_dashboard.json"
INCIDENT_DASHBOARD_FILE_PATH = ROOT / "project" / "grafana" / "incident_insights_dashboard.json"
PUBLIC_DASHBOARD_FILE_PATH = ROOT / "project" / "grafana" / "incident_insights_public_dashboard.json"
INVALID_TASK_REGEX = "/^task_completed / task_total$/"
CORRECT_TASK_REGEX = "/^(task_completed|task_total)$/"


class TestGrafanaDashboardSchema:
    """Test Suite for Grafana Dashboard JSON Schema Validity."""

    def test_dashboard_file_exists(self):
        """Verify project/grafana/horoconsultant_dashboard.json file exists."""
        assert DASHBOARD_FILE_PATH.exists(), f"Dashboard JSON does not exist at {DASHBOARD_FILE_PATH}"

    def test_dashboard_json_structure(self):
        """Verify dashboard file is valid JSON and has required root keys."""
        data = load_dashboard_schema(DASHBOARD_FILE_PATH)
        assert isinstance(data, dict), "Dashboard root must be a dict"
        assert "title" in data, "Dashboard JSON missing 'title'"
        assert "panels" in data, "Dashboard JSON missing 'panels'"
        assert "schemaVersion" in data, "Dashboard JSON missing 'schemaVersion'"
        assert "uid" in data, "Dashboard JSON missing 'uid'"

    def test_dashboard_title_and_metadata(self):
        """Verify title and metadata formatting."""
        data = load_dashboard_schema(DASHBOARD_FILE_PATH)
        assert isinstance(data["title"], str) and len(data["title"]) > 0
        assert "HoroConsultant" in data["title"]
        assert data["uid"] == "horoconsultant-observability"

    def test_dashboard_panels_structure(self):
        """Verify panels array structure, titles, types, and grid positions."""
        data = load_dashboard_schema(DASHBOARD_FILE_PATH)
        panels = data.get("panels", [])
        assert isinstance(panels, list)
        assert len(panels) >= 3, "Dashboard should contain at least 3 observability panels"

        for idx, panel in enumerate(panels):
            assert "id" in panel, f"Panel at index {idx} missing 'id'"
            assert "title" in panel, f"Panel at index {idx} missing 'title'"
            assert "type" in panel, f"Panel at index {idx} missing 'type'"
            assert "targets" in panel, f"Panel at index {idx} missing 'targets'"

    def test_dashboard_datasource_structure(self):
        """Verify panels have valid Prometheus datasource configuration."""
        data = load_dashboard_schema(DASHBOARD_FILE_PATH)
        panels = data.get("panels", [])

        for idx, panel in enumerate(panels):
            datasource = panel.get("datasource")
            assert datasource is not None, f"Panel '{panel.get('title')}' missing datasource"
            if isinstance(datasource, dict):
                assert datasource.get("type") == "prometheus", f"Panel '{panel.get('title')}' datasource type should be prometheus"
            elif isinstance(datasource, str):
                assert len(datasource) > 0

    def test_dashboard_targets_structure(self):
        """Verify panels' targets structure and Prometheus metric expressions."""
        data = load_dashboard_schema(DASHBOARD_FILE_PATH)
        panels = data.get("panels", [])

        metric_expressions = []
        for panel in panels:
            targets = panel.get("targets", [])
            assert isinstance(targets, list) and len(targets) > 0, f"Panel '{panel.get('title')}' has no targets"

            for target in targets:
                assert "expr" in target, f"Target in panel '{panel.get('title')}' missing 'expr'"
                assert "refId" in target, f"Target in panel '{panel.get('title')}' missing 'refId'"
                assert len(target["expr"].strip()) > 0
                metric_expressions.append(target["expr"])

        # Ensure core application metrics are queried in the dashboard
        all_exprs = " ".join(metric_expressions)
        assert "http_requests_total" in all_exprs or "process_uptime_seconds" in all_exprs
        assert "rag_search_total" in all_exprs or "llm_inference_total" in all_exprs

    def test_public_dashboard_file_structure(self):
        """Verify the public incident dashboard JSON schema is valid and uses Prometheus datasource."""
        assert PUBLIC_DASHBOARD_FILE_PATH.exists(), f"Public dashboard JSON does not exist at {PUBLIC_DASHBOARD_FILE_PATH}"
        data = load_dashboard_schema(PUBLIC_DASHBOARD_FILE_PATH)
        assert isinstance(data, dict), "Public dashboard root must be a dict"
        assert data["uid"] == "horoconsultant-incident-insights-public"
        assert "Prometheus" not in data.get("title", "") or "public" in data.get("title", "").lower()

        panels = data.get("panels", [])
        assert isinstance(panels, list) and len(panels) >= 3

        exprs = []
        for panel in panels:
            datasource = panel.get("datasource")
            assert isinstance(datasource, dict), f"Panel '{panel.get('title')}' missing datasource"
            assert datasource.get("type") == "prometheus", f"Panel '{panel.get('title')}' must use Prometheus datasource"
            assert datasource.get("uid") in ("${DS_PROMETHEUS}", "grafanacloud-prom"), (
                f"Panel '{panel.get('title')}' datasource uid must be templated or default to grafanacloud-prom"
            )
            targets = panel.get("targets", [])
            assert isinstance(targets, list) and len(targets) > 0, f"Panel '{panel.get('title')}' has no targets"
            for target in targets:
                assert "expr" in target, f"Target in panel '{panel.get('title')}' missing 'expr'"
                exprs.append(target["expr"])

        all_exprs = " ".join(exprs)
        assert "process_uptime_seconds" in all_exprs
        assert "http_requests_total" in all_exprs
        assert "http_request_duration_seconds_sum" in all_exprs
        assert "http_request_duration_seconds_count" in all_exprs
        assert "rag_search_total" in all_exprs
        assert "llm_inference_total" in all_exprs

    def test_public_dashboard_uses_prometheus_variable_uid(self):
        """Verify public incident dashboard panels use the DS_PROMETHEUS templated datasource UID."""
        data = load_dashboard_schema(PUBLIC_DASHBOARD_FILE_PATH)
        panels = data.get("panels", [])
        for panel in panels:
            datasource = panel.get("datasource")
            if isinstance(datasource, dict):
                uid = datasource.get("uid")
                assert uid == "${DS_PROMETHEUS}", f"Panel '{panel.get('title')}' should use '$'+'{{DS_PROMETHEUS}}' datasource variable, got '{uid}'"

    def test_incident_dashboard_field_filter_regex(self):
        """Verify the incident dashboard uses a correct regex for task completed/total field filtering."""
        data = load_dashboard_schema(INCIDENT_DASHBOARD_FILE_PATH)
        panels = data.get("panels", [])

        gauge_panel = next((panel for panel in panels if panel.get("id") == 63), None)
        assert gauge_panel is not None, "Incident dashboard missing panel 63"

        reduce_fields = gauge_panel.get("options", {}).get("reduceOptions", {}).get("fields")
        assert reduce_fields == CORRECT_TASK_REGEX, f"Panel 63 task field filter regex is invalid: {reduce_fields}"


class TestGrafanaCloudExporterCLI:
    """Test Suite for scripts/grafana_cloud_exporter.py Functions and CLI."""

    def test_load_dashboard_schema_success(self):
        """Verify load_dashboard_schema loads data successfully."""
        data = load_dashboard_schema(DASHBOARD_FILE_PATH)
        assert isinstance(data, dict)
        assert data["uid"] == "horoconsultant-observability"

    def test_load_dashboard_schema_file_not_found(self):
        """Verify load_dashboard_schema raises FileNotFoundError for non-existent path."""
        with pytest.raises(FileNotFoundError):
            load_dashboard_schema(ROOT / "non_existent_dashboard.json")

    def test_format_grafana_payload(self):
        """Verify Grafana API payload structure formatting."""
        mock_dashboard = {"title": "Test Dashboard", "uid": "test-uid"}
        payload = format_grafana_payload(mock_dashboard, overwrite=True, folder_uid="test-folder")

        assert payload["dashboard"]["title"] == mock_dashboard["title"]
        assert payload["dashboard"]["uid"] == mock_dashboard["uid"]
        assert payload["dashboard"]["id"] is None
        assert payload["overwrite"] is True
        assert payload["folderUid"] == "test-folder"
        assert "Exported via HoroConsultant" in payload["message"]

    def test_export_dashboard_dry_run(self):
        """Verify export_dashboard_to_grafana with dry_run=True."""
        res = export_dashboard_to_grafana(dashboard_path=str(DASHBOARD_FILE_PATH), dry_run=True)
        assert res["status"] == "dry_run"
        assert "validated" in res["message"]
        assert res["payload"]["dashboard"]["uid"] == "horoconsultant-observability"

    def test_export_dashboard_missing_credentials(self):
        """Verify export_dashboard_to_grafana handles missing env vars/credentials cleanly."""
        with patch.dict(os.environ, {}, clear=True):
            res = export_dashboard_to_grafana(
                dashboard_path=str(DASHBOARD_FILE_PATH),
                url=None,
                token=None,
                dry_run=False,
            )
            assert res["status"] == "missing_credentials"
            assert "missing" in res["message"].lower()

    def test_export_dashboard_http_success_mock(self):
        """Verify export_dashboard_to_grafana HTTP POST logic with mocked urlopen."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps({"status": "success", "slug": "horoconsultant-observability", "version": 1}).encode("utf-8")
        mock_response.__enter__.return_value = mock_response

        with patch("urllib.request.urlopen", return_value=mock_response):
            res = export_dashboard_to_grafana(
                dashboard_path=str(DASHBOARD_FILE_PATH),
                url="https://horo.grafana.net",
                token="test-api-token-123",
                dry_run=False,
            )
            assert res["status"] == "success"
            assert res["response"]["slug"] == "horoconsultant-observability"

    def test_cli_dry_run_flag(self):
        """Verify CLI invocation with --dry-run and --export-dashboard args."""
        test_args = [
            "grafana_cloud_exporter.py",
            "--dashboard-path", str(DASHBOARD_FILE_PATH),
            "--dry-run",
            "--export-dashboard",
        ]
        with patch.object(sys, "argv", test_args):
            exit_code = exporter_main()
            assert exit_code == 0

    def test_cli_execution_via_subprocess(self):
        """Verify executing scripts/grafana_cloud_exporter.py directly via python process."""
        script_path = ROOT / "scripts" / "grafana_cloud_exporter.py"
        cmd = [
            sys.executable,
            str(script_path),
            "--dashboard-path", str(DASHBOARD_FILE_PATH),
            "--dry-run",
            "--export-dashboard",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        assert res.returncode == 0
        assert "Dry-run mode enabled" in res.stdout or "Dry run" in res.stdout or "dry_run" in res.stdout
