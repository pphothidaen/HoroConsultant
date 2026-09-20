import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import test from "node:test";

import { configuredBackendOrigins, configuredRenderBackendOrigin } from "../api/index.js";

const CANONICAL_HF = "https://pphothidaen-horoconsultant-core-backend.hf.space";
const CANONICAL_RENDER = "https://horoconsultant-core-backend.onrender.com";
const INDEX_MODULE_URL = new URL("../api/index.js", import.meta.url).href;

test("only the exact canonical Render backend origin is accepted", () => {
  assert.equal(configuredRenderBackendOrigin({ RENDER_BACKEND_URL: CANONICAL_RENDER }), CANONICAL_RENDER);
  assert.equal(configuredRenderBackendOrigin({ RENDER_BACKEND_URL: `${CANONICAL_RENDER}/` }), CANONICAL_RENDER);
  for (const value of [
    undefined,
    "http://horoconsultant-core-backend.onrender.com",
    "https://horoconsultant-core-backend2.onrender.com",
    "https://another.onrender.com",
    `${CANONICAL_RENDER}/api`,
    `${CANONICAL_RENDER}?redirect=other`,
  ]) {
    assert.equal(configuredRenderBackendOrigin({ RENDER_BACKEND_URL: value }), null, value);
  }
});

test("origins are ordered Render primary then HF fallback", () => {
  assert.deepEqual(
    configuredBackendOrigins({ RENDER_BACKEND_URL: CANONICAL_RENDER, HF_BACKEND_URL: CANONICAL_HF }),
    [CANONICAL_RENDER, CANONICAL_HF],
  );
  assert.deepEqual(configuredBackendOrigins({ HF_BACKEND_URL: CANONICAL_HF }), [CANONICAL_HF]);
  assert.deepEqual(configuredBackendOrigins({ RENDER_BACKEND_URL: CANONICAL_RENDER }), [CANONICAL_RENDER]);
  assert.deepEqual(configuredBackendOrigins({}), []);
});

function runGateway(testCase) {
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
    };
    if (testCase.body) request.body = testCase.body;
    const calls = [];
    globalThis.fetch = async (url, options) => {
      calls.push({ url, method: options.method });
      const plan = testCase.upstreams || [];
      for (const entry of plan) {
        if (entry.match && url.startsWith(entry.match)) {
          if (entry.throw) throw new Error("upstream unreachable");
          return new Response(entry.body || "ok", {
            status: entry.status || 200,
            headers: { "content-type": "application/json", "x-request-id": entry.requestId || "upstream-correlation" },
          });
        }
      }
      return new Response("ok", { status: 200, headers: { "content-type": "application/json" } });
    };
    await handler(request, response);
    process.stdout.write(JSON.stringify({
      calls,
      statusCode: response.statusCode,
      body: response.body,
    }));
  `;
  const environment = { ...process.env, TEST_CASE: JSON.stringify(testCase) };
  environment.RENDER_BACKEND_URL = testCase.render === null ? "" : (testCase.render || CANONICAL_RENDER);
  environment.HF_BACKEND_URL = testCase.hf === null ? "" : (testCase.hf || CANONICAL_HF);
  const result = spawnSync(process.execPath, ["--input-type=module", "--eval", script], {
    env: environment,
    encoding: "utf8",
  });
  assert.equal(result.status, 0, result.stderr);
  return JSON.parse(result.stdout);
}

test("Render 5xx fails over to the HF fallback origin", () => {
  const result = runGateway({
    url: "/api/index?path=/api/v1/calendar/month&year=2026&month=8",
    upstreams: [
      { match: CANONICAL_RENDER, status: 503 },
      { match: CANONICAL_HF, status: 200, requestId: "hf-correlation" },
    ],
  });
  assert.equal(result.statusCode, 200);
  assert.equal(result.calls.length, 2);
  assert.equal(result.calls[0].url, `${CANONICAL_RENDER}/api/v1/calendar/month?year=2026&month=8`);
  assert.equal(result.calls[1].url, `${CANONICAL_HF}/api/v1/calendar/month?year=2026&month=8`);
  assert.deepEqual(result.body, { bytes: 2 });
});

test("Render network failure fails over to the HF fallback origin", () => {
  const result = runGateway({
    url: "/api/index?path=/health",
    upstreams: [
      { match: CANONICAL_RENDER, throw: true },
      { match: CANONICAL_HF, status: 200 },
    ],
  });
  assert.equal(result.statusCode, 200);
  assert.equal(result.calls.length, 2);
  assert.equal(result.calls[0].url, `${CANONICAL_RENDER}/health`);
  assert.equal(result.calls[1].url, `${CANONICAL_HF}/health`);
});

test("Render 4xx passes through without falling back", () => {
  const result = runGateway({
    method: "POST",
    url: "/api/index?path=/api/v1/bazi/interpret",
    body: { query: "safe" },
    upstreams: [{ match: CANONICAL_RENDER, status: 422 }],
  });
  assert.equal(result.statusCode, 422);
  assert.equal(result.calls.length, 1);
  assert.equal(result.calls[0].url, `${CANONICAL_RENDER}/api/v1/bazi/interpret`);
});

test("HF-only configuration still makes exactly one upstream request", () => {
  const result = runGateway({
    render: null,
    url: "/api/index?path=/health",
    upstreams: [{ match: CANONICAL_HF, status: 200 }],
  });
  assert.equal(result.statusCode, 200);
  assert.equal(result.calls.length, 1);
  assert.equal(result.calls[0].url, `${CANONICAL_HF}/health`);
});

test("all origins failing surfaces a single public error", () => {
  const result = runGateway({
    url: "/api/index?path=/health",
    upstreams: [
      { match: CANONICAL_RENDER, throw: true },
      { match: CANONICAL_HF, throw: true },
    ],
  });
  assert.equal(result.statusCode, 502);
  assert.equal(result.body.code, "backend_unreachable");
  assert.equal(result.calls.length, 2);
});
