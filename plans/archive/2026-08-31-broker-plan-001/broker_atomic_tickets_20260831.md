# BROKER-PLAN-001 - Atomic Broker and Capacity Admission Plan

**Document ID**: `BROKER-PLAN-001`  
**Date**: `2026-08-31` (Asia/Bangkok)  
**Gate**: `APPROVED`  
**Authorized next phase**: test-only baselines in Milestone B0  
**Current document editor**: `business_analyst`  
**Current writable ownership**: `plans/broker_atomic_tickets_20260831.md` only  
**Capacity update**: owner-attested `37%` five-hour allowance remaining,
reset `14:24` Asia/Bangkok on `2026-08-31`; planning evidence only

## 1. GRILL REPORT

**Request**: Plan an atomic, test-first rollout of a local Swift broker and
immediate compatibility bridge, then safely migrate and harden the six account
wrappers, correct permissions, admit isolated account capacity, integrate Agile
governance, obtain independent QA, and prove rollback.

**Status**: `APPROVED`

**Context evidence**:

- `[AUTO]` `AGENTS.md`; `.agents/rules/02-testing-standards.md`;
  `.agents/rules/11-orchestrator-subagent-delegation.md`;
  `.agents/rules/13-ai-agent-ecosystem-sync.md`;
  `.agents/rules/17-multi-account-agent-orchestration.md`;
  `.agents/rules/18-adaptive-model-effort-routing.md`;
  `.agents/rules/19-agy-capacity-governance.md`; and
  `.agents/rules/20-context-handoff.md` define the governing baseline.
- `[AUTO]` `.agents/config/s3_capacity_policy.json`,
  `scripts/multiagent_capacity.py`, `scripts/multiagent_root_worker.py`, and
  `scripts/multiagent_prompt_command.py` establish current static alias and
  cap behavior.
- `[AUTO]` `plans/agile_governance_refactor_spec_20260831.md` is visible
  concurrent work and owns overlapping governance/capacity changes until its
  source freeze and ownership release.
- `[AUTO]` `plans/account_broker_installation_runbook_20260831.md` is visible
  concurrent design work for an on-demand immutable Swift/Keychain broker, but
  currently covers only four aliases and says execution is not authorized.
  This plan requires six-alias reconciliation before live migration.
- `[AUTO]` `scripts/codex_quota_workaround.py` is visible concurrent work. Its
  provider/auth subprocesses, inherited environment, local session-log scan,
  and raw status field are not admitted capacity evidence in this plan until
  independently hardened and approved.
- `[AUTO]` Metadata-only inspection found all six wrappers under
  `~/.local/bin/` as user executables with mode `0755`, and all six account
  homes under `~/.ai-accounts/{agy,codex}/account{1,2,3}` with mode `0755`.
  No wrapper/account file content or secret value was read into this plan.

**Scope**:

- **IN [CONFIRMED]**: test baselines; Swift broker; immediate bridge;
  installer and migration; wrapper hardening; permission remediation; `agy1`
  and `agy2` smoke/quota checks; `agy3` and `codex1`-`codex3` quota/isolation
  admission; continuity validation of the owner-observed native cap 6; Agile
  governance integration; ecosystem synchronization; independent QA; canary,
  rollback drill, and evidence-bound closure.
- **OUT [CONFIRMED]**: application/business logic, deployment or publishing,
  remote infrastructure changes, paid-provider fallback, credential rotation,
  reading or recording secret values, manual edits to generated
  `.codex/agents/*.toml`, and any QA/provider/keychain command in this planning
  lane. Security architecture, signing, live Keychain migration, provider
  runtime proof, and production action remain separately decision-constrained.
- **Stable interfaces [CONFIRMED]**: wrapper names `agy1`, `agy2`, `agy3`,
  `codex1`, `codex2`, and `codex3`; existing typed Rule 17 WorkResult and
  receipt contracts; one-editor-per-file; fail-closed quota, circuit,
  ownership, and model-floor gates.

### Nine-dimension matrix

| ID | Result | Evidence state and decision |
|---|---|---|
| D1 Scope boundary | Resolved | `[CONFIRMED]` Exact deliverable and sole current writable file are stated above. |
| D2 Requirement delta | Resolved | `[CONFIRMED]` Add a broker/bridge and migrate wrappers without weakening existing fail-closed dispatch contracts. |
| D3 Acceptance and stop | Resolved | `[CONFIRMED]` Each ticket below has measurable acceptance, evidence, and an exact stop condition. |
| D4 Inputs/dependencies | Resolved | `[AUTO]` AGENTS.md, Rules 02/11/13/17/18/19A/20, current capacity policy, dispatcher, root worker, and visible Agile M5 spec were scanned. |
| D5 Ownership/handoff | Resolved | `[CONFIRMED]` Every ticket names exactly one editor and writable ownership; overlapping files are sequential. |
| D6 Assumptions | Resolved | `[CONFIRMED]` Capacity facts supplied by the owner are preserved as planning inputs and not promoted to execution proof. |
| D7 Risk/recovery | Resolved | `[CONFIRMED]` Atomic backup/restore, canary, last-known-good caps, and fail-closed aborts are required. |
| D8 Budget/evidence | Resolved | `[AUTO]` Rule 18 applies at dispatch; only sanitized quota bands, typed results, digests, and trimmed ASCII-tagged logs may persist. |
| D9 Domain/HITL | Not applicable | `[NOT-APPLICABLE]` No metaphysical-domain behavior or source-domain decision changes. Provider execution still needs its own fresh exact grant. |

**Inputs and dependencies**: The owner-approved capacity facts, current
owner-attested `37%` five-hour allowance/reset observation, current macOS
wrapper/account layout, current repository policies, immutable test baselines,
Swift toolchain, released one-editor ownership, and future fresh provider probe
grants are required. No credential or keychain input belongs in an artifact.

**Risks and recovery**: Primary risks are wrapper command injection, account
cross-contamination, permission exposure, socket impersonation, orphaned
children, stale leases, circuit bypass, false capacity claims, and shared-file
conflict with Agile M5. Recovery is private hash-bound backup, atomic restore,
prior-mode restoration, broker disablement, and retention of the last passing
capacity stage.

**Waivers**: none.

**Blockers**: none for the authorized B0 test-baseline phase. All later source,
real-home, QA, provider, and capacity-probe tickets remain dependency-blocked as
shown below.

**Next question**: none.

### Assumption register

