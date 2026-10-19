"""tests/test_multiplatform_free_limit_guard.py
=============================================
TDD Unit & Integration Test Suite for Multi-Platform Free Limit Guardrail System.
Validates:
1. Multi-platform quota definitions (Northflank, Cloudflare, Vercel, Gemini, Kaggle).
2. Threshold transitions:
   - < 80%: Status is OK / NORMAL (traffic allowed, no alert).
   - >= 80% and < 90%: Status is WARNING (traffic allowed, warning alert emitted).
   - >= 90%: Status is CRITICAL_SHUTDOWN (fail-closed, shutdown action triggered).
3. Fail-closed behavior on corrupted / missing / invalid data.
4. Safe dry-run vs enforcement dispatch for platform shutdowns (Northflank pause, etc.).
5. AI Provider Router Gemini cutoff at >= 90% quota.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.multiplatform_free_limit_guard import (
    DEFAULT_SHUTDOWN_THRESHOLD,
    DEFAULT_WARNING_THRESHOLD,
    PLATFORM_FREE_LIMITS,
    GuardStatus,
    PlatformDecision,
    evaluate_platform_usage,
    evaluate_all_platforms,
    enforce_platform_shutdown,
)


class TestPlatformFreeLimitsDefinitions:
    """Verifies official zero-cost free limits are configured for all project platforms."""

    def test_all_expected_platforms_defined(self):
        expected_platforms = {"northflank", "cloudflare", "vercel", "gemini", "kaggle"}
        assert expected_platforms.issubset(set(PLATFORM_FREE_LIMITS.keys()))

    def test_northflank_free_limits(self):
        nf = PLATFORM_FREE_LIMITS["northflank"]
        assert nf["bandwidth_gb_monthly"] == 10.0
        assert nf["build_minutes_monthly"] == 300.0
        assert nf["instance_count"] == 1.0

    def test_cloudflare_free_limits(self):
        cf = PLATFORM_FREE_LIMITS["cloudflare"]
        assert cf["worker_requests_daily"] == 100_000.0
        assert cf["kv_reads_daily"] == 100_000.0
        assert cf["kv_writes_daily"] == 1_000.0
        assert cf["d1_rows_read_daily"] == 5_000_000.0
        assert cf["d1_rows_written_daily"] == 100_000.0
        assert cf["r2_storage_gb_monthly"] == 10.0

    def test_vercel_free_limits(self):
        vercel = PLATFORM_FREE_LIMITS["vercel"]
        assert vercel["bandwidth_gb_monthly"] == 100.0
        assert vercel["serverless_gb_hours_monthly"] == 100.0

    def test_gemini_free_limits(self):
        gemini = PLATFORM_FREE_LIMITS["gemini"]
        assert gemini["requests_daily"] == 1500.0
        assert gemini["requests_per_minute"] == 15.0

    def test_kaggle_free_limits(self):
        kaggle = PLATFORM_FREE_LIMITS["kaggle"]
        assert kaggle["gpu_hours_weekly"] == 30.0


class TestUsageEvaluationThresholds:
    """Verifies exact 80% warning and 90% shutdown logic across platforms."""

    def test_normal_usage_below_80_percent(self):
        snapshot = {
            "bandwidth_gb_monthly": 5.0,  # 50% of 10GB
            "build_minutes_monthly": 100.0,  # 33.3% of 300
            "instance_count": 1.0,
        }
        decision = evaluate_platform_usage("northflank", snapshot)
        assert decision.status == GuardStatus.OK
        assert decision.allowed is True
        assert decision.highest_ratio == pytest.approx(0.50, abs=0.01)
        assert decision.warning_triggered is False
        assert decision.shutdown_triggered is False

    def test_warning_at_exactly_80_percent(self):
        snapshot = {
            "bandwidth_gb_monthly": 8.0,  # 80.0% of 10GB
            "build_minutes_monthly": 150.0,
            "instance_count": 1.0,
        }
        decision = evaluate_platform_usage(
            "northflank",
            snapshot,
            warning_threshold=DEFAULT_WARNING_THRESHOLD,
            shutdown_threshold=DEFAULT_SHUTDOWN_THRESHOLD,
        )
        assert decision.status == GuardStatus.WARNING
        assert decision.allowed is True
        assert decision.highest_ratio == pytest.approx(0.80, abs=0.001)
        assert decision.warning_triggered is True
        assert decision.shutdown_triggered is False
        assert any("80%" in reason or "warning" in reason.lower() for reason in decision.reasons)

    def test_warning_between_80_and_90_percent(self):
        snapshot = {
            "worker_requests_daily": 85_000.0,  # 85% of 100k
            "kv_reads_daily": 10_000.0,
            "kv_writes_daily": 100.0,
            "d1_rows_read_daily": 500_000.0,
            "d1_rows_written_daily": 10_000.0,
            "r2_storage_gb_monthly": 2.0,
        }
        decision = evaluate_platform_usage("cloudflare", snapshot)
        assert decision.status == GuardStatus.WARNING
        assert decision.allowed is True
        assert decision.highest_ratio == pytest.approx(0.85, abs=0.001)
        assert decision.warning_triggered is True
        assert decision.shutdown_triggered is False

    def test_critical_shutdown_at_exactly_90_percent(self):
        snapshot = {
            "worker_requests_daily": 90_000.0,  # Exactly 90.0% of 100k
            "kv_reads_daily": 10_000.0,
            "kv_writes_daily": 100.0,
            "d1_rows_read_daily": 500_000.0,
            "d1_rows_written_daily": 10_000.0,
            "r2_storage_gb_monthly": 2.0,
        }
        decision = evaluate_platform_usage(
            "cloudflare",
            snapshot,
            warning_threshold=0.80,
            shutdown_threshold=0.90,
        )
        assert decision.status == GuardStatus.CRITICAL_SHUTDOWN
        assert decision.allowed is False
        assert decision.highest_ratio == pytest.approx(0.90, abs=0.001)
        assert decision.warning_triggered is True
        assert decision.shutdown_triggered is True
        assert any("90%" in reason or "shutdown" in reason.lower() for reason in decision.reasons)

    def test_critical_shutdown_above_90_percent(self):
        snapshot = {
            "requests_daily": 1400.0,  # 1400 / 1500 = 93.3%
            "requests_per_minute": 10.0,
        }
        decision = evaluate_platform_usage("gemini", snapshot)
        assert decision.status == GuardStatus.CRITICAL_SHUTDOWN
        assert decision.allowed is False
        assert decision.highest_ratio == pytest.approx(1400.0 / 1500.0, abs=0.01)
        assert decision.shutdown_triggered is True


class TestFailClosedBehavior:
    """Verifies fail-closed safety when data is invalid, non-finite, or empty."""

    def test_unknown_platform_raises_or_denies(self):
        decision = evaluate_platform_usage("unknown_cloud", {})
        assert decision.allowed is False
        assert decision.status == GuardStatus.CRITICAL_SHUTDOWN

    def test_negative_or_nan_usage_fails_closed(self):
        snapshot = {
            "bandwidth_gb_monthly": float("nan"),
            "build_minutes_monthly": 50.0,
            "instance_count": 1.0,
        }
        decision = evaluate_platform_usage("northflank", snapshot)
        assert decision.allowed is False
        assert decision.status == GuardStatus.CRITICAL_SHUTDOWN

    def test_empty_snapshot_fails_closed(self):
        decision = evaluate_platform_usage("northflank", {})
        assert decision.allowed is False
        assert decision.status == GuardStatus.CRITICAL_SHUTDOWN


class TestMultiPlatformEvaluation:
    """Verifies multi-platform full evaluation aggregation."""

    def test_evaluate_all_platforms_aggregated(self):
        system_snapshot = {
            "northflank": {
                "bandwidth_gb_monthly": 4.0,
                "build_minutes_monthly": 50.0,
                "instance_count": 1.0,
            },
            "cloudflare": {
                "worker_requests_daily": 82_000.0,  # Warning: 82%
                "kv_reads_daily": 20_000.0,
                "kv_writes_daily": 200.0,
                "d1_rows_read_daily": 1_000_000.0,
                "d1_rows_written_daily": 10_000.0,
                "r2_storage_gb_monthly": 1.0,
            },
            "vercel": {
                "bandwidth_gb_monthly": 10.0,
                "serverless_gb_hours_monthly": 5.0,
            },
            "gemini": {
                "requests_daily": 1450.0,  # Critical: 96.6% >= 90%
                "requests_per_minute": 5.0,
            },
            "kaggle": {
                "gpu_hours_weekly": 10.0,
            },
        }

        report = evaluate_all_platforms(system_snapshot)
        assert report["overall_status"] == GuardStatus.CRITICAL_SHUTDOWN.value
        assert report["overall_allowed"] is False
        assert len(report["warning_platforms"]) == 2  # cloudflare and gemini
        assert len(report["shutdown_platforms"]) == 1  # gemini
        assert "gemini" in report["shutdown_platforms"]
        assert "cloudflare" in report["warning_platforms"]


class TestEnforcePlatformShutdown:
    """Verifies that platform shutdown calls are correctly dispatched or safely dry-run."""

    def test_dry_run_does_not_call_remote_api(self):
        result = enforce_platform_shutdown(
            "northflank",
            reason="Bandwidth reached 92%",
            dry_run=True,
        )
        assert result["dry_run"] is True
        assert result["executed"] is False
        assert result["platform"] == "northflank"

    @patch("urllib.request.urlopen")
    def test_northflank_live_pause_invocation(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"success": true}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = enforce_platform_shutdown(
            "northflank",
            reason="Bandwidth reached 95%",
            dry_run=False,
            token="test-token",
            project_id="default",
            service_id="horoconsultant",
        )
        assert result["executed"] is True
        assert result["platform"] == "northflank"
        assert result["action"] == "pause_service"
