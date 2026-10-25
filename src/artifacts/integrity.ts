#!/usr/bin/env tsx
/**
 * Artifact Integrity Hash Generator
 * Generates SHA256 hashes for wheel files, provenance.json, and openapi.json
 * Used by CI artifact-integrity-tests job
 */

import { createHash } from "node:crypto";
import { readFileSync, readdirSync, statSync, existsSync } from "node:fs";
import { resolve, basename } from "node:path";

interface ArtifactHashes {
  wheel: Record<string, string>;
  provenance: string;
  openapi: string;
  generated_at: string;
}

function sha256(filePath: string): string {
  const content = readFileSync(filePath);
  return createHash("sha256").update(content).digest("hex");
}

function findWheelFiles(dir: string): string[] {
  try {
    return readdirSync(dir)
      .filter((f) => f.endsWith(".whl"))
      .map((f) => resolve(dir, f));
  } catch {
    return [];
  }
}

function generate(wheelGlob: string, provenancePath: string, openapiPath: string): void {
  // Parse wheel glob - assume it's a directory with *.whl
  const wheelDir = wheelGlob.replace("/*.whl", "").replace("wheelhouse/", ".");
  const wheelFiles = findWheelFiles(wheelDir);

  const hashes: ArtifactHashes = {
    wheel: {},
    provenance: "",
    openapi: "",
    generated_at: new Date().toISOString(),
  };

  // Hash wheel files
  for (const wheel of wheelFiles) {
    try {
      hashes.wheel[basename(wheel)] = sha256(wheel);
    } catch (e) {
      console.warn(`Warning: Could not hash ${wheel}:`, e);
    }
  }

  // Hash provenance.json
  try {
    hashes.provenance = sha256(provenancePath);
  } catch (e) {
    console.warn("Warning: Could not hash provenance.json:", e);
    hashes.provenance = "MISSING";
  }

  // Hash openapi.json
  try {
    hashes.openapi = sha256(openapiPath);
  } catch (e) {
    console.warn("Warning: Could not hash openapi.json:", e);
    hashes.openapi = "MISSING";
  }

  // Output JSON
  console.log(JSON.stringify(hashes, null, 2));
}

function verify(hashesPath: string, wheelGlob: string, provenancePath: string, openapiPath: string): void {
  // Read expected hashes
  let expected: ArtifactHashes;
  try {
    expected = JSON.parse(readFileSync(hashesPath, "utf-8"));
  } catch (e) {
    console.error("Failed to read hashes file:", e);
    process.exit(1);
  }

  // Parse wheel glob
  const wheelDir = wheelGlob.replace("/*.whl", "").replace("wheelhouse/", ".");
  const wheelFiles = findWheelFiles(wheelDir);

  let allMatch = true;

  // Verify wheel files
  for (const wheel of wheelFiles) {
    const name = basename(wheel);
    try {
      const actual = sha256(wheel);
      const expectedHash = expected.wheel[name];
      if (expectedHash && actual !== expectedHash) {
        console.error(`MISMATCH: ${name}: expected ${expectedHash}, got ${actual}`);
        allMatch = false;
      } else if (!expectedHash) {
        console.warn(`WARNING: ${name} not in expected hashes`);
      } else {
        console.log(`OK: ${name}`);
      }
    } catch (e) {
      console.error(`ERROR hashing ${wheel}:`, e);
      allMatch = false;
    }
  }

  // Check for missing expected wheels
  for (const [name, expectedHash] of Object.entries(expected.wheel)) {
    if (!wheelFiles.some(f => basename(f) === name)) {
      console.error(`MISSING WHEEL: ${name} (expected ${expectedHash})`);
      allMatch = false;
    }
  }

  // Verify provenance.json
  if (existsSync(provenancePath)) {
    try {
      const actual = sha256(provenancePath);
      if (actual !== expected.provenance) {
        console.error(`MISMATCH: provenance.json: expected ${expected.provenance}, got ${actual}`);
        allMatch = false;
      } else {
        console.log("OK: provenance.json");
      }
    } catch (e) {
      console.error("ERROR hashing provenance.json:", e);
      allMatch = false;
    }
  } else {
    console.error("MISSING: provenance.json");
    allMatch = false;
  }

  // Verify openapi.json
  if (existsSync(openapiPath)) {
    try {
      const actual = sha256(openapiPath);
      if (actual !== expected.openapi) {
        console.error(`MISMATCH: openapi.json: expected ${expected.openapi}, got ${actual}`);
        allMatch = false;
      } else {
        console.log("OK: openapi.json");
      }
    } catch (e) {
      console.error("ERROR hashing openapi.json:", e);
      allMatch = false;
    }
  } else {
    console.error("MISSING: openapi.json");
    allMatch = false;
  }

  if (allMatch) {
    console.log("All artifact hashes verified successfully.");
    process.exit(0);
  } else {
    console.error("Artifact integrity verification FAILED.");
    process.exit(1);
  }
}

function main(): void {
  const args = process.argv.slice(2);
  
  if (args.length === 0) {
    console.error("Usage: integrity.ts <generate|verify> ...");
    process.exit(1);
  }

  const command = args[0];

  if (command === "generate") {
    if (args.length < 4) {
      console.error("Usage: integrity.ts generate <wheel_glob> <provenance.json> <openapi.json>");
      process.exit(1);
    }
    generate(args[1], args[2], args[3]);
  } else if (command === "verify") {
    if (args.length < 5) {
      console.error("Usage: integrity.ts verify <hashes.json> <wheel_glob> <provenance.json> <openapi.json>");
      process.exit(1);
    }
    verify(args[1], args[2], args[3], args[4]);
  } else {
    console.error(`Unknown command: ${command}`);
    console.error("Usage: integrity.ts <generate|verify> ...");
    process.exit(1);
  }
}

main();
