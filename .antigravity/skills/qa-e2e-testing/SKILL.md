---
name: qa-e2e-testing
description: Compatibility router for QA regression, API/UI contract, and release verification.
owner: qa_tester
sunset: Sunset upon full migration to focused QA skills in v2.0.0; no focused-profile activation.
---

# QA E2E Testing Compatibility Router

Workflow-free compatibility router delegating to focused quality engineering skills.

## Governance and Metadata

- **Owner**: `qa_tester`
- **Sunset Condition**: Retained strictly for backwards-compatible routing; scheduled for sunset in v2.0.0 after full migration to focused QA skills.
- **Activation Restriction**: No focused-profile activation permitted; this is a workflow-free router.

## Routing Targets

Inquiries and tasks mapped to this router are forwarded to the appropriate focused skill:

1. **`qa-regression-provenance`**:
   - Manages immutable RED baselines, pre-source test-only commits, and `test-provenance-v1` manifests.
   - Enforces that no source lane is released until the ticket is `TEST_BASELINE_VERIFIED`.
   - Regulates test-only superseding baseline procedures when test corrections are required.

2. **`qa-api-ui-e2e`**:
   - Handles decoupled verification of the HF Docker backend and Vercel static UI.
   - Validates Pydantic v2 schemas, CORS headers, and multi-viewport browser layouts.

## Reporting Protocol

- All status reports from routed tasks must use pure ASCII logs only:
  - `[OK]`: Sub-task routed and verified.
  - `[ERROR]`: Routing failure or target contract breach.
  - `[WARNING]`: Compatibility router invoked instead of direct focused skill.
  - `[INFO]`: Delegation target identified.
