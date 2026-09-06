---
name: qa-api-ui-e2e
description: Verify API and UI contracts across Docker backend and static UI targets.
---

# QA API and UI E2E Verification

Verify API and UI contracts across decoupled backend and frontend environments.

## Purpose

Enforce independent verification of the Hugging Face Docker backend and Vercel static UI,
guaranteeing strict API schemas and reliable UI interactions.

## Target Separation

- **HF Docker Backend Target**:
  - Validated via Docker healthcheck endpoint `/health`.
  - Enforces Pydantic v2 data models and structured error formats.
  - Requires explicit CORS header checks and security headers.
  - Confirms OpenAPI golden schema conformance.

- **Vercel Static UI Target**:
  - Verified independently via browser-level interaction tests.
  - Validates client-side routing, theme toggles, and form submissions.
  - Never infer target URLs from legacy HF Static hostnames.

## Verification Protocol

1. **Backend API Contract Verification**:
   - Send requests to endpoints under `project/routers/`.
   - Validate response status, JSON payload against Pydantic models, and CORS headers.
   - Assert structured error contracts on invalid inputs.

2. **UI End-to-End Interaction Testing**:
   - Execute browser automation or layout check scripts against verified URLs.
   - Test user interaction flows across viewport breakpoints.
   - Confirm fail-closed assertion handling for broken UI states.

3. **Status Reporting**:
   - `[OK]`: Backend schema and UI interactions verified.
   - `[ERROR]`: Contract drift, CORS mismatch, or UI failure detected.
   - `[WARNING]`: Deprecated endpoint parameter encountered.
   - `[INFO]`: Test environment target recorded.

## Gotchas

- Never test backend Docker and Vercel UI as a single unified target.
- Pure ASCII logs only: `[OK]`, `[ERROR]`, `[WARNING]`, `[INFO]`.
