"""Production smoke test for the Gemini Web Bridge endpoint.

Loads the bridge token from .env (synced from gemini-web-bridge/CLIENT_API_TOKEN)
and sends a single tools/call JSON-RPC request to verify the endpoint responds
correctly — not just a 401.
"""
from __future__ import annotations

import json
import os
import sys
import time

import httpx

# Load token from .env file (same source as the production sync note)
_token = None
_env_path = "/Users/kimlenglim/Project/HoroConsultant/.env"
_root = "/Users/kimlenglim/Project/HoroConsultant"
with open(_env_path) as f:
    for line in f:
        if line.startswith("GEMINI_WEB_BRIDGE_TOKEN="):
            _token = line.strip().split("=", 1)[1]
            break

if not _token:
    print(json.dumps({"error": "GEMINI_WEB_BRIDGE_TOKEN not found in .env"}))
    sys.exit(1)

url = os.path.join(os.path.dirname(__file__), "..", ".env")
# Read URL and scope from .env as well
_bridge_url = "https://gemini-web-bridge.pansakorn-pho.workers.dev"
_scope = "notebook:b55f1ee0-384e-4bdf-ab1b-e2ee3b0063a0"
with open(os.path.join(_root, ".env"), "r") as f:
    for line in f:
        line = line.strip()
        if line.startswith("GEMINI_WEB_BRIDGE_URL="):
            _bridge_url = line.split("=", 1)[1]
        elif line.startswith("GEMINI_WEB_BRIDGE_SCOPE="):
            _scope = line.split("=", 1)[1]

payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "horo_consult",
        "arguments": {
            "query": "ทดสอบการเชื่อมต่อ bridge endpoint",
            "response_format": "text",
            "scope": _scope,
        },
    },
}

headers = {
    "Authorization": f"Bearer {_token}",
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}

endpoint = f"{_bridge_url.rstrip('/')}/mcp"
t0 = time.monotonic()
result = {}

try:
    r = httpx.post(endpoint, json=payload, headers=headers, timeout=30.0)
    elapsed = round((time.monotonic() - t0) * 1000)
    result["http_status"] = r.status_code
    result["elapsed_ms"] = elapsed
    result["content_type"] = r.headers.get("content-type", "")

    try:
        data = r.json()
        result["jsonrpc"] = data.get("jsonrpc")
        result["has_result"] = "result" in data
        result["has_error"] = "error" in data

        if "result" in data:
            res = data["result"]
            content = res.get("content", [])
            text_found = False
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text_found = True
                        result["response_text"] = item.get("text", "")[:200]
                        break
            result["content_items"] = len(content) if isinstance(content, list) else 0
            result["text_extracted"] = text_found
            result["structured_content"] = "structuredContent" in res
            result["jsonrpc_valid"] = True
        elif "error" in data:
            result["jsonrpc_error"] = data["error"]
        else:
            result["jsonrpc_valid"] = False
            result["jsonrpc_keys"] = list(data.keys())

        result["body_preview"] = r.text[:300]
    except Exception as exc:
        result["json_parse_error"] = str(exc)
        result["body_preview"] = r.text[:300]

except httpx.ConnectError as e:
    elapsed = round((time.monotonic() - t0) * 1000)
    result["error"] = f"ConnectError: {e}"
    result["elapsed_ms"] = elapsed
except httpx.TimeoutException:
    elapsed = round((time.monotonic() - t0) * 1000)
    result["error"] = "TimeoutException"
    result["elapsed_ms"] = elapsed
except Exception as e:
    elapsed = round((time.monotonic() - t0) * 1000)
    result["error"] = f"{type(e).__name__}: {e}"
    result["elapsed_ms"] = elapsed

print(json.dumps(result, indent=2, ensure_ascii=False))
