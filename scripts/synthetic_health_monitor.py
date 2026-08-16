#!/usr/bin/env python3
"""Run health checks and incident notifications for production services.

The monitor is intentionally dependency-light so it can run in GitHub Actions,
a container, or a long-running host.  It checks the public static UI, the
Vercel gateway, and the Hugging Face Docker backend.

Usage:
    python3 scripts/synthetic_health_monitor.py --once
    python3 scripts/synthetic_health_monitor.py --daemon --interval 300
    python3 scripts/synthetic_health_monitor.py --dry-run

Set one or more of HEALTH_ALERT_WEBHOOK_URL, SLACK_WEBHOOK_URL,
DISCORD_WEBHOOK_URL, or TELEGRAM_BOT_TOKEN plus TELEGRAM_CHAT_ID to receive a
notification when any target is degraded.  Grafana OTLP metric export remains
optional and is activated by GRAFANA_OTLP_ENDPOINT (or GRAFANA_CLOUD_URL) and
a Grafana token.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Mapping

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_VERCEL_GATEWAY_URL = "https://horo-consultant-psi.vercel.app"
DEFAULT_HF_STATIC_CDN_URL = "https://pphothidaen-horoconsultant-core-backend.static.hf.space"
DEFAULT_HF_BACKEND_URL = "https://horo-consultant-psi.vercel.app"
DEFAULT_PING_INTERVAL_SECONDS = 300
DEFAULT_MAX_LATENCY_MS = float(os.getenv("MAX_LATENCY_THRESHOLD_MS", "5000.0"))


def _base_url(value: str) -> str:
    """Normalize a usable URL and ignore template placeholders."""
    normalized = value.strip().rstrip("/")
    if "changeme" in normalized.lower() or "your_" in normalized.lower():
        return ""
    return normalized


def build_health_targets(
    environment: Mapping[str, str] | None = None,
    *,
    require_backend: bool = True,
) -> list[dict[str, Any]]:
    """Build the active production targets after environment loading.

    Azure ingress is unavailable, so the public FastAPI backend is deployed to
    a dedicated Hugging Face Docker Space and is required in production.
    """
    env = os.environ if environment is None else environment
    hf_static_url = _base_url(env.get("HF_STATIC_CDN_URL", DEFAULT_HF_STATIC_CDN_URL))
    backend_url = _base_url(env.get("HF_BACKEND_URL", DEFAULT_HF_BACKEND_URL))

    if not hf_static_url:
        raise ValueError("HF_STATIC_CDN_URL must not be empty")
    if require_backend and not backend_url:
        raise ValueError("HF_BACKEND_URL is required for this monitor run")

    targets: list[dict[str, Any]] = [
        {
            "name": "Hugging Face Static UI /index.html",
            "url": f"{hf_static_url}/index.html",
            "critical": True,
        },
    ]
    if backend_url:
        targets.append(
            {
                "name": "Hugging Face Docker Backend /health",
                "url": f"{backend_url}/health",
                "critical": True,
            }
        )
    return targets


def _ping(url: str, timeout: int = 10) -> tuple[int, float, str, str | None]:
    """Send a GET request and return status code, latency, body, and error."""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "HoroConsultant-SyntheticMonitor/2.0",
            "Accept": "application/json, text/html;q=0.9, */*;q=0.8",
        },
        method="GET",
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            return response.status, (time.perf_counter() - started) * 1000, body, None
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        return error.code, (time.perf_counter() - started) * 1000, body, f"HTTP {error.code}: {error.reason}"
    except Exception as error:
        return 0, (time.perf_counter() - started) * 1000, "", str(error)


def _target_response_is_valid(target_name: str, body: str) -> bool:
    """Require meaningful content, not only an HTTP 200 status."""
    if "Static UI" in target_name:
        lowered = body.lower()
        return "<html" in lowered or "<!doctype html" in lowered
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return False
    return str(payload.get("status", "")).lower() in {"ok", "healthy", "running", "alive", "up"}


def _post_json(url: str, payload: dict[str, Any], timeout: int = 10) -> tuple[bool, str]:
    """Post JSON to a notification endpoint without exposing credential data."""
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "HoroConsultant-SyntheticMonitor/2.0"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response.read()
            return response.status in (200, 201, 202, 204), f"HTTP {response.status}"
    except urllib.error.HTTPError as error:
        error.read()
        return False, f"HTTP {error.code}"
    except Exception as error:
        return False, str(error)


def notify_health_degradation(results: list[dict[str, Any]], environment: Mapping[str, str] | None = None) -> bool:
    """Send one compact incident notification to every configured channel."""
    env = os.environ if environment is None else environment
    degraded = [result for result in results if not result["healthy"]]
    if not degraded:
        return True

    lines = ["[ALERT] HoroConsultant production health degradation detected."]
    for result in degraded:
        severity = "CRITICAL" if result["critical"] else "WARNING"
        lines.append(
            f"- {severity}: {result['target']} returned HTTP {result['status']} "
            f"in {result['latency_ms']:.0f}ms"
        )
    message = "\n".join(lines)
    attempts: list[tuple[str, bool, str]] = []

    generic_webhook = env.get("HEALTH_ALERT_WEBHOOK_URL", "").strip()
    if generic_webhook:
        ok, detail = _post_json(generic_webhook, {"text": message})
        attempts.append(("generic webhook", ok, detail))

    slack_webhook = env.get("SLACK_WEBHOOK_URL", "").strip()
    if slack_webhook:
        ok, detail = _post_json(slack_webhook, {"text": message})
        attempts.append(("Slack", ok, detail))

    discord_webhook = env.get("DISCORD_WEBHOOK_URL", "").strip()
    if discord_webhook:
        ok, detail = _post_json(discord_webhook, {"content": message})
        attempts.append(("Discord", ok, detail))

    telegram_token = env.get("TELEGRAM_BOT_TOKEN", "").strip()
    telegram_chat_id = env.get("TELEGRAM_CHAT_ID", "").strip()
    if telegram_token and telegram_chat_id:
        telegram_url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
        ok, detail = _post_json(telegram_url, {"chat_id": telegram_chat_id, "text": message})
        attempts.append(("Telegram", ok, detail))
    elif telegram_token or telegram_chat_id:
        print("[WARNING] Telegram alerting is partially configured; both token and chat ID are required")

    if not attempts:
        print("[WARNING] No incident notification channel is configured")
        return False

    all_delivered = True
    for channel, delivered, detail in attempts:
        if delivered:
            print(f"[OK] Incident notification delivered to {channel}: {detail}")
        else:
            print(f"[ERROR] Incident notification failed for {channel}: {detail}")
            all_delivered = False
    return all_delivered


def _push_alert_metric_to_grafana(
    target_name: str,
    status_code: int,
    latency_ms: float,
    is_healthy: bool,
    environment: Mapping[str, str] | None = None,
) -> None:
    """Push a synthetic-health metric to Grafana OTLP when configured."""
    env = os.environ if environment is None else environment
    grafana_url = env.get("GRAFANA_CLOUD_URL", env.get("GRAFANA_URL", "")).strip()
    otlp_endpoint = env.get("GRAFANA_OTLP_ENDPOINT", "").strip()
    user_id = env.get("GRAFANA_USER_ID", "").strip()
    api_key = env.get(
        "GRAFANA_API_KEY",
        env.get("GRAFANA_SERVICE_ACCOUNT_TOKEN", env.get("GRAFANA_TOKEN", "")),
    ).strip()
    if not api_key or not (grafana_url or otlp_endpoint):
        return

    if otlp_endpoint:
        push_url = otlp_endpoint.rstrip("/")
        if not push_url.endswith("/v1/metrics"):
            push_url = f"{push_url}/v1/metrics"
    else:
        push_url = urllib.parse.urljoin(f"{grafana_url.rstrip('/')}/", "otlp/v1/metrics")

    now_nano = str(int(time.time() * 1_000_000_000))
    target_label = target_name.replace(" ", "_").lower()
    attributes = [{"key": "target", "value": {"stringValue": target_label}}]
    payload: dict[str, Any] = {
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
                        "scope": {"name": "synthetic_health_monitor", "version": "2.0.0"},
                        "metrics": [
                            {
                                "name": "synthetic_health_status",
                                "gauge": {
                                    "dataPoints": [{"timeUnixNano": now_nano, "asDouble": float(is_healthy), "attributes": attributes}]
                                },
                            },
                            {
                                "name": "synthetic_health_latency_ms",
                                "gauge": {
                                    "dataPoints": [{"timeUnixNano": now_nano, "asDouble": latency_ms, "attributes": attributes}]
                                },
                            },
                            {
                                "name": "synthetic_health_http_status",
                                "gauge": {
                                    "dataPoints": [{"timeUnixNano": now_nano, "asDouble": float(status_code), "attributes": attributes}]
                                },
                            },
                        ],
                    }
                ],
            }
        ]
    }

    headers = {"Content-Type": "application/json", "User-Agent": "HoroConsultant-SyntheticMonitor/2.0"}
    if user_id and "your_grafana" not in user_id.lower():
        credentials = base64.b64encode(f"{user_id}:{api_key}".encode("utf-8")).decode("ascii")
        headers["Authorization"] = f"Basic {credentials}"
    else:
        headers["Authorization"] = f"Bearer {api_key}"

    request = urllib.request.Request(
        push_url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            response.read()
            if response.status in (200, 202, 204):
                print(f"[OK] Grafana OTLP push for {target_name}: HTTP {response.status}")
            else:
                print(f"[WARNING] Grafana OTLP push for {target_name}: HTTP {response.status}")
    except Exception as error:
        print(f"[WARNING] Grafana OTLP push failed for {target_name}: {error}")


def _write_report(path: Path, results: list[dict[str, Any]], all_critical_healthy: bool) -> None:
    """Persist a machine-readable result that can be uploaded as a CI artifact."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "all_critical_healthy": all_critical_healthy,
        "healthy_count": sum(1 for result in results if result["healthy"]),
        "target_count": len(results),
        "results": results,
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"[INFO] Synthetic health report written to {path}")


