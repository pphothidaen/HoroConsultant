#!/usr/bin/env python3
"""Verify the complete public production request path.

The checks deliberately cover static content, the public backend, and one
deterministic calculation. A 200 response alone is not sufficient evidence
that the public application works.
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
from typing import Any, Callable, Mapping

DEFAULT_VERCEL_GATEWAY_URL = "https://horo-consultant-psi.vercel.app"
DEFAULT_HF_STATIC_CDN_URL = "https://pphothidaen-horoconsultant-core-backend.hf.space"
DEFAULT_HF_BACKEND_URL = "https://horo-consultant-psi.vercel.app"


def _backend_from_space_id(space_id: str) -> str:
    """Derive an HF public space URL from a space id if available."""
    parts = space_id.strip().split("/")
    if len(parts) != 2:
        return ""
    user, repo = parts
    return f"https://{user.lower()}-{repo.lower().replace('_', '-').replace('.', '-')}.hf.space"


def _configured_url(value: str) -> str:
    """Return a usable configured URL, rejecting template placeholders."""
    normalized = value.strip().rstrip("/")
    lowered = normalized.lower()
    if (
        not normalized
        or "changeme" in lowered
        or "your_" in lowered
        or "${" in normalized
    ):
        return ""
    return normalized


def _backend_url_from_env(env: Mapping[str, str]) -> str:
    """Resolve backend URL from explicit config or space-id convention."""
    configured = _configured_url(env.get("HF_BACKEND_URL", ""))
    if configured:
        return configured

    space_url = _backend_from_space_id(env.get("HF_BACKEND_SPACE_ID", ""))
    if space_url:
        return _configured_url(space_url)

    return _configured_url(DEFAULT_HF_BACKEND_URL)


def _request(url: str, timeout: int) -> tuple[int, str, float]:
    """Execute one public GET request and return status, body, and latency."""
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "HoroConsultant-ProductionVerifier/2.0",
            "Accept": "application/json, text/html;q=0.9, */*;q=0.8",
        },
        method="GET",
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read().decode("utf-8", errors="replace"), (time.perf_counter() - started) * 1000
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode("utf-8", errors="replace"), (time.perf_counter() - started) * 1000
    except Exception as error:
        return 0, str(error), (time.perf_counter() - started) * 1000


def _is_health_response(body: str) -> bool:
    """Return whether the documented health response signals an operational app."""
    try:
        return str(json.loads(body).get("status", "")).lower() in {"ok", "healthy", "running", "alive", "up"}
    except json.JSONDecodeError:
        return False


def _is_html_response(body: str) -> bool:
    """Return whether a static UI response contains an HTML document."""
    lowered = body.lower()
    return "<html" in lowered or "<!doctype html" in lowered


def _is_ziwei_response(body: str) -> bool:
    """Return whether the gateway returned the expected deterministic API payload."""
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return False
    return (
        ("ming_gong_branch" in payload and "palaces" in payload)
        or ("pillars" in payload and "day_master" in payload)
        or ("palaces" in payload)
        or ("chart" in payload)
    )


def _static_candidates(static_url: str) -> list[str]:
    """Build the candidate static UI URLs for deployment variations."""
    base = static_url.rstrip("/")
    return [
        f"{base}/",
        f"{base}/index.html",
    ]


def _pick_first_healthy_url(urls: list[str], timeout: int, validator: Callable[[str], bool]) -> tuple[str, int, str, float, bool]:
    """Try multiple URLs and return the first successful match."""
    last_status = 0
    last_body = ""
    last_latency = 0.0
    for url in urls:
        status, body, latency_ms = _request(url, timeout)
        last_status = status
        last_body = body
        last_latency = latency_ms
        if status == 200 and validator(body):
            return url, status, body, latency_ms, True
    return urls[0], last_status, last_body, last_latency, False


def build_checks(
    environment: Mapping[str, str] | None = None,
    *,
    require_backend: bool = True,
) -> list[dict[str, Any]]:
    """Build checks for the active production architecture."""
    env = os.environ if environment is None else environment
    backend_url = _backend_url_from_env(env)
    static_space_id = env.get("HF_STATIC_SPACE_ID", "").strip()
    backend_space_id = env.get("HF_BACKEND_SPACE_ID", "").strip()
    if static_space_id and static_space_id == backend_space_id and backend_url:
        static_url = backend_url
    else:
        static_url = _configured_url(env.get("HF_STATIC_CDN_URL", DEFAULT_HF_STATIC_CDN_URL))
    if not static_url:
        raise ValueError("HF_STATIC_CDN_URL must be a valid URL")
    if require_backend and not backend_url:
        raise ValueError("HF_BACKEND_URL must be configured for a production deployment verification")

    checks: list[dict[str, Any]] = [
        {
            "name": "Hugging Face static UI",
            "urls": _static_candidates(static_url),
            "validator": _is_html_response,
        },
    ]
    if backend_url:
        checks.append(
            {
                "name": "Hugging Face Docker backend health",
                "url": f"{backend_url}/health",
                "validator": _is_health_response,
            }
        )
    if backend_url:
        checks.append(
            {
                "name": "Public backend deterministic API",
                "url": f"{backend_url}/api/v1/ziwei/calculate?year=1990&month=5&day=15&hour=14&gender=male",
                "validator": _is_ziwei_response,
            }
        )
    return checks


def run_verification(
    timeout: int = 15,
    verbose: bool = False,
    *,
    require_backend: bool = True,
    environment: Mapping[str, str] | None = None,
) -> tuple[bool, list[dict[str, Any]]]:
    """Run every check and return a success flag plus structured results."""
    checks = build_checks(environment, require_backend=require_backend)
    print("[INFO] HoroConsultant production path verification started")
    results: list[dict[str, Any]] = []
    for index, check in enumerate(checks, start=1):
        urls = check.get("urls")
        if urls:
            chosen_url, status, body, latency_ms, passed = _pick_first_healthy_url(urls, timeout, check["validator"])
        else:
            chosen_url, status, body, latency_ms = (
                check["url"],
                *_request(check["url"], timeout),
            )
            passed = status == 200 and check["validator"](body)
        result = {
            "target": check["name"],
            "url": chosen_url,
            "passed": passed,
            "status": status,
            "latency_ms": round(latency_ms, 1),
        }
        results.append(result)
        tag = "[OK]" if passed else "[ERROR]"
        print(f"{tag} [{index}/{len(checks)}] {check['name']}: HTTP {status} | {latency_ms:.0f}ms")
        if verbose and not passed:
            print(f"[INFO] Response snippet: {body[:300]}")

    success = all(result["passed"] for result in results)
    passed_count = sum(1 for result in results if result["passed"])
    print(f"[INFO] Production verification result: {passed_count}/{len(results)} checks passed")
    print("[OK] All production path checks passed" if success else "[ERROR] Production path verification failed")
    return success, results


def main() -> int:
    """Run the verifier from the command line."""
    parser = argparse.ArgumentParser(description="Verify the HoroConsultant public production request path")
    parser.add_argument("--timeout", type=int, default=15, help="HTTP timeout in seconds")
    parser.add_argument("--verbose", action="store_true", help="Show response snippets for failed checks")
    parser.add_argument("--allow-missing-backend", action="store_true", help="Do not require the public backend health check")
    parser.add_argument("--json-output", type=Path, help="Write structured verification output to this file")
    args = parser.parse_args()
    if args.timeout <= 0:
        print("[ERROR] --timeout must be a positive integer")
        return 2
    try:
        success, results = run_verification(args.timeout, args.verbose, require_backend=not args.allow_missing_backend)
    except ValueError as error:
        print(f"[ERROR] {error}")
        return 2
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(
            json.dumps({"success": success, "results": results}, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"[INFO] Verification report written to {args.json_output}")
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
