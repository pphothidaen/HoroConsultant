# 📜 Rule 02: Testing & Verification Standards
> **Scope:** `project/tests/*.py`, `tests/*.py`

## 📌 Requirements
1. **Pytest Integration**: All test cases must run via `python3 -m pytest -v`.
2. **100% Pass Policy**: No pull request or code change is accepted until all 80 unit & integration tests pass with Exit Code 0.
3. **No Masking**: Never resolve errors by swallowing exceptions, deleting failing assertions, or adding dummy try-except blocks.
4. **Deterministic Testing**: Verify solar time calculations, 4-Pillars BaZi Engine output, FAISS vector queries, and API endpoints deterministically.
5. **Post-Goal Mandatory E2E & CI/CD**: Upon completion of any goal/task, agents MUST run E2E Playwright screenshots, button regression testing (`run_button_regression.py`), and verify CI/CD release readiness before declaring success.

