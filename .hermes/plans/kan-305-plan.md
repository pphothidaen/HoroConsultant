# KAN-305: Phase 1 - AI Code/Test Generation in CI

## Jira Ticket: KAN-305
**Status:** TDD GREEN (In Progress)
**Labels:** agent-hermes, ai-code-test-gen, ai-sdlc, phase-1

---

## Scope
- AI-assisted code generation in CI (Cursor/Copilot integration)
- AI test generation for new features
- Human review mandatory for all AI-generated code
- Test provenance guard must pass (no test weakening)

---

## TODO Plan

### Phase 1A: Infrastructure & CI Integration
- [ ] **KAN-305-1**: Add AI code generation step to CI pipeline
  - Integrate AI coding assistant (Cursor/Copilot) in CI
  - Configure authentication for AI service
  - Add step to generate code for new features marked with `ai-generate` label
  
- [ ] **KAN-305-2**: Add AI test generation step to CI pipeline
  - Generate unit tests for new functions/classes
  - Configure test patterns and conventions
  - Integrate with existing pytest suite

### Phase 1B: Human Review Enforcement
- [ ] **KAN-305-3**: Create PR template with human review checkbox
  - Mandatory checkbox: "I have reviewed all AI-generated code"
  - Auto-detect AI-generated changes (via commit message pattern or labels)
  - Block merge if checkbox not checked (via branch protection)

- [ ] **KAN-305-4**: Implement AI-generated code detection
  - Detect commits with `AI-Generated:` prefix or `ai-generated` label
  - Add `ai-review-required` label to PRs with AI content
  - Notify reviewers automatically

### Phase 1C: Test Provenance Integration
- [ ] **KAN-305-5**: Ensure test_provenance_guard.py passes for AI-generated tests
  - Verify AI-generated tests have Test-Baseline trailers
  - Prevent test weakening (assertion removal, coverage reduction)
  - Integrate with existing test provenance workflow

### Phase 1D: Measurement & Validation
- [ ] **KAN-305-6**: Add cycle time measurement
  - Baseline: current PR cycle time (without AI)
  - Measure: PR cycle time with AI generation
  - Report: cycle time reduction vs baseline

- [ ] **KAN-305-7**: Validate acceptance criteria
  - [ ] AI generates code/tests for new features
  - [ ] Human review enforced via PR template
  - [ ] test_provenance_guard.py passes
  - [ ] No test weakening detected
  - [ ] Cycle time reduction measured vs baseline

---

## Acceptance Criteria
1. ✅ AI generates code/tests for new features
2. ✅ Human review enforced via PR template
3. ✅ test_provenance_guard.py passes
4. ✅ No test weakening detected
5. ✅ Cycle time reduction measured vs baseline

---

## Dependencies
- Phase 0 complete (all 6 required CI checks passing) ✅
- test_provenance_guard.py working ✅
- Branch protection ruleset with 6 required checks ✅

---

## Risk Mitigation
| Risk | Mitigation |
|---|---|
| AI generates incorrect code | Human review mandatory; tests must pass |
| Test weakening | test_provenance_guard.py blocks weakening |
| AI hallucinations in tests | Generated tests must pass against real implementation |
| Auth/quota issues | Fallback to manual generation if AI unavailable |

---

## Rollback Plan
- Disable AI generation steps in CI via feature flag
- Revert PR template changes
- Remove AI detection logic