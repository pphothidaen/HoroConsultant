import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const TEMPLATE = readFileSync(
  new URL("../.env.example", import.meta.url),
  "utf8",
);

function templateValue(key) {
  const line = TEMPLATE.split("\n").find(
    candidate => candidate.startsWith(`${key}=`),
  );
  return line ? line.slice(key.length + 1).trim() : undefined;
}

test("env template advertises the Render primary backend origin", () => {
  assert.equal(
    templateValue("RENDER_BACKEND_URL"),
    "https://horoconsultant-core-backend.onrender.com",
  );
});

test("env template keeps the HF Space fallback origin", () => {
  assert.equal(
    templateValue("HF_BACKEND_URL"),
    "https://pphothidaen-horoconsultant-core-backend.hf.space",
  );
});
