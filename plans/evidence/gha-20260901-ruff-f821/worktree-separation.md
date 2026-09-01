# GHA-20260901-OPS-WORKTREE-RECOVERY — Dirty-Worktree Separation Plan

**Observed:** `2026-09-01T10:28:14+0700`  
**Mode:** read-only provenance inventory. No add, commit, stash, reset, restore,
clean, checkout, fetch, rebase, push, remote/auth mutation, or candidate
worktree creation was performed.

## Decision

`BLOCKED` — the current primary worktree is not an authorized RUFF OPS
candidate. Preserve every current overlay in place. A future, explicitly
authorized OPS operator can create a *new detached* worktree at the exact
reviewed commit, then continue only after all prior remote, CI, authentication,
and push-authorization gates are independently rechecked.

This receipt does not declare any worktree clean, does not approve a push, and
does not change the earlier `GHA-20260901-OPS-040` decision.

## Bound Candidate and Current Topology

- Candidate SHA: `cb1df9fd573f2936e9d57c4cb390f307cfeb17b7` (`cb1df9f`), current
  primary `HEAD`; parent: `5bee032a0c3e53d0125d1e24f3990cef74030ff6`.
- Candidate scope is exactly `M project/mcp_server.py` (7 lines: 5 additions,
  2 deletions). No current overlay targets that path.
- `origin/main` is `f9f80487a5f01a176ce7c16d3f1657e2c8908e16`; it is two commits
  behind the candidate (`0 2` for `origin/main...cb1df9f`).
- The primary worktree is `/Users/kimlenglim/Project/HoroConsultant` on `main`.
  Its snapshot contains 46 tracked modifications and 13 untracked files (59
  total).
- An already-registered `/Users/kimlenglim/Project/HoroConsultant/.worktrees/main`
  also resolves to `cb1df9f`, but it has its own tracked modifications and
  deletions. It is **not** a clean isolation target.

### Classification rule

`candidate` means a path changed by the bound commit. `ancestor` would mean a
path changed only before the candidate and not present as a current overlay.
`unrelated overlay` means a current tracked modification or untracked path that
is absent from the bound candidate's one-path diff. Git status cannot establish
the human author or business provenance of an overlay; this is a path-scope
classification only.

Result: the current inventory has **0 candidate overlays**, **0 ancestor-only
overlays**, and **59 unrelated overlays**. The `ancestor` category is empty
because this inventory records only present working-tree changes, all observed
relative to `HEAD == cb1df9f`.

## Exact Primary-Worktree Inventory

All entries below classify as `unrelated overlay` to `cb1df9f`.

### Tracked modifications (46)

```text
M  .agents/AGENTS.md
M  .agents/LESSONS_LEARNED.md
M  .agents/config/context_handoff_v1.json
M  .agents/rules/08-grill-gate-enforcement.md
M  .agents/rules/12-claude-code-three-level-governance.md
M  .agents/rules/17-multi-account-agent-orchestration.md
M  .agents/rules/20-context-handoff.md
M  .agents/skills/anti-cognitive-decay/SKILL.md
M  .agents/skills/bsa-doc-skill-management/SKILL.md
M  .agents/skills/orchestrator-delegation/SKILL.md
M  .agents/skills/requirement-grill-gate/SKILL.md
M  .agents/skills/sdlc-aisdlc-workflow/SKILL.md
M  .agents/workflows/aisdlc.md
M  .agy/rules/context-handoff.md
M  .agy/skills/anti-cognitive-decay/SKILL.md
M  .antigravity/skills/anti-cognitive-decay/SKILL.md
M  .antigravity/skills/bsa-doc-skill-management/SKILL.md
M  .antigravity/skills/orchestrator-delegation/SKILL.md
M  .antigravity/skills/requirement-grill-gate/SKILL.md
M  .antigravity/skills/sdlc-aisdlc-workflow/SKILL.md
M  .claude/rules/context-handoff.md
M  .claude/skills/anti-cognitive-decay/SKILL.md
M  HANDOFF.md
M  PROJECT_TASKS.md
M  docs/CLAUDE_CODE_COMMAND_GOVERNANCE.md
M  docs/RELEASE_NOTES.md
M  docs/architecture/multiagent-control-plane/tickets/c0.md
M  docs/superpowers/plans/2026-08-09-codex-agent-compatibility.md
M  docs/superpowers/plans/2026-08-10-rust-first-azure-v1.md
M  docs/superpowers/specs/2026-08-09-codex-agent-compatibility-design.md
M  docs/superpowers/specs/2026-08-10-rust-first-azure-v1-design.md
M  docs/templates/MULTIAGENT_PROMPT_COMMAND.md
M  plans/plan.md
M  project_tickets.md
M  scripts/agent_quota_status_guard.py
M  scripts/agentic_pipeline.sh
M  scripts/auto_deploy_all.sh
M  scripts/context_handoff.py
M  scripts/hermes_sdlc_runner.sh
M  scripts/test_provenance_guard.py
M  scripts/update_docs.py
M  tests/fixtures/context_handoff/codex/native_mappings.json
M  tests/fixtures/context_handoff/context_handoff.py
M  tests/fixtures/context_handoff/context_handoff_v1.json
M  tests/test_context_handoff.py
M  tests/test_context_handoff_hooks.py
```

