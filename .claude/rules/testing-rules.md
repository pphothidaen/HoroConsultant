---
description: Test quality gates, regression requirements, and zero-mock verification standards.
paths: "tests/**/*, scripts/*regression*.py"
---

# Testing & Quality Assurance Standards

## Pytest Suite & Regression Verification
- All test suites must achieve 100% pass rate before committing changes.
- Tests must be deterministic with isolated state fixtures.

<important if="writing_tests">
- Never mock core mathematical calculation functions; test against exact golden outputs.
- Regression test scripts must execute with fail-closed return codes (Exit 0 on success, Exit 1+ on failure).
- Ensure async tests properly cleanup event loops and mock HTTP connections.
</important>
