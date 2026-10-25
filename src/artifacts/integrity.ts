#!/usr/bin/env tsx
/**
 * Artifact Integrity Hash Generator
 * Generates SHA256 hashes for wheel files, provenance.json, and openapi.json
 * Used by CI artifact-integrity-tests job
 */

import { createHash } from "node:crypto";
import { readFileSync, readdirSync, statSync } from "node:fs";
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

function main(): void {
  const args = process.argv.slice(2);
  
  if (args[0] !== "generate") {
    console.error("Usage: integrity.ts generate <wheel_glob> <provenance.json> <openapi.json>");
    process.exit(1);
  }

  const wheelGlob = args[1];
  const provenancePath = args[2];
  const openapiPath = args[3];

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

main();
