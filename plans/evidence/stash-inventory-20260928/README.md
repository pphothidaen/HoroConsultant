# Stash Inventory & Backup Register — 2026-09-28

Ticket: KAN-130 · Review: `~/.hermes/reviews/KAN-130-cross-functional-review.md`
Base: `main` @ `f778c122` (in sync with `origin/main`)
Recoverability: git defaults apply — `gc.reflogExpire=90d`, `gc.reflogExpireUnreachable=30d`, `gc.pruneExpire=2w` (none overridden in this repo).

## Why this file exists

`git stash drop` deletes the stash reflog entry. The underlying commit objects survive
as unreachable objects until `gc.pruneExpire` (2 weeks) prunes them, after which recovery
requires `git fsck --unreachable` **and** the objects must not yet have been pruned.
This register pins every stash SHA so any dropped stash can be restored deterministically:

```bash
git stash apply <SHA>          # or
git branch recover/<n> <SHA>   # materialize to a branch
```

## Pre-cleanup state

Working tree: CLEAN. Branch `main` @ `f778c122`. Only `main` exists locally and remotely —
**every stash's parent branch was deleted**, so no stash can be recovered by checking out its
original branch.

## Stash register

| idx | SHA | date | parent branch (DELETED) | base | apply to main | % added lines already in main | classification |
|---|---|---|---|---|---|---|---|
| 0 | `805c2ec15e5f0c1a87fe1716186ec88b4084d517` | 2026-09-27 17:37 | feat/medium-tier-test-impact | 5c3c0c37 (diverged) | OK, 0 files changed | 100% | ALREADY INTEGRATED — drop |
| 1 | `acd23777a11b628c699b4b3f80c53e0a3f165fb3` | 2026-09-27 16:54 | fix/kan-95-twg-consent-fix-v2 | 11f69b23 (ancestor) | OK clean, +17 | 47% | SALVAGE — new provenance manifest |
| 2 | `9d350f7f9422c2a02af2a72c06d79a0a82c299c1` | 2026-09-27 16:31 | main (orchestrator-sessions) | 11f69b23 (ancestor) | OK clean, +75/−33 | 41% | MIXED — generated data + ATOMIC_TICKET |
| 3 | `346a1b4522fac7144fa34273478d4e46280614fe` | 2026-09-24 12:41 | feat/kan-118-runtime-guardrails | 314f8cda (ancestor) | OK, 0 files changed | 100% | ALREADY INTEGRATED — drop |
| 4 | `1950c20ec9213a4e04790f87a51bc2645e8feea3` | 2026-09-24 11:19 | feat/kan-105-label-governance | 4d8d766d (ancestor) | CONFLICT | 0% | SUPERSEDED — main already has JIRA_EMAIL |
| 5 | `e300a3d0cd499bb8d275e241bfe9806a24180acb` | 2026-09-24 07:45 | feat/kan101-model-routing-ledger | f4c12514 (diverged) | CONFLICT | 33% | SALVAGE — code+tests, ci.yml hunk POISONED |
| 6 | `ed0ccaf1d8fe571f10139c417345167480c938a0` | 2026-09-24 01:04 | feat/kan101-model-routing-ledger | f4c12514 (diverged) | CONFLICT ×4 | 55% | SALVAGE (partial) — docs/ATOMIC_TICKET/svg |
| 7 | `3fe54c1cb3bd8b03eb481e52bae28366f04b5283` | 2026-09-22 02:39 | main | 569e83bc (diverged) | CONFLICT | 38% | **SECURITY FIX** — HMAC webhook signing |
| 8 | `501b0c3d95089bf55ad8f17df223c537b462f5d7` | 2026-09-14 11:24 | release/horo-lite-review-remediation-20260908 | db386683 (diverged) | CONFLICT ×4 | 75% | GENERATED ARTIFACTS — drop |
| 9 | `4c878c8d26d30eb31cb700e3183fe49c8327c17c` | 2026-09-09 01:58 | ″ | 9bac7c62 (diverged) | CONFLICT ×5 | 80% | GENERATED ARTIFACTS — drop |
| 10 | `83978d8d26d8833380fe71d2530c5cc706fea5c3` | 2026-09-09 00:50 | ″ | ba6d0dfa (diverged) | CONFLICT ×2 | 88% | GENERATED ARTIFACTS — drop |
| 11 | `11cc33e687a24f7761f2172e0d7d9bb30571f2a1` | 2026-09-09 00:29 | ″ | ea1610bc (diverged) | CONFLICT ×4 | 80% | GENERATED ARTIFACTS — drop |
| 12 | `2e8744504b9744156ec9836f211c33b787f12092` | 2026-09-09 00:17 | ″ | ea1610bc (diverged) | CONFLICT ×2 | 95% | GENERATED ARTIFACTS — drop |
| 13 | `af6cad7b1376bba3754dbcd5938b26fabac08bf8` | 2026-09-09 00:13 | ″ | 1cb3c9f (diverged) | CONFLICT ×4 | 80% | GENERATED ARTIFACTS — drop |
| 14 | `08445870e9ae9cdacec0d331cc37a5edae45b2c0` | 2026-09-08 23:36 | ″ | 1cb3c9f (diverged) | CONFLICT ×2 | 95% | GENERATED ARTIFACTS — drop |
| 15 | `cf90e6573ee2e70528a88a1899d08571ca380945` | 2026-09-08 23:33 | ″ | 9c58b2f9 (diverged) | CONFLICT ×5 | 71% | GENERATED ARTIFACTS + RAG dataset — verify corpus before drop |
| 16 | `033ec824bbfff236903e46ba81c5595a9d3c9199` | 2026-09-08 22:56 | ″ | 9c58b2f9 (diverged) | CONFLICT ×4 | 80% | GENERATED ARTIFACTS — drop |
| 17 | `6d8b2becc084f47db9e1fab38a36a4f530c81dae` | 2026-09-08 22:35 | ″ | 6ac8136 (diverged) | CONFLICT ×2 | 95% | GENERATED ARTIFACTS — drop |

