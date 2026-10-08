/**
 * KAN-272: Render free-tier cold starts must be survivable, not a 15s hang.
 *
 * Render's free plan spins down after ~15 minutes idle and takes ~50 seconds to
 * wake, while the Worker's proxy timeout is 15 s — a 35 s gap, so the first
 * request after an idle period could never succeed.
 *
 * Keep-alive was evaluated and rejected: holding a free Render service warm 24/7
 * consumes ~730 of the 750 free instance-hours per month, leaving no headroom,
 * and it only works while this is the sole service in the workspace. Upgrading
 * the plan is a paid change requiring explicit owner sign-off, which the standing
 * "free only" constraint rules out.
 *
 * So the Worker must fail *usefully* instead of hanging:
 *   - a timeout is most likely a cold start -> 503 + Retry-After (transient)
 *   - a connection failure is a real outage -> 502 + Retry-After
 *   - liveness endpoints get a short timeout so they answer fast
 *   - error responses are never cached
 */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const RENDER = "https://horoconsultant-core-backend.onrender.com";
const WORKER_URL = new URL("../project/static/_worker.js", import.meta.url).href;
const REPO_ROOT = new URL("..", import.meta.url);

function abortError() {
  const err = new Error("The operation was aborted");
  err.name = "AbortError";
  return err;
}

async function callWorker({ path = "/health", method = "GET", env = {}, upstreams = [] } = {}) {
  const worker = (await import(WORKER_URL)).default;
  const calls = [];
  globalThis.fetch = async (url, options = {}) => {
    const target = typeof url === "string" ? url : url.url;
    calls.push({ url: target, method: options.method || "GET" });
    for (const entry of upstreams) {
      if (entry.match && target.startsWith(entry.match)) {
        if (entry.abort) throw abortError();
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
    cacheControl: response.headers.get("cache-control"),
    guardrail: response.headers.get("x-cost-guardrail"),
    text: await response.text(),
  };
}

test("a backend timeout is reported as a transient 503, not a 502", async () => {
  const result = await callWorker({
    path: "/api/v1/health",
    upstreams: [{ match: RENDER, abort: true }],
  });
  assert.equal(result.status, 503, "a cold start is transient — 503, not a hard 502");
  const body = JSON.parse(result.text);
  assert.equal(body.code, "backend_waking");
});

test("a connection failure is reported as a 502", async () => {
  const result = await callWorker({
    path: "/health",
    upstreams: [{ match: RENDER, throw: true }],
  });
  assert.equal(result.status, 502);
  const body = JSON.parse(result.text);
  assert.equal(body.code, "backend_unreachable");
});

test("an upstream 5xx is treated as transient and retryable", async () => {
  const result = await callWorker({
    path: "/health",
    upstreams: [{ match: RENDER, status: 503 }],
  });
  assert.equal(result.status, 503);
  const body = JSON.parse(result.text);
  assert.equal(body.code, "backend_waking");
});

test("every failure path advertises Retry-After", async () => {
  for (const upstream of [{ match: RENDER, abort: true }, { match: RENDER, throw: true }, { match: RENDER, status: 502 }]) {
    const result = await callWorker({ path: "/health", upstreams: [upstream] });
    assert.ok(result.retryAfter, `missing Retry-After for ${JSON.stringify(upstream)}`);
    assert.match(String(result.retryAfter), /^\d+$/);
  }
});

test("failure responses are never cached", async () => {
  const result = await callWorker({
    path: "/health",
    upstreams: [{ match: RENDER, abort: true }],
  });
  assert.match(result.cacheControl || "", /no-store/);
});

test("failure bodies leak no internal origin", async () => {
  const result = await callWorker({
    path: "/health",
    upstreams: [{ match: RENDER, abort: true }],
  });
  assert.ok(!result.text.includes("onrender.com"));
  assert.ok(!result.text.includes("hf.space"));
});

test("failure responses keep the guardrail headers", async () => {
  const result = await callWorker({
    path: "/health",
    upstreams: [{ match: RENDER, abort: true }],
  });
  assert.equal(result.guardrail, "free-tier-enforced");
});

test("a healthy backend is unaffected", async () => {
  const result = await callWorker({
    path: "/health",
    upstreams: [{ match: RENDER, status: 200 }],
  });
  assert.equal(result.status, 200);
  assert.equal(result.calls.length, 1);
});

test("liveness endpoints use a shorter timeout than the general proxy timeout", () => {
  const source = readFileSync(new URL("project/static/_worker.js", REPO_ROOT), "utf8");
  const general = source.match(/const BACKEND_TIMEOUT_MS\s*=\s*(\d+)/);
  const liveness = source.match(/const LIVENESS_TIMEOUT_MS\s*=\s*(\d+)/);
  assert.ok(general, "BACKEND_TIMEOUT_MS must exist");
  assert.ok(liveness, "a dedicated liveness timeout must exist");
  assert.ok(
    Number(liveness[1]) < Number(general[1]),
    `liveness timeout (${liveness[1]}ms) must be shorter than the proxy timeout (${general[1]}ms)`,
  );
});

test("the general timeout stays below the cold-start wake window", () => {
  // The timeout must not be raised toward ~50s: that would hang the caller.
  // The chosen mitigation is a fast, useful failure, not a longer wait.
  const source = readFileSync(new URL("project/static/_worker.js", REPO_ROOT), "utf8");
  const general = source.match(/const BACKEND_TIMEOUT_MS\s*=\s*(\d+)/);
  assert.ok(Number(general[1]) <= 20000, "the proxy timeout must stay short enough to fail fast");
});
