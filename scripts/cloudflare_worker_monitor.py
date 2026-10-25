#!/usr/bin/env python3
"""Synthetic health monitor for Cloudflare Worker production endpoint.

Checks the Cloudflare Worker at https://horoconsultant-production.pansakorn.workers.dev
with focus on /health endpoint and D1 database connectivity.

Usage:
    python3 scripts/cloudflare_worker_monitor.py --once
    python3 scripts/cloudflare_worker_monitor.py --daemon --interval 300
    python3 scripts/cloudflare_worker_monitor.py --dry-run

Set one or more of HEALTH_ALERT_WEBHOOK_URL, SLACK_WEBHOOK_URL,
DISCORD_WEBHOOK_URL, or TELEGRAM_BOT_TOKEN plus TELEGRAM_CHAT_ID to receive a
notification when any target is degraded.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Mapping

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_WORKER_URL = "https://horoconsultant-production.pansakorn.workers.dev"
DEFAULT_PING_INTERVAL_SECONDS = 300
DEFAULT_MAX_LATENCY_MS = float(os.getenv("MAX_LATENCY_THRESHOLD_MS", "10000.0"))  # 10s for cold starts


def _base_url(value: str) -> str:
    """Normalize a usable URL and ignore template placeholders."""
    normalized = value.strip().rstrip("/")
    if "changeme" in normalized.lower() or "your_" in normalized.lower():
        return ""
    return normalized


def _worker_url(env: Mapping[str, str]) -> str:
    """Resolve the Cloudflare Worker URL from environment."""
    configured = _base_url(env.get("CLOUDFLARE_WORKER_URL", ""))
    if configured:
        return configured
    if "CLOUDFLARE_WORKER_URL" in env:
        return ""
    return DEFAULT_WORKER_URL


def build_health_targets(
    environment: Mapping[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Build the active production targets for Cloudflare Worker."""
    env = os.environ if environment is None else environment
    worker_url = _worker_url(env)

    if not worker_url:
        raise ValueError("CLOUDFLARE_WORKER_URL must not be empty")

    targets: list[dict[str, Any]] = [
        {
            "name": "Cloudflare Worker /health",
            "url": f"{worker_url}/health",
            "critical": True,
            "expected_status": {"service": "Computational Metaphysics Engine", "status": "ok"},
        },
        {
            "name": "Cloudflare Worker /metrics",
            "url": f"{worker_url}/metrics",
            "critical": False,  # Optional metrics endpoint
        },
    ]
    return targets


def _ping(url: str, timeout: int = 15, retries: int = 2) -> tuple[int, float, str, str | None]:
    """Send a GET request and return status code, latency, body, and error with automatic retry on transient failure."""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "HoroConsultant-WorkerMonitor/1.0",
            "Accept": "application/json, text/html;q=0.9, */*;q=0.8",
        },
        method="GET",
    )
    started = time.perf_counter()
    last_error: str | None = None
    attempt_count = max(1, retries)
    for attempt in range(1, attempt_count + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                body = response.read().decode("utf-8", errors="replace")
                return response.status, (time.perf_counter() - started) * 1000, body, None
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            return error.code, (time.perf_counter() - started) * 1000, body, f"HTTP {error.code}: {error.reason}"
        except Exception as error:
            last_error = str(error)
            if attempt < attempt_count:
                time.sleep(2)
                continue
            return 0, (time.perf_counter() - started) * 1000, "", last_error
    return 0, (time.perf_counter() - started) * 1000, "", last_error


def _target_response_is_valid(target_name: str, body: str, expected: dict | None = None) -> bool:
    """Require meaningful content, not only an HTTP 200 status."""
    lowered_target = target_name.lower()

    if "/health" in lowered_target:
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            return False
        # Check for expected structure
        if expected:
            return all(
                str(payload.get(k, "")).lower() == str(v).lower()
                for k, v in expected.items()
            )
        # Fallback: check for generic healthy status
        return str(payload.get("status", "")).lower() in {"ok", "healthy", "running", "alive", "up"}

    if "/metrics" in lowered_target:
        # Metrics endpoint - accept any valid response (Prometheus format or JSON)
        return bool(body.strip())

    return bool(body.strip())


def _post_json(url: str, payload: dict[str, Any], timeout: int = 10) -> tuple[bool, str]:
    """Post JSON to a notification endpoint without exposing credential data."""
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "HoroConsultant-WorkerMonitor/1.0"},
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

    lines = ["[ALERT] Cloudflare Worker production health degradation detected."]
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
    print(f"[INFO] Cloudflare Worker health report written to {path}")


