#!/usr/bin/env python3
"""
scripts/hermes_telemetry.py
============================
Hermes Agentic Loop Telemetry — emits OTLP metrics to Grafana Cloud.

Tracks per-iteration stats for the Plan->Act->Observe->Reflect loop:
  - hermes.loop.tokens      : token usage per loop iteration
  - hermes.loop.iterations  : iteration count per phase
  - hermes.loop.failover    : failover events (9router -> fallback)
  - hermes.loop.latency_ms  : loop iteration wall-clock latency

Usage (from shell):
  python3 scripts/hermes_telemetry.py --phase qa --status passed
  python3 scripts/hermes_telemetry.py --phase deploy --status failed --tokens 1200

Usage (from Python):
  from scripts.hermes_telemetry import emit_loop_metric
  emit_loop_metric(phase="dev", model="deepseek-v3", tokens_used=800)
"""

import argparse
import os
import time
from datetime import datetime, timezone

try:
    import httpx
    _HTTPX_AVAILABLE = True
except ImportError:
    _HTTPX_AVAILABLE = False


# ── Config (resolved from env) ────────────────────────────────────────────────
GRAFANA_ENDPOINT = os.getenv("GRAFANA_OTLP_ENDPOINT", "")
GRAFANA_USER_ID  = os.getenv("GRAFANA_USER_ID", "")
GRAFANA_API_KEY  = os.getenv("GRAFANA_API_KEY", "")
TELEMETRY_ON     = os.getenv("HERMES_TELEMETRY_ENABLED", "false").lower() == "true"

# Active router (resolved by hermes_sdlc_runner.sh and exported to env)
ACTIVE_ROUTER = (
    os.getenv("ROUTER_BASE_URL")
    or os.getenv("NINE_ROUTER_BASE_URL")
    or os.getenv("OPENAI_BASE_URL")
    or "gemini-direct"
)
ACCOUNT_ALIAS = (
    os.getenv("HERMES_ACCOUNT_ALIAS_RESOLVED")
    or os.getenv("ROUTER_ACCOUNT_ALIAS")
    or os.getenv("HERMES_ACCOUNT_ALIAS")
    or os.getenv("NINE_ROUTER_ACCOUNT_ALIAS")
    or "agy1"
)


def _now_nano() -> str:
    """Return current UTC time as Unix nanoseconds string (OTLP requirement)."""
    return str(int(datetime.now(tz=timezone.utc).timestamp() * 1e9))


