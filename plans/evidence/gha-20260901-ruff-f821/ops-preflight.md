# GHA-20260901-OPS-040 — Operations Push Preflight Receipt

**Observed at:** `2026-09-01T10:17:07+0700`  
**Mode:** read-only preflight; no fetch, add, commit, push, workflow edit, deploy, or publish performed.

## Decision

`BLOCKED` — do **not** request or perform an OPS push yet.  The reviewed repair
is locally identifiable, but the candidate is surrounded by an unrelated dirty
worktree, it is not present on `origin/main`, no exact-SHA GitHub Actions run
exists, and the configured GitHub CLI credential is invalid.  An operator must
first isolate the candidate in a clean, provenance-valid worktree and provide
fresh GitHub authentication plus explicit push authorization.  HITL review does
not itself authorize a push.

## Bound Candidate and Review Receipt

- Current branch: `main`.
- Current `HEAD`: `cb1df9fd573f2936e9d57c4cb390f307cfeb17b7` —
  `fix(mcp): preserve lazy HybridRouter type reference`.
- The reviewed SHA is exactly the current `HEAD`; both
  `cb1df9f...` is an ancestor of `HEAD` and `HEAD` is an ancestor of
  `cb1df9f...`.
- `plans/evidence/gha-20260901-ruff-f821/review.md` exists and records a
  commit-specific `PASS` for this candidate against frozen baseline
  `5bee032a0c3e53d0125d1e24f3990cef74030ff6`.
- Candidate commit scope from `git diff-tree`: only `M project/mcp_server.py`.

## Remote and CI Identity

- Configured target: `origin` = `git@github.com:pphothidaen/HoroConsultant.git`;
  local `main` tracks `origin/refs/heads/main`.
- Read-only `git ls-remote --heads origin refs/heads/main` returned remote
  `main` = `f9f80487a5f01a176ce7c16d3f1657e2c8908e16`.
- `f9f8048...` is an ancestor of the candidate; the candidate is two local
  commits ahead (`git rev-list --left-right --count f9f8048...cb1df9f...` =
  `0 2`). It is therefore not remote-main identity.
- `gh run list --commit cb1df9f...` returned `[]`: no exact-candidate remote
  Actions run exists. Main CI cannot be claimed green.
- The recorded baseline run `33418206471` is for `f9f8048...`, workflow
  `Lint & Security Check`, and concluded `failure`; it is stale and cannot be
  reused as candidate evidence.

## Dirty-Worktree Classification

`git status --porcelain=v1 --untracked-files=all` reported 40 entries:

- 32 tracked modifications (` M`), including governance/configuration, scripts,
  tests, handoff and planning artifacts.
- 8 untracked paths (`??`), including `atomic_tasks.md`, the atomic-task archive,
  and evidence directories.
- No candidate-specific clean isolation or provenance-valid commit boundary was
  established by this preflight. No dirty file was changed or restored.

## Authorization Assessment and Typed Blockers

- **`DIRTY_WORKTREE`**: exact-candidate push is unsafe while 40 unrelated
  modifications/untracked paths coexist on `main`.
- **`REMOTE_CANDIDATE_ABSENT`**: `origin/main` is `f9f8048...`, not
  `cb1df9f...`.
- **`EXACT_SHA_CI_MISSING`**: there is no GitHub Actions run bound to
  `cb1df9f...`; the only inspected baseline run failed.
- **`GITHUB_AUTH_INVALID`**: read-only `gh auth status` reports the default
  `pphothidaen` GitHub token invalid. Git transport push authority was not
  probed because push and dry-run push are outside this preflight.
- **`EXPLICIT_PUSH_AUTH_REQUIRED`**: no explicit authorization to alter
  `origin/main` was supplied to this ticket; HITL does not substitute for it.

## Required Next Gate

After a clean candidate worktree and an authorized, freshly authenticated push
request are available, push only the reviewed candidate, then bind an Actions
run with `headSha == cb1df9fd573f2936e9d57c4cb390f307cfeb17b7` and a green
conclusion before creating `main-ci.json`. This preflight is not a CI-success,
release, deployment, or production-readiness receipt.