| Assumption/fact | State | Treatment |
|---|---|---|
| Earlier native dispatch observed 2 active children | `[CONFIRMED-SUPERSEDED]` | Historical observation retained only; the newer owner-observed cap 6 governs current planning. |
| Native collaboration has now been observed at cap 6 | `[CONFIRMED]` | Current-session owner observation replaces the earlier 2/target-4 baseline; schedule against 6 only as planning evidence until exact current evidence is reconciled. |
| Current orchestrator five-hour allowance is 37%, resetting 14:24 | `[CONFIRMED]` | User-attested planning evidence only; permits bounded critical-path planning but is not provider/runtime proof and must be refreshed after reset. |
| AGY executable capacity is currently 0 because the circuit breaker is open | `[CONFIRMED]` | No AGY start until policy-driven circuit recovery is evidenced; no manual-reset bypass. |
| Repository AGY cap is 3 per alias | `[AUTO]` | Enforced in `.agents/config/s3_capacity_policy.json` and `scripts/multiagent_capacity.py`; it is a ceiling, not proof. |
| `agy1` and `agy2` quota bands are healthy | `[CONFIRMED]` | Planning input only; wrapper safety and circuit state still block execution. |
| Current wrappers are unsafe | `[CONFIRMED]` | Their contents were not copied into this plan; replacement is test-first and rollback-backed. |
| `agy3` and `codex1`-`codex3` quota/isolation are unknown | `[CONFIRMED]` | Each starts at zero admitted capacity and needs alias-specific proof. |
| Visible Agile M5 work may mutate shared governance/capacity files | `[AUTO]` | Broker tickets touching those files wait for `GOV-M5` source freeze and ownership release. |

### Program success and stop conditions

The program is successful only when all tickets reach `DONE`, the independent
QA and review verdicts are `PASS`, rollback is rehearsed, all six aliases have
an explicit admitted or typed-blocked status, and the final capacity report
separates theoretical, policy-admitted, and runtime-proven values.

Only bounded critical-path work may consume capacity. Each lane is typed
`READ`, `WRITE`, or `EXECUTE`, has explicit acceptance/evidence/stop fields,
and must advance a dependency on the shortest safe path to closure. Exploratory
work, duplicate implementation/review, speculative probes, and refill merely
to occupy a slot are prohibited.

Stop the affected lane immediately on a missing/frozen-baseline mismatch,
ownership overlap, symlink or owner mismatch, unsafe permissions, schema or
digest mismatch, secret-bearing output, keychain prompt, unknown/low quota,
open circuit, provider identity mismatch, cross-account state change, invalid
receipt/WorkResult, timeout, orphan process, or failed rollback. No blind retry,
manual circuit reset, quota aggregation, direct-provider fallback, or capacity
promotion is permitted.

## 2. Current Capacity Truth

### Definitions

- **Theoretical capacity**: a platform, repository, or configuration ceiling.
  It authorizes nothing and proves no executable worker.
- **Policy-admitted capacity**: lanes that currently pass alias registry,
  quota, circuit, permission, ownership, lease, Rule 17, and Rule 18 gates.
- **Runtime-proven capacity**: the highest simultaneous bounded executions
  observed with valid, alias-bound terminal results under the exact current
  broker/configuration version.

### Baseline matrix

| Capacity domain | Theoretical/configured ceiling | Policy-admitted now | Runtime-proven now | Required next proof |
|---|---:|---:|---:|---|
| Native collaboration | Owner-observed current cap 6 | Up to 6 bounded disjoint critical-path lanes as current-session planning input | 6 observed; independently portable receipt proof not established in this plan | Reconcile evidence opportunistically from real critical-path lanes; no synthetic capacity probe |
| Current orchestrator allowance | Five-hour window, reset owner-attested at 14:24 | 37% planning band; bounded work only | Not provider execution proof | Refresh after reset or before any broad/high-burn decision |
| AGY `agy1` | 3 per alias | 0: circuit open and wrapper unsafe | 0 for this workstream | Circuit recovery, hardened wrapper, fresh safe quota band, one-lane smoke |
| AGY `agy2` | 3 per alias | 0: circuit open and wrapper unsafe | 0 for this workstream | Circuit recovery, hardened wrapper, fresh safe quota band, one-lane smoke |
| AGY `agy3` | Candidate 3 after registry change | 0: absent from current capacity registry and quota/isolation unknown | 0 | Registry, account isolation, quota, receipt, then staged concurrency |
| Codex `codex1` | 2 per current policy | 0 for broad work: quota/isolation unknown | 0 for this workstream | Hardened wrapper, fresh quota/isolation proof, one-lane smoke |
| Codex `codex2` | 2 per current policy | 0 for broad work: quota/isolation unknown | 0 for this workstream | Hardened wrapper, fresh quota/isolation proof, one-lane smoke |
| Codex `codex3` | 2 per capacity policy; not in ordinary dispatcher allowlist | 0 | 0 | Ordinary-dispatch registry, quota/isolation proof, one-lane smoke |
| Swift broker | Not implemented; no valid ceiling | 0 | 0 | Contract tests, implementation, canary, staged load evidence |

Static repository constraints must not be summed into a runtime claim. Root A
currently has a 3-worker aggregate pool over `codex1`-`codex3`, with per-account
caps of 2. Root B currently has a 3-worker aggregate pool over `agy1` and
`agy2`, while each AGY account has a cap of 3. Adding `agy3` would make the AGY
per-account sum 9 but would not raise Root B's aggregate 3-worker cap. Native
children and brokered provider processes may also share host resources, so
their ceilings are not additive without a combined runtime probe.

The final broker cap is therefore:

```text
safe_cap = minimum(
  configured ceiling,
  policy-admitted isolated lanes,
  last runtime-proven stable stage,
  host resource guard,
  useful disjoint ticket inventory
)
```

## 3. Lifecycle, Scheduling, and Evidence Rules

- Ticket states are exactly `TODO`, `READY`, `DOING`, `BLOCKED`,
  `NEEDS_HITL`, and `DONE`.
- Severity order is `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`; effort is
  `XS`, `S`, `M`, `L`, or `XL`.
- Each ticket has one editor. Other agents are read-only reviewers.
- No source ticket becomes `READY` before its test-only baseline is committed
  as `TEST_BASELINE_VERIFIED`; source commits bind the exact baseline SHA.
- Shared files named by the visible Agile M5 plan are not available until its
  owner records source freeze and releases ownership.
- Provider-facing tickets remain `BLOCKED`, then `NEEDS_HITL`, until a fresh
  exact execution grant is recorded. This plan is not that grant.
- Security/signing, live login-Keychain migration, provider runtime proof, and
  every production action require separate recorded decisions. Synthetic
  fixtures and static review never imply those decisions.
- Admit only bounded lane types:
  - `READ`: exact read-only sources and a decision-producing acceptance result.
  - `WRITE`: one editor, exact paths, frozen baseline, and no execution side effect.
  - `EXECUTE`: exact argv/action, bounded duration/budget, typed output, and an
    explicit authority decision for provider, Keychain, signing, or production scope.
