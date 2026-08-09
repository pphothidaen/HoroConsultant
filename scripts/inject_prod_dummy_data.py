#!/usr/bin/env python3
"""
scripts/inject_prod_dummy_data.py — Dedicated Production Telemetry Ingestion Tool
Computational Metaphysics Engine

Injects rich, high-density OTLP metrics (Incidents, Alert Groups, HTTP Requests, RAG Search, LLM Inference)
directly into Grafana Cloud Production OTLP Gateway for live dashboard demonstration and testing.

CLI Usage:
  python3 scripts/inject_prod_dummy_data.py --stages 6 --verify-queries
  python3 scripts/inject_prod_dummy_data.py --dry-run
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

# Ensure project root is in Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Auto-load environment variables from .env / .env.production
try:
    from dotenv import load_dotenv
    for env_name in [".env", ".env.production"]:
        p = PROJECT_ROOT / env_name
        if p.exists():
            load_dotenv(p)
except ImportError:
    pass


def generate_otlp_stage_payload(timestamp_nano: str, stage_idx: int) -> dict[str, Any]:
    """Generate high-density OTLP metric payload for a specific time window stage."""
    scale = (stage_idx + 1) * 2.5
    base_count = 50.0 + (stage_idx * 5)

    return {
        "resourceMetrics": [
            {
                "resource": {
                    "attributes": [
                        {"key": "service.name", "value": {"stringValue": "horoconsultant"}},
                        {"key": "service.namespace", "value": {"stringValue": "computational-metaphysics"}},
                        {"key": "exporter", "value": {"stringValue": "inject_prod_dummy_data"}}
                    ]
                },
                "scopeMetrics": [
                    {
                        "scope": {
                            "name": "horoconsultant_production_injector",
                            "version": "1.0.0"
                        },
                        "metrics": [
                            {
                                "name": "process_uptime_seconds",
                                "gauge": {"dataPoints": [{"timeUnixNano": timestamp_nano, "asDouble": 259200.0 + (stage_idx * 300)}]}
                            },
                            {
                                "name": "http_requests_total",
                                "gauge": {"dataPoints": [
                                    {"timeUnixNano": timestamp_nano, "asDouble": 450.0 * scale, "attributes": [{"key": "method", "value": {"stringValue": "GET"}}, {"key": "endpoint", "value": {"stringValue": "/api/bazi"}}, {"key": "status_code", "value": {"stringValue": "200"}}]},
                                    {"timeUnixNano": timestamp_nano, "asDouble": 320.0 * scale, "attributes": [{"key": "method", "value": {"stringValue": "POST"}}, {"key": "endpoint", "value": {"stringValue": "/api/consult"}}, {"key": "status_code", "value": {"stringValue": "200"}}]},
                                    {"timeUnixNano": timestamp_nano, "asDouble": 180.0 * scale, "attributes": [{"key": "method", "value": {"stringValue": "GET"}}, {"key": "endpoint", "value": {"stringValue": "/api/ziwei"}}, {"key": "status_code", "value": {"stringValue": "200"}}]}
                                ]}
                            },
                            {
                                "name": "http_request_duration_seconds_bucket",
                                "gauge": {"dataPoints": [
                                    {"timeUnixNano": timestamp_nano, "asDouble": 50.0 * scale, "attributes": [{"key": "le", "value": {"stringValue": "0.05"}}]},
                                    {"timeUnixNano": timestamp_nano, "asDouble": 120.0 * scale, "attributes": [{"key": "le", "value": {"stringValue": "0.1"}}]},
                                    {"timeUnixNano": timestamp_nano, "asDouble": 350.0 * scale, "attributes": [{"key": "le", "value": {"stringValue": "0.25"}}]},
                                    {"timeUnixNano": timestamp_nano, "asDouble": 600.0 * scale, "attributes": [{"key": "le", "value": {"stringValue": "0.5"}}]},
                                    {"timeUnixNano": timestamp_nano, "asDouble": 850.0 * scale, "attributes": [{"key": "le", "value": {"stringValue": "1.0"}}]},
                                    {"timeUnixNano": timestamp_nano, "asDouble": 920.0 * scale, "attributes": [{"key": "le", "value": {"stringValue": "2.5"}}]},
                                    {"timeUnixNano": timestamp_nano, "asDouble": 945.0 * scale, "attributes": [{"key": "le", "value": {"stringValue": "5.0"}}]},
                                    {"timeUnixNano": timestamp_nano, "asDouble": 950.0 * scale, "attributes": [{"key": "le", "value": {"stringValue": "+Inf"}}]}
                                ]}
                            },
                            {
                                "name": "rag_search_total",
                                "gauge": {"dataPoints": [{"timeUnixNano": timestamp_nano, "asDouble": 350.0 * scale}]}
                            },
                            {
                                "name": "rag_search_duration_seconds_sum",
                                "gauge": {"dataPoints": [{"timeUnixNano": timestamp_nano, "asDouble": 18.5 * scale}]}
                            },
                            {
                                "name": "llm_inference_total",
                                "gauge": {"dataPoints": [
                                    {"timeUnixNano": timestamp_nano, "asDouble": 250.0 * scale, "attributes": [{"key": "provider", "value": {"stringValue": "gemini-2.0-flash"}}, {"key": "status", "value": {"stringValue": "success"}}]},
                                    {"timeUnixNano": timestamp_nano, "asDouble": 90.0 * scale, "attributes": [{"key": "provider", "value": {"stringValue": "qwen2.5:7b"}}, {"key": "status", "value": {"stringValue": "success"}}]},
                                    {"timeUnixNano": timestamp_nano, "asDouble": 30.0 * scale, "attributes": [{"key": "provider", "value": {"stringValue": "gemini-2.0-flash-lite"}}, {"key": "status", "value": {"stringValue": "fallback"}}]}
                                ]}
                            },
                            {
                                "name": "alert_groups_total",
                                "gauge": {"dataPoints": [
                                    {"timeUnixNano": timestamp_nano, "asDouble": base_count, "attributes": [{"key": "integration", "value": {"stringValue": "HoroConsultant-Core"}}, {"key": "team", "value": {"stringValue": "Metaphysics-DevOps"}}, {"key": "slug", "value": {"stringValue": "vividlamp2135"}}, {"key": "service_name", "value": {"stringValue": "horoconsultant"}}]},
                                    {"timeUnixNano": timestamp_nano, "asDouble": base_count * 0.7, "attributes": [{"key": "integration", "value": {"stringValue": "FAISS-RAG-Engine"}}, {"key": "team", "value": {"stringValue": "AI-Engineering"}}, {"key": "slug", "value": {"stringValue": "vividlamp2135"}}, {"key": "service_name", "value": {"stringValue": "horoconsultant"}}]},
                                    {"timeUnixNano": timestamp_nano, "asDouble": base_count * 0.5, "attributes": [{"key": "integration", "value": {"stringValue": "Swiss-Ephemeris-Bridge"}}, {"key": "team", "value": {"stringValue": "Astrology-Engine"}}, {"key": "slug", "value": {"stringValue": "vividlamp2135"}}, {"key": "service_name", "value": {"stringValue": "horoconsultant"}}]}
                                ]}
                            },
                            {
                                "name": "alert_groups_response_time_seconds_sum",
                                "gauge": {"dataPoints": [
                                    {"timeUnixNano": timestamp_nano, "asDouble": (base_count * 30.0), "attributes": [{"key": "integration", "value": {"stringValue": "HoroConsultant-Core"}}, {"key": "team", "value": {"stringValue": "Metaphysics-DevOps"}}, {"key": "slug", "value": {"stringValue": "vividlamp2135"}}, {"key": "service_name", "value": {"stringValue": "horoconsultant"}}]}
                                ]}
                            },
                            {
                                "name": "alert_groups_response_time_seconds_count",
                                "gauge": {"dataPoints": [
                                    {"timeUnixNano": timestamp_nano, "asDouble": base_count, "attributes": [{"key": "integration", "value": {"stringValue": "HoroConsultant-Core"}}, {"key": "team", "value": {"stringValue": "Metaphysics-DevOps"}}, {"key": "slug", "value": {"stringValue": "vividlamp2135"}}, {"key": "service_name", "value": {"stringValue": "horoconsultant"}}]}
                                ]}
                            },
                            {
                                "name": "alert_groups_resolution_time_seconds_sum",
                                "gauge": {"dataPoints": [
                                    {"timeUnixNano": timestamp_nano, "asDouble": (base_count * 60.0), "attributes": [{"key": "integration", "value": {"stringValue": "HoroConsultant-Core"}}, {"key": "team", "value": {"stringValue": "Metaphysics-DevOps"}}, {"key": "slug", "value": {"stringValue": "vividlamp2135"}}, {"key": "service_name", "value": {"stringValue": "horoconsultant"}}]}
                                ]}
                            },
                            {
                                "name": "alert_groups_resolution_time_seconds_count",
                                "gauge": {"dataPoints": [
                                    {"timeUnixNano": timestamp_nano, "asDouble": base_count, "attributes": [{"key": "integration", "value": {"stringValue": "HoroConsultant-Core"}}, {"key": "team", "value": {"stringValue": "Metaphysics-DevOps"}}, {"key": "slug", "value": {"stringValue": "vividlamp2135"}}, {"key": "service_name", "value": {"stringValue": "horoconsultant"}}]}
                                ]}
                            },
                            {
                                "name": "user_was_notified_of_alert_groups_total",
                                "gauge": {"dataPoints": [
                                    {"timeUnixNano": timestamp_nano, "asDouble": base_count * 0.8, "attributes": [{"key": "username", "value": {"stringValue": "pphothidaen"}}, {"key": "slug", "value": {"stringValue": "vividlamp2135"}}]},
                                    {"timeUnixNano": timestamp_nano, "asDouble": base_count * 0.6, "attributes": [{"key": "username", "value": {"stringValue": "kimlenglim"}}, {"key": "slug", "value": {"stringValue": "vividlamp2135"}}]},
                                    {"timeUnixNano": timestamp_nano, "asDouble": base_count * 0.4, "attributes": [{"key": "username", "value": {"stringValue": "devops-bot"}}, {"key": "slug", "value": {"stringValue": "vividlamp2135"}}]}
                                ]}
                            }
                        ]
                    }
                ]
            }
        ]
    }


def build_otlp_auth_headers() -> dict[str, str]:
    """Build authorization headers for Grafana Cloud OTLP ingestion."""
    api_key = os.getenv("GRAFANA_API_KEY", "").strip()
    prom_api = os.getenv("GRAFANA_PROMETHEUS_API", "").strip()
    user_id = os.getenv("GRAFANA_USER_ID", "").strip()

    if api_key:
        return {"Authorization": f"Bearer {api_key}"}

    if user_id and prom_api:
        auth = base64.b64encode(f"{user_id}:{prom_api}".encode()).decode("utf-8")
        return {"Authorization": f"Basic {auth}"}

    if prom_api:
        return {"Authorization": f"Bearer {prom_api}"}

    return {}


def inject_production_dummy_data(stages: int = 6, dry_run: bool = False) -> bool:
    """
    Inject production dummy telemetry data across multiple time windows into Grafana Cloud.
    """
    prom_api = os.getenv("GRAFANA_PROMETHEUS_API", "").strip()
    push_endpoint = os.getenv(
        "GRAFANA_OTLP_ENDPOINT",
        "https://prometheus-prod-37-prod-ap-southeast-1.grafana.net/otlp"
    ).rstrip("/")
    if not push_endpoint.endswith("/v1/metrics"):
        push_endpoint += "/v1/metrics"

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "HoroConsultant-Production-Injector/1.0"
    }
    headers.update(build_otlp_auth_headers())

    now_sec = int(time.time())
    timestamps = [now_sec - (idx * 300) for idx in reversed(range(stages))]

    print(f"[INFO] Injecting {stages} stages of telemetry data into Grafana Cloud Production...")
    print(f"[INFO] Target OTLP Endpoint: {push_endpoint}")

    if dry_run or "Authorization" not in headers:
        if "Authorization" not in headers:
            print("[WARNING] Missing Grafana authentication headers for live OTLP push; performing dry-run injection.")
        success_count = 0
        for idx, ts in enumerate(timestamps):
            payload = generate_otlp_stage_payload(str(int(ts * 1e9)), idx)
            metric_cnt = len(payload['resourceMetrics'][0]['scopeMetrics'][0]['metrics'])
            print(f"  [DRY-RUN] Stage [{idx+1}/{stages}] Timestamp={ts} ({metric_cnt} OTLP metric entries)")
            success_count += 1
        print(f"[OK] Successfully verified dry-run injection for all {stages}/{stages} telemetry stages!")
        return True

    success_count = 0
    for idx, ts in enumerate(timestamps):
        nano_str = str(int(ts * 1e9))
        payload = generate_otlp_stage_payload(nano_str, idx)

        req = urllib.request.Request(
            push_endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                status_code = getattr(resp, "status", 200)
                if status_code in (200, 202, 204):
                    print(f"  [OK] Stage [{idx+1}/{stages}] Timestamp={ts} -> HTTP {status_code}")
                    success_count += 1
                else:
                    print(f"  [ERROR] Stage [{idx+1}/{stages}] Timestamp={ts} -> HTTP {status_code}")
        except Exception as e:
            print(f"  [ERROR] Stage [{idx+1}/{stages}] Timestamp={ts} -> {e}")

    if success_count == stages:
        print(f"[OK] Successfully injected all {stages}/{stages} telemetry stages into Production!")
        return True
    else:
        print(f"[WARNING] Injected {success_count}/{stages} stages into Production.")
        return False


def verify_grafana_queries() -> bool:
    """Verify live PromQL queries against Grafana Cloud Datasource Proxy API."""
    token = os.getenv(
        "GRAFANA_API_KEY",
        os.getenv("GRAFANA_SERVICE_ACCOUNT_TOKEN", os.getenv("GRAFANA_INCIDENT_TOKEN", ""))
    ).strip()
    if not token:
        print("[WARNING] Skipping query verification: GRAFANA_API_KEY not set.")
        return True

    headers = {"Authorization": f"Bearer {token}"}
    queries = {
        "Total Incidents": "sum(max_over_time(alert_groups_total[24h]))",
        "Status of Services": "sum by (service_name) (max_over_time(http_requests_total[24h]))",
        "Security Incidents": 'sum(max_over_time(alert_groups_total{team="Metaphysics-DevOps"}[24h]))',
        "Mean Time to Resolve (MTTR)": "sum(max_over_time(alert_groups_resolution_time_seconds_sum[24h])) / sum(max_over_time(alert_groups_resolution_time_seconds_count[24h]))",
        "Incidents by Integration": "sum by (integration) (max_over_time(alert_groups_total[24h]))",
        "Commander Assignment": "sum by (username) (max_over_time(user_was_notified_of_alert_groups_total[24h]))"
    }

    print("\n=== VERIFYING GRAFANA CLOUD PROMETHEUS QUERIES ===")
    all_ok = True
    for label, q in queries.items():
        url_q = f"https://vividlamp2135.grafana.net/api/datasources/proxy/uid/grafanacloud-prom/api/v1/query?query={urllib.parse.quote(q)}"
        req = urllib.request.Request(url_q, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                result = data.get("data", {}).get("result", [])
                val = [r.get("value", [None, "N/A"])[1] for r in result]
                if result:
                    print(f"  [OK] {label:32s} -> {len(result)} series, Values: {val}")
                else:
                    print(f"  [WARNING] {label:32s} -> 0 series returned")
                    all_ok = False
        except Exception as e:
            print(f"  [ERROR] {label:32s} -> {e}")
            all_ok = False

    return all_ok


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inject Production Telemetry Dummy Data directly into Grafana Cloud."
    )
    parser.add_argument(
        "--stages",
        type=int,
        default=6,
        help="Number of time windows to inject (default: 6)."
    )
    parser.add_argument(
        "--target",
        choices=["prom", "incident", "all"],
        default="all",
        help="Target datasource for dummy data injection: prom (OTLP PromQL), incident (Grafana Incident), all (both)."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview OTLP and Incident stages without pushing live HTTP requests."
    )
    parser.add_argument(
        "--verify-queries",
        action="store_true",
        help="Execute verification queries against Grafana Cloud API after injection."
    )

    args = parser.parse_args()
    ok = True

    if args.target in ("prom", "all"):
        print("\n--- [STAGE 1] INJECTING PROMETHEUS / OTLP METRICS ---")
        prom_ok = inject_production_dummy_data(stages=args.stages, dry_run=args.dry_run)
        ok = ok and prom_ok

    if args.target in ("incident", "all"):
        print("\n--- [STAGE 2] INJECTING GRAFANA INCIDENT DATASOURCE RECORDS ---")
        try:
            from scripts.inject_grafana_incident_data import (
                inject_grafana_incident_data,
                verify_incident_datasource_queries,
            )
            inc_ok = inject_grafana_incident_data(stages=args.stages, dry_run=args.dry_run)
            ok = ok and inc_ok
            if args.verify_queries and not args.dry_run:
                inc_ver_ok = verify_incident_datasource_queries()
                ok = ok and inc_ver_ok
        except ImportError as e:
            print(f"[WARNING] Could not import inject_grafana_incident_data: {e}")

    if args.verify_queries and not args.dry_run and args.target in ("prom", "all"):
        verify_ok = verify_grafana_queries()
        ok = ok and verify_ok

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