### Untracked paths (13)

```text
?? atomic_tasks.md
?? plans/archive/2026-09-01-atomic-tasks-refactor/PROJECT_TASKS_original.md
?? plans/archive/2026-09-01-atomic-tasks-refactor/project_tickets_original.md
?? plans/evidence/gha-20260901-aisafety/agy-capacity-triage.json
?? plans/evidence/gha-20260901-aisafety/context-handoff-triage.json
?? plans/evidence/gha-20260901-aisafety/distillation-timestamp-triage.json
?? plans/evidence/gha-20260901-aisafety/hf-gradient-digest-triage.json
?? plans/evidence/gha-20260901-aisafety/local-release-runner-triage.json
?? plans/evidence/gha-20260901-aisafety/quota-handoff-triage.json
?? plans/evidence/gha-20260901-aisafety/rag-chunk-triage.json
?? plans/evidence/gha-20260901-aisafety/triage-readiness-review.md
?? plans/evidence/gha-20260901-ruff-f821/ops-preflight.md
?? plans/evidence/gha-20260901-ruff-f821/review.md
```

## Authorized Future Isolation Procedure

The following is a proposal only; do not execute it without explicit operator
authorization. The proposed sibling path was absent at observation time and is
not the dirty `.worktrees/main` path.

```bash
git worktree add --detach /Users/kimlenglim/Project/HoroConsultant-ruff-f821-cb1df9f cb1df9fd573f2936e9d57c4cb390f307cfeb17b7
git -C /Users/kimlenglim/Project/HoroConsultant-ruff-f821-cb1df9f rev-parse HEAD
git -C /Users/kimlenglim/Project/HoroConsultant-ruff-f821-cb1df9f status --porcelain=v1 --untracked-files=all
git -C /Users/kimlenglim/Project/HoroConsultant-ruff-f821-cb1df9f diff --quiet
git -C /Users/kimlenglim/Project/HoroConsultant-ruff-f821-cb1df9f diff --cached --quiet
```

Acceptance for isolation is: the first command reports exactly `cb1df9f`; the
status command has no output; both diff checks exit zero. The operator must
retain the primary worktree untouched throughout. Do not use `stash`, `reset`,
`restore`, `clean`, or checkout in the primary worktree to make this happen.

Isolation is deliberately separate from integration. Before any push request,
re-run and satisfy every `OPS-040` blocker: candidate identity must be reviewed
against the intended remote base, current GitHub authentication must be valid,
an exact candidate-SHA Actions run must conclude green, and explicit push
authorization must be present. The former preflight found all of these missing.

## Reconciliation with `GHA-20260901-OPS-040`

This receipt confirms the material parts of the previous preflight: `cb1df9f`
remains the local candidate, `origin/main` remains behind it, and the primary
worktree remains dirty. It refines the isolation evidence with an exact
59-path snapshot and identifies the existing `.worktrees/main` as unusable due
to independent dirt. No remote or GitHub-auth claim was revalidated here, so
the prior `REMOTE_CANDIDATE_ABSENT`, `EXACT_SHA_CI_MISSING`,
`GITHUB_AUTH_INVALID`, and `EXPLICIT_PUSH_AUTH_REQUIRED` gates remain open,
not re-proven or cleared.