- Refill only an eligible critical-path ticket. If none exists, emit
  `CAPACITY_EXCEPTION: NO_SAFE_CRITICAL_PATH_LANE`, replan, and leave the slot
  unused; do not manufacture fallback, exploratory, or duplicate work.
- A quota statement is persisted only as a sanitized band and timestamp. No
  secret, account identifier, raw stream, or quota percentage is retained.
- Every child result uses the standard typed headings: `Status`, `Scope owned`,
  `Evidence`, `Findings`, `Changed files`, `Residual risk`, and
  `Recommended next action`.
- Every implementation prompt includes: "You are not alone in the codebase;
  do not revert edits made by others. Work only within your assigned ownership
  and adapt to visible changes from other agents."

### Lane-type register

| Lane type | Tickets | Boundary |
|---|---|---|
| `READ` | none as a standalone ticket; read-only analysis is bounded inside independent review | Must produce a named decision/finding needed by a direct dependency; no exploratory scan. |
| `WRITE` | `BRK-B0-001`, `BRK-B0-010`, `BRK-B0-020`, `BRK-B0-030`, `BRK-B1-010`, `BRK-B1-020`, `BRK-B2-010`, `BRK-B2-020`, `BRK-B2-030`, `BRK-B3-010`, `BRK-B3-020`, `BRK-B6-030` | One editor and exact writable ownership; no provider, Keychain, signing, production, or unrelated command side effect. |
| `EXECUTE` | `BRK-B3-030`, `BRK-B4-010`, `BRK-B4-020`, `BRK-B5-010`, `BRK-B5-020`, `BRK-B5-025`, `BRK-B5-030`, `BRK-B5-040`, `BRK-B5-050`, `BRK-B5-060`, `BRK-B5-070`, `BRK-B5-080A`, `BRK-B5-080B`, `BRK-B5-080C`, `BRK-B6-010`, `BRK-B6-020` | Exact bounded action and typed evidence; decision-constrained actions remain unreachable until their named grants exist. |

## 4. Milestone DAG and Rollup

```text
B0 Test baselines
  -> B1 Swift broker and immediate bridge
  -> B2 Installer, wrapper, and permission tooling
  -> B3 Registry and Agile governance integration
  -> B4 Independent pre-install QA/review
  -> B5 Canary migration and isolated capacity admission
  -> B6 Runtime capacity certification, rollback drill, and closure
```

| Milestone | Purpose | Total | Done | Ready | Blocked | Needs HITL |
|---|---|---:|---:|---:|---:|---:|
| B0 | Plan and immutable test baselines | 4 | 1 | 3 | 0 | 0 |
| B1 | Swift broker and immediate bridge | 2 | 0 | 0 | 2 | 0 |
| B2 | Installer, wrapper, and permission tooling | 3 | 0 | 0 | 3 | 0 |
| B3 | Capacity registry and Agile integration | 3 | 0 | 0 | 3 | 0 |
| B4 | Independent pre-install QA and review | 2 | 0 | 0 | 2 | 0 |
| B5 | Canary and per-domain admissions | 11 | 0 | 0 | 10 | 1 |
| B6 | Capacity certification, rollback, closure | 3 | 0 | 0 | 3 | 0 |
| **Total** |  | **28** | **1** | **3** | **23** | **1** |

## 5. Atomic Tickets

### B0 - Test-first baselines

#### `BRK-B0-001` - Canonical atomic plan

- **State**: `DONE`
- **Severity**: `CRITICAL`
- **Effort**: `S`
- **One editor**: `business_analyst`
- **Writable ownership**: `plans/broker_atomic_tickets_20260831.md`
- **Dependencies**: none
- **Objective**: Freeze scope, capacity truth, ticket DAG, acceptance, and rollback boundaries.
- **Acceptance**: All requested workstreams are represented; every ticket has state, severity, effort, one editor, dependencies, acceptance, evidence, and stop condition; no secret values or execution claims appear.
- **Evidence**: This document and a scoped diff of this document only.
- **Stop condition**: Stop if another editor changes this file or if scope expands beyond the owner-approved boundary.

#### `BRK-B0-010` - Swift broker test-only baseline

- **State**: `READY`
- **Severity**: `CRITICAL`
- **Effort**: `M`
- **One editor**: `qa_tester_swift_baseline`
- **Writable ownership**: `tools/agent-broker/Tests/AgentBrokerTests/**`; `plans/test_provenance/broker-swift-baseline-20260831.json`
- **Dependencies**: `BRK-B0-001`
- **Objective**: Freeze black-box Swift contracts before broker source exists.
- **Acceptance**: A test-only commit records red/negative controls for closed request schema, immutable executable/manifest binding, bounded admission/backpressure, lease expiry, cancellation, crash cleanup, capacity clamping, duplicate/replay rejection, arbitrary-command rejection, secret-free process boundaries, and synthetic-Keychain failure modes without touching the login Keychain; the provenance manifest validates and records exact hashes.
- **Evidence**: Test commit SHA, red exit status/fingerprint, manifest digest, and collected test list.
- **Stop condition**: Stop before any `Sources/**` mutation, provider invocation, or correction to a frozen test without a superseding QA-owned baseline.

#### `BRK-B0-020` - Bridge/installer/wrapper/permission test-only baseline

- **State**: `READY`
- **Severity**: `CRITICAL`
- **Effort**: `M`
- **One editor**: `qa_tester_install_baseline`
- **Writable ownership**: `tests/test_agent_broker_bridge.py`; `tests/test_agent_broker_installer.py`; `tests/fixtures/agent_broker/**`; `plans/test_provenance/broker-install-baseline-20260831.json`
- **Dependencies**: `BRK-B0-001`
- **Objective**: Freeze compatibility, atomic migration, permissions, and rollback contracts.
- **Acceptance**: Negative controls cover shell metacharacter preservation without evaluation, strict six-alias allowlist, direct-provider fallback rejection, atomic backup/install/session-only rollback, symlink refusal, owner mismatch, account-home `0700`, sensitive regular-file `0600`, wrapper `0500`, state/backup directory `0700`, state/manifest `0600`, prohibited plaintext restoration, and idempotent dry-run.
- **Evidence**: Test-only commit SHA, manifest, red fingerprints, and fixture hashes containing no secret material.
- **Stop condition**: Stop before touching installer/bridge/wrapper source or any real home/account path.

#### `BRK-B0-030` - Capacity/admission/Agile test-only baseline