def run_ping_cycle(
    targets: list[dict[str, Any]],
    *,
    timeout: int = 10,
    max_latency_ms: float = DEFAULT_MAX_LATENCY_MS,
    report_path: Path | None = None,
    environment: Mapping[str, str] | None = None,
) -> bool:
    """Check every target, export metrics, notify on degradation, and return health."""
    print(f"[INFO] Synthetic health ping cycle started at {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
    results: list[dict[str, Any]] = []
    all_critical_healthy = True

    for target in targets:
        status, latency_ms, body, error = _ping(target["url"], timeout=timeout)
        healthy = status == 200 and _target_response_is_valid(target["name"], body)
        if status == 200 and not healthy and not error:
            error = "HTTP 200 response did not contain a valid health/UI payload"
        
        latency_degraded = latency_ms > max_latency_ms
        result = {
            "target": target["name"],
            "url": target["url"],
            "status": status,
            "latency_ms": round(latency_ms, 1),
            "healthy": healthy,
            "latency_degraded": latency_degraded,
            "critical": bool(target.get("critical", True)),
            "error": error,
        }
        results.append(result)
        if healthy:
            if latency_degraded:
                print(f"[WARNING] {target['name']}: HTTP {status} | {latency_ms:.0f}ms (High Latency > {max_latency_ms:.0f}ms SLA)")
            else:
                print(f"[OK] {target['name']}: HTTP {status} | {latency_ms:.0f}ms")
        else:
            tag = "[ERROR]" if result["critical"] else "[WARNING]"
            detail = f" | {error}" if error else ""
            print(f"{tag} {target['name']}: HTTP {status} | {latency_ms:.0f}ms{detail}")
            if result["critical"]:
                all_critical_healthy = False
        _push_alert_metric_to_grafana(target["name"], status, latency_ms, healthy, environment)

    if report_path:
        _write_report(report_path, results, all_critical_healthy)

    healthy_count = sum(1 for result in results if result["healthy"])
    print(f"[INFO] Cycle complete: {healthy_count}/{len(results)} targets healthy")
    if all_critical_healthy:
        print("[OK] All critical health targets are operational")
    else:
        print("[ERROR] One or more critical health targets are degraded")
        notify_health_degradation(results, environment)
    return all_critical_healthy


def _load_local_environment() -> None:
    """Load .env for local use before target URLs are derived."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        load_dotenv(env_file)


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(description="Synthetic production health monitor for HoroConsultant")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--once", action="store_true", help="Run one health cycle and exit")
    mode.add_argument("--daemon", action="store_true", help="Run health cycles continuously")
    parser.add_argument("--interval", type=int, default=DEFAULT_PING_INTERVAL_SECONDS, help="Seconds between daemon cycles")
    parser.add_argument("--timeout", type=int, default=10, help="Per-target HTTP timeout in seconds")
    parser.add_argument("--max-latency-ms", type=float, default=DEFAULT_MAX_LATENCY_MS, help="Max latency SLA threshold in ms before warning (default 5000)")
    parser.add_argument("--allow-missing-backend", action="store_true", help="Do not require HF_BACKEND_URL")
    parser.add_argument("--json-output", type=Path, help="Write the latest health report as JSON")
    parser.add_argument("--dry-run", action="store_true", help="Print resolved targets without network requests")
    return parser


def main() -> int:
    """Run the requested monitor mode and return an appropriate process status."""
    _load_local_environment()
    args = build_parser().parse_args()
    if args.interval <= 0 or args.timeout <= 0:
        print("[ERROR] --interval and --timeout must be positive integers")
        return 2
    try:
        targets = build_health_targets(require_backend=not args.allow_missing_backend)
    except ValueError as error:
        print(f"[ERROR] {error}")
        return 2

    if args.dry_run:
        print("[INFO] Dry-run mode - resolved production health targets:")
        for target in targets:
            print(f"[INFO] {target['name']} | {target['url']} | critical={target['critical']}")
        print("[OK] Dry-run complete - no HTTP requests sent")
        return 0

    if not args.daemon:
        return 0 if run_ping_cycle(targets, timeout=args.timeout, max_latency_ms=args.max_latency_ms, report_path=args.json_output) else 1

    print(f"[INFO] Synthetic health monitor daemon started with interval={args.interval}s")
    try:
        while True:
            run_ping_cycle(targets, timeout=args.timeout, max_latency_ms=args.max_latency_ms, report_path=args.json_output)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("[INFO] Synthetic health monitor stopped")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
