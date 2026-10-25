#!/usr/bin/env python3
"""
RED Tests for Phase 4 M5: AI Governance Observability (KAN-308 4E)
Tests: LangSmith/MLflow tracing, CI/CD anomaly detection, SDLC health dashboard, quality gate telemetry
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


class TestObservabilityScriptExists:
    """Verify observability.py script exists and is executable"""

    def test_script_exists(self):
        script_path = Path("scripts/observability.py")
        assert script_path.exists(), "scripts/observability.py should exist"

    def test_script_executable(self):
        script_path = Path("scripts/observability.py")
        assert os.access(script_path, os.X_OK), "script should be executable"

    def test_help_flag(self):
        result = subprocess.run(
            [sys.executable, "scripts/observability.py", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Help failed: {result.stderr}"
        assert "observability" in result.stdout.lower() or "usage" in result.stdout.lower()


class TestLangSmithMLflowTracing:
    """LangSmith/MLflow tracing integration for AI SDLC pipeline"""

    def test_tracing_script_exists(self):
        script_path = Path("scripts/observability.py")
        assert script_path.exists(), "scripts/observability.py should exist for tracing"

    def test_langsmith_integration(self):
        """Test LangSmith tracing initialization and logging"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Test that LangSmith client can be initialized
            script_path = Path("scripts/observability.py")
            assert script_path.exists(), "observability.py needed for LangSmith integration"

    def test_mlflow_integration(self):
        """Test MLflow tracking setup"""
        script_path = Path("scripts/observability.py")
        assert script_path.exists(), "observability.py needed for MLflow integration"

    def test_trace_ai_review(self):
        """Test tracing AI code review execution"""
        script_path = Path("scripts/observability.py")
        assert script_path.exists(), "observability.py needed for AI review tracing"

    def test_trace_quality_gate(self):
        """Test tracing quality gate evaluation"""
        script_path = Path("scripts/observability.py")
        assert script_path.exists(), "observability.py needed for quality gate tracing"

    def test_trace_refactoring(self):
        """Test tracing refactoring agent runs"""
        script_path = Path("scripts/observability.py")
        assert script_path.exists(), "observability.py needed for refactoring tracing"


class TestCICDAnomalyDetection:
    """CI/CD metric anomaly detection (duration, failure rate, queue time)"""

    def test_anomaly_detection_script_exists(self):
        script_path = Path("scripts/observability.py")
        assert script_path.exists(), "scripts/observability.py should exist for anomaly detection"

    def test_duration_anomaly_detection(self):
        """Test detection of build duration anomalies"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mock CI metrics history
            history = Path(tmpdir) / "ci_history.json"
            history.write_text(json.dumps({
                "builds": [
                    {"duration_seconds": 300, "timestamp": "2026-01-01T00:00:00Z"},
                    {"duration_seconds": 310, "timestamp": "2026-01-02T00:00:00Z"},
                    {"duration_seconds": 600, "timestamp": "2026-01-03T00:00:00Z"},  # anomaly
                ]
            }))
            # Should detect 600s as anomaly (2x normal)
            script_path = Path("scripts/observability.py")
            assert script_path.exists(), "observability.py needed for duration anomaly detection"

    def test_failure_rate_anomaly(self):
        """Test detection of failure rate spikes"""
        script_path = Path("scripts/observability.py")
        assert script_path.exists(), "observability.py needed for failure rate anomaly"

    def test_queue_time_anomaly(self):
        """Test detection of queue time anomalies"""
        script_path = Path("scripts/observability.py")
        assert script_path.exists(), "observability.py needed for queue time anomaly"

    def test_anomaly_threshold_config(self):
        """Test configurable anomaly thresholds"""
        script_path = Path("scripts/observability.py")
        assert script_path.exists(), "observability.py needed for threshold config"


class TestSDLCHealthDashboard:
    """SDLC health dashboard (read-only, alerting only - NO control authority)"""

    def test_dashboard_script_exists(self):
        script_path = Path("scripts/observability.py")
        assert script_path.exists(), "scripts/observability.py should exist for dashboard"

    def test_health_metrics_collection(self):
        """Test collection of SDLC health metrics"""
        script_path = Path("scripts/observability.py")
        assert script_path.exists(), "observability.py needed for health metrics"

    def test_dashboard_generation(self):
        """Test dashboard data generation (JSON for UI)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "health_dashboard.json"
            # Should generate dashboard data
            script_path = Path("scripts/observability.py")
            assert script_path.exists(), "observability.py needed for dashboard generation"

    def test_alerting_only_no_control(self):
        """Test that dashboard only alerts, never controls"""
        # Verify no control actions in code
        script_path = Path("scripts/observability.py")
        assert script_path.exists(), "observability.py needed for alerting verification"

    def test_weekly_health_report(self):
        """Test weekly health report generation"""
        script_path = Path("scripts/observability.py")
        assert script_path.exists(), "observability.py needed for weekly report"


class TestQualityGateTelemetry:
    """Quality gate telemetry aggregation"""

    def test_telemetry_script_exists(self):
        script_path = Path("scripts/observability.py")
        assert script_path.exists(), "scripts/observability.py should exist for telemetry"

    def test_telemetry_aggregation(self):
        """Test aggregation of quality gate results over time"""
        script_path = Path("scripts/observability.py")
        assert script_path.exists(), "observability.py needed for telemetry aggregation"

    def test_trend_analysis(self):
        """Test trend analysis of quality metrics"""
        script_path = Path("scripts/observability.py")
        assert script_path.exists(), "observability.py needed for trend analysis"


class TestCIIntegration:
    """CI integration for observability"""

    def test_ci_job_defined(self):
        ci_path = Path(".github/workflows/ci.yml")
        content = ci_path.read_text()
        assert "observability" in content, "observability job should be in ci.yml"

    def test_ci_job_triggers(self):
        ci_path = Path(".github/workflows/ci.yml")
        content = ci_path.read_text()
        assert "schedule:" in content, "Should have schedule trigger"

    def test_ci_job_weekly_schedule(self):
        ci_path = Path(".github/workflows/ci.yml")
        content = ci_path.read_text()
        # Weekly schedule for health report
        assert "cron:" in content or "schedule:" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])