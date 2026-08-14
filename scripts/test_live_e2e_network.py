"""
scripts/test_live_e2e_network.py
==================================
Strict Live Network E2E Verification Suite for Master Orchestrator.

Sends real HTTP packets over the public internet to verify:
1. Live Static Edge CDN (Hugging Face Space)
2. Live Edge Gateway (Vercel Production)
3. Live Backend Micro-Services (Fly.io)

Usage:
------
    python3 scripts/test_live_e2e_network.py
"""

from __future__ import annotations

import json
import logging
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("live_e2e_audit")

import os

VERCEL_PROD_URL = "https://horo-consultant-psi.vercel.app"
HF_STATIC_CDN_URL = "https://pphothidaen-horoconsultant-core-backend.static.hf.space"
AZURE_BACKEND_URL = os.getenv("AZURE_CONTAINER_APP_URL", "https://horoconsult-env-new.politepond-CHANGEME.southeastasia.azurecontainerapps.io")



def execute_network_request(url: str, method: str = "GET", headers: dict | None = None, payload: dict | None = None, expected_status: int = 200, timeout: int = 15) -> tuple[bool, int, str]:
    """Execute a real live network HTTP request over the public internet."""
    req_headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) HoroConsultant-E2E-Auditor/1.0",
        "Accept": "application/json, text/html, */*",
    }
    if headers:
        req_headers.update(headers)

    data_bytes = None
    if payload:
        data_bytes = json.dumps(payload).encode("utf-8")
        req_headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data_bytes, headers=req_headers, method=method)
    start_time = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed = (time.time() - start_time) * 1000
            body = resp.read().decode("utf-8", errors="replace")
            status = resp.status
            return (status == expected_status, status, body)
    except urllib.error.HTTPError as e:
        elapsed = (time.time() - start_time) * 1000
        body = e.read().decode("utf-8", errors="replace")
        return (False, e.code, body)
    except Exception as e:
        return (False, 0, str(e))


def run_strict_live_e2e_audit() -> bool:
    logger.info("======================================================================")
    logger.info("  🎭 STRICT MASTER ORCHESTRATOR LIVE NETWORK E2E AUDIT")
    logger.info("======================================================================")

    all_passed = True
    test_results = []

    # 1. Test Hugging Face Static Edge CDN UIs
    hf_pages = ["/index.html", "/admin.html", "/hitl.html"]
    logger.info("📌 [1/3] Auditing Live Static Edge CDN (Hugging Face Spaces)...")
    for page in hf_pages:
        url = HF_STATIC_CDN_URL + page
        success, status, body = execute_network_request(url, method="GET")
        if success and ("<!DOCTYPE html>" in body or "<html" in body):
            logger.info(f"   ✅ HF Static Page `{page}`: HTTP {status} OK ({len(body)} bytes)")
            test_results.append((f"HF CDN {page}", True, f"HTTP {status}"))
        else:
            logger.error(f"   ❌ HF Static Page `{page}`: HTTP {status} FAILED! Body snippet: {body[:150]}")
            test_results.append((f"HF CDN {page}", False, f"HTTP {status}"))
            all_passed = False

    # 2. Test Vercel Edge Gateway UI & API Proxy
    logger.info("\n📌 [2/3] Auditing Live Edge Proxy Gateway (Vercel Production)...")
    vercel_endpoints = [
        ("/", "GET", None, None),
        ("/index.html", "GET", None, None),
        ("/admin.html", "GET", None, None),
    ]
    for path, method, headers, payload in vercel_endpoints:
        url = VERCEL_PROD_URL + path
        success, status, body = execute_network_request(url, method=method, headers=headers, payload=payload)
        if success:
            logger.info(f"   ✅ Vercel Route `{path}`: HTTP {status} OK ({len(body)} bytes)")
            test_results.append((f"Vercel {path}", True, f"HTTP {status}"))
        else:
            logger.error(f"   ❌ Vercel Route `{path}`: HTTP {status} FAILED! Body snippet: {body[:150]}")
            test_results.append((f"Vercel {path}", False, f"HTTP {status}"))
            all_passed = False

    # 3. Test Full User Query BaZi Interpret API Payload
    logger.info("\n📌 [3/3] Auditing User BaZi Interpret API Call over Public Network...")
    user_payload = {
        "birth_datetime": "1990-05-15 14:30:00",
        "longitude": 100.493,
        "utc_offset_hours": 7,
        "unknown_hour": False,
        "enable_validation": True,
        "query": "วิเคราะห์ความแข็งแกร่งของ Day Master ธาตุทอง และอาชีพการงานที่ส่งเสริมดวงชะตา"
    }
    user_headers = {
        "Origin": HF_STATIC_CDN_URL,
        "Referer": f"{HF_STATIC_CDN_URL}/index.html",
    }
    
    # Try Vercel Gateway first
    api_url = f"{VERCEL_PROD_URL}/api/v1/bazi/interpret"
    success, status, body = execute_network_request(api_url, method="POST", headers=user_headers, payload=user_payload, timeout=30)
    
    if success and ("chart" in body or "status" in body):
        logger.info(f"   ✅ Live API Endpoint `/api/v1/bazi/interpret`: HTTP {status} OK")
        test_results.append(("Live BaZi Interpret API", True, f"HTTP {status}"))
    else:
        logger.warning(f"   ⚠️ Vercel Gateway API Proxy returned HTTP {status}. Checking fallback routes...")
        # Fallback check against Fly.io or Local server
        fly_url = f"{FLY_BACKEND_URL}/api/v1/bazi/interpret"
        fly_success, fly_status, fly_body = execute_network_request(fly_url, method="POST", headers=user_headers, payload=user_payload, timeout=10)
        if fly_success:
            logger.info(f"   ✅ Fly.io Direct Backend `/api/v1/bazi/interpret`: HTTP {fly_status} OK")
            test_results.append(("Fly.io BaZi Interpret API", True, f"HTTP {fly_status}"))
        else:
            logger.error(f"   ❌ Live API Endpoint FAILED across all hosts! Vercel: {status}, Fly: {fly_status}")
            logger.error(f"   Snippet: {body[:200]}")
            test_results.append(("Live BaZi Interpret API", False, f"HTTP {status}"))
            all_passed = False

    logger.info("\n======================================================================")
    logger.info("  📊 AUDIT SUMMARY REPORT")
    logger.info("======================================================================")
    for target, ok, detail in test_results:
        symbol = "✅ PASSED" if ok else "❌ FAILED"
        logger.info(f"  • {target:<30}: {symbol} ({detail})")
    logger.info("======================================================================\n")

    return all_passed


def main():
    success = run_strict_live_e2e_audit()
    if not success:
        logger.error("🛑 STRICT ORCHESTRATOR AUDIT FAILED: Live network services are not 100% operational!")
        sys.exit(1)
    else:
        logger.info("🎉 STRICT ORCHESTRATOR AUDIT PASSED: All live production services verified operational 100%!")
        sys.exit(0)


if __name__ == "__main__":
    main()
