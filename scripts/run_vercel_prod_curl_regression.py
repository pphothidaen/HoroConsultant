"""Read-only HTTP regression for the Vercel UI and its backend gateway.

The UI target is the canonical Vercel deployment. Its same-origin API gateway
forwards to the separately identified Hugging Face Docker backend. The command
is offline by default; ``--live`` is required before any request is sent.
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import urlsplit

CANONICAL_VERCEL_UI_URL = "https://horo-consultant-psi.vercel.app"
CANONICAL_HF_DOCKER_BACKEND_URL = (
    "https://pphothidaen-horoconsultant-core-backend.hf.space"
)
DEFAULT_BASE_URL = CANONICAL_VERCEL_UI_URL
ORIGIN = CANONICAL_VERCEL_UI_URL
DEFAULT_TIMEOUT_SECONDS = 15
DEFAULT_RETRIES = 0

BROWSER_HEADERS = {
    "accept": "application/json",
    "cache-control": "no-cache",
    "origin": ORIGIN,
    "pragma": "no-cache",
    "referer": f"{ORIGIN}/",
    "user-agent": "HoroConsultant-UI-Diagnostics/1.0",
}


def _require_canonical_https_url(value: str, expected: str, label: str) -> str:
    candidate = value.strip().rstrip("/")
    parsed = urlsplit(candidate)
    if (
        candidate != expected
        or parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(f"{label} must be the canonical HTTPS target")
    return candidate


def _empty_result(error_class: str, latency_ms: float = 0.0) -> dict[str, Any]:
    return {
        "status": 0,
        "headers": {},
        "body_text": "",
        "body_json": None,
        "latency_ms": round(latency_ms, 1),
        "error": error_class,
    }


def _do_request(
    url: str,
    method: str = "GET",
    body: bytes | None = None,
    extra_headers: dict[str, str] | None = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    retries: int = DEFAULT_RETRIES,
) -> dict[str, Any]:
    """Make one bounded request without exposing response bodies in output."""
    headers = {**BROWSER_HEADERS, **(extra_headers or {})}
    for attempt in range(retries + 1):
        request = urllib.request.Request(url, method=method, headers=headers, data=body)
        started = time.monotonic()
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                body_text = response.read().decode("utf-8", errors="replace")
                try:
                    body_json = json.loads(body_text)
                except json.JSONDecodeError:
                    body_json = None
                return {
                    "status": response.status,
                    "headers": dict(response.headers),
                    "body_text": "[REDACTED]" if body_text else "",
                    "body_json": body_json,
                    "latency_ms": round((time.monotonic() - started) * 1000, 1),
                    "error": None,
                }
        except urllib.error.HTTPError as exc:
            return {
                "status": exc.code,
                "headers": dict(exc.headers),
                "body_text": "",
                "body_json": None,
                "latency_ms": round((time.monotonic() - started) * 1000, 1),
                "error": "HTTP_ERROR",
            }
        except (OSError, TimeoutError, urllib.error.URLError):
            latency_ms = (time.monotonic() - started) * 1000
            if attempt < retries:
                continue
            return _empty_result("NETWORK_ERROR", latency_ms)
    return _empty_result("NETWORK_ERROR")


def _header(result: dict[str, Any], name: str) -> str:
    return {key.lower(): value for key, value in result["headers"].items()}.get(
        name.lower(), ""
    ).strip()


def _check_cors(result: dict[str, Any], expected_origin: str = ORIGIN) -> bool:
    """Require the exact canonical Vercel origin in the CORS response."""
    return _header(result, "access-control-allow-origin") == expected_origin


def _print_result(
    name: str, passed: bool, result: dict[str, Any], details: str
) -> None:
    tag = "[OK]" if passed else "[ERROR]"
    print(
        f"{tag} {name}: http={result['status']} "
        f"latency_ms={result['latency_ms']} {details}"
    )


def run_regression(
    base_url: str,
    timeout_seconds: int,
    retries: int,
    *,
    backend_url: str = CANONICAL_HF_DOCKER_BACKEND_URL,
) -> int:
    """Run three read-only gateway checks and return zero only when all pass."""
    base_url = _require_canonical_https_url(base_url, CANONICAL_VERCEL_UI_URL, "UI URL")
    backend_url = _require_canonical_https_url(
        backend_url,
        CANONICAL_HF_DOCKER_BACKEND_URL,
        "Backend URL",
    )
    if not 1 <= timeout_seconds <= 60:
        raise ValueError("timeout must be between 1 and 60 seconds")
    if not 0 <= retries <= 2:
        raise ValueError("retries must be between 0 and 2")
    print("[INFO] Vercel UI HTTP regression")
    print(f"[INFO] UI target: {base_url}")
    print(f"[INFO] Backend target: {backend_url}")
    results: list[dict[str, Any]] = []

    health = _do_request(
        f"{base_url}/health",
        timeout_seconds=timeout_seconds,
        retries=retries,
    )
    deploy_sha_present = bool(_header(health, "x-deploy-sha"))
    health_passed = (
        health["status"] == 200
        and isinstance(health["body_json"], dict)
        and health["body_json"].get("status") == "ok"
        and deploy_sha_present
        and _check_cors(health, base_url)
    )
    _print_result(
        "GET /health",
        health_passed,
        health,
        f"cors={str(_check_cors(health, base_url)).lower()} "
        f"deploy_sha_present={str(deploy_sha_present).lower()}",
    )
    results.append({"test": "GET /health", "passed": health_passed})

    endpoint = f"{base_url}/api/v1/bazi/interpret"
    preflight = _do_request(
        endpoint,
        "OPTIONS",
        extra_headers={
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
        timeout_seconds=timeout_seconds,
        retries=retries,
    )
    methods_present = bool(_header(preflight, "access-control-allow-methods"))
    preflight_passed = (
        preflight["status"] in {200, 204}
        and _check_cors(preflight, base_url)
        and methods_present
    )
    _print_result(
        "OPTIONS /api/v1/bazi/interpret",
        preflight_passed,
        preflight,
        f"cors={str(_check_cors(preflight, base_url)).lower()} "
        f"methods_present={str(methods_present).lower()}",
    )
    results.append(
        {"test": "OPTIONS /api/v1/bazi/interpret", "passed": preflight_passed}
    )

    payload = json.dumps(
        {
            "birth_datetime": "1990-05-15 14:30:00",
            "longitude": 100.493,
            "utc_offset_hours": 7,
            "unknown_hour": False,
            "enable_validation": True,
            "query": "Analyze Day Master strength and supportive career directions.",
        },
        ensure_ascii=True,
    ).encode("utf-8")
    interpretation = _do_request(
        endpoint,
        "POST",
        body=payload,
        extra_headers={"content-type": "application/json"},
        timeout_seconds=timeout_seconds,
        retries=retries,
    )
    response_json = interpretation["body_json"] or {}
    has_chart = isinstance(response_json.get("chart"), dict)
    has_interpretation = bool(response_json.get("interpretation"))
    ai_source_present = bool(_header(interpretation, "x-ai-source"))
    ai_model_present = bool(_header(interpretation, "x-ai-model"))
    interpretation_passed = (
        interpretation["status"] == 200
        and has_chart
        and has_interpretation
        and ai_source_present
        and ai_model_present
        and _check_cors(interpretation, base_url)
    )
    _print_result(
        "POST /api/v1/bazi/interpret",
        interpretation_passed,
        interpretation,
        f"cors={str(_check_cors(interpretation, base_url)).lower()} "
        f"chart={str(has_chart).lower()} interpretation={str(has_interpretation).lower()} "
        f"ai_metadata={str(ai_source_present and ai_model_present).lower()}",
    )
    results.append(
        {"test": "POST /api/v1/bazi/interpret", "passed": interpretation_passed}
    )

    passed_count = sum(1 for result in results if result["passed"])
    all_passed = passed_count == len(results)
    print(f"[INFO] Results: {passed_count}/{len(results)} passed")
    print(
        "[OK] HTTP regression passed"
        if all_passed
        else "[ERROR] HTTP regression failed"
    )
    return 0 if all_passed else 1


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only HTTP regression for the Vercel UI gateway"
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--live", action="store_true", help="Enable live read-only requests"
    )
    mode.add_argument(
        "--dry-run", action="store_true", help="Validate the offline plan"
    )
    parser.add_argument(
        "--ui-url", "--url", dest="ui_url", default=CANONICAL_VERCEL_UI_URL
    )
    parser.add_argument("--backend-url", default=CANONICAL_HF_DOCKER_BACKEND_URL)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--retries", type=int, default=DEFAULT_RETRIES)
    parser.add_argument(
        "--use-python",
        action="store_true",
        help="Compatibility flag; Python is the deterministic implementation",
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        ui_url = _require_canonical_https_url(
            args.ui_url, CANONICAL_VERCEL_UI_URL, "UI URL"
        )
        backend_url = _require_canonical_https_url(
            args.backend_url,
            CANONICAL_HF_DOCKER_BACKEND_URL,
            "Backend URL",
        )
        if not 1 <= args.timeout <= 60:
            raise ValueError("timeout must be between 1 and 60 seconds")
        if not 0 <= args.retries <= 2:
            raise ValueError("retries must be between 0 and 2")
    except ValueError as exc:
        print(f"[ERROR] Invalid diagnostic configuration: {exc}")
        return 2

    if not args.live:
        print("[INFO] Offline dry run; no network access")
        print(f"[INFO] UI target: {ui_url}")
        print(f"[INFO] Backend target: {backend_url}")
        print("[OK] Planned HTTP checks: 3")
        return 0

    return run_regression(
        ui_url,
        args.timeout,
        args.retries,
        backend_url=backend_url,
    )


if __name__ == "__main__":
    raise SystemExit(main())
