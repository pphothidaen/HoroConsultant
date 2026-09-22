# Sprint F — Jira Scope Grill Intake (KAN-73/74/75/76)

**Parent Epic:** [KAN-73] Gemini Bridge Integration — MCP toggle, circuit breaker, CI/CD
**Owner (pinged):** Pansakorn (林金龍) Phothidaen
**Spec:** `docs/gemini-bridge-mcp-toggle.md`
**Production URL:** `https://gemini-web-bridge.pansakorn-pho.workers.dev`
**Status:** Grill comment posted on KAN-73 → awaiting owner response within 30 min → if no reply, KAN-73 flagged **Blocked**.

---

## Ticket Scope Summary

| Ticket | Summary | Assignee | Priority | Status |
|--------|---------|----------|----------|--------|
| **KAN-73** | Gemini Bridge Integration — MCP toggle, circuit breaker, CI/CD | — | Medium | Done |
| **KAN-74** | test: Gemini Bridge toggle E2E tests (TDD RED→GREEN) | Pansakorn | High | Done |
| **KAN-75** | test: Circuit breaker + failover chain verification | Pansakorn | High | Done |
| **KAN-76** | ci: Bridge CI/CD integration + provenance manifest | — | Medium | Done |

**Scope (from KAN-73):** Gemini Bridge MCP toggle E2E tests (disabled / no-config / circuit-breaker scenarios), circuit breaker + failover chain verification, bridge CI/CD integration + provenance manifest.

---

## 9-Dimension Scope Grill — Questions to Owner

### 1. Requirements

- **Q:** KAN-74 covers toggle-disabled and no-config scenarios. Which specific behaviors must be byte-identical to the legacy HybridRouter chain when the bridge is disabled? (e.g., empty birth_context, malformed JSON, non-Thai queries)
- **Q:** KAN-75 specifies circuit breaker failover: Gemini Bridge → Cloudflare AI → local model. Is this the exact failover priority, or should Ollama qwen2.5:7b remain first as in the legacy chain (section 6.2 of spec)?
- **Q:** Are there any acceptance criteria beyond the per-ticket checklists? E.g., minimum pass rate for E2E tests, coverage thresholds?

### 2. Constraints

- **Q:** KAN-74 RED phase requires 3 test files committed and failing. Must tests be committed to a specific branch (e.g., `feat/render-primary-backend`) or to main?
- **Q:** Are there constraints on test execution time? The spec sets `GEMINI_WEB_BRIDGE_TIMEOUT_S=90`. Do CI integration tests need to complete within a hard deadline (e.g., 180s)?
- **Q:** Can tests run against the production URL (`https://gemini-web-bridge.pansakorn-pho.workers.dev`) directly, or must they use a staging environment?

### 3. Dependencies

- **Q:** Does KAN-76's provenance manifest depend on the bridge being deployed to a specific version/branch of the `gemini-web-bridge` Worker? If so, which version?
- **Q:** KAN-74 spec references `project/core/gemini_bridge_client.py`. Are there any pending changes to that file or the spec doc (`docs/gemini-bridge-mcp-toggle.md`) that tests must account for?
- **Q:** Does the CI/CD workflow (KAN-76) depend on downstream systems (Render.com, GitHub Actions runners, Doppler sync) having specific permissions or secrets available?

### 4. Acceptance Criteria

- **Q:** For KAN-74 GREEN phase: "All tests pass after implementation." Should these tests pass against production, staging, or both? What's the exact verification command?
- **Q:** For KAN-75: Circuit breaker state machine (closed → open → half-open → closed) — must this be tested via unit tests, integration tests, or both?
- **Q:** For KAN-76: "Provenance manifest generated and attached to releases" — what format? (e.g., SPDX SBOM, in-toto attestation, CycloneDX) And must it be a GitHub release asset, a Render artifact, or a comment on the PR?

### 5. Edge Cases

- **Q:** Beyond the documented fail-fast HTTP statuses (503/422/429/401/timeout), what edge cases must tests cover? (e.g., HTTP 400 with invalid JSON body, HTTP 500 from Worker, network partition causing `ConnectionError`, SSL/TLS errors)
- **Q:** For PDF mode: what happens if the `pdf_url` artifact expires (TTL 3600s) before the client downloads it? Must this be tested?
- **Q:** What happens when the NotebookLM notebook scope is valid but the notebook is empty or has no relevant knowledge? Is that a bridge-level error or a valid empty response?

### 6. Integrations

- **Q:** KAN-76 mentions GitHub Actions workflow. Which existing workflow YAML should be extended, or should a new one be created? (e.g., `.github/workflows/integration.yml`)
- **Q:** Does the provenance manifest need to integrate with any existing observability stack (e.g., Sentry, DataDog, custom logging)?
- **Q:** The failover chain includes Ollama, Gemini API, and Cloudflare AI. Are these upstreams already configured in CI/CD, or do tests need to mock them?

### 7. Security

- **Q:** The spec states Bearer token must never be committed. Do test fixtures use mock tokens or a dedicated test token provisioned in Doppler? How is token rotation handled in test environments?
- **Q:** PDF artifact download uses unguessable-key URLs with no Bearer. Are there any rate-limiting or IP-restriction controls on the `/artifacts/{key}` endpoint that tests must account for?
- **Q:** Does the provenance manifest need to include vulnerability scanning results (e.g., `pip-audit`, `bandit`) as part of CI?

### 8. Rollback Plan

- **Q:** The runtime toggle (`GEMINI_WEB_BRIDGE_ENABLED`) can be flipped to `false` via Doppler + `scripts/sync-render-secrets.sh`. Is there a documented runbook for operators to execute this rollback?
- **Q:** If KAN-76's CI/CD integration introduces a regression, is there a specific commit/rollback protocol (e.g., revert PR, rollback Render deploy, revert Doppler secret)?
- **Q:** For the circuit breaker specifically: if all failover paths fail, what's the final user-facing behavior? Must tests verify this terminal fallback path?

### 9. Success Metrics

- **Q:** Beyond test pass/fail, what are the measurable success criteria for this sprint? (e.g., bridge response latency < X seconds, error rate < Y%, query volume routed to bridge > Z%)
- **Q:** How will success be measured in production after toggle is enabled? Are there dashboards or SLOs defined?
- **Q:** Is there a target date for production toggle enablement, and does the 30-min response window here align with the sprint timeline?

---

## Owner Response Log

| Timestamp (UTC+7) | Dimension | Response | Action Taken |
|-------------------|-----------|----------|--------------|
| (pending) | (all) | (awaiting response) | Comment posted on KAN-73; 30-min timer started |

> **Timer:** If no owner response on KAN-73 within 30 minutes of comment posting, KAN-73 will be flagged as **Blocked** (status transition + blocker flag) and the parent Epic (KAN-38) will be notified.
