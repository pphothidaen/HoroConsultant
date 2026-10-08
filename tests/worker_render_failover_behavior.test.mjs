/**
 * KAN-268: Behavioural tests for project/static/_worker.js backend routing.
 *
 * This is the file that is ACTUALLY DEPLOYED to the Cloudflare Worker
 * `horoconsultant-production` (proven by its unique response headers
 * X-Cost-Guardrail / X-R2-Policy). It previously proxied to the retired,
 * PAUSED Hugging Face Space and ignored wrangler.toml's BACKEND_BASE_URL
 * because a module-level const shadowed it — a silent no-op that passed
 * unit tests. These tests exercise the real module with a stubbed global
 * fetch, so a "config-only" change that does not alter runtime behaviour
 * cannot pass.
 */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const RENDER = "https://horoconsultant-core-backend.onrender.com";
const HF = "https://pphothidaen-horoconsultant-core-backend.hf.space";
const WORKER_URL = new URL("../project/static/_worker.js", import.meta.url).href;

const REPO_ROOT = new URL("..", import.meta.url);

function readRepoFile(relative) {
  return readFileSync(new URL(relative, REPO_ROOT), "utf8");
}

/**
 * Invoke the real worker with a stubbed fetch.
 * @param {object} options
 * @param {string} [options.path]
 * @param {string} [options.method]
 * @param {object} [options.env]
 * @param {Array<{match?:string,status?:number,throw?:boolean,body?:string}>} [options.upstreams]
 */
async function callWorker({ path = "/health", method = "GET", env = {}, upstreams = [], headers = {} } = {}) {
  const worker = (await import(WORKER_URL)).default;
  const calls = [];
  globalThis.fetch = async (url, options = {}) => {
    const target = typeof url === "string" ? url : url.url;
    calls.push({ url: target, method: options.method || "GET" });
    for (const entry of upstreams) {
      if (entry.match && target.startsWith(entry.match)) {
        if (entry.throw) throw new Error("upstream unreachable");
        return new Response(entry.body ?? "ok", {
          status: entry.status ?? 200,
          headers: { "content-type": "application/json" },
        });
      }
    }
    // Anything not explicitly planned (e.g. the Pages SPA passthrough).
    return new Response("passthrough", { status: 200 });
  };

  const request = new Request(
    `https://horoconsultant-production.pansakorn.workers.dev${path}`,
    { method, headers },
  );
  const response = await worker.fetch(request, env);
  return {
    calls,
    status: response.status,
    origin: response.headers.get("x-backend-origin"),
    guardrail: response.headers.get("x-cost-guardrail"),
    text: await response.text(),
  };
}

test("Render is the primary origin when env is unset", async () => {
  const result = await callWorker({
    path: "/health",
    upstreams: [{ match: RENDER, status: 200 }],
  });
  assert.equal(result.calls.length, 1);
  assert.equal(result.calls[0].url, `${RENDER}/health`);
  assert.equal(result.status, 200);
  assert.equal(result.origin, "render");
});

test("env.BACKEND_BASE_URL overrides the primary origin", async () => {
  const result = await callWorker({
    path: "/health",
    env: { BACKEND_BASE_URL: "https://override.example.test" },
    upstreams: [{ match: "https://override.example.test", status: 200 }],
  });
  assert.equal(result.calls.length, 1);
  assert.equal(result.calls[0].url, "https://override.example.test/health");
  assert.equal(result.origin, "render");
});

test("Render 5xx does not fail over to the retired HF Space", async () => {
  // KAN-271: the HF fallback was removed. Failing over spent a second 15s
  // subrequest to hand the user a 503 from a PAUSED origin. Superseded by the
  // fail-fast contract in tests/worker_backend_failfast_behavior.test.mjs.
  const result = await callWorker({
    path: "/api/v1/health",
    upstreams: [
      { match: RENDER, status: 503 },
      { match: HF, status: 200 },
    ],
  });
  assert.equal(result.calls.length, 1, "must not contact a dead fallback");
  assert.equal(result.status, 502);
  assert.equal(result.origin, null);
});

