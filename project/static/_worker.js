const RENDER_BACKEND_URL = 'https://horoconsultant-core-backend.onrender.com';
const HF_FALLBACK_URL = 'https://pphothidaen-horoconsultant-core-backend.hf.space';
const VERCEL_FALLBACK_ORIGIN = 'https://horo-consultant-psi.vercel.app';
const CORS_ALLOWED_ORIGINS = [
  'https://horo-consultant-psi.vercel.app',
  'https://horoconsultant-pages.pages.dev',
];
const BACKEND_TIMEOUT_MS = 15000;
const TURNSTILE_SECRET = '__TURNSTILE_SECRET__'; // Set via wrangler secret put TURNSTILE_SECRET

// Cloudflare R2 Zero-Cost Monthly Free Tier Policy Limits ($0.00 Cost Guarantee)
// Storage: <= 10GB/month (Free) | Class A: <= 1M ops/month (Free) | Class B: <= 10M ops/month (Free)
const R2_FREE_TIER_POLICY = {
  maxStorageBytes: 10 * 1024 * 1024 * 1024, // 10 GB
  maxClassAOpsMonthly: 1000000,
  maxClassBOpsMonthly: 10000000,
  zeroEgressCost: true,
};

const PUBLIC_API_PATH = /^\/api\/v[123](?:[\w.~!$&'()*+,;=:@/-]*)?$/;
const PUBLIC_READ_PATHS = new Set(['/health', '/docs', '/openapi.json']);
const PRIVILEGED_API_PATH = /^\/admin\/[\w.~!$&'()*+,;=:@/-]*$/;
const PRIVILEGED_READ_PATHS = new Set(['/hitl/stats']);
const ARTIFACT_PATH = /^\/artifacts\/[\w.~!$&'()*+,;=:@/-]*$/;

function getPrimaryBackendUrl(env) {
  return env?.BACKEND_BASE_URL || RENDER_BACKEND_URL;
}

function getFallbackBackendUrl() {
  return HF_FALLBACK_URL;
}

async function tryFetchOrigin(origin, request, path, timeoutMs) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const url = `${origin}${path}${new URL(request.url).search}`;
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
    return response;
  } finally {
    clearTimeout(timeout);
  }
}

function isFailoverStatus(status) {
  return status >= 500;
}

function isAllowedPath(path) {
  return PUBLIC_READ_PATHS.has(path) ||
         PUBLIC_API_PATH.test(path) ||
         PRIVILEGED_API_PATH.test(path) ||
         PRIVILEGED_READ_PATHS.has(path) ||
         ARTIFACT_PATH.test(path) ||
         path === '/metrics' ||
         path === '/api/wake';
}

function costGuardrailHeaders() {
  return {
    'X-Cost-Guardrail': 'free-tier-enforced',
    'X-R2-Policy': 'zero-cost-capped',
  };
}

function corsHeaders(request) {
  const origin = request.headers.get('origin');
  const baseHeaders = { ...costGuardrailHeaders() };
  if (origin && CORS_ALLOWED_ORIGINS.includes(origin)) {
    return {
      ...baseHeaders,
      'Access-Control-Allow-Origin': origin,
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With',
      'Vary': 'Origin',
    };
  }
  return baseHeaders;
}

function cacheKey(request) {
  const url = new URL(request.url);
  return `cache:${request.method}:${url.pathname}${url.search}`;
}

async function kvCacheGet(env, key) {
  try {
    const value = await env.CACHE.get(key, { type: 'json' });
    return value;
  } catch {
    return null;
  }
}

async function proxyToBackend(request, path, env) {
  const primaryBase = getPrimaryBackendUrl(env);
  const fallbackBase = getFallbackBackendUrl();

  // Try primary origin first
  try {
    const response = await tryFetchOrigin(primaryBase, request, path, BACKEND_TIMEOUT_MS);
    if (!isFailoverStatus(response.status)) {
      return new Response(response.body, {
        status: response.status,
        headers: { ...corsHeaders(request), 'content-type': response.headers.get('content-type') || 'application/json', 'x-backend-origin': 'render' },
      });
    }
  } catch (_) {
    // Primary failed with network error — fall through to fallback
  }

  // Fallback to HF origin
  try {
    const response = await tryFetchOrigin(fallbackBase, request, path, BACKEND_TIMEOUT_MS);
    return new Response(response.body, {
      status: response.status,
      headers: { ...corsHeaders(request), 'content-type': response.headers.get('content-type') || 'application/json', 'x-backend-origin': 'hf' },
    });
  } catch (err) {
    return new Response(JSON.stringify({ detail: 'Backend unavailable' }), { status: 502 });
  }
}

async function kvCacheSet(env, key, value, ttlSeconds = 86400) {
  try {
    await env.CACHE.put(key, JSON.stringify(value), { expirationTtl: ttlSeconds });
  } catch {
    // KV write failed, continue without cache
  }
}

async function verifyTurnstile(token) {
  const res = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ secret: TURNSTILE_SECRET, response: token }),
  });
  const data = await res.json();
  return data.success === true;
}

