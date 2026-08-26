import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import test from "node:test";

import { configuredBackendOrigin } from "../api/index.js";

const CANONICAL_BACKEND = "https://pphothidaen-horoconsultant-core-backend.hf.space";
const INDEX_MODULE_URL = new URL("../api/index.js", import.meta.url).href;

function runIndexGateway(testCase) {
  const script = `
    const testCase = JSON.parse(process.env.TEST_CASE);
    const handler = (await import(${JSON.stringify(INDEX_MODULE_URL)})).default;
    const headers = new Map();
    const response = {
      statusCode: null,
      body: undefined,
      setHeader(name, value) { headers.set(name.toLowerCase(), value); },
      getHeader(name) { return headers.get(name.toLowerCase()); },
      status(code) { this.statusCode = code; return this; },
      json(body) { this.body = body; return this; },
      send(body) { this.body = Buffer.isBuffer(body) ? { bytes: body.length } : body; return this; },
      end(body) { this.body = body; return this; },
    };
    const request = {
      method: testCase.method || "GET",
      headers: testCase.headers || {},
      url: testCase.url || "/api/index?path=/health",
      query: testCase.query || {},
    };
    if (testCase.bodyBytes) request.body = "x".repeat(testCase.bodyBytes);
    else if (Object.hasOwn(testCase, "body")) request.body = testCase.body;
    const calls = [];
    globalThis.fetch = async (url, options) => {
      calls.push({ url, method: options.method, bodyBytes: options.body ? options.body.length : 0 });
      const upstream = testCase.upstream || {};
      return new Response(upstream.body || "ok", {
        status: upstream.status || 200,
        headers: {
          "content-type": "application/json",
          "x-request-id": upstream.requestId || "upstream-correlation",
        },
      });
    };
    await handler(request, response);
    process.stdout.write(JSON.stringify({
      calls,
      statusCode: response.statusCode,
      body: response.body,
      headers: Object.fromEntries(headers),
    }));
  `;
  const environment = { ...process.env, TEST_CASE: JSON.stringify(testCase) };
  if (testCase.backend === null) delete environment.HF_BACKEND_URL;
  else environment.HF_BACKEND_URL = testCase.backend || CANONICAL_BACKEND;
  const result = spawnSync(process.execPath, ["--input-type=module", "--eval", script], {
    env: environment,
    encoding: "utf8",
  });
  assert.equal(result.status, 0, result.stderr);
  return JSON.parse(result.stdout);
}

function errorResult(testCase) {
  const result = runIndexGateway(testCase);
  assert.equal(result.calls.length, 0);
  assert.equal(result.body.status, "error");
  return result;
}

test("only the exact canonical HF backend origin is accepted", () => {
  assert.equal(configuredBackendOrigin({ HF_BACKEND_URL: CANONICAL_BACKEND }), CANONICAL_BACKEND);
  assert.equal(configuredBackendOrigin({ HF_BACKEND_URL: `${CANONICAL_BACKEND}/` }), CANONICAL_BACKEND);
  for (const value of [
    undefined,
    "http://pphothidaen-horoconsultant-core-backend.hf.space",
    "https://pphothidaen-horoconsultant-core-backend.static.hf.space",
    "https://legacy.azurecontainerapps.io",
    "https://another-backend.hf.space",
    `${CANONICAL_BACKEND}/api`,
    `${CANONICAL_BACKEND}?redirect=other`,
    `https://user:password@pphothidaen-horoconsultant-core-backend.hf.space`,
  ]) {
    assert.equal(configuredBackendOrigin({ HF_BACKEND_URL: value }), null, value);
  }
});

test("missing or alternate configuration fails closed before an upstream call", () => {
  for (const backend of [null, "https://legacy.azurecontainerapps.io", "https://pphothidaen-horoconsultant-core-backend.static.hf.space"]) {
    const result = errorResult({
      backend,
      url: "/api/index?path=/api/v1/calendar/month",
      headers: { "x-request-id": "bad@example.invalid" },
    });
    assert.equal(result.statusCode, 503);
    assert.equal(result.body.code, "backend_not_configured");
    assert.equal(result.body.detail, "Service is temporarily unavailable.");
    assert.match(result.body.correlation_id, /^api-[a-z0-9]+-[a-z0-9]+$/);
    assert.doesNotMatch(JSON.stringify(result.body), /bad@example\.invalid|azurecontainerapps|static\.hf\.space/);
  }
});

