# Implementation Plan: Horo Lite Default Landing Page & Clean Routing

Set **Horo Lite** (`public/lite.html`) as the default landing page across Vercel production (`https://horo-consultant-psi.vercel.app/`), eliminate HTTP 404 on `/lite`, maintain `/advanced` as the entrance for the Advanced BaZi Dashboard (`public/index.html`), and uphold all existing API gateway contracts and test baselines.

---

## 1. Goal Description

Currently on Vercel production:
- Visiting the root URL `https://horo-consultant-psi.vercel.app/` serves `public/index.html` (the legacy Advanced BaZi Dashboard).
- Visiting `https://horo-consultant-psi.vercel.app/lite` returns **HTTP 404 Not Found**.
- Visiting `https://horo-consultant-psi.vercel.app/lite.html` serves Horo Lite (`public/lite.html`).

The goal is to establish Horo Lite as the default user experience:
1. Accessing root `/` opens **Horo Lite** as the default landing page.
2. Accessing `/lite` (without extension) opens **Horo Lite** (clean URL, zero 404).
3. Accessing `/lite.html` continues to serve **Horo Lite**.
4. Accessing `/advanced` serves the **Advanced BaZi Dashboard** (`public/index.html`).
5. Seamless bidirectional switching between Horo Lite and Advanced Dashboard is preserved.

---

## 2. User Review Required

> [!IMPORTANT]
> **Routing Strategy Selection (Edge Redirects vs File Swap)**:
> We recommend **Option A (Vercel Edge Redirects)**.
> - **Option A (Recommended)**: Add edge `redirects` in `vercel.json` (`/` ➔ `/lite.html` and `/lite` ➔ `/lite.html`).
>   - *Advantages*: Edge CDN handles routing instantly before static files; zero blast radius to the 15+ existing test suites asserting `public/index.html` DOM contracts; zero disruption to `project/static/index.html` parity.
> - **Option B (File Renaming)**: Swap `public/lite.html` ➔ `public/index.html` and `public/index.html` ➔ `public/advanced.html`.
>   - *Disadvantages*: High blast radius; breaks `assert static_html == public_html` and 15+ tests that inspect `public/index.html` for BaZi elements unless all those test suites are refactored.

---

## 3. Open Questions

> [!NOTE]
> **Redirect HTTP Status**:
> Option A uses HTTP 307 (Temporary Redirect, `"permanent": false`) in `vercel.json`. This ensures browser caches do not permanently lock the route, allowing instant agility for future releases.

---

## 4. Proposed Changes

### Vercel Routing Configuration

#### [MODIFY] `vercel.json`
- Add `redirects` block at top level to route `/` and `/lite` to `/lite.html`.
- Preserve existing `rewrites` array exactly intact so that `tests/api_index_vercel_contract.test.mjs` and all API gateway routes continue to pass without regression.

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "framework": null,
  "buildCommand": "",
  "outputDirectory": "public",
  "installCommand": "",
  "redirects": [
    {"source": "/", "destination": "/lite.html", "permanent": false},
    {"source": "/lite", "destination": "/lite.html", "permanent": false}
  ],
  "rewrites": [
    {"source": "/", "destination": "/lite.html"},
    {"source": "/advanced", "destination": "/index.html"},
    {"source": "/health", "destination": "/api/index?path=/health"},
    {"source": "/api/wake", "destination": "/api/index?path=/api/wake"},
    {"source": "/api/v1/:path*", "destination": "/api/index?path=/api/v1/:path*"},
    {"source": "/api/v2/:path*", "destination": "/api/index?path=/api/v2/:path*"},
    {"source": "/api/v3/:path*", "destination": "/api/index?path=/api/v3/:path*"},
    {"source": "/docs", "destination": "/api/index?path=/docs"},
    {"source": "/openapi.json", "destination": "/api/index?path=/openapi.json"},
    {"source": "/admin/auth/config", "destination": "/api/index?path=/admin/auth/config"},
    {"source": "/admin/auth/google", "destination": "/api/index?path=/admin/auth/google"},
    {"source": "/admin/catalog/summary", "destination": "/api/index?path=/admin/catalog/summary"},
    {"source": "/admin/catalog", "destination": "/api/index?path=/admin/catalog"},
    {"source": "/admin/catalog/source/:source_id", "destination": "/api/index?path=/admin/catalog/source/:source_id"},
    {"source": "/admin/grayzone", "destination": "/api/index?path=/admin/grayzone"},
    {"source": "/admin/finetune/status", "destination": "/api/index?path=/admin/finetune/status"},
    {"source": "/admin/finetune/download", "destination": "/api/index?path=/admin/finetune/download"},
    {"source": "/admin/finetune/download-grayzone", "destination": "/api/index?path=/admin/finetune/download-grayzone"},
    {"source": "/admin/provider-pools", "destination": "/api/index?path=/admin/provider-pools"},
    {"source": "/hitl/stats", "destination": "/api/index?path=/hitl/stats"}
  ],
  "github": {"silent": true, "autoAlias": false, "deploymentEnabled": {"*": false, "main": true}}
}
```

---

### Regression Test Suite

#### [MODIFY] `tests/test_kan120_default_page_horo_lite.py`
- Add unit assertions for the new `redirects` block in `vercel.json`.

```python
def test_vercel_redirects_root_and_lite():
    """Verify vercel.json redirects / and /lite to /lite.html."""
    vercel_path = ROOT / "vercel.json"
    assert vercel_path.exists()
    config = json.loads(vercel_path.read_text(encoding="utf-8"))
    redirects = config.get("redirects", [])
    redirect_map = {r.get("source"): r.get("destination") for r in redirects}
    assert redirect_map.get("/") == "/lite.html", "vercel.json missing redirect for '/' -> '/lite.html'"
    assert redirect_map.get("/lite") == "/lite.html", "vercel.json missing redirect for '/lite' -> '/lite.html'"
```

---

## 5. Verification Plan

### Automated Tests
1. **KAN-120 Default Page Suite**:
   ```bash
   python3 -m pytest tests/test_kan120_default_page_horo_lite.py -v
   ```
2. **Node.js Vercel Gateway & Ingress Contract Tests**:
   ```bash
   node --test tests/*.test.mjs
   ```
   (Must achieve 76/76 PASS)
3. **AI Agent Ecosystem & Platform Sync**:
   ```bash
   python3 scripts/sync_ai_agent_ecosystem.py --check
   ```
4. **Git Branch & Provenance Verification**:
   ```bash
   python3 scripts/test_provenance_guard.py verify-pr --base origin/main --head HEAD
   ```

### Post-Deployment Verification (via Kapture MCP)
1. **HTTP Probe**:
   - `curl -sI https://horo-consultant-psi.vercel.app/` ➔ HTTP 307 to `/lite.html`
   - `curl -sI https://horo-consultant-psi.vercel.app/lite` ➔ HTTP 307 to `/lite.html`
   - `curl -sI https://horo-consultant-psi.vercel.app/lite.html` ➔ HTTP 200 OK (Horo Lite)
   - `curl -sI https://horo-consultant-psi.vercel.app/advanced` ➔ HTTP 200 OK (Advanced Dashboard)
2. **Kapture MCP Visual Verification**:
   - Navigate tab to `https://horo-consultant-psi.vercel.app/` and confirm Horo Lite renders.
   - Click "⚙️ แดชบอร์ดขั้นสูง (Advanced Dashboard) →" and confirm navigation to `/advanced`.
   - Click "✨ Horo Lite" and confirm navigation back to `/`.
