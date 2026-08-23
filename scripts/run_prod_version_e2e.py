#!/usr/bin/env python3
"""
scripts/run_prod_version_e2e.py
===============================
Live Production E2E Version Regression & Alignment Verification Suite.

Features:
1. Fetches server version from https://horo-consultant-psi.vercel.app/version.json
2. Scans live HTML (<head> and footer), /app.js, and /sw.js for version consistency.
3. Validates Hard Reset & Version Update Modal architecture on client side.
4. Auto-update option: If mismatch is detected and --auto-update is specified,
   automatically stamps local files and triggers production deployment via Vercel CLI.
5. Generates structured JSON report at project/tests/prod_version_regression_report.json.

Usage:
  python3 scripts/run_prod_version_e2e.py
  python3 scripts/run_prod_version_e2e.py --auto-update
  python3 scripts/run_prod_version_e2e.py --url https://horo-consultant-psi.vercel.app
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_URL = "https://horo-consultant-psi.vercel.app"
REPORT_PATH = ROOT / "project" / "tests" / "prod_version_regression_report.json"


def fetch_resource(url: str, timeout: int = 25) -> tuple[int, str, float]:
    """Fetch URL with cache busting and return (status, content, latency_ms)."""
    full_url = f"{url}?t={int(time.time() * 1000)}"
    start = time.perf_counter()
    req = urllib.request.Request(
        full_url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) HoroConsultant-Version-E2E",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content = resp.read().decode("utf-8")
            latency = (time.perf_counter() - start) * 1000
            return resp.status, content, latency
    except urllib.error.HTTPError as e:
        content = e.read().decode("utf-8") if e.fp else ""
        latency = (time.perf_counter() - start) * 1000
        return e.code, content, latency
    except Exception as ex:
        latency = (time.perf_counter() - start) * 1000
        return 0, str(ex), latency


def run_version_e2e_audit(base_url: str = DEFAULT_URL) -> dict:
    """Perform comprehensive E2E version verification across all endpoints and assets."""
    base_url = base_url.rstrip("/")
    print(f"\n🚀 Running Production Version E2E Regression Audit on: {base_url}\n" + "=" * 70)

    report: dict = {
        "target_url": base_url,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "UNKNOWN",
        "checks": [],
        "server_version": None,
        "mismatches": [],
    }

    # 1. Fetch server authoritative /version.json
    status_ver, body_ver, lat_ver = fetch_resource(f"{base_url}/version.json")
    if status_ver != 200:
        print(f"❌ [FAIL] /version.json returned status {status_ver} ({lat_ver:.1f}ms)")
        report["status"] = "FAILED"
        report["checks"].append({
            "name": "version_json_fetch",
            "status": "FAILED",
            "error": f"HTTP {status_ver}",
            "latency_ms": lat_ver,
        })
        return report

    try:
        ver_data = json.loads(body_ver)
        server_ver = ver_data.get("version", "").strip()
        server_commit = ver_data.get("commit", "").strip()
        report["server_version"] = server_ver
        report["server_commit"] = server_commit
        print(f"✅ [OK] Server Authoritative Version: {server_ver} (Commit: {server_commit}) [{lat_ver:.1f}ms]")
        report["checks"].append({
            "name": "version_json_contract",
            "status": "PASSED",
            "version": server_ver,
            "commit": server_commit,
            "latency_ms": lat_ver,
        })
    except Exception as ex:
        print(f"❌ [FAIL] JSON parsing /version.json failed: {ex}")
        report["status"] = "FAILED"
        return report

    # 2. Fetch live HTML and check <head> script + footer version
    status_html, body_html, lat_html = fetch_resource(f"{base_url}/")
    if status_html == 200:
        head_match = re.search(r'window\.CURRENT_PAGE_VERSION\s*=\s*["\']([^"\']+)["\']', body_html)
        head_ver = head_match.group(1).strip() if head_match else "NOT_FOUND"

        footer_match = re.search(r'id=["\']footer-version-text["\'][^>]*>([^<]+)</', body_html)
        footer_text = footer_match.group(1).strip() if footer_match else "NOT_FOUND"

        head_ok = (head_ver == server_ver)
        footer_ok = (server_ver in footer_text)

        if head_ok and footer_ok:
            print(f"✅ [OK] Live HTML Head & Footer match server version: {head_ver} [{lat_html:.1f}ms]")
            report["checks"].append({
                "name": "html_version_match",
                "status": "PASSED",
                "head_version": head_ver,
                "footer_text": footer_text,
                "latency_ms": lat_html,
            })
        else:
            print(f"❌ [FAIL] HTML Version Drift: Head='{head_ver}', Expected='{server_ver}'")
            report["mismatches"].append({
                "asset": "index.html",
                "actual": head_ver,
                "expected": server_ver,
            })
            report["checks"].append({
                "name": "html_version_match",
                "status": "FAILED",
                "head_version": head_ver,
                "expected": server_ver,
                "footer_text": footer_text,
            })
    else:
        print(f"❌ [FAIL] Live HTML fetch failed: HTTP {status_html}")
        report["checks"].append({"name": "html_version_match", "status": "FAILED", "http_status": status_html})

    # 3. Fetch live /app.js and check CLIENT_APP_VERSION
    status_js, body_js, lat_js = fetch_resource(f"{base_url}/app.js")
    if status_js == 200:
        js_match = re.search(r'const CLIENT_APP_VERSION\s*=\s*["\']([^"\']+)["\']', body_js)
        js_ver = js_match.group(1).strip() if js_match else "NOT_FOUND"

        if js_ver == server_ver:
            print(f"✅ [OK] Live app.js CLIENT_APP_VERSION matches: {js_ver} [{lat_js:.1f}ms]")
            report["checks"].append({
                "name": "app_js_version_match",
                "status": "PASSED",
                "app_version": js_ver,
                "has_show_modal": "showVersionModal" in body_js,
                "has_hard_reset": "forcePurgeAndReload" in body_js,
                "latency_ms": lat_js,
            })
        else:
            print(f"❌ [FAIL] app.js Version Drift: Found='{js_ver}', Expected='{server_ver}'")
            report["mismatches"].append({
                "asset": "app.js",
                "actual": js_ver,
                "expected": server_ver,
            })
            report["checks"].append({
                "name": "app_js_version_match",
                "status": "FAILED",
                "app_version": js_ver,
                "expected": server_ver,
            })
    else:
        print(f"❌ [FAIL] Live app.js fetch failed: HTTP {status_js}")
        report["checks"].append({"name": "app_js_version_match", "status": "FAILED", "http_status": status_js})

    # 4. Fetch live /sw.js and check CACHE_VERSION
    status_sw, body_sw, lat_sw = fetch_resource(f"{base_url}/sw.js")
    if status_sw == 200:
        sw_match = re.search(r'const CACHE_VERSION\s*=\s*["\']v?([^"\']+)["\']', body_sw)
        sw_ver = sw_match.group(1).strip() if sw_match else "NOT_FOUND"

        if sw_ver == server_ver:
            print(f"✅ [OK] Live sw.js CACHE_VERSION matches: {sw_ver} [{lat_sw:.1f}ms]")
            report["checks"].append({
                "name": "sw_js_version_match",
                "status": "PASSED",
                "sw_version": sw_ver,
                "latency_ms": lat_sw,
            })
        else:
            print(f"❌ [FAIL] sw.js CACHE_VERSION Drift: Found='{sw_ver}', Expected='{server_ver}'")
            report["mismatches"].append({
                "asset": "sw.js",
                "actual": sw_ver,
                "expected": server_ver,
            })
            report["checks"].append({
                "name": "sw_js_version_match",
                "status": "FAILED",
                "sw_version": sw_ver,
                "expected": server_ver,
            })
    else:
        print(f"❌ [FAIL] Live sw.js fetch failed: HTTP {status_sw}")
        report["checks"].append({"name": "sw_js_version_match", "status": "FAILED", "http_status": status_sw})

    # 5. Determine overall status
    if len(report["mismatches"]) == 0 and all(c.get("status") == "PASSED" for c in report["checks"]):
        report["status"] = "ALL_PASSED_READY_FOR_PROD"
        print("\n🎉 [SUCCESS] 100% Version Consistency Verified Across All Live Production Assets!")
    else:
        report["status"] = "MISMATCH_DETECTED"
        print(f"\n⚠️ [WARNING] Detected {len(report['mismatches'])} version mismatch(es)!")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"📊 Detailed Report Saved to: {REPORT_PATH}\n" + "=" * 70)
    return report


def main():
    parser = argparse.ArgumentParser(description="Live Production E2E Version Regression & Alignment Suite")
    parser.add_argument("--url", type=str, default=DEFAULT_URL, help="Base production URL")
    parser.add_argument("--auto-update", action="store_true", help="Auto-remediate version drift by stamping and redeploying")
    args = parser.parse_args()

    report = run_version_e2e_audit(args.url)

    if report["status"] == "ALL_PASSED_READY_FOR_PROD":
        sys.exit(0)

    if args.auto_update and report["status"] == "MISMATCH_DETECTED":
        print("\n🔧 Auto-Remediation Triggered: Stamping and Re-deploying to Vercel...")
        subprocess.run([sys.executable, "scripts/stamp_version.py"], check=True)
        subprocess.run(["npx", "vercel", "--prod", "--yes"], check=True)
        print("🔄 Re-testing after auto-update...")
        second_report = run_version_e2e_audit(args.url)
        if second_report["status"] == "ALL_PASSED_READY_FOR_PROD":
            print("✅ Auto-Remediation Successful!")
            sys.exit(0)
        else:
            print("❌ Version mismatch still detected after deployment.")
            sys.exit(1)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
