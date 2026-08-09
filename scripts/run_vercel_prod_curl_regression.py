#!/usr/bin/env python3
"""
scripts/run_vercel_prod_curl_regression.py
==========================================
Post-Deployment Production Regression Suite for Vercel Edge Gateway.

Tests the live Vercel production endpoint (https://horo-consultant-psi.vercel.app)
with the exact same curl headers that the HuggingFace static frontend sends.

Checks:
  1. GET /health  → HTTP 200 + JSON {status: ok} + CORS headers present
  2. OPTIONS /api/v1/bazi/interpret → HTTP 204 + CORS preflight headers
  3. POST /api/v1/bazi/interpret → HTTP 200 + {chart, interpretation} + CORS headers

Usage:
  python3 scripts/run_vercel_prod_curl_regression.py
  python3 scripts/run_vercel_prod_curl_regression.py --url https://custom-deploy.vercel.app
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://pphothidaen-horoconsultant-core-backend.static.hf.space"
DEFAULT_BASE_URL = "https://horo-consultant-psi.vercel.app"

# Browser headers that reproduce the exact curl the user reported
BROWSER_HEADERS = {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9,ja;q=0.8",
    "cache-control": "no-cache",
    "origin": ORIGIN,
    "pragma": "no-cache",
    "priority": "u=1, i",
    "referer": f"{ORIGIN}/",
    "sec-ch-ua": '"Not=A?Brand";v="99", "Google Chrome";v="151", "Chromium";v="151"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
}


def _do_request(url: str, method: str = "GET", body: bytes | None = None,
                extra_headers: dict[str, str] | None = None) -> dict[str, Any]:
    """Make HTTP request and return {status, headers, body_text, body_json, latency_ms}."""
    headers = {**BROWSER_HEADERS, **(extra_headers or {})}

    req = urllib.request.Request(url, method=method, headers=headers, data=body)
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            latency = (time.perf_counter() - start) * 1000
            raw = response.read()
            body_text = raw.decode("utf-8", errors="replace")
            try:
                body_json = json.loads(body_text)
            except Exception:
                body_json = None
            return {
                "status": response.status,
                "headers": dict(response.headers),
                "body_text": body_text,
                "body_json": body_json,
                "latency_ms": round(latency, 1),
                "error": None,
            }
    except urllib.error.HTTPError as e:
        latency = (time.perf_counter() - start) * 1000
        raw = e.read()
        body_text = raw.decode("utf-8", errors="replace")
        return {
            "status": e.code,
            "headers": dict(e.headers),
            "body_text": body_text,
            "body_json": None,
            "latency_ms": round(latency, 1),
            "error": str(e),
        }
    except Exception as e:
        latency = (time.perf_counter() - start) * 1000
        return {
            "status": 0,
            "headers": {},
            "body_text": "",
            "body_json": None,
            "latency_ms": round(latency, 1),
            "error": str(e),
        }


def _check_cors(result: dict[str, Any]) -> bool:
    """Return True if CORS header is present and non-empty."""
    headers_lower = {k.lower(): v for k, v in result["headers"].items()}
    acao = headers_lower.get("access-control-allow-origin", "")
    return bool(acao)


def run_regression(base_url: str) -> int:
    """Run all regression tests. Returns exit code (0=pass, 1=fail)."""
    results = []
    all_passed = True

    print("\n[INFO] Vercel Production Curl Regression Suite")
    print(f"[INFO] Target: {base_url}")
    print(f"[INFO] Origin: {ORIGIN}")
    print("-" * 70)

    # ── Test 1: GET /health ──────────────────────────────────────────────────
    url = f"{base_url}/health"
    r = _do_request(url, "GET")
    passed = (
        r["status"] == 200
        and r["body_json"] is not None
        and r["body_json"].get("status") == "ok"
        and _check_cors(r)
    )
    all_passed = all_passed and passed
    tag = "[OK]" if passed else "[FAIL]"
    print(f"{tag} GET /health → HTTP {r['status']} | CORS={_check_cors(r)} | {r['latency_ms']}ms")
    if not passed:
        print(f"     Body: {r['body_text'][:200]}")
        print(f"     CORS header: {r['headers'].get('Access-Control-Allow-Origin', 'MISSING')}")
    results.append({"test": "GET /health", "passed": passed, "status": r["status"], "latency_ms": r["latency_ms"]})

    # ── Test 2: OPTIONS /api/v1/bazi/interpret (CORS preflight) ─────────────
    url = f"{base_url}/api/v1/bazi/interpret"
    r = _do_request(url, "OPTIONS", extra_headers={
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    })
    passed = (
        r["status"] in {200, 204}
        and _check_cors(r)
        and bool(r["headers"].get("Access-Control-Allow-Methods") or
                 r["headers"].get("access-control-allow-methods"))
    )
    all_passed = all_passed and passed
    tag = "[OK]" if passed else "[FAIL]"
    h = {k.lower(): v for k, v in r["headers"].items()}
    print(f"{tag} OPTIONS /api/v1/bazi/interpret → HTTP {r['status']} | CORS={_check_cors(r)} | {r['latency_ms']}ms")
    if not passed:
        print(f"     Access-Control-Allow-Origin: {h.get('access-control-allow-origin', 'MISSING')}")
        print(f"     Access-Control-Allow-Methods: {h.get('access-control-allow-methods', 'MISSING')}")
    results.append({"test": "OPTIONS /api/v1/bazi/interpret", "passed": passed, "status": r["status"], "latency_ms": r["latency_ms"]})

    # ── Test 3: POST /api/v1/bazi/interpret ─────────────────────────────────
    url = f"{base_url}/api/v1/bazi/interpret"
    payload = json.dumps({
        "birth_datetime": "1990-05-15 14:30:00",
        "longitude": 100.493,
        "utc_offset_hours": 7,
        "unknown_hour": False,
        "enable_validation": True,
        "query": "วิเคราะห์ความแข็งแกร่งของ Day Master ธาตุทอง และอาชีพการงานที่ส่งเสริมดวงชะตา",
    }, ensure_ascii=False).encode("utf-8")
    r = _do_request(url, "POST", body=payload, extra_headers={"content-type": "application/json"})
    has_chart = (r["body_json"] or {}).get("chart") is not None
    has_interp = (r["body_json"] or {}).get("interpretation") is not None
    passed = (
        r["status"] == 200
        and has_chart
        and has_interp
        and _check_cors(r)
    )
    all_passed = all_passed and passed
    tag = "[OK]" if passed else "[FAIL]"
    print(f"{tag} POST /api/v1/bazi/interpret → HTTP {r['status']} | CORS={_check_cors(r)} | {r['latency_ms']}ms")
    if not passed:
        print(f"     Body (first 300): {r['body_text'][:300]}")
        print(f"     Access-Control-Allow-Origin: {r['headers'].get('Access-Control-Allow-Origin', 'MISSING')}")
    elif r["body_json"]:
        dm = r["body_json"]["chart"].get("day_master", {})
        print(f"     Day Master: {dm.get('stem', '?')} ({dm.get('element', '?')}, {dm.get('polarity', '?')})")
    results.append({"test": "POST /api/v1/bazi/interpret", "passed": passed, "status": r["status"], "latency_ms": r["latency_ms"]})

    # ── Summary ──────────────────────────────────────────────────────────────
    print("-" * 70)
    passed_count = sum(1 for r in results if r["passed"])
    total = len(results)
    print(f"[INFO] Results: {passed_count}/{total} PASSED")
    if all_passed:
        print("[OK] ALL TESTS PASSED — Vercel production gateway is healthy & CORS-compliant")
    else:
        print("[FAIL] SOME TESTS FAILED — Check the output above for details")

    return 0 if all_passed else 1


def main():
    parser = argparse.ArgumentParser(description="Vercel Production Curl Regression Suite")
    parser.add_argument("--url", default=DEFAULT_BASE_URL, help="Base URL to test against")
    parser.add_argument("--use-python", action="store_true", help="Force python execution instead of Rust binary")
    args = parser.parse_args()

    rust_binary = ROOT / "rust_core" / "target" / "release" / "vercel_curl_regression"
    if rust_binary.exists() and not args.use_python:
        import subprocess
        print(f"[INFO] Delegating Vercel Curl Regression to High-Performance Rust Binary ({rust_binary.name})...")
        res = subprocess.run([str(rust_binary), "--url", args.url])
        sys.exit(res.returncode)

    sys.exit(run_regression(args.url))


if __name__ == "__main__":
    main()
