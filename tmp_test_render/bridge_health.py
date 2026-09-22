"""Check bridge endpoint health/info endpoints (no auth needed)."""
import httpx
import json

base = "https://gemini-web-bridge.pansakorn-pho.workers.dev"
paths = ["", "/", "/health", "/mcp", "/info", "/version"]

results = {}
for path in paths:
    url = base + path
    # GET
    try:
        r = httpx.get(url, timeout=10.0, headers={"Accept": "application/json"})
        results[f"GET {path}"] = {"status": r.status_code, "body": r.text[:200]}
    except Exception as e:
        results[f"GET {path}"] = {"error": f"{type(e).__name__}: {e}"}
    # POST to /mcp with tools/list (no auth)
    if path == "/mcp" or path == "":
        post_url = base + "/mcp" if path != "/mcp" else base + path
        try:
            r = httpx.post(
                post_url,
                json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
                timeout=10.0,
                headers={"Content-Type": "application/json", "Accept": "application/json"},
            )
            results[f"POST {post_url}"] = {"status": r.status_code, "body": r.text[:200]}
        except Exception as e:
            results[f"POST {post_url}"] = {"error": f"{type(e).__name__}: {e}"}

print(json.dumps(results, indent=2, ensure_ascii=False))
