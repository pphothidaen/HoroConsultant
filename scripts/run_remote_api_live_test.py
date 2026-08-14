#!/usr/bin/env python3
"""
scripts/run_remote_api_live_test.py
===================================
Real Remote Production API & Live Endpoints Verification Runner.
Executes live HTTP requests across:
  1. Production API Gateway (Vercel Serverless Gateway: https://horo-consultant-psi.vercel.app)
  2. Hugging Face Live Space (https://pphothidaen-horoconsultant-core-backend.static.hf.space)
  3. All Core Endpoints: /health, /api/v1/bazi/calculate, /api/v1/bazi/interpret, /api/v1/location/resolve
  4. CORS Preflight (OPTIONS) with Origin: https://pphothidaen-horoconsultant-core-backend.static.hf.space
"""

import sys
import time
import httpx

STATIC_SPACE_ORIGIN = "https://pphothidaen-horoconsultant-core-backend.static.hf.space"
GATEWAY_BASE_URL = "https://horo-consultant-psi.vercel.app"

BROWSER_HEADERS = {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "no-cache",
    "content-type": "application/json",
    "origin": STATIC_SPACE_ORIGIN,
    "referer": f"{STATIC_SPACE_ORIGIN}/",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site",
}


def test_endpoint(name: str, method: str, url: str, json_data: dict = None, headers: dict = None, expected_status: list[int] = [200, 204]):
    t0 = time.monotonic()
    try:
        with httpx.Client(timeout=15.0, follow_redirects=True) as client:
            if method.upper() == "GET":
                res = client.get(url, headers=headers)
            elif method.upper() == "POST":
                res = client.post(url, json=json_data, headers=headers)
            elif method.upper() == "OPTIONS":
                res = client.options(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")

        elapsed_ms = round((time.monotonic() - t0) * 1000, 2)
        passed = res.status_code in expected_status
        cors_origin = res.headers.get("access-control-allow-origin", "none")

        status_tag = "[OK] PASSED" if passed else "[ERROR] FAILED"
        print(f"{status_tag:15} | {name:40} | HTTP {res.status_code} ({elapsed_ms:6.1f}ms) | CORS: {cors_origin}")
        return passed
    except Exception as exc:
        elapsed_ms = round((time.monotonic() - t0) * 1000, 2)
        print(f"{'[ERROR] FAILED':15} | {name:40} | EXCEPTION: {exc} ({elapsed_ms}ms)")
        return False


def main():
    print("=" * 80)
    print("  🌌 REAL REMOTE PRODUCTION API & LIVE ENDPOINT INTEGRATION TESTS")
    print(f"  API Gateway: {GATEWAY_BASE_URL}")
    print(f"  CORS Origin: {STATIC_SPACE_ORIGIN}")
    print("=" * 80)

    results = []

    # 1. Health Checks
    results.append(test_endpoint("GET /health (Gateway Health Check)", "GET", f"{GATEWAY_BASE_URL}/health", headers=BROWSER_HEADERS))
    results.append(test_endpoint("GET /api/health (API Health Alias)", "GET", f"{GATEWAY_BASE_URL}/api/health", headers=BROWSER_HEADERS))

    # 2. CORS Preflights (OPTIONS)
    options_headers = {
        "Origin": STATIC_SPACE_ORIGIN,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    }
    results.append(test_endpoint("OPTIONS /api/v1/bazi/calculate Preflight", "OPTIONS", f"{GATEWAY_BASE_URL}/api/v1/bazi/calculate", headers=options_headers))
    results.append(test_endpoint("OPTIONS /api/v1/bazi/interpret Preflight", "OPTIONS", f"{GATEWAY_BASE_URL}/api/v1/bazi/interpret", headers=options_headers))

    # 3. BaZi Calculate
    calc_payload = {
        "birth_datetime": "1990-05-15 14:30:00",
        "longitude": 100.493,
        "utc_offset_hours": 7.0,
        "unknown_hour": False,
    }
    results.append(test_endpoint("POST /api/v1/bazi/calculate Execution", "POST", f"{GATEWAY_BASE_URL}/api/v1/bazi/calculate", json_data=calc_payload, headers=BROWSER_HEADERS))

    # 4. BaZi Interpret
    interp_payload = {
        "birth_datetime": "1990-05-15 14:30:00",
        "longitude": 100.493,
        "utc_offset_hours": 7.0,
        "unknown_hour": False,
        "enable_validation": True,
        "query": "วิเคราะห์ความแข็งแกร่งของ Day Master ธาตุทอง และอาชีพการงานที่ส่งเสริมดวงชะตา"
    }
    results.append(test_endpoint("POST /api/v1/bazi/interpret Execution", "POST", f"{GATEWAY_BASE_URL}/api/v1/bazi/interpret", json_data=interp_payload, headers=BROWSER_HEADERS))

    # 5. Location Resolve
    loc_payload = {"location": "Bangkok"}
    results.append(test_endpoint("POST /api/v1/location/resolve Execution", "POST", f"{GATEWAY_BASE_URL}/api/v1/location/resolve", json_data=loc_payload, headers=BROWSER_HEADERS))

    # 6. Hugging Face Space Runtime Check
    try:
        from huggingface_hub import HfApi
        api = HfApi()
        space_info = api.space_info("pphothidaen/horoconsultant-core-backend")
        stage = getattr(space_info.runtime, "stage", "UNKNOWN")
        hf_pass = stage == "RUNNING"
        status_tag = "[OK] PASSED" if hf_pass else "[ERROR] FAILED"
        print(f"{status_tag:15} | Hugging Face Space Runtime Status        | Stage: {stage} (SDK: {space_info.sdk})")
        results.append(hf_pass)
    except Exception as e:
        print(f"{'[ERROR] FAILED':15} | Hugging Face Space Runtime Status        | {e}")
        results.append(False)

    print("=" * 80)
    passed_count = sum(1 for r in results if r)
    total_count = len(results)
    pass_rate = (passed_count / total_count) * 100
    print(f"  📊 SUMMARY: {passed_count}/{total_count} Tests Passed ({pass_rate:.1f}% Pass Rate)")
    print("=" * 80)

    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