test("an allowed public route makes exactly one canonical upstream request", () => {
  const result = runIndexGateway({
    url: "/api/index?path=/api/v1/calendar/month&year=2026&month=8",
    headers: { "x-request-id": "caller-correlation" },
  });

  assert.equal(result.statusCode, 200);
  assert.deepEqual(result.calls, [{
    url: `${CANONICAL_BACKEND}/api/v1/calendar/month?year=2026&month=8`,
    method: "GET",
    bodyBytes: 0,
  }]);
  assert.equal(result.headers["x-request-id"], "upstream-correlation");
});

test("privileged, traversal, and unlisted mutation routes are denied before fetch", () => {
  const cases = [
    ["/api/index?path=/admin", "GET", 404, "route_not_available"],
    ["/api/index?path=/api/v1/admin/users", "GET", 404, "route_not_available"],
    ["/api/index?path=/hitl", "GET", 404, "route_not_available"],
    ["/api/index?path=/api/v2/hitl/review", "GET", 404, "route_not_available"],
    ["/api/index?path=/api/v1/../admin", "GET", 404, "route_not_available"],
    ["/api/index?path=/api/v1/calendar/month", "POST", 405, "method_not_allowed"],
    ["/api/index?path=/api/v1/not-a-mutation", "POST", 405, "method_not_allowed"],
    ["/api/index?path=/health", "DELETE", 405, "method_not_allowed"],
  ];
  for (const [url, method, status, code] of cases) {
    const result = errorResult({ url, method, headers: { "x-request-id": "caller-id" } });
    assert.equal(result.statusCode, status, `${method} ${url}`);
    assert.equal(result.body.code, code, `${method} ${url}`);
    assert.equal(result.body.correlation_id, "caller-id");
    assert.doesNotMatch(JSON.stringify(result.body), /admin|hitl|\.\./i);
  }
});

test("body limit and unsafe upstream errors produce fixed public output", () => {
  const oversized = errorResult({
    method: "POST",
    url: "/api/index?path=/api/v3/calculate",
    bodyBytes: 2 * 1024 * 1024 + 1,
  });
  assert.equal(oversized.statusCode, 413);
  assert.deepEqual(oversized.body.detail, "The request is too large.");

  const upstream = runIndexGateway({
    method: "POST",
    url: "/api/index?path=/api/v1/bazi/interpret",
    body: { query: "safe" },
    upstream: {
      status: 422,
      requestId: "safe-upstream-id",
      body: JSON.stringify({
        detail: "private@example.invalid from /Users/private-user/report at 203.0.113.42",
      }),
    },
  });
  assert.equal(upstream.calls.length, 1);
  assert.equal(upstream.statusCode, 422);
  assert.deepEqual(upstream.body, {
    status: "error",
    code: "upstream_request_rejected",
    detail: "The API rejected the request data.",
    correlation_id: "safe-upstream-id",
  });
  assert.doesNotMatch(JSON.stringify(upstream.body), /private@example\.invalid|\/Users\/private-user|203\.0\.113\.42/);
});

test("CORS blocks an untrusted origin before it can reach the configured backend", () => {
  const result = runIndexGateway({
    url: "/api/index?path=/health",
    headers: { origin: "https://untrusted.example" },
  });

  assert.equal(result.statusCode, 403);
  assert.equal(result.calls.length, 0);
  assert.deepEqual(result.body, {
    status: "error",
    code: "cors_origin_forbidden",
    detail: "Origin is not allowed.",
  });
});

test("Vercel rewrites expose only public health, v1-v3, docs, and OpenAPI routes", () => {
  const vercel = JSON.parse(readFileSync(new URL("../vercel.json", import.meta.url), "utf8"));
  const rewrites = new Map(vercel.rewrites.map(rule => [rule.source, rule.destination]));

  assert.deepEqual([...rewrites], [
    ["/health", "/api/index?path=/health"],
    ["/api/v1/:path*", "/api/index?path=/api/v1/:path*"],
    ["/api/v2/:path*", "/api/index?path=/api/v2/:path*"],
    ["/api/v3/:path*", "/api/index?path=/api/v3/:path*"],
    ["/docs", "/api/index?path=/docs"],
    ["/openapi.json", "/api/index?path=/openapi.json"],
  ]);
  assert.equal([...rewrites.keys()].some(source => /admin|hitl/i.test(source)), false);
  assert.equal([...rewrites.values()].some(destination => /admin|hitl/i.test(destination)), false);
});
