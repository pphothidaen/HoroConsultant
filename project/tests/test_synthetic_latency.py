"""
project/tests/test_synthetic_latency.py
=======================================
Unit tests for synthetic health monitor latency SLA checking.
"""

from pathlib import Path
from unittest.mock import patch
from scripts.synthetic_health_monitor import run_ping_cycle, build_parser


def test_synthetic_latency_threshold_reporting():
    targets = [
        {"name": "Fast Service", "url": "https://fast.service/health", "critical": True},
        {"name": "Slow Service", "url": "https://slow.service/health", "critical": True},
    ]

    # Mock ping to return fast (100ms) for Fast Service, slow (6000ms) for Slow Service
    def mock_ping(url, timeout=10):
        if "fast" in url:
            return 200, 100.0, '{"status":"ok"}', None
        return 200, 6000.0, '{"status":"ok"}', None

    with patch("scripts.synthetic_health_monitor._ping", side_effect=mock_ping):
        with patch("scripts.synthetic_health_monitor._push_alert_metric_to_grafana"):
            report_path = Path("/tmp/test_synth_latency_report.json")
            healthy = run_ping_cycle(targets, max_latency_ms=5000.0, report_path=report_path)

            assert healthy is True  # Status is 200 and healthy payload
            assert report_path.exists()

            import json
            data = json.loads(report_path.read_text(encoding="utf-8"))
            results = data["results"]

            fast_res = next(r for r in results if r["target"] == "Fast Service")
            slow_res = next(r for r in results if r["target"] == "Slow Service")

            assert fast_res["latency_degraded"] is False
            assert slow_res["latency_degraded"] is True
            assert slow_res["latency_ms"] == 6000.0


def test_synthetic_parser_max_latency_arg():
    parser = build_parser()
    args = parser.parse_args(["--once", "--max-latency-ms", "3500"])
    assert args.max_latency_ms == 3500.0
