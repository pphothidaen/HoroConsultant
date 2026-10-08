# HoroConsultant Architecture

## Overview
HoroConsultant is a multi-agent astrological consultation platform deployed across Cloudflare Workers, Render, and Vercel with Cloudflare D1 as the durable data layer.

---

## Active Architecture (Post-KAN-274, Post-KAN-173, Post-KAN-275/276)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            USER REQUEST                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CLOUDFLARE EDGE (Global)                              │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐  │
│  │  aipass-web-bridge  │  │ gemini-web-bridge   │  │  hermes-web-bridge  │  │
│  │  (OpenAI proxy)     │  │  (Gemini proxy)     │  │  (webhook bridge)   │  │
│  │  taijustarrett417   │  │  prod.gemini-web-   │  │  (CI webhooks)      │  │
│  │  .workers.dev       │  │  bridge.workers.dev │  │                     │  │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
┌─────────────────────────┐ ┌──────────────┐ ┌────────────────────┐
│     RENDER (Backend)    │ │  VERCEL      │ │  CLOUDFLARE D1     │
│  horoconsultant-core-   │ │  (Static UI) │ │  (Durable Outbox)  │
│  backend.onrender.com   │ │  horo-       │ │  - Sync bookkeeping│
│  - FastAPI (Docker)     │ │  consultant  │ │  - Idempotency     │
│  - Rust gateway (opt)   │ │  -psi.vercel │ │  - Lease/fencing   │
│  - 60s cold start       │ │  .app        │ │  - Heartbeat       │
│  - KAN-272 503 semantics│ │              │ │  - 5GB, no expiry  │
└─────────────────────────┘ └──────────────┘ └────────────────────┘
                    │               │               │
                    └───────────────┼───────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATA LAYER                                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │  Google Drive   │  │  Obsidian Vault │  │  Vector Store (derived)     │
│  │  (Authoritative)│──▶│  (Derived,     │──▶│  (Derived, recomputable)    │
│  │  - Folder IDs   │  │   git-tracked)  │  │  - .dockerignore excluded   │
│  │  - Source corpus│  │                 │  │  - Rebuilt from vault       │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Architectural Decisions

### 1. KAN-274 Option A: Render + Cloudflare D1 Outbox (APPROVED)
**Decision**: Stay on Render for backend hosting; add Cloudflare D1 durable outbox for sync bookkeeping.

**Rationale**:
- Fixes KAN-275 silent data loss (nightly sync writes to ephemeral FS)
- D1: 5GB, no expiry, free forever on existing Cloudflare account
- No new provider, no ARM64 rebuild, no second ops surface
- Corpus is derived from Google Drive → reclamation = rebuild, not permanent loss
- Keeps all existing contracts (KAN-272 503/502, KAN-268/269/270/271/273)

**Rejected**: 
- Option B: Koyeb edge + D1 (held as independent follow-up for cold-start)
- Option C: Koyeb + Oracle (ARM64 rebuild, unproven volume survival, 2 providers)
- Status quo: leaves silent data loss defect

### 2. KAN-173: Ops Watchdog for CD Pipeline
**Problem**: 51-minute silent stall at `environment: production` gate with no alert.

**Solution**: Scheduled watchdog workflow (`cd-watchdog.yml`, every 10 min) that:
- Detects deployments stuck > 15 min in `pending`/`queued`
- Creates idempotent GitHub tracker issue + Jira alert
- Auto-closes on deployment success
- Respects `cd-concurrency-audit` gate

**Runbook**: `docs/CD-STALL-RUNBOOK.md`

### 3. KAN-275/276: HF Static Retired
**Change**: Removed Hugging Face Spaces (`.hf.space`) from architecture.

**Before**: Dual backend targets (Render + HF Spaces) with fallback logic
**After**: Single canonical Render backend (`horoconsultant-core-backend.onrender.com`)

**Code changes**:
- `synthetic_health_monitor.py`: Removed `DEFAULT_HF_BACKEND_URL` fallback
- `_backend_url()`: Prefers `RENDER_BACKEND_URL` only
- `_assert_separated_targets()`: Rejects `HF_STATIC_SPACE_ID` configuration
- CI/CD: Removed HF deploy workflows

---

## Component Details

### Cloudflare Workers (Bridges)

| Bridge | Endpoint | Purpose | Version |
|--------|----------|---------|---------|
| aipass-web-bridge | `taijustarrett417.workers.dev` | OpenAI-compatible proxy → de.aipass.net | Primary |
| gemini-web-bridge | `prod.gemini-web-bridge.workers.dev` | Gemini API proxy | v4.4.3 |
| hermes-web-bridge | (internal) | CI webhook bridge via Cloudflare Tunnel | - |