- **State**: `READY`
- **Severity**: `CRITICAL`
- **Effort**: `M`
- **One editor**: `qa_tester_capacity_baseline`
- **Writable ownership**: `tests/test_broker_capacity_admission.py`; `tests/test_broker_agile_governance.py`; `plans/test_provenance/broker-capacity-baseline-20260831.json`
- **Dependencies**: `BRK-B0-001`
- **Objective**: Freeze fail-closed registry, isolation, lifecycle, and capacity-promotion behavior.
- **Acceptance**: Negative controls prove `agy3`/`codex3` are not executable merely because configured; unknown quota admits zero; open circuit admits zero; AGY cap above 3 rejects; Codex cap above its frozen policy rejects; Root A/Root B aggregate caps are enforced; cross-account lease/circuit/quota reuse rejects; capacity categories cannot be conflated; lifecycle/DoR/DoD and one-editor checks reject invalid transitions.
- **Evidence**: Test-only commit SHA, closed provenance manifest, exact red fingerprints, and schema validation result.
- **Stop condition**: Stop before capacity, dispatcher, rule, skill, hook, or configuration source mutation.

### B1 - Swift broker and immediate bridge

#### `BRK-B1-010` - Swift broker core

- **State**: `BLOCKED`
- **Severity**: `CRITICAL`
- **Effort**: `L`
- **One editor**: `swift_broker_developer`
- **Writable ownership**: `tools/agent-broker/Package.swift`; `tools/agent-broker/Sources/AgentBroker/**`
- **Dependencies**: `BRK-B0-010=TEST_BASELINE_VERIFIED`
- **Objective**: Implement an on-demand local macOS Swift broker that owns admission, immutable alias/provider binding, bounded process lifecycle, and typed status, with a reviewed Security-framework boundary behind a protocol.
- **Acceptance**: Frozen Swift tests pass; request/result schemas reject unknown fields; exact signed binary/manifest and private state permissions are enforced; no daemon, socket, secret cache, `eval`, shell interpolation, arbitrary executable, provider fallback, or unbounded worker exists; security/signing paths default disabled pending their decision ticket; shutdown leaves no orphan child or stale lease.
- **Evidence**: Source commit with `Test-Baseline` trailer, Swift test receipt, binary hash, schema version, permission snapshot, and crash-cleanup receipt.
- **Stop condition**: Stop on baseline hash drift, unsupported macOS/Swift toolchain, permission/symlink mismatch, orphan process, schema ambiguity, or any need to inspect credentials.

#### `BRK-B1-020` - Immediate typed Python bridge

- **State**: `BLOCKED`
- **Severity**: `CRITICAL`
- **Effort**: `M`
- **One editor**: `broker_bridge_developer`
- **Writable ownership**: `scripts/multiagent_broker_bridge.py`; `.agents/schemas/agent-broker-request-v1.schema.json`; `.agents/schemas/agent-broker-result-v1.schema.json`; `.agents/config/agent_broker.v1.json`
- **Dependencies**: `BRK-B0-020=TEST_BASELINE_VERIFIED`; `BRK-B1-010=DONE`
- **Objective**: Translate the broker's closed request into existing typed dispatcher/library calls while preserving Rule 17 receipts and WorkResults.
- **Acceptance**: The bridge accepts only the six canonical aliases and declared actions; preserves argv boundaries; never invokes a shell; binds request/session/ticket/alias/provider/lease/ownership/decision digests; returns typed unavailable/blocked results; unavailable or unsigned broker fails `BROKER_UNAVAILABLE` or `BROKER_INSTALL_INTEGRITY` with no direct-provider fallback; session-only mode never reads Keychain data.
- **Evidence**: Focused frozen-test receipt, schema validation, fake-adapter receipt parity, and source commit with baseline trailer.
- **Stop condition**: Stop if integration requires free-form command execution, receipt inference from prose, raw stream persistence, or weakening the existing dispatcher gate.

### B2 - Installer, wrapper, and permission tooling

#### `BRK-B2-010` - Atomic immutable installer staging

- **State**: `BLOCKED`
- **Severity**: `HIGH`
- **Effort**: `M`
- **One editor**: `broker_installer_developer`
- **Writable ownership**: `scripts/install_agent_broker.py`; `config/agent-broker/broker-install-manifest-v1.json`
- **Dependencies**: `BRK-B0-020=TEST_BASELINE_VERIFIED`; `BRK-B1-010=DONE`; `BRK-B1-020=DONE`
- **Objective**: Build an idempotent, dry-run-first installer for side-by-side immutable broker/session-only-bridge releases, signed manifests, and private per-user migration/runtime roots; no LaunchAgent is required.
- **Acceptance**: Staging occurs in a private temporary directory; signatures, hashes, immutable ownership/modes, and manifests are checked before atomic rename; existing targets are never overwritten; install and repeated install are deterministic; uninstall delegates only to manifest-owned artifacts; signing remains disabled until separately decided; no network, provider, live Keychain, or secret read occurs.
- **Evidence**: Frozen installer-test receipt, dry-run plan, staged-tree manifest, mode/owner report, and source commit trailer.
- **Stop condition**: Stop on unresolved target, existing untracked target, owner mismatch, symlink, non-private backup location, hash mismatch, or non-atomic filesystem boundary.

#### `BRK-B2-020` - Six-wrapper hardening and migration tool

- **State**: `BLOCKED`
- **Severity**: `CRITICAL`
- **Effort**: `M`
- **One editor**: `wrapper_security_developer`
- **Writable ownership**: `scripts/agent_broker_wrapper.py`; `scripts/migrate_agent_wrappers.py`
- **Dependencies**: `BRK-B0-020=TEST_BASELINE_VERIFIED`; `BRK-B1-020=DONE`; `BRK-B2-010=DONE`
- **Objective**: Replace unsafe wrapper semantics with one strict broker client while preserving all six command names.
- **Acceptance**: `agy1`-`agy3` and `codex1`-`codex3` map by a closed basename/manifest binding; arguments remain an exact array; unknown flags/aliases fail before broker contact; no `eval`, shell, environment dump, raw output, credential access, direct CLI fallback, or alias substitution exists; migration is dry-run-first, hash-bound, atomic, and reversible.
- **Evidence**: Frozen wrapper tests, six alias mapping fixtures, sanitized eligibility/backup-complete fields, replacement wrapper hashes only, migration manifest schema result, and source commit trailer; no legacy wrapper hash, size, excerpt, or derivative is emitted.
- **Stop condition**: Stop if any current wrapper cannot be privately backed up, contains an unresolved execution path, resolves through a symlink chain outside approved roots, or requires live Keychain access before the decision gate.

#### `BRK-B2-030` - Permission remediation tool

