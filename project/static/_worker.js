const BACKEND_BASE_URL = 'https://pphothidaen-horoconsultant-core-backend.hf.space';
const CORS_ALLOWED_ORIGINS = ['https://horoconsultant.yourdomain.com'];
const BACKEND_TIMEOUT_MS = 15000;

const PUBLIC_API_PATH = /^\\/api\\/v[123](?:[\\w.~!$&'()*+,;=:@/-]*)?$/;
const PUBLIC_READ_PATHS = new Set(['/health', '/docs', '/openapi.json']);
const PRIVILEGED_API_PATH = /^\\/admin\\/[\\w.~!$&'()*+,;=:@/-]*$/;
const PRIVILEGED_READ_PATHS = new Set(['/hitl/stats']);
const TURNSTILE_SECRET_KEY = 'REPLACE_WITH_TURNSTILE_SECRET'; // Set via wrangler secret put TURNSTILE_SECRET_KEY

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

async function verifyTurnstile(token) {
  const res = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ secret: TURNSTILE_SECRET_KEY, response: token }),
  });
  const data = await res.json();
  return data.success === true;
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
    if (path.match(/\\.(js|css|svg|png|ico|json|html)$/)) {
      return fetch(request);
    }

    // API proxy
    if (isAllowedPath(path)) {
      if (request.method === 'OPTIONS') {
        return new Response(null, { status: 204, headers: corsHeaders(request) });
      }

      // Turnstile challenge for admin routes
      if (PRIVILEGED_API_PATH.test(path)) {
        const turnstileToken = request.headers.get('cf-turnstile-response');
        if (!turnstileToken || !(await verifyTurnstile(turnstileToken))) {
          return new Response(JSON.stringify({ detail: 'Turnstile verification required' }), { status: 403 });
        }
      }

      // Check KV cache for GET requests
      if (request.method === 'GET') {
        const cached = await kvCacheGet(cacheKey(request));
        if (cached) {
          return new Response(JSON.stringify(cached.response), {
            status: 200,
            headers: { ...corsHeaders(request), 'content-type': 'application/json', 'X-Cache': 'HIT' },
          });
        }
      }

      const response = await proxyToBackend(request, path);

      // Write to KV cache for successful GET requests
      if (request.method === 'GET' && response.status === 200) {
        try {
          const body = await response.clone().json();
          await kvCacheSet(cacheKey(request), { response: body });
        } catch {
          // Response body not JSON, skip cache
        }
      }

      return response;
    }

    // SPA fallback
    return fetch(request);
  }
};
