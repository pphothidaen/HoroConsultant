# Restart Handoff — Delegate/Spark Governance

## Current Owner Scope Override — 2026-08-27

- Owner decision:
  `อนุญาติตามแผนงาน ต้องการครอบคลุม native spawn_agent ทุกตัว งานต้องคง BLOCKED จนแพลตฟอร์มมี pre-spawn hook/receipt API`.
- DSG-009A is `BLOCKED — PLATFORM NATIVE PRE-SPAWN HOOK/RECEIPT API REQUIRED`.
  Its acceptance covers every collaboration-platform native `spawn_agent`
  call, not only repository PromptCommand/`subprocess.Popen`. Repository hooks
  and wrappers cannot prove host-platform interception, and fresh HITL cannot
  manufacture a missing host API, receipt, trust root or runtime evidence.
- Exact unblock evidence is a platform-supported pre-spawn enforcement API for
  every native spawn; a host-issued pre-child receipt binding session, ticket,
  attempt, owner, ownership, Rule 11, Rule 18 and authoritative snapshot
  revision; zero-child denial evidence; and an independently documented API
  and trust root.
- The earlier recommended repository-managed-only approval was superseded
  before any mutation and authorized no completed action. No frozen DSG-001T
  or DSG-009 source is reopened and no Stage-C source ownership is released.
- DSG-009B is `BLOCKED — 009A + TRUSTED PROVIDER TELEMETRY`. Its future
  single `agy1` read-only plan+sandbox attempt is dependency-blocked,
  `NOT DISPATCHED — no child ran`; `agy2` remains disabled. No provider/AGY,
  quota preflight, network, sync, deploy, commit, push or secret operation
  occurred.
- Status at this checkpoint: **DONE** read-only boundary map, governed
  deep-reasoning advice, scope grill, the three-file BSA reconciliation, and
  DSG-009's local fail-closed re-freeze. **TODO/BLOCKED** remains DSG-009A,
  DSG-009B and provider proof. DSG-009 is `DONE — LOCAL FAIL-CLOSED RE-FREEZE /
  QA + SECURITY PASS; RUNTIME NOT_PROVEN`; it releases no runtime authority.
- **Historical failed candidate (superseded)**: pre-remediation QA was
  `543/545` with two token failures, the rejected Approach C review recorded
  C/H/M/L `1/5/1/0`, and 5/11 then-current DSG-009 hashes drifted. Those values
  do not describe the current local re-freeze or authorize the rejected design.
- **Current local re-freeze evidence**: guard QA passed `552`; integrated safe
  mocked QA passed `823` (`552 + 271`, with four intentional local-child tests
  deselected); PromptCommand developer QA passed `275` plus focused adversarial
  `33`; named security regression passed `761` with C/H/M/L `0/0/0/0`;
  ecosystem sync/check is green; and the secret scan reported `1,967` files /
  `0` leaks. The historical Static `6c351ba` production record is not the
  current live target/version; fresh release verification remains pending.
- The scoped 32-ticket ledger has 21 outstanding. Project-wide, the
  deduplicated outstanding inventory is 106 (85 outside scope): 61 `BLOCKED`,
  13 `PENDING`, 12 `READY`, 6 `TODO`, 5 `IN_REVIEW`, 4 `DOING`, 2 `NEEDS_HITL`,
  and 3 conflict/unverified. All feature flags remain `false`; no local token
  can make AGY eligible, and every native `spawn_agent` remains owner-gated.
- The authoritative registry remains 18 unique DSG tickets and the combined
  DAG remains 33 edges (20 DSG plus 13 DRG), acyclic. All Stage-A hashes and
  QA/security evidence below remain unchanged.

### Current DSG-009 local re-freeze manifest (verified current bytes)

The exact 11-file Stage-A manifest is stable at these SHA-256 values.
`scripts/multiagent_prompt_command.py` is a final dependency outside the
11-file manifest. This evidence is local only: runtime/native interception,
trusted provider telemetry, actual dispatch, trusted clock, and natural exit
remain `NOT_PROVEN`.

| Current file | SHA-256 |
|---|---|
| `.agents/rules/11-orchestrator-subagent-delegation.md` | `d7ea9f79aea2ea3d8737a44329ef7eecd05e4166b78ca56af7a1fdf2b4f6b278` |
| `.agents/skills/orchestrator-delegation/SKILL.md` | `7521cf8fb254245ff9ad41ec451899130a30e43cd1586c1390d27e60e53a75cf` |
| `.agents/skills/orchestrator-delegation/evals/evals.json` | `7ad0aa7fee4b06d1609400d439e863d1dfd03df1470474d4a41361a5f3ba9faa` |
| `.agents/hooks/full_capacity_guard.py` | `352bb05f221b4c7feb36561bb307b482209aabc95e19e7539aca58c350f073f1` |
| `.agents/hooks/full_capacity_test_harness.py` | `1bd1475f319a5d4aeb4d1ff9c64b43ba0ce8031b445f39326d975bbedc169b40` |
| `.claude/hooks/full_capacity_guard.py` | `69345184490918d5076a8d501670ad246a31ae00af472fd97e95d67cc34a5a4f` |
| `project/tests/test_full_capacity_governance.py` | `7d10469b44266dc093105fc8640beb6ecf9d643a421046cb33238c4a0fc00321` |
| `.agents/config/full_capacity_guard.v2.json` | `d3f73601e539bcfe85e9096700c69be25a42ea8d27d6b2f4f02ab7eae9cb37a4` |
| `.agents/schemas/full-capacity-governance-v2.schema.json` | `90f0c18bec385f83d50fffeb69e136f1b6b21fca4c350bb62778695287dedde9` |
| `.agents/hooks.json` | `d744fc95bd1ea44b06e0f1b1c82b230a4216003c9b2bc1da2ab8d353988505cb` |
| `.claude/settings.json` | `735e43dbe0930a6688593edc44256a20b7de4dc39dc30f5c6b7ae9b484c9202a` |
| `scripts/multiagent_prompt_command.py` (final dependency) | `48b0aee8400ce59add3d4f0575ea8d6ba533be0b89f02e7cef476f10361735e1` |

## Snapshot

- Captured: `2026-08-26T11:38:24Z` / `2026-08-26 18:38:24 +07`
  (Asia/Bangkok).
- Branch: `main`.
- HEAD: `8071323ce05ff5e0ed1153110ec5940bf305ac9b`.
- This handoff contains no secrets or raw provider output.

## Emergency Shutdown Checkpoint — 2026-08-26T11:21:29Z

> Historical checkpoint only. The Final Safe-Exit Checkpoint below supersedes
> its status and proposed resume actions.

- The user requested an immediate stop for machine shutdown. All live delegates
  were interrupted cleanly: `deep_reasoning_arch`, `dsg001s_telemetry`, and the
  DSG-001S read-only QA baseline. `collaboration.list_agents` showed no running
  child after interruption; do not assume an old lane still owns files on
  restart.
- The DSG-007/007A/008 documentation reconciliation below is complete. The
  reviewed freezes, hashes, 11 unique ticket definitions, 13-edge acyclic DAG,
  focused regression, and scoped diff evidence remain valid.
- At this historical checkpoint, DSG-001S ownership was reserved but the
  developer was interrupted before any telemetry mutation. A read-only search
  found no
  `provider_parse_subreason`, `candidate_count`,
  `completed_item_shape`, `agent_message_text_shape`, or
  `multiple_structured_candidates` implementation in the owned dispatcher/test
  files. The then-proposed resume was to freshly reserve the same two-file
  ownership; that proposal is superseded. Do not treat the interrupted attempt
  as source freeze, QA, review, claim, or provider evidence.
- The user added a governed deep-reasoning requirement. A read-only
  `gpt-5.6-sol` / `ultra` architecture audit recommended refactoring the
  existing adaptive lane-level router instead of adding a static specialist
  role. Owner-confirmed scope: advisory/escalation only; use `max` initially
  for Severity blocker root-cause/options analysis and `ultra` for
  cross-system/multi-owner blockers or unresolved decision-maker deadlock.
  The lane never becomes implementation owner or decision maker and cannot
  approve HITL, bypass the DAG, sync, deploy, or infer execution proof from a
  static label. The audit was interrupted before its final report and made no
  file changes; finish the read-only grill/design before opening a mutation
  ticket.
