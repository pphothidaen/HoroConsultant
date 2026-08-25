import assert from "node:assert/strict";
import test from "node:test";

import indexHandler from "../api/index.js";
import healthHandler from "../api/health.js";
import { applyCorsPolicy, configuredCorsOrigins } from "../api/gateway.js";

function responseRecorder() {
  const headers = new Map();
  return {
    statusCode: null,
    body: undefined,
    setHeader(name, value) { headers.set(name.toLowerCase(), value); },
    getHeader(name) { return headers.get(name.toLowerCase()); },
    status(code) { this.statusCode = code; return this; },
    json(body) { this.body = body; return this; },
    end(body) { this.body = body; return this; },
    header(name) { return headers.get(name.toLowerCase()); },
  };
}

function request({ method = "OPTIONS", origin, requestMethod = "GET", requestHeaders = "content-type" } = {}) {
  const headers = {};
  if (origin) headers.origin = origin;
  if (requestMethod) headers["access-control-request-method"] = requestMethod;
  if (requestHeaders) headers["access-control-request-headers"] = requestHeaders;
  return { method, headers, url: "/api/index" };
}

test("default CORS allowlist is exactly the canonical Vercel frontend", () => {
  assert.deepEqual(configuredCorsOrigins({}), ["https://horo-consultant-psi.vercel.app"]);
  assert.deepEqual(
    configuredCorsOrigins({ CORS_ALLOWED_ORIGINS: "https://preview.example,https://app.example" }),
    ["https://preview.example", "https://app.example"],
  );
  assert.deepEqual(
    configuredCorsOrigins({ CORS_ALLOWED_ORIGINS: "https://app.example, http://unsafe.example" }),
    ["https://horo-consultant-psi.vercel.app"],
  );
});

test("allowed origin receives exact reflection, Vary, and a constrained header subset", () => {
  const res = responseRecorder();
  const result = applyCorsPolicy(
    request({ origin: "https://horo-consultant-psi.vercel.app", requestHeaders: "content-type, x-request-id" }),
    res,
    { methods: "GET, POST, OPTIONS", environment: {} },
  );

  assert.deepEqual(result, { allowed: true, cors: true });
  assert.equal(res.header("access-control-allow-origin"), "https://horo-consultant-psi.vercel.app");
  assert.equal(res.header("vary"), "Origin");
  assert.equal(res.header("access-control-allow-methods"), "GET, POST, OPTIONS");
  assert.equal(res.header("access-control-allow-headers"), "Content-Type, Authorization, X-Requested-With, X-Request-ID");
  assert.equal(res.header("access-control-allow-credentials"), undefined);
});

test("credentials require explicit configuration and remain paired with an exact origin", () => {
  const res = responseRecorder();
  applyCorsPolicy(
    request({ origin: "https://horo-consultant-psi.vercel.app" }),
    res,
    { methods: "GET, OPTIONS", environment: { CORS_ALLOW_CREDENTIALS: "true" } },
  );
  assert.equal(res.header("access-control-allow-origin"), "https://horo-consultant-psi.vercel.app");
  assert.equal(res.header("access-control-allow-credentials"), "true");
});

test("disallowed-origin and disallowed-header preflights are forbidden without ACAO", async () => {
  for (const req of [
    request({ origin: "https://evil.example" }),
    request({ origin: "https://horo-consultant-psi.vercel.app", requestHeaders: "x-unapproved" }),
  ]) {
    const res = responseRecorder();
    await indexHandler(req, res);
    assert.equal(res.statusCode, 403);
    assert.equal(res.header("access-control-allow-origin"), undefined);
  }
});

test("index and health use the shared strict CORS policy while requests without Origin remain supported", async () => {
  const preflight = responseRecorder();
  await healthHandler(request({ origin: "https://horo-consultant-psi.vercel.app" }), preflight);
  assert.equal(preflight.statusCode, 204);
  assert.equal(preflight.header("access-control-allow-origin"), "https://horo-consultant-psi.vercel.app");

  const sameOrigin = responseRecorder();
  const result = applyCorsPolicy(request({ origin: undefined }), sameOrigin, { methods: "GET, OPTIONS", environment: {} });
  assert.deepEqual(result, { allowed: true, cors: false });
  assert.equal(sameOrigin.header("access-control-allow-origin"), undefined);
});
