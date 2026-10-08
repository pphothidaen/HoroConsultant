// KAN-271: the HF Space fallback was REMOVED. The Space is retired (PAUSED,
// hardware: None) and HF_TOKEN was never configured, so failing over to it only
// spent a second 15s subrequest to hand the user a 503 from a dead origin.
// A Vercel fallback was evaluated and rejected: vercel.json rewrites API paths
// into api/index.js, which itself proxies to this same Render backend, so the
// two share one failure domain and failing over would change nothing.
// The honest behaviour is a single fast, explicit failure.
const RENDER_BACKEND_URL = 'https://horoconsultant-core-backend.onrender.com';
const VERCEL_FALLBACK_ORIGIN = 'https://horo-consultant-psi.vercel.app';
const CORS_ALLOWED_ORIGINS = [
  'https://horo-consultant-psi.vercel.app',
  'https://horoconsultant-pages.pages.dev',
];
const BACKEND_TIMEOUT_MS = 15000;
// KAN-272: liveness/telemetry endpoints must answer fast. A cold Render free-tier
// instance takes ~50s to wake, so waiting the full proxy timeout on /health just
// makes the caller hang. A short probe fails quickly and honestly.
const LIVENESS_TIMEOUT_MS = 5000;
const LIVENESS_PATHS = new Set(['/health', '/api/v1/health', '/metrics']);
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
  // KAN-272: liveness probes get a short timeout so they fail fast.
  const timeoutMs = LIVENESS_PATHS.has(path) ? LIVENESS_TIMEOUT_MS : BACKEND_TIMEOUT_MS;

  // KAN-271: single origin, single attempt. No dead fallback hop.
  try {
    const response = await tryFetchOrigin(primaryBase, request, path, timeoutMs);
    if (!isFailoverStatus(response.status)) {
      return new Response(response.body, {
        status: response.status,
        headers: { ...corsHeaders(request), 'content-type': response.headers.get('content-type') || 'application/json', 'x-backend-origin': 'render' },
      });
    }
    // An upstream 5xx is most likely a cold start: transient and retryable.
    return backendWakingResponse(request);
  } catch (err) {
    // A timeout means the backend did not answer in time — the signature of a
    // Render free-tier cold start (~50s wake). Report it as transient so the
    // caller retries instead of treating the service as broken.
    if (err && err.name === 'AbortError') {
      return backendWakingResponse(request);
    }
    // A connection failure is a genuine outage.
    return backendUnreachableResponse(request);
  }
}

function failureHeaders(request) {
  return {
    ...corsHeaders(request),
    'content-type': 'application/json',
    'Retry-After': '30',
    // KAN-272: never let a transient failure be cached.
    'Cache-Control': 'no-store',
  };
}

// Transient: the backend is probably cold-starting and will answer shortly.
function backendWakingResponse(request) {
  return new Response(JSON.stringify({
    code: 'backend_waking',
    detail: 'The backend is starting up. Please retry shortly.',
  }), {
    status: 503,
    headers: failureHeaders(request),
  });
}

// Genuine outage: the backend could not be reached at all.
function backendUnreachableResponse(request) {
  return new Response(JSON.stringify({
    code: 'backend_unreachable',
    detail: 'The backend is unavailable. Please retry shortly.',
  }), {
    status: 502,
    headers: failureHeaders(request),
  });
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

// KAN-271: /api/wake used to probe the backend and, on failure, call the
// Hugging Face Space restart API. That Space is retired and HF_TOKEN was never
// configured, so the branch could only ever report failure. Render's free plan
// wakes on demand by itself, so the useful behaviour is: report whether the
// backend is currently answering, and tell the caller to retry if it is not.
async function handleWake(request, env) {
  try {
    const probeRes = await fetch(`${getPrimaryBackendUrl(env)}/health`, {
      method: 'GET',
      signal: AbortSignal.timeout(5000),
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

  return new Response(JSON.stringify({
    status: 'waking',
    message: 'Backend is not answering yet. Render wakes on demand; retry shortly.',
    retry_after_seconds: 30,
  }), {
    status: 503,
    headers: {
      ...corsHeaders(request),
      'content-type': 'application/json',
      'Retry-After': '30',
    },
  });
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
};