- No sync, provider/Spark execution, new content-addressed claim, external
  action, commit, push, deploy, publish, or secret operation occurred after the
  reconciled checkpoint. `git diff --check` passed immediately before shutdown.

## Second Pause Checkpoint — 2026-08-26T11:24:35Z

> Historical checkpoint only. The Final Safe-Exit Checkpoint below supersedes
> its status and proposed resume actions.

- The user requested another immediate pause. The resumed
  `deep_reasoning_arch`, `dsg001s_telemetry`, and DSG-001S read-only QA lanes
  were interrupted; `collaboration.list_agents` confirmed all three are
  `interrupted` and no child remains running.
- At this historical checkpoint, unlike the earlier shutdown checkpoint,
  DSG-001S had a partial mutation
  in `scripts/multiagent_prompt_command.py`: the closed subreason names and
  saturated candidate-count plumbing are present. No matching occurrences were
  found yet in `tests/test_multiagent_prompt_command.py`, so this is explicitly
  **NOT SOURCE FROZEN**, not QA/review evidence, and not permission to build a
  claim or run a provider. The then-proposed resume was to inspect the partial
  diff, complete focused tests and validation, then freeze before review; it is
  superseded by the completed freeze recorded below.
- Partial checkpoint hashes (identifiers only): dispatcher
  `5cb89103ae019a7a77da3aa7eaf56369571e74dbd284feba16d2ada4a0723c75`;
  focused test file
  `9b22637202fd144104f59fd7242407c29f4dbd2ef143ca240a371da38c2dec3f`.
  `git diff --check` passed at pause time.
- The deep-reasoning architecture audit was interrupted again before its final
  report and made no governed source changes. The then-proposed resume was to
  finish its read-only finalization independently of DSG-001S ownership; that
  proposal is superseded by the DRG-001 architecture result below.
- No sync, Spark/provider execution, fresh claim, external action, commit,
  push, deploy, publish, or secret operation occurred in this resumed window.

### Pause Confirmation — 2026-08-26T11:26:10Z

- One DSG-001S editor turn was briefly resumed, then immediately interrupted at
  the user's request. Dispatcher and focused-test hashes remained exactly
  `5cb89103ae019a7a77da3aa7eaf56369571e74dbd284feba16d2ada4a0723c75`
  and `9b22637202fd144104f59fd7242407c29f4dbd2ef143ca240a371da38c2dec3f`;
  no test telemetry cases were added and `git diff --check` still passed.
- `deep_reasoning_arch`, `dsg001s_telemetry`, and the read-only DSG-001S QA
  lane are all `interrupted`. This pause record was authoritative only before
  the final checkpoint and is superseded by the completed freeze below.

## Historical Safe-Exit Checkpoint — 2026-08-26T11:38:24Z (Superseded)

- DSG-001S is now `DONE — OFFLINE FREEZE / REVIEW PASS`; the earlier pause
  entries are superseded by the completed source/test, QA and review evidence.
  Dispatcher SHA256 is
  `5e0a07069899db68227f28cab902bad73c653580ffccb7e5e6043674d012c120` and
  focused-test SHA256 is
  `df53da50dd55b96b7b188b09434e239edef664703098dca950cee835208114f4`.
  Developer focused/owned/combined counts are `15`/`169`/`190`; final QA and
  independent review passed `190`, with exact semantics/privacy and synthetic
  matrix/privacy/invalid-count checks. The initial hash-movement QA attempt is
  superseded audit history only.
- DSG-001S live smoke remains `BLOCKED`: no fresh content-addressed claim,
  separate explicit one-shot authorization, valid live WorkResult or bound
  ExecutionReceipt exists. The next safe DSG action is to construct a fresh
  claim, then request authorization separately; this checkpoint authorizes
  neither action. DSG-003/004 remain blocked.
- DRG-001 is `DONE — ARCHITECTURE / NO FILE CHANGES`. The selected design
  refactors the adaptive lane-level router, reuses the orchestrator child, and
  adds a `deep-reasoning-advisory` skill/rule rather than a static agent role.
  The advisory is non-authoritative; `max` is for Severity blocker advice and
  `ultra` for cross-system/multi-owner blockers or prior-max decision deadlock.
  DRG-002 is `NEEDS_HITL` for owner lease confirmation (`600s` max,
  `900s` ultra, one attempt/no auto-retry); hard token/effective runtime
  telemetry is `NOT PROVEN`. DRG-003..008 remain blocked on DRG-002 and DSG-006;
  deep mutation is not `READY`.
- Safe exit: all child lanes are terminal/interrupted after this documentation
  lane; no provider/Spark execution, claim creation, sync, secret operation or
  external action occurred. The root must verify live agents and processes
  separately before any resume action.

## Current Ticket DAG and Status

```text
DSG-001 BLOCKED
  -> DSG-001R NEEDS_HITL (immutable one-shot consumed)
     -> DSG-001S DONE — OFFLINE FREEZE / REVIEW PASS
        -> DSG-001T DONE — LOCAL SOURCE FROZEN / U PASS
           -> DSG-001U DONE — LOCAL QA + REVIEW PASS
              -> DSG-001V BLOCKED — FUTURE HITL / EXACT CLAIM + GRANT
                 -> DSG-001W BLOCKED — ATOMIC ONE-SHOT PROBE / VERIFY
                    -> DSG-004 BLOCKED
                    -> DSG-003 BLOCKED

DSG-002 DONE — SOURCE FROZEN (historical baseline)
  -> DSG-007 DONE — SOURCE FROZEN / REVIEW PASS
     -> DSG-007A DONE — SOURCE FROZEN / REVIEW PASS
        -> DSG-008 DONE — SOURCE FROZEN / REVIEW PASS
           -> DSG-009 DONE — LOCAL FAIL-CLOSED RE-FREEZE / QA + SECURITY PASS;
              RUNTIME NOT_PROVEN (the 5/11 drift and prior freeze are
              superseded historical failed-candidate evidence)
              -> DSG-009A BLOCKED — AUTHORITATIVE SCHEDULER / NATIVE PRE-SPAWN
                 -> DSG-003 BLOCKED
                 -> DSG-009B BLOCKED — TRUSTED VERIFIER / POSITIVE AGY + HITL

DSG-003 + DSG-004
  -> DSG-005 BLOCKED — SOURCE FREEZE
     -> DSG-006 BLOCKED — QA
```

- `DSG-003` requires only DSG-001W's valid WorkResult, Receipt-v3 and consume
  receipt, plus existing frozen DSG-002 and reviewed DSG-009A predecessors. The historic
  direct `DSG-001S -> DSG-003` edge is superseded and cannot release it.
- `DSG-004` requires only DSG-001W's valid WorkResult, Receipt-v3 and consume
  receipt plus DSG-002. The historic direct `DSG-001S -> DSG-004` edge is
  superseded and cannot release it.
- `DSG-008` required the reviewed DSG-007 source and DSG-007A eval remediation;
  both are now frozen.
- `DSG-009` follows DSG-008 and is isolated from frozen DSG-001T/U. Its first
  Stage A candidate passed `288` local tests/static checks but failed independent
  QA `0/1/1/0` and security `0/1/3/1`; a later candidate closed M1-M3 and
  passed QA `0/0/0/1` with `446` plus targeted/static checks green, but
  integrated security failed `0/1/0/1` on a pathless benign-shell envelope
  bypass. A superseding candidate passed functional QA `0/0/0/1` with focused
  `382`, adjacent `248`, combined `630`, but integrated security again failed
  `0/1/0/1` on case-sensitive execution-family matching, contradictory
  top-level/native tool/input/response representations, and non-universal
  Claude Pre/Post matching. The final frozen candidate then closed H1;
  independent QA and security both pass `0/0/0/1`, with QA focused `540`,
  adjacent `248`, combined `788`, H1 adversarial `163`, and M1-M3 subset `21`,
  plus security focused `540`. Positive AGY/provider and
  actual dispatch are disabled. The release chain is
  `DSG-008 -> DSG-009 -> DSG-009A -> DSG-003`; `DSG-009A -> DSG-009B` gates
  the separate trusted-verifier/positive-AGY path. None blocks T/U/V/W. Its normative
  short-fallback lease is integer `1..600s` inclusive, and each positive AGY
  decision requires separately proven current alias-specific role/config
  binding evidence.
- Keep DSG-003, DSG-004, DSG-005 and DSG-006 blocked until their listed
  dependencies are evidenced; do not bypass the DAG.