async function handleWake(request, env) {
  const hfToken = env?.HF_TOKEN || '';

  // 1. Fast check if backend is already healthy
  try {
    const probeRes = await fetch(`${getPrimaryBackendUrl(env)}/health`, {
      method: 'GET',
      signal: AbortSignal.timeout(3000),
    });
    if (probeRes.ok) {
      return new Response(JSON.stringify({
        status: 'ready',
        message: 'Backend is already running',
      }), {
        status: 200,
        headers: { ...corsHeaders(request), 'content-type': 'application/json' },
      });
    }
  } catch (_) {}

  // 2. If HF_TOKEN not configured
  if (!hfToken) {
    return new Response(JSON.stringify({
      status: 'paused_unauthenticated',
      message: 'Backend is paused and HF_TOKEN is not configured in Cloudflare environment',
      space_url: 'https://huggingface.co/spaces/pphothidaen/horoconsultant-core-backend',
    }), {
      status: 200,
      headers: { ...corsHeaders(request), 'content-type': 'application/json' },
    });
  }

  // 3. Trigger restart via Hugging Face Space API
  try {
    const restartRes = await fetch('https://huggingface.co/api/spaces/pphothidaen/horoconsultant-core-backend/restart', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${hfToken}`,
        'Content-Type': 'application/json',
      },
      signal: AbortSignal.timeout(8000),
    });

    if (restartRes.ok || restartRes.status === 200) {
      return new Response(JSON.stringify({
        status: 'waking',
        message: 'Hugging Face Space restart triggered successfully',
        estimated_seconds: 60,
      }), {
        status: 200,
        headers: { ...corsHeaders(request), 'content-type': 'application/json' },
      });
    }

    const errorText = await restartRes.text().catch(() => '');
    return new Response(JSON.stringify({
      status: 'trigger_failed',
      message: `Hugging Face API returned HTTP ${restartRes.status}`,
      detail: errorText.slice(0, 200),
      space_url: 'https://huggingface.co/spaces/pphothidaen/horoconsultant-core-backend',
    }), {
      status: 200,
      headers: { ...corsHeaders(request), 'content-type': 'application/json' },
    });
  } catch (err) {
    return new Response(JSON.stringify({
      status: 'trigger_error',
      message: err.message || 'Failed to contact Hugging Face API',
      space_url: 'https://huggingface.co/spaces/pphothidaen/horoconsultant-core-backend',
    }), {
      status: 200,
      headers: { ...corsHeaders(request), 'content-type': 'application/json' },
    });
  }
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;

    // Static assets — pass through to Pages CDN
    if (path.match(/\.(js|css|svg|png|ico|json|html)$/)) {
      return fetch(request);
    }

    // API proxy
    if (isAllowedPath(path)) {
      if (request.method === 'OPTIONS') {
        return new Response(null, { status: 204, headers: corsHeaders(request) });
      }

      // Wake-on-demand endpoint
      if (path === '/api/wake') {
        if (request.method !== 'POST') {
          return new Response(JSON.stringify({ detail: 'Method not allowed' }), {
            status: 405,
            headers: { ...corsHeaders(request), 'Allow': 'POST, OPTIONS' },
          });
        }
        return await handleWake(request, env);
      }

      // Turnstile challenge for admin/privileged routes
      if (PRIVILEGED_API_PATH.test(path)) {
        const turnstileToken = request.headers.get('cf-turnstile-response');
        if (!turnstileToken || !(await verifyTurnstile(turnstileToken))) {
          return new Response(JSON.stringify({ detail: 'Turnstile verification required' }), { status: 403 });
        }
      }

      // R2 Zero-Cost Guardrail & Artifact Handler
      if (ARTIFACT_PATH.test(path)) {
        if (env.ARTIFACTS) {
          try {
            const artifactKey = path.replace(/^\/artifacts\//, '');
            const object = await env.ARTIFACTS.get(artifactKey);
            if (object) {
              const headers = new Headers();
              object.writeHttpMetadata(headers);
              headers.set('etag', object.httpEtag);
              Object.entries(corsHeaders(request)).forEach(([k, v]) => headers.set(k, v));
              return new Response(object.body, { headers });
            }
          } catch (_) {
            // Failover to Vercel fallback
          }
        }
        // Transparent Failover / Redirect to Vercel Gateway
        return Response.redirect(`${VERCEL_FALLBACK_ORIGIN}${path}`, 307);
      }

      // KV cache check for GET requests
      if (request.method === 'GET' && env.CACHE) {
        const key = cacheKey(request);
        const cached = await kvCacheGet(env, key);
        if (cached) {
          return new Response(JSON.stringify(cached.response), {
            status: 200,
            headers: { ...corsHeaders(request), 'content-type': 'application/json', 'X-Cache': 'HIT' },
          });
        }
      }

      // Proxy to backend
      const response = await proxyToBackend(request, path, env);

      // Write successful GET responses to KV cache.
      // KAN-268: never cache liveness/telemetry endpoints — a cached 200 would
      // keep reporting "healthy" for up to 24h after the backend went down.
      const NO_CACHE_PATHS = new Set(['/health', '/api/v1/health', '/metrics']);
      if (request.method === 'GET' && response.status === 200 && env.CACHE && !NO_CACHE_PATHS.has(path)) {
        try {
          const body = await response.clone().json();
          await kvCacheSet(env, cacheKey(request), { response: body });
        } catch {
          // Cache write failed, continue
        }
      }

      return response;
    }

    // Root service banner (KAN-270).
    // `/` is deliberately NOT in isAllowedPath(): adding it there would also
    // expose it to the generic proxy + KV cache path. Handled explicitly here,
    // before the SPA fallback, because that fallback cannot resolve without a
    // Pages asset layer — which is why `/` used to answer 404.
    // The body intentionally discloses no backend origins or internal hosts.
    if (path === '/') {
      if (request.method === 'OPTIONS') {
        return new Response(null, { status: 204, headers: corsHeaders(request) });
      }
      if (request.method !== 'GET' && request.method !== 'HEAD') {
        return new Response(JSON.stringify({ detail: 'Method not allowed' }), {
          status: 405,
          headers: {
            ...corsHeaders(request),
            'content-type': 'application/json',
            'Allow': 'GET, HEAD, OPTIONS',
          },
        });
      }
      return new Response(JSON.stringify({
        service: 'HoroConsultant',
        status: 'ok',
        docs: '/docs',
      }), {
        status: 200,
        headers: { ...corsHeaders(request), 'content-type': 'application/json' },
      });
    }

    // SPA fallback — serve from Pages
    return fetch(request);
  },

  async scheduled(event, env, ctx) {
    // Cron trigger: midnight sync
    const syncUrl = `${getPrimaryBackendUrl(env)}/api/v1/sync`;
    ctx.waitUntil(fetch(syncUrl, { method: 'POST' }));
  },
};
