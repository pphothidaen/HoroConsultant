# KAN-306: Phase 2 - AI-Assisted Code Review & Quality Gates

## Jira Ticket: KAN-306
**Status:** In Progress (TDD RED phase)
**Labels:** agent-hermes, ai-code-review, ai-sdlc, phase-2

---

## Scope
- AI-powered code review in CI pipeline
- Quality gates based on AI review results
- Automated fix suggestions for common issues
- Human override mechanism
- Test provenance compliance

---

## TODO Plan

### Phase 2A: AI Review Infrastructure
- [ ] **KAN-306-1**: Create AI code review script (`scripts/ai_code_review.py`)
  - Call gemini-web-bridge / aipass-web-bridge for reviews
  - Parse review results into structured format
  - Support review categories: security, style, correctness, complexity, best-practices
  
- [ ] **KAN-306-2**: Add unit tests for AI review agent (`tests/test_ai_code_review.py`)
  - Test review request/response parsing
  - Test quality gate evaluation
  - Test fix suggestion parsing

### Phase 2B: CI Integration
- [ ] **KAN-306-3**: Add `ai-code-review` job to CI pipeline
  - Runs after `ai-code-generation` and `ai-review-enforcement`
  - Fetches PR diff and sends to AI review
  - Posts review results as PR comment
  - Uploads review report as artifact

- [ ] **KAN-306-4**: Add quality gate script (`scripts/quality_gate.py`)
  - Evaluates review results against thresholds
  - Exit code 0 = pass, 1 = fail (blocks merge)
  - Configurable thresholds per category

### Phase 2C: Quality Gates & Automation
- [ ] **KAN-306-5**: Implement quality gate in CI
  - Add `quality-gate` job that runs `scripts/quality_gate.py`
  - Blocks merge if critical issues found and no human override
  - Human override via `ai-override` label on PR

- [ ] **KAN-306-6**: Automated fix suggestions
  - Parse AI review for actionable fixes
  - Generate `fix-suggestions.json` artifact
  - Auto-apply trivial fixes (formatting, imports) if enabled

### Phase 2D: Test Provenance & Validation
- [ ] **KAN-306-7**: Ensure test_provenance_guard.py passes
  - Create test provenance manifests for new tests
  - Verify no test weakening
  - Test-Baseline trailers on all commits

- [ ] **KAN-306-8**: Validate acceptance criteria
  - [ ] AI reviews PRs for security, style, correctness
  - [ ] Quality gates enforced in CI
  - [ ] Automated fix suggestions for common issues
  - [ ] Human override mechanism documented
  - [ ] Test provenance maintained

---

## Acceptance Criteria
1. ✅ AI reviews PRs for security, style, correctness
2. ✅ Quality gates enforced in CI
3. ✅ Automated fix suggestions for common issues
4. ✅ Human override mechanism documented
5. ✅ Test provenance maintained (test_provenance_guard.py passes)

---

## Dependencies
- Phase 1 complete (KAN-305) ✅
- gemini-web-bridge available at localhost:8765 ✅
- aipass-web-bridge available at localhost:8766 ✅
- Test provenance working ✅

---

## Risk Mitigation
| Risk | Mitigation |
|---|---|
| AI review latency | Timeout 60s, fallback to pass with warning |
| False positives | Human override via `ai-override` label |
| Bridge unavailable | Graceful degradation - skip review, log warning |
| Token limits | Chunk large diffs, summarize |

---

## Rollback Plan
- Disable `ai-code-review` job via feature flag
- Remove quality gate job
- Revert PR template changes if any