DRG-001 DONE — ARCHITECTURE / NO FILE CHANGES
  -> DRG-002 DONE — POLICY RECORDED; RUNTIME NOT_PROVEN
     -> DRG-003..008 BLOCKED — DRG-002 + DSG-006

Documented combined DAG edge inventory (33, acyclic): DSG edges are `001 ->
001R`, `001R -> 001S`, `001S -> 001T`, `001T -> 001U`, `001U -> 001V`,
`001V -> 001W`, `001W -> 003`, `001W -> 004`, `002 -> 003`, `002 -> 004`,
`002 -> 007`, `003 -> 005`, `004 -> 005`, `005 -> 006`, `007 -> 007A`,
`007A -> 008`, `008 -> 009`, `009 -> 009A`, `009A -> 003`, and
`009A -> 009B`; DRG edges are
`DRG-001 -> DRG-002`,
`DRG-002 -> DRG-003`, `DRG-002 -> DRG-004`, `DRG-002 -> DRG-005`,
`DRG-002 -> DRG-006`, `DRG-002 -> DRG-007`, `DRG-002 -> DRG-008`,
`DSG-006 -> DRG-003`, `DSG-006 -> DRG-004`, `DSG-006 -> DRG-005`,
`DSG-006 -> DRG-006`, `DSG-006 -> DRG-007`, and `DSG-006 -> DRG-008`.

## Ownership and Lane Checkpoints

- `full_capacity_governance` owned DSG-007 edits only in:
  `.agents/rules/11-orchestrator-subagent-delegation.md`,
  `.agents/skills/orchestrator-delegation/SKILL.md`, and
  `.agents/skills/orchestrator-delegation/evals/evals.json`. Edits flushed the
  full-capacity invariant, refill loop, useful dependency-blocked fallback work,
  and typed capacity exception. The final independent review passed
  with zero Critical/High/Medium/Low findings at the Rule 11 and skill hashes
  recorded below. DSG-007A records the reviewed eval remediation: `15`
  contiguous cases, final eval hash `be2264545016ea67875fd5ef075c67b64d8ef6ab30958fda56d5b2bf02d06c70`,
  JSON and scoped diff checks passed. The former eval claim
  `18420f0306702ff74c03ea06a3f5e31dc04a01d833647d8ea16705ff95d4420b` was
  unsupported and is superseded. No sync ran.
- DSG-008 is a separate developer hook lane now at a reviewed frozen `DONE`
  checkpoint. Its exact dirty set is modified `.agents/hooks.json` and
  `.claude/settings.json`, plus untracked
  `.agents/hooks/full_capacity_guard.py`,
  `.claude/hooks/full_capacity_guard.py`, and
  `project/tests/test_full_capacity_governance.py`. The frozen hashes and
  evidence are recorded in the DSG-008 section below: developer focused `13`
  passed, adjacent `36` passed, final QA `28` passed, independent review PASS
  with zero Critical/High/Medium/Low findings, and H1-H4 closed. No live
  Claude/provider execution or sync was performed. It must not edit the DSG-007
  Rule 11/skill/evals sources.
- DSG-009 is the current Stage A structural governance/hook/test lane. This BSA
  editor owns only `PROJECT_TASKS.md`, `plans/plan.md`, this handoff, Rule 11,
  and the orchestrator skill/evals. Its disjoint developer owns only the two
  full-capacity hooks, the local full-capacity test harness, hook/config
  registration including
  `.agents/config/full_capacity_guard.v2.json`,
  `.agents/schemas/full-capacity-governance-v2.schema.json`,
  and the focused full-capacity governance test; QA/review are read-only. These reservations do not overlap
  the frozen DSG-001T dispatcher, receipt tests, model-policy, runtime-v3 or T/U schemas.
  DSG-009 retains the DSG-008 hashes as predecessor evidence. Its first Stage A
  candidate manifest is failed historical evidence; reopened remediation must
  record new superseding hashes without rewriting DSG-008 or failed-freeze history.
- DSG-001S implementation is now source/test frozen with QA and independent
  review PASS. This historical claim-first wording is superseded by the current
  T/U/V/W chain; DSG-001S owns no live claim or authorization.
- The final `business_analyst` reconciliation owns these three documents plus
  Rule 11 and the orchestrator skill/evals in this checkpoint. Preserve all
  unrelated content and user edits outside the Delegate/Spark sections.
- The board and plan are the status authorities. This handoff records their
  current reviewed DSG-001S/DSG-007/007A/008 freeze, locally signed-off
  DSG-001T/U, active DSG-009 Stage A, blocked 009A/009B, and later V/W claim
  gates; later evidence must
  update all three documents together.
- The implementation, documentation and reviewer collaboration lanes reached
  their terminal reporting checkpoints. This is not a live-process guarantee;
  the final root must verify current agents and processes after this handoff is
  finalized.

## Immutable Spark Attempt

- DSG-001R consumed exactly one authorized bundle claim:
  `5cfdce4b12a79b77afb967f4e71e83f0ebf9c0845653d6ff8c2a804ee8f1438b`.
- Artifact `smoke-result.json` SHA256:
  `3ccf0ab371f68961925dc1505524f8157d9de0f5133b7179ff9bda62c09794a5`.
- Requested invocation: exact `gpt-5.3-codex-spark`, requested effort `high`,
  read-only sandbox and ephemeral execution.
- Child exit was `0`; dispatcher exit was `3`; provider parse reason was
  `final_message_cardinality`.
- No normalized WorkResult or ExecutionReceipt was produced. Effective model,
  effort, account and quota are all `NOT PROVEN`; requested argv is not
  effective-execution proof.
- DSG-001R is terminal `NEEDS_HITL`, not `DONE`. Never retry it, substitute a
  model, start a second process, reuse its claim, or reuse/overwrite its artifact
  bundle.
- DSG-001S completed offline diagnosis and freeze: the old artifacts were
  extended with content-free `completed_item_shape`, `agent_message_text_shape`,
  and `multiple_structured_candidates` subreasons plus saturated
  `candidate_count` (`0`, `1`, `2`, where `2` means two or more). Do not select
  the last candidate or ignore duplicates. Live execution remains separately
  gated.

## DSG-001S Offline Freeze and Live Probe Gate

- Dispatcher SHA256:
  `5e0a07069899db68227f28cab902bad73c653580ffccb7e5e6043674d012c120`.
  Focused-test SHA256:
  `df53da50dd55b96b7b188b09434e239edef664703098dca950cee835208114f4`.
- Developer focused/owned/combined counts are `15`/`169`/`190`; pycompile and
  scoped diff checks passed. Final QA passed `190` plus synthetic
  matrix/privacy/invalid-count checks. Independent review passed `190` with
  zero Critical/High findings and exact semantics/privacy checks.
- An initial QA attempt invalidated only because hashes moved during the lane;
  it is superseded audit history. The source/test freeze is
  `DONE — OFFLINE FREEZE / REVIEW PASS`, but the live smoke remains `BLOCKED`:
  no fresh content-addressed claim, separate explicit one-shot authorization,
  valid live WorkResult or bound ExecutionReceipt exists. DSG-003 and DSG-004
  are not released.

## Source Freeze Hashes

The following are immutable historical DSG-002 predecessor hashes. Current
DSG-007 edits intentionally supersede them in the working tree; do not claim
they are current hashes.

| Source | Historical DSG-002 SHA256 |
|---|---|
| `.agents/rules/11-orchestrator-subagent-delegation.md` | `55a839c0699c0980435cbf2a58357e3752037faed5d4d4fcc11ee3d058cca60b` |
| `.agents/skills/orchestrator-delegation/SKILL.md` | `0f6e5e439aacac820cd510eeaa8d8be7f37ac8bc45311da4d0c3700a1e158917` |
| `.agents/skills/orchestrator-delegation/evals/evals.json` | `79e54af6f37d2a707d305cb94617869a1647454ddb396d53925adafbc077fb41` |

Current DSG-007/007A hashes, which intentionally supersede the historical
DSG-002 working-tree content without rewriting its evidence, are:

| Source | Current DSG-007/007A SHA256 |
|---|---|
| `.agents/rules/11-orchestrator-subagent-delegation.md` | `50bf92ab82ef0108e8c5081ce2d6d465aba55b26227323facaa56c53939c51b5` |
| `.agents/skills/orchestrator-delegation/SKILL.md` | `daa95fef8746f29916e6ef265b8dcf2e440e5adbfcb0f7c477027894c5e9e5dd` |
| `.agents/skills/orchestrator-delegation/evals/evals.json` | `be2264545016ea67875fd5ef075c67b64d8ef6ab30958fda56d5b2bf02d06c70` |

