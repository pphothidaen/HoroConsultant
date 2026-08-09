#!/usr/bin/env python3
"""
scripts/synthetic_health_monitor.py
=====================================
Post-Deployment Synthetic Health Monitoring Cron.

Runs scheduled 5-minute health ping checks against:
  - /health endpoint (Vercel Edge Gateway)
  - /api/v1/health alias (Vercel Edge Gateway)
  - HuggingFace Spaces Backend /health
  - Fly.io Backend /health

Outputs ping results with ASCII status tags and optionally pushes
alert metrics to Grafana Cloud via OTLP when degradation is detected.

Usage:
  # Run once (single ping cycle — useful for CI/CD)
  python3 scripts/synthetic_health_monitor.py --once

  # Run continuously every 5 minutes (daemon mode)
  python3 scripts/synthetic_health_monitor.py --daemon

  # Run continuously with custom interval
  python3 scripts/synthetic_health_monitor.py --daemon --interval 120

  # Dry-run: Show config and exit
  python3 scripts/synthetic_health_monitor.py --dry-run

Pure ASCII logging tags enforced: [OK], [ERROR], [INFO], [WARNING].
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ──────────────────────────────────────────────────────────────────────────────
# Project root on sys.path
# ──────────────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ──────────────────────────────────────────────────────────────────────────────
# Production endpoint constants
# ──────────────────────────────────────────────────────────────────────────────
VERCEL_GATEWAY_URL = os.getenv("VERCEL_GATEWAY_URL", "https://horo-consultant-psi.vercel.app")
HF_BACKEND_URL = os.getenv("HF_BACKEND_URL", "https://pphothidaen-horoconsultant-core-backend.hf.space")
FLY_BACKEND_URL = os.getenv("FLY_BACKEND_URL", "https://horoconsultant-core-backend.fly.dev")

DEFAULT_PING_INTERVAL_SECONDS = 300  # 5 minutes


# ──────────────────────────────────────────────────────────────────────────────
# Health check targets
# ──────────────────────────────────────────────────────────────────────────────
HEALTH_TARGETS = [
    {
        "name": "Vercel Gateway /health",
        "url": f"{VERCEL_GATEWAY_URL}/health",
        "critical": True,
    },
    {
        "name": "Vercel Gateway /api/v1/health",
        "url": f"{VERCEL_GATEWAY_URL}/api/v1/health",
        "critical": False,
    },
    {
        "name": "HuggingFace Backend /health",
        "url": f"{HF_BACKEND_URL}/health",
        "critical": True,
    },
    {
        "name": "Fly.io Backend /health",
        "url": f"{FLY_BACKEND_URL}/health",
        "critical": False,
    },
]


# ──────────────────────────────────────────────────────────────────────────────
# HTTP helper
# ──────────────────────────────────────────────────────────────────────────────
def _ping(url: str, timeout: int = 10) -> Tuple[int, float, Optional[str]]:
    """
    Send GET request to url. Returns (status_code, latency_ms, error_msg).
    Returns (0, latency_ms, error) on connection failure.
    """
    headers = {
        "User-Agent": "HoroConsultant-SyntheticMonitor/1.0",
        "Accept": "application/json",
    }
    req = urllib.request.Request(url, headers=headers, method="GET")
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            resp.read()  # consume body
            latency = (time.perf_counter() - t0) * 1000
            return resp.status, latency, None
    except urllib.error.HTTPError as e:
        latency = (time.perf_counter() - t0) * 1000
        e.read()
        return e.code, latency, f"HTTP {e.code}: {e.reason}"
    except Exception as exc:
        latency = (time.perf_counter() - t0) * 1000
        return 0, latency, str(exc)


# ──────────────────────────────────────────────────────────────────────────────
# Grafana OTLP alert metric push
# ──────────────────────────────────────────────────────────────────────────────
def _push_alert_metric_to_grafana(target_name: str, status_code: int, latency_ms: float, is_healthy: bool) -> None:
    """
    Push synthetic monitor health ping metric to Grafana Cloud via OTLP.
    No-op if GRAFANA environment variables are not set.
    """
    grafana_url = os.getenv("GRAFANA_CLOUD_URL", os.getenv("GRAFANA_URL", ""))
    user_id = os.getenv("GRAFANA_USER_ID", "")
    api_key = os.getenv(
        "GRAFANA_API_KEY",
        os.getenv("GRAFANA_SERVICE_ACCOUNT_TOKEN", os.getenv("GRAFANA_TOKEN", ""))
    )

    if not grafana_url or not api_key:
        return  # Grafana not configured; skip push

    now_nano = str(int(time.time() * 1e9))
    health_value = 1.0 if is_healthy else 0.0
    label = target_name.replace(" ", "_").lower()

    payload: Dict[str, Any] = {
        "resourceMetrics": [
            {
                "resource": {
                    "attributes": [
                        {"key": "service.name", "value": {"stringValue": "horoconsultant"}},
                        {"key": "service.namespace", "value": {"stringValue": "synthetic-monitor"}},
                    ]
                },
                "scopeMetrics": [
                    {
                        "scope": {"name": "synthetic_health_monitor", "version": "1.0.0"},
                        "metrics": [
                            {
                                "name": "synthetic_health_status",
                                "description": "Synthetic health check result (1=healthy, 0=degraded)",
                                "gauge": {
                                    "dataPoints": [
                                        {
                                            "timeUnixNano": now_nano,
                                            "asDouble": health_value,
                                            "attributes": [
                                                {"key": "target", "value": {"stringValue": label}},
                                                {"key": "url", "value": {"stringValue": target_name}},
                                            ],
                                        }
                                    ]
                                },
                            },
                            {
                                "name": "synthetic_health_latency_ms",
                                "description": "Synthetic health ping response latency (ms)",
                                "gauge": {
                                    "dataPoints": [
                                        {
                                            "timeUnixNano": now_nano,
                                            "asDouble": latency_ms,
                                            "attributes": [
                                                {"key": "target", "value": {"stringValue": label}},
                                            ],
                                        }
                                    ]
                                },
                            },
                            {
                                "name": "synthetic_health_http_status",
                                "description": "HTTP status code from synthetic health ping",
                                "gauge": {
                                    "dataPoints": [
                                        {
                                            "timeUnixNano": now_nano,
                                            "asDouble": float(status_code),
                                            "attributes": [
                                                {"key": "target", "value": {"stringValue": label}},
                                            ],
                                        }
                                    ]
                                },
                            },
                        ],
                    }
                ],
            }
        ]
    }

    otlp_endpoint = os.getenv("GRAFANA_OTLP_ENDPOINT", "").strip()
    if not otlp_endpoint:
        push_url = urllib.parse.urljoin(grafana_url, "/otlp/v1/metrics")
    elif not otlp_endpoint.endswith("/v1/metrics"):
        push_url = otlp_endpoint.rstrip("/") + "/v1/metrics"
    else:
        push_url = otlp_endpoint

    headers: Dict[str, str] = {"Content-Type": "application/json", "User-Agent": "HoroConsultant-SyntheticMonitor/1.0"}
    if user_id and "your_grafana" not in user_id.lower():
        import base64
        cred = base64.b64encode(f"{user_id}:{api_key}".encode()).decode()
        headers["Authorization"] = f"Basic {cred}"
    else:
        headers["Authorization"] = f"Bearer {api_key}"

    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(push_url, data=data_bytes, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            _ = resp.read()
            code = getattr(resp, "status", 200)
            if code in (200, 202, 204):
                print(f"[OK] Grafana OTLP push for '{target_name}': HTTP {code}")
    except Exception as exc:
        print(f"[WARNING] Grafana OTLP push skipped for '{target_name}': {exc}")


# ──────────────────────────────────────────────────────────────────────────────
# Single ping cycle
# ──────────────────────────────────────────────────────────────────────────────
def run_ping_cycle(targets: List[Dict[str, Any]], timeout: int = 10) -> bool:
    """
    Execute one complete ping cycle across all health targets.
    Returns True if all CRITICAL targets are healthy.
    """
    ts = time.strftime("%Y-%m-%d %H:%M:%S %Z", time.localtime())
    print(f"\n[INFO] ── Synthetic Health Ping Cycle: {ts} ──────────────────────────")

    all_critical_healthy = True
    cycle_results: List[Dict[str, Any]] = []

    for target in targets:
        name = target["name"]
        url = target["url"]
        critical = target.get("critical", True)

        status, latency, error = _ping(url, timeout=timeout)
        is_healthy = (status == 200)

        if is_healthy:
            print(f"[OK]      {name}: HTTP {status} | {latency:.0f}ms")
        elif status in (502, 503, 504):
            print(f"[WARNING] {name}: HTTP {status} | {latency:.0f}ms (Degraded/Gateway Error)")
        elif status == 0:
            print(f"[ERROR]   {name}: UNREACHABLE | {latency:.0f}ms | {error}")
        else:
            print(f"[WARNING] {name}: HTTP {status} | {latency:.0f}ms")

        if not is_healthy and critical:
            all_critical_healthy = False

        # Push metric to Grafana Cloud (no-op if env vars not set)
        _push_alert_metric_to_grafana(name, status, latency, is_healthy)

        cycle_results.append({
            "target": name,
            "url": url,
            "status": status,
            "latency_ms": round(latency, 1),
            "healthy": is_healthy,
            "critical": critical,
        })

    healthy_count = sum(1 for r in cycle_results if r["healthy"])
    print(f"[INFO] Cycle complete: {healthy_count}/{len(cycle_results)} targets healthy")

    if not all_critical_healthy:
        print("[WARNING] One or more CRITICAL targets are DEGRADED. Check services.")
    else:
        print("[OK] All critical health targets are operational.")

    return all_critical_healthy


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Synthetic Health Monitoring Cron for HoroConsultant Multi-Cloud."
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single ping cycle and exit (useful for CI/CD health gates).",
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run continuously in daemon mode, pinging every --interval seconds.",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=DEFAULT_PING_INTERVAL_SECONDS,
        help=f"Ping interval in seconds for daemon mode (default: {DEFAULT_PING_INTERVAL_SECONDS}).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="HTTP ping timeout per request in seconds (default: 10).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print configuration and exit without sending any HTTP requests.",
    )
    return parser


def main() -> int:
    # Load .env if available
    try:
        from dotenv import load_dotenv
        env_file = PROJECT_ROOT / ".env"
        if env_file.exists():
            load_dotenv(env_file)
    except ImportError:
        pass

    parser = build_parser()
    args = parser.parse_args()

    if args.dry_run:
        print("[INFO] Dry-run mode — configuration:")
        for t in HEALTH_TARGETS:
            print(f"  [INFO] Target: {t['name']} | URL: {t['url']} | Critical: {t['critical']}")
        print(f"[INFO] Ping interval: {args.interval}s | Timeout: {args.timeout}s")
        print("[OK] Dry-run complete — no HTTP requests sent.")
        return 0

    # Default to --once if no mode specified
    if not args.daemon and not args.once:
        args.once = True

    if args.once:
        print("[INFO] Running single synthetic health ping cycle...")
        healthy = run_ping_cycle(HEALTH_TARGETS, timeout=args.timeout)
        return 0 if healthy else 1

    # Daemon mode
    print(f"[INFO] Synthetic health monitor daemon started (interval: {args.interval}s)")
    print("[INFO] Press Ctrl+C to stop.")
    iteration = 0
    try:
        while True:
            iteration += 1
            run_ping_cycle(HEALTH_TARGETS, timeout=args.timeout)
            print(f"[INFO] Next ping in {args.interval}s... (iteration #{iteration})")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n[INFO] Monitor daemon stopped by user.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
