import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import test from "node:test";

import { configuredBackendOrigin } from "../api/index.js";

const ROOT = new URL("../", import.meta.url);
const INDEX_MODULE_URL = new URL("../api/index.js", import.meta.url).href;
const CANONICAL_BACKEND = "https://pphothidaen-horoconsultant-core-backend.hf.space";

// Deliberately explicit: adding a new privileged route requires a conscious
// gateway, browser-token, and deployment-contract review instead of a wildcard.
const ADMIN_STARTUP_ROUTES = [
  ["GET", "/admin/auth/config"],
  ["POST", "/admin/auth/google"],
  ["GET", "/admin/catalog/summary"],
  ["GET", "/admin/grayzone"],
  ["GET", "/admin/finetune/status"],
  ["GET", "/admin/provider-pools"],
  ["GET", "/hitl/stats"],
];
const TOKEN_PROTECTED_STARTUP_ROUTES = ADMIN_STARTUP_ROUTES.filter(([method, path]) =>
  method === "GET" && path !== "/admin/auth/config",
);

function runGateway({ method = "GET", path, authorization = "Bearer verified-google-id-token" }) {
  const script = `
    const handler = (await import(${JSON.stringify(INDEX_MODULE_URL)})).default;
    const request = {
      method: ${JSON.stringify(method)},
      headers: { authorization: ${JSON.stringify(authorization)} },
      url: "/api/index?path=" + encodeURIComponent(${JSON.stringify(path)}),
      query: {},
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
      calls.push({ url, method: options.method, authorization: options.headers.authorization || "" });
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

test("production Vercel has explicit protected Admin and HITL ingress rewrites", () => {
  const vercel = JSON.parse(readFileSync(new URL("../vercel.json", import.meta.url), "utf8"));
  const rewrites = new Map(vercel.rewrites.map(({ source, destination }) => [source, destination]));

  assert.equal(rewrites.get("/admin/:path*"), "/api/index?path=/admin/:path*");
  assert.equal(rewrites.get("/hitl/stats"), "/api/index?path=/hitl/stats");
  assert.equal(rewrites.has("/hitl/:path*"), false, "HITL ingress must remain exact");
});

test("gateway forwards authenticated Admin startup routes and preserves the ID token", () => {
  assert.equal(configuredBackendOrigin({ HF_BACKEND_URL: CANONICAL_BACKEND }), CANONICAL_BACKEND);
  for (const [method, path] of ADMIN_STARTUP_ROUTES) {
    const result = runGateway({ method, path });
    assert.equal(result.statusCode, 200, `${method} ${path} should be routable through production ingress`);
    assert.deepEqual(result.calls, [{
      url: `${CANONICAL_BACKEND}${path}`,
      method,
      authorization: "Bearer verified-google-id-token",
    }]);
  }

  for (const [method, path] of TOKEN_PROTECTED_STARTUP_ROUTES) {
    const denied = runGateway({ method, path, authorization: "" });
    assert.equal(denied.statusCode, 401, `${method} ${path} must reject missing Google ID token`);
    assert.equal(denied.calls.length, 0, `${method} ${path} must not reach the backend without a token`);
  }

  for (const path of ["/admin", "/hitl", "/api/v1/admin/users", "/api/v2/hitl/review"]) {
    const denied = runGateway({ path });
    assert.equal(denied.statusCode, 404, `${path} must not be admitted by a broad Admin rule`);
    assert.equal(denied.calls.length, 0);
  }
});

test("both deployed Admin UI mirrors send a server-verifiable Google ID token on every protected startup request", () => {
  for (const relativePath of ["public/admin.html", "project/static/admin.html"]) {
    const html = readFileSync(new URL(`../${relativePath}`, import.meta.url), "utf8");
    assert.match(html, /State\.adminIdToken\s*=\s*response\.credential/, `${relativePath} must retain the Google ID token in memory`);
    assert.match(html, /Authorization:\s*`Bearer \$\{State\.adminIdToken\}`/, `${relativePath} must send the token as Authorization`);
    assert.match(html, /if\s*\(endpoint\.startsWith\('\/admin\/'\).*?!State\.adminIdToken/s, `${relativePath} must fail closed before protected calls without a token`);
    for (const [, path] of TOKEN_PROTECTED_STARTUP_ROUTES) {
      assert.ok(html.includes(`'${path}'`), `${relativePath} must request ${path} during Admin startup`);
    }
  }
});

test("provider-pools has deployment parity with the production Admin UI", () => {
  for (const relativePath of ["public/admin.html", "project/static/admin.html"]) {
    const html = readFileSync(new URL(`../${relativePath}`, import.meta.url), "utf8");
    assert.ok(html.includes("loadProviderPoolsStatus()"), `${relativePath} must render provider-pools status`);
    assert.ok(html.includes("'/admin/provider-pools'"), `${relativePath} must use the protected provider-pools route`);
    assert.equal(html.includes("'/api/admin/provider-pools'"), false, `${relativePath} must not use an undeployed provider-pools alias`);
  }
});
