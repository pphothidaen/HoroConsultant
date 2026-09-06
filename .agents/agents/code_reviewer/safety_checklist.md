# Pre-Deployment Safety Review Checklist

Authority: TICKET-SAFE-SPARK-CR-001 / Rule 21 & Rule 22 Agile Governance
Role: code_reviewer (Pre-Deployment Safety Auditor)
Engine: project/core/code_reviewer.py
Status: MANDATORY PRE-DEPLOYMENT GATE

## Overview
This checklist governs all release preflight audits. No pull request or release branch may be granted a READY_FOR_PROD verdict without passing every gate specified herein. Evaluation is strictly fail-closed: any anomaly, unhandled exception, or missing evidence immediately halts the release pipeline with status BLOCKED.

---

## Pre-Deployment Verification Gates

### Gate 1: AST & Syntax Integrity Gate
- [ ] Command: python3 project/core/code_reviewer.py --audit-ast
- [ ] Requirement: Scans all Python source files (*.py) in the repository.
- [ ] Verification criteria:
  * AST Parse: ast.parse() succeeds on every Python file without SyntaxError, IndentationError, or TabError.
  * Bytecode Compilation: compile(..., "exec") succeeds with zero compilation errors.
  * Null Byte Rejection: 0 files contain null bytes (\x00) indicating corruption or binary payload injection.
  * Surrogate Encoding Check: 0 lone surrogate code points (0xD800 to 0xDFFF) that cause runtime crashes.
  * UTF-8 Decoding: 100% of tracked Python files decode cleanly as strict UTF-8.
- [ ] Pass condition: status == "PASSED" and issues_found == 0.

### Gate 2: Zero-Secret-Leak Gate
- [ ] Command: python3 project/core/code_reviewer.py --scan-secrets
- [ ] Requirement: Comprehensive secret pattern scanning across all repository files.
- [ ] Token patterns verified:
  * Google AI Studio API Keys (AIzaSy...)
  * Hugging Face User Access Tokens (hf_...)
  * Kaggle API Tokens (kg_...)
  * Doppler Service Tokens (dp.pt....)
  * GitHub Personal Access Tokens (ghp_...)
  * Docker Hub Personal Access Tokens (dckr_pat_...)
  * Grafana Cloud API Keys (glc_...)
  * OpenAI API Keys (sk-... / sk-proj-...)
  * Anthropic API Keys (sk-ant-...)
  * AWS Access Key IDs (AKIA...)
  * Private Key Headers (-----BEGIN ... PRIVATE KEY-----)
  * Slack Bot & User Tokens (xoxb-... / xoxp-...)
  * Telegram Bot Tokens ([0-9]{9,10}:[a-zA-Z0-9_-]{35})
- [ ] Exclusion rules: .env files, gitignored credentials, and explicit test canaries with dummy tokens.
- [ ] Pass condition: status == "PASSED" and secret_leaks_found == 0.

### Gate 3: Automated Test Regression Gate
- [ ] Command: python3 -m pytest -q --ignore=project/kaggle_kernel
- [ ] Requirement: 100% test pass rate across the unit and contract test suites.
- [ ] Verification criteria:
  * Zero failed tests (failed == 0).
  * Zero test errors (errors == 0).
  * Process exit code is strictly 0.
- [ ] Pass condition: status == "PASSED" and exit_code == 0.

### Gate 4: Test Provenance & Evidence Receipt Gate
- [ ] Command: python3 project/core/code_reviewer.py --ticket <TICKET_ID> --test-baseline <SHA> --test-manifest <PATH>
- [ ] Requirement: Enforce immutable test-first development history under Rule 02 and Rule 21.
- [ ] Verification criteria:
  * Test manifest exists and matches the ticket ID.
  * Committed test baseline commit SHA exists and is an ancestor of HEAD.
  * Test file SHA256 hashes match the immutable provenance manifest.
  * No test tampering or retroactive mutation after freeze.
- [ ] Pass condition: status == "PASSED" (or "NOT_REQUESTED" if running unticketed local checks).

### Gate 5: Dependency & Notebook Safety Gate
- [ ] Command: Internal checks executed via python3 project/core/code_reviewer.py --review
- [ ] Verification criteria:
  * Kaggle notebook setup does not reinstall torch over pre-compiled CUDA binaries.
  * Jupyter notebooks parse as valid JSON and contain zero code cell SyntaxErrors.
  * No forbidden deprecated packages (e.g. accelerate==0.33.0, datasets==2.18.0).
- [ ] Pass condition: notebook_audit status == "PASSED" and kaggle_cuda_audit status in ("PASSED", "WARNING").

---

## Codified Stop Conditions (Fail-Closed Verdict Matrix)

Release pipeline is immediately BLOCKED upon tripping ANY of the following stop conditions:

| Stop Condition Code | Threshold Trigger | Action |
|:---|:---|:---|
| STOP_CONDITION_SECRET_LEAK | secret_leaks_found > 0 | Abort release; revoke leaked credential; clean commit history |
| STOP_CONDITION_AST_ANOMALY | issues_found > 0 in AST audit | Abort release; fix syntax/encoding anomaly immediately |
| STOP_CONDITION_TEST_REGRESSION | exit_code != 0 in pytest | Abort release; developer must resolve all test failures |
| STOP_CONDITION_NOTEBOOK_FAILURE | issues_found > 0 in notebook audit | Abort release; repair corrupted cell or invalid dependency |
| STOP_CONDITION_KAGGLE_CRITICAL | status == "FAILED" in Kaggle audit | Abort release; restore pre-compiled CUDA binary configuration |
| STOP_CONDITION_PROVENANCE_FAILURE | issues found in provenance audit | Abort release; regenerate or correct test provenance manifest |

---

## Release Approval Invariant
A release verdict of READY_FOR_PROD is granted IF AND ONLY IF:
1. All 5 Gates are evaluated and recorded.
2. The stop_conditions array is strictly empty ([ ]).
3. Audit report is serialized in pure ASCII format with machine-readable timestamps.
