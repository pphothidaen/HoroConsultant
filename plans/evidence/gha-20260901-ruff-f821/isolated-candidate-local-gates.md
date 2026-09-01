# GHA-20260901-OPS-LOCAL-CANDIDATE-010 — Isolated Candidate Local Gates

**Observed:** `2026-09-01T10:30:43+0700`  
**Mode:** local candidate preparation only. No current-worktree edit, add,
commit, push, fetch, rebase, reset, clean, stash, restore, authentication,
workflow, deploy, or publish action was performed.

## Bound Candidate

- Detached worktree created at
  `/Users/kimlenglim/Project/HoroConsultant-ruff-f821-cb1df9f` after confirming
  that path was absent.
- Requested SHA: `cb1df9fd573f2936e9d57c4cb390f307cfeb17b7`.
- Observed detached `HEAD`: `cb1df9fd573f2936e9d57c4cb390f307cfeb17b7`.
- `git branch --show-current` returned empty, as required for a detached
  candidate.
- Immediately after creation and before any local gate, `git status --short
  --untracked-files=all` returned no output. This is the clean-candidate
  status result.

## Bound Local Gates

| Gate | Exact command | Result |
|---|---|---|
| Ruff F821 | `ruff check project/mcp_server.py --select F821` | `PASS` — `All checks passed!` |
| MCP contract | `python3 -m pytest -q tests/test_mcp_server_contract.py` | `PASS` — `13 passed in 0.47s` |
| Test provenance | `python3 scripts/test_provenance_guard.py verify --manifest plans/test_provenance/gha-20260901-ruff-f821-baseline.json --baseline 5bee032a0c3e53d0125d1e24f3990cef74030ff6 --head cb1df9fd573f2936e9d57c4cb390f307cfeb17b7 --include-worktree` | `PASS` — status `PASSED`, zero issues, one test file verified, ticket `TICKET-GHA-20260901-QA-010` |

The provenance report bound `baseline_commit` to
`5bee032a0c3e53d0125d1e24f3990cef74030ff6` and `head_commit` to the exact
candidate SHA above.

## Post-Gate Contamination Warning

The candidate was clean before gates, but a post-gate status check reported:

```text
 M project/static/charts/bazi_chart.svg
```

The observed diff is `34` additions and `34` deletions in that generated SVG.
It appeared after the contract-test run during this lane; this receipt does not
attribute a root cause beyond that observed sequence. No cleanup was performed,
because `reset`, `restore`, and `clean` are outside this ticket.

Therefore the local verification gates are `PASS`, but this *particular
post-test worktree must not be treated as a clean candidate for subsequent OPS
operations*. Preserve it for inspection. A future authorized operator needs a
fresh detached worktree (or an expressly authorized cleanup procedure) before
performing any integration activity.

## Decision

`DONE_WITH_LIMITATION` — the required initial clean state and all three local
gates passed at the exact reviewed SHA. The generated post-test SVG overlay
does not clear or alter any `GHA-20260901-OPS-040` remote, CI, authentication,
or explicit-push-authorization blocker. This is not a push, CI-success,
release, deployment, or production-readiness receipt.
