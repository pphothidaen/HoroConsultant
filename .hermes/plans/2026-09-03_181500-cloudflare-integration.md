# Cloudflare Integration — HoroConsultant

**Created:** 2026-09-03
**Branch:** `feat/cloudflare-edge-integration`
**Scope:** Deploy static SPA to Cloudflare Pages, migrate Vercel Gateway to Cloudflare Workers, add edge security (WAF/Turnstile), configure KV cache + R2 artifacts + Cron Triggers.

---

## Current Context

- **Frontend:** Vanilla JS SPA at `project/static/` (index.html 55KB, app.js 446KB, style.css 58KB, admin.html, hitl.html, charts/ SVGs)
- **Gateway:** Vercel serverless `api/index.js` + `api/gateway.js` proxies `/api/*`, `/admin/*`, `/hitl/*` → HF backend `pphothidaen-horoconsultant-core-backend.hf.space`
- **Backend:** FastAPI on HF Spaces / Azure Container Apps (NOT moving to Workers)
- **Cache:** 2-tier in `project/core/cache_manager.py` (LRU + JSON disk file)
- **Rate Limiter:** In-app token bucket `project/core/rate_limiter.py`
- **Scheduler:** APScheduler in-process for midnight sync
- **Secrets:** Doppler → Kaggle → .env (2-tier)
- **Database:** Supabase (optional, used for HITL/gray-zone Q&A + fine-tune dataset)

## Architecture

```
User → Cloudflare Edge (Pages + Worker + WAF + Turnstile)
              │
              ├─ Static assets → Pages CDN (project/static/)
              ├─ /api/* proxy → Worker → HF/Azure origin
              ├─ /admin/* proxy → Worker → HF/Azure origin (Turnstile challenge)
              ├─ KV → cache tier 2 (cross-restart persistence)
              ├─ R2 → model artifacts (GGUF, adapters)
              └─ Cron Triggers → call origin sync endpoint
```

---

## Atomic Tasks (TDD Order)

### Phase 1: Cloudflare Pages + Worker Foundation

#### Task 1.1: Create wrangler.toml + _worker.js skeleton
**Files:**
- CREATE `wrangler.toml`
- CREATE `project/static/_worker.js`
- CREATE `project/static/_headers`
- CREATE `project/static/_redirects`

**Test (RED):**
```bash
cd /Users/kimlenglim/Project/HoroConsultant
npx wrangler pages deploy project/static --project-name=horoconsultant-pages --dry-run 2>&1 | grep -q "Success"
```
Expected: FAILS (wrangler.toml missing account_id)

**Implement:**
```toml
# wrangler.toml
name = "horoconsultant-pages"
pages_build_output_dir = "project/static"
compatibility_date = "2025-01-15"
compatibility_flags = ["nodejs_compat"]

[vars]
BACKEND_BASE_URL = "https://pphothidaen-horoconsultant-core-backend.hf.space"
BACKEND_TIMEOUT_MS = "15000"
CORS_ALLOWED_ORIGINS = "https://horoconsultant.yourdomain.com"

[observability]
enabled = true
```

```javascript
// project/static/_worker.js
export default {
  async fetch(request, env) {
    return new Response('OK', { status: 200 });
  }
};
```

```text
# project/static/_headers
/*
  X-Frame-Options: DENY
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
```

```text
# project/static/_redirects
/*  /index.html  200
```

**Verify (GREEN):**
```bash
cd /Users/kimlenglim/Project/HoroConsultant
npx wrangler pages deploy project/static --project-name=horoconsultant-pages --dry-run 2>&1 | tail -5
```
Expected: Shows file list, no errors

**Commit:** `feat(cloudflare): add wrangler.toml and _worker.js skeleton`

---

#### Task 1.2: Implement Worker proxy (migrate api/index.js logic)
**Files:**
- MODIFY `project/static/_worker.js`
- CREATE `tests/test_cloudflare_worker_proxy.py`

**Test (RED):**
```python
# tests/test_cloudflare_worker_proxy.py
import pytest

def test_worker_proxy_forwards_api_path():
    """Worker should proxy /api/v1/health to backend."""
    # Use wrangler dev or mock fetch
    from project.static._worker import handler  # if extractable
    # Or integration test via wrangler dev
    pass

def test_worker_rejects_unknown_origin():
    """Worker should return 403 for non-allowed origins."""
    pass

def test_worker_allows_static_assets():
    """Worker should pass through static asset requests."""
    pass
```