def run_ping_cycle(
    targets: list[dict[str, Any]],
    *,
    timeout: int = 10,
    max_latency_ms: float = DEFAULT_MAX_LATENCY_MS,
    report_path: Path | None = None,
    environment: Mapping[str, str] | None = None,
) -> bool:
    """Check every target, export metrics, notify on degradation, and return health."""
    print(f"[INFO] Cloudflare Worker health ping cycle started at {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
    results: list[dict[str, Any]] = []
    all_critical_healthy = True

    for target in targets:
        target_name = target["name"]
        target_url = target["url"]
        expected = target.get("expected_status")

        status, latency_ms, body, error = _ping(target_url, timeout=timeout)

        healthy = False
        if error is None and _target_response_is_valid(target_name, body, expected):
            healthy = True
            error = None
        elif status == 200 and not healthy and error is None:
            error = "HTTP 200 response did not contain a valid health payload"

        latency_degraded = latency_ms > max_latency_ms

        result = {
            "target": target["name"],
            "url": target_url,
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
                print(f"[WARNING] {target_name}: HTTP {status} | {latency_ms:.0f}ms (High Latency > {max_latency_ms:.0f}ms SLA)")
            else:
                print(f"[OK] {target_name}: HTTP {status} | {latency_ms:.0f}ms")
        else:
            tag = "[ERROR]" if result["critical"] else "[WARNING]"
            detail = f" | {error}" if error else ""
            print(f"{tag} {target_name}: HTTP {status} | {latency_ms:.0f}ms{detail}")
            if result["critical"]:
                all_critical_healthy = False

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


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(description="Synthetic health monitor for Cloudflare Worker")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--once", action="store_true", help="Run one health cycle and exit")
    mode.add_argument("--daemon", action="store_true", help="Run health cycles continuously")
    parser.add_argument("--interval", type=int, default=DEFAULT_PING_INTERVAL_SECONDS, help="Seconds between daemon cycles")
    parser.add_argument("--timeout", type=int, default=15, help="Per-target HTTP timeout in seconds (default 15)")
    parser.add_argument("--max-latency-ms", type=float, default=DEFAULT_MAX_LATENCY_MS, help="Max latency SLA threshold in ms before warning (default 10000)")
    parser.add_argument("--json-output", type=Path, help="Write the latest health report as JSON")
    parser.add_argument("--dry-run", action="store_true", help="Print resolved targets without network requests")
    return parser


def main() -> int:
    """Run the requested monitor mode and return an appropriate process status."""
    args = build_parser().parse_args()
    if args.interval <= 0 or args.timeout <= 0:
        print("[ERROR] --interval and --timeout must be positive integers")
        return 2
    try:
        targets = build_health_targets()
    except ValueError as error:
        print(f"[ERROR] {error}")
        return 2

    if args.dry_run:
        print("[INFO] Dry-run mode - resolved Cloudflare Worker health targets:")
        for target in targets:
            print(f"[INFO] {target['name']} | {target['url']} | critical={target['critical']}")
        print("[OK] Dry-run complete - no HTTP requests sent")
        return 0

    if not args.daemon:
        return 0 if run_ping_cycle(targets, timeout=args.timeout, max_latency_ms=args.max_latency_ms, report_path=args.json_output) else 1

    print(f"[INFO] Cloudflare Worker monitor daemon started with interval={args.interval}s")
    try:
        while True:
            run_ping_cycle(targets, timeout=args.timeout, max_latency_ms=args.max_latency_ms, report_path=args.json_output)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("[INFO] Cloudflare Worker monitor stopped")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())