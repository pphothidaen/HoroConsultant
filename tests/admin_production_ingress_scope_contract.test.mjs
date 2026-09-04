import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import test from "node:test";

import { configuredBackendOrigin } from "../api/index.js";

const ROOT = new URL("../", import.meta.url);
const INDEX_MODULE_URL = new URL("../api/index.js", import.meta.url).href;
const CANONICAL_BACKEND = "https://pphothidaen-horoconsultant-core-backend.hf.space";

// Exact IN matrix for production admin ingress scope (least-privilege read + single Google auth POST)
const EXACT_IN_ROUTES = [
  { method: "GET", path: "/admin/auth/config", authRequired: false },
  { method: "POST", path: "/admin/auth/google", authRequired: false, body: { credential: "mock-google-id-token" } },
  { method: "GET", path: "/admin/catalog/summary", authRequired: true },
  { method: "GET", path: "/admin/catalog", authRequired: true },
  { method: "GET", path: "/admin/catalog/source/src-classical-001", authRequired: true },
  { method: "GET", path: "/admin/grayzone", authRequired: true },
  { method: "GET", path: "/admin/grayzone?answered=true", authRequired: true },
  { method: "GET", path: "/admin/grayzone?answered=false", authRequired: true },
  { method: "GET", path: "/admin/finetune/status", authRequired: true },
  { method: "GET", path: "/admin/finetune/download", authRequired: true },
  { method: "GET", path: "/admin/finetune/download-grayzone", authRequired: true },
  { method: "GET", path: "/admin/provider-pools", authRequired: true },
  { method: "GET", path: "/hitl/stats", authRequired: true },
];

// Exact OUT fail-closed matrix (must NOT be forwarded by gateway in production ingress, returning 404/405/401)
const EXACT_OUT_ROUTES = [
  { method: "POST", path: "/admin/grayzone/answer", body: { id: "gz-1", answer: "test" } },
  { method: "DELETE", path: "/admin/grayzone/answer" },
  { method: "POST", path: "/admin/finetune/export-grayzone" },
  { method: "POST", path: "/admin/finetune/merge" },
  { method: "POST", path: "/admin/finetune/trigger" },
  { method: "GET", path: "/admin/unknown" },
  { method: "POST", path: "/admin/unknown" },
  { method: "GET", path: "/hitl/unknown" },
  { method: "POST", path: "/hitl/stats" },
  { method: "POST", path: "/admin/catalog/summary" },
  { method: "DELETE", path: "/admin/catalog/summary" },
  { method: "POST", path: "/admin/catalog" },
  { method: "DELETE", path: "/admin/catalog" },
  { method: "POST", path: "/admin/provider-pools" },
  { method: "PUT", path: "/admin/auth/config" },
  { method: "DELETE", path: "/admin/auth/config" },
  { method: "GET", path: "/admin/auth/google" },
  { method: "POST", path: "/admin/auth/mock-email", body: { email: "admin@test.com" } },
];

function runGateway({ method = "GET", path, authorization = "Bearer verified-google-id-token", body = null }) {
  const script = `
    const handler = (await import(${JSON.stringify(INDEX_MODULE_URL)})).default;
    const request = {
      method: ${JSON.stringify(method)},
      headers: {
        authorization: ${JSON.stringify(authorization)},
        "content-type": "application/json",
      },
      url: "/api/index?path=" + encodeURIComponent(${JSON.stringify(path)}),
      query: {},
      body: ${JSON.stringify(body)},
    };
    const calls = [];
    const headers = new Map();
    const response = {
      statusCode: null, body: null,
      setHeader(name, value) { headers.set(name.toLowerCase(), value); },
      status(code) { this.statusCode = code; return this; },
      json(body) { this.body = body; return this; },
      send(body) { this.body = Buffer.isBuffer(body) ? body.toString("utf8") : body; return this; },
      end(body) { this.body = body; return this; },
    };
    globalThis.fetch = async (url, options) => {
      calls.push({ url, method: options.method, authorization: options.headers?.authorization || "" });
      return new Response("{}", { status: 200, headers: { "content-type": "application/json" } });
    };
    await handler(request, response);
    process.stdout.write(JSON.stringify({ statusCode: response.statusCode, body: response.body, calls }));
  `;
  const result = spawnSync(process.execPath, ["--input-type=module", "--eval", script], {
    encoding: "utf8",
    env: { ...process.env, HF_BACKEND_URL: CANONICAL_BACKEND },
  });
  assert.equal(result.status, 0, result.stderr);
  return JSON.parse(result.stdout);
}

