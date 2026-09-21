# Deployment Rail Architecture

## Overview

HoroConsultant uses a **dual-layer deployment**: a Rust `horo_server` gateway sits in front of a Python uvicorn worker. The gateway serves some routes natively (health, native math kernels) and proxies others to Python via localhost.

## Architecture Diagram

```
                    ┌──────────────────────────────┐
                    │    Render / Docker           │
                    │    ├── Dockerfile (Rust)     │   ← Production
                    │    │   PID 1: horo_server    │
                    │    │   PID 2: uvicorn        │   ← Python worker
                    │    └── HORO_ALLOW_PYTHON_    │
                    │        FALLBACK=0          │
                    └──────────────┬───────────────┘
                                   │ localhost:8000
                                   ▼
                    ┌──────────────────────────────┐
                    │  Rust horo_server            │
                    │  ├─ Native routes            │
                    │  │   /health → Liveness       │
                    │  │   /api/v1/bazi/calculate  │
                    │  ├─ PythonProxy routes       │
                    │  │   /admin/*, /hitl/*, etc.  │
                    │  └─ 404 fallback             │
                    └──────┬──────────┬───────────┘
                           │          │
            (native response)│          │(HTTP proxy)
                           │          │
                           ▼          ▼
                    ┌──────┴──┐  ┌────┴─────────────────┐
                    │ Client  │  │ Python uvicorn       │
                    │         │  │ ├── FastAPI app      │
                    │         │  │ ├── admin_auth_      │
                    │         │  │ │   middleware       │
                    │         │  │ └── All API routes   │
                    └─────────┘  └──────────────────────┘
```

## Dockerfiles

| File | Purpose | CMD | Used by |
|---|---|---|---|
| `Dockerfile` | Rust gateway + Python worker (subprocess) | `["/app/horo_server"]` | **Production (Render)** |
| `Dockerfile.render` | Python uvicorn only | `python3 -m uvicorn project.main:app` | Development / local |

### `render.yaml`

```yaml
services:
  - type: web
    name: horo-core
    # NOTE: Currently Render uses the default Dockerfile (Rust gateway),
    # NOT Dockerfile.render. This is a known mismatch. See ISSUE-023.
    healthCheckPath: /health
```

## Routing Table Sync

The Rust gateway's `route_kind()` function in `rust_core/src/server.rs` is a **closed allowlist**. Any route not listed returns 404 from the Rust fallback handler — even if the Python app has a valid handler.

### How routes are synchronized

1. Every new Flask/FastAPI route must be added to `route_kind()` in `server.rs`
2. `tests/test_route_sync.py` enforces this — fails CI if OpenAPI routes are missing from Rust table
3. Run `cargo check --features server` after modifying `server.rs`

### RouteKind variants

| Variant | Handler | Example |
|---|---|---|
| `Liveness` | Native Rust response | `GET /health` → `{"status":"ok","service":"..."}` |
| `Readiness` | Native Rust response | `GET /api/v1/health` |
| `NativeBazi` | Rust math kernel | `POST /api/v1/bazi/calculate` |
| `NativeEquationOfTime` | Rust math kernel | `GET /api/v1/eot` |
| `PythonProxy` | HTTP proxy to localhost:8000 | All `/admin/*`, `/api/v2/*` routes |

## Environment Variables

| Variable | Scope | Default | Description |
|---|---|---|---|
| `HORO_ALLOW_PYTHON_FALLBACK` | Rust + Python | `0` | When `0`, unmatched routes return 404. When `1`, proxy to Python anyway |
| `GATEWAY_PORT` | Rust | `8000` | Port Python worker listens on |
| `HORO_SERVER_PORT` | Rust | `80` | Port Rust gateway listens on |

## Incident History

### INCIDENT-021 (Sep 21, 2026): `/admin/provider-pools` 404

**Root cause**: `/admin/provider-pools` route added to Python `admin_router.py` in commit `dcd154c1` (Aug 29) but never added to the Rust `route_kind()` allowlist. Production was running the Rust gateway (`Dockerfile`, not `Dockerfile.render`).

**Fix**: Added the missing route to `route_kind()` in `rust_core/src/server.rs:240`.

**Prevention**: Added `tests/test_route_sync.py` contract test — runs in CI.

## References

- `rust_core/src/server.rs` — Rust gateway source (routing table + gateway handler)
- `rust_core/tests/test_gateway_contract.rs` — Rust-side gateway tests
- `tests/test_route_sync.py` — Python-side route sync contract test
- `project/main.py` — Python FastAPI app (middleware, route registration)
- `project/admin_router.py` — Admin route definitions
- `Dockerfile` — Rust gateway production Dockerfile
- `Dockerfile.render` — Python-only Dockerfile (development)
- `render.yaml` — Render service configuration
