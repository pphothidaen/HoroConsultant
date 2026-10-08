/**
 * KAN-271: The HF fallback was inert — a Render outage must not proxy a dead 503.
 *
 * The Worker's fallback pointed at the retired Hugging Face Space, which is
 * PAUSED and returns 503. `HF_TOKEN` was never configured, so `handleWake()`
 * could not revive it either. The result: when Render failed, the Worker spent
 * a second 15 s timeout calling a permanently-dead origin and then handed the
 * user a 503 from that dead Space — turning a Render outage into a guaranteed
 * failure while making the request take ~30 s.
 *
 * A Vercel fallback was evaluated and REJECTED: `vercel.json` rewrites API paths
 * into `api/index.js`, which itself proxies to Render — the same failure domain,
 * so failing over to it would change nothing.
 *
 * These tests pin the honest behaviour: one clear, fast failure instead of a
 * second dead hop. They drive the real module with a stubbed global fetch.
 */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const RENDER = "https://horoconsultant-core-backend.onrender.com";
const HF = "https://pphothidaen-horoconsultant-core-backend.hf.space";
const WORKER_URL = new URL("../project/static/_worker.js", import.meta.url).href;
const REPO_ROOT = new URL("..", import.meta.url);

async function callWorker({ path = "/health", method = "GET", env = {}, upstreams = [] } = {}) {
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
    { method },
  );
  const response = await worker.fetch(request, env);
  return {
    calls,
    status: response.status,
    retryAfter: response.headers.get("retry-after"),
    guardrail: response.headers.get("x-cost-guardrail"),
    origin: response.headers.get("x-backend-origin"),
    text: await response.text(),
  };
}

test("Render 5xx does not fall back to the dead HF Space", async () => {
  const result = await callWorker({
    path: "/health",
    upstreams: [
      { match: RENDER, status: 503 },
      { match: HF, status: 200 },
    ],
  });
  assert.equal(result.calls.length, 1, "must not spend a second subrequest on a dead origin");
  assert.ok(!result.calls[0].url.startsWith(HF), "the paused HF Space must not be contacted");
});

test("Render 5xx surfaces a transient 503 for non-liveness paths (KAN-272)", async () => {
  const result = await callWorker({
    path: "/api/v1/test",
    upstreams: [{ match: RENDER, status: 503 }],
  });
  assert.equal(result.status, 503, "non-liveness path 5xx -> transient 503 backend_waking");
  const body = JSON.parse(result.text);
  assert.equal(body.code, "backend_waking");
});

test("Render network failure surfaces the same single 502", async () => {
  const result = await callWorker({
    path: "/health",
    upstreams: [{ match: RENDER, throw: true }],
  });
  assert.equal(result.status, 502);
  assert.equal(result.calls.length, 1);
  const body = JSON.parse(result.text);
  assert.equal(body.code, "backend_unreachable");
});

test("the failure response advertises Retry-After", async () => {
  const result = await callWorker({
    path: "/health",
    upstreams: [{ match: RENDER, status: 503 }],
  });
  assert.ok(result.retryAfter, "a retryable failure must tell the client when to come back");
  assert.match(String(result.retryAfter), /^\d+$/);
});

test("the failure response keeps the guardrail headers", async () => {
  const result = await callWorker({
    path: "/health",
    upstreams: [{ match: RENDER, status: 503 }],
  });
  assert.equal(result.guardrail, "free-tier-enforced");
});

test("the failure body leaks no internal origin", async () => {
  const result = await callWorker({
    path: "/health",
    upstreams: [{ match: RENDER, status: 503 }],
  });
  assert.ok(!result.text.includes("onrender.com"));
  assert.ok(!result.text.includes("hf.space"));
});

test("a healthy primary is unaffected and marked as render", async () => {
  const result = await callWorker({
    path: "/health",
    upstreams: [{ match: RENDER, status: 200 }],
  });
  assert.equal(result.status, 200);
  assert.equal(result.calls.length, 1);
  assert.equal(result.origin, "render");
});

test("4xx still passes through without being rewritten to 502", async () => {
  const result = await callWorker({
    method: "POST",
    path: "/api/v1/bazi/interpret",
    upstreams: [{ match: RENDER, status: 422 }],
  });
  assert.equal(result.status, 422);
  assert.equal(result.calls.length, 1);
});

test("the paused HF origin is gone from the request path entirely", () => {
  const source = readFileSync(new URL("project/static/_worker.js", REPO_ROOT), "utf8");
  assert.ok(!source.includes("HF_FALLBACK_URL"), "HF_FALLBACK_URL must be removed");
  assert.ok(!source.includes("getFallbackBackendUrl"), "getFallbackBackendUrl must be removed");
  assert.ok(!source.includes(HF), "the paused HF Space must not appear as an origin");
});

test("handleWake no longer calls the retired HF restart API", () => {
  const source = readFileSync(new URL("project/static/_worker.js", REPO_ROOT), "utf8");
  assert.ok(!source.includes("huggingface.co/api/spaces"), "the HF restart API is dead code");
});
