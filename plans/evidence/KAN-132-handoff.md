# KAN-132 Handoff

**Status:** PR [#109](https://github.com/pphothidaen/HoroConsultant/pull/109) OPEN (branch `kAN-132-closeout` → `main`, 11 commits). Awaiting review/approval. Live-site actions below are **owner-only**.

This document is the authoritative handoff for anyone picking up the loose ends.

## ✅ Done (committed, PR'd, verified)

1. **Credential leak vector closed.** The dead `hermes-392e…` token was found inside two local git refs (`refs/heads/credential/quarantine-stash6`, `refs/stash-backup/6`). The quarantined tree was rebuilt **parentless** (so history can't reach the original) with the token replaced by a placeholder, and both refs repointed. Verified: the token is present in **no reachable commit** across **all 150 refs** (full-history scan, not tip-only). The dead token is **not** the live one — it already returns HTTP 401.
2. **New guard test** `tests/test_git_ref_credential_hygiene.py` — scans git ref tips for credential shapes, with a negative-control self-check (plants a synthetic token, asserts detection). Catches the class, not the specific incident.
3. **Subprocess CWD hardening** — `/tmp` removed from test subprocesses; per-invocation temp dirs; works on Python 3.10+ (where `-P` doesn't exist); `PYTHONSAFEPATH` set in child env for nested-interpreter safety.
4. **OWNER_TOKEN fix** — `tests/test_agent_token_scope.py` no longer infers the owner credential from `GH_TOKEN` (this repo's `.env` puts a scoped fine-grained PAT there → 403).
5. **Cross-functional review artifact** complete: `~/.hermes/reviews/KAN-132-cross-functional-review.md`, **APPROVED** (triggers: security + rework-loop; 4 specialists).

**Evidence:** `plans/evidence/stash-inventory-20260928/README.md` (updated).

## ⏸️ Open items — owner-optional, NOT incident-driven

> ✅ **Correction:** Independent full-object + ref-tip scan confirms the **live** token
> (`hermes-a7f…`, sha `d63378f1fa9d`) appears in **0 git objects** and **no ref**. It was never
> exposed in git. The tracked token (`hermes-392e…`) is dead (HTTP 401) and has been **fully
> redacted from all refs**. **No live-credential incident occurred** — rotation is hygiene, not
> response. (This corrects the original handoff's "rotate the live token" recommendation.)

### 2. 🗑️ Retire the quarantine refs
The redacted refs still exist. With rotation done, delete them and reclaim the dangling unredacted object:
```bash
git push origin --delete credential/quarantine-stash6   # remote, if ever pushed
git update-ref -d refs/heads/credential/quarantine-stash6 refs/stash-backup/6
git reflog expire --expire=unreachable=now --all && git gc --prune=now
git cat-file -e ed0ccaf1d8fe571f10139c417345167480c938a0^{commit} 2>/dev/null && echo "STILL PRESENT" || echo "reclaimed"
```

### 3. 🔐 Rotate the 5 OTHER live secrets in `~/.hermes/.env`
Per Red Team: a `ghp_…` PAT (repo scope), Grafana, Azure AD, Atlassian, and two Google API keys. All gitignored, none in git — but all still valid. Out of scope for #108; this is the next hygiene sweep.

### 4. 🏗️ Architectural follow-ups (documented, not built)
- **a)** Remove the `CLIENT_API_TOKEN` *bake* from the shipped browser extension (Red Team) — closes the exposure class so rotation can't recur via release zips. Requires a `gemini-web-bridge` release cycle.
- **b)** Replace the provenance guard's commit-ordering model with diff-coverage (`diff-cover`) + auto-generated `Test-Baseline:` trailers (Research, Worker). 23 of 186 manifests on `main` already have unreachable `baseline_parent` SHAs. See issue to file.

## 📋 Items filed
| # | Title | State |
|---|---|---|
| 108 | `rust_core/tests/test_installed_wheel.py` fails outside the CI wheel-build job | OPEN |
| 109 | This closeout PR | OPEN (merge-ready; verify-pr + pre-push ✅) |

## 🧪 Gate status
- `verify-pr --base 38f31b30 --head HEAD` → **PASSED**, 6 test files, 3 manifests.
- pre-push TDD gate → **APPROVED** for KAN-131 + KAN-132.
- Full suite (current tip): **5107 passed, 18 skipped, 0 failed**, 8m41s. (Local main is 11 ahead of origin/main; nothing pushed to origin/main.)