- **State**: `BLOCKED`
- **Severity**: `CRITICAL`
- **Effort**: `S`
- **One editor**: `permission_security_developer`
- **Writable ownership**: `scripts/harden_agent_account_permissions.py`
- **Dependencies**: `BRK-B0-020=TEST_BASELINE_VERIFIED`; `BRK-B2-010=DONE`
- **Objective**: Enforce owner-only account and broker state boundaries without reading credential values.
- **Acceptance**: Dry-run inventories metadata only; account homes become `0700`; known sensitive regular files become `0600`; broker state/backup directories are `0700`; state/manifests are `0600`; replacement/session-only/disabled wrappers are user-owned executable `0500`; symlinks, foreign owners, ACL surprises, and broader paths reject; rollback records prior modes.
- **Evidence**: Frozen permission tests, metadata-only before/after fixture, rollback-mode manifest, and source commit trailer.
- **Stop condition**: Stop before mutation on any foreign owner, symlink, unknown file class, path outside the six exact account homes/broker roots, or request to display file content.

### B3 - Registry and Agile governance integration

#### `BRK-B3-010` - Six-alias registry and broker admission wiring

- **State**: `BLOCKED`
- **Severity**: `CRITICAL`
- **Effort**: `L`
- **One editor**: `capacity_registry_developer`
- **Writable ownership**: `scripts/multiagent_capacity.py`; `scripts/multiagent_root_worker.py`; `scripts/multiagent_prompt_command.py`; `scripts/codex_quota_workaround.py`; `.agents/config/s3_capacity_policy.json`; `.agents/config/multiagent_model_policy.yaml`
- **Dependencies**: `BRK-B0-030=TEST_BASELINE_VERIFIED`; `BRK-B1-020=DONE`; visible `GOV-M5-005=DONE` or formally superseded; shared-file ownership released
- **Objective**: Make all six aliases structurally known to capacity and ordinary dispatch while defaulting every unproven alias to disabled/zero admitted capacity.
- **Acceptance**: `agy3` is added with AGY hard cap 3; existing Codex per-account cap 2 and Root A/Root B aggregate cap 3 remain unchanged until separate proof; all six aliases have immutable provider binding; unknown quota/open circuit/unsafe permissions deny admission; broker lease is required; cross-account state reuse rejects; no static config enables provider execution. The concurrent Codex quota helper is replaced or hardened to emit content-free coarse bands only, inherit no unsafe environment, persist no raw auth/provider/session-log data, and never run a micro-canary without its own provider-runtime decision.
- **Evidence**: Frozen capacity tests, config/schema diff, alias matrix, source commit trailer, and proof that all new aliases default to disabled.
- **Stop condition**: Stop on Agile M5 or quota-helper ownership overlap, pin/schema cascade without a dedicated update, cap increase without runtime evidence, raw/session-derived quota evidence, or any compatibility failure in the existing four-alias path.

#### `BRK-B3-020` - Agile Rule 21 and skill integration

- **State**: `BLOCKED`
- **Severity**: `HIGH`
- **Effort**: `M`
- **One editor**: `agile_governance_editor`
- **Writable ownership**: `.agents/rules/21-agile-governance.md`; `.agents/skills/agile-governance/SKILL.md`; `.agents/skills/agile-governance/evals/evals.json`; `.agents/AGENTS.md`
- **Dependencies**: `BRK-B0-030=TEST_BASELINE_VERIFIED`; `BRK-B3-010=DONE`; visible `GOV-M5-003=DONE` and ownership released
- **Objective**: Integrate broker admission and capacity truth into the canonical six-state Agile lifecycle.
- **Acceptance**: DoR requires baseline, one editor, dependencies, safe quota, closed circuit, permissions, lease, Rule 18 decision, and exact evidence path; DoD requires typed result, independent QA/review, rollback status, and capacity classification; WIP counts policy-admitted work only; theoretical capacity never moves a ticket to `READY` or `DOING`.
- **Evidence**: Frozen governance tests, skill eval result, rule/skill diff, and source commit trailer.
- **Stop condition**: Stop if the visible Agile work is not frozen, if duplicate Rule 21 authority would result, or if lifecycle wording permits prose-only completion or phantom WIP.

#### `BRK-B3-030` - Ecosystem sync and generated mirrors

- **State**: `BLOCKED`
- **Severity**: `HIGH`
- **Effort**: `S`
- **One editor**: `ecosystem_sync_operator`
- **Writable ownership**: only outputs generated by `scripts/sync_ai_agent_ecosystem.py --sync` from the frozen B3 sources, including `.agents/agents/**`, `.codex/agents/**`, `.claude/rules/**`, and `.agy/rules/**`
- **Dependencies**: `BRK-B3-010=DONE`; `BRK-B3-020=DONE`; all generated-output ownership released
- **Objective**: Synchronize broker/Agile governance without hand-editing generated artifacts.
- **Acceptance**: One sync run changes only expected generated outputs; subsequent read-only sync check reports parity; no source-of-truth or unrelated dirty file changes; generated Codex TOML is attributable only to the synchronizer.
- **Evidence**: Sync receipt, before/after generated manifest, scoped diff, and read-only parity check.
- **Stop condition**: Stop on unrelated output, nondeterminism, dirty-file collision, source mutation by the sync, or secret-bearing generated content.

### B4 - Independent pre-install QA and review

#### `BRK-B4-010` - Independent functional/security QA

- **State**: `BLOCKED`
- **Severity**: `CRITICAL`
- **Effort**: `L`
- **One editor**: `independent_broker_qa`
- **Writable ownership**: `plans/evidence/broker/b4-independent-qa.json` only; all source/tests/config are read-only
- **Dependencies**: `BRK-B1-010..BRK-B3-030=DONE`; all source frozen
- **Objective**: Independently verify broker, bridge, installer, wrappers, permissions, registry, Agile governance, and ecosystem parity in an isolated temporary home with fake providers.
- **Acceptance**: Swift and Python focused suites, provenance guard, migration/session-only rollback fixtures, crash/orphan checks, permission checks, schema checks, Agile evals, ecosystem check, and secret scan all exit 0; only synthetic isolated Keychain fixtures may run after the security test decision, and no login Keychain, real provider, account mutation, deployment, or network call occurs.
- **Evidence**: Sanitized command argv/digests, exit statuses, test collection counts determined at run time, concise failure fingerprints if any, and signed QA verdict.
- **Stop condition**: Stop and return `BLOCKED` on first Critical/High failure; do not edit frozen source/tests or auto-remediate.

#### `BRK-B4-020` - Independent architecture/code review

- **State**: `BLOCKED`
- **Severity**: `CRITICAL`
- **Effort**: `M`
- **One editor**: `independent_broker_reviewer`
- **Writable ownership**: `plans/evidence/broker/b4-independent-review.json` only; implementation is read-only
- **Dependencies**: `BRK-B4-010=DONE`
- **Objective**: Review trust boundaries, process lifecycle, install/rollback safety, permission model, and capacity claim correctness independently of implementers.
- **Acceptance**: No unresolved Critical/High finding; review explicitly checks arbitrary execution, TOCTOU/symlink attacks, binary/signature/manifest substitution, Keychain ACL/cardinality/UI behavior, alias/provider confusion, secret leakage, stale leases, circuit bypass, cross-account contamination, orphan cleanup, and theoretical/admitted/proven language.
- **Evidence**: Finding register with severity, exact path/line references, disposition, and `PASS` or typed blocker.
- **Stop condition**: Any unresolved Critical/High finding blocks real-home installation and provider admission.

