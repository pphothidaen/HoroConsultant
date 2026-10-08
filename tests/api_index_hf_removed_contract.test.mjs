/**
 * KAN-276: the Vercel gateway must not carry the retired Hugging Face backend.
 *
 * KAN-271 removed the dead HF fallback from the Worker (project/static/_worker.js).
 * The same defect survived in api/index.js, which vercel.json rewrites every API
 * path into — so it IS the live Vercel channel. It still declared the retired HF
 * Space origin and still POSTed to the retired huggingface.co restart API.
 *
 * These tests pin the removal. They drive the real module.
 */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { configuredBackendOrigins, configuredRenderBackendOrigin } from "../api/index.js";

const CANONICAL_RENDER = "https://horoconsultant-core-backend.onrender.com";
const INDEX_SOURCE = readFileSync(new URL("../api/index.js", import.meta.url), "utf8");

test("the retired HF Space origin is gone from the gateway source", () => {
  assert.doesNotMatch(INDEX_SOURCE, /hf\.space/);
  assert.doesNotMatch(INDEX_SOURCE, /huggingface\.co/);
});

test("the retired HF restart API is never called", () => {
  assert.doesNotMatch(INDEX_SOURCE, /api\/spaces\/.*\/restart/);
});

test("the retired HF origin is no longer an accepted upstream", () => {
  const HF = "https://pphothidaen-horoconsultant-core-backend.hf.space";
  assert.deepEqual(configuredBackendOrigins({ HF_BACKEND_URL: HF }), []);
  assert.deepEqual(
    configuredBackendOrigins({ RENDER_BACKEND_URL: CANONICAL_RENDER, HF_BACKEND_URL: HF }),
    [CANONICAL_RENDER],
  );
});

test("Render remains the single accepted upstream", () => {
  assert.equal(configuredRenderBackendOrigin({ RENDER_BACKEND_URL: CANONICAL_RENDER }), CANONICAL_RENDER);
  assert.deepEqual(configuredBackendOrigins({ RENDER_BACKEND_URL: CANONICAL_RENDER }), [CANONICAL_RENDER]);
  assert.deepEqual(configuredBackendOrigins({}), []);
});