DSG-007 and DSG-007A independent review passed with zero
Critical/High/Medium/Low findings at the Rule 11, skill and final eval hashes
above. The former `18420f0306702ff74c03ea06a3f5e31dc04a01d833647d8ea16705ff95d4420b`
claim was unsupported and is superseded.

## DSG-008 Source Freeze and Review

The reviewed full content hashes are:

| File | SHA256 |
|---|---|
| `.agents/hooks/full_capacity_guard.py` | `b84c1ad54368890d595c78e192700fa28eecb14a6a75cdf2acc4f401e75466a2` |
| `.claude/hooks/full_capacity_guard.py` | `94c62fd171f60eb68ca4ca74930a9c7f6c24938168c5f427eea8d4423c0d8e28` |
| `.agents/hooks.json` | `36f94a13a5d133ab5e737757ee04a1cdf951f3c9109a2f587a54a6b291efd460` |
| `.claude/settings.json` | `ad877b9aeefc897e7b43d3b6c2d00c28203933680d2ead7bb8bb1f48afde9ec2` |
| `project/tests/test_full_capacity_governance.py` | `9bd6c5d0b9eb3af6f0c97af8949d17ae2f81c1da759b05823169439bbb6c648b` |

DSG-008 is `DONE — SOURCE FROZEN / REVIEW PASS`: developer focused tests passed
`13`, the adjacent suite passed `36`, and final QA passed `28`. Independent
review passed with zero Critical/High/Medium/Low findings; all H1-H4 findings,
including Claude PostToolUse/native Task envelopes and fail-closed malformed or
read/import errors, are closed. No live Claude/provider execution and no sync
were performed. These hashes are freeze evidence, not provider or account
identity proof.

## Dirty Working Tree at Handoff

Modified:

- `.agents/config/multiagent_model_policy.yaml`
- `.agents/hooks.json`
- `.agents/rules/11-orchestrator-subagent-delegation.md`
- `.agents/skills/orchestrator-delegation/SKILL.md`
- `.agents/skills/orchestrator-delegation/evals/evals.json`
- `.claude/settings.json`
- `PROJECT_TASKS.md`
- `plans/plan.md`
- `project/data/bazi_bazi_manual_chatml.jsonl` (unrelated pre-existing user work)
- `project/data/distillation_checklist.json` (unrelated pre-existing user work)
- `project/data/vault_sync_status.json` (unrelated pre-existing user work)
- `scripts/multiagent_prompt_command.py`
- `tests/test_multiagent_prompt_command.py`
- `tests/test_multiagent_prompt_command_r4.py`
- `tests/test_multiagent_receipt_schema.py`

Untracked:

- `.agents/config/full_capacity_guard.v2.json`
- `.agents/config/multiagent_prompt_command.runtime-readonly-v3.yaml`
- `.agents/hooks/full_capacity_guard.py`
- `.agents/schemas/multiagent-approval-consume-receipt-v1.schema.json`
- `.agents/schemas/multiagent-dispatch-receipt-v3.schema.json`
- `.agents/schemas/multiagent-probe-approval-v1.schema.json`
- `.agents/schemas/multiagent-probe-claim-v1.schema.json`
- `.claude/hooks/full_capacity_guard.py`
- `plans/RESTART_HANDOFF.md`
- `project/tests/artifacts/delegate_spark_governance/5cfdce4b12a79b77afb967f4e71e83f0ebf9c0845653d6ff8c2a804ee8f1438b/decision.json`
- `project/tests/artifacts/delegate_spark_governance/5cfdce4b12a79b77afb967f4e71e83f0ebf9c0845653d6ff8c2a804ee8f1438b/policy.yaml`
- `project/tests/artifacts/delegate_spark_governance/5cfdce4b12a79b77afb967f4e71e83f0ebf9c0845653d6ff8c2a804ee8f1438b/probe-claim.json`
- `project/tests/artifacts/delegate_spark_governance/5cfdce4b12a79b77afb967f4e71e83f0ebf9c0845653d6ff8c2a804ee8f1438b/runtime.yaml`
- `project/tests/artifacts/delegate_spark_governance/5cfdce4b12a79b77afb967f4e71e83f0ebf9c0845653d6ff8c2a804ee8f1438b/smoke-result.json`
- `project/tests/artifacts/delegate_spark_governance/5cfdce4b12a79b77afb967f4e71e83f0ebf9c0845653d6ff8c2a804ee8f1438b/snapshot.json`
- `project/tests/test_full_capacity_governance.py`
- `tests/test_multiagent_probe_approval.py`

These changes belong to multiple lanes. Preserve them, inspect scoped diffs and
never revert or overwrite another lane's work.

## Validation Evidence

- QA baseline: scheduler `56 passed`; dispatcher plus R4 `173 passed`; receipt
  `3 passed`.
- Claude plus ecosystem baseline: `15 passed`, with `1` expected sync mismatch.
  This is not a clean sync claim and does not authorize sync.
- Tracked digest at that baseline:
  `e09ed981ca6fda2e096310aef32b37ef1cd6e4f0a6ca7c17ad475ee1f034c1bd`.
- No provider or sync action was part of that baseline.
- DSG-007 JSON and scoped diff checks passed; DSG-007 and DSG-007A
  independent review passed with zero Critical/High/Medium/Low findings at the
  exact hashes recorded above.
- DSG-008 developer focused tests passed `13`, the adjacent suite passed `36`,
  and final QA passed `28`; pycompile, JSON and diff-check passed. Independent
  review passed with zero Critical/High/Medium/Low findings and all H1-H4 are
  closed. No live Claude/provider execution or sync occurred.
- DSG-001S offline freeze evidence: dispatcher/test hashes are recorded in the
  DSG-001S section above; developer focused/owned/combined counts are
  `15`/`169`/`190`, final QA passed `190` plus synthetic matrix/privacy/
  invalid-count checks, and independent review passed `190` with zero
  Critical/High findings and exact semantics/privacy. No fresh claim,
  authorization, live WorkResult or bound ExecutionReceipt exists.
- DSG-001T/U local-only freeze evidence is the 11-file manifest below.
  Developer focused `53` and combined `240` passed; the broad run reported
  `1382 passed`, `2` known sync-drift failures and `1 deselected`. Independent
  QA passed focused `53`, combined `240`, adversarial `38`; independent review
  passed its two-file command with `53`. Both reported stable hashes and
  C/H/M/L `0/0/0/0`. This does not release V/W/provider/AGY.
- DSG-009 initial candidate freeze failed: QA C/H/M/L `0/3/0/0`, security
  C/H/M/L `0/6/1/0`. The first Stage A source candidate then passed `288` tests
  and static checks but independent QA failed `0/1/1/0` and security failed
  `0/1/3/1`; it was reopened for bounded H1/M1-M3 remediation. A later
  functional candidate closed M1-M3 and passed QA `0/0/0/1` with `446` plus
  targeted/static checks green, but integrated security failed `0/1/0/1` on a
  pathless benign-shell envelope bypass. A superseding normalized-event
  candidate passed independent functional QA `0/0/0/1` with `382` focused,
  `248` adjacent and `630` combined, but integrated security failed `0/1/0/1`
  on case-sensitive execution-family names, conflicting top-level/native
  tool/input/response precedence and non-universal Claude Pre/Post matching.
  At that failed checkpoint DSG-009 remained `DOING` H1-only; the final freeze
  below supersedes it. The
  `gpt-5.6-sol/ultra` request/effective-runtime distinction and Stage A/B/C/D
  decision are recorded in the current checkpoint below. No positive dispatch
  is enabled.
- Documentation scoped `git diff --check` passed for `PROJECT_TASKS.md`,
  `plans/plan.md` and this handoff before DSG-009 was opened. The current board
  must have exactly one detailed heading and one sprint-table definition for
  each of the 18 DSG tickets (including DSG-007A, DSG-009, DSG-009A and
  DSG-009B). The separate DRG
  block has one definition for DRG-001..008. The current authoritative graph
  has 33 dependency edges and must remain acyclic.

## Ordered Resume Actions

1. Read this handoff, `PROJECT_TASKS.md` and the delegate/Spark section of
   `plans/plan.md`; inspect `git status --short` and scoped diffs without
   reverting any change.