### B5 - Canary migration and isolated capacity admission

#### `BRK-B5-010` - Real-home canary install and migration

- **State**: `BLOCKED`
- **Severity**: `CRITICAL`
- **Effort**: `M`
- **One editor**: `broker_canary_operator`
- **Writable ownership**: `/Library/Application Support/HoroConsultant/AccountBroker/**`; `~/.local/bin/{agy1,agy2,agy3,codex1,codex2,codex3}`; `~/Library/Application Support/HoroConsultant/AccountBroker/**`; `plans/evidence/broker/b5-canary-install.json`
- **Dependencies**: `BRK-B4-010=DONE`; `BRK-B4-020=DONE`; exact backup targets resolved; no ownership collision
- **Objective**: Install the reviewed broker/session-only bridge immutably and stage six wrapper replacements without activating live Keychain or provider behavior.
- **Acceptance**: Dry-run matches the approved six-alias manifest; private sensitive-wrapper backup completes internally before replacement but emits no content/hash/size; installed signatures/hashes/modes match reviewed artifacts; all six wrappers are staged as session-only or disabled `0500` routes; no provider/login-Keychain/network action occurs; rollback mode is immediately available.
- **Evidence**: Installed artifact/replacement-wrapper hashes and modes, sanitized legacy-backup completion flags, immutable-install result, six route-only results, and rollback manifest identifier.
- **Stop condition**: Stop and install session-only/disabled rollback wrappers on any artifact hash/mode/owner mismatch, wrapper incompatibility, unexpected prompt, provider start, live Keychain contact, or target drift; never restore a plaintext legacy wrapper.

#### `BRK-B5-020` - Real-home permission remediation

- **State**: `BLOCKED`
- **Severity**: `CRITICAL`
- **Effort**: `S`
- **One editor**: `account_permission_operator`
- **Writable ownership**: exactly `~/.ai-accounts/{agy,codex}/account{1,2,3}` metadata/modes and `plans/evidence/broker/b5-permissions.json`; file contents remain unread
- **Dependencies**: `BRK-B5-010=DONE`; rollback-mode manifest present
- **Objective**: Change currently broad account-home permissions to the reviewed owner-only policy.
- **Acceptance**: Each of six account homes is user-owned, regular directory, non-symlink, and `0700`; allowlisted sensitive regular files are `0600`; no content is emitted; wrapper and broker health remain available without provider start.
- **Evidence**: Metadata-only before/after mode/owner table and rollback-mode manifest digest.
- **Stop condition**: Stop and restore changed modes on foreign ownership, symlink, ACL anomaly, unknown target, broker health regression, or any content/keychain access.

#### `BRK-B5-025` - Security, signing, and live Keychain migration decision

- **State**: `NEEDS_HITL`
- **Severity**: `CRITICAL`
- **Effort**: `M`
- **One editor**: `broker_security_migration_operator`
- **Writable ownership**: exact immutable broker signing/ACL metadata; exact login-Keychain service/account items for `agy1`-`agy3` and `codex1`-`codex3`; six wrapper activation states; `plans/evidence/broker/b5-security-keychain-decision.json`
- **Dependencies**: `BRK-B5-010=DONE`; `BRK-B5-020=DONE`; six-alias revision of `BROKER-RUNBOOK-001` independently reviewed and frozen; synthetic security suite passes; fresh named security/signing/live-migration owner decisions
- **Objective**: Decide and, only if separately authorized, execute serial six-alias signing/ACL/live-Keychain migration without exposing or restoring plaintext wrapper material.
- **Acceptance**: Decision record independently covers signing mode/identity, immutable path, exact login Keychain, UI-disabled access, create-only six-item cardinality, broker-only ACL, serial alias order, session-only rollback, and backup quarantine. If execution is approved, each alias reaches exact ACL/cardinality/wrapper/environment checks before the next begins; if not, all wrappers remain session-only/disabled and the ticket returns typed `NEEDS_HITL` without Keychain contact.
- **Evidence**: Decision identifiers, binary/manifest digests, synthetic-gate digest, sanitized per-alias `PASS|BLOCKED|ROLLED_BACK`, and secret-exposure boolean only; no wrapper derivative, raw Keychain/provider data, identity, or secret value.
- **Stop condition**: Stop before live action without every named decision; during action stop serial migration on lock/UI request, item collision/cardinality/ACL mismatch, signature drift, wrapper/environment defect, or exposure signal; quarantine and use session-only/disabled rollback, never plaintext restoration.

#### `BRK-B5-030` - AGY circuit recovery gate

- **State**: `BLOCKED`
- **Severity**: `CRITICAL`
- **Effort**: `XS`
- **One editor**: `agy_circuit_operator`
- **Writable ownership**: `plans/evidence/broker/b5-agy-circuit.json` only; broker/capacity state is operational state under policy
- **Dependencies**: `BRK-B5-025=DONE`; `BRK-B3-010=DONE`
- **Objective**: Prove policy-driven expiration/recovery of the AGY circuit before any AGY provider attempt.
- **Acceptance**: A sanitized broker snapshot shows no active AGY circuit and no manual reset/config weakening; failure history is retained per policy; lease preflight remains alias-isolated.
- **Evidence**: Snapshot digest, policy digest/version, observation time, circuit state, and typed admission result without provider start.
- **Stop condition**: If any AGY circuit remains open or state/policy digest is invalid, remain `BLOCKED`; do not reset, delete state, or invoke AGY.

#### `BRK-B5-040` - Native observed-cap-6 continuity evidence

- **State**: `BLOCKED`
- **Severity**: `HIGH`
- **Effort**: `S`
- **One editor**: `native_capacity_probe_operator`
- **Writable ownership**: `plans/evidence/broker/b5-native-capacity.json` only; probe tasks are read-only and disjoint
- **Dependencies**: `BRK-B4-020=DONE`; enough independent critical-path `READ`/`WRITE`/`EXECUTE` tickets naturally become eligible; no synthetic work is created
- **Objective**: Reconcile the owner-observed native cap 6 from real critical-path execution without a standalone exploratory capacity probe.
- **Acceptance**: When normal critical-path scheduling naturally reaches concurrency, collect exact lane type, ownership, acceptance, simultaneous running intervals, and terminal typed results up to observed cap 6; no duplicate objective, fallback busywork, or capacity-only task is dispatched. Until that evidence exists, 6 remains owner-attested planning capacity rather than portable proof.
- **Evidence**: Owner observation plus any naturally produced platform-native identifiers, overlap intervals, exact critical-path ticket IDs/types, terminal results, and no ownership conflict; no provider receipt claim.
- **Stop condition**: Stop collecting at first rejection, timeout, ownership overlap, orphan, invalid result, or loss of critical-path eligibility; reduce admitted scheduling to the highest naturally evidenced stable level and do not create replacement probe work.

