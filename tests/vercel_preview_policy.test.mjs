import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const vercelConfig = JSON.parse(
  readFileSync(new URL("../vercel.json", import.meta.url), "utf8"),
);

test("Vercel automatic Git deployments keep main production and disable previews", () => {
  assert.deepEqual(vercelConfig.git?.deploymentEnabled, {
    "*": false,
    main: true,
  });
});