2. Confirm the recorded DSG-001S/DSG-007/007A/008 freeze evidence and exact
   hashes; do not reopen reviewed sources without a new governed ticket.
3. Construct a fresh content-addressed DSG-001S probe claim. This does not
   authorize execution.
4. After the claim is independently inspected, request separate explicit
   one-shot authorization; do not infer authorization from this handoff.
5. Only after authorization, run exactly one read-only/ephemeral requested
   Spark/high smoke and require a valid live WorkResult and bound receipt.
6. Release DSG-003/004, then DSG-005/006, only as their exact predecessor
   evidence becomes valid. Do not run sync before those gates and the dedicated
   sync/review ticket are complete.
7. Resolve DRG-002 owner lease HITL (`600s` max/`900s` ultra, one attempt/no
   auto-retry) only after owner sign-off; keep DRG-003..008 blocked and deep
   mutation not READY until DSG-006 and DRG-002 close.

## Safe Restart Commands and Prohibitions

Safe read-only starting commands:

```bash
git status --short
git diff -- PROJECT_TASKS.md plans/plan.md plans/RESTART_HANDOFF.md
git diff -- .agents/rules/11-orchestrator-subagent-delegation.md .agents/skills/orchestrator-delegation/SKILL.md .agents/skills/orchestrator-delegation/evals/evals.json
git diff -- .agents/hooks.json .claude/settings.json
git diff -- scripts/multiagent_prompt_command.py tests/test_multiagent_prompt_command.py tests/test_multiagent_prompt_command_r4.py tests/test_multiagent_receipt_schema.py
git diff --check
```

Do not, on restart:

- reuse the exhausted DSG-001R claim or artifact bundle;
- restart, duplicate or overwrite the existing DSG-008 atomic edits;
- run a provider/Spark smoke without the confirmed DSG-001S offline
  freeze/review, a fresh content-addressed claim and separate one-shot
  authorization;
- run `python3 scripts/sync_ai_agent_ecosystem.py --sync`;
- edit generated `.codex/agents/*.toml` files manually;
- kill unknown sessions or processes; inspect and resolve ownership first;
- claim effective model, effort, account or quota from requested argv; or
- commit, push, deploy, publish, rewrite history or perform external actions
  without their separate gates and authorization.

## Historical Safe-Exit Checkpoint — 2026-08-26T11:58:04Z (Superseded)

> This checkpoint supersedes the preceding ordered instruction to construct a
> fresh DSG-001S claim. It is a safe-exit record only; it authorizes no claim,
> provider, alias, Spark, sync, external action, or status release.

- All child lanes are terminal or interrupted. The `gpt-5.6-sol` / `max`
  advisory lane was explicitly interrupted for shutdown before a final result;
  it made no file changes. Therefore no advisory conclusion or effective
  runtime proof exists.
- DSG-001S remains at its reviewed offline freeze: dispatcher SHA256
  `5e0a07069899db68227f28cab902bad73c653580ffccb7e5e6043674d012c120`,
  focused-test SHA256
  `df53da50dd55b96b7b188b09434e239edef664703098dca950cee835208114f4`,
  and final offline QA `190` passed. This record neither alters those hashes
  nor changes DSG-001R's immutable one-shot history.
- Independent review found a High pre-execution blocker: no `ProbeClaim` or
  approval schema, validator, CLI surface, or spawn-boundary atomic consume is
  implemented. The runtime `DispatchClaim` is a 30-second execution ledger,
  not a preauthorization artifact. Consequently the historical sequence
  "construct, inspect, then separately approve a claim" cannot be safely
  performed or enforced yet.
- No fresh claim, claim artifact, authorization, provider/Spark/alias action,
  sync, or other external action occurred in this window. Effective runtime,
  model, effort, account, and quota remain `NOT PROVEN`.
- The read-only proposed three-ticket subchain is historical and superseded by
  the current `DSG-001S -> 001T -> 001U -> 001V -> 001W -> 003/004` chain.
  Historic direct `001S -> 003/004` edges are replaced rather than preserved.
- MAREF remains design-only and is not implemented. Its existing documentation
  inconsistency remains a noted reconciliation item, not implementation or
  execution evidence.

### Superseding Resume Order

1. Re-run or finish the governed `max` advisory and retain its result only if
   it completes under its own gates.
2. Obtain owner decisions for the proposed DSG-001T/001U/001V contract,
   ownership, QA, and one-shot approval boundaries; then reconcile the board,
   plan, and handoff together.
3. Do **not** construct a claim or run any provider until the pre-execution
   enforcement source work, independent QA, and owner approval gates have all
   passed.

## Historical Safe-Exit Checkpoint — 2026-08-26T12:01:20Z (Superseded)

> This checkpoint supersedes prior resume state and records the user's explicit
> request to exit this session. It authorizes no claim, artifact, authorization,
> provider, Spark, alias, sync, external action, or source mutation.

- The three newly resumed lanes—`gpt-5.6-sol`/`max` advisory, read-only
  enforcement-seam design, and read-only QA matrix—were interrupted before
  final results and made no authorized changes.
- No claim/artifact/authorization/provider/Spark/alias/sync/external action or
  source mutation occurred. The prior High blocker and proposed-not-approved
  `DSG-001T`/`DSG-001U`/`DSG-001V` subchain remain authoritative.
- Next resume begins by re-reading the previous checkpoint and restarting the
  `max` advisory only if the owner/session permits. Dispatch ranks are
  `1/1/1/0/1`; floor/selected is `luna medium`; runtime proof is
  `NOT_PROVEN`; documentation only.

## Authoritative Pre-Execution Governance Supersession — 2026-08-26T14:53:14Z

> This owner session-scoped sign-off supersedes every earlier non-historical
> instruction to construct a fresh claim. It authorizes documentation and the
> local DSG-001T/001U implementation-and-QA path only; it expires at session
> end and does not authorize a future exact claim, approval, consume, provider,
> Spark, alias, sync, commit, push, deploy, secrets, or external action.

- `DSG-001T` is `DONE — LOCAL SOURCE FROZEN / U PASS` for central,
  fail-closed `ProbeClaim v1`, `ProbeApproval`/`ApprovalGrant v1`,
  `ApprovalConsumeReceipt v1`, and `ExecutionReceipt v3` implementation.
  `DSG-001U` is `DONE — LOCAL QA + REVIEW PASS`; `DSG-001V` remains a future HITL
  gate for an exact late-bound claim and grant; `DSG-001W` remains blocked on V
  plus distinct exact authorization. Only W can atomically consume once, run
  one probe, and release DSG-003/004.
- Local single-host attestation is the selected approval trust model. It is
  explicitly nonportable and non-cryptographic human-authenticity proof; it is
  not an asymmetric signature or portable identity assertion. Claim TTL is
  `10m`; grant TTL is `2m`; zero grace, current-session binding and
  `max_uses=1` apply. Deterministic preflight precedes an fsynced consume
  immediately before spawn; a post-consume failure burns the one-shot with no
  retry. Content-free metadata remains `90d`, then may be explicitly compacted
  to an indefinite anti-replay tombstone. Raw provider streams are never kept.
- Receipt-v3 is mandatory for a new probe and binds the claim, grant and consume
  receipt. v1/v2 are frozen historical contracts and cannot authorize or prove
  a new probe. MAREF is a design reference only.
- The authoritative 33-edge DAG replaces (rather than preserves) historic
  direct `001S -> 003`, `001S -> 004`, and `008 -> 003` release edges: DSG has
  20 edges,
  `001 -> 001R -> 001S -> 001T -> 001U -> 001V -> 001W`, then
  `001W -> 003/004`, and
  `002 -> 007 -> 007A -> 008 -> 009 -> 009A -> 003`, plus `009A -> 009B`,
  with all other original DSG edges preserved; DRG retains 13 edges. The graph
  is acyclic only if the superseded direct release edges are absent.
- DRG-002 is `DONE — POLICY RECORDED; RUNTIME NOT_PROVEN`: `max` lease `600s`,
  `ultra` lease `900s`, one attempt and no auto-retry. DRG-003..008 remain
  blocked on DRG-002 and DSG-006. This is policy only, never provider/runtime proof.
