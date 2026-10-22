/**
 * Artifact Integrity Verification (SHA256) - KAN-300 M10
 * Implements CONTRACT 3: Artifact Integrity Interface
 */

import { createHash } from "node:crypto";
import { readFileSync, writeFileSync, existsSync, readdirSync } from "node:fs";
import { resolve, basename } from "node:path";

export interface ArtifactHashes {
  rust_wheel: string;
  provenance_json: string;
  openapi_snapshot: string;
}

export interface ArtifactManifest {
  schema_version: string;
  generated_at: string;
  git_commit: string;
  hashes: ArtifactHashes;
}

export class ArtifactIntegrity {
  private workspaceRoot: string;

  constructor(workspaceRoot: string = process.cwd()) {
    this.workspaceRoot = workspaceRoot;
  }

  /**
   * Find the Rust wheel artifact
   */
  findWheel(): string | null {
    const wheelhouse = resolve(this.workspaceRoot, "wheelhouse");
    if (!existsSync(wheelhouse)) return null;
    
    const files = readdirSync(wheelhouse);
    const wheel = files.find(f => f.endsWith(".whl"));
    return wheel ? resolve(wheelhouse, wheel) : null;
  }

  /**
   * Find the provenance JSON artifact
   */
  findProvenance(): string | null {
    const path = resolve(this.workspaceRoot, "provenance.json");
    return existsSync(path) ? path : null;
  }

  /**
   * Find the OpenAPI snapshot artifact
   */
  findOpenAPI(): string | null {
    const path = resolve(this.workspaceRoot, "openapi.json");
    return existsSync(path) ? path : null;
  }

  /**
   * Generate SHA256 hash of a file
   */
  hashFile(filepath: string): string {
    const content = readFileSync(filepath);
    return createHash("sha256").update(content).digest("hex");
  }

  /**
   * Generate hashes for all three artifacts
   */
  generate(): ArtifactHashes {
    const wheelPath = this.findWheel();
    const provenancePath = this.findProvenance();
    const openapiPath = this.findOpenAPI();

    if (!wheelPath) throw new Error("Rust wheel not found in wheelhouse/");
    if (!provenancePath) throw new Error("provenance.json not found");
    if (!openapiPath) throw new Error("openapi.json not found");

    return {
      rust_wheel: this.hashFile(wheelPath),
      provenance_json: this.hashFile(provenancePath),
      openapi_snapshot: this.hashFile(openapiPath)
    };
  }

  /**
   * Get current git commit SHA
   */
  getGitCommit(): string {
    try {
      const result = require("child_process").execSync("git rev-parse HEAD", {
        cwd: this.workspaceRoot,
        encoding: "utf-8"
      });
      return result.trim();
    } catch {
      return "unknown";
    }
  }

  /**
   * Publish hashes to manifest file
   */
  publish(hashes: ArtifactHashes, outputPath: string = "artifact-hashes.json"): void {
    const manifest: ArtifactManifest = {
      schema_version: "artifact-hashes-v1",
      generated_at: new Date().toISOString(),
      git_commit: this.getGitCommit(),
      hashes
    };
    writeFileSync(outputPath, JSON.stringify(manifest, null, 2));
    console.log(`Published hashes to ${outputPath}`);
  }

  /**
   * Verify artifacts against manifest
   */
  verify(manifestPath: string): boolean {
    const manifest = JSON.parse(readFileSync(manifestPath, "utf-8")) as ArtifactManifest;
    const hashes = this.generate();
    
    const mismatches: string[] = [];
    for (const [key, expected] of Object.entries(manifest.hashes)) {
      const actual = hashes[key as keyof ArtifactHashes];
      if (actual !== expected) {
        mismatches.push(` - ${key}: hash mismatch (expected ${expected}, got ${actual})`);
      }
    }

    if (mismatches.length > 0) {
      console.error("Verification failed:\n" + mismatches.join("\n"));
      return false;
    }

    console.log("All artifacts verified successfully");
    return true;
  }

  /**
   * Load manifest from file
   */
  load(manifestPath: string): ArtifactManifest {
    return JSON.parse(readFileSync(manifestPath, "utf-8")) as ArtifactManifest;
  }

  /**
   * Detect tampering - returns list of tampered artifacts
   */
  detectTampering(manifestPath: string): string[] {
    const manifest = this.load(manifestPath);
    const hashes = this.generate();
    const tampered: string[] = [];
    
    for (const [key, expected] of Object.entries(manifest.hashes)) {
      const actual = hashes[key as keyof ArtifactHashes];
      if (actual !== expected) {
        tampered.push(key);
      }
    }
    
    return tampered;
  }
}

/**
 * CLI interface
 */
function main(): void {
  const args = process.argv.slice(2);
  const integrity = new ArtifactIntegrity();

  if (args[0] === "generate") {
    const hashes = integrity.generate();
    console.log(JSON.stringify(hashes, null, 2));
  } else if (args[0] === "publish") {
    const hashes = integrity.generate();
    integrity.publish(hashes, args[1] || "artifact-hashes.json");
  } else if (args[0] === "verify") {
    const ok = integrity.verify(args[1] || "artifact-hashes.json");
    process.exit(ok ? 0 : 1);
  } else if (args[0] === "load") {
    const manifest = integrity.load(args[1] || "artifact-hashes.json");
    console.log(JSON.stringify(manifest, null, 2));
  } else if (args[0] === "detect-tampering") {
    const tampered = integrity.detectTampering(args[1] || "artifact-hashes.json");
    if (tampered.length > 0) {
      console.error("Tampered artifacts:", tampered.join(", "));
      process.exit(1);
    } else {
      console.log("No tampering detected");
    }
  } else {
    console.error("Usage: npx tsx src/artifacts/integrity.ts [generate|publish|verify|load|detect-tampering] [path]");
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}