test("production Vercel has exact allowlist rewrites and no privileged wildcards", () => {
  const vercel = JSON.parse(readFileSync(new URL("../vercel.json", import.meta.url), "utf8"));
  const rewrites = new Map(vercel.rewrites.map(({ source, destination }) => [source, destination]));

  assert.equal(
    [...rewrites.keys()].some(source => /^\/(?:admin|hitl)(?:\/|$)/.test(source) && /(?:\*|:path)/.test(source)),
    false,
    "privileged ingress must never have broad /admin/:path* or /hitl/:path* wildcards",
  );

  const exactPaths = [
    "/admin/auth/config",
    "/admin/auth/google",
    "/admin/catalog/summary",
    "/admin/catalog",
    "/admin/catalog/source/:source_id",
    "/admin/grayzone",
    "/admin/finetune/status",
    "/admin/finetune/download",
    "/admin/finetune/download-grayzone",
    "/admin/provider-pools",
    "/hitl/stats",
  ];

  for (const path of exactPaths) {
    assert.equal(
      rewrites.get(path),
      `/api/index?path=${path}`,
      `missing exact least-privilege gateway rewrite for ${path}`,
    );
  }
});

test("gateway forwards exact IN matrix and enforces authentication where required", () => {
  assert.equal(configuredBackendOrigin({ HF_BACKEND_URL: CANONICAL_BACKEND }), CANONICAL_BACKEND);

  for (const route of EXACT_IN_ROUTES) {
    const result = runGateway({ method: route.method, path: route.path, body: route.body });
    assert.equal(
      result.statusCode,
      200,
      `${route.method} ${route.path} should be admitted and return 200 through production ingress`,
    );
    assert.equal(
      result.calls.length,
      1,
      `${route.method} ${route.path} should forward exactly 1 request to backend`,
    );
    assert.equal(
      result.calls[0].url,
      `${CANONICAL_BACKEND}${route.path}`,
      `${route.method} ${route.path} must forward to exact canonical backend target`,
    );
    assert.equal(
      result.calls[0].method,
      route.method,
      `${route.method} ${route.path} must preserve HTTP method`,
    );

    if (route.authRequired) {
      const unauth = runGateway({ method: route.method, path: route.path, authorization: "", body: route.body });
      assert.equal(
        unauth.statusCode,
        401,
        `${route.method} ${route.path} must reject unauthenticated requests with 401`,
      );
      assert.equal(
        unauth.calls.length,
        0,
        `${route.method} ${route.path} must not reach backend without authorization`,
      );
    }
  }
});

test("gateway strictly blocks exact OUT matrix, mutations, unknown routes, and method substitution", () => {
  for (const route of EXACT_OUT_ROUTES) {
    const result = runGateway({ method: route.method, path: route.path, body: route.body });
    assert.ok(
      [401, 404, 405].includes(result.statusCode),
      `${route.method} ${route.path} must be rejected with 401, 404, or 405 (got ${result.statusCode})`,
    );
    assert.equal(
      result.calls.length,
      0,
      `${route.method} ${route.path} must NEVER forward to backend (fail-closed)`,
    );
  }
});

test("both deployed Admin UI mirrors retain Google ID token authentication and required controls", () => {
  for (const relativePath of ["public/admin.html", "project/static/admin.html"]) {
    const html = readFileSync(new URL(`../${relativePath}`, import.meta.url), "utf8");
    assert.match(
      html,
      /State\.adminIdToken\s*=\s*response\.credential/,
      `${relativePath} must retain the Google ID token in State.adminIdToken`,
    );
    assert.match(
      html,
      /Authorization:\s*`Bearer \$\{State\.adminIdToken\}`/,
      `${relativePath} must send the token in Authorization header`,
    );
    assert.match(
      html,
      /if\s*\(endpoint\.startsWith\('\/admin\/'\).*?!State\.adminIdToken/s,
      `${relativePath} must fail closed before protected calls without a token`,
    );
    assert.ok(
      html.includes("loadProviderPoolsStatus()"),
      `${relativePath} must render provider-pools status`,
    );
    assert.ok(
      html.includes("'/admin/provider-pools'"),
      `${relativePath} must use the protected provider-pools route`,
    );
  }
});
