/**
 * KAN-270: Behavioural tests for the Worker root path.
 *
 * `GET /` previously fell through `isAllowedPath()` to the SPA passthrough
 * (`return fetch(request)`), which cannot resolve without a Pages asset layer,
 * so the live Worker answered 404 with Cloudflare's default page.
 *
 * These tests invoke the real module with a stubbed global fetch, so a change
 * that only edits configuration or comments cannot pass them.
 */
import assert from "node:assert/strict";
import test from "node:test";

const RENDER = "https://horoconsultant-core-backend.onrender.com";
const HF = "https://pphothidaen-horoconsultant-core-backend.hf.space";
const WORKER_URL = new URL("../project/static/_worker.js", import.meta.url).href;

async function callWorker({ path = "/", method = "GET", env = {}, upstreams = [], headers = {} } = {}) {
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
    return new Response("passthrough", { status: 200 });
  };

  const request = new Request(
    `https://horoconsultant-production.pansakorn.workers.dev${path}`,
    { method, headers },
  );
  const response = await worker.fetch(request, env);
  const text = await response.text();
  return {
    calls,
    status: response.status,
    contentType: response.headers.get("content-type"),
    allow: response.headers.get("allow"),
    guardrail: response.headers.get("x-cost-guardrail"),
    text,
  };
}

test("GET / returns 200 from a real handler, not the SPA passthrough", async () => {
  const result = await callWorker({ path: "/", upstreams: [{ match: RENDER, status: 200 }] });
  assert.equal(result.status, 200, `expected 200 for / but got ${result.status}`);
  // The stub returns the literal "passthrough" for anything not explicitly planned.
  // Reaching it means `/` fell through to the Pages SPA fallback, which is the bug:
  // in production that passthrough cannot resolve and the user gets a 404.
  assert.notEqual(result.text, "passthrough", "/ must be handled explicitly, not passed to the SPA fallback");
});

test("GET / returns a JSON service banner with the contract shape", async () => {
  const result = await callWorker({ path: "/" });
  assert.match(result.contentType || "", /application\/json/);
  const body = JSON.parse(result.text);
  assert.equal(body.service, "HoroConsultant");
  assert.equal(body.status, "ok");
  assert.equal(body.docs, "/docs");
});

test("GET / does not disclose backend origins or internal hosts", async () => {
  const result = await callWorker({ path: "/" });
  assert.ok(!result.text.includes("onrender.com"), "root must not disclose the Render origin");
  assert.ok(!result.text.includes("hf.space"), "root must not disclose the HF origin");
  assert.ok(!result.text.includes("vercel.app"), "root must not disclose the Vercel origin");
});

test("GET / makes no upstream request", async () => {
  const result = await callWorker({ path: "/", upstreams: [{ match: RENDER, status: 200 }] });
  assert.equal(result.calls.length, 0, "the root banner is static and must not hit a backend");
});

test("GET / keeps the cost-guardrail headers", async () => {
  const result = await callWorker({ path: "/" });
  assert.equal(result.guardrail, "free-tier-enforced");
});

test("OPTIONS / returns 204", async () => {
  const result = await callWorker({ path: "/", method: "OPTIONS" });
  assert.equal(result.status, 204);
});

test("POST / returns 405 with an Allow header", async () => {
  const result = await callWorker({ path: "/", method: "POST" });
  assert.equal(result.status, 405);
  assert.ok(result.allow, "405 must advertise the allowed methods");
  assert.match(result.allow, /GET/);
});

test("GET / is not written to the KV cache", async () => {
  const puts = [];
  const worker = (await import(WORKER_URL)).default;
  globalThis.fetch = async () => new Response("ok", { status: 200 });
  const env = {
    CACHE: {
      get: async () => null,
      put: async (key) => { puts.push(key); },
    },
  };
  const response = await worker.fetch(
    new Request("https://horoconsultant-production.pansakorn.workers.dev/"),
    env,
  );
  assert.equal(response.status, 200);
  assert.deepEqual(puts, [], "a static root banner must never be cached");
});

test("deny-list preserved: /admin/nope is 403 and touches no backend", async () => {
  const result = await callWorker({ path: "/admin/nope", upstreams: [{ match: RENDER, status: 200 }] });
  assert.equal(result.status, 403);
  assert.equal(result.calls.length, 0);
});

test("existing routes unchanged: /health still proxies to the Render origin", async () => {
  const result = await callWorker({ path: "/health", upstreams: [{ match: RENDER, status: 200 }] });
  assert.equal(result.status, 200);
  assert.equal(result.calls.length, 1);
  assert.equal(result.calls[0].url, `${RENDER}/health`);
  assert.ok(!result.calls[0].url.startsWith(HF), "health must not go to the paused HF Space");
});