- D1-D9 local implementation grill is resolved: scope is T/U contract and QA;
  out of scope are all live/external actions; acceptance is zero Critical/High
  findings plus full fail-closed negative matrix at frozen hashes; one developer
  owns the exact T source/test/schema/config surface and U/review are read-only;
  trust/TTL/retention/v3/one-editor decisions are confirmed. The exact future
  V/W claim/grant/consume/probe remains `PENDING-OWNER` HITL.
- Active documentation/review routing ranks are `2/2/2/1/2`; floor/selected is
  `gpt-5.6-terra/high`. This is not a DSG-001T execution rank record. Effective
  runtime and root-medium execution proof remain `NOT_PROVEN`.

## DSG-001T/U Local Freeze and Sign-Off

The authoritative stable 11-file SHA256 manifest is:

| T/U local source | SHA256 |
|---|---|
| `scripts/multiagent_prompt_command.py` | `4416d09cb64065302d4dc9a76b9af3d462a9b2baa00a4b0c251580f27b23ebf4` |
| `tests/test_multiagent_prompt_command.py` | `35b263dffe1dd9b14370499b17a40747fc488c34c36b5bf7b8b19ae379390c94` |
| `tests/test_multiagent_prompt_command_r4.py` | `235c1c63e0647727857d156b8ad5e90c469cc2c904b92d98d52d35750c16794f` |
| `tests/test_multiagent_receipt_schema.py` | `8eaf5195188bc37799dbb83503906ddd55cc65651945f144a73333cffdb7a343` |
| `tests/test_multiagent_probe_approval.py` | `f4988fedbbdbc1d3e0654cec21669e27cff8b38006e27b9ca81ae967e7944e45` |
| `.agents/config/multiagent_model_policy.yaml` | `66f54e411d90e21494665d20cdd86a6b79b04b543beef28190fa78a43e780a38` |
| `.agents/config/multiagent_prompt_command.runtime-readonly-v3.yaml` | `f4b848d6c0c511c4fa0c8b88b9254f4a31b023421413fde2b2136ae005551546` |
| `.agents/schemas/multiagent-probe-claim-v1.schema.json` | `612f179315ab808323aefdda2b2a57f8c9c9e06653794e92ae4c1da4a11e7b27` |
| `.agents/schemas/multiagent-probe-approval-v1.schema.json` | `99d5778cbd74ce61aa1683c2ea9262b27a7e4e7319d85d1dd93ceefb82e61012` |
| `.agents/schemas/multiagent-approval-consume-receipt-v1.schema.json` | `31ab1bd3958fc644251f2f64e0bc55bd8110726010e34c72b533da18f47d6416` |
| `.agents/schemas/multiagent-dispatch-receipt-v3.schema.json` | `12885e42c2ee6bb27a3583373ecfb85b38319e60e31eb3f5c1a763ae4d32d093` |

- Developer focused `53` and combined `240` passed. The broad run reported
  `1382 passed`, `2` known sync-drift failures and `1 deselected`; it is not a
  clean sync or release claim.
- Independent QA confirmed stable hashes, focused `53`, combined `240`, and
  adversarial `38`, C/H/M/L `0/0/0/0`. Independent review confirmed the same
  manifest and its two-file probe-approval/receipt-schema command passed `53`,
  C/H/M/L `0/0/0/0`.
- This is local-only T/U sign-off. It authorizes no V/W claim/grant/consume,
  provider, AGY, sync, deploy, external action, commit, push or secret.

## Current DSG-009 Short-Fallback and AGY Capacity Checkpoint — updated 2026-08-27

This checkpoint is the current capacity-governance instruction. It authorizes
only local DSG-009 documentation, governance/hook/test implementation and
read-only QA/review for Stage A/B in this session. Positive AGY/provider and
actual dispatch are disabled. It authorizes no provider call, alias
execution, sync, claim/probe, deployment, external action, commit, push or
secret operation.

- While a source editor runs and dependent QA waits for source freeze, every
  unused slot must scan for short fallback work. Eligible work is only
  `TODO`/`READY`, dependency-complete, ownership-disjoint from active source and
  docs editors, read-only, evidence-bearing, provider/quota independent unless
  separately authorized and currently proven, naturally terminating and
  non-preemptive. `lease_seconds` must be an integer `1..600` inclusive and no
  greater than the scan/config limit. A scan/config may set a stricter ceiling
  but must never raise or override the normative `600s` hard maximum; missing,
  non-integer or out-of-range leases are ineligible.
- When source freeze makes QA eligible, do not cancel a running fallback. It
  finishes within its bounded lease, the scheduler recomputes, and QA receives
  the first available or next released slot. No new fallback may starve QA.
- Every capacity scan considers `agy1` and `agy2` separately. Dispatch an
  eligible bounded lane only when that alias has a separately `PROVEN`, current,
  alias-specific role/config binding whose evidence binds runtime identity,
  account, provider, current quota, authorization, session, ticket, ownership,
  Rule 11 snapshot/decision, Rule 18 decision/policy digest and receipt
  contract. The resulting receipt/WorkResult must bind the same tuple before
  utilization is claimed. Static labels, config alone, rendered commands,
  historical evidence or Hermes topology never establish utilization.
- Missing, mismatched, stale or non-alias-specific role/config proof makes that
  alias `NOT_ELIGIBLE` and requires `no child ran`. For each unavailable,
  quota-blocked, conflict-blocked or no-eligible-ticket alias, record the exact
  per-lane reason too. Never force a provider call, silently substitute an
  alias, or invent a child result to keep a slot occupied.
- Current audit at `2026-08-26T15:13:44Z`: `agy1` and `agy2` were both
  considered, both are `NOT_ELIGIBLE` and `NOT DISPATCHED — no child ran`, and
  both lack separate current alias-specific role/config proof plus bound
  runtime/account/provider/quota/authorization/session/ticket/ownership/
  Rule 11/Rule 18/receipt evidence. The session also does not authorize
  AGY/provider execution. This is not a utilization success claim; reconsider
  both on every later scan; positive dispatch remains disabled until DSG-009B
  and fresh exact HITL are complete.
- Audit distinction: that durable AGY scan proves only its two alias
  rejections. No event-specific short-fallback candidate/rejection snapshot or
  `CAPACITY_EXCEPTION: NO_SAFE_USEFUL_LANE` receipt was found for the earlier
  interval when QA waited for source freeze and documentation review had
  ended. Do not infer that the required scan ran, that no safe candidate
  existed, or that a fallback executed. Any narrative claim about that episode
  is documentary only; current Rule 11/skill/evals prevent treating it as
  machine-proven. Stage A remains structural/manual, not native scheduler or
  historical world-state proof.
- Current refill attempt: an independent read-only audit lane was selected,
  but spawn was rejected by `CAPACITY_BLOCKED: AGENT_THREAD_LIMIT`. No child
  ran and no execution receipt exists; do not relabel this as
  `NO_SAFE_USEFUL_LANE`. Once source freezes, QA keeps first-idle/
  next-released-slot priority and no new fallback may precede it.
- Hooks validate supplied capacity/candidate/lease/QA-return/per-alias evidence
  and decision metadata. They are not a scheduler and cannot prove that a
  child or provider ran.
- If no candidate passes, record exactly
  `CAPACITY_EXCEPTION: NO_SAFE_USEFUL_LANE` with the capacity snapshot and
  rejected-candidate dependency, ownership, HITL and quota evidence, then
  replan. This exception is honest unused capacity, not a completion claim.
- Historical DSG-009 status was `DONE — STAGE A STRUCTURAL SOURCE FREEZE / QA +
  SECURITY PASS; RUNTIME NOT_PROVEN`; its later 5/11 drift and `543/545`
  pre-remediation baseline are superseded failed-candidate evidence. Current
  status is `DONE — LOCAL FAIL-CLOSED RE-FREEZE / QA + SECURITY PASS; RUNTIME
  NOT_PROVEN`, with the verified current manifest and final QA/security evidence
  at the top of this handoff. Its editor is disjoint from frozen DSG-001T/U. The
  current DAG is 33 edges: 20 DSG and 13 DRG;
  `008 -> 009 -> 009A -> 003` replaces the old direct release and
  `009A -> 009B` gates trusted positive AGY. These do not block T/U/V/W. Its hard lease ceiling is
  `1..600s`; stricter scan/config input is allowed but no input can raise 600.

### Initial Failed Candidate and Ultra Decision

