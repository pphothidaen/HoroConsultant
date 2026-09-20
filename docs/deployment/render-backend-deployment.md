# Render Backend Deployment Guide

Primary production backend architecture introduced in PR #53: the **Render web service** (`horoconsultant-core-backend`) becomes the primary backend origin, with the **Hugging Face Space** demoted to fallback origin. The Vercel gateway performs multi-origin failover between them.

> Related files: [`render.yaml`](../../render.yaml), [`Dockerfile.render`](../../Dockerfile.render), [`.github/workflows/deploy-render.yml`](../../.github/workflows/deploy-render.yml), [`scripts/sync-render-secrets.sh`](../../scripts/sync-render-secrets.sh), [`api/index.js`](../../api/index.js)

---

## 1. Architecture Overview

```
                ┌──────────────────────────┐
   Clients ───► │  Vercel Gateway (api/)   │
                │  origin order:           │
                │   1. Render (primary)    │──► https://horoconsultant-core-backend.onrender.com
                │   2. HF Space (fallback) │──► https://pphothidaen-horoconsultant-core-backend.hf.space
                └──────────────────────────┘
```

- **Render primary** — Docker web service built from `Dockerfile.render` (Ubuntu 22.04, Rust core compiled via maturin, uvicorn binds to Render's injected `PORT`, default 10000). Declared in `render.yaml` as a Blueprint: `runtime: docker`, `plan: free`, `region: singapore`, `autoDeploy: true`, `healthCheckPath: /health`.
- **HF Space fallback** — the previous primary (`pphothidaen/horoconsultant-core-backend`); remains deployed and is only used when Render fails.
- **Fail-closed origin validation** — the gateway accepts only the exact canonical origins (`https://horoconsultant-core-backend.onrender.com` and `https://pphothidaen-horoconsultant-core-backend.hf.space`). Any other `RENDER_BACKEND_URL` / `HF_BACKEND_URL` value, or both being empty, results in `503 backend_not_configured` — never an arbitrary upstream.

### Gateway Failover Behavior

The gateway resolves origins in order `[Render, HF Space]` and walks the list per request:

| Condition on Render (non-final origin) | Gateway behavior |
| :--- | :--- |
| Upstream responds `5xx` | Fails over to the HF Space origin |
| Network error / connection refused | Fails over to the HF Space origin |
| Request times out (`VERCEL_BACKEND_TIMEOUT_MS`, default 8s, max 30s) | Fails over to the HF Space origin; if all origins time out, returns `504 backend_timeout` |
| Upstream responds `4xx` | **Passed through** — no failover (client errors are not retried against the fallback); surfaced as `upstream_request_rejected` |
| Render returns success (`2xx`) | Response proxied directly; request never touches the HF Space |
| Both origins unreachable | `502 backend_unreachable` (or `504 backend_timeout` on timeouts) |
| `RENDER_BACKEND_URL` unset/invalid | Render is skipped; gateway serves from HF Space only |
| Both env vars unset/invalid | `503 backend_not_configured` |

---

## 2. One-Time Setup Checklist

1. **Render account & billing** — Add a payment method at `https://dashboard.render.com/billing` (required to provision the web service, even on the free plan).
2. **Create the Render web service** — Either:
   - **Blueprint (recommended):** In the Render dashboard, choose *New → Blueprint* and point it at `https://github.com/pphothidaen/HoroConsultant` (branch `main`). Render reads `render.yaml` and provisions the `horoconsultant-core-backend` web service with `Dockerfile.render`, the `/health` health check, free plan, and auto-deploy already configured; **or**
   - **Manual:** Create a *Web Service* with runtime **Docker**, Dockerfile path `./Dockerfile.render`, health check path `/health`, instance type **Free**, and region **Singapore**.
3. **Collect Render identifiers** — Note the **service id** (`srv-...`, from the service's URL/settings) and the canonical URL `https://horoconsultant-core-backend.onrender.com`.
4. **Create a Render API key** — Dashboard → *Account Settings → API Keys*; used by CI and the secrets sync script.
5. **GitHub repository secrets** (Settings → Secrets and variables → Actions):

   | Secret | Value |
   | :--- | :--- |
   | `RENDER_API_KEY` | Render API token |
   | `RENDER_SERVICE_ID` | Render service id (`srv-...`) |
   | `RENDER_BACKEND_URL` | `https://horoconsultant-core-backend.onrender.com` (optional — the workflow falls back to this value if unset) |

6. **Vercel environment variable** — In the Vercel project (Production environment), set:

   | Variable | Value |
   | :--- | :--- |
   | `RENDER_BACKEND_URL` | `https://horoconsultant-core-backend.onrender.com` |

   Redeploy the Vercel gateway afterward so the new origin is picked up.
7. **Verify** — `GET https://horoconsultant-core-backend.onrender.com/health` returns `200`, then `GET https://horo-consultant-psi.vercel.app/health` (or your Vercel domain) returns `200` through the Render primary.

---

## 3. Secrets Sync (Doppler → Render)

`scripts/sync-render-secrets.sh` fetches every secret from the Doppler `prd` config and upserts them as Render environment variables via the Render API.

**Required environment variables:**

| Variable | Description |
| :--- | :--- |
| `DOPPLER_SERVICE_TOKEN` | Doppler service token (`dp.st.prd.*`) |
| `RENDER_API_KEY` | Render API token (`rnd_...`) |
| `RENDER_SERVICE_ID` | Render service id (`srv-...`) |

**Optional:** `DOPPLER_PROJECT` (default `horo-consultant`), `DOPPLER_CONFIG` (default `prd`).

**Usage:**

```bash
DOPPLER_SERVICE_TOKEN=dp.st.prd.xxxx \
RENDER_API_KEY=rnd_xxxx \
RENDER_SERVICE_ID=srv-xxxx \
  ./scripts/sync-render-secrets.sh
```

With optional overrides:

```bash
DOPPLER_SERVICE_TOKEN=dp.st.prd.xxxx \
RENDER_API_KEY=rnd_xxxx \
RENDER_SERVICE_ID=srv-xxxx \
DOPPLER_PROJECT=horo-consultant \
DOPPLER_CONFIG=prd \
  ./scripts/sync-render-secrets.sh
```

**Exclusions** — gateway-only and self-referential credentials are never pushed to Render:

- Prefixes: `VERCEL_*`, `GITHUB_*`, `HF_STATIC_*`
- Exact keys: `DOPPLER_SERVICE_TOKEN`, `DOPPLER_TOKEN`, `RENDER_API_KEY`, `RENDER_SERVICE_ID`, `RENDER_TOKEN`

After the sync completes, Render automatically redeploys the service so the new environment takes effect.

---

## 4. Deploy Flow

Publication is **CI-gated**: a direct push never publishes. The successful "Unified CI & Quality Audit Pipeline" run supplies the immutable source commit.

### Automatic (push to `main`)

1. **CI** — Push to `main` runs the *Unified CI & Quality Audit Pipeline*.
2. **Trigger** — On CI success on `main`, `.github/workflows/deploy-render.yml` runs (`workflow_run` hook, `production` environment, concurrency group `render-backend-production`).
3. **Render build** — The workflow POSTs the commit SHA to the Render API (`POST /v1/services/{RENDER_SERVICE_ID}/deploys`). Render builds the Docker image itself from `Dockerfile.render` on the connected repository.
4. **Deploy tracking** — The workflow polls the deploy status every 15s (up to 60 attempts / ~15 min) until `live`, failing on any terminal state (`build_failed`, `update_failed`, `pre_deploy_failed`, `canceled`, `deactivated`).
5. **Health check** — Polls `https://horoconsultant-core-backend.onrender.com/health` until HTTP `200` (up to 20 attempts, 10s apart).
6. **Vercel smoke test** — Requests `{VERCEL_STATIC_URL}/health` (default `https://horo-consultant-psi.vercel.app`) and requires HTTP `200`, verifying the full Vercel → Render production path end-to-end.

Workflow timeout: 30 minutes total.

### Manual dispatch

Run *Render Docker Backend - Production Deployment* from the GitHub Actions **Actions** tab → *Run workflow*, on branch `main`. Optionally provide `source_sha` (full commit SHA) to publish a specific commit; it defaults to the dispatch commit. Manual runs on non-`main` refs are rejected by the job's `if` guard.

---

## 5. Failover Runbook (Render Down → Revert to HF Space)

The gateway reads `RENDER_BACKEND_URL` at deploy time. Setting it empty (or unsetting it) makes `configuredRenderBackendOrigin()` return `null`, dropping Render from the origin list so the HF Space becomes the sole upstream — with no code change.

1. **Confirm Render is impaired**

   ```bash
   curl -s -o /dev/null -w "%{http_code}" https://horoconsultant-core-backend.onrender.com/health
   ```

   Non-`200` (or timeout) confirms the outage. Note: the gateway auto-fails-over per request, so clients may still be served via HF Space — this runbook makes the fallback authoritative and removes Render's latency penalty.

2. **Empty `RENDER_BACKEND_URL` in Vercel** — Vercel dashboard → Project → Settings → Environment Variables → set `RENDER_BACKEND_URL` to an empty value (or remove it) for Production. Redeploy the gateway to apply.

3. **Wake the HF Space** — The free-tier Space may be paused. Trigger the gateway wake endpoint:

   ```bash
   curl -X POST https://horo-consultant-psi.vercel.app/api/wake
   ```

   Behavior of `POST /api/wake`:
   - If any configured origin already answers `/health` → `{"status": "ready"}`.
   - Otherwise, if `HF_TOKEN` is configured on the gateway, it POSTs to the Hugging Face Space restart API → `{"status": "waking", "estimated_seconds": 60}`.
   - Without `HF_TOKEN` → `{"status": "paused_unauthenticated"}`; restart the Space manually from `https://huggingface.co/spaces/pphothidaen/horoconsultant-core-backend`.

4. **Verify**

   ```bash
   curl -s -o /dev/null -w "%{http_code}" https://horo-consultant-psi.vercel.app/health
   ```

   Expect `200`.

5. **Restore Render later** — Once Render is healthy again (`/health` → `200`), set `RENDER_BACKEND_URL=https://horoconsultant-core-backend.onrender.com` back in Vercel and redeploy. Render resumes as primary.

---

## 6. Expected Metrics

| Metric | Target | Notes |
| :--- | :--- | :--- |
| Deploy time (CI success → Render `live`) | < 5 min | Render Docker build + release; workflow polls up to ~15 min as safety margin |
| Cold start (free tier) | < 30 s | Free plan spins down after ~15 min idle; first request pays the wake cost, `/health` polling in CI tolerates this |
| Availability | 24/7 | Render auto-deploy on `main` + gateway per-request failover to the HF Space |
| Gateway upstream timeout | 8 s (default) | Configurable via `VERCEL_BACKEND_TIMEOUT_MS`, capped at 30 s |
| Health check | `/health` → `200` | Used by Render (`healthCheckPath`), CI verification, and `POST /api/wake` probing |
