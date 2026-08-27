# Rule 02: Testing, Test Provenance, and Verification

> Scope: `project/tests/**`, `tests/**`, `TDD-HORO-v3.0/tests/**`, test
> fixtures, provenance manifests, quality gates, and source commits governed by
> those tests.

## Test-first history gate

1. Before a source mutation lane starts, create a test-only baseline commit
   containing the new or changed tests, their fixtures, and exactly one closed
   `test-provenance-v1` manifest under `plans/test_provenance/`.
2. The baseline must demonstrate a red test or an explicit negative control.
   Record its argv, non-zero exit status, and concise failure fingerprint in the
   manifest. Acceptance criteria must come from the problem contract, not from
   implementation internals.
3. A source lane is eligible only after the baseline commit exists and the
   ticket state is `TEST_BASELINE_VERIFIED`. Every later commit for that ticket
   carries the exact `Test-Baseline: <sha>` trailer.
4. Test hashes are immutable from the baseline through completion. A commit
   that mixes governed tests with source is rejected.
5. History reconstructed after implementation is labeled
   `NON_TDD_RECONSTRUCTED`. It may be reviewed but must never be presented as
   verified test-first evidence.

## Correcting a frozen test

Stop the source lane when a frozen test is wrong. A QA-owned, independently
reviewed, test-only superseding baseline must record the old baseline SHA,
correction reason, new hashes, and new red/negative-control evidence. Resume
source work only after the superseding baseline passes the provenance gate.
Never amend, squash, delete, or silently rewrite the original baseline.

## Verification requirements

- Run tests with `python3 -m pytest`; acceptance requires exit code 0 for the
  current collected suite. Do not preserve a stale hard-coded test count.
- Do not swallow exceptions, remove or weaken assertions, comment out tests,
  add dummy fallbacks, or tailor expected values to the implementation merely
  to obtain green output.
- Prefer black-box contracts, invariants, negative controls, property or
  metamorphic cases, and deterministic domain vectors over private
  implementation details.
- After source freeze, QA runs the bounded suite followed by the applicable full
  regression, UI/API, E2E, security, ecosystem-sync, and release gates.
- Before sign-off, run the Git-history provenance guard and code reviewer with
  the ticket, exact baseline SHA, and manifest. Missing history or runtime
  evidence fails closed.

Local hooks are early feedback only and must be read-only. They may never run
formatters, version stamping, file writes, or `git add`. Required CI is the
authoritative merge gate because local hooks can be bypassed with
`--no-verify`.
