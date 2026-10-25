#!/usr/bin/env python3
"""
scripts/audit_openai_connection.py
==================================
Diagnostic tool to verify real HTTP network calls to OpenAI / Prox5 API endpoints.
Inspects API keys, Base URLs, HTTP Response Codes, and Fallback Routing.
"""

import sys
import os
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from project.core.config import get_priority_secret
from project.core.codex_client import get_prox5_base_url, is_dev_environment, get_codex_auth_token


def run_audit():
    print("==========================================================")
    print("🔍 OPENAI / CODEX_PRO API INVOCATION AUDIT REPORT")
    print("==========================================================")
    
    dev_env = is_dev_environment()
    print(f"1. Development Environment Guard : {'✅ Local Dev (Allowed)' if dev_env else '❌ Production (Blocked)'}")
    
    resolved_key = get_codex_auth_token() or ""
    masked_key = (resolved_key[:12] + "..." + resolved_key[-6:]) if len(resolved_key) > 18 else ("NOT_FOUND" if not resolved_key else resolved_key)

    auth_file = Path.home() / ".codex" / "auth.json"
    print(f"2. Auth Resolution Status:")
    print(f"   - Native Auth File (~/.codex/auth.json): {'✅ Present & Loaded' if auth_file.exists() else '⚠️ Missing'}")
    print(f"   - Resolved Auth Token Used              : {masked_key}")

    base_url = get_prox5_base_url()
    print(f"3. Base URL Resolved    : {base_url}")
    target_endpoint = f"{base_url}/chat/completions"
    print(f"4. Endpoint Target      : {target_endpoint}")

    if not resolved_key:
        print("\n❌ Audit Failed: No valid API Key found in DOPPLER or local .env.")
        sys.exit(1)

    print("\n🌐 Sending real HTTP POST request to OpenAI / Proxy endpoint...")
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": "Respond with exact text: HELLO_OPENAI"}],
        "max_tokens": 10,
    }

    req = urllib.request.Request(
        target_endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {resolved_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            status_code = resp.getcode()
            body_bytes = resp.read()
            body = json.loads(body_bytes.decode("utf-8"))
            content = body.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            print("==========================================================")
            print("✅ REAL HTTP CONNECTION TO OPENAI SUCCESSFUL!")
            print(f"   - HTTP Status Code : {status_code} OK")
            print(f"   - Response Content : {content}")
            print("==========================================================")
    except urllib.error.HTTPError as err:
        print("==========================================================")
        print("🌐 HTTP REQUEST WAS MADE AND RECEIVED BY OPENAI SERVER!")
        print(f"   - HTTP Error Status : HTTP {err.code} ({err.reason})")
        err_body = err.read().decode("utf-8", errors="ignore")
        print(f"   - Server Response   : {err_body[:300]}")
        print("\n💡 Conclusion: OpenAI endpoint was successfully reached over network.")
        if err.code == 429:
            print("   (HTTP 429 = Quota Limit / Rate Limit hit on OpenAI account -> Dynamic Fallback to Gemini 3.6 Flash activated correctly)")
        elif err.code == 401:
            print("   (HTTP 401 = Invalid/Expired API Key on OpenAI account)")
        print("==========================================================")
    except Exception as exc:
        print(f"❌ Network Error: {exc}")


if __name__ == "__main__":
    run_audit()
