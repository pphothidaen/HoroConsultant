const BACKEND_BASE_URL = 'https://pphothidaen-horoconsultant-core-backend.hf.space';
const CORS_ALLOWED_ORIGINS = ['https://horoconsultant.yourdomain.com'];
const BACKEND_TIMEOUT_MS = 15000;

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