**Bridge Principles**:
- No secrets in bridge code (Cloudflare Workers don't store secrets in code)
- Secrets via Cloudflare Workers KV / Doppler / GitHub secrets
- Proxies only — no business logic

### Render Backend
- **Service**: `horoconsultant-core-backend` (Docker)
- **URL**: `https://horoconsultant-core-backend.onrender.com`
- **Cold start**: ~60 seconds (free tier)
- **Health semantics**: KAN-272 honest 503 + Retry-After header
- **Contracts**: KAN-268/269/270/271/273 enforced via tests

### Vercel Static UI
- **URL**: `https://horo-consultant-psi.vercel.app`
- **Assets**: `index.html`, `app.js`, `sw.js`, `version.json`
- **Version verification**: Exact release identity match with backend

### Cloudflare D1 (Durable Outbox)
- **Database**: `horoconsultant-sync` (or similar)
- **Tables**: `sync_outbox`, `sync_leases`, `sync_heartbeats`
- **Schema**: idempotency key (`sync-YYYY-MM-DD`), lease token, status, heartbeat
- **Quota**: 5GB storage, 5M reads/day, 100k writes/day (Workers Free)
- **No expiry** — unlike Cloudflare Queues (24h retention)

---

## Data Flow: Nightly Sync (Post-KAN-274)

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Scheduler  │───▶│  D1: Create │───▶│  Download   │───▶│  Build      │
│  (cron)     │    │  outbox row │    │  from Drive │    │  vector     │
│             │    │  (lease +   │    │  (gdown)    │    │  store      │
│             │    │  idempotency)│    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                          │                                       │
                          ▼                                       ▼
                   ┌─────────────┐                        ┌─────────────┐
                   │  D1: Update │◀───────────────────────│  D1: Mark   │
                   │  heartbeat  │   (on progress)        │  success +  │
                   │  periodically│                        │  release    │
                   └─────────────┘                        │  lease      │
                                                         └─────────────┘
```

**Durability Patterns** (from KAN-274 Research):
| Need | Pattern | Store | Why |
|------|---------|-------|-----|
| Durable bookkeeping | Outbox table | D1 | No expiry; Queues 24h too short for nightly |
| Safe retry | Idempotency key | D1 row | `sync-YYYY-MM-DD` makes retry effectively-once |
| Single writer | Lease + fencing | D1 row | Kleppmann fencing tokens, not Redlock |
| Rebuild detection | Heartbeat + last-success | D1 | Turns silent loss into loud, queryable failure |

---

## Monitoring & Alerting

### Production Synthetic Monitor (`.github/workflows/production_monitor.yml`)
- **Schedule**: Every 15 minutes (`*/15 * * * *`)
- **Targets**: 
  - Vercel static UI (HTML, version.json, app.js, sw.js)
  - Render backend `/health`
- **Verification**: Exact release identity match (version.json on both)
- **Notifications**: Generic webhook, Slack, Discord, Telegram
- **Metrics**: Grafana OTLP (optional)

### CD Watchdog (KAN-173)
- **Schedule**: Every 10 minutes (`*/10 * * * *`)
- **Target**: `gemini-web-bridge` worker deployments
- **Stall threshold**: 15 minutes in `pending`/`queued`
- **Alert**: GitHub Issue + Jira ticket
- **Auto-close**: On deployment `success`

### Health Check Endpoints
| Endpoint | Expected Response | SLA |
|----------|-------------------|-----|
| `https://horoconsultant-core-backend.onrender.com/health` | `{"status":"ok"}` | < 5s |
| `https://horo-consultant-psi.vercel.app/version.json` | Release metadata | < 3s |
| `https://prod.gemini-web-bridge.workers.dev/health` | `{"status":"ok"}` | < 3s |

---

## Security & Secrets

### Secret Management
- **Doppler**: Project-scoped configs for each bridge/worker
- **Cloudflare Workers**: Secrets via `wrangler secret put` (not in code)
- **GitHub Actions**: `secrets.*` for CI/CD
- **HITL**: Human-in-the-loop for secret rotation (never auto-commit)

### Access Boundaries
- Per-provider Doppler scopes (aipass-web-bridge, gemini-web-bridge, hermes-web-bridge)
- Cloudflare Access + restricted ingress
- TLS 1.3 / mTLS in transit
- Encryption at rest (provider-managed)

---

## Disaster Recovery

### Rollback Procedures
1. **Worker rollback**: `wrangler rollback` or redeploy previous version
2. **Render rollback**: Re-deploy previous Docker image tag
3. **Vercel rollback**: Promote previous deployment in Vercel dashboard
4. **D1 rollback**: Point-in-time recovery not available; rebuild from Drive

### Blast Radius
- **Worker failure**: Single bridge affected; others independent
- **Render failure**: Backend down; UI shows cached/stale data
- **Vercel failure**: UI down; API still functional
- **D1 failure**: Sync bookkeeping lost; next run recreates (idempotent)

---

## Capacity & Limits

| Resource | Limit | Current Usage | Headroom |
|----------|-------|---------------|----------|
| Cloudflare Workers Free | 100k requests/day | ~10k/day | 90% |
| Cloudflare D1 Free | 5GB, 5M reads/day | < 100MB | 98% |
| Render Free | 750 hrs/mo, sleeps after 15min idle | ~500 hrs | 33% |
| Vercel Hobby | 100GB bandwidth | ~5GB | 95% |
| GitHub Actions | 2000 min/mo (private) | ~800 min | 60% |

---

## Related Documentation

| Document | Purpose |
|----------|---------|
| `docs/CD-STALL-RUNBOOK.md` | KAN-173 watchdog operations |
| `docs/deployment/render-backend-deployment.md` | Render deployment details |
| `docs/RELEASE_ROLLBACK_RUNBOOK.md` | Release rollback procedures |
| `docs/governance-as-code.md` | KAN-105 governance rules |
| `reviews/KAN-274-cross-functional-review.md` | Full decision record |

---

## Version History

| Date | Change | Ticket |
|------|--------|--------|
| 2026-10-08 | KAN-274 Option A approved; KAN-173 watchdog deployed; HF Static retired | KAN-274, KAN-173, KAN-275/276 |
| 2026-09-29 | Initial architecture docs | — |