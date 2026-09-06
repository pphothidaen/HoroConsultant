# Release QA Remediation Triage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a current, evidence-backed inventory of every reproducible release-QA failure and admit exact, non-overlapping TDD successor tickets without changing application source, tests, or configuration.

**Architecture:** Run one sequential read-only QA lane against the existing dirty worktree, starting with cached last-failed nodes and widening only enough to establish authoritative failure classes. Store one sanitized inventory, then translate only persistent deterministic failures into bounded subsystem plans and exact atomic tickets.

**Tech Stack:** Python 3.12, pytest, Node.js test runner, Git read-only inspection, JSON evidence, HoroConsultant Agile/TDD governance.

**Spec:** `docs/superpowers/specs/2026-09-05-release-qa-remediation-design.md`

## Global Constraints

- Preserve every pre-existing dirty-worktree change; do not reset, checkout, clean, stage, commit, or push.
- Do not modify application source, tests, fixtures, configuration, rules, skills, generated mirrors, credentials, or external systems during triage.
- Do not install or change Swift, Xcode, SDKs, compilers, packages, or other toolchains.
- Do not weaken assertions, authentication, route allowlists, release identity, negative controls, or metaphysics results.
- Use trimmed ASCII evidence only; never record secrets, Keychain values, raw provider streams, or unverified provider claims.
- Execute sequentially without subagents; the active environment policy does not authorize delegation.
- A cached node is not a current failure until a fresh command reproduces it.
- A full-suite green claim requires the current collected suite to exit 0; environment blockers remain failures for release purposes.

---

### Task 1: Freeze current triage context

**Files:**
- Create: `plans/evidence/release-qa-remediation-20260905/failure-inventory.json`
- Read: `.pytest_cache/v/cache/lastfailed`
- Read: `ATOMIC_TICKET.md`
- Read: `plans/plan.md`
- Read: `docs/superpowers/specs/2026-09-05-release-qa-remediation-design.md`

**Interfaces:**
- Consumes: pytest last-failed JSON keyed by node ID and read-only Git metadata.
- Produces: `failure-inventory-v1` with repository identity, baseline, closed classifications, clusters, blockers, and summary counts.

- [ ] **Step 1: Record immutable repository context**

Run:

```bash
git rev-parse HEAD
git branch --show-current
git status --short
```

Expected: exact HEAD and branch are printed; dirty paths are observed but not changed.

- [ ] **Step 2: Validate the cached failure input**

Run:

```bash
python3 -m json.tool .pytest_cache/v/cache/lastfailed
jq -r 'keys[]' .pytest_cache/v/cache/lastfailed
```

Expected: JSON validation exits 0 and prints cached node IDs. If the cache is absent or invalid, record that fact and reconstruct it with a fresh full run.

- [ ] **Step 3: Create the closed evidence object**

Create `failure-inventory.json` with concrete values and these exact fields:

```json
{
  "schema_version": "failure-inventory-v1",
  "ticket_id": "TICKET-REMED-QA-010",
  "captured_at": "RFC3339 timestamp with +07:00 offset",
  "repository": {
    "head": "observed 40-hex commit",
    "branch": "observed branch",
    "worktree_clean": false
  },
  "baseline": {
    "command": ["python3", "-m", "pytest", "-v", "--ignore=project/kaggle_kernel"],
    "exit_code": 1,
    "result": {"failed": 102, "passed": 4007, "skipped": 9, "errors": 36},
    "cache_status": "valid",
    "cached_node_ids": []
  },
  "classifications": [
    "source_defect",
    "configuration_drift",
    "stale_test_or_golden",
    "generated_drift",
    "environment_blocker",
    "external_or_flaky",
    "domain_hitl_conflict",
    "not_reproduced"
  ],
  "clusters": [],
  "blockers": [],
  "summary": {
    "cached_nodes": 0,
    "reproduced_nodes": 0,
    "not_reproduced_nodes": 0,
    "deterministic_successors": 0,
    "environment_blockers": 0,
    "domain_hitl_conflicts": 0,
    "status": "triage_in_progress"
  }
}
```

Replace the descriptive timestamp, commit, branch, node list, and counts with observed values. Do not include raw command output.

- [ ] **Step 4: Validate evidence syntax and scope**

Run:

```bash
python3 -m json.tool plans/evidence/release-qa-remediation-20260905/failure-inventory.json
git status --short
```

Expected: JSON validation exits 0; the only new triage evidence path is the inventory file.

### Task 2: Reproduce and classify cached failures

**Files:**
- Modify: `plans/evidence/release-qa-remediation-20260905/failure-inventory.json`
- Read: `.pytest_cache/v/cache/lastfailed`
- Read: failing tests and directly implicated sources only

**Interfaces:**
- Consumes: cached node IDs and `failure-inventory-v1` from Task 1.
- Produces: one cluster per contract group with exact node IDs, reproduction command/result, fingerprint, classification, contract authority, affected paths, successor decision, and stop reason.

- [ ] **Step 1: Re-run the current last-failed set**

Run:

```bash
python3 -m pytest -q --lf --ignore=project/kaggle_kernel --tb=short
```

Expected: persistent failures/errors exit nonzero and print current fingerprints. Exit 0 classifies cached nodes as not reproduced but does not prove the full suite green.

- [ ] **Step 2: Reproduce capacity independently**

Run:

```bash
python3 -m pytest -q project/tests/test_full_capacity_governance.py::test_exact_no_safe_exception_and_cross_process_replay_guard -vv
```

Expected before repair: nonzero `CAPACITY_CONFIG_INVALID` while the guard requires `agy1`–`agy4` and the config lists only `agy1` and `agy2`. Classify as configuration drift only when current evidence confirms both facts.

