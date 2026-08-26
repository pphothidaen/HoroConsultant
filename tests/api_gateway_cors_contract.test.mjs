import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import test from "node:test";

import indexHandler from "../api/index.js";
import healthHandler from "../api/health.js";
import {
  applyCorsPolicy,
  configuredBackendOrigin,
  configuredCorsOrigins,
} from "../api/gateway.js";

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

function runGatewayProbe({ backend, status, payload }) {
  const moduleUrl = new URL("../api/gateway.js", import.meta.url).href;
  const script = `
    const { proxyToBackend } = await import(${JSON.stringify(moduleUrl)});
    const headers = new Map();
    const response = {
      statusCode: null,
      body: undefined,
      setHeader(name, value) { headers.set(name.toLowerCase(), value); },
      status(code) { this.statusCode = code; return this; },
      json(body) { this.body = body; return this; },
      send(body) { this.body = body; return this; },
    };
    const calls = [];
    globalThis.fetch = async (url) => {
      calls.push(url);
      return new Response(JSON.stringify(${JSON.stringify(payload)}), {
        status: ${JSON.stringify(status)},
        headers: { "content-type": "application/json", "x-request-id": "upstream-id" },
      });
    };
    await proxyToBackend(
      { method: "GET", headers: {}, query: { subject: "private@example.invalid" } },
      response,
      "health",
      "caller-id",
    );
    process.stdout.write(JSON.stringify({
      calls,
      statusCode: response.statusCode,
      body: response.body,
      requestId: headers.get("x-request-id"),
    }));
  `;
  const environment = { ...process.env, AZURE_API_ORIGIN: "https://ignored.azure.example" };
  if (backend === null) {
    delete environment.HF_BACKEND_URL;
  } else {
    environment.HF_BACKEND_URL = backend;
  }
  const result = spawnSync(process.execPath, ["--input-type=module", "--eval", script], {
    env: environment,
    encoding: "utf8",
  });
  assert.equal(result.status, 0, result.stderr);
  return JSON.parse(result.stdout);
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

test("backend target accepts only an absolute HTTPS Hugging Face Space origin", () => {
  assert.equal(
    configuredBackendOrigin({ HF_BACKEND_URL: "https://horo-backend.hf.space" }),
    "https://horo-backend.hf.space",
  );
  for (const value of [
    undefined,
    "http://horo-backend.hf.space",
    "https://horo-backend.static.hf.space/path",
    "https://horo-backend.hf.space/?unexpected=query",
    "https://user:password@horo-backend.hf.space",
    "https://horo-backend.azurecontainerapps.io",
    "https://not-hf.example",
  ]) {
    assert.equal(configuredBackendOrigin({ HF_BACKEND_URL: value }), null, value);
  }
});

test("gateway fails closed without a backend and exposes no alternate provider", () => {
  const result = runGatewayProbe({ backend: null, status: 200, payload: { detail: "unused" } });

  assert.deepEqual(result.calls, []);
  assert.equal(result.statusCode, 503);
  assert.deepEqual(result.body, {
    detail: "Service is temporarily unavailable.",
    correlation_id: "caller-id",
  });
});

test("gateway makes one HF request and replaces upstream 4xx or PII with a public error", () => {
  const result = runGatewayProbe({
    backend: "https://canonical-backend.hf.space",
    status: 422,
    payload: {
      detail: [{
        type: "validation_error",
        loc: ["body", "email"],
        msg: "private@example.invalid from /Users/private-user/report at 203.0.113.42",
      }],
    },
  });

  assert.deepEqual(result.calls, ["https://canonical-backend.hf.space/health?subject=private%40example.invalid"]);
  assert.equal(result.statusCode, 422);
  assert.deepEqual(result.body, {
    detail: "The API rejected the request data.",
    correlation_id: "upstream-id",
  });
  const publicResponse = JSON.stringify({
    statusCode: result.statusCode,
    body: result.body,
    requestId: result.requestId,
  });
  assert.doesNotMatch(publicResponse, /private@example\.invalid|\/Users\/private-user|203\.0\.113\.42/);
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
