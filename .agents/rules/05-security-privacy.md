# 📜 Rule 05: Security, Secrets & Privacy Standards
> **Scope:** Entire Repository, `.env`, `project/core/code_reviewer.py`

## 📌 Requirements
1. **No Secret Leaks**: Tokens (`KAGGLE_TOKEN`, `HF_TOKEN`, `GOOGLE_AI_STUDIO_API_KEY`, `GH_TOKEN`) must never be hardcoded into source files or committed to Git.
2. **Doppler & Environment Fallback**: Load secrets via `os.getenv` or Doppler Config with fallback to `.env.production` / `.env`.
3. **Automated Safety Audit**: Run `python3 project/core/code_reviewer.py --review` before committing to scan for secret leakage and security vulnerabilities.