#### `BRK-B5-050` - `agy1` one-lane smoke and quota admission

- **State**: `BLOCKED`
- **Severity**: `CRITICAL`
- **Effort**: `XS`
- **One editor**: `agy1_admission_operator`
- **Writable ownership**: isolated `agy1` broker/capacity state and `plans/evidence/broker/b5-agy1-admission.json`
- **Dependencies**: `BRK-B5-030=DONE`; `BRK-B5-025=DONE`; fresh exact provider-execution grant; `agy1` lease and Rule 18 decision
- **Objective**: Admit exactly one `agy1` lane using the hardened wrapper and broker.
- **Acceptance**: Fresh sanitized quota band is safe; account home/wrapper/provider identity are bound; one bounded read-only smoke returns a valid alias-bound receipt and WorkResult; only `agy1` lease/circuit/burn state changes; admitted capacity becomes 1, not 3.
- **Evidence**: Sanitized quota band/timestamp, broker request/lease digests, execution receipt, WorkResult, state-delta digest, and `validated in-process only` AGY wording.
- **Stop condition**: Stop with no retry on unknown/low quota, circuit opening, keychain/auth prompt, provider mismatch, timeout, invalid event/result, cross-account delta, or secret-bearing output.

#### `BRK-B5-060` - `agy2` one-lane smoke and quota admission

- **State**: `BLOCKED`
- **Severity**: `CRITICAL`
- **Effort**: `XS`
- **One editor**: `agy2_admission_operator`
- **Writable ownership**: isolated `agy2` broker/capacity state and `plans/evidence/broker/b5-agy2-admission.json`
- **Dependencies**: `BRK-B5-030=DONE`; `BRK-B5-025=DONE`; fresh exact provider-execution grant; `agy2` lease and Rule 18 decision
- **Objective**: Admit exactly one `agy2` lane using the hardened wrapper and broker.
- **Acceptance**: Fresh sanitized quota band is safe; account home/wrapper/provider identity are bound; one bounded read-only smoke returns a valid alias-bound receipt and WorkResult; only `agy2` state changes; admitted capacity becomes 1, not 3.
- **Evidence**: Sanitized quota band/timestamp, request/lease digests, receipt, WorkResult, state-delta digest, and `validated in-process only` wording.
- **Stop condition**: Same fail-closed no-retry conditions as `BRK-B5-050`, scoped independently to `agy2`.

#### `BRK-B5-070` - `agy3` quota/isolation admission

- **State**: `BLOCKED`
- **Severity**: `CRITICAL`
- **Effort**: `S`
- **One editor**: `agy3_admission_operator`
- **Writable ownership**: isolated `agy3` broker/capacity state and `plans/evidence/broker/b5-agy3-admission.json`
- **Dependencies**: `BRK-B3-010=DONE`; `BRK-B5-030=DONE`; `BRK-B5-025=DONE`; fresh exact provider-execution grant; `agy3` lease and Rule 18 decision
- **Objective**: Prove `agy3` is a distinct account pool before admitting one lane.
- **Acceptance**: Canonical home and wrapper are unique and owner-only; quota band is freshly sanitized; lease/circuit/burn/queue keys are disjoint from `agy1/2`; one read-only smoke yields an `agy3`-bound receipt/WorkResult and no sibling delta; admitted capacity becomes 1.
- **Evidence**: Non-secret isolation fingerprint, quota band/timestamp, receipt/WorkResult, before/after state digests for all AGY pools, and in-process-only qualifier.
- **Stop condition**: Stop with no retry if identity/isolation cannot be proven, quota remains unknown/low, any sibling state changes, or any standard provider safety gate fails.

#### `BRK-B5-080A` - `codex1` quota/isolation admission

- **State**: `BLOCKED`
- **Severity**: `CRITICAL`
- **Effort**: `S`
- **One editor**: `codex1_admission_operator`
- **Writable ownership**: isolated `codex1` broker/capacity state and `plans/evidence/broker/b5-codex1-admission.json`
- **Dependencies**: `BRK-B3-010=DONE`; `BRK-B5-025=DONE`; hardened content-free Codex quota observer accepted; fresh exact provider-execution grant; `codex1` lease and Rule 18 decision
- **Objective**: Prove quota, identity, and state isolation before admitting one `codex1` lane.
- **Acceptance**: Fresh sanitized quota band is safe; account/wrapper/provider bindings pass; one bounded read-only smoke has a valid receipt/WorkResult; sibling Codex/AGY states do not change; admitted capacity becomes 1.
- **Evidence**: Non-secret isolation fingerprint, quota band/timestamp, lease/receipt/WorkResult, and all-pool state-delta digests.
- **Stop condition**: Stop with no retry on unknown/low quota, auth/keychain prompt, identity mismatch, invalid receipt/result, cross-pool delta, timeout, or secret-bearing output.

#### `BRK-B5-080B` - `codex2` quota/isolation admission

- **State**: `BLOCKED`
- **Severity**: `CRITICAL`
- **Effort**: `S`
- **One editor**: `codex2_admission_operator`
- **Writable ownership**: isolated `codex2` broker/capacity state and `plans/evidence/broker/b5-codex2-admission.json`
- **Dependencies**: `BRK-B3-010=DONE`; `BRK-B5-025=DONE`; hardened content-free Codex quota observer accepted; fresh exact provider-execution grant; `codex2` lease and Rule 18 decision
- **Objective**: Prove quota, identity, and state isolation before admitting one `codex2` lane.
- **Acceptance**: Same measurable one-lane admission contract as `BRK-B5-080A`, bound exclusively to `codex2`.
- **Evidence**: `codex2` isolation fingerprint, quota band/timestamp, lease/receipt/WorkResult, and all-pool state-delta digests.
- **Stop condition**: Same fail-closed no-retry conditions as `BRK-B5-080A`, scoped independently to `codex2`.

#### `BRK-B5-080C` - `codex3` quota/isolation admission

