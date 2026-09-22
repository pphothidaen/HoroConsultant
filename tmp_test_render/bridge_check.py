import httpx, json, time

results = {}

# 1. Bridge health (no auth)
t0 = time.monotonic()
try:
    r = httpx.get("https://gemini-web-bridge.pansakorn-pho.workers.dev", timeout=15.0)
    elapsed = round((time.monotonic()-t0)*1000)
    results["bridge_health"] = {
        "method": "GET",
        "path": "/",
        "http_status": r.status_code,
        "elapsed_ms": elapsed,
        "content_type": r.headers.get("content-type", ""),
    }
    try:
        results["bridge_health"]["body"] = r.json()
    except:
        results["bridge_health"]["body"] = r.text[:500]
except Exception as e:
    elapsed = round((time.monotonic()-t0)*1000)
    results["bridge_health"] = {"error": f"{type(e).__name__}: {e}", "elapsed_ms": elapsed}

# 2. Bridge /mcp POST without auth
t0 = time.monotonic()
try:
    r = httpx.post(
        "https://gemini-web-bridge.pansakorn-pho.workers.dev/mcp",
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "horo_consult", "arguments": {"query": "test", "response_format": "text", "scope": "notebook:b55f1ee0-384e-4bdf-ab1b-e2ee3b0063a0"}}},
        timeout=15.0,
        headers={"Authorization": "Bearer test", "Content-Type": "application/json", "Accept": "application/json, text/event-stream"},
    )
    elapsed = round((time.monotonic()-t0)*1000)
    results["bridge_mcp_no_auth"] = {
        "method": "POST",
        "path": "/mcp",
        "http_status": r.status_code,
        "elapsed_ms": elapsed,
        "content_type": r.headers.get("content-type", ""),
    }
    try:
        results["bridge_mcp_no_auth"]["body"] = r.json()
    except:
        results["bridge_mcp_no_auth"]["body"] = r.text[:500]
except Exception as e:
    elapsed = round((time.monotonic()-t0)*1000)
    results["bridge_mcp_no_auth"] = {"error": f"{type(e).__name__}: {e}", "elapsed_ms": elapsed}

# 3. Production endpoint
t0 = time.monotonic()
try:
    r = httpx.get("https://horoconsultant.onrender.com", timeout=20.0, follow_redirects=True)
    elapsed = round((time.monotonic()-t0)*1000)
    results["prod_root"] = {
        "http_status": r.status_code,
        "elapsed_ms": elapsed,
        "headers": dict(r.headers),
        "body": r.text[:500],
    }
except Exception as e:
    elapsed = round((time.monotonic()-t0)*1000)
    results["prod_root"] = {"error": f"{type(e).__name__}: {e}", "elapsed_ms": elapsed}

with open("/Users/kimlenglim/Project/HoroConsultant/tmp_test_render/bridge_health_result.json", "w") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(json.dumps(results, indent=2, ensure_ascii=False))
