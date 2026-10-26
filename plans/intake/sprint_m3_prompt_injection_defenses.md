# Sprint: M3 Prompt Injection Defenses — 9-Dimension Grill Intake Report

**Sprint ID**: `SPRINT-M3-PROMPT-INJECTION-DEFENSES`  
**Date**: 2026-10-26  
**Authorized By**: Issue #242 "M3 Prompt Injection Defenses"  
**Status**: APPROVED — Ready for Sprint Registration

---

## 1. Problem Statement

Red Team assessment found **11 prompt injection sites** across the codebase where raw/untrusted data is interpolated into LLM prompts without sanitization:

| Site | File | Line | Risk |
|------|------|------|------|
| 1 | `scripts/sync_claude_agy_parity.py` | 87 | Raw AI output concatenated into prompts |
| 2 | `scripts/render_agent_context_profiles.py` | 234 | User-supplied paths interpolated |
| 3 | `scripts/cost_ledger.py` | 156 | PR titles/descriptions injected into LLM prompts |
| 4 | `scripts/governance_sync.py` | 251 | Markdown content interpolated without sanitization |
| 5 | `scripts/sync_codex_agents.py` | 112 | Agent definitions from external sources |
| 5 | `scripts/sync_sdlc_agents.py` | 98 | YAML frontmatter parsed without validation |
| 7 | `scripts/hermes_agy_router.py` | 67 | Model responses used in routing logic |
| 8 | `scripts/stamp_version.py` | 45 | Git commit messages interpolated |
| 9 | `scripts/tdd_gate.py` | 134 | Test output fed back into analysis |
| 10 | `scripts/cloudflare_worker_monitor.py` | 89 | Worker logs sent to LLM |
| 11 | `scripts/sync_ai_agent_ecosystem.py` | 278 | Agent configs from multiple sources |

**Impact**: Potential prompt injection, data exfiltration, privilege escalation via LLM manipulation.

---

## 2. Goal

Build a **centralized prompt sanitization layer** and harden all 11 injection sites:

1. **Create** `scripts/prompt_sanitizer.py` with:
   - `sanitize_for_prompt(text: str) -> str` — strip/escape injection patterns
   - `canary_token() -> str` — generate unique token per call for exfiltration detection
   - `verify_canary(response: str, token: str) -> bool` — detect token leakage
   - Injection patterns: `ignore previous`, `system:`, `assistant:`, `###`, `[[[`, `>>>`, `<<<`, role-play markers

2. **Update all 11 sites** to use `sanitize_for_prompt()` before interpolation

3. **Add contract test** `tests/test_prompt_injection_contract.py` asserting:
   - `sanitize_for_prompt` exists and rejects known injection patterns
   - Canary tokens are unique and verifiable
   - No site bypasses sanitization (grep check)

4. **TDD Workflow**: RED commit (test + manifest) → GREEN commit (sanitizer + 11 site fixes)

---

## 3. Core Execution Invariants [FROZEN]

- **INVARIANT-M3-01**: Centralized Sanitization — All prompt interpolation MUST go through `scripts/prompt_sanitizer.py::sanitize_for_prompt()`
- **INVARIANT-M3-02**: Canary Token Protocol — Every LLM call that processes external data MUST include a unique canary token and verify it in the response
- **INVARIANT-M3-03**: Injection Pattern Coverage — Must reject: `ignore previous`, `system:`, `assistant:`, `###`, `[[[`, `>>>`, `<<<`, role-play markers, `<|`, `|>`, `<<SYS>>`, `<</SYS>>`
- **INVARIANT-M3-04**: TDD Enforcement — RED commit (failing test + provenance manifest) MUST precede GREEN commit (implementation)
- **INVARIANT-M3-05**: Pure ASCII Logging — All execution traces use `[OK]`, `[INFO]`, `[WARNING]`, `[ERROR]` only
- **INVARIANT-M3-06**: Single-Editor Resource Boundaries:
  - `lead_ba`: `ATOMIC_TICKET.md`, `plans/plan.md`, `plans/intake/**`
  - `developer`: `scripts/prompt_sanitizer.py`, 11 injection site files
  - `qa_tester`: `tests/test_prompt_injection_contract.py`, `plans/test_provenance/**`
  - `code_reviewer`: `plans/evidence/**`, `ReleaseNotes.md`
  - `devops`: git tree, release tags, deployment receipts

---

## 4. Stop Conditions

- Any injection pattern bypasses sanitization (grep verification fails)
- Canary token not unique or not verifiable
- Contract test fails
- Non-ASCII log emission
- Secret leak detected
- `scripts/tdd_gate.py` or `scripts/test_provenance_guard.py verify-pr` fails

---

## 5. Acceptance Criteria (Definition of Done)

1. `scripts/prompt_sanitizer.py` created with all 3 functions + pattern coverage
2. All 11 injection sites updated to call `sanitize_for_prompt()` + canary protocol
3. `tests/test_prompt_injection_contract.py` passes 100% with provenance manifest registered
4. `grep -r "sanitize_for_prompt" scripts/` shows 11+ calls (one per site minimum)
5. `python3 scripts/sync_ai_agent_ecosystem.py --check` exits 0
6. Rayon secret scan 0 leaks, AST audit 0 issues
7. PR created, CI green, squash-merged to main
8. Live production verification (if applicable)

---

## 6. Dependencies

- **Blocker**: None — independent security hardening sprint
- **Reference**: Provenance manifest schema from `plans/test_provenance/ticket-kan-293-m4-jira-verify-command-injection-001.json`
- **Guard**: Pre-push runs `scripts/tdd_gate.py` and `scripts/test_provenance_guard.py`

---

## 7. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Over-sanitization breaking legitimate prompts | Medium | High | Unit tests for each pattern; preserve legitimate markdown/code |
| Canary token collision | Low | Medium | Use crypto-random 32-byte tokens |
| Missed injection site | Low | Critical | Grep verification in contract test; code review |
| Performance regression | Low | Low | Sanitization < 1ms per call; benchmark in tests |

---

## 8. Success Metrics

- 11/11 injection sites hardened
- 100% contract test pass
- 0 secret leaks, 0 AST issues
- Zero prompt injection vulnerabilities in Red Team re-assessment
- PR merged with CI green

---

## 9. Owner Sign-off

**Status**: ✅ APPROVED — Ready for `lead_ba` sprint registration and ticket decomposition.

> "Security hardening is non-negotiable. M3 defenses must be in place before any new feature work." — Owner directive
