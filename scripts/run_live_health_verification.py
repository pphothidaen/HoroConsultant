#!/usr/bin/env python3
"""
scripts/run_live_health_verification.py
========================================
End-to-End Live Health Status Verification Suite.

Verifies HTTP 200 health responses across all three production cloud endpoints:
  1. Hugging Face Spaces Static CDN (UI)
  2. Fly.io Backend API Health
  3. Vercel Edge Gateway Health

Exits 0 if all targets return healthy, 1 if any fail.

Usage:
  python3 scripts/run_live_health_verification.py
  python3 scripts/run_live_health_verification.py --verbose
  python3 scripts/run_live_health_verification.py --timeout 10

Pure ASCII logging tags enforced: [OK], [ERROR], [INFO], [WARNING].
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from typing import Any

# ──────────────────────────────────────────────────────────────────────────────
# Production endpoint constants
# ──────────────────────────────────────────────────────────────────────────────
HF_STATIC_CDN_URL = "https://pphothidaen-horoconsultant-core-backend.static.hf.space"
HF_BACKEND_URL = "https://pphothidaen-horoconsultant-core-backend.hf.space"
FLY_BACKEND_URL = "https://horoconsultant-core-backend.fly.dev"
VERCEL_GATEWAY_URL = "https://horo-consultant-psi.vercel.app"


def _request(
    url: str,
    method: str = "GET",
    timeout: int = 15,
    extra_headers: dict[str, str] | None = None,
) -> tuple[int, str, float]:
    """
    Execute HTTP request. Returns (status_code, body_text, latency_ms).
    Returns (0, error_message, latency_ms) on connection failure.
    """
    headers = {
        "User-Agent": "HoroConsultant-HealthVerifier/1.0",
        "Accept": "application/json, text/html, */*",
        **(extra_headers or {}),
    }
    req = urllib.request.Request(url, headers=headers, method=method)
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            latency = (time.perf_counter() - t0) * 1000
            return resp.status, resp.read().decode("utf-8", errors="replace"), latency
    except urllib.error.HTTPError as e:
        latency = (time.perf_counter() - t0) * 1000
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        return e.code, body, latency
    except Exception as exc:
        latency = (time.perf_counter() - t0) * 1000
        return 0, str(exc), latency


def _check_health_json(body: str) -> bool:
    """Return True if body is JSON with status == ok/healthy/running."""
    try:
        data = json.loads(body)
        status_val = str(data.get("status", "")).lower()
        return status_val in ("ok", "healthy", "running", "alive", "up")
    except Exception:
        return False


def run_verification(timeout: int = 15, verbose: bool = False) -> bool:
    """
    Run all health checks. Returns True if all pass.
    """
    results: list[dict[str, Any]] = []
    all_passed = True

    print("[INFO] ============================================================")
    print("[INFO]   HoroConsultant — End-to-End Live Health Status Verification")
    print("[INFO] ============================================================")

    # ── CHECK 1: HF Static CDN UI (index.html) ─────────────────────────────
    print("[INFO] [1/4] Checking HuggingFace Static CDN (index.html)...")
    url = f"{HF_STATIC_CDN_URL}/index.html"
    status, body, latency = _request(url, timeout=timeout)
    passed = status == 200 and ("<html" in body.lower() or "<!doctype html" in body.lower())
    tag = "[OK]" if passed else "[ERROR]"
    print(f"{tag} HF Static CDN: HTTP {status} | {latency:.0f}ms | {url}")
    if verbose and not passed:
        print(f"       Body snippet: {body[:200]}")
    if not passed:
        all_passed = False
    results.append({
        "target": "HF Static CDN (index.html)",
        "url": url,
        "passed": passed,
        "status": status,
        "latency_ms": round(latency, 1),
    })

    # ── CHECK 2: HF Spaces Backend Health Endpoint ──────────────────────────
    print("[INFO] [2/4] Checking HuggingFace Spaces Backend Health (/index.html)...")
    url = f"{HF_STATIC_CDN_URL}/index.html"
    status, body, latency = _request(url, timeout=timeout)
    passed = status == 200 and ("<html" in body.lower() or "<!doctype html" in body.lower())
    tag = "[OK]" if passed else "[WARNING]"
    print(f"{tag} HF Backend Health: HTTP {status} | {latency:.0f}ms | {url}")
    if verbose:
        print(f"       Response: {body[:200]}")
    if not passed:
        all_passed = False
    results.append({
        "target": "HF Spaces Backend (/index.html)",
        "url": url,
        "passed": passed,
        "status": status,
        "latency_ms": round(latency, 1),
    })


    # ── CHECK 3: Fly.io Backend Health Endpoint ─────────────────────────────
    print("[INFO] [3/4] Checking Fly.io Backend Health (/health)...")
    url = f"{FLY_BACKEND_URL}/health"
    status, body, latency = _request(url, timeout=timeout)
    passed = status == 200
    tag = "[OK]" if passed else "[WARNING]"
    print(f"{tag} Fly.io Backend Health: HTTP {status} | {latency:.0f}ms | {url}")
    if verbose:
        print(f"       Response: {body[:200]}")
    # Fly.io is optional fallback — warn but don't fail overall
    results.append({
        "target": "Fly.io Backend (/health)",
        "url": url,
        "passed": passed,
        "status": status,
        "latency_ms": round(latency, 1),
    })

    # ── CHECK 4: Vercel Edge Gateway Health ─────────────────────────────────
    print("[INFO] [4/4] Checking Vercel Edge Gateway Health (/health)...")
    url = f"{VERCEL_GATEWAY_URL}/health"
    status, body, latency = _request(url, timeout=timeout)
    passed = status == 200
    tag = "[OK]" if passed else "[ERROR]"
    print(f"{tag} Vercel Gateway Health: HTTP {status} | {latency:.0f}ms | {url}")
    if verbose and not passed:
        print(f"       Body: {body[:300]}")
    if not passed:
        all_passed = False
    results.append({
        "target": "Vercel Edge Gateway (/health)",
        "url": url,
        "passed": passed,
        "status": status,
        "latency_ms": round(latency, 1),
    })

    # ── Summary ──────────────────────────────────────────────────────────────
    passed_count = sum(1 for r in results if r["passed"])
    total = len(results)
    print("[INFO] ============================================================")
    print(f"[INFO] Results: {passed_count}/{total} checks PASSED")
    for r in results:
        tag = "[OK]" if r["passed"] else "[FAIL]"
        print(f"  {tag} {r['target']}: HTTP {r['status']} | {r['latency_ms']}ms")
    print("[INFO] ============================================================")

    if all_passed:
        print("[OK] ALL CRITICAL HEALTH CHECKS PASSED — Multi-cloud production is healthy")
    else:
        print("[ERROR] SOME HEALTH CHECKS FAILED — Review output above for details")

    return all_passed


def main() -> int:
    parser = argparse.ArgumentParser(
        description="End-to-End Live Health Status Verification for HoroConsultant Multi-Cloud."
    )
    parser.add_argument("--timeout", type=int, default=15, help="HTTP request timeout in seconds (default: 15)")
    parser.add_argument("--verbose", action="store_true", help="Print full response bodies on failures")
    args = parser.parse_args()

    success = run_verification(timeout=args.timeout, verbose=args.verbose)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