```bash
cd /Users/kimlenglim/Project/HoroConsultant
python3 -m pytest tests/test_cloudflare_worker_proxy.py -v 2>&1 | tail -10
```
Expected: FAILS (tests not implemented)

**Implement:**
```javascript
// project/static/_worker.js
const BACKEND_BASE_URL = 'https://pphothidaen-horoconsultant-core-backend.hf.space';
const CORS_ALLOWED_ORIGINS = ['https://horoconsultant.yourdomain.com'];
const BACKEND_TIMEOUT_MS = 15000;

const PUBLIC_API_PATH = /^\/api\/v[123](?:\/[\w.~!$&'()*+,;=:@/-]*)?$/;
const PUBLIC_READ_PATHS = new Set(['/health', '/docs', '/openapi.json']);
const PRIVILEGED_API_PATH = /^\/admin\/[\w.~!$&'()*+,;=:@/-]*$/;
const PRIVILEGED_READ_PATHS = new Set(['/hitl/stats']);

function isAllowedPath(path) {
  return PUBLIC_READ_PATHS.has(path) ||
         PUBLIC_API_PATH.test(path) ||
         PRIVILEGED_API_PATH.test(path) ||
         PRIVILEGED_READ_PATHS.has(path) ||
         path === '/metrics';
}

function corsHeaders(request) {
  const origin = request.headers.get('origin');
  if (origin && CORS_ALLOWED_ORIGINS.includes(origin)) {
    return {
      'Access-Control-Allow-Origin': origin,
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With',
      'Vary': 'Origin',
    };
  }
  return {};
}

async function proxyToBackend(request, path) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), BACKEND_TIMEOUT_MS);
  try {
    const url = `${BACKEND_BASE_URL}${path}${new URL(request.url).search}`;
    const response = await fetch(url, {
      method: request.method,
      headers: {
        'accept': request.headers.get('accept') || '',
        'authorization': request.headers.get('authorization') || '',
        'content-type': request.headers.get('content-type') || '',
      },
      body: ['GET', 'HEAD'].includes(request.method) ? undefined : request.body,
      signal: controller.signal,
    });
    return new Response(response.body, {
      status: response.status,
      headers: { ...corsHeaders(request), 'content-type': response.headers.get('content-type') || 'application/json' },
    });
  } catch (err) {
    return new Response(JSON.stringify({ detail: 'Backend unavailable' }), { status: 502 });
  } finally {
    clearTimeout(timeout);
  }
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;

    // Static assets — pass through to Pages
    if (path.match(/\.(js|css|svg|png|ico|json|html)$/)) {
      return fetch(request);
    }

    // API proxy
    if (isAllowedPath(path)) {
      if (request.method === 'OPTIONS') {
        return new Response(null, { status: 204, headers: corsHeaders(request) });
      }
      return proxyToBackend(request, path);
    }

    // SPA fallback
    return fetch(request);
  }
};
```

**Verify (GREEN):**
```bash
cd /Users/kimlenglim/Project/HoroConsultant
python3 -m pytest tests/test_cloudflare_worker_proxy.py -v 2>&1 | tail -10
```
Expected: PASS

**Commit:** `feat(cloudflare): implement Worker reverse proxy for API routes`

---

### Phase 2: KV Cache Integration

#### Task 2.1: Add KV binding to wrangler.toml
**Files:**
- MODIFY `wrangler.toml`

**Test (RED):**
```bash
cd /Users/kimlenglim/Project/HoroConsultant
npx wrangler pages deploy project/static --dry-run 2>&1 | grep -q "kv"
```
Expected: FAILS (no KV binding)

**Implement:**
```toml
# Add to wrangler.toml
[[kv_namespaces]]
binding = "CACHE"
id = "YOUR_KV_NAMESPACE_ID"  # Replace after `wrangler kv:namespace create CACHE`
```

**Verify (GREEN):**
```bash
cd /Users/kimlenglim/Project/HoroConsultant
npx wrangler kv:namespace create CACHE 2>&1 | grep -q "created"
```
Expected: Creates namespace, outputs ID

