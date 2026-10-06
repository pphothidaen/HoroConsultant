# KAN-264 Status — 2026-10-05 (Hermo audit; updated 2026-10-06 orchestrator resume + provisioning complete)

## Done
- developer_api: poll fail-safe in `scripts/jira_query.py` + `orchestrator-dispatch.yml` (4b30b518, a2e0715a)
- devops: `sync-jira.yml` migrated to direct REST + new `scripts/sync_jira_to_atomic.py` (PR #128, e9b6c2be)
- ba_auditor: provenance manifest retired (supersedes 7f66545f verified ancestor), ATOMIC_TICKET row added
- verify-pr PASSED, 30 tests passing, live Jira call verified
- QA lane: regression test re-pinned to the REST path on main as `test_sync_jira_workflow_uses_direct_rest_no_twg_login` (asserts `twg login` gone, REST helper invoked with `--jql`, dead TWG_TOKEN/USER/SITE secrets removed) — closes the re-pin item from the 2026-10-05 audit
- devops: MTTR monitor excludes admin-disabled workflows (PR #126, ac1e1b72) — closes the gap noted as "not fixed here" in cd4b91e4's commit message
- operator (HITL) CLOSED 2026-10-06: Atlassian 3LO OAuth app "HoroConsultant Orchestrator Dispatch" created; JIRA_CLIENT_ID/SECRET/REFRESH_TOKEN provisioned with `offline_access`; authorization grant + code exchange driven via browser
- devops (PR #132, 486c6775): orchestrator-dispatch.yml fixed — `steps.*` reference removed from workflow-level env (made the workflow unparseable, HTTP 422 on every dispatch) and poll now resolves the OAuth gateway base URL (`api.atlassian.com/ex/jira/{cloudId}`) per run; 3LO bearer tokens are not accepted on the site hostname
- devops (PR #133): rotated refresh-token persistence wired to `GH_SECRETS_PAT` (fine-grained PAT, Secrets: Read and write on this repo only, expires 2027-10-06; annual renewal reminder armed). `GITHUB_TOKEN` cannot call the actions/secrets API
- QA (PR #131, 9094c928): `test_orchestrator_dispatch_uses_direct_rest_no_twg` guard added; poller verified green end-to-end (run 37397085686: refresh exit 0, rotated token persisted, JQL poll clean)

## Closed — superseded branches
- Branch `fix/KAN-264-twg-installer-consent` (commit cd4b91e4, "pass --skip-login and --skip-skills to the TWG installer") is superseded by PR #128: main no longer installs or invokes the TWG CLI anywhere, so the installer consent flags have no remaining call site and the branch would conflict on merge. Branch deleted 2026-10-06 with no PR; recoverable via sha cd4b91e4.
- Branch `fix/KAN-264-twg-token-refresh` (commits 7f66545f, 2cb8bfe5, 14e16e31; closed PR #127) is the TWG-based predecessor of the current per-run refresh design. Main's REST-based `scripts/refresh_jira_token.py` (PR #128, wired by PR #133) supersedes it, and merging would reintroduce `twg login`/TWG_TOKEN in violation of the merged TWG-free regression tests. Branch deleted 2026-10-06; recoverable via sha 14e16e31.

## Open
- sync-jira.yml `sync-from-jira` job inert (no jira event) — documented, never-runs
- Renewal: GH_SECRETS_PAT expires 2027-10-06 (annual reminder fires Sep 29)
