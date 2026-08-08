---
name: qa-e2e-testing
description: >-
  Quality Assurance & E2E Testing skill. Provides procedures for Pytest test execution, UI button contract
  regression testing, Playwright E2E visual screen capture verification, and bug traceback extraction.
---

# 🧪 QA & E2E Testing Skill Guide

This skill specifies testing standards, regression execution commands, and log filtering protocols for the QA Tester and Developer agents.

---

## 🛠️ Testing Command Suite

### 1. Pytest Unit & Integration Regression Suite
Run full test suite with verbose output:
```bash
python3 -m pytest -v --ignore=project/kaggle_kernel
```
*Goal*: Ensure 100% pass rate across all 123 test cases (BaZi, Swiss Ephemeris, 5-branch Metaphysics, RAG, MCP, API Router).

### 2. UI Button & Endpoint Contract Regression Suite
Run full 25-button/endpoint contract check across `index.html` (Main Dashboard), `admin.html` (Admin Panel), `hitl.html` (HITL Review Studio), and `OpenAPI Documentation` (`/docs`, `/redoc`, `/openapi.json`):
```bash
python3 scripts/run_button_regression.py
```
*Report Output*: `project/tests/button_regression_report.json`

### 3. Playwright E2E Browser Screenshot Visual Verification
Run browser automation, test UI interactions, and capture full-page screenshots across all 4 Core UI Components (Main Dashboard, Admin Panel, HITL Review Studio, OpenAPI Interactive Docs):
```bash
python3 scripts/run_e2e_screenshots.py
```
*Screenshots Output*: `project/tests/screenshots/`

---

## 🛡️ QA Rules & Guidelines

1. **Zero Superficial Symptom Patching**:
   - Never resolve failing tests by commenting out assertions, deleting tests, returning dummy fallbacks, or swallowing exceptions in silent try/except blocks.
   - Trace upstream root causes in source modules.

2. **Log Extraction Protocol**:
   - Extract only relevant error snippets (file, line number, exception traceback) when reporting bugs to the Developer or Orchestrator.
   - Keep log output concise to preserve token context window.

3. **Post-Deployment Mandatory Verification**:
   - After any push to `main` or production release, always re-run `python3 scripts/run_button_regression.py` to confirm live system functionality.
