# api/ — Vercel Serverless Gateway

## Purpose
Least-privilege Vercel gateway that proxies requests to the canonical Hugging Face Docker backend.

## Key Files
- `api/index.js` — Main Vercel Function handler (Node.js)
- `api/gateway.js` — CORS policy enforcement

## Rewrites (vercel.json)
All traffic routes through `/api/index?path=...`:
- `/health`, `/docs`, `/openapi.json` — Public read
- `/api/v1/:path*`, `/api/v2/:path*`, `/api/v3/:path*` — Public API
- `/admin/:path*` — Privileged (requires Google OAuth Bearer)
- `/hitl/stats` — Privileged read

## Environment Variables
- `HF_BACKEND_URL` — Canonical HF Space origin (validated at boot)
- `VERCEL_BACKEND_TIMEOUT_MS` — Backend timeout (default 8000ms, max 30000ms)
- `VERCEL_GIT_COMMIT_SHA` — Injected by Vercel, returned in `X-Deploy-SHA`

## Security
- Only `https://pphothidaen-horoconsultant-core-backend.hf.space` is accepted as backend
- Privileged paths require `Authorization: Bearer <Google_ID_token>`
- Path traversal, null-bytes, and URL-encoded attacks are rejected
