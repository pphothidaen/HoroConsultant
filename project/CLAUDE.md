# project/ — Claude Code Operating Contract

## Governance Level
Level 3 global context — see `.claude/rules/` for path-scoped rules and `.claude/settings.json` for hard constraints.

## Architecture
- FastAPI + Uvicorn on port 8000
- Rust PyO3 extensions for high-performance math (BaZi, Solar Time, LuoPan)
- FAISS vector store (dim=768, `nomic-embed-text`)
- Multi-tier LLM routing: Local Ollama → Gemini Cloud → 9router proxy

## Safety
- `ADMIN_ALLOWED_EMAILS` controls admin panel access
- Google OAuth `aud` verification enforced against `GOOGLE_CLIENT_ID`
- Zero-cost billing policy: `ai_router.zero_cost_only`

## Testing
```bash
python3 -m pytest project/tests/ -v
python3 scripts/run_prod_version_e2e.py
python3 scripts/run_luopan_e2e_regression.py
```
