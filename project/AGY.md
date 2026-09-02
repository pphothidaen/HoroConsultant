# project/ — AGY CLI Operating Contract

## Verified Commands
```bash
python3 -m uvicorn project.main:app --reload --port 8000
python3 -m pytest project/tests/ -v
python3 project/core/code_reviewer.py --review
```

## Subsystems
- `core/` — Astro-calculation engine (NOAA Spencer 1971, Swiss Ephemeris, BaZi)
- `rag/` — FAISS vector DB + vault ingestion
- `routers/` — REST/WebSocket route handlers
- `static/` — Glassmorphism dark UI frontend

## Git Hygiene
- Atomic commits: `feat:`, `fix:`, `refactor:`, `test:`
- Never `git add .` — stage targeted files only
- Draft PRs: `gh pr create --draft`

## Log Sanitization
Keep main terminal output under 30 lines. Use `.agy/scripts/tmux-runner.sh` for heavy outputs.
