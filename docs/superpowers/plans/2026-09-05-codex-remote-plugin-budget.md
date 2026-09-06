# Remote-Curated Skill Context Budget Remediation — Executed Plan

**Ticket:** `TICKET-SKILL-BUDGET-001`
**Lifecycle:** `READY_FOR_OWNER_REVIEW` — locally implemented and independently verified; this is not a release-DONE claim. Commit, push, release, deploy, and publish remain excluded, and the shared worktree is intentionally dirty.

**Objective:** Keep each configured Codex account prompt at or below 8,000 characters without truncation or shortening warnings, while retaining required HoroConsultant skills, `superpowers`, and bundled browser/UI capabilities.

## Implemented contract

- [x] Remote-curated plugins are discovered from local cache/config surfaces and default-disabled except `superpowers`; no plugin cache or skill source directory is deleted.
- [x] Reusable role profiles derive only from canonical `.agents/agents/*/agent.json` `tools` values and matching `.agents/skills/<tool>/SKILL.md` sources. A `codex -p <role>` profile is new-session-only and never enables an optional remote-curated plugin.
- [x] Browser, chrome, computer-use, unified-computer-use, `superpowers`, and canonical role-bound Horo skills remain preserved.
- [x] Prompt validation fails closed for command/JSON/skills-block/measurement failure, missing expected account, prompt overage, truncation, and the exact shortened-description warning; an unavailable measurement cannot produce a false green.
- [x] Canonical `prediction_validator.tools` uses unsuffixed `bazi-calculator` and `rag-search`.
- [x] Python `sync_sdlc_agents.py` treats nested canonical JSON as source, does not allow stale Antigravity output to overwrite it, validates required fields before writes, and uses a non-mutating check path.
- [x] Optional runtime fields are preserved: `developer.thinking=true`, `orchestrator.thinking=true`, and `ui_visual_tester.fallback_agent="qa_tester"`.
- [x] Identifier safety follows the implemented rule: lowercase safe slug `^[a-z0-9_-]+$` (letters, digits, `_`, `-`; leading digits permitted). Resolved-root containment is authoritative; unsafe names or `fallback_agent` values fail before an output path is used.
- [x] Ecosystem/account/SDLC checks passed after the focused tests; the final ecosystem result is explicitly a read-only refresh, while generated outputs reflect the canonical boundary.

## TDD sequence and evidence

1. [x] QA specified failure cases for discovery policy, canonical profile derivation/non-activation, retained bundled capabilities, all four expected accounts, measurement false-green prevention, stale-mirror authority, required field validation, check-only immutability, optional runtime-field round trips, and unsafe identifiers/fallbacks.
2. [x] Developer implemented the account-policy and canonical-generator changes, including resolved-root containment.
3. [x] Independent QA passed the combined focused suites: `82` tests; the DevOps receipt also records successful compilation of all three updated Python modules.
4. [x] DevOps completed the authorized local account work and green ecosystem/account/SDLC checks. The final ecosystem status is a read-only refresh; the receipt records reversible backup/recovery availability.
5. [x] Independent reviewer confirmed the non-destructive boundary and preserved capabilities. The only former review issue was stale governance prose, reconciled by this document set.

**Authoritative local receipt:** [`plans/evidence/skill-budget-001/devops-live-budget.json`](../../plans/evidence/skill-budget-001/devops-live-budget.json) records `status: passed`, 82 focused tests, compilation of all three updated Python modules, green ecosystem/account/SDLC checks, and all four accounts at `2182` prompt characters, `truncated_skills: 0`, and `shortened_warning: false`. Its ecosystem value is `not_run_read_only_refresh`, not a new synchronization claim.

## Verification matrix

| Gate | Result |
|---|---|
| Focused QA | PASS — 82 tests, including unsafe `fallback_agent` negative coverage. |
| Python compilation | PASS — all three updated Python modules. |
| Canonical generator check | PASS — canonical nested JSON retained; generated loose/Antigravity outputs checked. |
| Ecosystem/account/SDLC checks | PASS — receipt records exit `0`; ecosystem is a read-only refresh. |
| Four-account live budget | PASS — default, codex1, codex2, codex3: `2182 <= 8000`, zero truncation, no warning. |
| Read-only review | PASS — containment and non-deletion boundary confirmed. |

## Recovery and remaining boundary

If a later local account-config verification fails, restore only the four DevOps-created local config backups and re-run the fail-closed budget check. Never remove plugin caches as rollback. No release, deployment, publication, commit, or push has been performed or is implied by this verified local result.

**Next action:** Owner review of the locally verified change set and explicit authorization for any integration/release action. Broader Horo Lite sprint lanes remain independently unresolved; do not archive active plans or create release notes from this ticket.