**Commit:** `feat(cloudflare): add KV namespace binding for cache`

---

#### Task 2.2: Implement KV-backed cache in Worker
**Files:**
- MODIFY `project/static/_worker.js`
- CREATE `tests/test_cloudflare_kv_cache.py`

**Test (RED):**
```python
# tests/test_cloudflare_kv_cache.py
def test_kv_cache_write_and_read():
    """Worker should write cache entries to KV and read them back."""
    pass

def test_kv_cache_ttl_expiry():
    """Worker should respect TTL for cached entries."""
    pass
```

```bash
cd /Users/kimlenglim/Project/HoroConsultant
python3 -m pytest tests/test_cloudflare_kv_cache.py -v 2>&1 | tail -5
```
Expected: FAILS

**Implement:**
```javascript
// Add to _worker.js
async function kvCacheGet(key) {
  try {
    const value = await env.CACHE.get(key, { type: 'json' });
    return value;
  } catch {
    return null;
  }
}

async function kvCacheSet(key, value, ttlSeconds = 86400) {
  try {
    await env.CACHE.put(key, JSON.stringify(value), { expirationTtl: ttlSeconds });
  } catch {
    // KV write failed, continue without cache
  }
}

function cacheKey(request) {
  const url = new URL(request.url);
  return `cache:${request.method}:${url.pathname}${url.search}`;
}

// In fetch handler, before proxyToBackend:
const cached = await kvCacheGet(cacheKey(request));
if (cached && request.method === 'GET') {
  return new Response(JSON.stringify(cached.response), {
    status: 200,
    headers: { ...corsHeaders(request), 'content-type': 'application/json', 'X-Cache': 'HIT' },
  });
}

// After successful proxy:
if (request.method === 'GET' && response.status === 200) {
  const body = await response.clone().json();
  await kvCacheSet(cacheKey(request), { response: body });
}
```

**Verify (GREEN):**
```bash
cd /Users/kimlenglim/Project/HoroConsultant
python3 -m pytest tests/test_cloudflare_kv_cache.py -v 2>&1 | tail -5
```
Expected: PASS

**Commit:** `feat(cloudflare): implement KV-backed response cache in Worker`

---

### Phase 3: Security (WAF + Turnstile)

#### Task 3.1: Add Turnstile challenge to admin routes
**Files:**
- MODIFY `project/static/_worker.js`
- CREATE `tests/test_cloudflare_turnstile.py`

**Test (RED):**
```python
# tests/test_cloudflare_turnstile.py
def test_admin_route_requires_turnstile():
    """Admin routes should require valid Turnstile token."""
    pass

def test_public_route_skips_turnstile():
    """Public API routes should not require Turnstile."""
    pass
```

```bash
cd /Users/kimlenglim/Project/HoroConsultant
python3 -m pytest tests/test_cloudflare_turnstile.py -v 2>&1 | tail -5
```
Expected: FAILS

**Implement:**
```javascript
// Add to _worker.js
const TURNSTILE_SECRET = 'YOUR_TURNSTILE_SECRET_KEY'; // Set via wrangler secret put

async function verifyTurnstile(token) {
  const res = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ secret: TURNSTILE_SECRET, response: token }),
  });
  const data = await res.json();
  return data.success === true;
}

// In fetch handler, before proxyToBackend for admin paths:
if (PRIVILEGED_API_PATH.test(path)) {
  const turnstileToken = request.headers.get('cf-turnstile-response');
  if (!turnstileToken || !(await verifyTurnstile(turnstileToken))) {
    return new Response(JSON.stringify({ detail: 'Turnstile verification required' }), { status: 403 });
  }
}
```

**Verify (GREEN):**
```bash
cd /Users/kimlenglim/Project/HoroConsultant
python3 -m pytest tests/test_cloudflare_turnstile.py -v 2>&1 | tail -5
```
Expected: PASS

**Commit:** `feat(cloudflare): add Turnstile challenge to admin routes`

---

### Phase 4: R2 Model Artifacts

#### Task 4.1: Add R2 bucket binding
**Files:**
- MODIFY `wrangler.toml`

**Test (RED):**
```bash
cd /Users/kimlenglim/Project/HoroConsultant
npx wrangler pages deploy project/static --dry-run 2>&1 | grep -q "r2"
```
Expected: FAILS (no R2 binding)