## Confirmed live bug (main @ f778c122)

`.github/workflows/jira-governance.yml:40` reads:

```
-H "Authorization: Bearer *** secrets.HERMES_AGENT_TOKEN }}"
```

Introduced in `74ddf4d2` ("chore: add Jira PR governance workflow") — the literal `***` and
stray `}}` mean the `notify-agent-on-failure` job has never sent a valid Authorization header,
so the autonomous CI-failure callback to Hermes has been non-functional since it was added.
stash@{7} (`3fe54c1c`) contains the HMAC-SHA256 replacement.

## Recovery commands

```bash
# materialize any dropped stash back to a branch
git branch recover/stash-7 3fe54c1cb3bd8b03eb481e52bae28366f04b5283

# or list anything gc has not yet pruned
git fsck --unreachable --no-reflogs 2>/dev/null | grep commit
```

---

## Disposition & Execution Record (KAN-130, Option B — APPROVED)

### Safety net established BEFORE any drop
- `refs/stash-backup/{0..17}` pin all 18 stash SHAs → objects stay **reachable**, so `git gc`
  cannot prune them. Recovery window is permanent, not the ~2-week `gc.pruneExpire` default.
- `credential/quarantine-stash6` — stash@{6} holds a live-format bearer token in `ATOMIC_TICKET.md`;
  confirmed absent from `main` and from every reachable commit. Never to be merged.
- `corpus/hitl-approved-stash15`, `corpus/bazi-chatml-stash9` — the only copies of HITL training
  data (1 + 15 records) that `main` holds as zero-byte placeholders.

### Integrated (1 of 18 value-bearing changes)
| Stash | Content | Disposition |
|---|---|---|
| stash@{7} | Hermes V2 HMAC webhook | **Integrated, adapted** (not diff-applied) |
| stash@{0}, stash@{3} | — | Dropped: already in `main` (zero-change apply) |
| stash@{1} | KAN-67 docs manifest | Dropped: KAN-67 tracked, ticket closed |
| stash@{2}, @{6}, @{8}–@{17} | Regenerated artifacts (71–95% already in `main`) | Dropped; corpus + credential quarantined |
| stash@{4} | `JIRA_EMAIL` fallback | Dropped: main already has the equivalent |
| stash@{5} | ci.yml tier hunk + ledger metric | Dropped: calls nonexistent `scripts/path_router.py`; ledger metric is a separate scoped ticket |

### The three corrections that changed the outcome
1. **My Phase 1 premise was false.** I reported `jira-governance.yml:40` as a corrupted production
   bug. It is not — the `***` is *tool-layer secret redaction*. Byte check: `len=74`, one `${{`,
   one `}}`, no literal `***`, identical to the canonical GitHub Actions bearer line. Red Team
   caught this; acting on it would have meant a pointless "fix".
2. **stash@{7} is correct but would have regressed main.** Its HMAC scheme matches the receiver
   contract (7/8 checks), but it emits `"pr_number": <expr>` with no push-event fallback, producing
   **invalid JSON on `push`**. Applied surgically, keeping main's `|| 'null'` / `|| github.ref_name` guards.
3. **actionlint found a real injection vector** the stash draft also had: `github.event.pull_request.*`
   interpolated into the `run:` block. PR branch names are attacker-controlled. Now routed through
   `env:` and assembled with `jq --arg`, with a regression test that fails if a heredoc reappears.

### Verification
- 9/9 new contract tests pass; genuine RED proven against original `main` (7 failed / 1 passed, then 1 failed for the jq test).
- `actionlint` clean; HMAC reproduces byte-identically (64-hex); malicious branch name stays inert JSON data.
- 3-commit gate-verified TDD sequence: `f27f7e52` → `42a50858` → `33445cc0`.
- Reflog recovery horizon: **unbounded** (reachable refs) rather than ~2 weeks.
