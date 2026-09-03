const BACKEND_BASE_URL = 'https://pphothidaen-horoconsultant-core-backend.hf.space';
const CORS_ALLOWED_ORIGINS = ['https://horoconsultant.yourdomain.com'];
const BACKEND_TIMEOUT_MS = 15000;
const TURNSTILE_SECRET = '__TURNSTILE_SECRET__'; // Set via wrangler secret put TURNSTILE_SECRET

const PUBLIC_API_PATH = /^\/api\/v[123](?:[\w.~!$&'()*+,;=:@/-]*)?$/;
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

      // Turnstile challenge for admin/privileged routes
      if (PRIVILEGED_API_PATH.test(path)) {
        const turnstileToken = request.headers.get('cf-turnstile-response');
        if (!turnstileToken || !(await verifyTurnstile(turnstileToken))) {
          return new Response(JSON.stringify({ detail: 'Turnstile verification required' }), { status: 403 });
        }
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
      const response = await proxyToBackend(request, path);

      // Write successful GET responses to KV cache
      if (request.method === 'GET' && response.status === 200 && env.CACHE) {
        try {
          const body = await response.clone().json();
          await kvCacheSet(env, cacheKey(request), { response: body });
        } catch {
          // Cache write failed, continue
        }
      }

      return response;
    }

    // SPA fallback — serve from Pages
    return fetch(request);
  },

  async scheduled(event, env, ctx) {
    // Cron trigger: midnight sync
    const syncUrl = `${BACKEND_BASE_URL}/api/v1/sync`;
    ctx.waitUntil(fetch(syncUrl, { method: 'POST' }));
  },
};
