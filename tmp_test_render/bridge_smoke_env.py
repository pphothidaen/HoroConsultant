"""Bridge endpoint smoke test — reads token from env var BRIDGE_TEST_TOKEN."""
import httpx, json, time, os

token = os.environ.get("BRIDGE_TEST_TOKEN", "")
if not token:
    print(json.dumps({"error": "BRIDGE_TEST_TOKEN not set"}))
    exit(1)

url = "https://gemini-web-bridge.pansakorn-pho.workers.dev/mcp"
scope = "notebook:b55f1ee0-384e-4bdf-ab1b-e2ee3b0063a0"

payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "horo_consult",
        "arguments": {
            "query": "ทดสอบการเชื่อมต่อ bridge endpoint",
            "response_format": "text",
            "scope": scope,
        },
    },
}

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}

t0 = time.monotonic()
result = {}
try:
    r = httpx.post(url, json=payload, headers=headers, timeout=30.0)
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
            result["body_preview"] = r.text[:500]
        elif "error" in data:
            result["jsonrpc_error"] = data["error"]
            result["body_preview"] = r.text[:300]
        else:
            result["jsonrpc_valid"] = False
            result["jsonrpc_keys"] = list(data.keys())
            result["body_preview"] = r.text[:300]
    except Exception as exc:
        result["json_parse_error"] = str(exc)
        result["body_preview"] = r.text[:300]
except Exception as e:
    elapsed = round((time.monotonic() - t0) * 1000)
    result["error"] = f"{type(e).__name__}: {e}"
    result["elapsed_ms"] = elapsed

print(json.dumps(result, indent=2, ensure_ascii=False))