- Candidate QA failed C/H/M/L `0/3/0/0`: Rule 11 priority bypass;
  contradictory `NOT_ELIGIBLE` reason acceptance; and unbound
  `provider_authorization.authorization_id`/evidence versus alias receipt.
- Security review failed C/H/M/L `0/6/1/0`: caller Rule 11/18 declarations were
  trusted; reasons were not reconciled; positive provider/AGY proof was
  self-attested/forgeable; replay and Pre/Post chaining were not durable/bound;
  snapshot completeness/omission was unverifiable; trusted stricter limit,
  start/deadline and exact unknown-control rejection were absent. M1 records
  structural hooks/native interception/provider-looking unenveloped events as
  `NOT_PROVEN`.
- The advisory requested `gpt-5.6-sol/ultra`, lease `<=900s`, one attempt and
  no retry. Effective model, effort, account, quota and receipt remain
  `NOT_PROVEN`. Its decision authorizes no execution.

### First Stage A Source Freeze — Failed Historical Candidate

The first Stage A source candidate passed `288` tests and its reported static
checks were green. These exact hashes bind that failed historical candidate
only; reopened remediation may move them and must publish a new manifest:

| First Stage A candidate source | Historical SHA256 |
|---|---|
| `.agents/rules/11-orchestrator-subagent-delegation.md` | `f686d2307cf508e784d109a5cf495bd84a855cbcd35101daae29012f2fb1ddd2` |
| `.agents/skills/orchestrator-delegation/SKILL.md` | `d1436443f0bbc0c5eddcd3b9de63c7fe71e9969031c435c1e7eee86b95f4eb2d` |
| `.agents/skills/orchestrator-delegation/evals/evals.json` | `e6d81218023ad0645a015bec85e06bbb284763db67ed452b403d74a27032af24` |
| `.agents/hooks/full_capacity_guard.py` | `e749f7a92a31393835db748490c8d25736cbcb3eff0bf122d40582f309116277` |
| `.claude/hooks/full_capacity_guard.py` | `69345184490918d5076a8d501670ad246a31ae00af472fd97e95d67cc34a5a4f` |
| `project/tests/test_full_capacity_governance.py` | `047da361fa813ded965a0f59bfdb809a1ae318fbcf5504b13348c2bb634392dc` |
| `.agents/config/full_capacity_guard.v2.json` | `28fea665b0c89093dba14d2515f669b1157ef3144faeecfaf30e4f7a7596f7da` |
| `.agents/schemas/full-capacity-governance-v2.schema.json` | `c1d8d09965234814df44234f96477ec3beb7a255b2a22d481e86826200c4743a` |
| `.agents/hooks.json` | `d744fc95bd1ea44b06e0f1b1c82b230a4216003c9b2bc1da2ab8d353988505cb` |
| `.claude/settings.json` | `ad877b9aeefc897e7b43d3b6c2d00c28203933680d2ead7bb8bb1f48afde9ec2` |

- Independent QA failed C/H/M/L `0/1/1/0`: H1 wrapper/envelope bypass and M1
  unbounded lifecycle ledger.
- Independent security review failed C/H/M/L `0/1/3/1`: H1 confirmed the
  conservative-envelope/wrapper bypass; M1 unbounded ledger growth; M2 a
  production environment state override; M3 unpinned transitive validation
  dependencies and missing exact schema-digest binding through a local
  registry; L1 monolithic-hook maintainability risk.
- `288 passed` and green static checks do not overrule those reviews. The
  manifest is not current-byte evidence, and DSG-009 is reopened `DOING` only
  for bounded H1/M1-M3 remediation. L1 remains a documented residual risk and
  does not authorize scope expansion or a freeze.

### Final Functional Candidate — Failed Integrated H1 Freeze

The subsequent functional candidate closed M1-M3. Functional QA passed
C/H/M/L `0/0/0/1`; `446` plus targeted checks passed and static checks were
green. Integrated freeze still failed security C/H/M/L `0/1/0/1`: H1 found a
pathless benign-shell allowlist that bypassed the closed governance envelope;
L1 retains the documented monolithic-hook maintainability risk. This exact
11-file manifest is failed, superseded historical evidence only and is not a
statement of current bytes:

| Failed H1 candidate source | Historical SHA256 |
|---|---|
| `.agents/rules/11-orchestrator-subagent-delegation.md` | `f686d2307cf508e784d109a5cf495bd84a855cbcd35101daae29012f2fb1ddd2` |
| `.agents/skills/orchestrator-delegation/SKILL.md` | `d1436443f0bbc0c5eddcd3b9de63c7fe71e9969031c435c1e7eee86b95f4eb2d` |
| `.agents/skills/orchestrator-delegation/evals/evals.json` | `e6d81218023ad0645a015bec85e06bbb284763db67ed452b403d74a27032af24` |
| `.agents/hooks/full_capacity_guard.py` | `42c9a217a4fd537699d9fd94093e89955d467c8b0ecff613a12cb3b848e6970f` |
| `.agents/hooks/full_capacity_test_harness.py` | `1bd1475f319a5d4aeb4d1ff9c64b43ba0ce8031b445f39326d975bbedc169b40` |
| `.claude/hooks/full_capacity_guard.py` | `69345184490918d5076a8d501670ad246a31ae00af472fd97e95d67cc34a5a4f` |
| `project/tests/test_full_capacity_governance.py` | `75b79e7bf882fa79394a3fa9ba2d8322cb67dfce54aed50fe2f5ae307c9eb970` |
| `.agents/config/full_capacity_guard.v2.json` | `1330f59e682597d3cf7c9096194b90911772b300f1c2ce63cf3993bb01e6fbda` |
| `.agents/schemas/full-capacity-governance-v2.schema.json` | `cd6abd3ce954a6ec4c88783956183e3337c2268e4611617c9cbb06b1393ac645` |
| `.agents/hooks.json` | `d744fc95bd1ea44b06e0f1b1c82b230a4216003c9b2bc1da2ab8d353988505cb` |
| `.claude/settings.json` | `ad877b9aeefc897e7b43d3b6c2d00c28203933680d2ead7bb8bb1f48afde9ec2` |

- M1 is closed by the `O(1)` bounded lifecycle ledger; M2 is closed by
  forbidding a production environment state override; M3 is closed by exact
  dependency/schema-digest binding through the local registry. These closures
  do not overrule H1 or the L1 residual.
- H1-only final acceptance requires the exact closed governance envelope for
  every `Pre` and `Post` event in `Bash`, `run_command`, `shell`, or any
  `terminal*` family. Pathless `pwd`, `echo`, `git status`, and absolute binary
  paths are governed too; no benign-command, path, command, or wrapper allowlist
  bypass exists. Only unrelated non-shell tools such as `Read`, `Grep`, and
  `Edit` may pass this capacity-envelope boundary, while normal gates still
  apply.
- A complete governed shell envelope still cannot authorize actual dispatch
  during Stage A. It must fail closed as `AUTHORITATIVE_SNAPSHOT_NOT_PROVEN`
  until DSG-009A proves the authoritative scheduler/native pre-spawn boundary.
  At that failed checkpoint DSG-009 was reopened `DOING` H1-only; no
  downstream, provider, or AGY gate was released.

### Normalized Event-Representation Candidate — Failed Integrated H1 Freeze

The next candidate closed the pathless-shell bypass and passed independent
functional QA C/H/M/L `0/0/0/1`: targeted H1 `327`, focused `382`, adjacent
`248`, and combined `630`. Integrated security nevertheless failed C/H/M/L
`0/1/0/1`: execution-family matching was case-sensitive; conflicting top-level
`tool_name`/`tool_input` versus native `toolCall.name`/`toolCall.args` and
top-level `tool_response` versus native `toolResult` could conceal execution;
and Claude did not register the guard universally under matcher `.*` in both
Pre and Post. L1 remains the accepted monolithic-hook maintenance residual.
This exact manifest is failed historical evidence only:

| Failed normalized-envelope candidate source | Historical SHA256 |
|---|---|
| `.agents/rules/11-orchestrator-subagent-delegation.md` | `3dac38065702af2f0c75e97be5bad3d61bd9c1e786942184e732cc1f66ee165d` |
| `.agents/skills/orchestrator-delegation/SKILL.md` | `d816d94e35dc4c250d455195504d5ec09adcabe9ac321384af82da80dee0dea2` |
| `.agents/skills/orchestrator-delegation/evals/evals.json` | `ea1c6209c5a254691a01fb0e7eb93f3a2bf2b44d4b673349b975f2a05a3cb6b6` |
| `.agents/hooks/full_capacity_guard.py` | `b93af9b9617d4553adaa4ad8c28868c9d36f9326057ec7bf453636e32d5b7d85` |
| `.agents/hooks/full_capacity_test_harness.py` | `1bd1475f319a5d4aeb4d1ff9c64b43ba0ce8031b445f39326d975bbedc169b40` |
| `.claude/hooks/full_capacity_guard.py` | `69345184490918d5076a8d501670ad246a31ae00af472fd97e95d67cc34a5a4f` |
| `project/tests/test_full_capacity_governance.py` | `251ca8c79888562f709eff42f1a6be83de2b1d8100b2f450070b80fbcbe6cee7` |
| `.agents/config/full_capacity_guard.v2.json` | `1330f59e682597d3cf7c9096194b90911772b300f1c2ce63cf3993bb01e6fbda` |
| `.agents/schemas/full-capacity-governance-v2.schema.json` | `cd6abd3ce954a6ec4c88783956183e3337c2268e4611617c9cbb06b1393ac645` |
| `.agents/hooks.json` | `d744fc95bd1ea44b06e0f1b1c82b230a4216003c9b2bc1da2ab8d353988505cb` |
| `.claude/settings.json` | `ad877b9aeefc897e7b43d3b6c2d00c28203933680d2ead7bb8bb1f48afde9ec2` |

Final narrow H1 acceptance normalizes `Task`, `Bash`, `run_command`, `shell`,
and `terminal*` case-insensitively; recognizes top-level and nested-only native
event forms; and requires exact canonical equivalence when both name/input or
response forms exist. Conflicts return `CAPACITY_TOOL_ENVELOPE_CONFLICT` and a
missing normalized execution envelope returns
`CAPACITY_PROVIDER_EVENT_ENVELOPE_REQUIRED`. Claude must register
`full_capacity_guard` exactly once under matcher `.*` in both `PreToolUse` and
`PostToolUse`, preserving other hooks. Governed execution remains blocked as
`AUTHORITATIVE_SNAPSHOT_NOT_PROVEN` until DSG-009A.

### Historical DSG-009 Stage A Structural Freeze / Stage B Review Pass

The prior DSG-009 status was `DONE — STAGE A STRUCTURAL SOURCE FREEZE / QA +
SECURITY PASS; RUNTIME NOT_PROVEN` at this exact historical manifest. Its later
5/11 drift and `543/545` pre-remediation baseline are superseded historical
failed-candidate evidence. Current DSG-009 is `DONE — LOCAL FAIL-CLOSED
RE-FREEZE / QA + SECURITY PASS; RUNTIME NOT_PROVEN`; consult the verified
current-byte manifest at the top of this handoff.

| Final Stage A frozen source | SHA256 |
|---|---|
| `.agents/rules/11-orchestrator-subagent-delegation.md` | `6e76f4ea1ea348b47397ba5b9996c55c60498f873726dcfd2b7933043f89d5b1` |
| `.agents/skills/orchestrator-delegation/SKILL.md` | `7521cf8fb254245ff9ad41ec451899130a30e43cd1586c1390d27e60e53a75cf` |
| `.agents/skills/orchestrator-delegation/evals/evals.json` | `7ad0aa7fee4b06d1609400d439e863d1dfd03df1470474d4a41361a5f3ba9faa` |
| `.agents/hooks/full_capacity_guard.py` | `496cb5096598f3fafe40a878fb0af4e9853ff8094471286a0d485ebacda668aa` |
| `.agents/hooks/full_capacity_test_harness.py` | `1bd1475f319a5d4aeb4d1ff9c64b43ba0ce8031b445f39326d975bbedc169b40` |
| `.claude/hooks/full_capacity_guard.py` | `69345184490918d5076a8d501670ad246a31ae00af472fd97e95d67cc34a5a4f` |
| `project/tests/test_full_capacity_governance.py` | `bc0a27701fda863b593e4b6fcdb35627605811468c4c2335d9d05897cbe7290c` |
| `.agents/config/full_capacity_guard.v2.json` | `1330f59e682597d3cf7c9096194b90911772b300f1c2ce63cf3993bb01e6fbda` |
| `.agents/schemas/full-capacity-governance-v2.schema.json` | `cd6abd3ce954a6ec4c88783956183e3337c2268e4611617c9cbb06b1393ac645` |
| `.agents/hooks.json` | `d744fc95bd1ea44b06e0f1b1c82b230a4216003c9b2bc1da2ab8d353988505cb` |
| `.claude/settings.json` | `735e43dbe0930a6688593edc44256a20b7de4dc39dc30f5c6b7ae9b484c9202a` |

- Independent QA PASS C/H/M/L `0/0/0/1`: focused `540`, adjacent `248`,
  combined `788`, H1 adversarial `163`, M1-M3 subset `21`; frozen hashes were
  stable.
- Independent security PASS C/H/M/L `0/0/0/1`: focused `540`; prior H1 closed.
  L1 is the accepted monolithic-hook maintenance residual only.
- Structural Stage A/B closure releases no runtime authority. Authoritative
  snapshot/native interception, provider runtime/provenance, actual dispatch,
  world state, trusted wall clock and natural-exit enforcement remain
  `NOT_PROVEN`; positive AGY/provider remains disabled. DSG-009A and DSG-009B
  remain `BLOCKED`.

### DSG-009 H1-Only Stage A/B and Blocked Stage C/D

- Stage A repairs deterministic Rule 11 priority and bound Rule 11/18 evidence,
  derived reason reconciliation, authorization/alias/receipt binding,
  owner-only SQLite lifecycle continuity, durable replay and Pre/Post chain,
  exact complete schemas, trusted start/deadline, exact unknown-control
  rejection, and governed envelopes. Effective config cap is `300s`, beneath
  the normative `600s` ceiling.
- M1-M3 are closed at the failed H1 candidates and remain closed absent new
  contrary evidence. Final Stage A acceptance is H1-only: every normalized
  execution-family `Pre`/`Post` event has the envelope; top-level/native forms
  cannot conflict; nested-only forms are recognized; and Claude registration
  is universal and unique in both phases. Runtime/native/provider execution and
  authoritative snapshot completeness remain `NOT_PROVEN` after structural
  validation.
- Stage B independent stable-hash QA/security review passed C/H/M/L
  `0/0/0/1`. The accepted L1 cannot authorize dispatch or claim native
  completeness.
- `TICKET-DSG-009A-AUTHORITATIVE-SCHEDULER-NATIVE-BOUNDARY` is `BLOCKED —
  PLATFORM NATIVE PRE-SPAWN HOOK/RECEIPT API REQUIRED`. Stage C covers every
  collaboration-platform native `spawn_agent` call. It requires the host API,
  a pre-child receipt bound to session/ticket/attempt/owner/ownership/Rule
  11/18/snapshot revision, zero-child denial evidence and an independently
  documented trust root. Repository wrappers cannot close this gate; no source
  ownership or external action is authorized.
- `TICKET-DSG-009B-TRUSTED-PROVIDER-VERIFIER-AGY` is `BLOCKED — 009A + TRUSTED
  PROVIDER TELEMETRY`. Stage D must replace self-attestation with a trusted alias-specific
  verifier and bind all role/config/runtime/account/provider/quota/
  authorization/session/ticket/ownership/Rule 11/18 evidence to the resulting
  receipt/WorkResult. The future `agy1` one-shot remains dependency-blocked and
  undispatched; `agy2` is disabled. Missing trusted effective telemetry remains
  `NOT_PROVEN` and cannot be waived into proof.

### Current Resume Order

1. Preserve the frozen DSG-009 manifest and its QA/security PASS. Do not treat
   structural closure as native interception, authoritative snapshot, provider,
   AGY, wall-clock or natural-exit proof; do not rerun or mutate the frozen
   lane without a new governed ticket.
2. Keep DSG-009A blocked until the platform exposes and independently documents
   the required native pre-spawn enforcement/receipt API and trust root. Do not
   reserve repository source ownership or reopen frozen T/009 evidence.
3. Keep DSG-009B and provider proof blocked until 009A passes and trusted
   effective telemetry exists. A later fresh sanitized quota gate may authorize
   only the recorded one-shot `agy1` attempt; `agy2` stays disabled. V/W,
   provider/Spark, sync, deploy, external, commit, push and secrets remain
   independently blocked.
