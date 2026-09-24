# Eval Harness Draft — Model Routing Golden Task Sets (KAN-101)

Status: DRAFT (design only — do not implement yet; YAGNI until the ledger
has >= 10 real entries to calibrate against).

## Purpose

The cost ledger (scripts/cost_ledger.py) records what sessions cost. This
harness measures what sessions *achieve*, so routing decisions (CLI vs
browser, reasoning tier vs frontier multimodal) can be made on
success-rate-per-token rather than narrative.

## Golden Task Sets (5 per role)

Each task is a frozen, replayable prompt + expected outcome. A run is
scored pass/fail against the expected outcome, then joined to the ledger
entry for that session.

### qa_tester

| # | Task | Pass criterion | Measures |
|---|------|----------------|----------|
| 1 | Write a failing test for a new script subcommand (RED) | test fails with expected fingerprint | test-first discipline |
| 2 | Freeze a provenance manifest for a test baseline | verify-pr PASSED on the baseline | governance fluency |
| 3 | Reproduce a known CI failure from logs and identify the error code | correct root-cause code named | diagnosis |
| 4 | Convert a narrative claim into a measurable metric assertion | assertion exists and passes | metric thinking |
| 5 | Review a diff for test/source separation violations | all violations caught, no false positives | review precision |

### devops

| # | Task | Pass criterion | Measures |
|---|------|----------------|----------|
| 1 | Add a workflow file without breaking the frozen inventory tests | all 3 inventory files updated, CI green | repo-specific hygiene |
| 2 | Diagnose a failed deployment from its log tail | correct blocking check identified | triage |
| 3 | Recover a branch after squash-merge broke verify-pr ancestry | verify-pr PASSED post-recovery | recovery pattern |
| 4 | Write a stdlib-only, ASCII-only CLI script per scripts/AGENTS.md | lint + constraints pass | portability discipline |
| 5 | Roll back a bad release using the stamped version anchor | correct SHA restored | release safety |

### reviewer

| # | Task | Pass criterion | Measures |
|---|------|----------------|----------|
| 1 | Review a PR with a missing Test-Baseline trailer | violation caught | provenance review |
| 2 | Review a manifest with supersedes="" (invalid) | schema error caught | manifest schema |
| 3 | Review a PR mixing test and source files in one commit | STAGED_COMMIT_MIXES_SOURCE_AND_TEST caught | commit hygiene |
| 4 | Verify a RED fingerprint actually matches a real failure | fabricated fingerprint rejected | honesty check |
| 5 | Review a report for metric-gaming (Goodhart) | aggregate manipulation caught | red-team review |

## Measurement Protocol

For each golden task, run N=3 times per routing config (e.g. cli+reasoning,
browser+frontier). Record per run:

- success: 1/0 against the pass criterion
- tool_calls: from the session ledger entry
- token_cost: from provider usage (when available; else estimated from
  tool_calls x avg tokens/call for that interface)
- wall_time: start-to-done seconds

Report per config:

- success_rate = mean(success)
- cost_per_success = total_token_cost / count(success)  (infinite if 0)
- rerun_cost = cost of re-running failed tasks once (measures whether
  retrying is cheaper than switching interface/model)

## Decision Rule (draft)

Route to the cheapest config whose lower-bound success rate (Wilson 95%
interval) stays above the target for that role's task class. With < 10
observations per config, fall back to the current default (cli+reasoning)
— the ledger exists precisely to make this threshold empirical later.

## Non-Goals (for now)

- No automated grading of free-form prose (only pass/fail criteria)
- No token-level instrumentation inside the agent runtime
- No web UI; reports are ASCII tables from cost_ledger.py report
