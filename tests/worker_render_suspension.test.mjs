/**
 * KAN-283: Render upstream administrative suspension must be disambiguated from cold starts.
 *
 * When Render suspends a service (monthly free-tier hour exhaustion or administrative pause),
 * it returns HTTP 503 with header `x-render-routing: suspend`.
 *
 * The Worker must NOT return `backend_waking` ("starting up, retry shortly"), which creates
 * an infinite retry loop in synthetic monitors and client apps. Instead, it must return
 * `backend_suspended` with an honest explanation and longer retry-after window.
 */
import assert from "node:assert/strict";
import test from "node:test";

const RENDER = "https://horoconsultant-core-backend.onrender.com";
const WORKER_URL = new URL("../project/static/_worker.js", import.meta.url).href;

async function callWorker({ path = "/health", method = "GET", env = {}, upstreams = [] } = {}) {
  const worker = (await import(WORKER_URL)).default;
  const calls = [];
  globalThis.fetch = async (url, options = {}) => {
    const target = typeof url === "string" ? url : url.url;
    calls.push({ url: target, method: options.method || "GET" });
    for (const entry of upstreams) {
      if (entry.match && target.startsWith(entry.match)) {
        if (entry.abort) {
          const err = new Error("The operation was aborted");
          err.name = "AbortError";
          throw err;
        }
        if (entry.throw) throw new Error("upstream unreachable");
        return new Response(entry.body ?? "ok", {
          status: entry.status ?? 200,
          headers: {
            "content-type": entry.contentType ?? "text/html; charset=utf-8",
            ...(entry.headers || {}),
          },
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
    text: await response.text(),
  };
}

test("Render suspension header (x-render-routing: suspend) returns backend_suspended", async () => {
  const result = await callWorker({
    path: "/health",
    upstreams: [{
      match: RENDER,
      status: 503,
      headers: { "x-render-routing": "suspend" },
      body: "<!DOCTYPE html><html><title>Service Suspended</title><body>This service has been suspended.</body></html>",
    }],
  });

  assert.equal(result.status, 503, "suspension remains a 503 HTTP status");
  const body = JSON.parse(result.text);
  assert.equal(body.code, "backend_suspended", "must disambiguate from backend_waking");
  assert.match(body.detail, /suspended/i, "must clearly state the service is suspended");
  assert.equal(result.guardrail, "free-tier-enforced");
  assert.ok(Number(result.retryAfter) >= 300, "suspended service must not suggest rapid retry (e.g. 30s)");
});

test("Normal upstream 503 without suspension header still returns backend_waking", async () => {
  const result = await callWorker({
    path: "/health",
    upstreams: [{
      match: RENDER,
      status: 503,
      body: JSON.stringify({ error: "temporary glitch" }),
      contentType: "application/json",
    }],
  });

  assert.equal(result.status, 503);
  const body = JSON.parse(result.text);
  assert.equal(body.code, "backend_waking");
  assert.equal(result.retryAfter, "30");
});

test("backend_suspended never leaks internal origin and is not cached", async () => {
  const result = await callWorker({
    path: "/health",
    upstreams: [{
      match: RENDER,
      status: 503,
      headers: { "x-render-routing": "suspend" },
      body: "<!DOCTYPE html><html><title>Service Suspended</title><body>This service has been suspended.</body></html>",
    }],
  });

  assert.ok(!result.text.includes("onrender.com"), "must not leak internal origin");
  assert.ok(!result.text.includes("hf.space"), "must not leak internal origin");
});

