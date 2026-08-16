# Rust-first Azure v1 Design

**Date:** 2026-08-10
**Status:** Approved for implementation
**Production image:** `pansakorn/horoconsult:v1.0` (`linux/amd64`, private)

## Goal and problem statement

HoroConsultant currently advertises a complete Rust migration, but its production Dockerfiles do not build or install the Rust package and the checked-in native libraries are host-specific macOS ARM64 artifacts. Several Rust implementations also diverge from the Python reference. The release must therefore make Rust real, measurable, and safe instead of extending the existing silent-fallback pattern.

The target is a cost-aware production runtime on Azure Container Apps that preserves the existing FastAPI `/api/v1` wire contract. Axum owns the public listener and only routes verified deterministic calculations to Rust. Dynamic, native-library, RAG, LLM, admin, and HITL work stays behind an explicitly allowlisted Python worker.

## Functional requirements

1. Publish a private Linux AMD64 image as immutable `sha-<git-sha>` plus release aliases `v1.0` and `latest`; deploy by the resolved digest rather than the mutable alias.
2. Listen publicly on port `8000`. The Python worker listens only on `127.0.0.1:8001` and exits with the container if either process fails.
3. Preserve all existing path, method, request, response, status, OpenAPI, and SVG contracts. A correlation header may be added without changing response bodies.
4. Route only parity-qualified deterministic engines to Rust. Keep Swiss Ephemeris, FAISS/NumPy, geolocation, RAG/LLM, admin, and HITL in Python.
5. Keep static UI available through Hugging Face/Vercel while Azure scales to zero. UI must show a bounded wake-up state and must never synthesize a successful calculation after an API failure.
6. Deploy Azure revisions as blue/green with `minReplicas=0`, `maxReplicas=1`, Southeast Asia, private Docker Hub pull credentials, health probes, and rollback by immutable digest.
7. Prevent unrelated pushes from deploying Fly or triggering Kaggle. Production promotion must be explicit and gated by CI.
8. Maintain `PROJECT_TASKS.md`, `plans/plan.md`, `README.md`, `HOWTO.md`, and lessons learned with exact evidence rather than historical counts.

## Architecture and data flow

```text
Browser -> Vercel/HF static UI
        -> Vercel API rewrite -> Azure Container Apps :8000 (Axum)
                                  |-> pure Rust calculation handlers
                                  |-> explicit proxy allowlist
                                      -> 127.0.0.1:8001 (Uvicorn/FastAPI)
```

Axum is PID 1 and supervises Uvicorn as a child. Startup succeeds only after the Python readiness endpoint is healthy. If either process exits unexpectedly, the container exits so Azure can replace the revision. Forwarded requests preserve method, query, relevant headers, body, status, content type, and response bytes. Hop-by-hop headers are stripped. Mutating requests are never retried by the browser or gateway.

The public listener remains port `8000`, so Azure Ingress Target port is `8000`; external clients continue using HTTPS port 443. `/health` is the liveness contract and `/api/v1/health` is the readiness/runtime identity contract without exposing secrets.

## Correctness and ROI gates

- Exact match for categorical and integer fields; floating-point tolerance `1e-6`; equation-of-time error at most `0.01` minute.
- At least 10,000 randomized date/location cases for migrated engines and 100,000 invalid/fuzz inputs without panic or process abort.
- A Rust candidate is enabled only when its endpoint p95 improves by at least 20% and CPU/request falls by at least 30%. Otherwise it remains Python and is recorded as PARKED with evidence.
- Dense vector search remains NumPy/FAISS unless a zero-copy bridge beats the current path by at least 20%; full `.tolist()` conversion is forbidden.
- Rust release profile uses unwind-safe behavior for tests/runtime boundaries. Checked-in native binaries and source-tree scanning loaders are removed.

## Failure handling and release

The UI probes health on page load and retries after 1, 2, 4, 8, and 10 seconds for no more than 60 seconds. It disables only the affected action, preserves form state, announces status through `aria-live`, and sends an actual POST once after readiness. API failures show the real message and correlation ID.

The first Azure revision is a verified Python baseline. The green Rust-first revision receives no production traffic until contract, parity, security, image, cold-start, and performance gates pass through its label URL. Promotion switches traffic to 100% green. Any readiness failure, contract mismatch, parity mismatch, 5xx rate above 1%, or p95 above twice staging rolls traffic back to blue.

## Security and cost constraints

- The credential previously pasted into chat is considered exposed and cannot be the final production credential.
- GitHub receives a read/write Docker Hub token only as a secret; Azure receives a separate read-only pull token.
- The application never logs secret values. Secret synchronization must fail closed and print key names/status only.
- Azure starts at 0.5 vCPU/1 GiB, may increase once to 1 vCPU/2 GiB only after measured staging pressure, and never scales above one replica.
- A scheduled guard evaluates monthly resource consumption. At 70% of the free allowance, or on any non-zero billed cost, it disables public backend ingress until the next monthly reset and the static UI reports temporary unavailability.

## Acceptance

The work is accepted only when the feature branch passes Python, Rust, contract, UI, security, Linux image, and agent-sync gates; the private image digest is deployed to Azure; production E2E identifies the expected Git SHA/runtime; rollback is exercised; and the Kanban is moved from DOING to DONE with exact commands and results.
