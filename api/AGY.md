# api/ — AGY CLI Operating Contract

## Verified Commands
```bash
node -c api/index.js   # syntax check
```

## Environment Variables
- `HF_BACKEND_URL` — Canonical HF Space origin
- `VERCEL_BACKEND_TIMEOUT_MS` — Backend timeout (default 8000ms)

## Path Routing
- `/admin/:path*` → `/api/index?path=/admin/:path*` (privileged)
- `/hitl/stats` → `/api/index?path=/hitl/stats` (privileged read)
- `/api/v1/:path*` → `/api/index?path=/api/v1/:path*` (public)