def emit_loop_metric(
    phase: str,
    model: str = "unknown",
    tokens_used: int = 0,
    latency_ms: float = 0.0,
    iteration: int = 1,
    failover: bool = False,
    status: str = "passed",
) -> bool:
    """
    Emit OTLP metric payload to Grafana Cloud endpoint.

    Args:
        phase:       SDLC phase (dev / qa / deploy / sync)
        model:       LLM model used in this iteration
        tokens_used: Approximate token count for this iteration
        latency_ms:  Wall-clock latency in milliseconds
        iteration:   Loop iteration number (1-indexed)
        failover:    True if 9router was unavailable and fallback was used
        status:      "passed" | "failed" | "retried"

    Returns:
        True if metric was accepted (HTTP 2xx), False otherwise.
    """
    if not TELEMETRY_ON:
        print(f"[INFO] [HERMES] Telemetry disabled — skipping metric (phase={phase})")
        return False

    if not _HTTPX_AVAILABLE:
        print("[WARNING] [HERMES] httpx not installed — telemetry skipped")
        return False

    if not GRAFANA_ENDPOINT or not GRAFANA_API_KEY:
        print("[WARNING] [HERMES] GRAFANA_OTLP_ENDPOINT or GRAFANA_API_KEY not set — telemetry skipped")
        return False

    ts_nano = _now_nano()

    def _attr(key: str, value) -> dict:
        if isinstance(value, bool):
            return {"key": key, "value": {"boolValue": value}}
        if isinstance(value, int):
            return {"key": key, "value": {"intValue": value}}
        if isinstance(value, float):
            return {"key": key, "value": {"doubleValue": value}}
        return {"key": key, "value": {"stringValue": str(value)}}

    common_attrs = [
        _attr("phase",         phase),
        _attr("model",         model),
        _attr("codex_fallback_model", os.getenv("HERMES_CODEX_FALLBACK_MODEL", "gpt-5.3-codex-spark high")),
        _attr("failover",      failover),
        _attr("status",        status),
        _attr("router",        ACTIVE_ROUTER),
        _attr("account_alias", ACCOUNT_ALIAS),
    ]

    def _sum_metric(name: str, value: int, unit: str = "1") -> dict:
        return {
            "name": name,
            "unit": unit,
            "sum": {
                "dataPoints": [{
                    "attributes": common_attrs,
                    "asInt": value,
                    "timeUnixNano": ts_nano,
                }],
                "aggregationTemporality": 2,  # AGGREGATION_TEMPORALITY_CUMULATIVE
                "isMonotonic": True,
            },
        }

    def _gauge_metric(name: str, value: float, unit: str = "ms") -> dict:
        return {
            "name": name,
            "unit": unit,
            "gauge": {
                "dataPoints": [{
                    "attributes": common_attrs,
                    "asDouble": value,
                    "timeUnixNano": ts_nano,
                }],
            },
        }

    payload = {
        "resourceMetrics": [{
            "resource": {
                "attributes": [
                    _attr("service.name",    "horoconsultant-hermes"),
                    _attr("service.version", "1.0.0"),
                    _attr("deployment.env",  os.getenv("APP_ENV", "development")),
                ]
            },
            "scopeMetrics": [{
                "scope": {"name": "hermes.execution.engine", "version": "1.0.0"},
                "metrics": [
                    _sum_metric("hermes.loop.tokens",     tokens_used),
                    _sum_metric("hermes.loop.iterations", iteration),
                    _sum_metric("hermes.loop.failover",   int(failover)),
                    _gauge_metric("hermes.loop.latency_ms", latency_ms),
                ],
            }],
        }]
    }

    headers = {
        "Authorization": f"Bearer {GRAFANA_USER_ID}:{GRAFANA_API_KEY}",
        "Content-Type":  "application/json",
    }

    try:
        resp = httpx.post(
            f"{GRAFANA_ENDPOINT}/v1/metrics",
            json=payload,
            headers=headers,
            timeout=5.0,
        )
        if resp.status_code < 300:
            print(f"[OK]   [HERMES] Telemetry emitted: phase={phase} tokens={tokens_used} latency={latency_ms:.0f}ms failover={failover}")
            return True
        else:
            print(f"[WARNING] [HERMES] Grafana returned HTTP {resp.status_code}: {resp.text[:120]}")
            return False
    except Exception as exc:  # noqa: BLE001
        print(f"[WARNING] [HERMES] Telemetry emit failed: {exc}")
        return False


# ── CLI entrypoint ─────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Hermes Agentic Loop Telemetry — emit OTLP metrics to Grafana Cloud"
    )
    parser.add_argument("--phase",     required=True, help="SDLC phase: dev|qa|deploy|sync")
    parser.add_argument("--status",    default="passed", help="passed|failed|retried")
    parser.add_argument(
        "--model",
        default=(
            os.getenv("HERMES_ROUTER_MODEL")
            or os.getenv("NINE_ROUTER_DEVELOPER_MODEL", "unknown")
            or "unknown"
        ),
    )
    parser.add_argument("--tokens",    type=int,   default=0)
    parser.add_argument("--latency",   type=float, default=0.0, help="Latency in ms")
    parser.add_argument("--iteration", type=int,   default=1)
    parser.add_argument("--failover",  action="store_true")
    args = parser.parse_args()

    emit_loop_metric(
        phase=args.phase,
        model=args.model,
        tokens_used=args.tokens,
        latency_ms=args.latency,
        iteration=args.iteration,
        failover=args.failover,
        status=args.status,
    )


if __name__ == "__main__":
    main()
