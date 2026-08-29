#!/usr/bin/env python3
"""
scripts/run_prod_version_e2e.py
===============================
Live Production E2E Version Regression & Alignment Verification Suite.

Features:
1. Binds the live release identity to committed project/static/version.json.
2. Scans live HTML (<head> and footer), /app.js, and /sw.js for version consistency.
3. Validates Hard Reset & Version Update Modal architecture on client side.
4. Rejects retired deployment targets before any network request.
5. Generates a read-only structured audit report at
   project/tests/prod_version_regression_report.json.

Usage:
  python3 scripts/run_prod_version_e2e.py
  python3 scripts/run_prod_version_e2e.py --url https://horo-consultant-psi.vercel.app
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_URL = "https://horo-consultant-psi.vercel.app"
REPORT_PATH = ROOT / "project" / "tests" / "prod_version_regression_report.json"
APPROVED_CANDIDATE_METADATA_PATH = ROOT / "project" / "static" / "version.json"
RELEASE_IDENTITY_FIELDS = (
    "version",
    "release_source_commit",
    "release_source_revision",
    "release_source_metadata_path",
    "release_source_metadata_sha256",
)
RELEASE_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+\.([0-9a-f]{7,40})$")
RELEASE_COMMIT_RE = re.compile(r"^[0-9a-f]{7,40}$")
RELEASE_REVISION_RE = re.compile(r"^[0-9a-f]{40}$")
RELEASE_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
RETIRED_UI_HOST_SUFFIXES = (
    ".hf.space",
    ".azurecontainerapps.io",
    ".azurewebsites.net",
    ".fly.dev",
)


def parse_release_identity(raw_text: str) -> dict[str, str]:
    """Return one validated canonical release identity or fail closed."""

    def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
        parsed: dict[str, object] = {}
        for key, value in pairs:
            if key in parsed:
                raise ValueError("duplicate release identity key")
            parsed[key] = value
        return parsed

    parsed = json.loads(raw_text, object_pairs_hook=reject_duplicate_keys)
    if not isinstance(parsed, dict) or set(parsed) != set(RELEASE_IDENTITY_FIELDS):
        raise ValueError("release identity must use the closed canonical schema")
    if not all(isinstance(parsed[field], str) for field in RELEASE_IDENTITY_FIELDS):
        raise ValueError("release identity fields must be strings")

    identity = {field: parsed[field] for field in RELEASE_IDENTITY_FIELDS}
    version = identity["version"]
    source_commit = identity["release_source_commit"]
    source_revision = identity["release_source_revision"]
    source_path = identity["release_source_metadata_path"]
    source_digest = identity["release_source_metadata_sha256"]
    version_match = RELEASE_VERSION_RE.fullmatch(version)
    if (
        version_match is None
        or RELEASE_COMMIT_RE.fullmatch(source_commit) is None
        or version_match.group(1) != source_commit
        or RELEASE_REVISION_RE.fullmatch(source_revision) is None
        or not source_revision.startswith(source_commit)
        or source_path != "project/static/version.json"
        or RELEASE_DIGEST_RE.fullmatch(source_digest) is None
    ):
        raise ValueError("release identity fields are malformed or inconsistent")

    canonical = json.dumps(
        {
            "release_source_commit": source_commit,
            "release_source_metadata_path": source_path,
            "release_source_revision": source_revision,
            "version": version,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    if hashlib.sha256(canonical).hexdigest() != source_digest:
        raise ValueError("release identity digest mismatch")
    return identity


def load_approved_candidate_identity() -> dict[str, str]:
    """Load the one committed candidate identity used by post-deploy gates."""
    try:
        raw_text = APPROVED_CANDIDATE_METADATA_PATH.read_text(encoding="utf-8")
    except OSError as error:
        raise ValueError("approved candidate release metadata is unavailable") from error
    try:
        return parse_release_identity(raw_text)
    except (json.JSONDecodeError, TypeError, ValueError) as error:
        raise ValueError("approved candidate release metadata is invalid") from error


def _validated_vercel_url(value: str) -> str:
    """Return one active HTTPS UI origin and reject retired release targets."""
    normalized = value.strip().rstrip("/")
    parsed = urllib.parse.urlsplit(normalized)
    hostname = (parsed.hostname or "").lower()
    if any(hostname.endswith(suffix) for suffix in RETIRED_UI_HOST_SUFFIXES):
        raise ValueError("retired production UI target is not permitted")
    if (
        parsed.scheme != "https"
        or not hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("production UI target must be one HTTPS origin")
    return normalized


def write_report(report: dict) -> None:
    """Persist one current machine-readable audit report."""
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


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
            raw_bytes = resp.read()
            content = raw_bytes.decode("utf-8", errors="replace")
            latency = (time.perf_counter() - start) * 1000
            return resp.status, content, latency
    except urllib.error.HTTPError as e:
        content = e.read().decode("utf-8", errors="replace") if e.fp else ""
        latency = (time.perf_counter() - start) * 1000
        return e.code, content, latency
    except Exception as ex:
        latency = (time.perf_counter() - start) * 1000
        return 0, str(ex), latency


def run_version_e2e_audit(base_url: str = DEFAULT_URL) -> dict:
    """Perform comprehensive E2E version verification across all endpoints and assets."""
    base_url = _validated_vercel_url(base_url)
    print(f"[INFO] Running production version E2E audit on: {base_url}")

    report: dict = {
        "target_url": base_url,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "UNKNOWN",
        "checks": [],
        "server_version": None,
        "mismatches": [],
    }

    try:
        approved_candidate = load_approved_candidate_identity()
    except ValueError:
        print("[ERROR] Approved candidate release identity is invalid")
        report["status"] = "FAILED"
        report["checks"].append({
            "name": "approved_candidate_contract",
            "status": "FAILED",
            "error": "invalid_approved_candidate_identity",
        })
        write_report(report)
        return report

    report["approved_candidate_identity"] = approved_candidate
    print(
        f"[INFO] Approved candidate: {approved_candidate['version']} "
        f"(source: {approved_candidate['release_source_commit']})"
    )

    # 1. Fetch server authoritative /version.json
    status_ver, body_ver, lat_ver = fetch_resource(f"{base_url}/version.json")
    if status_ver != 200:
        print(f"[ERROR] /version.json returned status {status_ver} ({lat_ver:.1f}ms)")
        report["status"] = "FAILED"
        report["checks"].append({
            "name": "version_json_fetch",
            "status": "FAILED",
            "error": f"HTTP {status_ver}",
            "latency_ms": lat_ver,
        })
        write_report(report)
        return report

    try:
        release_identity = parse_release_identity(body_ver)
        if release_identity != approved_candidate:
            print("[ERROR] /version.json does not match the approved candidate")
            report["status"] = "FAILED"
            report["checks"].append({
                "name": "version_json_contract",
                "status": "FAILED",
                "error": "candidate_release_identity_mismatch",
            })
            write_report(report)
            return report
        server_ver = release_identity["version"]
        source_commit = release_identity["release_source_commit"]
        report.update(release_identity)
        report["server_version"] = server_ver
        print(
            f"[OK] Server release identity: {server_ver} "
            f"(source: {source_commit}) [{lat_ver:.1f}ms]"
        )
        report["checks"].append({
            "name": "version_json_contract",
            "status": "PASSED",
            **release_identity,
            "latency_ms": lat_ver,
        })
    except (json.JSONDecodeError, TypeError, ValueError):
        print("[ERROR] /version.json contains an invalid release identity")
        report["status"] = "FAILED"
        report["checks"].append({
            "name": "version_json_contract",
            "status": "FAILED",
            "error": "invalid_release_identity",
        })
        write_report(report)
        return report

    # 2. Fetch live HTML and check <head> script + footer version
    status_html, body_html, lat_html = fetch_resource(f"{base_url}/")
    if status_html == 200:
        head_versions = [
            value.strip()
            for value in re.findall(
                r'window\.CURRENT_PAGE_VERSION\s*=\s*["\']([^"\']+)["\']',
                body_html,
            )
        ]
        footer_texts = [
            value.strip()
            for value in re.findall(
                r'id=["\']footer-version-text["\'][^>]*>([^<]+)</',
                body_html,
            )
        ]
        footer_versions = (
            re.findall(r"\bv?(\d+\.\d+\.\d+\.[0-9a-f]{7,40})\b", footer_texts[0])
            if len(footer_texts) == 1
            else []
        )
        head_ver = head_versions[0] if len(head_versions) == 1 else "NOT_FOUND_OR_DUPLICATE"
        footer_text = footer_texts[0] if len(footer_texts) == 1 else "NOT_FOUND_OR_DUPLICATE"

        head_ok = head_versions == [server_ver]
        footer_ok = footer_versions == [server_ver]

        if head_ok and footer_ok:
            print(f"[OK] Live HTML head and footer match candidate version: {head_ver} [{lat_html:.1f}ms]")
            report["checks"].append({
                "name": "html_version_match",
                "status": "PASSED",
                "head_version": head_ver,
                "footer_text": footer_text,
                "latency_ms": lat_html,
            })
        else:
            print(f"[ERROR] HTML version drift: head='{head_ver}', expected='{server_ver}'")
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
        print(f"[ERROR] Live HTML fetch failed: HTTP {status_html}")
        report["checks"].append({"name": "html_version_match", "status": "FAILED", "http_status": status_html})

    # 3. Fetch live /app.js and check CLIENT_APP_VERSION
    status_js, body_js, lat_js = fetch_resource(f"{base_url}/app.js")
    if status_js == 200:
        js_versions = [
            value.strip()
            for value in re.findall(
                r'const CLIENT_APP_VERSION\s*=\s*["\']([^"\']+)["\']',
                body_js,
            )
        ]
        js_ver = js_versions[0] if len(js_versions) == 1 else "NOT_FOUND_OR_DUPLICATE"

        if js_versions == [server_ver]:
            print(f"[OK] Live app.js CLIENT_APP_VERSION matches: {js_ver} [{lat_js:.1f}ms]")
            report["checks"].append({
                "name": "app_js_version_match",
                "status": "PASSED",
                "app_version": js_ver,
                "has_show_modal": "showVersionModal" in body_js,
                "has_hard_reset": "forcePurgeAndReload" in body_js,
                "latency_ms": lat_js,
            })
        else:
            print(f"[ERROR] app.js version drift: found='{js_ver}', expected='{server_ver}'")
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
        print(f"[ERROR] Live app.js fetch failed: HTTP {status_js}")
        report["checks"].append({"name": "app_js_version_match", "status": "FAILED", "http_status": status_js})

    # 4. Fetch live /sw.js and check CACHE_VERSION
    status_sw, body_sw, lat_sw = fetch_resource(f"{base_url}/sw.js")
    if status_sw == 200:
        sw_versions = [
            value.strip()
            for value in re.findall(
                r'const CACHE_VERSION\s*=\s*["\']v?([^"\']+)["\']',
                body_sw,
            )
        ]
        sw_ver = sw_versions[0] if len(sw_versions) == 1 else "NOT_FOUND_OR_DUPLICATE"

        if sw_versions == [server_ver]:
            print(f"[OK] Live sw.js CACHE_VERSION matches: {sw_ver} [{lat_sw:.1f}ms]")
            report["checks"].append({
                "name": "sw_js_version_match",
                "status": "PASSED",
                "sw_version": sw_ver,
                "latency_ms": lat_sw,
            })
        else:
            print(f"[ERROR] sw.js CACHE_VERSION drift: found='{sw_ver}', expected='{server_ver}'")
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
        print(f"[ERROR] Live sw.js fetch failed: HTTP {status_sw}")
        report["checks"].append({"name": "sw_js_version_match", "status": "FAILED", "http_status": status_sw})

    # 5. Fetch live /favicon.ico and /favicon.svg
    status_ico, _, lat_ico = fetch_resource(f"{base_url}/favicon.ico")
    if status_ico == 200:
        print(f"[OK] Live /favicon.ico available: HTTP 200 [{lat_ico:.1f}ms]")
        report["checks"].append({"name": "favicon_ico_available", "status": "PASSED", "latency_ms": lat_ico})
    else:
        print(f"[ERROR] Live /favicon.ico failed: HTTP {status_ico}")
        report["mismatches"].append({"asset": "favicon.ico", "actual": f"HTTP {status_ico}", "expected": "HTTP 200"})
        report["checks"].append({"name": "favicon_ico_available", "status": "FAILED", "http_status": status_ico})

    status_svg, _, lat_svg = fetch_resource(f"{base_url}/favicon.svg")
    if status_svg == 200:
        print(f"[OK] Live /favicon.svg available: HTTP 200 [{lat_svg:.1f}ms]")
        report["checks"].append({"name": "favicon_svg_available", "status": "PASSED", "latency_ms": lat_svg})
    else:
        print(f"[ERROR] Live /favicon.svg failed: HTTP {status_svg}")
        report["mismatches"].append({"asset": "favicon.svg", "actual": f"HTTP {status_svg}", "expected": "HTTP 200"})
        report["checks"].append({"name": "favicon_svg_available", "status": "FAILED", "http_status": status_svg})

    # 5. Determine overall status
    if len(report["mismatches"]) == 0 and all(c.get("status") == "PASSED" for c in report["checks"]):
        report["status"] = "ALL_PASSED_READY_FOR_PROD"
        print("[OK] Candidate identity and live production assets are consistent")
    else:
        report["status"] = "MISMATCH_DETECTED"
        print(f"[WARNING] Detected {len(report['mismatches'])} version mismatch(es)")

    write_report(report)
    print(f"[INFO] Detailed report saved to: {REPORT_PATH}")
    return report


def main() -> int:
    """Run the read-only production version audit."""
    parser = argparse.ArgumentParser(description="Live Production E2E Version Regression & Alignment Suite")
    parser.add_argument("--url", type=str, default=DEFAULT_URL, help="Base production URL")
    args = parser.parse_args()

    try:
        report = run_version_e2e_audit(args.url)
    except ValueError as error:
        print(f"[ERROR] {error}")
        return 2
    return 0 if report["status"] == "ALL_PASSED_READY_FOR_PROD" else 1


if __name__ == "__main__":
    raise SystemExit(main())