- **State**: `BLOCKED`
- **Severity**: `CRITICAL`
- **Effort**: `S`
- **One editor**: `codex3_admission_operator`
- **Writable ownership**: isolated `codex3` broker/capacity state and `plans/evidence/broker/b5-codex3-admission.json`
- **Dependencies**: `BRK-B3-010=DONE`; `BRK-B5-025=DONE`; ordinary-dispatch registry proof; hardened content-free Codex quota observer accepted; fresh exact provider-execution grant; `codex3` lease and Rule 18 decision
- **Objective**: Prove the newly ordinary-admitted `codex3` route is distinct and safe before assigning one lane.
- **Acceptance**: Dispatcher and broker agree on `codex3` provider binding; fresh quota band is safe; account/state isolation holds; one read-only smoke yields a valid `codex3` receipt/WorkResult; admitted capacity becomes 1.
- **Evidence**: Registry digest, isolation fingerprint, quota band/timestamp, lease/receipt/WorkResult, and all-pool state-delta digests.
- **Stop condition**: Stop with no retry if ordinary and broker registries differ, identity/isolation is ambiguous, or any standard Codex safety gate fails.

### B6 - Certification, rollback, and closure

#### `BRK-B6-010` - Staged per-pool and combined capacity certification

- **State**: `BLOCKED`
- **Severity**: `CRITICAL`
- **Effort**: `L`
- **One editor**: `capacity_certification_operator`
- **Writable ownership**: `plans/evidence/broker/b6-capacity-certification.json` only; runtime state changes are lease-bound and account-isolated
- **Dependencies**: `BRK-B5-040..BRK-B5-080C=DONE` or each incomplete alias has a terminal owner-accepted blocker; useful disjoint bounded work exists; fresh exact probe grants
- **Objective**: Measure, never infer, maximum safe broker capacity under per-account, per-root, native, host-resource, ownership, and quota constraints.
- **Acceptance**: For each admitted alias, probe 1 then increment by one up to its unchanged policy cap; then probe Root A and Root B aggregates up to 3; finally run a combined native/broker stage only if host telemetry and ownership remain safe. Each stage requires simultaneous overlap, valid terminal results, no state leakage/orphans, bounded resource use, and stable latency/error thresholds declared before execution. Final admitted values equal the last passing stages, not theoretical ceilings.
- **Evidence**: Stage matrix with configured/admitted/proven counts, exact configuration/policy/binary digests, overlap intervals, typed results, sanitized host metrics, rejected stage reason, and final cap calculation.
- **Stop condition**: Stop the affected domain at the first circuit, quota, isolation, ownership, receipt, orphan, timeout, or resource-threshold failure; retain the previous passing cap, do not retry, and do not sum overlapping domains.

#### `BRK-B6-020` - Independent rollback drill and final QA

- **State**: `BLOCKED`
- **Severity**: `CRITICAL`
- **Effort**: `M`
- **One editor**: `independent_rollback_qa`
- **Writable ownership**: `plans/evidence/broker/b6-rollback-qa.json` only; installer-managed targets may change only through the reviewed rollback command
- **Dependencies**: `BRK-B6-010=DONE`; original private backup and prior-mode manifests intact
- **Objective**: Prove recovery to six owner-only session-only/disabled wrappers and broker-disabled routing, then reinstall the reviewed version without restoring plaintext or losing account state.
- **Acceptance**: Rollback stops new broker admission, changes only manifest-owned artifacts, atomically installs six reviewed `0500` session-only/disabled wrappers, leaves account content and quarantined Keychain items/backups untouched, performs no provider/live-Keychain action, and passes route-only rollback checks; reinstall restores reviewed artifact/wrapper hashes and all certified caps remain disabled until explicitly re-admitted.
- **Evidence**: Active-wrapper and installed-artifact hashes/modes only, sanitized backup/item quarantine states, process/orphan check, manifest ownership proof, route-only results, and independent `PASS` verdict; no legacy wrapper derivative.
- **Stop condition**: Stop and require HITL if manifest/ownership differs, an unowned target would be removed, session-only/disabled restoration is partial, plaintext restoration would occur, account content would be read/changed, or any provider/live-Keychain action is requested.

#### `BRK-B6-030` - Evidence reconciliation and closure

- **State**: `BLOCKED`
- **Severity**: `HIGH`
- **Effort**: `S`
- **One editor**: `broker_release_governor`
- **Writable ownership**: the future authoritative board/plan/handoff artifacts explicitly assigned at closure; no production/deployment target
- **Dependencies**: all prior tickets `DONE` or terminal `BLOCKED`/`NEEDS_HITL` with owner disposition; `BRK-B6-020=DONE`; final ecosystem check passes
- **Objective**: Reconcile ticket states, accepted blockers, evidence digests, rollback readiness, and the final three-category capacity report.
- **Acceptance**: Ticket totals reconcile; every `DONE` has evidence; no alias is reported executable without current proof; theoretical, policy-admitted, and runtime-proven values are separate; residual risks and operator actions are explicit; no secret or transient quota percentage is recorded; no release/deployment claim is made.
- **Evidence**: Final rollup, evidence index/digests, independent QA/review/rollback verdicts, and synchronized governance check.
- **Stop condition**: Do not close on missing evidence, stale quota/circuit state, unresolved Critical/High finding, rollback failure, generated-mirror drift, or inconsistent capacity totals.

## 6. Admission and Rollback Decision Matrix

| Condition | Admission result | Required action |
|---|---|---|
| Theoretical/configured cap only | 0 new lanes | Keep disabled; create test/probe evidence. |
| Healthy user-attested quota but unsafe wrapper/open circuit | 0 new lanes | Harden wrapper and wait for policy recovery. |
| Unknown quota or isolation | 0 new lanes | One exact sanitized observation/isolation ticket with fresh grant. |
| One valid smoke receipt and isolated state | Admit 1 for that alias | Keep higher concurrency disabled pending staged proof. |
| Security/signing/live Keychain decision missing | 0 activated wrappers | Keep all six wrappers session-only/disabled; return `NEEDS_HITL`. |
| Stage N passes all gates | Admit N up to policy cap | Record exact config/runtime digest and proceed to N+1 only if authorized. |
| Stage N fails | Retain N-1 | Stop, open/retain circuit as policy requires, no retry in ticket. |
| Rollback manifest/hash mismatch | No mutation | `NEEDS_HITL`; preserve all current files and processes safely. |

## 7. Handoff Boundary

Only `BRK-B0-010`, `BRK-B0-020`, and `BRK-B0-030` are ready after this plan.
They are the only current critical-path refill candidates and may run in
parallel only if their exact writable ownership remains disjoint. The
owner-observed native cap is 6, but only these three useful lanes exist; the
remaining slots stay unused rather than receiving exploratory or duplicate
work. The owner-attested five-hour allowance is 37% until the stated 14:24
reset and must be refreshed afterward. No broker source, wrapper, permission,
capacity config, signing, live Keychain, provider runtime proof, QA, production,
deployment, or release action is authorized by completion of this planning
ticket.