test("Render network failure does not fail over to the retired HF Space", async () => {
  const result = await callWorker({
    path: "/health",
    upstreams: [
      { match: RENDER, throw: true },
      { match: HF, status: 200 },
    ],
  });
  assert.equal(result.calls.length, 1, "must not contact a dead fallback");
  assert.equal(result.status, 502);
});

test("Render 4xx passes through without falling back", async () => {
  const result = await callWorker({
    method: "POST",
    path: "/api/v1/bazi/interpret",
    upstreams: [{ match: RENDER, status: 422 }],
  });
  assert.equal(result.status, 422);
  assert.equal(result.calls.length, 1);
  assert.equal(result.calls[0].url, `${RENDER}/api/v1/bazi/interpret`);
  assert.equal(result.origin, "render");
});

test("both origins failing surfaces a single 502", async () => {
  // KAN-271: there is only one origin now. Kept as a regression guard that the
  // failure is a single explicit 502 rather than a chained timeout.
  const result = await callWorker({
    path: "/health",
    upstreams: [
      { match: RENDER, throw: true },
      { match: HF, throw: true },
    ],
  });
  assert.equal(result.status, 502);
  assert.equal(result.calls.length, 1);
});

test("the retired HF origin is never the primary", async () => {
  const result = await callWorker({
    path: "/health",
    upstreams: [{ match: RENDER, status: 200 }],
  });
  assert.notEqual(result.calls[0].url, `${HF}/health`);
  assert.ok(result.calls[0].url.startsWith(RENDER));
});

test("guardrail headers still identify this worker", async () => {
  const result = await callWorker({
    path: "/health",
    upstreams: [{ match: RENDER, status: 200 }],
  });
  assert.equal(result.guardrail, "free-tier-enforced");
});

test("deny-list preserved: /admin/nope is rejected without touching a backend", async () => {
  const result = await callWorker({
    path: "/admin/nope",
    upstreams: [{ match: RENDER, status: 200 }],
  });
  assert.equal(result.status, 403);
  assert.equal(result.calls.length, 0);
});

test("unknown paths fall through to the Pages SPA, not to a backend", async () => {
  // KAN-270 gave `/` its own handler, so `/` is no longer an "unknown path".
  // Use a genuinely unhandled path to keep testing the SPA passthrough.
  const result = await callWorker({
    path: "/some-unhandled-route",
    upstreams: [{ match: RENDER, status: 200 }],
  });
  assert.equal(result.calls.length, 1);
  assert.ok(!result.calls[0].url.startsWith(RENDER));
  assert.ok(!result.calls[0].url.startsWith(HF));
});

test("wrangler configs point BACKEND_BASE_URL at Render, not the paused HF Space", () => {
  for (const file of ["wrangler.toml", "wrangler.hermes.toml"]) {
    const content = readRepoFile(file);
    const match = content.match(/BACKEND_BASE_URL\s*=\s*"([^"]+)"/);
    assert.ok(match, `${file} must define BACKEND_BASE_URL`);
    assert.equal(match[1], RENDER, `${file} must point BACKEND_BASE_URL at the Render origin`);
  }
});

test("the worker source has a single backend origin and marks the serving origin", () => {
  const source = readRepoFile("project/static/_worker.js");
  assert.ok(!source.includes(`const BACKEND_BASE_URL = '${HF}'`),
    "HF must not remain a hardcoded backend origin");
  assert.ok(source.includes("RENDER_BACKEND_URL"), "worker must define RENDER_BACKEND_URL");
  assert.ok(source.includes("x-backend-origin"), "worker must mark the serving origin");
  // KAN-271: the HF fallback was removed from the request path entirely.
  assert.ok(!source.includes("HF_FALLBACK_URL"), "the retired HF fallback must be gone");
});
