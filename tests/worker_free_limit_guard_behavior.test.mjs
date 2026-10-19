/**
 * Multi-Platform Free Limit Guardrail: 80% Warning and 90% Cutoff Behavior.
 *
 * Requirements:
 * 1. Warning when >= 80% free tier limit:
 *    - Injects 'x-cost-guardrail-alert: warning_approaching_free_limit_80'
 *    - Traffic is allowed to continue normally.
 * 2. Cutoff when >= 90% free tier limit:
 *    - Fail-closed circuit breaker.
 *    - Returns HTTP 503 with code 'free_limit_cutoff_90_percent'.
 *    - Upstream backend is NOT called, protecting against any accidental charges.
 *    - Health probe (/health) returns health status with cutoff indication.
 */
import assert from "node:assert/strict";
import test from "node:test";

const WORKER_URL = new URL("../project/static/_worker.js", import.meta.url).href;

async function callWorker({ path = "/api/v1/bazi/calculate", method = "POST", env = {}, body = "{}" } = {}) {
  const worker = (await import(WORKER_URL)).default;
  let backendCalled = false;
  globalThis.fetch = async (url, options = {}) => {
    const target = typeof url === "string" ? url : url.url;
    if (target.includes("code.run") || target.includes("backend")) {
      backendCalled = true;
      return new Response(JSON.stringify({ result: "calculation_ok" }), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    }
    return new Response("pages_fallback", { status: 200 });
  };

  const request = new Request(
    `https://horoconsultant-production.pansakorn.workers.dev${path}`,
    {
      method,
      headers: { "content-type": "application/json" },
      body: method === "GET" ? undefined : body,
    },
  );
  const response = await worker.fetch(request, env);
  return {
    backendCalled,
    status: response.status,
    alertHeader: response.headers.get("x-cost-guardrail-alert"),
    guardrail: response.headers.get("x-cost-guardrail"),
    ratioHeader: response.headers.get("x-cost-guardrail-ratio"),
    data: await response.json().catch(() => null),
  };
}

test("Normal usage below 80% proxies normally without warning alert", async () => {
  const env = { USAGE_RATIO: "0.50" };
  const res = await callWorker({ path: "/api/v1/bazi/calculate", method: "POST", env });
  assert.equal(res.status, 200);
  assert.equal(res.backendCalled, true);
  assert.equal(res.guardrail, "free-tier-enforced");
  assert.equal(res.alertHeader, null);
});

test("Approaching 80% free limit emits warning header but allows traffic", async () => {
  const env = { USAGE_RATIO: "0.82" };
  const res = await callWorker({ path: "/api/v1/bazi/calculate", method: "POST", env });
  assert.equal(res.status, 200);
  assert.equal(res.backendCalled, true);
  assert.equal(res.guardrail, "free-tier-enforced");
  assert.equal(res.alertHeader, "warning_approaching_free_limit_80");
  assert.equal(res.ratioHeader, "0.82");
});

test("At or above 90% free limit fails closed with 503 cutoff and blocks backend call", async () => {
  const env = { USAGE_RATIO: "0.91" };
  const res = await callWorker({ path: "/api/v1/bazi/calculate", method: "POST", env });
  assert.equal(res.status, 503);
  assert.equal(res.backendCalled, false, "Backend MUST NOT be called when cutoff is active");
  assert.equal(res.guardrail, "cutoff-enforced");
  assert.ok(res.data);
  assert.equal(res.data.code, "free_limit_cutoff_90_percent");
  assert.equal(res.data.status, "cutoff_active");
  assert.equal(res.data.threshold, "90%");
});

test("Emergency FREE_LIMIT_CUTOFF environment flag triggers 90% shutdown immediately", async () => {
  const env = { FREE_LIMIT_CUTOFF: "true" };
  const res = await callWorker({ path: "/api/v1/bazi/calculate", method: "POST", env });
  assert.equal(res.status, 503);
  assert.equal(res.backendCalled, false);
  assert.equal(res.data.code, "free_limit_cutoff_90_percent");
});
