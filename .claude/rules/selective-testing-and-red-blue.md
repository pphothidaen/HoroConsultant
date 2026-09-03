---
description: Red Team vs Blue Team governance and Test Impact Analysis (TIA) selective testing rules.
paths: ["tests/**/*", "project/tests/**/*", ".agents/rules/24-*", "scripts/*test*.py"]
---

# Red/Blue Governance & Selective Testing (TIA)

## Dual-Team Operational Governance
- **Blue Team (Builders)**: `developer`, `devops`, `orchestrator`, `ui_designer`. Mindset: **Analytical & Critical Thinking** (First Principles, contracts, modular architecture).
- **Red Team (Auditors)**: `qa_tester`, `code_reviewer`, `prediction_validator`. Mindset: **Inversion Thinking** ("Assume code is broken until proven otherwise").

## 4-Tier Testing Paths
1. **Atomic Path**: Core mathematical formulas, Julian Day, BaZi 4-Pillars, PyO3 FFI.
2. **System Path**: API Gateways, FAISS RAG, Multi-Provider Router failover.
3. **Smoke Path**: Critical readiness checks (`/health` gate, Cloudflare proxy < 5s).
4. **Happy Path**: End-to-end user workflows, Playwright button regression, theme visual testing.

## Test Impact Analysis (TIA) Matrix (Git Diff Driven)
- **Docs/Rules Only**: Run `python3 scripts/sync_ai_agent_ecosystem.py --check` (< 3s).
- **UI/CSS Only**: Run `python3 scripts/run_button_regression.py` (< 20s).
- **Rust Core Only**: Run `cargo test` and BaZi unit tests (< 15s).
- **API Routers Only**: Run Gateway contract tests (< 20s).
- **Pre-Release / PR to main**: Run Full Regression suite asynchronously on GitHub Actions CI.

## Fail-Fast Enforcement
- Use `pytest -x` to stop on the first failure during debugging.
- Use `pytest --lf` to rerun only failed tests.
- Combine `pytest -x --lf` for fast iterative feedback before running full TIA scope.