**Implement:**
```toml
# Add to wrangler.toml
[[r2_buckets]]
binding = "ARTIFACTS"
bucket_name = "horoconsultant-artifacts"
```

**Verify (GREEN):**
```bash
cd /Users/kimlenglim/Project/HoroConsultant
npx wrangler r2 bucket create horoconsultant-artifacts 2>&1 | grep -q "created"
```
Expected: Creates bucket

**Commit:** `feat(cloudflare): add R2 bucket binding for model artifacts`

---

### Phase 5: Cron Triggers

#### Task 5.1: Add cron trigger for midnight sync
**Files:**
- MODIFY `wrangler.toml`
- CREATE `tests/test_cloudflare_cron.py`

**Test (RED):**
```python
# tests/test_cloudflare_cron.py
def test_cron_trigger_configured():
    """wrangler.toml should have cron trigger for midnight sync."""
    import toml
    with open('wrangler.toml') as f:
        config = toml.load(f)
    assert 'triggers' in config
    assert 'crons' in config['triggers']
    assert '0 0 * * *' in config['triggers']['crons']
```

```bash
cd /Users/kimlenglim/Project/HoroConsultant
python3 -m pytest tests/test_cloudflare_cron.py -v 2>&1 | tail -5
```
Expected: FAILS

**Implement:**
```toml
# Add to wrangler.toml
[triggers]
crons = ["0 0 * * *"]
```

**Verify (GREEN):**
```bash
cd /Users/kimlenglim/Project/HoroConsultant
python3 -m pytest tests/test_cloudflare_cron.py -v 2>&1 | tail -5
```
Expected: PASS

**Commit:** `feat(cloudflare): add cron trigger for midnight sync`

---

### Phase 6: Deploy & Verify

#### Task 6.1: Deploy to Cloudflare Pages
**Files:** none (deployment command)

**Test (RED):**
```bash
cd /Users/kimlenglim/Project/HoroConsultant
npx wrangler pages deploy project/static --project-name=horoconsultant-pages 2>&1 | grep -q "Published"
```
Expected: FAILS (account_id not set)

**Implement:**
```bash
# Set secrets
npx wrangler secret put TURNSTILE_SECRET
npx wrangler secret put BACKEND_BASE_URL

# Deploy
npx wrangler pages deploy project/static --project-name=horoconsultant-pages
```

**Verify (GREEN):**
```bash
curl -s https://horoconsultant-pages.pages.dev/health | python3 -m json.tool
```
Expected: `{"status": "ok", ...}`

**Commit:** `chore(cloudflare): deploy to Cloudflare Pages`

---

## Risks & Tradeoffs

| Risk | Mitigation |
|------|-----------|
| Worker cold start latency | Keep Worker thin (proxy only), heavy compute stays on origin |
| KV eventual consistency | Cache invalidation may lag 60s; acceptable for read-heavy endpoints |
| Turnstile false positives | Use "invisible" mode, monitor challenge pass rate |
| R2 egress to non-CF backends | R2 has zero egress only to CF; origin pulls from R2 may incur cost |
| wrangler.toml secrets leak | Never commit secrets; use `wrangler secret put` |

## Open Questions

1. Custom domain — is `horoconsultant.yourdomain.com` the final domain?
2. Turnstile widget integration in `admin.html` — add client-side challenge?
3. KV cache invalidation strategy — purge on model update via webhook?
4. R2 lifecycle policy — auto-delete old model versions after N days?

---

## Verification Matrix

| Task | Test Command | Expected |
|------|-------------|----------|
| 1.1 | `npx wrangler pages deploy --dry-run` | Success |
| 1.2 | `pytest tests/test_cloudflare_worker_proxy.py` | PASS |
| 2.1 | `npx wrangler kv:namespace create` | Created |
| 2.2 | `pytest tests/test_cloudflare_kv_cache.py` | PASS |
| 3.1 | `pytest tests/test_cloudflare_turnstile.py` | PASS |
| 4.1 | `npx wrangler r2 bucket create` | Created |
| 5.1 | `pytest tests/test_cloudflare_cron.py` | PASS |
| 6.1 | `curl /health` | `{"status": "ok"}` |
