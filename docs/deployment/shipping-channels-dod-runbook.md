# Production Shipping Channels & DoD Gate Runbook (KAN-259)

## 1. Overview & Architecture

HoroConsultant distributes production traffic through three governed shipping channels, each bound to specific CI/CD gates and infrastructure:

```
                                  Git Push / Merge to main
                                             │
                                             ▼
                          ┌─────────────────────────────────────┐
                          │ Unified CI & Quality Audit Pipeline │
                          └──────────────────┬──────────────────┘
                                             │ (success)
                                             ▼
                               ┌───────────────────────────┐
                               │    DoD Production Gate    │
                               └─────────────┬─────────────┘
                                             │ (success)
                         ┌───────────────────┴───────────────────┐
                         ▼                                       ▼
            ┌─────────────────────────┐             ┌─────────────────────────┐
            │ deploy-vercel.yml       │             │ deploy-render.yml       │
            │ (Edge Frontend)         │             │ (Core Backend)          │
            │ vercel --prod --yes     │             │ Render Deploy Hook      │
            └─────────────────────────┘             └─────────────────────────┘

        Parallel / Path-triggered:
            ┌─────────────────────────┐
            │ workers-builds.yml      │
            │ (Edge Gateway Worker)   │
            │ wrangler deploy --prod  │
            └─────────────────────────┘
```

---

## 2. Channel 1: Edge Frontend (Vercel)

- **Target URL**: `https://horo-consultant-psi.vercel.app`
- **Deployment Channel**: GitHub Actions Workflow `.github/workflows/deploy-vercel.yml`
- **Gate Dependency**: Gated strictly on `workflow_run: ["DoD Production Gate"]` with `conclusion == 'success'` and `head_branch == 'main'`.
- **Bypass Prevention (KAN-259)**:
  - In `vercel.json`:
    ```json
    "github": {
      "silent": true,
      "autoAlias": false,
      "deploymentEnabled": {
        "*": false,
        "main": false
      }
    }
    ```
  - Disabling automatic Git integration on `main` guarantees that Vercel never auto-deploys upon Git push.
  - Production deployments occur exclusively through `deploy-vercel.yml` via the Vercel CLI (`vercel --token=$VERCEL_TOKEN --prod --yes`) AFTER all DoD criteria have passed.
- **Preview Deployments**: Disabled (`"*": false`) to prevent unverified previews and eliminate cancelled checks.

---

## 3. Channel 2: Edge Gateway Worker (Cloudflare Workers)

- **Target Worker**: `horoconsultant` (`horoconsultant-production`)
- **Deployment Channel**: GitHub Actions Workflow `.github/workflows/workers-builds.yml`
- **Configuration**:
  - Main entry point: `project/static/_worker.js` (consolidated in KAN-269, replacing legacy `api/index.js`).
  - Backend origin: Render primary backend `https://horoconsultant-core-backend.onrender.com` (KAN-268).
  - Dead bindings: Unused R2 binding removed (KAN-264) and dead Worker cron removed (KAN-273).
  - Durable state: `CACHE` KV and `SYNC_STATE` D1 database (`horo-sync-state`).
- **Validation**:
  - `wrangler deploy --dry-run --env production` runs in CI to catch configuration or schema drift without silent failures.

---

## 4. Channel 3: Core Backend (Render)

- **Target Service**: `https://horoconsultant-core-backend.onrender.com`
- **Deployment Channel**: GitHub Actions Workflow `.github/workflows/deploy-render.yml`
- **Gate Dependency**: Gated on `DoD Production Gate` (`conclusion == 'success'`) and `head_branch == 'main'`.
- **Runtime**: Multi-stage Docker container running Rust `horo_server` PID 1 and Python FastAPI worker PID 2.

---

## 5. DoD Production Gate & Verification Sequence

The `DoD Production Gate` (`.github/workflows/dod-production-gate.yml`) validates the following 5 criteria on `main` before triggering production deployments:

1. **Test Provenance Guard**: Verifies PR baseline manifests and test immutability (`scripts/test_provenance_guard.py verify-pr --post-squash-merge`).
2. **Pytest Test Suite**: Verifies core test suite health.
3. **Documentation Index**: Verifies all Markdown documentation is indexed in `docs/INDEX.md` (`scripts/verify_doc_index.py`).
4. **Rust↔Python Route Sync**: Verifies OpenAPI schema sync between Rust gateway and FastAPI endpoints (`tests/test_route_sync.py`).
5. **Sprint Verdict & Evidence**: Emits certified pass confirmation.
