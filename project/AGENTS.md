# project/ — Core Application Source

## Purpose
FastAPI application entrypoint and all Python business logic for the Computational Metaphysics Engine.

## Key Files
- `project/main.py` — FastAPI app entrypoint (`uvicorn project.main:app`)
- `project/admin_router.py` — Admin panel API (provider-pools, gray-zone, finetune)
- `project/core/` — Solar Time, BaZi Engine, SVG, Code Reviewer
- `project/rag/` — FAISS vector DB, ingestion, fine-tune export
- `project/routers/` — API route handlers
- `project/static/` — Glassmorphism Web UI frontend
- `project/tests/` — Production verification regression tests

## Environment Variables (from `.env`)
- `APP_PORT=8000` — Local FastAPI port
- `ADMIN_ALLOWED_EMAILS` — Google OAuth whitelist
- `GOOGLE_CLIENT_ID` — Google OAuth audience verification
- `HF_BACKEND_URL` — Canonical HF Docker backend origin
- `OLLAMA_BASE_URL` — Local Ollama endpoint
- `REDIS_URL` — Cache connection

## Commands
```bash
python3 -m uvicorn project.main:app --reload --port 8000
python3 -m pytest project/tests/ -v
```

## Agent Rules
- Never commit `.env` or secrets
- Admin routes require Google OAuth `id_token` in `Authorization: Bearer` header
- Provider-pools endpoint returns live circuit breaker + quota pool state