- [ ] **Step 3: Reproduce UI mirror and browser-safety contracts**

Run:

```bash
python3 -m pytest -q project/tests/test_object_rendering.py project/tests/test_gateway_ui_release_contract.py tests/test_mobile_tabs_accessibility_contract.py -vv
```

Expected before repair: exact mirror failures name `index.html` and `style.css`; browser safety names the missing safe-reason contract if still present. Do not select copy direction until Git/deployment evidence establishes it.

- [ ] **Step 4: Reproduce ecosystem parity after account-profile sync**

Run:

```bash
python3 -m pytest -q project/tests/test_ai_agent_ecosystem_sync.py project/tests/test_claude_governance.py project/tests/test_developer_routing_contract.py project/tests/test_requirement_grill_command_contract.py -vv
python3 scripts/sync_ai_agent_ecosystem.py --check
```

Expected: green nodes close as not reproduced. Persistent failures are classified from canonical-source and generator evidence; never edit generated files manually.

- [ ] **Step 5: Reproduce the known Swift environment boundary**

Run:

```bash
python3 -m pytest -q tests/test_ai_account_keychain_broker.py::test_swift_source_compiles_in_release_mode -vv
```

Expected under the observed mismatch: nonzero compiler/SDK compatibility evidence classified as `environment_blocker`; do not install or replace a toolchain.

- [ ] **Step 6: Classify domain nodes without mutation**

Run each persistent I Ching, Zi Wei, or other metaphysics node exactly as printed by Step 1. Classify a result `domain_hitl_conflict` unless current canonical evidence proves a non-domain infrastructure defect. Do not change formula source or expected vectors.

- [ ] **Step 7: Close summary arithmetic**

Assign each cached node to exactly one cluster or `not_reproduced`. Require:

```text
cached_nodes == reproduced_nodes + not_reproduced_nodes
deterministic_successors == number of clusters with successor_required=true
```

Set `summary.status` to `triage_complete` only after both invariants hold.

### Task 3: Admit exact subsystem successors

**Files:**
- Modify: `ATOMIC_TICKET.md`
- Modify: `plans/plan.md`
- Create: one `docs/superpowers/plans/2026-09-05-release-qa-remediation-<cluster>.md` per deterministic cluster
- Read: `plans/evidence/release-qa-remediation-20260905/failure-inventory.json`

**Interfaces:**
- Consumes: a closed inventory with `summary.status` equal to `triage_complete`.
- Produces: atomic successors with exact one-editor paths and one self-contained TDD plan per deterministic cluster.

- [ ] **Step 1: Reject inadmissible successors**

Do not create implementation tickets for `not_reproduced`, `environment_blocker`, `external_or_flaky`, or `domain_hitl_conflict`. Record only their evidence-backed closure or blocker.

- [ ] **Step 2: Create one ticket per deterministic cluster**

Each ticket must state ticket ID, owner role, required skills, exact writable files, read-only contract sources, baseline identity, RED fingerprint, dependencies, focused and neighbour commands, full-suite dependency, exclusions, recovery, and DONE/stop conditions.

Expected: no two active tickets own the same writable path; no ticket uses a directory wildcard when exact files are known.

- [ ] **Step 3: Write one self-contained cluster plan per ticket**

Repeat the global exclusions, exact failing test or negative control, minimal implementation interface, focused and neighbouring commands. Omit commit/push steps because those remain under `TICKET-RELEASE-004`.

- [ ] **Step 4: Validate governance artifacts**

Run:

```bash
rg -n 'T[B]D|T[O]DO|implement [l]ater|similar to [T]ask' docs/superpowers/plans/2026-09-05-release-qa-remediation-*.md
python3 scripts/sync_ai_agent_ecosystem.py --check
git diff --check -- ATOMIC_TICKET.md plans/plan.md docs/superpowers/plans plans/evidence/release-qa-remediation-20260905
```

Expected: placeholder search prints no matches; ecosystem and diff checks exit 0.

### Task 4: Execute successors and re-enter release QA

**Files:**
- Read: evidence-selected subsystem plans from Task 3
- Modify: only exact files assigned by each admitted ticket
- Create: only provenance/evidence files assigned by each admitted ticket

**Interfaces:**
- Consumes: a READY successor, its cluster plan, and verified baseline evidence.
- Produces: reviewed local corrections and green focused/neighbour/full verification evidence without release mutation.

- [ ] **Step 1: Execute successors sequentially**

Use `superpowers:systematic-debugging` before proposing each correction and `superpowers:test-driven-development` before source mutation. Preserve frozen tests; a wrong test requires a separate QA-owned supersession.

- [ ] **Step 2: Clear the last-failed set after each cluster**

Run:

```bash
python3 -m pytest -x --lf --ignore=project/kaggle_kernel -q
```

Expected: each iteration removes the corrected fingerprint or exposes the next current blocker without hiding it.

- [ ] **Step 3: Run full local release preflight**

Run only after admitted deterministic successors are green:

```bash
python3 -m pytest -v --ignore=project/kaggle_kernel
python3 scripts/sync_ai_agent_ecosystem.py --check
python3 project/core/code_reviewer.py --scan-secrets
```

Expected for release advancement: every command exits 0. Any test, toolchain, domain/HITL, external, sync, or secret failure keeps `TICKET-RELEASE-002` blocked.

- [ ] **Step 4: Record lifecycle truth**

Update `ATOMIC_TICKET.md` and `plans/plan.md` with exact results. Do not mark the sprint/release DONE, archive plans, update release notes, stage, commit, push, deploy, or publish without their separate prerequisites and authority.
