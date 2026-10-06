# KAN-264 Status — 2026-10-05 (Hermo audit; updated 2026-10-06 orchestrator resume)

## Done
- developer_api: poll fail-safe in `scripts/jira_query.py` + `orchestrator-dispatch.yml` (4b30b518, a2e0715a)
- devops: `sync-jira.yml` migrated to direct REST + new `scripts/sync_jira_to_atomic.py` (PR #128, e9b6c2be)
- ba_auditor: provenance manifest retired (supersedes 7f66545f verified ancestor), ATOMIC_TICKET row added
- verify-pr PASSED, 30 tests passing, live Jira call verified
- QA lane: regression test re-pinned to the REST path on main as `test_sync_jira_workflow_uses_direct_rest_no_twg_login` (asserts `twg login` gone, REST helper invoked with `--jql`, dead TWG_TOKEN/USER/SITE secrets removed) — closes the re-pin item from the 2026-10-05 audit
- devops: MTTR monitor excludes admin-disabled workflows (PR #126, ac1e1b72) — closes the gap noted as "not fixed here" in cd4b91e4's commit message

## Closed — superseded branch
- Branch `fix/KAN-264-twg-installer-consent` (commit cd4b91e4, "pass --skip-login and --skip-skills to the TWG installer") is superseded by PR #128: main no longer installs or invokes the TWG CLI anywhere, so the installer consent flags have no remaining call site and the branch would conflict on merge. Branch deleted 2026-10-06 with no PR; recoverable via sha cd4b91e4.

## Open
- Operator (HITL): create Atlassian 3LO OAuth app + add JIRA_CLIENT_ID/SECRET/REFRESH_TOKEN secrets to unlock poll
- sync-jira.yml `sync-from-jira` job inert (no jira event) — documented, never-runs
