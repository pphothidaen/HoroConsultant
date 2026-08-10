# Production Rust-first Runtime and Azure v1 Release

**Last updated:** 2026-08-10

**Detailed design:** `docs/superpowers/specs/2026-08-10-rust-first-azure-v1-design.md`

**Execution plan:** `docs/superpowers/plans/2026-08-10-rust-first-azure-v1.md`

## Goal / Problem Statement

Ship a verified Linux AMD64 production runtime that uses Rust where correctness and resource ROI are proven, preserves the existing `/api/v1` contract, and runs on Azure Container Apps within a strict free-allowance guard. The current production packaging does not install Rust, host-specific native files are committed, and several Rust paths diverge from their Python reference; those conditions must be corrected before any 100% migration claim is valid.

## Candidate and ROI Decision Matrix

| Area | Decision | Gate / reason |
|---|---|---|
| Axum ingress, health, correlation, proxy | Migrate | Low idle footprint and one public listener |
| BaZi and true solar time | Conditional migrate | Exact/golden parity plus p95 +20% and CPU/request -30% |
| ZiWei, QiMen, XuanKong, Thai/Vedic, I Ching, LiuRen, ZeJi, Numerology, SVG | Conditional migrate per engine | Enable independently only after parity and ROI |
| TF-IDF matrix kernel | Retain/evaluate | Existing audit measured approximately 2.6x improvement |
| Dense vector search | Keep Python/FAISS | Current list bridge is over 1,000x slower than NumPy; no `.tolist()` path allowed |
| Swiss Ephemeris and Western astronomy | Keep Python/native C | Accuracy and body coverage exceed current Rust approximation |
| RAG/LLM, geolocation, admin, HITL | Keep Python worker | Network/dynamic orchestration has poor rewrite ROI |

## Functional Requirements

- Produce private `pansakorn/horoconsult` for `linux/amd64` with immutable SHA tag plus `v1.0` and `latest`; deploy Azure by the verified digest.
- Serve publicly through Axum on port 8000 and proxy approved routes to Uvicorn on localhost:8001.
- Preserve all current methods, paths, schemas, statuses, OpenAPI, and chart data.
- Keep static UI always available, show bounded cold-start loading, and never retry mutations or fabricate success.
- Deploy blue/green Azure revisions with scale-to-zero, health probes, private registry access, and deterministic rollback.
- Make CI, release, secret scanning, and final documentation evidence truthful and reproducible.

## Non-Functional Requirements

- Python 3.12 and Rust 1.97.1 in CI/container; pure ASCII subprocess logs.
- Exact categorical/integer parity, float tolerance `1e-6`, EoT tolerance `0.01` minute.
- At least 10,000 randomized valid cases and 100,000 invalid/fuzz cases without abort.
- Migrated endpoint p95 improves at least 20% and CPU/request falls at least 30%.
- Azure min replicas 0, max replicas 1, initial 0.5 vCPU/1 GiB, Southeast Asia.
- No secret values in source, command arguments, reports, CI logs, or deployment output.

## Architecture and Data Flow Impact

Vercel serves as the public edge. Static assets continue to come from Hugging Face. API traffic is rewritten to Azure Container Apps, where Axum owns port 8000. Pure Rust handlers serve only qualified deterministic engines. An explicit allowlist proxies all retained Python functionality to a supervised Uvicorn child on `127.0.0.1:8001`. Azure revisions and immutable image digests replace in-image duplicate fallback code as the rollback mechanism.

## Phased Implementation

1. Correct the plan/Kanban and capture clean baseline evidence.
2. Stabilize Rust packaging/import behavior and remove host binaries.
3. Establish BaZi/solar and remaining-engine parity/ROI gates.
4. Implement the contract-safe Axum gateway and Python supervision.
5. Add cold-start UX and Vercel Azure routing.
6. Build Linux AMD64 CI, private Docker Hub publishing, Azure IaC, and the strict-free guard.
7. Complete security/QA review, PR merge, blue/green cutover, live verification, and final documentation.

## Acceptance Criteria and Test Matrix

| Gate | Required evidence |
|---|---|
| Baseline | Fresh full pytest output and starting Git SHA |
| Rust | `cargo fmt --check`, `cargo clippy -- -D warnings`, `cargo test`, installed-wheel smoke |
| Contract | All current OpenAPI paths plus representative error/status/SVG goldens through Axum |
| Correctness | Literal fixtures, 10k deterministic randomized cases, 100k invalid/fuzz cases |
| Python | Full `python3 -m pytest -v --ignore=project/kaggle_kernel` with zero failures |
| UI | Button regression and Playwright cold-start/mutation-once/error behavior |
| Image | Linux AMD64, non-root, health-ready, correct Git SHA and Rust runtime identity |
| Security | Zero secret leaks and code reviewer `READY_FOR_PROD` |
| Deployment | Green label verification, traffic promotion, public E2E, 30-minute soak, rollback evidence |
| Governance | Both agent sync checks pass and Kanban/docs contain exact final evidence |
