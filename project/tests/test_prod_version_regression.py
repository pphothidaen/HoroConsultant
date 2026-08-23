"""
project/tests/test_prod_version_regression.py
=============================================
E2E Regression Test for Live Production Version Alignment.

Verifies:
1. GET /version.json returns a valid version and commit hash.
2. The live webpage DOM (footer and <head> script) matches /version.json.
3. The live /app.js CLIENT_APP_VERSION matches /version.json.
4. The live /sw.js CACHE_VERSION matches /version.json.
5. If a version drift is detected, verifies that the client-side mismatch guard
   is properly structured to trigger the Hard Reset update modal.
"""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
import pytest
from pathlib import Path

PROD_BASE_URL = "https://horo-consultant-psi.vercel.app"
TIMEOUT_SECONDS = 30


def fetch_url(url: str, cache_buster: bool = True) -> tuple[int, str, dict[str, str]]:
    """Helper to fetch URL with cache-busting and return (status, body, headers)."""
    full_url = f"{url}?t={int(time.time() * 1000)}" if cache_buster else url
    req = urllib.request.Request(
        full_url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) HoroConsultant-E2E-Tester",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            status = resp.status
            body = resp.read().decode("utf-8")
            headers = {k.lower(): v for k, v in resp.headers.items()}
            return status, body, headers
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        return e.code, body, {}
    except Exception as ex:
        pytest.skip(f"Live network access to {url} unavailable or timed out: {ex}")


@pytest.mark.network
def test_prod_version_json_contract():
    """Verify live /version.json endpoint returns valid semantic version & commit hash."""
    status, body, _ = fetch_url(f"{PROD_BASE_URL}/version.json")
    assert status == 200, f"Expected 200 from /version.json, got {status}"
    
    data = json.loads(body)
    assert "version" in data, "Missing 'version' in /version.json"
    assert "commit" in data, "Missing 'commit' in /version.json"
    assert "timestamp" in data, "Missing 'timestamp' in /version.json"
    assert data["version"].startswith("1.0.0."), f"Unexpected version format: {data['version']}"
    assert len(data["commit"]) >= 7, f"Invalid commit length: {data['commit']}"


@pytest.mark.network
def test_prod_html_matches_version_json():
    """Verify live HTML contains matching CURRENT_PAGE_VERSION in <head> and footer."""
    status_ver, body_ver, _ = fetch_url(f"{PROD_BASE_URL}/version.json")
    assert status_ver == 200
    server_ver = json.loads(body_ver)["version"].strip()

    status_html, body_html, _ = fetch_url(f"{PROD_BASE_URL}/")
    assert status_html == 200

    # 1. Check window.CURRENT_PAGE_VERSION in <head>
    head_match = re.search(r'window\.CURRENT_PAGE_VERSION\s*=\s*["\']([^"\']+)["\']', body_html)
    assert head_match is not None, "window.CURRENT_PAGE_VERSION not found in live HTML"
    head_version = head_match.group(1).strip()
    assert head_version == server_ver, (
        f"Version mismatch: HTML head version '{head_version}' != /version.json '{server_ver}'"
    )

    # 2. Check footer version text
    footer_match = re.search(r'id=["\']footer-version-text["\'][^>]*>([^<]+)</', body_html)
    assert footer_match is not None, "footer-version-text element not found in live HTML"
    footer_text = footer_match.group(1)
    assert server_ver in footer_text, (
        f"Footer text '{footer_text}' does not contain expected version '{server_ver}'"
    )


@pytest.mark.network
def test_prod_app_js_matches_version_json():
    """Verify live /app.js has matching CLIENT_APP_VERSION and showVersionModal guard."""
    status_ver, body_ver, _ = fetch_url(f"{PROD_BASE_URL}/version.json")
    assert status_ver == 200
    server_ver = json.loads(body_ver)["version"].strip()

    status_js, body_js, _ = fetch_url(f"{PROD_BASE_URL}/app.js")
    assert status_js == 200

    # Check CLIENT_APP_VERSION constant
    app_match = re.search(r'const CLIENT_APP_VERSION\s*=\s*["\']([^"\']+)["\']', body_js)
    assert app_match is not None, "CLIENT_APP_VERSION not found in live app.js"
    app_version = app_match.group(1).strip()
    assert app_version == server_ver, (
        f"Version mismatch: app.js version '{app_version}' != /version.json '{server_ver}'"
    )

    # Verify presence of showVersionModal and forcePurgeAndReload in app.js
    assert "showVersionModal" in body_js, "showVersionModal function missing from live app.js"
    assert "forcePurgeAndReload" in body_js, "forcePurgeAndReload function missing from live app.js"
    assert "checkAppVersion" in body_js, "checkAppVersion function missing from live app.js"


@pytest.mark.network
def test_prod_sw_js_cache_version_alignment():
    """Verify live Service Worker /sw.js defines matching CACHE_VERSION."""
    status_ver, body_ver, _ = fetch_url(f"{PROD_BASE_URL}/version.json")
    assert status_ver == 200
    server_ver = json.loads(body_ver)["version"].strip()

    status_sw, body_sw, _ = fetch_url(f"{PROD_BASE_URL}/sw.js")
    assert status_sw == 200

    sw_match = re.search(r'const CACHE_VERSION\s*=\s*["\']v?([^"\']+)["\']', body_sw)
    assert sw_match is not None, "CACHE_VERSION not found in live sw.js"
    sw_version = sw_match.group(1).strip()
    assert sw_version == server_ver, (
        f"Version mismatch: sw.js CACHE_VERSION '{sw_version}' != /version.json '{server_ver}'"
    )


@pytest.mark.network
def test_prod_hard_reset_guard_behavior():
    """Verify that the client-side forcePurgeAndReload function exists and has correct cache purge steps."""
    status_html, body_html, _ = fetch_url(f"{PROD_BASE_URL}/")
    assert status_html == 200

    # Ensure hard reset logic includes localStorage, caches.delete, and serviceWorker unregister
    assert "window.forcePurgeAndReload" in body_html
    assert "localStorage.clear" in body_html
    assert "caches.delete" in body_html
    assert "serviceWorker.getRegistrations" in body_html
    assert "force_reload=" in body_html
