# Rule 24: Red/Blue Team Architecture & Test Impact Analysis (TIA)

## 1. Adversarial Dual-Team Operating Model

Engineering lifecycle enforces adversarial separation between builders and auditors:

- **Blue Team (The Builders)**: `developer`, `devops`, `business_analyst`, `orchestrator`, `ux_ui_designer`.
  - *Mindset*: **Analytical & Critical Thinking** (First Principles, Modular Architecture, Contract-Driven, Clean Code).
  - *Mission*: Construct robust features, ensure type safety, optimize performance, adhere to architectural standards.
- **Red Team (The Adversaries / Auditors)**: `qa_tester`, `code_reviewer`, `ui_visual_tester`, `prediction_validator`.
  - *Mindset*: **Inversion Thinking** ("Assume code is broken until proven otherwise").
  - *Mission*: Attack assumptions, find edge cases, test boundary faults, probe secret leaks, prevent regressions.

## 2. Four-Tier Testing Paths

Testing execution must follow tiered paths based on scope:

1. **Atomic Path**: Micro calculation formulas, Julian Day, BaZi 4-Pillars, PyO3 Math Core. Isolated, deterministic, zero-mock.
2. **System Path**: Component interoperability, API Gateways, FAISS RAG, Multi-Provider Router Failover, database integrity.
3. **Smoke Path**: Rapid critical readiness verification (`/health` gate, Cloudflare Worker proxy readiness, < 5s).
4. **Happy Path**: End-to-end user workflows, Playwright UI button regression, Five Elements visual theme rendering.

## 3. Test Impact Analysis (TIA) Selective Testing Matrix

To avoid overengineering and wasteful full test runs (4,000+ tests), select test suites based on `git diff`:

| Scope of Changes (`git diff`) | Verification Command | SLA Target |
|---|---|---|
| **Docs / Rules Only** (`*.md`, `.agents/`, `.claude/`, `.agy/`) | `python3 scripts/sync_ai_agent_ecosystem.py --check` | < 3s |
| **UI / CSS Only** (`project/static/**`, CSS, layouts) | `python3 scripts/run_button_regression.py` | < 20s |
| **Rust Core Only** (`rust_core/**`) | `cargo test` and BaZi unit tests | < 15s |
| **API Routers Only** (`project/routers/**`) | Gateway contract tests (`pytest project/tests/test_gateway*.py`) | < 20s |
| **Pre-Release / PR to main** | Full regression suite on GitHub Actions CI (asynchronous) | Async CI |

## 4. Fail-Fast Execution Parameters

During bug fixing and iterative development, test runners must enforce fail-fast parameters:
- `pytest -x`: Stop execution immediately on the first failed test.
- `pytest --lf`: Rerun only tests that failed in the previous test execution run.
- Combine `pytest -x --lf` for ultra-rapid triage loops before widening to tier regression.
