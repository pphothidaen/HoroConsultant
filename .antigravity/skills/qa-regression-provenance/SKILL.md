---
name: qa-regression-provenance
description: Run fail-closed regression baseline verification and test-provenance tracking.
---

# QA Regression Provenance

Fail-closed regression baseline verification and test-provenance tracking.

## Purpose

Enforce immutable RED test baselines before source implementation begins and maintain
unbroken provenance chains across tickets.

## Principles and Contracts

1. **Immutable RED Baseline**:
   - Every bug fix or feature starts with a test-only commit capturing the failing test.
   - Never comment out assertions, delete tests, add dummy fallbacks, or weaken checks.
   - Test mutations during source remediation are strictly forbidden.

2. **Test-Provenance-v1 Manifest**:
   - Bind exact test file SHA-256 digests.
   - Record assertion-level RED command fingerprints.
   - Separate QA test owner (`qa_tester`) and independent code reviewer (`code_reviewer`).

3. **Superseding Baselines**:
   - Any baseline correction requires an authorized, independently reviewed superseding baseline.
   - The superseding record must cite the prior baseline digest and explicit rationale.
   - Reconstructed history remains `NON_TDD_RECONSTRUCTED`.

## Verification Workflow

1. Execute test command to establish failing RED state:
   ```bash
   pytest tests/test_target.py -k "repro"
   ```
2. Compute test file SHA-256 digests:
   ```bash
   sha256sum tests/test_target.py
   ```
3. Generate or verify `test-provenance-v1` manifest.
4. Report status with standard ASCII tags:
   - `[OK]`: Baseline frozen and verified against schema.
   - `[ERROR]`: Mutation or missing test hash detected.
   - `[WARNING]`: Deprecated test structure identified.
   - `[INFO]`: Provenance manifest registered.

## Gotchas

- Never alter frozen test digests directly in manifests without reviewer sign-off.
- Pure ASCII logs only: `[OK]`, `[ERROR]`, `[WARNING]`, `[INFO]`.
