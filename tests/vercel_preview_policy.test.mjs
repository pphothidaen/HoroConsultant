import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const vercelConfig = JSON.parse(
  readFileSync(new URL("../vercel.json", import.meta.url), "utf8"),
);

test("Vercel automatic Git deployments are disabled in favor of DoD Production Gate", () => {
  assert.deepEqual(vercelConfig.github?.deploymentEnabled, {
    "*": false,
    main: false,
  });
});
