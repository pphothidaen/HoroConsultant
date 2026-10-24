# KAN-307: Phase 3 - AI-Powered Refactoring & Tech Debt Reduction

## Jira Ticket: KAN-307 (NEW)
**Status:** Ready for Implementation
**Labels:** agent-hermes, ai-refactoring, ai-sdlc, phase-3
**Epic:** KAN-289 "AI-SDLC Transformation"

---

## Rationale
Phase 1: Generate code/tests → Phase 2: Review code quality → **Phase 3: Auto-improve code**
- Leverage existing AI review infrastructure (KAN-306)
- Apply fix suggestions automatically where safe
- Reduce tech debt continuously in CI

---

## Scope
- **3A: Refactoring Agent** - Analyzes review results + codebase, proposes refactors
- **3B: Auto-Fix Engine** - Safely applies trivial fixes (formatting, imports, simple patterns)
- **3C: Tech Debt Tracker** - Tracks debt metrics over time, prioritizes high-impact refactors
- **3D: CI Integration** - Runs after quality-gate, creates refactor PRs for review

---

## TODO Plan

### Phase 3A: Refactoring Agent Infrastructure
- [ ] **KAN-307-1**: Create `scripts/ai_refactor.py` - refactoring suggestion engine
  - Consumes AI review results + quality gate violations
  - Uses gemini-web-bridge / aipass-web-bridge for refactoring suggestions
  - Supports categories: dead-code, complexity, duplication, modernization, performance
  - Outputs structured refactoring plan

- [ ] **KAN-307-2**: Add unit tests (`tests/test_ai_refactor.py`)
  - Test refactoring suggestion parsing
  - Test safety classification (auto-fix vs needs-review)
  - Test diff generation

### Phase 3B: Auto-Fix Engine
- [ ] **KAN-307-3**: Create `scripts/auto_fix.py` - Safe automatic fixes
  - Formatting (black, isort, prettier)
  - Import sorting/cleanup
  - Simple pattern fixes (unused vars, dead code, type hints)
  - Dry-run mode for CI verification

- [ ] **KAN-307-4**: Add unit tests (`tests/test_auto_fix.py`)
  - Test each fix type
  - Test dry-run vs apply modes
  - Test safety boundaries

### Phase 3C: Tech Debt Tracker
- [ ] **KAN-307-5**: Create `scripts/tech_debt_tracker.py`
  - Computes debt metrics: complexity, duplication, coverage gaps, outdated patterns
  - Stores history in `.hermes/tech_debt_history.json`
  - Generates trend reports
  - Identifies "hotspots" (files with high debt + high churn)

- [ ] **KAN-307-6**: Add unit tests (`tests/test_tech_debt_tracker.py`)

### Phase 3D: CI Integration
- [ ] **KAN-307-7**: Add `ai-refactor` job to CI (runs after quality-gate)
  - Runs refactoring agent on PR
  - Runs auto-fix in dry-run mode
  - If auto-fixes found → creates `fix/auto-<branch>` branch + PR
  - If refactor suggestions → posts summary as PR comment

- [ ] **KAN-307-8**: Add `tech-debt-report` job (scheduled weekly)
  - Runs full codebase analysis
  - Updates debt history
  - Posts summary to tracking issue

### Phase 3E: Test Provenance & Validation
- [ ] **KAN-307-9**: Ensure test_provenance_guard.py passes
  - Create provenance manifests for all new tests
  - Verify no test weakening

- [ ] **KAN-307-10**: Validate acceptance criteria
  - [ ] Refactoring suggestions generated from reviews
  - [ ] Auto-fixes applied safely in CI
  - [ ] Tech debt metrics tracked over time
  - [ ] Refactor PRs created for human review
  - [ ] Test provenance maintained

---

## Acceptance Criteria
1. ✅ Refactoring suggestions generated from AI reviews
2. ✅ Auto-fixes applied safely in CI (dry-run verified)
3. ✅ Tech debt metrics tracked over time
4. ✅ Refactor PRs created for human review
4. ✅ Test provenance maintained

---

## Dependencies
- Phase 2 complete (KAN-306) ✅
- AI review infrastructure working ✅
- Quality gates enforced ✅

---

## Risk Mitigation
| Risk | Mitigation |
|---|---|
| Auto-fix breaks code | Dry-run mandatory, only trivial fixes auto-applied, tests must pass |
| Refactor PR spam | Limit to 1 refactor PR per source PR per week |
| False positive suggestions | Human review required for non-trivial refactors |
| Performance on large codebase | Incremental analysis, file-level caching |

---

## Rollback Plan
- Disable `ai-refactor` and `tech-debt-report` jobs
- Remove auto-fix from CI
- Keep scripts for manual use