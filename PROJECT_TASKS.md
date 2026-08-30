<!-- CTX-HANDOFF-V1-20260830:START -->
## Cross-runtime context handoff v1 - local-only governance

**Recorded**: `2026-08-30` (Asia/Bangkok). **Gate**: `APPROVED` for
`CTX-000-GOV` planning/governance only. **Exact base**:
`b643d35243ad94949500c7627d46e27f580a020f`. **Isolated branch**:
`feat/context-handoff-v1-20260830`.

**Fresh owner scheduling adjustment**: test-first local implementation may
proceed now on this isolated branch for ASAP delivery. This adjustment makes
only `CTX-010-RED` ready; each descendant remains dependency-gated. It does
not relabel the current release, and release 120 remains blocked and not
production-green. Merge or cherry-pick into the current release, push, deploy,
publish, production activation, and any external mutation remain prohibited
until independent QA and review are green and `CTX-100-INTEGRATION-HOLD`
passes the existing release-120 and ownership-overlap integration gate.

### GRILL REPORT

- **Request**: freeze a complete local-only, test-first graph for one shared
  context handoff contract across Claude Code, Codex CLI, and AGY.
- **Status / authorized next phase**: `APPROVED`; after this docs-only commit,
  only `CTX-010-RED` is authorized to start.
- **D1 scope `[CONFIRMED]`**: this lane changes only `PROJECT_TASKS.md` and
  `plans/plan.md`. Follow-on local scope is exactly the ticket-owned paths
  below. Tests, source, config, hooks, skills, generated mirrors, `HANDOFF.md`,
  provider/network access, credentials, push, deploy, publish, merge, and
  production activation are out of scope for `CTX-000-GOV`.
- **D2 delta `[CONFIRMED]`**: the feature receives an isolated-branch
  scheduling exception for local test-first delivery; the current release and
  its production-green claim do not change.
- **D3 acceptance / stop `[CONFIRMED]`**: one commit with subject
  `docs(governance): plan cross-runtime context handoff` changes exactly the
  two governance files, passes staged-path and diff checks, and leaves the
  feature worktree clean. Stop on base drift, extra paths, ownership overlap,
  a failed check, or any attempt to cross the integration hold.
- **D4 inputs / dependencies `[CONFIRMED]`**: the exact base, owner adjustment,
  runtime set, ticket graph, test baseline paths, canonical source allowlist,
  later generated/docs scopes, independent QA/review, and release-120 overlap
  gate are supplied. No credential, provider, network, or production input is
  required or authorized.
- **D5 architecture / ownership `[CONFIRMED]`**: one editor owns each lane;
  shared paths are serial; generated refresh has one owner; the existing
  release integration owner is not duplicated.
- **D6 assumptions `[CONFIRMED]`**: static routing metadata is intent only,
  never runtime/provider proof. `HANDOFF.md` is derived state and cannot
  override `PROJECT_TASKS.md`. Silence, `UNKNOWN`, or local green checks never
  waive a dependency or release gate.
- **D7 risk / recovery `[CONFIRMED]`**: fail closed on untrusted hooks, raw
  transcript access, oversized/partial capsules, active-lane clear attempts,
  provenance drift, or overlap. Recovery is to stop descendants and revert
  only the isolated owned commit or abandon the isolated branch; current
  release history remains untouched.
- **D8 budget / evidence `[CONFIRMED]`**: evidence is bounded to exact paths,
  immutable provenance, concise ASCII-safe output, and the DispatchDecision
  below. No runtime/provider claim is inferred.
- **D9 domain / HITL `[NOT-APPLICABLE]`**: no metaphysical behavior, source
  domain, prediction, or training data changes. Owner HITL applies only to the
  scheduling adjustment and remains bounded by `CTX-100-INTEGRATION-HOLD`.
- **Waivers / unresolved questions**: none.

### Architecture invariants

1. `PROJECT_TASKS.md` is the ticket and current-state authority.
   `HANDOFF.md` is a derived, replaceable capsule and never an authority.
2. `.agents/config/context_handoff_v1.json` is the canonical machine policy;
   `.agents/skills/anti-cognitive-decay/SKILL.md` is the canonical skill, with
   `.agents/rules/20-context-handoff.md` the human-readable normative rule.
   Runtime mirrors are generated artifacts only.
3. `scripts/context_handoff.py` is a Python-standard-library-only shared engine
   with deterministic `hook`, `snapshot`, `rehydrate`, and `validate`
   operations. Runtime adapters call this engine and do not fork policy.
4. The engine never reads a raw chat/session transcript. It accepts only
   bounded structured state and repository metadata expressly allowed by the
   canonical policy.
5. Trigger evidence uses strict precedence: `tokens > percent > bytes >
   UNKNOWN`. Signals are never averaged,
   guessed, or silently promoted; `UNKNOWN` cannot authorize clear.
6. A derived capsule is capped at `16 KiB` and written atomically. The engine
   must bound content before replacement and must never leave a partial file.
7. No runtime automatically invokes compact, `/clear`, or reset. The engine
   may recommend an operator action only. Any active lane denies clear.
8. Codex hook execution requires an explicitly trusted hook configuration.
   Missing, unsupported, or untrusted hook state fails closed; no flag,
   fallback, adapter, or documentation may bypass trust.

### Frozen ownership and path allowlists

The test-only baseline is owned solely by `CTX-010-RED` and contains exactly:

- `tests/test_context_handoff.py`
- `tests/test_context_handoff_hooks.py`
- `tests/fixtures/context_handoff/**`
- `plans/test_provenance/ctx-handoff-20260830-b00.json`

The source allowlist is exactly the canonical files assigned to
`CTX-020-CORE`, `CTX-030-ADAPTERS`, `CTX-040-POLICY`, and `CTX-050-SYNC`:

- `.agents/config/context_handoff_v1.json`
- `scripts/context_handoff.py`
- `.codex/hooks.json`
- `.claude/hooks/stop-monitor.sh`
- `.agy/hooks/stop-monitor.sh`
- `.agents/skills/anti-cognitive-decay/SKILL.md`
- `.agents/rules/20-context-handoff.md`
- `.agents/AGENTS.md`
- `scripts/sync_claude_agy_parity.py`
- `scripts/sync_ai_agent_ecosystem.py`

Generated mirrors and documentation are excluded from that source allowlist
until their serial lanes. `CTX-060-GENERATED` owns exactly these three files:

- `.antigravity/skills/anti-cognitive-decay/SKILL.md`
- `.claude/skills/anti-cognitive-decay/SKILL.md`
- `.agy/skills/anti-cognitive-decay/SKILL.md`

After source and generated freeze, `CTX-070-DOCS` owns exactly:

- `README.md`
- `HOWTO.md`
- `HANDOFF.md`
- `AGENTS.md`
- `CLAUDE.md`
- `AGY.md`

### Canonical local-only ticket graph

| ID | Severity / effort | One owner | Status | Dependencies | Exact scope and measurable acceptance | Stop condition / exclusions |
|---|---|---|---|---|---|---|
| `CTX-000-GOV` | HIGH / S | `business_analyst` | DONE | fresh owner instruction | `PROJECT_TASKS.md`, `plans/plan.md` only; exact graph, invariants, scheduling adjustment, release hold, staged-path/diff checks, one prescribed commit | stop on any extra path or current-release mutation; no tests/source/config/hooks/skills/generated/`HANDOFF.md`/provider/network/credential/push/deploy action |
| `CTX-010-RED` | CRITICAL / S | `qa_tester` | READY | `CTX-000-GOV` | exact four-path test scope above; one immutable test-only `test-provenance-v1` baseline records deterministic RED or explicit negative control, argv, exit status, hashes, and concise fingerprint | stop on source/generated/docs mixing, missing RED evidence, manifest drift, or test ownership overlap |
| `CTX-020-CORE` | CRITICAL / M | `developer` | BLOCKED | `CTX-010-RED` is `TEST_BASELINE_VERIFIED` | `.agents/config/context_handoff_v1.json`, `scripts/context_handoff.py` only; stdlib engine implements and validates the frozen policy and all four operations against the immutable baseline | stop on baseline/hash drift, raw-transcript read, non-stdlib dependency, automatic clear/compact, partial/over-cap write, or extra path |
| `CTX-030-ADAPTERS` | HIGH / S | `developer` | BLOCKED | `CTX-020-CORE` | `.codex/hooks.json`, `.claude/hooks/stop-monitor.sh`, `.agy/hooks/stop-monitor.sh` only; all three call the shared engine with equivalent fail-closed behavior and Codex trust is proven | stop on duplicated policy, trust bypass, automatic clear/compact, swallowed failure, repository write outside the derived capsule, or extra path |
| `CTX-040-POLICY` | HIGH / S | `skill_rule_owner` | BLOCKED | `CTX-020-CORE` | `.agents/skills/anti-cognitive-decay/SKILL.md`, `.agents/rules/20-context-handoff.md`, `.agents/AGENTS.md` only; canonical skill/rule/catalog match machine policy and preserve operator-only clear | stop on policy divergence, generated-file edit, unsafe invocation, ownership overlap, or extra path |
| `CTX-050-SYNC` | HIGH / M | `developer` | BLOCKED | `CTX-030-ADAPTERS`, `CTX-040-POLICY` | `scripts/sync_claude_agy_parity.py`, `scripts/sync_ai_agent_ecosystem.py` only; deterministic sync/check recognizes canonical policy and produces only the declared mirrors with check mode read-only | stop on unrelated generation, out-of-repo/global write, source overwrite, parity drift, active current-release ownership, or extra path |
| `CTX-060-GENERATED` | HIGH / XS | `generated_refresh_owner` | BLOCKED | `CTX-050-SYNC` | exact three mirrored skill files above in one generated-refresh lane; bytes and provenance match canonical output and sync check is clean | stop on manual divergent edits, any fourth generated path, canonical-source mutation, or non-determinism |
| `CTX-070-DOCS` | HIGH / S | `business_analyst` | BLOCKED | `CTX-020-CORE` through `CTX-060-GENERATED` source/generated freeze | exact six documentation/global-guidance files above; operator guidance matches frozen behavior, labels `HANDOFF.md` derived, and makes no release/provider claim | stop on source/test/generated mutation, stale behavior, authority inversion, ownership overlap, or extra path |
| `CTX-080-QA` | CRITICAL / M | `qa_tester` | BLOCKED | `CTX-010-RED` through `CTX-070-DOCS` green | read-only independent QA runs frozen focused tests, provenance/history guards, adapter negatives, ecosystem parity/check, security scan, and applicable regression; every required command exits 0 with bounded evidence | any fail, skip, stale fixture/hash, trust ambiguity, or source/test edit blocks review |
| `CTX-090-REVIEW` | CRITICAL / S | `code_reviewer` | BLOCKED | `CTX-080-QA` green | read-only independent review verifies architecture, security/privacy, trust, one-editor history, exact-path provenance, and QA receipts; explicit approval required | any critical/high finding, missing evidence, raw transcript risk, trust bypass, or scope drift blocks integration |
| `CTX-100-INTEGRATION-HOLD` | CRITICAL / S | `release_integrator` (existing current-release owner; no duplicate) | BLOCKED | release 120 production-green and every `CTX-000` through `CTX-090` gate green | after explicit owner handoff, revalidate ancestry, exact commits, overlap, independent QA/review, current-release CI, and merge plan before any integration action | no integration, merge/cherry-pick, push, deploy, publish, or production activation while release 120, a prior CTX gate, ownership, or overlap is not green |

### DispatchDecision v1

`ticket=CTX-000-GOV`; `phase=planning/governance`; ranks `3/3/2/2/3`;
floor `gpt-5.6-sol/high`; selected `gpt-5.6-sol/ultra` by owner planning
override; quota `unknown` with bounded native mutation; `work_mode=mutation`;
`selected_alias=native-bsa`; policy `2026-08-29.1`; `root-medium=true`;
`hitl=true`; digest `pending`; status `READY_TO_VALIDATE`. This static label is
routing intent only, not provider execution proof.
<!-- CTX-HANDOFF-V1-20260830:END -->

<!-- IDQ-AUTH02-OPERATIONAL-GOVERNANCE-20260830:START -->
## Current IDQ operational correction and `AUTH-02` approval intent

**Recorded**: `2026-08-30` (Asia/Bangkok). **Gate**: `APPROVED` for this
planning/governance checkpoint only. This block is the canonical current IDQ
status. Older IDQ and release blocks below are retained as historical evidence;
their old test, deployment, or production claims are not current verification.

**Authority boundary**: the owner authorized `AUTH-02` approval intent for a
future bounded four-alias proof. Predecessor `IDQ-MVP-080-AUTH-01` is
`SEALED / EXPIRED` and cannot be replayed. No active TTL, nonce, risk lease, or
dispatch lease exists under `AUTH-02`; those values may be created only during
the final fresh preflight after every predecessor gate is green.

### Current evidence correction

- `IDQ-MVP-000-GOV` remains `DONE` as historical governance only.
- `IDQ-MVP-010-BASELINE`: `0e1941528c0c8f49ef50a14fd046db2163d33379`
  is the verified release-cycle baseline in current ancestry. Commit
  `0946bdec65173edacbaf4044b4198d55136c33ca` is a separately retained
  reconstructed five-path baseline and is `NON_TDD_RECONSTRUCTED`; it is not a
  substitute for, or proof of, the verified baseline.
- `IDQ-MVP-020-STORE` has a local contract in current ancestry, but fresh QA
  against the intended operational path is pending. No current production or
  provider-readiness claim follows from local source presence.
- `IDQ-MVP-030-DISPATCHER` through `IDQ-MVP-060-INTEGRATION` are reopened and
  blocked until a real executor/daemon route, including the cross-runtime
  handoff path, is implemented and evidenced.
- `IDQ-MVP-070-QA` is reopened. Earlier pass counts are historical and cannot
  satisfy the required fresh deterministic and operational QA gates.
- `IDQ-MVP-080-FOUR-ALIAS` is blocked pending the real path, fresh QA, an
  effective enforced read-only runtime, and a fresh activation/preflight.
- `IDQ-MVP-090-SEAL-GOV` remains blocked until all four terminal outcomes are
  valid and the temporary activation is sealed.

### Canonical operational ticket graph

| ID | Severity / Effort | One owner | Status | Dependencies | Exact scope and acceptance | Stop condition / exclusions |
|---|---|---|---|---|---|---|
| `IDQ-OP-000-GOV` | HIGH / S | `business_analyst` | DONE | owner authorization | only `PROJECT_TASKS.md` and `plans/plan.md`; current truth, graph, authorization boundary, and diff checks recorded | stop on overlap or evidence conflict; no source/tests/config/provider/release action |
| `IDQ-OP-010-BASELINE` | CRITICAL / S | `qa_tester` | DONE — VERIFIED | `IDQ-OP-000-GOV` | use verified baseline `0e1941528c0c8f49ef50a14fd046db2163d33379`; retain `0946bde` only as reconstructed history | stop on ancestry/hash/provenance drift; no baseline relabeling |
| `IDQ-OP-020-EXECUTOR` | CRITICAL / M | `developer` | BLOCKED | `IDQ-OP-010-BASELINE` | implement the real bounded executor/daemon route and explicit cross-runtime handoff with no alias fallback | stop on mutation-capable provider work, secret/raw-stream handling, ownership overlap, or missing baseline |
| `IDQ-OP-030-QA` | CRITICAL / M | `qa_tester` | BLOCKED | `IDQ-OP-020-EXECUTOR` | fresh deterministic queue, lifecycle, cross-runtime handoff, receipt-integrity, and read-only-boundary evidence is green | any stale, missing, ambiguous, or failing result stops descendants |
| `IDQ-OP-040-AUTH02-GOV` | CRITICAL / XS | `business_analyst` | INTENT RECORDED — HOLD | `IDQ-OP-030-QA` | convert owner approval intent into a bounded activation only after QA is fresh; keep `AUTH-01` sealed | no TTL, nonce, or lease before final preflight; no inherited/replayed authority |
| `IDQ-OP-050-PREFLIGHT` | CRITICAL / S | `orchestrator` | BLOCKED | `IDQ-OP-030-QA`, `IDQ-OP-040-AUTH02-GOV` | prove the real executor path, effective read-only isolation, safe fresh quota, alias/executable identity, fresh decision/snapshot, then atomically issue and bind single-use TTL/nonce/lease | any stale/unknown/contradictory binding, auth/billing need, or secret exposure stops before process creation |
| `IDQ-OP-060-FOUR-ALIAS` | CRITICAL / M | `qa_tester` | BLOCKED | `IDQ-OP-050-PREFLIGHT` | exactly `codex1`, `codex2`, `agy1`, and `agy2`; one distinct read-only provider proof each with fresh validated receipt and typed result | no retry, fallback, substitution, fabricated receipt, raw stream, mutation, push, deploy, or publish |
| `IDQ-OP-090-SEAL` | HIGH / S | `business_analyst` | BLOCKED | `IDQ-OP-060-FOUR-ALIAS` | record four valid terminal outcomes, seal all temporary authority, and reconcile current docs without a release claim | absent/invalid outcome or unsealed authority keeps the ticket blocked |

**Integrity and scope lock**: all provider proof is read-only and must preserve
secret safety, raw-stream non-retention, independent receipt/`WorkResult`
validation, exact alias/ticket/attempt bindings, and honest AGY language
(`validated in-process only`). Cross-runtime handoff is now in scope only as a
bounded executor/daemon feature and QA contract; multi-host authority,
credentials, billing, push, deploy, publish, production cutover, and fabricated
or reconstructed provider evidence remain out of scope.

**DispatchDecision evidence label**: `IDQ-OP-000-GOV-20260830`; phase
`planning/governance`; ranks `scope=2`, `complexity=2`, `risk=2`,
`ambiguity=1`, `evidence=2`; floor `gpt-5.6-terra/high`; selected quality
override `native-bsa / gpt-5.6-sol / ultra`; quota `unknown` with bounded native
mutation; policy `2026-08-29.1`; root-medium confirmed; HITL approved; digest
pending native runtime; status `READY_TO_VALIDATE`. This is routing intent,
not provider execution proof.
<!-- IDQ-AUTH02-OPERATIONAL-GOVERNANCE-20260830:END -->

<!-- RELEASE-VERIFIED-20260830-000-GOV:START -->
## Verified-only production release program - RELEASE-VERIFIED-20260830-000-GOV
Gate: APPROVED. Scope: active/releasable tickets only. Historical, superseded, and future-roadmap work is ARCHIVED or DEFERRED by evidence, never falsely DONE.
Policy: merge/cherry-pick only verified non-superseded deliverables; preserve evidence/recovery refs and never merge them wholesale. GitHub Actions starts only from main. Production targets are HF Docker pphothidaen/horoconsultant-core-backend and a separately gated Vercel UI. Push, deploy, and remote cleanup are owner-authorized but dependency-gated. Never read or record credential values.
Current release state: BLOCKED at live deployed-identity evidence, not production-green. HF prior-tree baseline `65e7335` and source `1dfb7ba` are locally DONE and independently `READY_FOR_INTEGRATION`, but the live HF identity remains stale/malformed. HTTP 200 health is availability evidence only, never release-identity or rollback proof.
Rollback gate: any nonzero, missing, stale, indeterminate, auth/permission, secret, provenance, prior-tree, or identity evidence stops downstream work. Deployment requires a bound prior revision/tree identity and tested rollback path. Cleanup requires ticket 120 production/post-deploy green.
Inventory 010 DONE: origin/main=665a507; local main=9e901fa; current b37b13d dirty; 58793b0 patch-equivalent; 9e901fa separate verification. fix/subagent-fail-closed DEFERRED. QA/IDQ/QOBS/evidence/recovery refs are preserved, never wholesale merged; cleanup is deferred until production green; the dirty linked qa/idq worktree is preserved. Legacy release-recovery is ARCHIVED/SUPERSEDED; MAREF, IDQ provider proof, and RC2/QOBS are DEFERRED; full-profile Playwright remains active under 120; TICKET-META-008 continuity is operational authority, not a release gate.
Lesson 20 truth: baseline 020 is DONE at `84b1dcf6125d13ed089ea2b6485fe059d6825d0a` and permanently `NON_TDD_RECONSTRUCTED`, never verified TDD. Source `ca7fdec` is review BLOCKED. Mode-only `f1ed5ee` has local evidence of 822 passing tests but inherits the reconstructed limitation. Safety follow-up baseline ticket 034 is IN_PROGRESS.
QA readiness truth: collection and shard planning is PREPARED; execution and fresh browser evidence wait for candidate freeze and the exact deployed HF/Vercel identities. Prepared plans or stale artifacts are not QA pass receipts.
Impact-gate policy is effective immediately: every lane emits a versioned `GateImpactDecision` with base/head/diff digest, changed paths/contracts/dependencies/surfaces, `RUN` gates, reasoned `NOT_APPLICABLE` gates, unknown-impact fallback, policy version, and reviewer/owner. Run only directly or transitively affected gates; unknown impact, stale/missing maps, or cross-cutting security/release boundaries fail closed broader. `NOT_APPLICABLE` never bypasses changed-source provenance, relevant security, reviewer evidence, or post-deploy identity/health for a touched deployment surface. Current release selection is manual and evidence-backed; deterministic selector/hook/rule/skill automation is `DEFERRED_NEXT_PHASE` until release 120 is production-green.
Temporary session routing evidence: owner approved Fast mode for new lanes until final production-green, and the active Codex account config changed `service_tier = "default"` to `service_tier = "priority"`. This is configured intent, not execution proof: collaboration receipts do not expose `service_tier`. The `gpt-5.6-sol/ultra` child override and root-medium gate remain unchanged. `GOV-BN-100-MODEL-RESTORE` must return `service_tier` to `default` only after final post-deploy green.
Throughput policy: while a dependency-ready, non-overlapping lane exists, Root A maintains 3/3 native child-slot occupancy and immediately backfills every completed or blocked slot with the next ready microticket. Parallelism must not duplicate work, cross one-editor ownership, or bypass a test-only baseline, provenance allowlist, QA, review, main-only CI, deployment, or identity gate. Root B/AGY fan-out remains prohibited until its separate provider-proof microticket succeeds; static config and supervisor smoke are non-proof.
Rule 11 ticket graph: each row includes ID, Severity, Work Effort, one Owner, Status, Dependencies, exact ownership, Acceptance, Stop condition, Exclusions.
| ID | Severity | Effort | Owner | Status | Dependencies | Exact ownership | Acceptance | Stop condition | Exclusions |
|---|---|---|---|---|---|---|---|---|---|
| RELEASE-VERIFIED-20260830-000-GOV | CRITICAL | XS | business_analyst | DONE | grill approval | both governance blocks | matching blocks and diff checks | mismatch or drift | source/tests/git/remotes/deploy/secrets |
| RELEASE-VERIFIED-20260830-010-INVENTORY | HIGH | S | business_analyst | DONE | 000 | read-only branch/worktree/ticket audit | classification evidence above | stale/indeterminate inventory | mutation/merge/cleanup/credentials |
| TICKET-RELEASE-VERIFIED-20260830-020-LESSON20-BASELINE | HIGH | M | qa_tester | DONE | 010 | `tests/test_fail_fast_triage.py`; `plans/test_provenance/ticket-release-verified-20260830-020-lesson20.json` | immutable test-only commit `84b1dcf6125d13ed089ea2b6485fe059d6825d0a`, RED/negative-control and guards; label `NON_TDD_RECONSTRUCTED` | hash/provenance drift | source/docs/unrelated dirty files/push/deploy; never verified TDD |
| RELEASE-VERIFIED-20260830-030-LESSON20-IMPL | HIGH | M | developer | REVIEW_BLOCKED | 020 DONE | `scripts/fail_fast_triage.py` only at `ca7fdec` | source commit is baseline-bound; review blocker remains explicit | review/failure/drift | docs/tests/branches/deploy |
| RELEASE-VERIFIED-20260830-031-LESSON20-MODE | HIGH | XS | developer | DONE_LOCAL | 030 source | mode-only `scripts/fail_fast_triage.py` commit `f1ed5ee` | 822 local tests pass; no content change | reconstructed limitation or review drift | tests/docs/deploy; never verified TDD |
| RELEASE-VERIFIED-20260830-034-LESSON20-SAFETY-BASELINE | CRITICAL | M | qa_tester | IN_PROGRESS | 031 | safety follow-up tests and closed provenance manifest only | immutable test-only RED/negative-control baseline | source/non-test path, missing RED, or provenance drift | source/docs/branches/deploy |
| RELEASE-VERIFIED-20260830-041-HF-PRIOR-TREE-AUDIT | CRITICAL | S | devops | DONE-BLOCKING | 010 | read-only GitHub/HF/Vercel/predecessor and identity audit | sanitized receipt records `PRIOR_TREE_UNAVAILABLE` and HF/Vercel candidate mismatch; HTTP 200 classified as non-proof | any inferred/fabricated prior tree or identity | file mutation/credentials/deploy/workflow trigger |
| RELEASE-VERIFIED-20260830-042-HF-PRIOR-TREE-BASELINE | CRITICAL | M | qa_tester | DONE_LOCAL | 041 | `tests/test_publish_space_hf.py`; `plans/test_provenance/ticket-release-verified-20260830-042-hf-prior-tree.json` at `65e7335` | immutable committed test-only baseline and provenance allowlist for `scripts/publish_space_hf.py` | hash/guard or extra-path drift | source/docs/remotes/deploy |
| RELEASE-VERIFIED-20260830-043-HF-PRIOR-TREE-IMPL | CRITICAL | M | developer | DONE_LOCAL | 042 immutable DONE | `scripts/publish_space_hf.py` only at `1dfb7ba` | focused local evidence proves bounded fail-closed prior-tree handling | test/failure/ownership drift | tests/docs/workflows/remotes/deploy |
| RELEASE-VERIFIED-20260830-044-HF-PRIOR-TREE-REVIEW | CRITICAL | S | release_reviewer | READY_FOR_INTEGRATION | 043 | read-only review of exact `65e7335`/`1dfb7ba` commits and receipts | independent scope/ancestry/failure-class review complete; integration still gated | live identity stale/malformed or evidence drift | implementation/deploy |
| RELEASE-VERIFIED-20260830-040-INTEGRATE | CRITICAL | M | release_integrator | TODO | 010,031,034,044 | dedicated clean integration branch | only verified non-superseded commits integrated; evidence refs preserved | conflict/unverified/wholesale evidence merge | deploy/cleanup |
| TICKET-RELEASE-VERIFIED-20260830-050-DOCS | HIGH | S | business_analyst | DONE_DOCS_SCOPE | current evidence freeze; final refresh after 040 | `README.md`, `HOWTO.md`, matching BSA blocks in `PROJECT_TASKS.md` and `plans/plan.md` | operator/status/impact policy match evidence; blocks hash-match; docs checks green | mismatch/stale evidence or transitive non-doc impact | HANDOFF/source/tests/config/rules/skills/hooks/generated/git/remotes/deploy |
| RELEASE-VERIFIED-20260830-060-QA | CRITICAL | L | qa_tester | IMPACT_SELECTED_PREPARED | 040,050 | only validated `GateImpactDecision.RUN` gates and fresh evidence for touched surfaces | zero missed affected gates; all RUN receipts green; every N/A reasoned; no stale evidence substituted | any missed/failed/missing/stale/indeterminate/security/provenance/identity evidence | unrelated traditional checklist gates |
| RELEASE-VERIFIED-20260830-070-REVIEW | CRITICAL | S | release_reviewer | TODO | 060 | independent safety verdict | scope/receipts/rollback/READY_FOR_PROD verified | unresolved/unverifiable risk | implementation/deploy |
| RELEASE-VERIFIED-20260830-080-MAIN | CRITICAL | S | release_integrator | TODO | 070 | local main integration and main push | approved release reachable/push receipt | dirty main/ancestry mismatch/gate fail | non-main push/deletion |
| RELEASE-VERIFIED-20260830-045-MAIN-ONLY-RETRY-EVIDENCE | CRITICAL | S | devops | TODO | 080 | one bounded retry/evidence collection from main only; sanitized run and deployed-identity inputs | exact main SHA and run identity bound; no workflow starts from any other branch | wrong branch/failure/stale/unbound run | source edits/non-main trigger/identity inference |
| RELEASE-VERIFIED-20260830-090-CI | CRITICAL | S | devops | TODO | 045 | GitHub Actions release gate from main only | bound main run succeeds | wrong branch/failure/stale run | bypass/deploy |
| RELEASE-VERIFIED-20260830-100-HF | CRITICAL | M | devops | TODO | 090 | HF Docker deploy/verify and rollback identity | health/version/API green | auth/nonzero/stale/missing/identity mismatch | Vercel/cleanup |
| RELEASE-VERIFIED-20260830-110-VERCEL | CRITICAL | M | devops | TODO | 090 | separate Vercel deploy/verify and rollback identity | UI/version green with receipt | failed/indeterminate UI/identity | HF/cleanup |
| RELEASE-VERIFIED-20260830-120-POSTDEPLOY | CRITICAL | M | qa_tester | TODO | 100,110 | health/version/API/button/E2E/five-viewport | both canonical identities green | any failed/missing/stale/auth/secret/provenance/identity evidence | cleanup/close |
| RELEASE-VERIFIED-20260830-130-CLEANUP | HIGH | S | release_integrator | TODO | 120 green | safe merged/superseded refs/worktrees | reachability proof; retain main/protected/evidence/recovery/needed | uncertain/unmerged/needed/protected/unsafe | delete evidence/needed |
| RELEASE-VERIFIED-20260830-140-CLOSE | HIGH | XS | business_analyst | TODO | 120,130 | canonical docs/tickets/HANDOFF reconciliation | final evidence and truthful statuses | missing evidence/mismatch | false completion/unrelated cleanup |
Archive/defer policy: preserve historical records; classify audited refs ARCHIVED when superseded/obsolete and DEFERRED when future/non-release or dependency-blocked, with evidence and owner.
Concurrent unowned changes .agents/config/multiagent_prompt_command.example.yaml and scripts/multiagent_prompt_command.py preserved/excluded six-pool work; do not edit, revert, or stage. Codex1 terminal dispatch: no child ran because runtime config/preflight/snapshot/current-policy binding was not independently validated; static planning is not execution proof and no provider ticket is DONE.
DispatchDecision v1: schema=1; ticket=RELEASE-VERIFIED-20260830-000-GOV; phase=planning; ranks=1/1/1/0/1; quota=unknown; mode=mutation; alias=codex1; model=gpt-5.6-luna; effort=medium; policy=2026-08-29.1; planning_to_medium_confirmed=true; hitl_approved=true; digest=4c998b557752f838a4d8cc15b547d357a3cba8a5b07d4ce22c135bb100e16d0b. Validated planning decision, not provider execution proof.
DispatchDecision v1 update: schema=1; ticket=RELEASE-VERIFIED-20260830-010-INVENTORY; phase=planning; ranks=1/1/1/0/1; quota=unknown; mode=mutation; alias=codex1; model=gpt-5.6-luna; effort=medium; policy=2026-08-29.1; root-medium=true; hitl=true; digest=e44bd9dea23f0b7592181d4b5ef880a2c69fdc36d8f854321c86f09ba34e1e52. Validated planning only.
Attempt 1: BLOCKED_SCHEMA_ID. No files, worktree, or commit created; immutable evidence, not a retry failure.
DispatchDecision v1 normalized baseline: schema=1; ticket=TICKET-RELEASE-VERIFIED-20260830-020-LESSON20-BASELINE; phase=qa; ranks=1/2/2/1/2; quota=constrained; mode=mutation; alias=codex1; model=gpt-5.6-terra; effort=high; policy=2026-08-29.1; root-medium=true; hitl=true; digest=30bd6c612ef65b15c20eaad7a49d03a630083bc2bf29d8d1402eeadd726c007a. Correction lane digest=8141f18bbc335d416d0c2c093f0505ea4e55809a27b7739d7163a5dab4bfe90d. Validated planning only.
Docs DispatchDecision v1: ticket=TICKET-RELEASE-VERIFIED-20260830-050-DOCS; phase=planning; ranks=2/2/1/2/2; quota=constrained; mode=mutation; alias=codex2; model=gpt-5.6-sol; effort=ultra; policy=2026-08-29.1; root-medium=true; HITL=true; digest=712cb22c7f17a6519c7d78d52b438bcc70dd1f69ecdec8638e0c2b04f058e144. Owner-approved temporary Sol/ultra quality exception remains active until all production post-deploy gates pass; parallel isolation is the latency control. Validated routing intent, not provider execution proof.
<!-- RELEASE-VERIFIED-20260830-000-GOV:END -->
<!-- GOV-BN-20260830:START -->
## Owner-approved bottleneck-removal epic - GOV-BN-20260830
Gate: APPROVED for planning and the dependency-gated phases below. The epic is isolated from the current release candidate. Its canonical mutations and integration wait for `RELEASE-VERIFIED-20260830-120-POSTDEPLOY` production-green; it then receives independent QA/review, its own main-only CI, production deployment, and post-deploy identity gate before routing is restored.

Owner-approved phase split: the current release may use immediate manual/evidence-based `GateImpactDecision` records, slot backfill, and only its already-scoped release fixes. Deterministic selector source, hook consolidation, ecosystem sync changes, dispatcher/scheduler, queue/heartbeat, skills/rules decomposition, Root B proof, HF payload/memory optimization, and every other cross-cutting refactor below are notes/tickets only with status `DEFERRED_NEXT_PHASE`. They cannot start before current release 120 is production-green. Each deferred feature group must retain separate immutable test-baseline, source, independent review, and integration microtickets with non-overlapping one-editor ownership and dependency-safe parallel waves.

Impact selection contract: every lane records schema/policy version, base/head/diff digest, changed paths/contracts/dependencies/surfaces, `RUN` gates, reasoned `NOT_APPLICABLE` gates, the unknown-impact fallback, and reviewer/owner. Only directly or transitively affected gates run. Unknown impact, rename ambiguity, stale/missing maps, or cross-cutting security/release boundaries expand to the broader applicable set. `NOT_APPLICABLE` never bypasses changed-source provenance, relevant security, reviewer evidence, or post-deploy identity/health for a touched surface.

GRILL REPORT: D1 IN is pool/config truth, repo-only ecosystem sync/parity, unified hooks, skill/rule decomposition and evals, Hermes contract, generated refresh, decision/result contracts, scheduler/dispatcher decomposition, queue fairness, heartbeat, supervisor/handoff, Root B proof, QA/review/release, and routing restoration. OUT is current-candidate mutation, secret/auth/billing bypass, manual generated-file edits, takeover of dirty/unowned work, and treating static metadata as provider proof. D2 changes a monolithic/duplicated control plane into bounded one-editor components while preserving public CLI/contracts and fail-closed denials. D3 succeeds only at ticket 110 after two production-green sequences and restoration verification; any gate failure stops descendants. D4 depends on current release 120 green, immutable baselines, provenance allowlists, current-owner handoff for dirty files, valid capacity/lease/quota evidence, main-only Actions, and production identities. D5 ownership and order are frozen below. D6 no silence is a waiver; provider/runtime and prior-tree claims require receipts. D7 recovery is preserve refs, revert only the owned commit, retain the facade, and halt before downstream integration. D8 temporary routing is owner-approved `gpt-5.6-sol/ultra`; parallel isolation, not assumed model speed, controls latency. D9 is NOT-APPLICABLE: no metaphysical behavior or data changes.

Temporary model/tier exception: all executable lanes use `gpt-5.6-sol/ultra`, preserve the root-medium gate, and request Fast mode through configured `service_tier = "priority"` until `GOV-BN-091-POSTDEPLOY` is production-green. Collaboration receipts do not expose `service_tier`, so Fast/priority is configured intent rather than execution proof. Only then may `GOV-BN-100-MODEL-RESTORE` return `service_tier` to `default` and restore Luna-default for bounded rank-0/1 work with risk-based Terra/Sol escalation; no risk floor may be lowered. Planning DispatchDecision: ticket=`TICKET-GOV-BOTTLENECK-20260830-000-PLAN`; phase=planning; ranks=3/3/2/2/3; quota=constrained; mode=mutation; alias=codex2; model=gpt-5.6-sol; effort=ultra; policy=2026-08-29.1; root-medium=true; HITL=true; digest=`7721208765231fad7efd9639c324c3fade7253713ed7941c004e2a8596cca4c0`; quality exception=owner-approved temporary Sol/ultra override until final production-green, with parallel isolation as latency control. This is validated routing intent, not provider execution proof.

Capacity policy: keep 3/3 native child slots occupied whenever dependency-ready, non-overlapping microtickets exist; immediately backfill a completed or blocked slot. Never create duplicate owners or bypass baseline/provenance dependencies to fill capacity. No AGY nested child may start before `GOV-BN-053-ROOTB-PROOF` records a fresh request, lease, quota observation, provider-bound receipt, and bounded no-write smoke; supervisor/static-config smoke is non-proof.

Immutable baseline/provenance matrix: every mutation row must name one committed test-only baseline and an exact allowed-source list. A baseline commit cannot include source, generated, documentation, or runtime output.
| Baseline | Status | Depends on | Test-only owner and files | Allowed source for descendant mutations | Stop condition |
|---|---|---|---|---|---|
| GOV-BN-B00-POOL | DEFERRED_NEXT_PHASE | release 120 green; current six-pool owner identified | qa_tester: `tests/test_multiagent_capacity.py`, `tests/test_multiagent_prompt_command.py`, `plans/test_provenance/gov-bn-20260830-b00-pool.json` | 000 only: `.agents/config/multiagent_prompt_command.example.yaml`, `scripts/multiagent_prompt_command.py` | dirty ownership unresolved; no RED/negative control; guard drift |
| GOV-BN-B10-SYNC | DEFERRED_NEXT_PHASE | release 120 green; 000 DONE | qa_tester: `tests/test_test_provenance_ecosystem_sync.py`, `tests/test_sync_claude_agy_parity_payload_mode_contract.py`, `plans/test_provenance/gov-bn-20260830-b10-sync.json` | 010/011 serially: `scripts/sync_ai_agent_ecosystem.py` | MAREF-054-A duplicate owner; no deterministic RED/parity fixture |
| GOV-BN-B20-HOOKS | DEFERRED_NEXT_PHASE | release 120 green | qa_tester: `tests/test_unified_governance_hooks.py`, `plans/test_provenance/gov-bn-20260830-b20-hooks.json` | 020/021 disjoint hook paths listed below | deny mismatch, timing fixture absent, or hook writes repository |
| GOV-BN-B30-POLICY | DEFERRED_NEXT_PHASE | release 120 green | qa_tester: immutable old snapshots, adversarial eval fixtures, `tests/test_agent_governance_decomposition.py`, `plans/test_provenance/gov-bn-20260830-b30-policy.json` | 030/031/032 canonical paths; 033 generated outputs only through sync | reviewer-first/trigger/safety/precision/recall/context fixture missing |
| GOV-BN-B40-CONTROL | DEFERRED_NEXT_PHASE | release 120 green; 000 DONE | qa_tester: schema/scheduler/dispatcher contract tests and `plans/test_provenance/gov-bn-20260830-b40-control.json` | 040/041/042/043 disjoint paths below | facade behavior or decision/result compatibility not frozen |
| GOV-BN-B50-RUNTIME | DEFERRED_NEXT_PHASE | release 120 green | qa_tester: `tests/test_multiagent_durable_queue.py`, `tests/test_multiagent_root_worker.py`, `tests/test_multiagent_root_supervisor.py`, `tests/test_inter_root_dispatch_contract.py`, `plans/test_provenance/gov-bn-20260830-b50-runtime.json` | 050/051/052 disjoint runtime paths below | deterministic fairness/TTL/race/provider boundaries not RED-frozen |
| GOV-BN-B60-IMPACT | DEFERRED_NEXT_PHASE | release 120 green | impact_baseline_qa: `tests/test_impact_gate_selector.py`, impact eval fixtures, `plans/test_provenance/gov-bn-20260830-b60-impact.json` | only the GOV-BN-060 impact source rows below | any missing deterministic RED/negative control, eval case, or closed allowlist |

Deferred one-editor execution graph. Nothing in this graph runs during the current release. After release 120 is green, baseline waves B00..B60 may run in parallel only where ownership is disjoint. Source waves start only from their own immutable baselines; 010 then 011 are serial, 030/031/032 may be parallel, 041/042 may be parallel after 040, 043 waits for 042 plus dirty-owner handoff, and 050/051 may be parallel before 052 joins. Ticket 033 is one serial generated refresh after canonical agent/rule/skill/hook sources freeze. Every group requires its own review and integration receipt before a shared release gate.
| ID | Severity | Owner | Status | Dependencies | Exact one-editor ownership | Acceptance / stop |
|---|---|---|---|---|---|---|
| TICKET-GOV-BOTTLENECK-20260830-000-PLAN | HIGH | business_analyst | DONE | owner approval | only matching governance blocks in `PROJECT_TASKS.md` and `plans/plan.md` | blocks hash-match and `git diff --check`; stop on semantic drift |
| GOV-BN-000-CONFIG-POOL | CRITICAL | existing_six_pool_owner | DEFERRED_NEXT_PHASE/BLOCKED_OWNER | release 120 green; B00 | `.agents/config/multiagent_prompt_command.example.yaml`, then the current dirty alias-map hunk in `scripts/multiagent_prompt_command.py`; no other editor | reconcile four/five/six pool truth; stop until current owner hands off both dirty edits |
| GOV-BN-010-REPO-SYNC | HIGH | MAREF-054-A_sync_owner | DEFERRED_NEXT_PHASE | release 120 green; B10; 000 | `scripts/sync_ai_agent_ecosystem.py`; ownership is merged with MAREF-054-A, never duplicated | repo-only deterministic sync; stop on duplicate owner or out-of-repo write |
| GOV-BN-011-DETERMINISTIC-PARITY | HIGH | parity_developer | DEFERRED_NEXT_PHASE | 010 | subsequent serial parity hunk in `scripts/sync_ai_agent_ecosystem.py` only | repeat runs byte-identical and check explains drift; stop on nondeterminism |
| GOV-BN-020-UNIFIED-PREHOOK | CRITICAL | prehook_developer | DEFERRED_NEXT_PHASE | release 120 green; B20 | `.claude/settings.json` and listed `.claude/hooks/*` prehook paths | exactly one prehook process/event, deny equivalence, no swallowed failure or repo mutation |
| GOV-BN-021-NOWRITE-POSTHOOK | HIGH | posthook_developer | DEFERRED_NEXT_PHASE | B20; 020 contract frozen | `.agents/hooks.json`, listed `.agents/hooks/*`, `.claude/hooks/post-tool-use-formatter.sh` | posthook/precommit audit-only; stop on write or swallowed failure |
| GOV-BN-030-SKILLS-EVALS | HIGH | skill_architect | DEFERRED_NEXT_PHASE | release 120 green; B30 | listed orchestration `SKILL.md` sources and extracted skills only | reviewer-first evals, 100% safety, precision/recall >=0.90, context reduction evidence |
| GOV-BN-031-RULES-DECOMPOSITION | HIGH | rule_architect | DEFERRED_NEXT_PHASE | B30 | listed `.agents/rules/*` canonical paths and extracted rules only | no duplicated/conflicting mandate; stop on semantic loss |
| GOV-BN-032-HERMES-CONTRACT | HIGH | hermes_developer | DEFERRED_NEXT_PHASE | B30 | `.agents/agents/hermes/agent.json`, `scripts/hermes_model_parity.py` | bounded fail-closed contract; no provider/static-label inference |
| GOV-BN-033-GENERATED-REFRESH | CRITICAL | ecosystem_sync_operator | DEFERRED_NEXT_PHASE | 000,011,020,021,030,031,032 | generated outputs reported by ecosystem sync only | no manual generated edits; stop on unowned output or canonical mutation |
| GOV-BN-040-DECISION-RESULT-CONTRACTS | CRITICAL | contract_developer | DEFERRED_NEXT_PHASE | release 120 green; B40 | listed dispatch/work-result schemas; new version only if required | negative fixtures fail closed; stop on compatibility loss |
| GOV-BN-041-SCHEDULER-SPLIT | HIGH | scheduler_developer | DEFERRED_NEXT_PHASE | B40,040 | `scripts/multiagent_ticket_scheduler.py` plus new scheduler modules | deterministic facade compatibility; stop on behavior drift |
| GOV-BN-042-DISPATCHER-COMPONENTS | CRITICAL | dispatcher_components_developer | DEFERRED_NEXT_PHASE | B40,040 | new dispatcher component modules only | focused contracts green; stop on facade edit/cycle |
| GOV-BN-043-DISPATCHER-FACADE | CRITICAL | dispatcher_facade_owner_after_handoff | DEFERRED_NEXT_PHASE/BLOCKED_OWNER | 000,042; explicit handoff | `scripts/multiagent_prompt_command.py` only after dirty hunk attribution | thin compatible facade; stop on unowned diff or overlap |
| GOV-BN-050-QUEUE-FAIRNESS | CRITICAL | queue_developer | DEFERRED_NEXT_PHASE | release 120 green; B50 | `scripts/multiagent_durable_queue.py` only | deterministic no-starvation behavior; stop on lease bypass |
| GOV-BN-051-HEARTBEAT | CRITICAL | worker_developer | DEFERRED_NEXT_PHASE | B50 | `scripts/multiagent_root_worker.py`, `scripts/check_cookie_heartbeat.py` | heartbeat < TTL/3 and deterministic recovery |
| GOV-BN-052-SUPERVISOR-HANDOFF | CRITICAL | supervisor_developer | DEFERRED_NEXT_PHASE | 050,051 | `scripts/multiagent_root_supervisor.py` only | zero duplicate starts and explicit UNKNOWN recovery |
| GOV-BN-053-ROOTB-PROOF | CRITICAL | root_b_bootstrap_owner | DEFERRED_NEXT_PHASE | 000,033,040,041,043,050,051,052 | no-write provider receipt artifacts only | fresh provider-bound Root B proof; static config remains non-proof |
| GOV-BN-060-QA | CRITICAL | qa_tester | DEFERRED_NEXT_PHASE | all applicable source integrations including IMPACT-060 | only validated `GateImpactDecision.RUN` evidence | zero missed affected gates; all RUN green; every N/A reasoned; no stale evidence |
| GOV-BN-070-REVIEW | CRITICAL | release_reviewer | DEFERRED_NEXT_PHASE | 060 | read-only exact-commit and receipt review | independent release verdict; stop on unresolved risk |
| GOV-BN-080-MAIN | CRITICAL | release_integrator | DEFERRED_NEXT_PHASE | 070 | clean integration branch then `main`; verified commits only | approved reachability; stop on ancestry/dirty/conflict |
| GOV-BN-081-MAIN-ONLY-CI | CRITICAL | devops | DEFERRED_NEXT_PHASE | 080 | GitHub Actions from `main` only | bound main run green; stop on wrong branch/stale run |
| GOV-BN-090-PRODUCTION | CRITICAL | devops | DEFERRED_NEXT_PHASE | 081 | canonical HF Docker and separate Vercel receipts | deployed and rollback identities match main |
| GOV-BN-091-POSTDEPLOY | CRITICAL | qa_tester | DEFERRED_NEXT_PHASE | 090 | affected health/version/API/UI evidence | exact touched identities green; stop on HTTP-200-only or mismatch |
| GOV-BN-100-MODEL-RESTORE | HIGH | routing_owner | DEFERRED_NEXT_PHASE | 091 green | active Codex account `service_tier` plus canonical routing only through its owner/sync | `service_tier=default`; Luna bounded rank-0/1 default with risk escalation; root-medium preserved; no lowered floor |
| GOV-BN-110-CLOSE | HIGH | business_analyst | DEFERRED_NEXT_PHASE | 100 and any restoration CI | canonical docs/tickets/HANDOFF reconciliation | truthful final receipts; stop on mismatch |

### GOV-BN-060 IMPACT-GATE-SELECTION microtickets

All rows are `DEFERRED_NEXT_PHASE` and require current release 120 production-green. Wave 0 freezes tests; Wave 1 implements the selector/map; Wave 2 may update rules, skills, and existing unified hook/CI consumers in parallel after the selector contract freezes; Wave 3 performs independent QA/review; Wave 4 integrates reviewed commits. No row adds a new hook registration/process.

| ID | Wave | Owner | Status | Dependencies | Exact ownership | Acceptance / stop |
|---|---|---|---|---|---|---|
| GOV-BN-060-IMPACT-000-BASELINE | 0 | impact_baseline_qa | DEFERRED_NEXT_PHASE | release 120 green | `tests/test_impact_gate_selector.py`, impact eval fixtures, `plans/test_provenance/gov-bn-20260830-b60-impact.json` only | immutable test-only RED/negative-control baseline covers all six eval cases; stop on source/mixed commit |
| GOV-BN-060-IMPACT-010-SELECTOR-MAP | 1 | impact_selector_developer | DEFERRED_NEXT_PHASE | IMPACT-000 verified | `scripts/impact_gate_selector.py`, `.agents/config/gate-impact-map-v1.json` only | deterministic versioned `GateImpactDecision`; rename/dependency closure and unknown fallback fail closed |
| GOV-BN-060-IMPACT-020-RULES | 2 | impact_rule_architect | DEFERRED_NEXT_PHASE | IMPACT-010 contract frozen | `.agents/rules/02-testing-standards.md`, `.claude/rules/testing-and-release.md` only | Rule 02/Claude semantics match; no traditional full-suite mandate or safety loss |
| GOV-BN-060-IMPACT-030-SKILLS | 2 | impact_skill_architect | DEFERRED_NEXT_PHASE | IMPACT-010 contract frozen | new `.agents/skills/impact-based-gate-selection/`, `.agents/skills/qa-e2e-testing/`, `.agents/skills/sdlc-aisdlc-workflow/` only | new skill plus QA/SDLC updates pass skill-creator old/new trigger, adversarial, and safety evals |
| GOV-BN-060-IMPACT-040-HOOK-CI | 2 | impact_hook_ci_owner | DEFERRED_NEXT_PHASE | IMPACT-010 contract frozen; 020/021 ownership frozen | `.githooks/pre-commit`, `.github/workflows/ci.yml` only | validate through existing unified hook/CI process; no extra hook registration/process, swallowed failure, or repo write |
| GOV-BN-060-IMPACT-050-QA-REVIEW | 3 | independent_qa_reviewer | DEFERRED_NEXT_PHASE | IMPACT-010,020,030,040 | read-only exact-commit/eval/benchmark receipts only | zero missed affected gates across six cases; every N/A reasoned; reduction benchmark is evidence-only until measured |
| GOV-BN-060-IMPACT-060-INTEGRATE | 4 | impact_release_integrator | DEFERRED_NEXT_PHASE | IMPACT-050 READY | clean next-phase integration branch; reviewed commits only | baseline/source/review ancestry preserved and selected commits integrated; stop on conflict/unreviewed evidence |

Impact eval matrix: docs-only runs Markdown structure/link/reference, matching governance blocks, and `git diff --check`, with product/browser/Rust/HF/provider/secret/sync N/A when no transitive impact exists. Lesson 20 runs its focused CLI contracts, provenance, relevant security, and review gates. HF publisher runs publisher/provenance/security/review plus touched post-deploy identity/health. Hooks/rules run governance/eval/sync checks without unrelated product/browser/Rust suites. Rename/unknown expands dependency closure or fails closed broader when unresolved. Deploy runs the affected deployment, rollback, reviewer, and exact post-deploy identity/health gates. Acceptance is zero missed affected gates; gate-count/runtime reduction is recorded as evidence only until a measured baseline exists.

### GOV-BN-061 TMUX-CODEX-THROUGHPUT microtickets

Live audit on 2026-08-30 found no tmux server/session. The current release uses Codex subagents with isolated worktrees; historical artifacts show tmux only in prior AGY quota probes. `ACTIVE_NOW` threshold policy: expected >3-minute or output-heavy local commands and CI/deploy polling use a unique detached tmux session with a persistent sanitized log and explicit exit/done evidence; surface at most 30 lines. Short commands run directly. Never present tmux panes as agent concurrency, and do not start a dummy session. The runner refactor remains deferred below.

Codex tuning reuses the existing routing tickets: each lane must distinguish requested from observed model, effort, and service tier; when receipts omit tier, record `UNAVAILABLE` and never claim `FAST_ACTIVE`. Use short-context forks for bounded lanes. Ultra effort is allowed only inside the explicit owner-approved production-green exception window or for rank-3 gates. After final deploy/post-deploy green, `GOV-BN-100-MODEL-RESTORE` returns to Luna-default with risk-based escalation and `service_tier=default`; no duplicate tuning ticket is created here.

All implementation rows are `DEFERRED_NEXT_PHASE` until current release 120 reaches first production-green. This docs lane does not start/kill tmux or mutate the runner.

| ID | Wave | Owner | Status | Dependencies | Exact ownership | Acceptance / stop |
|---|---|---|---|---|---|---|
| GOV-BN-061-TMUX-000-BASELINE | 0 | tmux_baseline_qa | DEFERRED_NEXT_PHASE | release 120 green | `tests/test_tmux_runner.py`, `tests/test_ci_deploy_event_watcher.py`, tmux fixtures, `plans/test_provenance/gov-bn-20260830-b61-tmux.json` only | immutable test-only RED/negative-control covers collision, completed-before-capture, fallback, redaction, stale cleanup |
| GOV-BN-061-TMUX-010-RUNNER | 1 | tmux_runner_developer | DEFERRED_NEXT_PHASE | TMUX-000 verified | `.agy/scripts/tmux-runner.sh` only | unique durable session; persistent log plus exit/done metadata; no unconditional same-name kill; async fallback; bounded tail/status |
| GOV-BN-061-TMUX-020-WATCHER | 1 | ci_watcher_developer | DEFERRED_NEXT_PHASE | TMUX-000 verified | new `scripts/ci_deploy_event_watcher.py` only | event/change-triggered CI/deploy watcher with bounded exponential backoff and redacted output |
| GOV-BN-061-TMUX-030-QA-REVIEW | 2 | independent_tmux_reviewer | DEFERRED_NEXT_PHASE | TMUX-010,020 | read-only exact-commit/test/log receipts only | zero lost completion/exit evidence and at most 30 surfaced lines; stop on stale/collision/redaction/fallback ambiguity |
| GOV-BN-061-TMUX-040-INTEGRATE | 3 | tmux_release_integrator | DEFERRED_NEXT_PHASE | TMUX-030 READY | clean next-phase integration branch; reviewed commits only | baseline/source/review ancestry preserved; stop on conflict or unreviewed evidence |

Explicit blockers and exclusions: `.agents/config/multiagent_prompt_command.example.yaml` and `scripts/multiagent_prompt_command.py` contain concurrent unowned six-pool edits; only their current owner may reconcile or hand them off. Pool truth currently conflicts across four/five/six, and static configuration never proves Root B/provider execution. Generated mirrors are outputs and must never be edited manually; canonical changes require `python3 scripts/sync_ai_agent_ecosystem.py --sync` followed by `--check`. Evidence/recovery branches remain preserved until every required commit is reachable from production-green main.
<!-- GOV-BN-20260830:END -->
<!-- PROD-DEPLOY-RUN-33251910604:START -->
## Production Deployment Run 33251910604 — Verified on `main` (`98e19b4`, PR #4 Merged)

**Status**: `DEPLOYED & VERIFIED ON PRODUCTION` (`main` @ `98e19b4`, Run `33251910604`)
**Authority**: Production Deployment Verification Gate & Single Source of Truth
**Audit Summary**: 1,833/1,833 Tests Passed (100% Green), 33/33 UI Button Regressions Passed, 0 Secret Leaks (2,186 files scanned), 100% Agent Ecosystem Sync (0 drift)

### 🌐 Live Production Endpoints

| Service | Target URL | HTTP Status | Response Time | Status / Telemetry |
|---|---|---|---|---|
| **Vercel Static UI** | `https://horo-consultant-psi.vercel.app` | `200 OK` | ~228 ms | Active (Static document, `app.js`, Service Worker) |
| **Vercel Version Metadata** | `https://horo-consultant-psi.vercel.app/version.json` | `200 OK` | ~196 ms | Active (Canonical release identity) |
| **HF Docker Backend Health** | `https://pphothidaen-horoconsultant-core-backend.hf.space/health` | `200 OK` | ~975 ms | Active (FastAPI / Uvicorn container operational) |
| **Public Deterministic API** | `https://pphothidaen-horoconsultant-core-backend.hf.space/api/bazi/calculate` | `200 OK` | ~861 ms | Active (True Solar Time + BaZi Four Pillars calculation) |
| **Admin Provider Pools** | `/api/admin/provider-pools` | `200 OK` | <50 ms | Active (`[ZERO-COST POLICY: ACTIVE]`, 5 provider pools) |

### 🔍 Post-Deployment Verification Summary
1. **PR #4 Main Merge**: Pull Request #4 merged into `main` as commit `98e19b4`.
2. **CI/CD Deployment Run**: GitHub Actions Run `33251910604` (`workflow_dispatch`) completed with status `SUCCESS`.
3. **UI Button Regression Suite**: 33/33 passed (`python3 scripts/run_button_regression.py` -> `project/tests/button_regression_report.json`).
4. **Zero-Cost Multi-Tier Pipeline**: 51/51 zero-cost tests passed (`project/tests/test_zero_cost_pipeline.py`, `project/tests/test_semantic_cache.py`). 0ms circuit breaker bypass on HTTP 429 verified.
5. **Spark Model Governance**: Policy `2026-08-29.1` verified (15/15 tests pass).
6. **Five-Pool Capacity & IDQ Architecture**: 392/392 multiagent and IDQ tests passed (`tests/test_multiagent*.py`, `tests/test_idq*.py`).
7. **Rust PyO3 Math Core**: High-performance celestial coordinate and LuoPan SVG generation verified.
8. **Secret Leak Audit**: 0 leaks detected across 2,186 scanned files via Rust Rayon parallel scanner.
9. **AI Agent Ecosystem Sync**: 100% synchronized across Claude Code, Antigravity, and OpenAI Codex definitions (`python3 scripts/sync_ai_agent_ecosystem.py --check` PASS, 0 drift).
<!-- PROD-DEPLOY-RUN-33251910604:END -->

---

<!-- IDQ-MVP-BOARD-20260828:START -->
## Sprint IDQ-MVP — Independent Roots + Durable Queue Local MVP

**Historical gate**: `APPROVED` in `plans/plan.md`; local SQLite single-host MVP
only. Current ticket classifications are corrected below and summarized in the
canonical `2026-08-30` operational block at the top of this file.
**DispatchDecision**: `v1`, ticket `IDQ-MVP-GOV-001`, planning ranks
`3/3/3/1/3`, `gpt-5.6-sol/xhigh`, policy `current`, root-medium confirmed,
HITL approved by the user's delegate instruction.
**Global exclusions**: no MAREF C1/C2 closure, push, deploy, publish,
production cutover, credential/secret operation, fabricated receipt, raw
provider-stream persistence, or ordinary activation opening. Bootstrap is
explicit, risk-recorded, read-only, ephemeral, sealable, and never healthy.

| Ticket | Severity | Work Effort | One editor/executor | Status | Dependencies |
|---|---|---|---|---|---|
| `IDQ-MVP-000-GOV` | CRITICAL | XS | `business_analyst` | DONE — HISTORICAL GOVERNANCE | None |
| `IDQ-MVP-010-BASELINE` | CRITICAL | M | `qa_tester` | DONE — VERIFIED `0e194152`; `0946bde` RECONSTRUCTED | `IDQ-MVP-000-GOV` |
| `IDQ-MVP-020-STORE` | CRITICAL | L | `developer` (store lane) | REOPENED — LOCAL CONTRACT / FRESH QA PENDING | `IDQ-MVP-010-BASELINE` |
| `IDQ-MVP-030-DISPATCHER` | CRITICAL | M | `developer` (dispatcher lane) | REOPENED / BLOCKED — REAL EXECUTOR ROUTE PENDING | `IDQ-MVP-010-BASELINE` |
| `IDQ-MVP-040-WORKER` | CRITICAL | L | `developer` (worker lane) | REOPENED / BLOCKED — REAL DAEMON ROUTE PENDING | `IDQ-MVP-020-STORE`, `IDQ-MVP-030-DISPATCHER` |
| `IDQ-MVP-050-SUPERVISOR` | CRITICAL | M | `developer` (supervisor lane) | REOPENED / BLOCKED — REAL DAEMON ROUTE PENDING | `IDQ-MVP-020-STORE`, `IDQ-MVP-040-WORKER` |
| `IDQ-MVP-060-INTEGRATION` | HIGH | M | `developer` (integration lane) | REOPENED / BLOCKED — CROSS-RUNTIME HANDOFF PENDING | `IDQ-MVP-020-STORE`..`IDQ-MVP-050-SUPERVISOR` |
| `IDQ-MVP-070-QA` | CRITICAL | L | `qa_tester` | REOPENED — FRESH QA PENDING | `IDQ-MVP-060-INTEGRATION` |
| `IDQ-MVP-080-FOUR-ALIAS` | CRITICAL | M | `qa_tester` (receipt executor) | BLOCKED — REAL PATH + FRESH ACTIVATION PENDING | `IDQ-MVP-070-QA`, `IDQ-OP-050-PREFLIGHT` |
| `IDQ-MVP-090-SEAL-GOV` | HIGH | S | `business_analyst` | BLOCKED | `IDQ-MVP-080-FOUR-ALIAS` |

### `IDQ-MVP-000-GOV` — Governance freeze

- **Severity / Work Effort**: `CRITICAL / XS`
- **Current classification**: `DONE — HISTORICAL GOVERNANCE`; it does not prove
  current executor, QA, provider, or release readiness.
- **Exact one-editor ownership**: `business_analyst`; only `plans/plan.md` and
  `PROJECT_TASKS.md` for this delimited governance block.
- **Dependencies**: none.
- **Acceptance/evidence**: nine-dimension `APPROVED` grill, exclusions,
  bootstrap boundaries, four-receipt criterion, ticket graph, and
  `DispatchDecision v1` are recorded.
- **Stop condition**: `DONE` once both blocks exist and pre-existing bytes
  remain untouched beneath them.
- **Exclusions**: source/tests/config, staging, commits, push/deploy/cutover.

### `IDQ-MVP-010-BASELINE` — Test-first provenance baseline

- **Severity / Work Effort**: `CRITICAL / M`
- **Verified baseline ownership**: `qa_tester`; commit
  `0e1941528c0c8f49ef50a14fd046db2163d33379` contains only
  `tests/test_idq_mvp_010_release_cycle.py` and
  `plans/test_provenance/idq-mvp-010-release-cycle-baseline.json`.
- **Reconstructed history**: commit
  `0946bdec65173edacbaf4044b4198d55136c33ca` contains the earlier four tests
  plus `plans/test_provenance/idq-mvp-010-baseline.json`; it remains
  `NON_TDD_RECONSTRUCTED` and is not verification evidence.
- **Dependencies**: `IDQ-MVP-000-GOV` (`DONE`).
- **Status**: `DONE — VERIFIED RELEASE-CYCLE BASELINE`
- **Acceptance/evidence**: the exact `0e194152` commit and its two-path tree are
  retained in current ancestry. Historical suite counts do not substitute for
  fresh operational QA.
- **Stop condition**: `READY -> DONE` only when commit SHA and history-guard
  proof exist; otherwise `BLOCKED`, with no source lane released.
- **Exclusions**: all product source, existing tests, docs, config, provider
  execution, and any commit containing a sixth path.

### `IDQ-MVP-020-STORE` — SQLite durable authority

- **Severity / Work Effort**: `CRITICAL / L`
- **Status**: `REOPENED — LOCAL CONTRACT PRESENT / FRESH QA PENDING`. The local
  source in current ancestry is not current runtime or provider proof.
- **Exact one-editor ownership**: store-lane `developer`; only
  `scripts/multiagent_durable_queue.py` (schema migration v1 embedded or
  owned from this module).
- **Dependencies**: `IDQ-MVP-010-BASELINE` (`DONE` and verified).
- **Acceptance/evidence**: WAL/pragma/permission contract, idempotency,
  atomic claim/fence/lease/result/outbox, recovery, and retry/`UNKNOWN`
  boundaries pass the frozen queue test.
- **Stop condition**: stop at the first frozen-test contradiction, ownership
  overlap, or missing verified baseline.
- **Exclusions**: dispatcher, worker, supervisor, legacy queue promotion,
  PostgreSQL/multi-host, tests, docs, push/deploy.
- **Provenance gate**: baseline commit must be an ancestor; every source
  commit must carry `Test-Baseline: <IDQ-MVP-010-BASELINE-SHA>`.

### `IDQ-MVP-030-DISPATCHER` — Bootstrap admission and lifecycle

- **Severity / Work Effort**: `CRITICAL / M`
- **Status**: `REOPENED / BLOCKED`; the real bounded executor route and fresh
  evidence are pending.
- **Exact one-editor ownership**: dispatcher-lane `developer`; only the
  existing multi-account dispatcher module's typed `LocalBootstrapAdmission`
  and `prepared/starting/provider_started/completed` hook surface.
- **Dependencies**: `IDQ-MVP-010-BASELINE` (`DONE` and verified).
- **Acceptance/evidence**: ordinary path stays byte-compatible and `CLOSED`;
  explicit risk-bound ephemeral bootstrap admits only read-only attempt 1,
  preserves unknown/constrained quota, and revalidates fence/decision/snapshot/
  executable/account identity before spawn.
- **Stop condition**: stop on auth/executable/identity ambiguity, fallback,
  quota-health promotion, frozen-test contradiction, or ownership overlap.
- **Exclusions**: store/worker/supervisor, account credentials, billing or
  executable bypass, mutation lanes, fabricated receipts, tests/docs/release.
- **Provenance gate**: baseline commit must be an ancestor; every source
  commit must carry `Test-Baseline: <IDQ-MVP-010-BASELINE-SHA>`.

### `IDQ-MVP-040-WORKER` — Independent root worker

- **Severity / Work Effort**: `CRITICAL / L`
- **Status**: `REOPENED / BLOCKED`; local source presence does not prove a real
  independent daemon route or cross-runtime handoff.
- **Exact one-editor ownership**: worker-lane `developer`; only
  `scripts/multiagent_root_worker.py`.
- **Dependencies**: `IDQ-MVP-020-STORE` (local contract / fresh QA pending) and
  `IDQ-MVP-030-DISPATCHER` (reopened/blocked).
- **Acceptance/evidence**: Root A cannot claim AGY and Root B cannot claim
  Codex; pool/caps/backpressure/circuit/retry rules hold; root/worker
  heartbeats and stale-fence/result rejection pass; post-start ambiguity is
  `UNKNOWN` with no blind retry.
- **Stop condition**: stop on cross-root claim/fallback, duplicate execution,
  raw-stream/secret persistence, provenance failure, or ownership overlap.
- **Exclusions**: supervisor CLI, dispatcher/store edits, tests/docs, external
  release actions.
- **Provenance gate**: baseline commit must be an ancestor; every source
  commit must carry `Test-Baseline: <IDQ-MVP-010-BASELINE-SHA>`.

### `IDQ-MVP-050-SUPERVISOR` — Local lifecycle authority

- **Severity / Work Effort**: `CRITICAL / M`
- **Status**: `REOPENED / BLOCKED`; a real daemon/executor path and fresh
  lifecycle evidence are pending.
- **Exact one-editor ownership**: supervisor-lane `developer`; only
  `scripts/multiagent_root_supervisor.py`.
- **Dependencies**: `IDQ-MVP-020-STORE` (local contract / fresh QA pending) and
  `IDQ-MVP-040-WORKER` (reopened/blocked).
- **Acceptance/evidence**: `doctor/init/start/submit/status/wait/smoke-all/
  seal-bootstrap/stop --drain`, detached PID/instance checks, stale-instance
  fencing, restart recovery, permissions, explicit risk acceptance, expiry,
  seal, and normal-restart `CLOSED` behavior pass frozen tests.
- **Stop condition**: stop on unsafe PID/home/symlink state, unrecorded risk,
  failed drain/fence, missing baseline, or ownership overlap.
- **Exclusions**: implementation-module edits, credential reads, deployment,
  production daemonization/cutover, tests/docs.
- **Provenance gate**: baseline commit must be an ancestor; every source
  commit must carry `Test-Baseline: <IDQ-MVP-010-BASELINE-SHA>`.

### `IDQ-MVP-060-INTEGRATION` — Secret-free four-route integration

- **Severity / Work Effort**: `HIGH / M`
- **Status**: `REOPENED / BLOCKED`; the explicit cross-runtime handoff route is
  now in scope and has not yet produced fresh evidence.
- **Exact one-editor ownership**: integration-lane `developer`; only the new
  secret-free four-alias route/config artifact selected during baseline freeze;
  fixes to `020`..`050` return to their owning editor.
- **Dependencies**: all of `IDQ-MVP-020-STORE`, `030-DISPATCHER`,
  `040-WORKER`, and `050-SUPERVISOR`; each must satisfy the current reopened
  operational gates before integration.
- **Acceptance/evidence**: all four aliases route only to their locked root;
  deterministic crash/replay/outbox/status flows integrate without secrets,
  fallback, duplicate work, or ordinary activation.
- **Stop condition**: stop and bounce to the owning source ticket on any
  source-module fix; stop on secret-bearing config or provenance failure.
- **Exclusions**: edits to `020`..`050` ownership, provider smoke, tests/docs,
  PostgreSQL/multi-host/SSE, push/deploy/cutover.
- **Provenance gate**: baseline commit must be an ancestor; every source/config
  commit must carry `Test-Baseline: <IDQ-MVP-010-BASELINE-SHA>`.

### `IDQ-MVP-070-QA` — Deterministic verification

- **Severity / Work Effort**: `CRITICAL / L`
- **Exact one-editor ownership**: `qa_tester`; the four tests and manifest from
  `010` remain QA-owned but frozen; this ticket collects read-only reports.
- **Dependencies**: `IDQ-MVP-060-INTEGRATION` (reopened/blocked) and source
  freeze.
- **Status**: `REOPENED — FRESH QA PENDING`
- **Acceptance/evidence**: rerun the applicable deterministic queue, daemon,
  cross-runtime handoff, QOBS, capacity, scheduler, receipt-integrity,
  read-only-boundary, ecosystem, and secret-safe gates on the exact candidate.
  Earlier pass counts are historical only.
- **Stop condition**: stop on any failure. A wrong frozen test requires a
  separate superseding test-only baseline; never edit it under this ticket.
- **Exclusions**: source fixes, baseline rewrite, provider smoke, staging/
  commit/push/deploy.

### `IDQ-MVP-080-FOUR-ALIAS` — Real provider proof

- **Severity / Work Effort**: `CRITICAL / M`
- **Exact one-editor ownership**: `qa_tester` is the sole bounded receipt
  executor/recorder; no repository-file edit is permitted.
- **Dependencies**: `IDQ-MVP-070-QA` (reopened), real executor/daemon path, and
  `IDQ-OP-050-PREFLIGHT` (fresh activation not issued).
- **Status**: `BLOCKED — REAL PATH + FRESH ACTIVATION PENDING`
- **Acceptance/evidence**: concurrent read-only jobs show at least one overlap;
  each of `codex1`, `codex2`, `agy1`, and `agy2` yields provider-native safe
  process/session evidence, a validated real `ExecutionReceipt`, and typed
  `WorkResult`; no raw streams, duplicate, or cross-account fallback.
- **Stop condition**: stop the affected alias on `BLOCKED_AUTH`, executable/
  identity failure, malformed/missing receipt/result, or ambiguity. Ticket
  remains incomplete until all four real receipts exist.
- **Exclusions**: fabricated/synthetic receipts, fallback alias, credential/
  billing repair, mutation work, repository edits, push/deploy/cutover.

### `IDQ-MVP-090-SEAL-GOV` — Seal and reconcile governance

- **Severity / Work Effort**: `HIGH / S`
- **Status**: `BLOCKED`; no valid four-alias terminal set or seal evidence
  exists for the current operational graph.
- **Exact one-editor ownership**: `business_analyst`; only `plans/plan.md` and
  `PROJECT_TASKS.md` after source freeze and acceptance evidence.
- **Dependencies**: requires `IDQ-MVP-080-FOUR-ALIAS` to become `DONE` with all
  four receipts real; it is currently blocked.
- **Acceptance/evidence**: bootstrap seal receipt exists; ordinary restart is
  `CLOSED`; board/plan reflect verified evidence; ecosystem sync/check and
  secret-safe review evidence are recorded without a release claim.
- **Stop condition**: stop if any receipt is absent, bootstrap is unsealed,
  ordinary activation is open, sync/check fails, or a push/deploy/cutover is
  requested without separate authorization.
- **Exclusions**: source/tests/config, receipt creation, evidence deletion,
  MAREF C1/C2 closure, push, deploy, publish, production cutover.

### `IDQ-MVP-080` conditional provider-test authorization — `IDQ-MVP-080-AUTH-01`

**Recorded**: `2026-08-29T00:57:56+07:00` (Asia/Bangkok)
**Authority**: the owner expressly requested: `start Codex/AGY provider` for
`IDQ-MVP-080`, across `codex1`, `codex2`, `agy1`, and `agy2`, one attempt per
alias, read-only, no retry/fallback, with receipt plus `WorkResult` binding.
**Status**: `SEALED / EXPIRED — NOT DISPATCH AUTHORITY`
**Non-secret risk record**: `RISK-IDQ-MVP-080-20260829-01`; expiry/TTL is the
earlier of `2026-08-29T04:57:56+07:00`, a root-session/control-process restart,
or the first terminal outcome for every listed alias. `IDQ-MVP-080-AUTH-01` is
sealed at its recorded expiry and cannot be renewed, replayed, inherited by
`AUTH-02`, or used for another alias/attempt.

This was a historical narrow supersession for `IDQ-MVP-080-FOUR-ALIAS`. Its
expiry restores the ticket to `BLOCKED`; it does not authorize a current
preflight or dispatch. It does not supersede prior attempt history, any other
ticket, Rule 17/18, ordinary `S5`/`CLOSED`/activation-prohibited behavior, or
any credential, billing, deployment, publication, push, mutation, or raw-data
boundary.

- **Safe objective**: each alias independently performs one bounded,
  non-sensitive repository-inventory review and returns only Result Contract v2
  metadata. The provider prompt, result, and all commands must be read-only;
  no file, Git, account, configuration, secret, or provider setting may change.
- **Fixed aliases and budget**: `codex1`, `codex2`, `agy1`, and `agy2` are four
  separate lanes, each with `attempt=1`, `max_attempts=1`, one lane, and no
  fallback, substitution, reroute, chaining, or automatic/manual retry.
- **Required fresh preflight, per alias**: before process creation, validate a
  current safe quota band (unknown, contradictory, below-threshold, or stale is
  a stop), effective alias identity/executable without reading credentials,
  enforced read-only runtime/sandbox path, a new Rule 18 `DispatchDecision` and
  non-placeholder Rule 11 scheduling snapshot bound to this alias/attempt,
  unexpired one-use lease/risk record, and an unused nonce. Validate all
  bindings before nonce consumption; atomically consume the nonce only at the
  irreversible start boundary.
- **Receipt/evidence boundary**: validate a provider-native `ExecutionReceipt`
  and normalized typed `WorkResult` independently, with matching ticket,
  alias, attempt, decision/snapshot/nonce bindings and digest. Retain only safe
  receipt metadata, hashes/counts, and the typed result. Never retain, print,
  persist, or reconstruct raw provider streams, credentials, account IDs,
  paths, cookies, or prompt/output bodies. Any AGY success is described only
  as `validated in-process only`.

| Alias | Terminal stop condition | Required terminal record |
|---|---|---|
| `codex1` | any failed/ambiguous preflight, start, receipt, or `WorkResult` validation | typed `BLOCKED`/`NEEDS_HITL` or valid bound receipt/result; seal this alias with no retry |
| `codex2` | same; its outcome never authorizes a substitute or another attempt | typed terminal record; seal this alias with no retry |
| `agy1` | same, including malformed native event/final result or absent in-process validation | typed terminal record; seal this alias with no retry |
| `agy2` | same, including malformed native event/final result or absent in-process validation | typed terminal record; seal this alias with no retry |

**Current hold**: `IDQ-MVP-070-QA` is reopened, the real executor/daemon route
is pending, and `AUTH-01` is sealed. The separate `AUTH-02` approval intent at
the top of this file carries no active TTL, nonce, or lease. `IDQ-OP-050-PREFLIGHT`
must prove every fresh gate before any process creation. `DONE` for
`IDQ-MVP-080` still requires four real, separately valid receipts and
`WorkResult`s; this historical record claims neither current readiness nor
provider execution.

<!-- IDQ-MVP-BOARD-20260828:END -->

<!-- FIVE-POOL-CAPACITY-20260829:START -->
## Sprint CAPACITY-5POOL — Five-Pool Dual-Root Capacity Architecture (`TICKET-CODEX3-SUPPORT`)

**Historical record**: the statuses and verification counts in this 2026-08-29
capacity block describe that checkpoint only. They are not fresh current IDQ
operational or production evidence; current IDQ truth is at the top of this
file.
**Grill Status at that checkpoint**: `APPROVED` in `plans/plan.md`.
**Dual-Root Topology**:
- **Root A (Codex Root)**: Controls 3 isolated Codex pools (`codex1`, `codex2`, `codex3`). Emits typed inter-root requests to Root B.
- **Root B (AGY Root)**: Controls 2 isolated AGY pools (`agy1`, `agy2`). Manages AGY worker queues, capacity leases, and returns typed outcomes to Root A; Root A does not directly spawn AGY.

| Ticket | Severity | Work Effort | One editor/executor | Status | Dependencies |
|---|---|---|---|---|---|
| `TICKET-CODEX3-SUPPORT` | HIGH | M | `business_analyst` (governance) / `developer` (runtime integration) / `qa_tester` (verification) | HISTORICAL DONE — VERIFIED AT 2026-08-29 CHECKPOINT | historical `IDQ-MVP-070-QA`, `Rule 19A` |

### `TICKET-CODEX3-SUPPORT` — Five-Pool Dual-Root Capacity Architecture (`codex1`, `codex2`, `codex3`, `agy1`, `agy2`)

- **Severity / Work Effort**: `HIGH / M`
- **Ownership**:
  - Governance & Specification: `business_analyst` (`PROJECT_TASKS.md`, `plans/plan.md`, `HANDOFF.md`, `.agents/rules/19-agy-capacity-governance.md`).
  - Runtime Capacity Admission: `developer` (`.agents/config/s3_capacity_policy.json`, `scripts/multiagent_capacity.py`).
  - Verification & Contract QA: `qa_tester` (`tests/test_multiagent_capacity.py`, `tests/test_multiagent_ticket_scheduler.py`).
- **Dependencies at that checkpoint**: historical `IDQ-MVP-070-QA` (`DONE`)
  and Rule 19A Five-Pool Dual-Root update. Current `IDQ-MVP-070-QA` is reopened.
- **Status**: `DONE — VERIFIED`

#### Dual-Root Pool Allocations:
- **Root A (Codex Root)**:
  - `codex1`: Primary implementation/integration writer lane.
  - `codex2`: QA verification / read-only review / contract evaluation lane.
  - `codex3`: Overflow / specialized reasoning / dedicated evaluation lane.
- **Root B (AGY Root)**:
  - `agy1`: Flash-first triage, retrieval, deterministic calculations, test planning lane.
  - `agy2`: Independent review on frozen diffs / high-risk evidence verification lane.

#### Five-Pool Isolation & Governance Rules:
1. **Per-Pool Isolation**: Quotas, rate limits, capacity leases, burn-rate ledgers, and circuit breakers are isolated per account alias across all five pools (`codex1`, `codex2`, `codex3`, `agy1`, `agy2`). No shared or inferred quota pool; zero cross-account borrowing.
2. **Dual-Root Boundaries**: Root A emits typed requests to Root B; Root B returns typed outcomes. Root A never directly spawns AGY subagents; Root B never executes Codex commands.
3. **Capacity Admission**: Bound execution requires a valid `CapacityLease` validating pool/account alias, request ID, owner/lane, request budget, TTL, model floor, and policy digest.
4. **Fail-Closed States**:
   - `S3`: Normal admission (1-2 lanes per account, Flash-first triage, bounded evidence).
   - `S4`: Capacity pressure, elevated burn, backpressure, or circuit open (queue or stop affected pool).
   - `S5`: Unknown/contradictory quota, invalid receipt/result, or ownership conflict (fail closed, `required_human_review=True`, hold unresolved work).

#### Acceptance Criteria:
- [x] Five-pool dual-root topology clearly defined in governance documentation (`.agents/rules/19-agy-capacity-governance.md`, `PROJECT_TASKS.md`, `plans/plan.md`, `HANDOFF.md`).
- [x] Root A (`codex1`, `codex2`, `codex3`) and Root B (`agy1`, `agy2`) boundaries enforce typed inter-root request/response flow with zero direct cross-root process spawning.
- [x] Strict per-pool isolation for quotas, leases, burn rates, and circuit breakers with zero cross-pool inference.
- [x] Capacity admission, lease validation, fail-closed S3/S4/S5 states, and quality floor requirements enforced across all 5 pools.
- [x] Runtime policy JSON (`.agents/config/s3_capacity_policy.json`) and capacity engine (`scripts/multiagent_capacity.py`) expanded to support `codex3` with explicit pool limits (Developer lane).
- [x] Comprehensive unit and integration test suite verifies 5-pool isolation, lease lifecycle, and dual-root contracts (QA lane).
- [x] Ecosystem synchronization check (`python3 scripts/sync_ai_agent_ecosystem.py --sync`) passes cleanly.

#### Verified Evidence:
- 392/392 multiagent & IDQ tests passing (`pytest tests/test_multiagent*.py tests/test_idq*.py tests/test_inter_root_dispatch_contract.py`).
- 5-pool capacity architecture (`codex1`, `codex2`, `codex3`, `agy1`, `agy2`) complete and operational across `.agents/config/s3_capacity_policy.json`, `scripts/multiagent_capacity.py`, and `.agents/rules/19-agy-capacity-governance.md`.
- 0 errors in py_compile (`python3 -m py_compile scripts/*.py tests/*.py`).
- AI agent ecosystem synchronized and verified (`python3 scripts/sync_ai_agent_ecosystem.py --check`).

#### Stop Condition:
Governance documentation is sealed when rule, plan, task board, and handoff reflect the 5-pool dual-root architecture. Implementation lanes require separate dispatch with explicit one-editor ownership.

<!-- FIVE-POOL-CAPACITY-20260829:END -->

<!-- SPARK-MODEL-GOVERNANCE-20260829:START -->
## Sprint SPARK-GOV — Fail-Closed Spark Model Governance & Regression Suite (`TICKET-SPARK-GOV`)

**Grill Status**: `DONE / VERIFIED` in `plans/plan.md`.
**Governance Posture**: Role-restricted (`devops`, `code_reviewer`), phase-restricted (`qa`, `review`, `release`, `operations`), and `reference_profile` support across quality floors under policy version `2026-08-29.1` (with backwards compatibility for `2026-08-26.1`).

| Ticket | Severity | Work Effort | One editor/executor | Status | Dependencies |
|---|---|---|---|---|---|
| `TICKET-SPARK-GOV` | HIGH | S | `developer` (policy engine) / `qa_tester` (regression suite) / `business_analyst` (governance) | DONE — VERIFIED | `TICKET-CODEX3-SUPPORT`, `Rule 18` |

### `TICKET-SPARK-GOV` — Fail-Closed Spark Model Governance (`gpt-5.3-codex-spark`)

- **Severity / Work Effort**: `HIGH / S`
- **Ownership**:
  - Runtime Policy & Guard: `developer` (`scripts/multiagent_prompt_command.py`, `scripts/agent_quota_status_guard.py`, `.agents/config/multiagent_model_policy.yaml`).
  - Verification & Test Suite: `qa_tester` (`tests/test_spark_model_governance.py`, `tests/test_multiagent_prompt_command.py`).
  - Governance & Ecosystem Alignment: `business_analyst` (`PROJECT_TASKS.md`, `plans/plan.md`, `HANDOFF.md`).
- **Dependencies**: `TICKET-CODEX3-SUPPORT` (`DONE`), Rule 18 Model Effort Policy.
- **Status**: `DONE — VERIFIED`

#### Governance & Constraint Rules:
1. **Role Restriction**: `gpt-5.3-codex-spark` is restricted exclusively to `devops` and `code_reviewer` roles; attempts by unauthorized roles (`developer`, `qa_tester`, `business_analyst`, etc.) fail closed.
2. **Phase Restriction**: Permitted only in `qa`, `review`, `release`, and `operations` lifecycle phases; rejected in `planning` and `implementation`.
3. **Reference Profile Resolution**: Quality floor validation supports `reference_profile` resolution mapping restricted profiles back to standard model capability profiles.
4. **Policy Version Backwards Compatibility**: Dual support for policy version `2026-08-29.1` and legacy `2026-08-26.1` across `scripts/agent_quota_status_guard.py` and `scripts/multiagent_prompt_command.py`.

#### Acceptance Criteria:
- [x] Fail-closed validation for `allowed_roles` and `allowed_phases` implemented in `scripts/multiagent_prompt_command.py`.
- [x] Model catalog and quality floors updated with `reference_profile` support in `.agents/config/multiagent_model_policy.yaml`.
- [x] Backwards-compatible policy version support (`2026-08-29.1` and `2026-08-26.1`) in quota guard and prompt command runner.
- [x] 15/15 Spark governance tests passing in `tests/test_spark_model_governance.py` and `tests/test_multiagent_prompt_command.py`.
- [x] 799/799 test suite passing in `tests/`.
- [x] Ecosystem check (`python3 scripts/sync_ai_agent_ecosystem.py --check`) passing cleanly with zero errors.

#### Verified Evidence:
- 15/15 Spark governance tests passing in `tests/test_spark_model_governance.py` and `tests/test_multiagent_prompt_command.py`.
- 799/799 tests passing in `tests/` across unit, integration, and scheduling test suites.
- Policy version `2026-08-29.1` verified with backwards compatibility for `2026-08-26.1`.
- `python3 scripts/sync_ai_agent_ecosystem.py --check` returned 100% PASS across all platform, settings, role map, hook, and rule validations.
- `git diff --check` passed with 0 formatting errors.

#### Stop Condition:
Governance documentation and test verification are sealed when all Spark governance tests and full test suite pass cleanly with ecosystem sync validated.

<!-- SPARK-MODEL-GOVERNANCE-20260829:END -->

# 📌 PROJECT_TASKS.md — Computational Metaphysics Engine
> **Source of Truth for Project Status & Operational Handoff — Central Kanban Board for ALL Project Work**  
> *Last Updated: 2026-08-29 (Asia/Bangkok) — PR #4 is merged into `main` as `98e19b4`; GitHub Actions Deployment Run `33251910604` completed with SUCCESS; Live Endpoints & 33/33 UI Button Regressions verified.*

---

## Sprint PROD-503 — Vercel Gateway Recovery and Remaining Release Concerns

**Current verdict**: `VERCEL UI LIVE / HF IDENTITY RELEASE-GATED / POST-MERGE CI REMEDIATION IN REVIEW`.
The production alias serves merge `85428c8` and proxies the healthy canonical HF
Docker backend. Static identity, LuoPan, and five-viewport visual checks are
green. The backend still exposes `version/git_commit=unknown` because no HF
Docker publish was authorized. Main CI correctly blocks on one stale live test;
the isolated correction retains the closed five-field schema and hardens the E2E
runner against legacy or tampered metadata.

| Ticket | Severity / Effort | Status | Evidence / Next Gate |
|---|---|---|---|
| `TICKET-PROD-503-001A` Vercel gateway config | BLOCKER / XS | DONE — LIVE | Production-only `HF_BACKEND_URL` entry `gTpSlwb3RL3Fr94e` is retained; deployment `dpl_FWVpyuKbY9iWs2rrVxEGKmmp8Qm4` is `READY`, owns the canonical alias, and returns `x-deploy-sha=85428c8` |
| `TICKET-PROD-503-001B` API recovery QA | BLOCKER / S | DONE — LIVE | `/health` is `200/status=ok`; canonical HF Docker health is `200`; post-merge LuoPan live E2E passed `8/8`; canonical static version and all mirrored UI assets agree at `1.0.0.e06b224` |
| `TICKET-PROD-503-001C` publisher/provenance gate | CRITICAL / M | DONE — MERGED | Docker payload dry-run passes; payload source modes match frozen `100644`; release metadata uses the closed five-field immutable schema; history guard passes all active/superseded baselines |
| `TICKET-PROD-503-001D` mobile visual/accessibility | HIGH / S | DONE — LIVE | Post-merge deterministic audit passed all five canonical viewports with zero overflow, overlaps, out-of-bounds, clipping, contrast failures, or indeterminate contrast |
| `TICKET-PROD-503-001E` HF runtime identity | HIGH / S | DONE — MERGED / PENDING HF RELEASE | Runtime fallback is merged, but live HF remains `version/git_commit=unknown` until a separately authorized owner-gated Docker publish |
| `TICKET-PROD-503-001F` release closure | CRITICAL / XS | DOING — HF + POST-MERGE CI GATED | PR `#2` merged as `85428c8` and Vercel UI release is verified. Remaining gates are the isolated stale-test correction, explicit HF Docker publish authorization, then exact backend identity verification |
| `TICKET-PROD-503-001G` Vercel Preview retirement | MEDIUM / XS | DONE — MERGED | Test-only baseline `062289e` preceded the `vercel.json` policy; `*` auto-deploy is disabled while `main` remains enabled. All canceled preview artifacts were deleted and the current preview deployment count is zero |
| `TICKET-PROD-503-002A` post-merge identity CI correction | HIGH / S | DOING — LOCAL GREEN / REVIEW GATED | Main runs `33054316810` and `33054316732` exposed the stale `commit/timestamp` network-test expectation after the canonical UI became live. Test-only baseline `2b195a6` recorded `3 failed, 5 passed`; source commit `45c635e` makes the focused matrix `8 passed` and makes `run_prod_version_e2e.py` reject legacy or digest-tampered metadata. No production source or frozen test was silently rewritten |

**Rollback anchors**:

- Remove only Vercel environment entry `gTpSlwb3RL3Fr94e` to restore the prior
  absent-variable state.
- Prior production deployment `dpl_2gEijnyqedG1Bn2XVcWZvWJ6amaZ` remains the
  immediate Vercel rollback deployment; never delete either production deployment.
- The hotfix branch is additive. Revert owned source commits while retaining
  test baselines and supersede history; no HF rollback is needed because no HF
  publish occurred in this incident.

**TDD-trap prevention evidence**: the first executable-mode test contradicted
the already-frozen `100644` release contract. Source work stopped; baseline
`7741b4f` was preserved, and test-only baseline `e3f7ebc` explicitly superseded
it before remediation. No baseline was amended, squashed, deleted, or silently
rewritten.

---

## Sprint TPG — Test-First Git Provenance and TDD-Trap Prevention

**Grill status**: `APPROVED` from the signed implementation plan. The initial
scope covered local repository code, tests, Git history, CI definition,
governance, and docs. Follow-up exact authorization covered pushing the feature
branch and activating the `Test Provenance` required check for `main`; the
subsequent `continue` authorized PR creation and bounded clean-checkout CI
remediation. No merge, deploy, provider/AGY execution, secret action, or
production mutation was authorized or performed.

| Ticket | Severity / Effort | Owner | Status | Evidence / Dependency |
|---|---|---|---|---|
| `TICKET-TPG-000` | CRITICAL / XS | orchestrator | DONE — REMOTE EVIDENCE | Recovery snapshot `ebfeee9` is pushed on `recovery/pre-test-provenance-20260827`, explicitly `NON_TDD_RECONSTRUCTED`; both remote full-suite jobs restored and verified the immutable ref |
| `TICKET-TPG-001` | CRITICAL / M | developer | DONE — LOCAL | Original baseline `b84989d` is preserved through cutoff `49f81bf`; full QA exposed a workflow-inventory design trap, so test-only baseline `4e13490` explicitly superseded it. Final test SHA-256 `72bc50d7cb661e6fa806eea4c12a338faebf67cbae22ba03d25294ecb15d8645`; source commits `f012519`, `83ce2a0`, `3179919` |
| `TICKET-TPG-002` | HIGH / S | business_analyst | DONE — LOCAL | Test-only baseline `11ff774` captured `2 failed`; generated skill mirrors were the only sync mutations in `49f81bf`; final SHA-256 `da116624ff7db828987c6ec1889760a1354055faa8349e24f04da71363ed2362`; ecosystem check passes |
| `TICKET-TPG-003` | CRITICAL / S | qa_tester | DONE — LOCAL | Focused workflow/provenance matrix `98 passed`; full QA `1275 passed, 12 warnings`; aggregate history verified 3 baseline records with the original cutoff preserved; secret scan 0/1,954 |
| `TICKET-TPG-004` | CRITICAL / XS | repository owner | DONE — REMOTE POLICY | Initial activation receipt used branch SHA `77e373ab41adf32ee18d552e8e214c1eb09fa324`; current PR head is recorded in TPG-006. Active ruleset `Require Test Provenance` (`21626253`) applies to `refs/heads/main`, requires exact context `Test Provenance`, uses strict mode, has no bypass actors, and reports `current_user_can_bypass: never` |
| `TICKET-TPG-005` | CRITICAL / XS | code_reviewer | DONE — LOCAL | `code_reviewer.py --review --use-python` returned `READY_FOR_PROD`; full suite `1275 passed`; TPG-001 baseline `4e13490`, manifest, ticket, and frozen hash all verified |
| `TICKET-TPG-006` | CRITICAL / S | developer / qa_tester | DONE — REMOTE QA | Initial PR CI exposed 15 clean-checkout failures. Test-only baseline `4c08782` recorded `3 failed, 4 passed`; atomic source commits `ef3557c` and `f759004` preserved its 7 frozen files. Local full suite passed `1278` with 12 warnings. GitHub runs `33043972950` and `33043972995` passed; remote provenance artifact reports `PASSED`, `issues: []`, and 10 verified test files across 4 baselines |

**Platform boundary**: native `spawn_agent` pre-spawn enforcement remains
`BLOCKED` under `DSG-009A` until the platform exposes an authoritative hook and
receipt API. This gate catches repository history/merge violations but does not
claim native runtime interception.

**Remote enforcement state**: repository ruleset `21626253` is authoritative
on GitHub. PR `#1` was merged as `db1231e430c39360226d6289afa8a4e665a0cbb1`
after required job `Test Provenance` passed. The canceled preview was not a
required context. Main Unified CI run `33048014471` initially failed only on
the live 503, then passed every job after the production gateway configuration
was restored. Native pre-spawn enforcement remains a separate blocked platform
boundary.

---

## 🚀 Quick-Start Commands (สำหรับผู้ช่วย AI หรือ Account ถัดไป)

```bash
cd /Users/kimlenglim/Project/HoroConsultant

# === RUST NATIVE CI/CD TOOLS ===

# 1. Native Rust Integration Test Suite (2 integration tests: vector search)
export PATH="/Users/kimlenglim/.agy-account-1/.rustup/toolchains/stable-aarch64-apple-darwin/bin:$PATH"
export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
export RUSTFLAGS="-C link-arg=-undefined -C link-arg=dynamic_lookup -L /opt/homebrew/opt/python@3.14/Frameworks/Python.framework/Versions/3.14/lib -l Python3.14"
cd rust_core
cargo test
# Optional runtime suite: 12 checks; start horo_server first to exercise its health check.
cargo run --bin regression_runner
cd ..

# 2. Rust Code Reviewer & Safety Auditor Binary (Pre-Deployment Audit)
python3 project/core/code_reviewer.py --review
# OR Direct Rust Binary:
./rust_core/target/release/code_reviewer

# 3. Rust Agent & Governance Spec Sync Check Binary
python3 scripts/sync_sdlc_agents.py --check
# OR Direct Rust Binary:
./rust_core/target/release/sync_sdlc_agents

# 4. Codex Agent Compatibility Sync Check
python3 scripts/sync_codex_agents.py --check

# 5. Rust Atomic Prometheus Observability Collector Test
python3 -c "import rust_core; print(rust_core.generate_prometheus_metrics_rust(120.0))"

# 6. Rust SVG Chart Rendering Engine Test (BaZi, ZiWei, Zodiac, QiMen, XuanKong)
python3 -c "from project.core.svg_generator import generate_bazi_svg; print(generate_bazi_svg({'day_master': {'stem': '庚'}}))"

# 7. Rust Astrological Consistency Audit (PyO3 Accelerated)
python3 scripts/audit_astrological_consistency.py

# 8. Pre-Deployment Safety Audit & Secret Scan (Rust Rayon Parallel)
python3 project/core/code_reviewer.py --scan-secrets

# 9. Full Python Pytest Suite (Current local status is in the evidence snapshot)
python3 -m pytest -q project/tests/
```

> **Current release state is captured by the latest evidence block below; historical ticket checkboxes above may reflect earlier completed milestones.**

### Documentation Authority Rules (current)

- The newest timestamped evidence artifact outranks older prose or historical release notes.
- A deployment is not considered healthy from a previous `200` result when the newest canonical probe is `404/503`.
- External deployment, production E2E, credential, and secret-sync actions remain separate HITL checkpoints; do not combine them with local QA.
- Each checkpoint below must produce its own evidence before the next checkpoint starts. If quota is low, stop after the current checkpoint and update `TICKET-META-008` only.

### Central documentation map (current)

`PROJECT_TASKS.md` is the sole authority for active ticket status, ownership,
dependencies, acceptance criteria, and operational handoff. Other documents
serve narrower purposes and must link here instead of copying the active board:

| Document | Canonical role | Must not duplicate |
|---|---|---|
| `HANDOFF.md` | Current-session resume context, constraints, blockers, and safe commands | Full ticket definitions or historical sprint logs |
| `plans/plan.md` | Decision records, grill reports, and implementation-plan rationale | Current ticket status tables |
| `plans/todo_tasks_plan.md` | Traceability index for the retired TODO workstreams | Active backlog or completion evidence |
| `plans/metaphysics_learning_roadmap.md` | Domain/product learning roadmap | Release status and ticket ownership |
| `plans/question_forecast_alignment_spec.md` | Benchmark contract and evaluation rubric | Runtime release claims |
| `project_tickets.md` | Compatibility pointer only | Any ticket/status content |

When two documents disagree, use the latest evidence linked from this board,
then update the narrower document or mark its text historical. Do not create a
second task board or add ticket definitions to a plan/pointer file.

## ✅ Latest Local & Remote Evidence Snapshot (2026-08-29 19:15)
- PR #4 merged into `main` (`98e19b4`) with 100% clean checkouts and complete CI matrix pass.
- GitHub Actions Deployment Run `33251910604` on `main` → `SUCCESS`.
- UI Button Regression suite (`python3 scripts/run_button_regression.py`) → `33/33 PASSED` (`project/tests/button_regression_report.json`).
- Live production endpoints verified: Vercel Static UI (200), Version JSON (200), HF Docker Backend Health (200), BaZi Four Pillars calculation (200), Admin Provider Pools (200, `[ZERO-COST POLICY: ACTIVE]`).
- Full PyTest test suite (`python3 -m pytest -q project/tests/ tests/`) → `1,833 passed`, `0 failed`, `12 warnings` (100% green).
- Zero-Cost AI Provider Pipeline (`project/tests/test_zero_cost_pipeline.py`, `project/tests/test_semantic_cache.py`) → `51 passed`, 0ms circuit breaker bypass on HTTP 429 verified.
- Multiagent & IDQ test suite (`tests/test_multiagent*.py`, `tests/test_idq*.py`) → `392 passed`.
- Spark model governance (`tests/test_spark_model_governance.py`) → `15 passed`.
- Pre-deployment safety audit & secret scan (`python3 project/core/code_reviewer.py --scan-secrets`) → PASSED: `0` leaks across `2,186` files.
- `python3 scripts/sync_ai_agent_ecosystem.py --check` → passed (all 12 platform files, hooks, 17 rules, 7 Antigravity definitions, and 19 Codex definitions synchronized, 0 drift).
- `python3 scripts/sync_sdlc_agents.py --check` → passed (all Antigravity definitions synchronized).
- `python3 scripts/sync_codex_agents.py --check` → passed (all Codex definitions synchronized).
- `HF_BACKEND_SPACE_ID="pphothidaen/horoconsultant-core-backend" HF_TOKEN="[REDACTED]" python3 scripts/publish_space_hf.py --space-id "$HF_BACKEND_SPACE_ID" --sdk docker` historically failed due `HF Token authentication failed: [Errno 8] nodename nor servname provided, or not known` (this runtime could not resolve `huggingface.co` hosts).
- `python3 -m pytest -q project/tests/` (full suite) → `582 passed`, `8 skipped`, `12 warnings` in 8.62s (fresh revalidation).
- `python3 scripts/run_quality_gate.py` → READY (`100% PASSED`, 4/4 stages).
- `cd rust_core && cargo test --no-default-features --test test_vector_search` → `2 passed`.
- `HF_BACKEND_URL=https://core-backend.hf.space HF_STATIC_CDN_URL=https://static.hf.space python3 scripts/run_live_health_verification.py --json-output project/tests/backend-release-check.json` → `0/3` checks passed (`core-backend.hf.space` is not the configured canonical target for this run).
- `python3 scripts/run_button_regression.py` → `25/25` passed, report written to `project/tests/button_regression_report.json`.
- `python3 scripts/run_vercel_prod_curl_regression.py --url https://horo-consultant-psi.vercel.app --use-python` → `2/3` with canonical back-end unavailable fallback (`POST /api/v1/bazi/interpret` `503`).
- `python3 -m pytest project/tests/test_ai_provider_router.py project/tests/test_ai_provider_router_tier3.py project/tests/test_llm_multirouter.py` → `19 passed`.
- `python3 -m pytest project/tests/test_observability.py project/tests/test_rust_extensions.py` → `25 passed`.
- `python3 -m pytest project/tests/test_web_regression.py` → `11 passed`, `4 skipped`.
- `python3 -m pytest -q project/tests/test_post_train_fuse.py project/tests/test_api_router_external.py project/tests/test_ingest_vault.py project/tests/test_swiss_ephemeris.py` → `19 passed` (focus: TODO workstream closure evidence for Tasks 1,2,3,4,6). Updated on 2026-08-17 at 22:53:25 after revalidation.
- Focused plan/workstream regression revalidation on 2026-08-21 → `59 passed`, `1 warning` across CI workflow, skill governance, observability, provider routing, model fusion, ingestion, and Swiss Ephemeris tests.
- Newly closed local roadmap artifacts: `scripts/mian_xiang_vision.py` (optional Gemini Vision adapter) and `project/tests/test_svg_i18n.py`; focused vision/i18n regression → `33 passed`.
- `python3 - <<"PY"` DNS probe on key external hosts (`project/tests/network-dns-probe.json`) was used for historical context; canonical HF outcomes remain mixed (`horo-consultant-psi.vercel.app` `200`, `pphothidaen-horoconsultant-core-backend.hf.space` `503`, `pphothidaen-horoconsultant-core-backend.static.hf.space` `404`) and authoritative runtime failures in this pass come from direct socket/DNS resolution errors.
- `project/tests/local_release_readiness_2026-08-17.md` contains the full local evidence matrix from this pass.
- Human-in-the-Loop operating procedure and escalation matrix: [`docs/HITL_OPERATING_GUIDE.md`](docs/HITL_OPERATING_GUIDE.md).
- `python3 project/core/code_reviewer.py --scan-secrets` → PASSED: `0` leaks across `1,507` files (2026-08-21 15:43).
- `python3 scripts/sync_sdlc_agents.py --check` → passed again on 2026-08-22 (all Antigravity definitions synchronized).
- `python3 scripts/sync_ai_agent_ecosystem.py --check` → passed on 2026-08-22 (platform files, Claude hooks/rules, Antigravity sync, and all `17` Codex agent definitions synchronized).
- `python3 -m pytest -q project/tests/test_agent_quota_status_guard.py project/tests/test_live_health_verification.py project/tests/test_synthetic_health_monitor.py project/tests/test_mian_xiang_vision.py project/tests/test_post_train_fuse.py project/tests/test_svg_i18n.py project/tests/test_web_regression.py project/tests/test_codex_client.py project/tests/test_agent_configurations.py` → `45 passed`, `4 skipped`, `1 warning` on 2026-08-22.
- `PYTHONPYCACHEPREFIX=/private/tmp/horo_pycache python3 -m py_compile .agents/hooks/pre_tool_check.py .claude/hooks/pre_tool_guard.py scripts/agent_quota_status_guard.py scripts/synthetic_health_monitor.py scripts/run_live_health_verification.py project/api_router.py project/routers/v2.py` → passed on 2026-08-22.
- CP-01 revalidation after `.github/workflows/production_monitor.yml` Azure-only backend selection: `python3 -m pytest -q project/tests/` → `642 passed`, `8 skipped`, `12 warnings`; Azure release tests → `9 passed`; sync/governance tests → `7 passed` (2026-08-22).
- `python3 scripts/agent_quota_status_guard.py --remaining-percent 9 --enforce` → warning emitted for `<10%` quota and confirmed required handoff markers in `PROJECT_TASKS.md` and `plans/plan.md`.
- `python3 project/core/code_reviewer.py --scan-secrets` → PASSED: `0` leaks across `1,530` files (2026-08-22 18:56).
- `git push origin main` → pushed `056b1aa` to `origin/main` on 2026-08-22.
- GitHub Actions `Unified CI & Quality Audit Pipeline` run `32571990179` for `056b1aa` → `success`.
- GitHub Actions `Hugging Face Docker Backend - Production Deployment` run `32571990206` for `056b1aa` → static publish `success`, Docker API backend publish `success`, final verification `failure` (HF Space paused).
- Vercel production verification 2026-08-22: `HF_BACKEND_URL=https://horo-consultant-psi.vercel.app HF_STATIC_CDN_URL=https://horo-consultant-psi.vercel.app python3 scripts/run_live_health_verification.py --json-output project/tests/backend-release-check-vercel-2026-08-22.json` → `3/3` checks passed (static UI 200, backend `/health` 200, deterministic API 200); HF Space remains paused, Vercel serves as verified production fallback.
- `HF_BACKEND_SPACE_ID="pphothidaen/horoconsultant-core-backend"` Space is paused/unhealthy; canonical HF checks remain blocked until maintainer restarts the Space. Vercel is the verified fallback endpoint.

---

## 📊 TASK BOARD (KANBAN)

<!-- AGY-CAPACITY-S3:START -->
## SPRINT: S3 AGY Capacity Governance Refactor — 2026-08-27
**Grill Gate Status**: OPTION C RECORDED; CONSERVATIVE FALLBACK ONLY; local admission plus pressure controls are complete, provider probing is stopped, and no portable runtime/provider proof exists.
**Decision**: Adopt four isolated quota pools (`agy1`, `agy2`, `codex1`, `codex2`) with CapacityLease admission, per-account AGY cap 3, operational nesting depth 2-3, Flash-first triage, Root A typed requests, and Root B AGY queue/worker ownership. Six AGY workers remains theoretical only.
**Implementation boundary**: This BSA lane creates the new S3 skill/rule and records the decision. It does not implement runtime leases, provider queues, quota probes, dispatch changes, or account actions.

**Current handoff (APPROVED — OPTION C ONLY)**: HITL-4 one-shot probing of `agy1` and `agy2`
returned empty sanitized captures for both aliases. Do not request HITL-5 for
the same command or a version-only sanitizer change. The next evidence path is
Option C is human-supplied and recorded, but retain
`quota_status: unknown`, `concurrency_status: unknown`,
`provider_execution: S5`, `dispatcher_execution: CLOSED`, and
`activation_prohibited: true`.

Option C is now recorded from human-supplied sanitized usage observations at
`2026-08-28T06:47:29Z`: `agy1` and `agy2` each reported Gemini weekly
`63.39%`, Gemini five-hour `99.67%`, and Claude/GPT weekly `0.00%`.
Concurrency remains unknown; these are time-bound observations, not portable
provider receipts or entitlement proof.

**Conservative fallback mode (APPROVED)**: use the completed local burn-rate
ledger, backpressure, and pool-local circuit-breaker controls with a floor of
one worker per account. This is local capacity management only and must not be
reported as provider quota or concurrency proof. Parent/orchestrator review is
not permission to request a new provider HITL, open the dispatcher, or activate
provider execution.

**Parent-review DRAFT reconciliation (metadata-only; pending independent
review)**: A user-supplied structured capture observed at
`2026-08-28T06:47:29Z` was parsed in-process without retaining raw provider
response, account identifiers, credentials, paths, or conversation identifiers.
For each of two aliases, the metadata showed Gemini weekly
`remaining_fraction: 0.6338797807693481` (reset `2026-08-29T17:33:23Z`),
Gemini five-hour `remaining_fraction: 0.9966928958892822` (reset
`2026-08-28T10:29:09Z`), third-party weekly `remaining_fraction: 0` (reset
`2026-08-30T14:11:52Z`), and third-party five-hour `disabled: true`.
Concurrency remains unknown; this is not portable/offline receipt evidence.
Sanitizer v1.4.0 recognizes this nested bucket metadata, but no authorized
lossless bridge exists to strict QOBS v1 because the complete non-derived
`usedPercent`, `remainingPercent`, `reached`, `limit`, `spend`, and `remaining`
contract fields are unavailable and must not be inferred.

The local repair for fabricated empty scheduling-snapshot digests now requires
a valid lowercase SHA-256 across dispatch, direct identity, and receipt-binding
paths; invalid attempts do not consume a nonce and valid reuse remains
replay-protected. Delegated local verification reported 81 passing tests,
compilation, and a scoped diff check. The local repair was independently
reviewed PASS; this documentation remains a DRAFT pending parent review and
acceptance. It does not alter historical ticket facts, the S5/CLOSED/
activation-prohibited block, or the parent-review requirement. No new provider
retry is authorized; a future provider path requires a separate exact HITL with
a genuine complete contract. The one-worker local fallback remains only local
ledger/backpressure/circuit-breaker control, not quota or concurrency
entitlement.

| Ticket ID | Assigned Agent | Severity / Work Effort | Status | Depends On |
|---|---|---|---|---|
| `TICKET-S3-AGY-CAPACITY-20260827` | `business_analyst` | HIGH / S | DONE — DOCUMENTATION | None |
| `TICKET-S3-AGY-CAPACITY-RUNTIME-20260827` | `developer` / `qa_tester` | HIGH / M | SUPERSEDED — BASE ADMISSION ONLY | `TICKET-S3-AGY-CAPACITY-20260827`; pressure contract absent |
| `TICKET-S3-AGY-PRESSURE-CONTRACT-20260828` | `developer` / `qa_tester` | HIGH / M | DONE — LOCAL PRESSURE CONTROLS ONLY | base admission evidence; Rule 17/18 and S3/S4/S5 local gates |
| `TICKET-S3-AGY-DOC-RECONCILIATION-20260828` | `business_analyst` | MEDIUM / XS | DONE — DOCUMENTATION RECONCILIATION | completed local S3 admission/pressure evidence |

### TICKET-S3-AGY-CAPACITY-20260827 | `business_analyst` | [STATUS: DONE — DOCUMENTATION]
**Ownership**: `.agents/skills/agy-capacity-orchestration/SKILL.md`, `.agents/rules/19-agy-capacity-governance.md`, `PROJECT_TASKS.md`, and `plans/plan.md` entries for this decision only.
**Explicit exclusions**: Existing Rule 17/18 and Rule 19 files, all existing skill/rule mirrors and generated catalogs, runtime source/tests/hooks, provider or account execution, secrets, deployment, publishing, push, commit, and unrelated dirty files.

#### Acceptance Criteria
- [x] Four-pool isolation, AGY cap/depth, S3 default, and theoretical-only six-worker boundary are documented.
- [x] CapacityLease fields are separated from burn-rate/circuit-breaker/backpressure policy-ledger admission state.
- [x] Flash-first/Pro-floor routing, Root A/Root B ownership, Rule 17/18 evidence, HITL, and S4/S5 escalation are documented.
- [x] User-attested limits are explicitly separated from runtime-proven limits.
- [x] No existing mirrors or unrelated files are changed.

#### Stop Condition
Stop after the two new canonical governance artifacts and these decision records are written and read-only validation is complete. Runtime enforcement requires a separately authorized implementation ticket.

### TICKET-S3-AGY-CAPACITY-RUNTIME-20260827 | `developer` / `qa_tester` | [STATUS: SUPERSEDED — BASE ADMISSION ONLY]
**Purpose**: Implement and locally verify the capacity lease contract/policy and its scheduler plus dispatcher admission boundaries. This ticket is distinct from the completed documentation-only ticket above.

**Actually completed scope**: `CapacityLease` base contract/policy, pool isolation, per-account worker limits, request-budget/TTL/atomic consumption, replay/tamper checks, scheduler admission, final dispatcher pre-process admission on governed CLI/bound invocation paths, and attributed local test evidence. The previous circuit-breaker, burn-rate, and backpressure completion wording was not supported by an implementation audit and is withdrawn.

**Explicit exclusions**: Provider execution or probes; AGY/Codex account access, `/usage`, `/agents`, quota discovery, credentials/secrets, external network actions, deployment, publishing, commit/push, and any capacity claim derived from configuration or user attestation. Do not change unrelated QOBS work or protected data.

**Preconditions / gates**: Apply Rule 17 ownership, typed receipt/result, and evidence boundaries; apply Rule 18 decision, quality-floor, policy-digest, and pre-process revalidation requirements. On governed CLI/bound invocation paths, S3 admission is allowed only after a valid local policy and lease; S4/S5 conditions must reduce or fail closed rather than reroute. Runtime capacity proof remains absent until a separately authorized provider-native action produces valid evidence.

#### Acceptance Criteria
- [x] Local lease contract/policy rejects cross-account borrowing, owner/scope overlap, expired/replayed/tampered leases, over-budget use, and concurrent over-admission; AGY maximum workers is 3 and Codex limits are explicit rather than inferred.
- [x] Consumption is atomic while a lease is live; release and TTL behavior were covered locally. Circuit-breaker, per-account burn-rate, and S4 backpressure enforcement are not complete here.
- [x] Scheduler and final dispatcher pre-process boundary enforce local admission on governed CLI/bound invocation paths while preserving covered Rule 17 ownership and Rule 18 quality-floor/digest bindings.
- [x] Attributed evidence: capacity-contract worker focused suite passed 7 tests; admission worker suite passed 201 tests; independent QA ran `python3 -m pytest -q tests/test_multiagent_capacity.py tests/test_multiagent_ticket_scheduler.py tests/test_multiagent_prompt_command.py` with `201 passed`, and its scoped diff check passed.
- [x] No provider command/probe/account action, secret operation, deploy, publish, commit, or push occurred under this ticket.

**Evidence boundary**: This partial/base completion proves only filesystem-backed local admission and its test coverage. It does not prove provider quota, provider concurrency, route execution, account capacity, or a provider-native Rule 17 receipt. No provider action occurred.

**Residual design note**: Programmatic `Invocation` keeps `capacity_required=False` as an explicit dry-run/legacy construction option. It is neither provider/runtime proof nor governed admission. The governed CLI execution path acquires and binds a lease before its final dispatcher admission boundary; any future programmatic execution entry point must require the same binding before it can be treated as governed admission.

#### Stop Condition
Superseded by `TICKET-S3-AGY-PRESSURE-CONTRACT-20260828` for the missing local pressure controls. A provider-capacity claim, external probe, or release/integration gate requires a new exact authorization and is not implied by local tests.

### TICKET-S3-AGY-PRESSURE-CONTRACT-20260828 | `developer` / `qa_tester` | [STATUS: DONE — LOCAL PRESSURE CONTROLS ONLY]
**Purpose**: Implement and locally verify the missing per-account pressure contract without changing provider state: burn-rate accounting, S4 backpressure, S5 pool-local circuit breaker, and scheduler plus final dispatcher enforcement.

**In scope**: Runtime source/tests/config necessary for a filesystem-backed local pressure ledger; per-account, non-borrowable burn-rate state; deterministic S4 queue/reduce admission; deterministic S5 circuit-open fail-closed admission; scheduler and final pre-process dispatcher enforcement on governed CLI/bound invocation paths; focused tests and independent QA. `multiagent_model_policy.yaml` is the sole executable model catalog for PromptCommand/AGY routing. `gemini_parity.yaml` is a separate Hermes parity configuration whose legacy/broader Gemini IDs are not executable PromptCommand/AGY routes.

**Explicit exclusions**: Provider commands/probes, account access, quota discovery, model-config changes, secrets, external networking, deployment, publishing, commit/push, and a route inferred from `gemini_parity.yaml`.

#### Acceptance Criteria
- [x] Per-account burn-rate accounting cannot aggregate or borrow across aliases and remains content-free.
- [x] S4 pressure applies typed block/queue admission deterministically; S5 circuit-open state has typed cooldown/manual-reset behavior and fails closed without silent reroute.
- [x] Scheduler and final dispatcher pre-process boundaries enforce the same local pressure contract before governed CLI/bound invocation admission; rejected admission creates no subprocess.
- [x] Attributed evidence: pressure-contract worker ran `pytest -q tests/test_multiagent_capacity.py` with `12 passed` plus `py_compile`; pressure-admission worker combined suite passed `213`; independent QA ran `python3 -m pytest -q tests/test_multiagent_capacity.py tests/test_multiagent_ticket_scheduler.py tests/test_multiagent_prompt_command.py` with `214 passed`; scoped tracked/untracked S3 diff check was clean.
- [x] Final independent gates: `python3 -m pytest -q project/tests/test_ai_agent_ecosystem_sync.py project/tests/test_claude_governance.py` passed `16`; the S3 matrix passed `214`; workspace-root `python3 project/core/code_reviewer.py --scan-secrets` passed after scanning `1,994` files with `0` findings, including current modified/untracked S3 artifacts; tracked and untracked S3 diff checks passed.
- [x] No provider action or executable route discovery from `gemini_parity.yaml` occurred.

**Evidence boundary**: This is filesystem-backed local pressure/admission evidence only. It establishes neither provider quota/concurrency nor account capacity, actual route execution, provider-native receipt, or release readiness; no provider action occurred.

**Integrity boundary**: SHA-256 lease digests are deterministic integrity hashes for local mismatch/tamper detection, not secret-keyed adversarial authentication or a substitute for provider identity/authorization.

#### Stop Condition
The local pressure-control extension is complete. Stop here: it remains neither provider quota/concurrency proof nor authorization for a provider action.

### TICKET-S3-AGY-DOC-RECONCILIATION-20260828 | `business_analyst` | [STATUS: DONE — DOCUMENTATION RECONCILIATION]
**Purpose**: Correct S3 documentation boundaries without changing runtime code or historical ticket status. The 20260827 BSA ticket was originally docs-only; later implementation tickets completed the local base-admission and pressure-control work.

**Verified correction**: Governed CLI/bound invocation admission, not every programmatic spawn, requires a lease. `CapacityLease` binds account/pool, owner/lane, request budget, TTL, quality floor, and policy integrity; per-account burn rate, circuit breaker, and backpressure belong to policy/ledger admission state. `Invocation.capacity_required=False` remains explicit programmatic dry-run/legacy optionality and is neither provider/runtime proof nor governed admission.

**Remaining boundary**: Local S3 contract, admission, and pressure work is complete and must not be duplicated. Provider-native proof is the only separately authorized remaining work.
<!-- AGY-CAPACITY-S3:END -->

## SPRINT: Priority Governance Scheduling — 2026-08-25
**Grill Gate Status**: APPROVED — session HITL recorded (Ref: [`plans/plan.md`](plans/plan.md)); the session approval covers the exact AGY native-protocol remediation reservation. No approver identity is retained.
**Session-Scoped Approval**: approval covers the remaining local priority-sprint remediation, QA, read-only review, and final synchronization/reconciliation. It additionally permits bounded workspace-ticket improvement, refactoring, fixes, and removal of explicitly identified obsolete code/tests. It never authorizes a `/root` glob deletion or broad/unrelated destructive action. Deploy, publish, push, secret/account, external, or destructive actions otherwise require an exact in-scope target and all target-scoped safety gates. None is currently required or used by this sprint; external actions remain unused and target-gated. This approval does not broaden `TICKET-PRIORITY-004` or `TICKET-PRIORITY-005`.
**Dispatch Status**: the completed R5 evidence and review remain frozen at `READY_FOR_PROD`, and the multi-agent standard is operationally accepted. Ticket44 attempt-1 remains immutable `BLOCKED` solely because command3 used the stale governance-test path; command1 passed `151`, command2 passed `70`, command3 exited `4` with no tests, and inventory digest `f372695e92ff025edccc35f47007ce53cea275b39d34c7c1c55c73c026a6889e` is unchanged. Ticket44R2 is now `DONE` on corrected offline evidence. Ticket45 local source commit, metadata21C, packaging commit/push, deploy, and external health/UI actions remain blocked in that order; no release approval or source-commit eligibility is inferred. RC2-004 remains a separate quota-unknown HITL blocker.
**Scheduling Authority**: Rule 11. Historical `Priority`-only fields below remain evidence but are superseded for scheduling.
**Current Stop**: Rule 11 has completed ticket44R2 (`CRITICAL/S`) under the approved `codex1_gateway_review` read-only sandbox. It preserves attempt-1 history and changes only command3 to the tracked `tests/test_hf_release_governance.py`. Ticket45 is the immediate handoff, but remains blocked until a fresh mutation decision/snapshot is issued; metadata21C remains strictly after the immutable local source commit. No staging, commit, push, deploy, publish, credential, secret, or external action occurs in this reconciliation.

| Seq | Ticket ID | Owner | Severity | Work Effort | Model / Reasoning Effort | Status | Depends On |
|---:|---|---|---|---|---|---|---|
| 1 | `TICKET-PRIORITY-001` | `business_analyst` | CRITICAL | XL | `gpt-5.6-sol` / `xhigh` | DONE | None |
| 2 | `TICKET-PRIORITY-002` | `developer` | CRITICAL | L | `gpt-5.6-sol` / `high` | DONE | `TICKET-PRIORITY-001` |
| 3 | `TICKET-PRIORITY-003` | `qa_tester` | HIGH | M | `gpt-5.6-terra` / `high` | DONE | `TICKET-PRIORITY-002` |
| 4 | `TICKET-PRIORITY-004` | `code_reviewer` | HIGH | S | `gpt-5.6-sol` / `high` | BLOCKED-AGY-R5-QA | `TICKET-PRIORITY-003R5` |
| 5 | `TICKET-PRIORITY-002R` | `developer` | CRITICAL | M | `gpt-5.6-sol` / `high` | DONE | `TICKET-PRIORITY-003` |
| 6 | `TICKET-PRIORITY-003R` | `qa_tester` | HIGH | S | `gpt-5.6-sol` / `high` | DONE | `TICKET-PRIORITY-002R` |
| 7 | `TICKET-PRIORITY-005` | `business_analyst` | MEDIUM | XS | `gpt-5.6-terra` / `medium` | PENDING — RELEASE COMPLETION | Release Completion closure |
| 8 | `TICKET-PRIORITY-002R2` | `developer` | CRITICAL | L | `gpt-5.6-sol` / `high` | DONE | `TICKET-PRIORITY-003R` |
| 9 | `TICKET-PRIORITY-003R2` | `qa_tester` | HIGH | S | `gpt-5.6-sol` / `high` | DONE | `TICKET-PRIORITY-002R2` |
| 10 | `TICKET-PRIORITY-002R3` | `developer` | CRITICAL | L | `gpt-5.6-sol` / `high` | DONE | `TICKET-PRIORITY-003R2` |
| 11 | `TICKET-PRIORITY-003R3` | `qa_tester` | HIGH | S | `gpt-5.6-sol` / `high` | DONE | `TICKET-PRIORITY-002R3` |
| 12 | `TICKET-PRIORITY-003R3E` | `root orchestrator` | HIGH | XS | `gpt-5.6-terra` / `high` | DONE | `TICKET-PRIORITY-003R3` |
| 13 | `TICKET-PRIORITY-002R4` | `developer` | CRITICAL | M | `gpt-5.6-sol` / `high` | DONE | `TICKET-PRIORITY-003R3E` |
| 14 | `TICKET-PRIORITY-002R5` | `developer` | HIGH | S | `gpt-5.6-sol` / `high` | DONE | `TICKET-PRIORITY-002R4` |
| 15 | `TICKET-AGY1-SMOKE-20260826-R2` | `developer` | HIGH | S | `gpt-5.6-sol` / `high` | DONE | `TICKET-PRIORITY-002R5` |
| 16 | `TICKET-AGY1-RECEIPT-SCHEMA-20260826-R1` | `developer` | HIGH | S | `gpt-5.6-sol` / `high` | DONE | `TICKET-PRIORITY-002R5` |
| 17 | `TICKET-AGY1-RECEIPT-VALIDATOR-20260826-R1` | `developer` | HIGH | XS | `gpt-5.6-sol` / `high` | DONE | `TICKET-AGY1-RECEIPT-SCHEMA-20260826-R1` |
| 18 | `TICKET-AGY1-DUPLICATE-JSON-20260826-R1` | `developer` | HIGH | S | `gpt-5.6-sol` / `high` | DONE | `TICKET-AGY1-SMOKE-20260826-R2` |
| 19 | `TICKET-AGY1-RECEIPT-V2-ADOPTION-20260826-R1` | `developer` | HIGH | S | `gpt-5.6-sol` / `high` | DONE | `TICKET-AGY1-RECEIPT-SCHEMA-20260826-R1` |
| 20 | `TICKET-AGY1-RECEIPT-V2-AGY-REQUIREMENT-20260826-R1` | `developer` | HIGH | XS | `gpt-5.6-sol` / `high` | DONE | `TICKET-AGY1-RECEIPT-SCHEMA-20260826-R1` |
| 21 | `TICKET-PRIORITY-003R5` | `qa_tester` | HIGH | M | `gpt-5.6-sol` / `high` | DONE | combined `213`; focused `142`; sync/lock/diff passed |
| 22 | `TICKET-AGY1-EVIDENCE-DOC-20260826-R1` | `business_analyst` | MEDIUM | XS | `gpt-5.6-terra` / `high` | DONE | None; disjoint from formal QA |
| 23 | `TICKET-AGY1-SMOKE-20260826-R3` | `orchestrator` | HIGH | XS | `TBD — fresh alias-specific decision required` | BLOCKED — FRESH GATES | successful acceptance R3 + current-session attested `agy1` Gemini band |
| 24 | `TICKET-PRIORITY-004R5` | `code_reviewer` | HIGH | S | `gpt-5.6-sol` / `high` | DONE — READY_FOR_PROD | `TICKET-PRIORITY-003R5` |
| 25 | `TICKET-AGY1-QUOTA-20260826-R1` | `devops` | HIGH | XS | `gemini-3.7-flash-high` / `high` | BLOCKED — CONSUMED / SANITIZATION_FAILURE | one query only; current-session attestation supersedes it for dispatch gating |
| 26 | `TICKET-MULTIAGENT-ACCEPTANCE-20260826-R1` | `orchestrator` | HIGH | S | `gpt-5.6-sol` / `high` | FAILED — CHILD SCOPE OVERLAP | timing/nonces/forwarding/fingerprint/no-change passed; exact child scope failed |
| 27 | `TICKET-MULTIAGENT-ACCEPTANCE-20260826-R2` | `orchestrator` | HIGH | S | `gpt-5.6-sol` / `high` | FAILED — NO EXACT 4/4 PEAK | B ended before child began; scope/nonces/fingerprint/no-change passed |
| 28 | `TICKET-MULTIAGENT-ACCEPTANCE-20260826-R3` | `orchestrator` | HIGH | S | `gpt-5.6-sol` / `high` | DONE | barrier captured root/A/B/child `running`; exact scopes/nonces/fingerprint/no-change and triple overlap passed |

### Scheduling Snapshot
- `TICKET-PRIORITY-001` is complete and therefore not selectable.
- `TICKET-PRIORITY-002` is complete: syntax compilation and scoped diff checks exited `0`; governance regression passed `11`; focused dispatcher regression passed `76` with `18` legacy execute-without-snapshot fixtures deselected; functional scheduler checks passed.
- `TICKET-PRIORITY-003` reproduced the baseline `18` missing-snapshot fixture failures, then passed its focused regression: `python3 -m pytest -q tests/test_multiagent_ticket_scheduler.py tests/test_multiagent_prompt_command.py project/tests/test_claude_governance.py` exited `0` with `154 passed in 1.14s`; scoped diff check also exited `0`.
- `TICKET-PRIORITY-002R` is complete. Its evidence is limited to `scripts/multiagent_prompt_command.py`, `scripts/multiagent_ticket_scheduler.py`, `.claude/hooks/adaptive_dispatch_guard.py`, and `.claude/hooks/orchestrator_only_guard.py`; `py_compile` and scoped diff checks exited `0`, focused pytest passed `106` in `1.13s`, and the five-review-findings plus shell-indirection reproductions were `OK`.
- The remediation records atomic local-temp claim behavior. Stale or ambiguous claims fail closed; this behavior is included in the completed independent QA evidence.
- `TICKET-PRIORITY-003R` completed independent remediation security regression QA: the combined focused pytest command over the three approved suites exited `0` with `173 passed` in `1.53s`; the scoped diff check exited `0`; all five remediation areas were covered and the Rule 11 matrix was green.
- `TICKET-PRIORITY-002R2` is complete: the bounded source fix changed one file; the exact regression passed (`1 passed`), the claim subset passed (`31 passed, 83 deselected`), and deletion of the active locked entry is blocked from same-authorization reacquisition.
- `TICKET-PRIORITY-003R2` completed independent QA: the exact combined three-suite command exited `0` with `185 passed in 2.01s`; scoped diff check exited `0`.
- The prior `TICKET-PRIORITY-004` read-only review returned `NEEDS_HITL — NOT READY`; its findings were remediated in R3 and independently QA-validated. The subsequent final R3 read-only re-review failed with the three R4 findings below. Its R3 QA (`185 passed`) and R3E environment `PASS` evidence remain valid historical evidence; they do not close the new findings.
- `TICKET-PRIORITY-002R3` is complete. This remediation edited only the dispatcher in this round; `py_compile` and scoped diff checks passed; scheduler plus Claude governance checks passed `71`; focused coverage passed `155` with `30` expected contract failures; and the eleven named direct reproductions passed: dirfd swap, durable outside-worktree derivation, independent receipt, lifecycle successful release, lifecycle failed release, write loop, unsupported platform, non-overlap concurrency, overlap, delete/reacquire, and replay.
- The single permitted R3E root verification superseded the managed-sandbox environment boundary: sanitized result `exit 0`, status `PASS`; `outside_worktree`, `canonical_namespace`, `directory_mode_0700`, `owned_by_current_user`, `retained_dirfd`, and `repo_horo_absent` were all `true`. No claim or lock record was created and no provider was dispatched.
- `TICKET-PRIORITY-003R3` completed independent QA: `python3 -m pytest -q tests/test_multiagent_ticket_scheduler.py tests/test_multiagent_prompt_command.py project/tests/test_claude_governance.py` exited `0` with `185 passed in 1.79s`; the scoped diff check exited `0`; only `tests/test_multiagent_prompt_command.py` changed. Lifecycle, isolated-store, and delete/reacquire coverage is green.
- `TICKET-PRIORITY-003R3E` completed its exact, single-use root-waiver action. The waiver is preserved below as consumed and expired audit evidence. Completion releases only the final R3 read-only re-review; it does not make `TICKET-PRIORITY-005` eligible.
- **Completed AGY and receipt-v2 remediations / R5 QA and review**: the source High-hardening lane passed `188` tests with three intentional obsolete-test deltas; the schema-v2 AGY conditional requirement passed; the validator dependency was isolated and locked successfully; and receipt-v2 policy/template adoption passed ecosystem sync/check, `16` focused governance tests, and the secret scan. Formal R5 QA completed with combined `213` and focused `142` tests plus sync, locked dependency, and diff checks. The final review is `DONE — READY_FOR_PROD`, with no Critical/High finding and completed sync, lock, secret, and diff checks. The wrapper-timeout residual is Medium; reviewer-recorded Medium/Low residuals remain tracked. No external AGY action occurred.
- **Consumed quota and attested dispatch bands**: the single allowed status query is consumed and blocked as `sanitization_failure` with alias quota `unknown`; no retry is permitted. Its fingerprint window is recorded only as `changed=true/confounded`, never as a raw digest. Current-session user attestation now supplies safe dispatch bands: `agy1` Gemini weekly/5h `healthy`; `agy1` Claude/GPT `exhausted`; `agy2` Gemini weekly/5h `healthy`; `agy2` Claude/GPT weekly `critical` and 5h `healthy`. The later R3 path is limited to `agy1` Gemini, subject to R2 plus a fresh decision/snapshot.
- **R1 failed / R2 reserved acceptance**: R1 did prove triple explorer overlap plus root `4/4`, verified A/B/C nonces, parent-child forwarding, equal safe fingerprint marker `00ab...d71a`, empty changed-file lists, `15` governance tests, and sync check. Its child nevertheless inspected Rule 11, overlapping parent A, rather than its assigned skill; no completion is inferred. R2 reserves Parent A only Rule 11, Parent B only the prompt template (and generated/catalog checks only after inspecting it), and child only the orchestration skill. Root plus the three explorers will again use exactly `4/4` without file mutation.
- **Public-outcome evidence boundary**: the documentation-governance ticket is complete. Public `ExecutionOutcome` is validated in-process with elided stdout/stderr; receipt plus WorkResult plus public outcome is not independently portable/offline evidence. `portable=True` still needs separately retained trusted exact raw stdout, and no approved private retention channel exists. Never restore or log raw streams. This is a Medium residual; a future encrypted sidecar requires separate scope/HITL and is not implemented. Successful AGY language is limited to `validated in-process only`.

### TICKET-PRIORITY-001 | Governance and Active Planning | [STATUS: DONE]
**Severity**: CRITICAL
**Work Effort**: XL
**Model / Reasoning Effort**: `gpt-5.6-sol` / `xhigh`
**Depends On**: None
**Blocks**: `TICKET-PRIORITY-002`
**Ownership**: `PROJECT_TASKS.md`, `plans/plan.md`, `.agents/rules/11-orchestrator-subagent-delegation.md`, `.agents/skills/orchestrator-delegation/SKILL.md`, `.agents/AGENTS.md`, `.claude/rules/orchestrator-subagents.md`, `.antigravity/skills/orchestrator-delegation/SKILL.md`

#### Objective, Evidence, and Stop Condition
- Define Rule 11 as the sole policy authority and mirror eligibility, comparator, tie, override, non-preemption, and effort-separation semantics.
- Preserve historical evidence and mark old `Priority`-only scheduling text superseded.
- Evidence: `python3 scripts/sync_ai_agent_ecosystem.py --sync` and then `--check` both returned `[OK]` on 2026-08-25; generated Codex files were not edited manually.
- Stop `DONE` after owned governance files and active planning artifacts are synchronized; do not implement enforcement code in this ticket.

### TICKET-PRIORITY-002 | Hook and Dispatcher Enforcement | [STATUS: DONE]
**Severity**: CRITICAL
**Work Effort**: L
**Model / Reasoning Effort**: `gpt-5.6-sol` / `high`
**Depends On**: `TICKET-PRIORITY-001`
**Blocks**: `TICKET-PRIORITY-003`
**Ownership Reserved**: developer lane owns only the scheduler/dispatcher and hook files explicitly assigned by the root; this decision record does not authorize governance-file edits by that lane

#### Objective, Acceptance, and Stop Condition
- Enforce filter-before-sort using Rule 11's total-order key immediately before executable dispatch; reserve ownership and recompute for parallel selection.
- Fail closed on invalid/missing Severity or Work Effort, duplicate Ticket ID, unmet dependencies, ownership conflict, quota/HITL failure, explicit blocker, or invalid Rule 18 decision.
- Keep Work Effort independent from model/provider/reasoning-effort routing and do not preempt `DOING` work.
- Fresh non-secret quota validation recorded band `healthy` for selected alias `codex1`, above the broad-work threshold. Executable decision: [`decision_priority_002.json`](project/tests/artifacts/priority_scheduling/decision_priority_002.json) (policy `2026-08-25.2`).
- Completion evidence: syntax compilation and scoped diff checks exited `0`; governance regression passed `11`; focused dispatcher regression passed `76`, with `18` legacy execute-without-snapshot fixtures deselected; functional scheduler checks passed.
- Residual risk: cross-process persistent reservation storage/locking is not yet present. This is retained for independent QA and read-only review; it is not a rollback condition for the completed implementation ticket.
- Stop condition met: targeted implementation evidence is recorded. Return to `BLOCKED` only if later review establishes an invalid decision, quota/HITL failure, ownership conflict, or another failed pre-execution gate.

### TICKET-PRIORITY-003 | Independent Scheduling QA | [STATUS: DONE]
**Severity**: HIGH
**Work Effort**: M
**Model / Reasoning Effort**: `gpt-5.6-terra` / `high`
**Depends On**: `TICKET-PRIORITY-002`
**Blocks**: `TICKET-PRIORITY-004`
**Ownership Reserved**: focused scheduler, dispatcher, and hook tests only

#### Objective, Acceptance, and Stop Condition
- Test every severity pair, every Work Effort pair, exact Ticket ID ties, empty eligible sets, recomputation after ownership reservation, and non-preemption.
- Test each override independently and in combination; verify lower-severity eligible work can run while higher-severity work is ineligible.
- Prove model reasoning effort cannot change order and invalid metadata fails before subprocess creation.
- Executable QA decision: [`decision_priority_003.json`](project/tests/artifacts/priority_scheduling/decision_priority_003.json) (schema v1; policy `2026-08-25.2`; non-secret quota band `healthy`; mutation mode).
- Work Effort `M` remains the delivery-size scheduling input. Reasoning effort `high` is a separate runtime-quality setting for independent QA and cannot change scheduling order.
- Include the `18` legacy execute-without-snapshot fixtures previously deselected from focused dispatcher regression. Independently assess the residual lack of a cross-process persistent reservation store/lock.
- Completion evidence: baseline `18` missing-snapshot fixture failures were reproduced. `python3 -m pytest -q tests/test_multiagent_ticket_scheduler.py tests/test_multiagent_prompt_command.py project/tests/test_claude_governance.py` exited `0` with `154 passed in 1.14s`; scoped diff check exited `0`. QA changes were limited to `tests/test_multiagent_ticket_scheduler.py`, `tests/test_multiagent_prompt_command.py`, and `project/tests/test_claude_governance.py`.
- Stop condition met: focused QA evidence and its concise baseline-failure record are complete. Return to `BLOCKED` only if later review establishes an invalid decision, quota/HITL failure, ownership conflict, or another failed pre-execution gate.

### TICKET-PRIORITY-004 | Final R3 Read-Only Safety and Compatibility Re-Review | [STATUS: BLOCKED-AGY-R5-QA]
**Severity**: HIGH
**Work Effort**: S
**Model / Reasoning Effort**: `gpt-5.6-sol` / `high`
**Depends On**: `TICKET-PRIORITY-003R5` formal QA after all pre-QA dependencies freeze
**Blocks**: `TICKET-PRIORITY-005`
**Ownership Reserved**: reviewer lane is reserved for final R3 read-only review only; no shared-file edits, implementation, test, hook, configuration, or generated-file changes are authorized

#### Objective, Acceptance, and Stop Condition
- The prior read-only review's `NEEDS_HITL — NOT READY` findings are historical evidence. The final R3 re-review was executed and failed: a crashed active-record ownership scan never evaluates liveness, age, or a per-claim lock and can permanently block fresh overlapping authorization; durable claim data persists raw PII in `ownership_resources`; and receipt validation is host/user-state dependent rather than portable archival evidence.
- Executable review decision: [`decision_priority_004.json`](project/tests/artifacts/priority_scheduling/decision_priority_004.json) (schema v1; policy `2026-08-25.2`; non-secret quota band `healthy`; read-only mode).
- Work Effort `S` remains the delivery-size scheduling input. Reasoning effort `high` is a separate runtime-quality setting for safety and compatibility review and cannot change scheduling order.
- **R3 prerequisite evidence retained**: independent QA over the exact three suites exited `0` with `185 passed in 1.79s`; the single-use root environment verification returned sanitized `exit 0`, status `PASS`, with all required environment assertions `true`. No claim or lock record was created and no provider was dispatched.
- R4 now meets its bounded acceptance evidence: `py_compile` and scoped diff checks passed; permanent R4 coverage passed `6`; scheduler plus Claude checks passed `71`; prompt-command plus R4 coverage passed `119` with one intentional legacy assertion delta. The frozen reviewer architecture check found no Critical or High finding.
- R5 source is frozen: secure temporary recovery and a typed non-PII diagnostic are implemented; `py_compile` and scoped diff passed, R4 coverage passed `6`, combined coverage passed `190` with one known intentional legacy `ownership_sha256` assertion, and direct temporary recovery passed. No unresolved Critical or High pre-QA finding remains.
- The review is `BLOCKED-AGY-R5-QA`. AGY native-protocol and all pre-QA remediation are frozen; the combined independent formal QA is now active. The sanitized-v1 raw-historical-receipt limitation remains a Medium compatibility/audit boundary; it does not make `TICKET-PRIORITY-005` eligible.
- Stop `DONE` only after AGY remediation, independent formal QA, and a fresh evidence-backed read-only terminal verdict. This documentation handoff records status only and does not execute remediation, QA, or review.

### TICKET-PRIORITY-002R4 | Fourth Safety Re-Review Remediation | [STATUS: DONE]
**Severity**: CRITICAL
**Work Effort**: M
**Model / Reasoning Effort**: `gpt-5.6-sol` / `high`
**Depends On**: `TICKET-PRIORITY-003R3E`
**Blocks**: `TICKET-PRIORITY-004`
**Ownership Reserved**: developer lane owns only the exact R4 source remediation and local validation assigned after implementation handoff. This governance record owns no source, test, hook, configuration, generated-file, external, or PII action.

#### Objective, Acceptance, and Stop Condition
- **Exact session-approved R4 scope**: remediate only the failed R3 review findings: (1) safely terminalize crashed active ownership records using liveness, age, and per-claim-lock checks before a fresh overlapping authorization may proceed, while exact replay remains blocked; (2) replace durable raw-PII `ownership_resources` with non-PII conflict tokens; and (3) make receipt validation portable archival evidence by embedding sanitized immutable proof rather than depending on host or user state.
- Decision artifact: [`decision_priority_002r4.json`](project/tests/artifacts/priority_scheduling/decision_priority_002r4.json) (schema v1; policy `2026-08-25.2`; phase `implementation`; mutation mode; non-secret quota band `healthy`; `hitl_approved: true`). Session approval is recorded without approver identity.
- **Explicit exclusions**: no unrelated remediation or refactor; no source/test/hook/configuration/generated-file action by this documentation lane; no deploy, publish, push, credentials, secrets, account, external, or PII action. The developer handoff must preserve the stated non-PII boundary.
- **Completion evidence**: `py_compile` and scoped diff checks passed; permanent R4 coverage passed `6`; scheduler plus Claude checks passed `71`; prompt-command plus R4 coverage passed `119` with one intentional legacy assertion delta. The frozen reviewer architecture check found no Critical or High findings.
- **Compatibility/audit boundary**: sanitized v1 migration preserves replay prevention and digest validation, but raw historical receipt revalidation is unsupported because durable PII is intentionally not retained. This is a Medium boundary, not a release approval.
- Stop condition met for R4 implementation. The fixed migration temporary residue that can block future migration (Medium) and typed legacy diagnostic (Low/Medium) are reserved to R5; do not release formal QA, `TICKET-PRIORITY-004`, or `TICKET-PRIORITY-005`.

### TICKET-PRIORITY-002R5 | Sanitized Migration Residue Remediation | [STATUS: DONE]
**Severity**: HIGH
**Work Effort**: S
**Model / Reasoning Effort**: `gpt-5.6-sol` / `high`
**Depends On**: `TICKET-PRIORITY-002R4`
**Blocks**: `TICKET-AGY1-SMOKE-20260826-R2`
**Ownership Reserved**: `scripts/multiagent_prompt_command.py` only. One developer editor; no test, hook, configuration, generated-file, deployment, push, credential, secret, account, external, or raw-PII action.

#### Objective, Acceptance, and Stop Condition
- Resolve only the fixed sanitized-v1 migration temporary residue that can block a later migration, and make the retained legacy diagnostic typed and actionable. Preserve replay prevention and digest validation; do not add durable raw PII or claim raw historical receipt revalidation support.
- Decision artifact: [`decision_priority_002r5.json`](project/tests/artifacts/priority_scheduling/decision_priority_002r5.json) (schema v1; policy `2026-08-25.2`; phase `implementation`; mutation mode; non-secret quota band `healthy`; `codex1` / `gpt-5.6-sol` / `high`; `hitl_approved: true`). Session approval is recorded without approver identity.
- **Completion evidence**: source API is frozen; `py_compile` and scoped diff checks passed; R4 coverage passed `6`; combined coverage passed `190` with one known intentional legacy `ownership_sha256` assertion; direct temporary recovery passed. Secure temporary recovery and a typed non-PII diagnostic are implemented. No unresolved Critical or High finding remains before QA.
- Stop condition met for R5 source remediation. The same dispatcher source is now reserved by the bounded AGY native-protocol remediation. Formal QA cannot start until that lane freezes; this ticket does not release `TICKET-PRIORITY-004` or `TICKET-PRIORITY-005`.

### TICKET-AGY1-SMOKE-20260826-R2 | AGY Native-Protocol Remediation | [STATUS: DONE]
**Severity**: HIGH
**Work Effort**: S
**Model / Reasoning Effort**: `gpt-5.6-sol` / `high`
**Depends On**: `TICKET-PRIORITY-002R5`
**Blocks**: `TICKET-PRIORITY-003R5`, `TICKET-PRIORITY-004`, and `TICKET-PRIORITY-005`
**Ownership Reserved**: `scripts/multiagent_prompt_command.py` only. One developer editor; no test, hook, configuration, generated-file, deployment, push, credential, secret, account, external retry, or raw-PII action.

#### Objective, Acceptance, and Stop Condition
- Correct only the HIGH availability/integration mismatch: align the outbound AGY user-event envelope with the installed AGY `1.1.20` native message shape and align terminal parsing with its native event/result nesting. The existing synthetic test dialect is not proof of the native protocol. Receipt-schema drift is expressly out of scope for this ticket.
- Decision artifact: [`decision_agy1_smoke_20260826_r2.json`](project/tests/artifacts/priority_scheduling/decision_agy1_smoke_20260826_r2.json) (schema v1; policy `2026-08-25.2`; phase `implementation`; mutation mode; non-secret quota band `healthy`; `codex1` / `gpt-5.6-sol` / `high`; `hitl_approved: true`). Session approval is recorded without approver identity.
- No external retry: the initial read-only smoke had a successful dry run, one ownership-conflict preflight without a child, and one fail-closed invalid-contract/terminal-shape child result. It produced no valid receipt, provider-execution proof, or quota proof, and no repository change.
- **Completion evidence**: source is frozen; `py_compile` and scoped diff passed; native parser plus fake-execute reproduction passed; R4 plus scheduler plus governance coverage passed `77`; prompt plus R4 coverage passed `118` with two expected legacy failures (old AGY dialect and old `ownership_sha256`).
- Stop condition met. The later pre-QA parser-hardening ticket has separate source ownership; do not broaden into receipt-schema drift or invoke another external child.

### TICKET-AGY1-RECEIPT-SCHEMA-20260826-R1 | Receipt-v2 Contract Remediation | [STATUS: DONE]
**Severity**: HIGH
**Work Effort**: S
**Model / Reasoning Effort**: `gpt-5.6-sol` / `high`
**Depends On**: `TICKET-PRIORITY-002R5`
**Blocks**: `TICKET-PRIORITY-003R5`, `TICKET-PRIORITY-004`, and `TICKET-PRIORITY-005`
**Ownership Reserved**: new receipt-v2 schema artifact only. Receipt-v1 remains immutable; no dispatcher, docs, tests, hooks, configuration, generated-file, deployment, push, credential, secret, account, external, or raw-PII action.

#### Objective, Acceptance, and Stop Condition
- Resolve the HIGH contract/evidence defect: receipt-v1 uses `additionalProperties: false` but omits `dispatch_claim_key`, `dispatch_claim_sha256`, `claim_proof`, `claim_proof_sha256`, `claim_proof_scope`, and `scheduling_snapshot_sha256`, so no current receipt can satisfy both code and schema. The v2 contract must model those fields and preserve their distinct semantics.
- Do not silently change the receipt-v1 identity. In particular, distinguish the embedded ClaimProof digest from the persisted-record digest; previous receipts used a different meaning for one of these values. Define explicit v2 meaning and migration rather than reinterpreting historical v1 receipts.
- Decision artifact: [`decision_agy1_receipt_schema_20260826_r1.json`](project/tests/artifacts/priority_scheduling/decision_agy1_receipt_schema_20260826_r1.json) (schema v1; policy `2026-08-25.2`; phase `implementation`; mutation mode; non-secret quota band `healthy`; `codex1` / `gpt-5.6-sol` / `high`; `hitl_approved: true`).
- **Completion evidence and v2 semantics**: receipt-v2 is a new schema only; receipt-v1 and its `$id` are unchanged. JSON and Draft 2020-12 metaschema validation, runtime/ClaimProof parity, two sanitized Codex/AGY valid samples, six invalid rejections, and scoped diff passed. In v2, `dispatch_claim_sha256` and `claim_proof_sha256` are both the canonical embedded ClaimProof digest, not a persisted-record digest; historical v1 receipts retain their original meaning and are not converted or retroactively revalidated as v2. Migration may retain terminal replay state/original record digest but cannot turn an old receipt into v2; only new governed execution emits v2.
- Stop condition met at frozen schema and local validation. Packaging, contract-adoption, and QA are separately owned later; no AGY retry is authorized.

### TICKET-AGY1-RECEIPT-VALIDATOR-20260826-R1 | Receipt-v2 Validator Packaging | [STATUS: DONE]
**Severity**: HIGH
**Work Effort**: XS
**Model / Reasoning Effort**: `gpt-5.6-sol` / `high`
**Depends On**: `TICKET-AGY1-RECEIPT-SCHEMA-20260826-R1`
**Blocks**: `TICKET-PRIORITY-003R5`, `TICKET-PRIORITY-004`, and `TICKET-PRIORITY-005`
**Ownership Reserved**: `pyproject.toml`, `requirements.txt`, and `uv.lock` only. One developer editor; no source, schema, test, workflow, generated-file, deployment, push, credential, secret, account, external, or raw-PII action.

#### Objective, Acceptance, and Stop Condition
- Make Draft 2020-12 validation reproducible in the repository rather than accepting an environment-only import. Add `jsonschema>=4.23,<5` consistently to the declared dependency sources and regenerate `uv.lock`; CI already derives its requirements and requires no workflow change.
- Decision artifact: [`decision_agy1_receipt_validator_20260826_r1.json`](project/tests/artifacts/priority_scheduling/decision_agy1_receipt_validator_20260826_r1.json) (schema v1; policy `2026-08-25.2`; phase `implementation`; mutation mode; non-secret quota band `healthy`; `codex1` / `gpt-5.6-sol` / `high`; `hitl_approved: true`). Session approval is recorded without approver identity.
- **Completion evidence**: the dependency declaration is isolated and the lock is regenerated successfully, making Draft 2020-12 validation reproducible rather than environment-only.
- Stop condition met at frozen dependency declarations and lockfile. No source/schema/test/CI-workflow change or external retry is authorized.

### TICKET-AGY1-DUPLICATE-JSON-20260826-R1 | AGY Parser and Evidence Hardening | [STATUS: DONE]
**Severity**: HIGH
**Work Effort**: S
**Model / Reasoning Effort**: `gpt-5.6-sol` / `high`
**Depends On**: `TICKET-AGY1-SMOKE-20260826-R2`
**Blocks**: `TICKET-PRIORITY-003R5`, `TICKET-PRIORITY-004`, and `TICKET-PRIORITY-005`
**Ownership Reserved**: `scripts/multiagent_prompt_command.py` only. One developer editor; no test, schema, hook, configuration, generated-file, deployment, push, credential, secret, account, external retry, or raw-PII action.

#### Objective, Acceptance, and Stop Condition
- Correct the smallest coherent HIGH AGY parser/evidence set: reject duplicate JSON member names rather than accepting ordinary `json.loads` last-key-wins semantics, and reject `NaN`/`Infinity` through `parse_constant`; ensure the resulting reason is content-free; redact decoded AGY prompt content as well as the encoded stdin envelope so arbitrary prompt text cannot echo in `structured_output`; sanitize before finalization, hashing, or persistence and use the exact sanitized `WorkResult` everywhere; and bind AGY `process_or_session_id` receipt validation to parsed native evidence so replacement/deletion fails. Preserve the frozen native-protocol behavior; receipt-v2 schema/adoption and tests are separate ownership.
- Decision artifact: [`decision_agy1_duplicate_json_20260826_r1.json`](project/tests/artifacts/priority_scheduling/decision_agy1_duplicate_json_20260826_r1.json) (schema v1; policy `2026-08-25.2`; phase `implementation`; mutation mode; non-secret quota band `healthy`; `codex1` / `gpt-5.6-sol` / `high`; `hitl_approved: true`). Session approval is recorded without approver identity.
- **Completion evidence**: source hardening is frozen and its focused evidence passed `188` tests with three intentional obsolete-test deltas. The local evidence covers strict duplicate/non-finite rejection, content-free/redacted result handling, sanitized-finalization binding, and exact AGY native process/session binding.
- Stop condition met at source freeze. The three obsolete fixtures/assertions are QA-owned updates; no external retry is authorized.

### TICKET-AGY1-RECEIPT-V2-ADOPTION-20260826-R1 | Receipt-v2 Contract Adoption | [STATUS: DONE]
**Severity**: HIGH
**Work Effort**: S
**Model / Reasoning Effort**: `gpt-5.6-sol` / `high`
**Depends On**: `TICKET-AGY1-RECEIPT-SCHEMA-20260826-R1`
**Blocks**: `TICKET-PRIORITY-003R5`, `TICKET-PRIORITY-004`, and `TICKET-PRIORITY-005`
**Ownership Reserved**: `.agents/config/multiagent_model_policy.yaml` and `docs/templates/MULTIAGENT_PROMPT_COMMAND.md` only. One developer editor; generated mirrors may change only through the prescribed ecosystem sync after the source files freeze. No dispatcher, schema, test, hook, deployment, push, credential, secret, account, external, or raw-PII action.

#### Objective, Acceptance, and Stop Condition
- Resolve the HIGH orphaned-contract defect: make receipt-v2 canonical for new governed receipts in policy and prompt-template contract language, while receipt-v1 remains explicitly legacy; align the timestamp contract to the required `Z` suffix. Do not alter receipt-v1 identity or alter generated files manually.
- Decision artifact: [`decision_agy1_receipt_v2_adoption_20260826_r1.json`](project/tests/artifacts/priority_scheduling/decision_agy1_receipt_v2_adoption_20260826_r1.json) (schema v1; policy `2026-08-25.2`; phase `implementation`; mutation mode; non-secret quota band `healthy`; `codex1` / `gpt-5.6-sol` / `high`; `hitl_approved: true`). Session approval is recorded without approver identity.
- **Completion evidence**: policy/template sources are frozen; ecosystem sync/check passed, `16` focused governance tests passed, and the secret scan passed. Receipt-v2 is canonical for new governed receipts; receipt-v1 remains explicit legacy/non-reinterpreted handling.
- Stop condition met at prescribed synchronization evidence. Runtime schema loading and QA tests are separate ownership; no external retry is authorized.

### TICKET-AGY1-RECEIPT-V2-AGY-REQUIREMENT-20260826-R1 | Receipt-v2 AGY Evidence Requirement | [STATUS: DONE]
**Severity**: HIGH
**Work Effort**: XS
**Model / Reasoning Effort**: `gpt-5.6-sol` / `high`
**Depends On**: `TICKET-AGY1-RECEIPT-SCHEMA-20260826-R1`
**Blocks**: `TICKET-PRIORITY-003R5`, `TICKET-PRIORITY-004`, and `TICKET-PRIORITY-005`
**Ownership Reserved**: `.agents/schemas/multiagent-dispatch-receipt-v2.schema.json` only. One developer editor; receipt-v1, dispatcher, policy, template, tests, hooks, configuration, generated files, deployment, push, credential, secret, account, external, and raw-PII actions are excluded.

#### Objective, Acceptance, and Stop Condition
- Correct only the HIGH receipt-v2 contract gaps: conditionally require `process_or_session_id` when `provider` is `agy`, retain Codex receipt compatibility, and align the timestamp contract to the required `Z` suffix. Do not mutate receipt-v1, broaden semantic migration, or hide provider-specific conditions.
- Decision artifact: [`decision_agy1_receipt_v2_agy_requirement_20260826_r1.json`](project/tests/artifacts/priority_scheduling/decision_agy1_receipt_v2_agy_requirement_20260826_r1.json) (schema v1; policy `2026-08-25.2`; phase `implementation`; mutation mode; non-secret quota band `healthy`; `codex1` / `gpt-5.6-sol` / `high`; `hitl_approved: true`). Session approval is recorded without approver identity.
- **Completion evidence**: the schema-v2 AGY conditional requirement passed: AGY requires `process_or_session_id`, Codex remains compatible, and the timestamp `Z` contract is enforced.
- Stop condition met at frozen schema-v2 update and local validation. No external retry is authorized.

### TICKET-PRIORITY-003R5 | R5 Combined Formal Regression QA | [STATUS: DONE]
**Severity**: HIGH
**Work Effort**: M
**Model / Reasoning Effort**: `gpt-5.6-sol` / `high`
**Depends On**: completed `TICKET-AGY1-SMOKE-20260826-R2`, `TICKET-AGY1-RECEIPT-SCHEMA-20260826-R1`, `TICKET-AGY1-RECEIPT-VALIDATOR-20260826-R1`, `TICKET-AGY1-DUPLICATE-JSON-20260826-R1`, `TICKET-AGY1-RECEIPT-V2-ADOPTION-20260826-R1`, and `TICKET-AGY1-RECEIPT-V2-AGY-REQUIREMENT-20260826-R1`
**Blocks**: `TICKET-PRIORITY-004R5` and `TICKET-PRIORITY-005`
**Ownership Reserved**: `tests/test_multiagent_prompt_command.py`, `tests/test_multiagent_prompt_command_r4.py`, and `tests/test_multiagent_receipt_schema.py` only. Dispatcher source and receipt schemas are read-only/frozen.

#### Objective, Acceptance, and Stop Condition
- Update the three obsolete fixtures/assertions, then independently validate: the official AGY envelope/native fake execute path; strict duplicate/non-finite JSON rejection; sanitation before hashing and public stdout/stderr elision; exact native process/session binding; the full R5 migration matrix; and real generated Codex plus AGY receipt-v2 Draft 2020 conformance, tamper rejection, and field parity. Receipt-v1 remains legacy coverage, not the v2 acceptance contract. No external AGY retry is part of QA.
- Decision artifact: [`decision_priority_003r5.json`](project/tests/artifacts/priority_scheduling/decision_priority_003r5.json) (schema v1; policy `2026-08-26.1`; phase `qa`; mutation mode limited to the owned test updates; non-secret quota band `healthy`; `codex1` / `gpt-5.6-sol` / `high`; `hitl_approved: true`).
- **Completion evidence**: combined `213` and focused `142` tests passed; ecosystem sync, locked dependency, and scoped diff checks passed. No external AGY action occurred.
- Stop condition met. Release only `TICKET-PRIORITY-004R5` fresh read-only final review; no external AGY retry is part of QA.

### TICKET-AGY1-EVIDENCE-DOC-20260826-R1 | Public Outcome Evidence Boundary | [STATUS: DONE]
**Severity**: MEDIUM
**Work Effort**: XS
**Model / Reasoning Effort**: `gpt-5.6-terra` / `high`
**Depends On**: None; explicitly disjoint from `TICKET-PRIORITY-003R5`
**Blocks**: portable/offline evidence claims only; it does not block QA or source work
**Ownership Reserved**: `.agents/rules/17-multi-account-agent-orchestration.md`, `.agents/skills/multi-account-agent-orchestration/SKILL.md`, and `docs/templates/MULTIAGENT_PROMPT_COMMAND.md` only. This governance lane also records its status in the owned board/plan and its decision artifact; generated mirrors change only through prescribed sync. No source, schema, policy, dependency, test, external, or raw-stream action.

#### Objective, Acceptance, and Stop Condition
- State precisely that public `ExecutionOutcome` is validated in-process and its stdout/stderr are elided; a receipt, WorkResult, and public outcome are not an independently portable/offline-verifiable evidence bundle. `portable=True` still requires separately retained trusted exact raw stdout. No approved private retention channel exists, and raw streams must never be restored, logged, or persisted.
- Successful AGY evidence must say `validated in-process only`; it must not claim portable, offline, or receipt-only verification. Record the Medium residual and an encrypted, access-controlled raw-output sidecar only as a future, separately scoped/HITL-gated design option; do not implement it.
- Decision artifact: [`decision_agy1_evidence_doc_20260826_r1.json`](project/tests/artifacts/priority_scheduling/decision_agy1_evidence_doc_20260826_r1.json) (schema v1; policy `2026-08-26.1`; phase `implementation`; mutation mode; non-secret quota band `healthy`; `codex1` / `gpt-5.6-terra` / `high`; `hitl_approved: true`).
- **Completion evidence**: the rule, skill, and template contain the same boundary; ecosystem sync/check, focused governance tests, secret scan, and diff check passed. Stop condition met with no runtime, schema, policy, dependency, test, or external AGY change.

### TICKET-PRIORITY-004R5 | Fresh R5 Read-Only Final Review | [STATUS: DONE — READY_FOR_PROD]
**Severity**: HIGH
**Work Effort**: S
**Model / Reasoning Effort**: `gpt-5.6-sol` / `high`
**Depends On**: `TICKET-PRIORITY-003R5`
**Blocks**: `TICKET-AGY1-SMOKE-20260826-R3` and `TICKET-PRIORITY-005`
**Ownership Reserved**: read-only review only; no writable ownership, implementation, test mutation, external AGY retry, generated-file edit, deployment, push, credential, secret, account, or raw-stream action.

#### Objective, Acceptance, and Stop Condition
- **Terminal verdict**: `READY_FOR_PROD`. The frozen R5 QA/source/schema/policy/dependency/documentation evidence, including the public-outcome evidence boundary, has no Critical/High reviewer finding. Do not execute source or QA actions.
- Decision artifact: [`decision_priority_004r5.json`](project/tests/artifacts/priority_scheduling/decision_priority_004r5.json) (schema v1; policy `2026-08-26.1`; phase `review`; read-only mode; non-secret quota band `healthy`; `codex1` / `gpt-5.6-sol` / `high`; `hitl_approved: true`).
- **Completion evidence**: combined `213` tests passed; sync, locked-dependency, secret, and diff checks passed. The wrapper timeout is a Medium residual, and reviewer-recorded Medium/Low residuals remain tracked. No external AGY action occurred.
- Stop condition met. The later AGY R3 smoke is still not eligible: it first requires the reserved quota audit, then its own fresh decision/snapshot and every pre-execution gate.

### TICKET-AGY1-QUOTA-20260826-R1 | Sanitized AGY Quota Discovery | [STATUS: BLOCKED — CONSUMED / SANITIZATION_FAILURE]
**Severity**: HIGH
**Work Effort**: XS
**Model / Reasoning Effort**: `gemini-3.7-flash-high` / `high` (`agy1`)
**Depends On**: completed `TICKET-PRIORITY-004R5` and explicit session authorization for this one status-only query
**Blocks**: retry of this quota query; it does not block use of later user-attested alias-specific bands
**Ownership Reserved**: `devops` read-only/no writable ownership only. One interactive/status-only AGY query is permitted to establish a safe quota band. It must not send a work prompt or mutate source, schemas, policy, dependencies, tests, generated files, deployment, credentials, secrets, accounts, or raw-stream storage.

#### Objective, Acceptance, and Stop Condition
- The one permitted query is consumed with alias quota `unknown` and `sanitization_failure`; it produced no work prompt, work dispatch, or durable account/session/raw-TUI/path data. No retry is authorized.
- Decision artifact: [`decision_agy1_quota_20260826_r1.json`](project/tests/artifacts/priority_scheduling/decision_agy1_quota_20260826_r1.json) (schema v1; policy `2026-08-26.1`; phase `operations`; read-only mode; pre-query quota band `unknown` is permitted solely for discovery; `agy1` / `gemini-3.7-flash-high` / `high`; `hitl_approved: true`).
- Outcome artifact: [`evidence_agy1_quota_20260826_r1.json`](project/tests/artifacts/priority_scheduling/evidence_agy1_quota_20260826_r1.json). The fingerprint window is reported only as `changed=true/confounded` because concurrent governance edits make attribution impossible; no raw hash is retained.
- **Superseding dispatch input**: current-session user attestation supplies safe bands only: `agy1` Gemini weekly/5h `healthy`; `agy1` Claude/GPT `exhausted`; `agy2` Gemini weekly/5h `healthy`; `agy2` Claude/GPT weekly `critical` and 5h `healthy`. R3 may be considered only for `agy1` Gemini after R2 and a fresh alias-specific decision/snapshot; never route `agy1` Claude/GPT.
- Stop condition met as `BLOCKED`: this reservation does not authorize a work dispatch or the R3 smoke.

### TICKET-MULTIAGENT-ACCEPTANCE-20260826-R1 | Read-Only Multi-Agent Concurrency Acceptance | [STATUS: FAILED — CHILD SCOPE OVERLAP]
**Severity**: HIGH
**Work Effort**: S
**Model / Reasoning Effort**: `gpt-5.6-sol` / `high` (`codex1`)
**Depends On**: consumed quota lane; declared no-editor window; explicit user authorization
**Blocks**: no product/release gate; it is independent acceptance evidence only
**Ownership Reserved**: read-only repository questions and orchestration evidence only; no writable ownership. Exclude external CLI/network, work prompts, source/test/configuration/generated-file edits, commits, deployment, credentials, secrets, accounts, raw-provider streams, and any action beyond bounded local reads.

#### Objective, Acceptance, and Stop Condition
- **Evidence that passed**: B `[526129134989708, 526195340109541]`, A `[526130546883708, 526185334543958]`, and child `[526152378570250, 526164771804291]` are monotonic and have a triple intersection. A/B/C nonces were verified; parent forwarding, equal safe fingerprint marker `00ab...d71a`, `changed_files=[]`, `15` governance tests, and sync check passed. Root plus three explorers used `4/4`.
- **Exact failure**: the child authoritatively inspected `.agents/rules/11-orchestrator-subagent-delegation.md`, overlapping parent A, instead of the required `.agents/skills/orchestrator-delegation/SKILL.md`. Timing or topology cannot substitute for the declared disjoint scope contract.
- Decision artifact: [`decision_multiagent_acceptance_20260826_r1.json`](project/tests/artifacts/priority_scheduling/decision_multiagent_acceptance_20260826_r1.json); outcome artifact: [`evidence_multiagent_acceptance_20260826_r1.json`](project/tests/artifacts/priority_scheduling/evidence_multiagent_acceptance_20260826_r1.json).
- Stop condition met as `FAILED`; use fresh R2 only.

### TICKET-MULTIAGENT-ACCEPTANCE-20260826-R2 | Corrected Read-Only Multi-Agent Concurrency Acceptance | [STATUS: FAILED — NO EXACT 4/4 PEAK]
**Severity**: HIGH
**Work Effort**: S
**Model / Reasoning Effort**: `gpt-5.6-sol` / `high` (`codex1`)
**Depends On**: consumed quota lane, explicit user authorization, and a declared no-editor window
**Blocks**: `TICKET-PRIORITY-005` documentation reconciliation
**Ownership Reserved**: Parent A may inspect only `.agents/rules/11-orchestrator-subagent-delegation.md`; Parent B may inspect only `docs/templates/MULTIAGENT_PROMPT_COMMAND.md`, then only after that inspection may run generated/catalog sync checks; the exactly one nested child may inspect only `.agents/skills/orchestrator-delegation/SKILL.md`. All ownership is read-only. Source/tests/config/schema/dependency/generated-file edits, external CLI/network, work prompts, commits, deployment, credentials, secrets, accounts, and raw-provider streams are excluded.

#### Objective, Acceptance, and Stop Condition
- **Evidence that passed**: exact disjoint scopes, fresh nonces, equal worktree fingerprint, and `changed_files=[]`.
- **Exact failure**: B `[526622835607125,526630510648125]` ended before child `[526638962397125,526638984734625]` began. Consequently, R2 cannot prove root plus A, B, and child simultaneously active at `4/4`, even though the evidence contract otherwise passed.
- Decision artifact: [`decision_multiagent_acceptance_20260826_r2.json`](project/tests/artifacts/priority_scheduling/decision_multiagent_acceptance_20260826_r2.json); outcome artifact: [`evidence_multiagent_acceptance_20260826_r2.json`](project/tests/artifacts/priority_scheduling/evidence_multiagent_acceptance_20260826_r2.json).
- Stop condition met as `FAILED`; use the final barrier-controlled R3. A third failure must be `BLOCKED` and escalated to HITL.

### TICKET-MULTIAGENT-ACCEPTANCE-20260826-R3 | Final Barrier-Controlled Multi-Agent Acceptance | [STATUS: DONE]
**Severity**: HIGH
**Work Effort**: S
**Model / Reasoning Effort**: `gpt-5.6-sol` / `high` (`codex1`)
**Depends On**: failed R1/R2 evidence, explicit user authorization, and a declared no-editor window
**Blocks**: `TICKET-PRIORITY-005` documentation reconciliation; a third failure blocks the acceptance sequence and requires HITL
**Ownership Reserved**: Parent A only `.agents/rules/11-orchestrator-subagent-delegation.md`; Parent B only `docs/templates/MULTIAGENT_PROMPT_COMMAND.md`; the exactly one nested child only `.agents/skills/orchestrator-delegation/SKILL.md`. All ownership is read-only. No source/test/config/schema/dependency/generated-file edit, external CLI/network, work prompt, commit, deploy, credential, secret, account, or raw-provider stream action is permitted.

#### Objective, Acceptance, and Stop Condition
- **Completion evidence**: A nonce `MAG_R3_A_4B91` owned only `.agents/rules/11-orchestrator-subagent-delegation.md` over `[526892398954541,526942163463791]`; B nonce `MAG_R3_B_72CE` owned only `docs/templates/MULTIAGENT_PROMPT_COMMAND.md` over `[526894784557666,526928042686666]`; child nonce `MAG_R3_C_AF30` owned only `.agents/skills/orchestrator-delegation/SKILL.md` over `[526908527668291,526926446552541]`. The child interval is the exact three-subagent overlap: `17,918,884,250 ns`.
- The root received `R3_B_READY` and `R3_CHILD_READY`, then captured exactly `/root`, `parent_a`, `parent_a/nested_child_r3`, and `parent_b` with every status `running` before sending `RELEASE_R3_CHILD` and `RELEASE_R3_B`. A forwarded the exact child result and nonce. Before/after fingerprints are equal under safe marker `ef0e56c4...27000`; A/B/child all reported `changed_files=[]`.
- Decision artifact: [`decision_multiagent_acceptance_20260826_r3.json`](project/tests/artifacts/priority_scheduling/decision_multiagent_acceptance_20260826_r3.json); sanitized outcome artifact: [`evidence_multiagent_acceptance_20260826_r3.json`](project/tests/artifacts/priority_scheduling/evidence_multiagent_acceptance_20260826_r3.json). The standard is operationally accepted with no external action or repository mutation.
- Stop condition met `DONE`.

### TICKET-AGY1-SMOKE-20260826-R3 | One-Shot Post-QA AGY Smoke | [STATUS: BLOCKED — FRESH GATES]
**Severity**: HIGH
**Work Effort**: XS
**Model / Reasoning Effort**: `TBD — fresh decision required after dependencies`
**Depends On**: completed formal QA/review, successful R3 acceptance, and a current-session user-attested `agy1` Gemini `healthy` band
**Blocks**: any external AGY retry only
**Ownership Reserved**: read-only/no writable ownership. The future lane may make at most one AGY execute attempt only after its dependencies and all fresh pre-execution gates pass; it owns no source, schema, policy, dependency, test, generated, deployment, push, credential, secret, account, or raw-stream mutation.

#### Objective, Acceptance, and Stop Condition
- Do not dispatch now. Acceptance R3 is complete, but a fresh Rule 18 alias-specific `DispatchDecision`, fresh Rule 11 scheduling snapshot, `agy1` Gemini `healthy` band/HITL/ownership validation, approved read-only runtime boundary, and the one-attempt cap are still required. `agy1` Claude/GPT is exhausted and is never a route. No stale execution decision or snapshot is created or reusable now.
- If later authorized, record only safe outcome metadata and use successful AGY language `validated in-process only`; never claim independent portable/offline proof, and never restore or log raw streams.
- Stop `PENDING` until all dependency and fresh-gate evidence exists. Any external AGY retry without that new decision/snapshot is prohibited.

### TICKET-PRIORITY-002R3 | Third Safety Re-Review Remediation | [STATUS: DONE]
**Severity**: CRITICAL
**Work Effort**: L
**Model / Reasoning Effort**: `gpt-5.6-sol` / `high`
**Depends On**: `TICKET-PRIORITY-003R2`
**Blocks**: `TICKET-PRIORITY-003R3`
**Ownership Reserved**: developer lane for the exact R3 local source remediation and local validation only. Deploy, publish, push, secrets, account, external, destructive, configuration, generated-file, and PII actions are excluded; external actions remain unused and target-gated.

#### Objective, Acceptance, and Stop Condition
- **Exact R3 scope after session HITL approval**: remediate only the failed final re-review findings: (1) eliminate intermediate `.horo` symlink TOCTOU caused by secure traversal followed by pathname reopen; (2) make returned receipts verifiable after live-claim release; (3) prevent removal of the worktree-local `.horo` replay ledger through `git clean`; (4) prevent public `execute_invocation` from leaking the global lock; (5) handle partial writes rather than relying on one `os.write`; (6) provide fail-closed `fcntl`/POSIX and macOS realpath-containment compatibility; and (7) replace the global store lock behavior that prevents safe non-overlap concurrency. No unrelated refactor is authorized.
- Decision artifact: [`decision_priority_002r3.json`](project/tests/artifacts/priority_scheduling/decision_priority_002r3.json) (schema v1; policy `2026-08-25.2`; phase `implementation`; mutation mode; non-secret quota band `healthy`; `hitl_approved: true`; status `DOING`).
- Session HITL approval is recorded without approver identity. It authorizes only the exact R3 local remediation and local validation scope, including removal of explicitly identified obsolete code/tests if needed by the bounded workspace ticket. It does not authorize a `/root` glob deletion or broad/unrelated destructive action. External actions remain unused and may occur only with an exact target and all target-scoped safety gates.
- Completion evidence: only the dispatcher was edited in this round. `py_compile` and scoped diff checks passed; scheduler plus Claude governance checks passed `71`; focused coverage passed `155` with `30` expected contract failures. All eleven named direct reproductions passed: dirfd swap, durable outside-worktree derivation, independent receipt, lifecycle successful release, lifecycle failed release, write loop, unsupported platform, non-overlap concurrency, overlap, delete/reacquire, and replay.
- Residual environment boundary: managed sandbox policy blocked default macOS user-state creation, while the isolated explicit override worked. Record a later real-environment verification gate; do not treat the sandbox limitation as evidence of implementation failure.
- Stop condition met: bounded developer remediation evidence is complete. This did not close `TICKET-PRIORITY-004`; `TICKET-PRIORITY-003R3` independently completed QA and `TICKET-PRIORITY-003R3E` verified the default environment before the later read-only re-review, which subsequently failed and opened R4.

### TICKET-PRIORITY-003R3 | Third-Remediation Independent QA | [STATUS: DONE]
**Severity**: HIGH
**Work Effort**: S
**Model / Reasoning Effort**: `gpt-5.6-sol` / `high`
**Depends On**: `TICKET-PRIORITY-002R3`
**Blocks**: `TICKET-PRIORITY-003R3E`
**Ownership Reserved**: independent `qa_tester` lane for bounded R3 dispatcher QA only. This record authorizes no current source, test, hook, configuration, generated-file, external, or PII change.

#### Objective, Acceptance, and Stop Condition
- Independently validated the completed R3 dispatcher remediation using the isolated explicit state-location override. The exact three-suite command `python3 -m pytest -q tests/test_multiagent_ticket_scheduler.py tests/test_multiagent_prompt_command.py project/tests/test_claude_governance.py` exited `0` with `185 passed in 1.79s`; the scoped diff check exited `0`; the only QA change was `tests/test_multiagent_prompt_command.py`. Lifecycle, isolated-store, and delete/reacquire coverage is green.
- Decision artifact: [`decision_priority_003r3.json`](project/tests/artifacts/priority_scheduling/decision_priority_003r3.json) (schema v1; policy `2026-08-25.2`; phase `qa`; mutation mode; non-secret quota band `healthy`; `hitl_approved: true`; status `DONE`). Work Effort `S` remains the delivery-size scheduling input; reasoning effort `high` is a separate runtime-quality setting.
- The managed-sandbox block on default macOS user-state creation remains a residual environment limitation. The isolated override is valid only for QA; it does not establish default-state behavior.
- Stop condition met: independent QA evidence is complete. It released only `TICKET-PRIORITY-003R3E`; that completed environment gate then released the later review, which subsequently failed and opened R4. R4 is now complete; R5 source remediation blocks formal QA and `TICKET-PRIORITY-004`, while `TICKET-PRIORITY-005` remains pending.

### TICKET-PRIORITY-003R3E | Default macOS User-State Environment Verification | [STATUS: DONE]
**Severity**: HIGH
**Work Effort**: XS
**Model / Reasoning Effort**: `gpt-5.6-terra` / `high`
**Depends On**: `TICKET-PRIORITY-003R3`
**Blocks**: `TICKET-PRIORITY-004` re-review
**Owner**: `root orchestrator` completed exactly the one recorded waiver action. Delegation was not viable because the delegated `devops` attempt was sandbox-blocked and its escalation remained unapproved.

#### Rule 17 Single-Use Root Waiver
- `ROOT-WAIVER: ROOT-WAIVER-R3E-20260826` **[CONSUMED AND EXPIRED]**
- **Approval reference / date**: session user authorization on `2026-08-26`, recorded without approver identity: “I approve all for this session include deploy, publish, push, secret/account changes หรือ destructive actions”; bounded `/root/*` improve/refactor/fix/remove was also approved. This is evidence only for the exact action below, not a standing or broad waiver.
- **Executed one action / exact target**: root ran exactly one minimal Python verification for the current project invoking dispatcher `_secure_claim_directory` with no override. Sanitized result: `exit 0`, status `PASS`; `outside_worktree`, `canonical_namespace`, `directory_mode_0700`, `owned_by_current_user`, `retained_dirfd`, and `repo_horo_absent` were all `true`.
- **Explicit exclusions**: no claim or lock record, provider dispatch, deletion, authentication, credential or secret access, source/test/config/generated-file change, external action, or PII handling.
- **Stop / expiry**: the command returned the sanitized result above; the waiver was consumed by that one action and expired immediately. Any additional action requires fresh authorization.

#### Objective, Acceptance, and Stop Condition
- Verified the actual default macOS user-state claim directory derived by the dispatcher helper. This was an environment-evidence gate only; no claim or lock record was created and no provider was dispatched.
- Decision artifact: [`decision_priority_003r3e.json`](project/tests/artifacts/priority_scheduling/decision_priority_003r3e.json) (schema v1; policy `2026-08-25.2`; phase `operations`; mutation mode; non-secret quota band `healthy`; `hitl_approved: true`; status `DOING`). Work Effort `XS` is the delivery-size scheduling input; reasoning effort `high` is a separate runtime-quality setting.
- Acceptance met: sanitized `exit 0` / `PASS` evidence records the required environment assertions as `true`, without retaining credentials, authentication data, provider output, PII, or external execution evidence.
- Stop condition met: completion released only the final R3 read-only `TICKET-PRIORITY-004` re-review; that review later failed and opened the reserved R4 remediation. R4 is now complete; R5 source remediation blocks formal QA and `TICKET-PRIORITY-004`, while `TICKET-PRIORITY-005` remains pending.

### TICKET-PRIORITY-002R2 | Second Safety Re-Review Remediation | [STATUS: DONE]
**Severity**: CRITICAL
**Work Effort**: L
**Model / Reasoning Effort**: `gpt-5.6-sol` / `high`
**Depends On**: `TICKET-PRIORITY-003R`
**Blocks**: `TICKET-PRIORITY-003R2`
**Ownership Reserved**: completed `developer` lane for the bounded claim verify-to-spawn TOCTOU fix only. The approved scope remained source remediation and local tests only; deploy, push, secrets, and account changes remained excluded.

#### Objective, Acceptance, and Stop Condition
- **Exact proposed scope after approval**: remediate only the four High and two Medium findings recorded by the failed re-review: encoded decode-pipeline direct-child bypass; claim verify-to-spawn TOCTOU/deletion-reacquire; receipt binding to claim identity, completion, output, and workresult digests; durable temporary claim-store handling including parent-directory fsync; unsafe claim-reader symlink, mode, and special-file handling; and initial configuration/OSError ASCII-safe, path-safe errors.
- Existing decision artifact: [`decision_priority_002r2.json`](project/tests/artifacts/priority_scheduling/decision_priority_002r2.json) (schema v1; policy `2026-08-25.2`; phase `implementation`; mutation mode; non-secret quota band `healthy`; `hitl_approved: true`). No new decision is required because the existing approval already covers the TOCTOU finding.
- Existing HITL approval is recorded from the owner exactly as `อนุมัติ TICKET-PRIORITY-002R2`. It authorizes the exact scope, including claim verify-to-spawn TOCTOU/deletion-reacquire remediation, source remediation, and local tests only. Deploy, push, secrets, and account changes remain out of scope.
- Completion evidence: the bounded source fix changed one file; the exact regression passed (`1 passed`), and the claim subset passed (`31 passed, 83 deselected`). The deleted active locked entry is blocked from same-authorization reacquisition.
- Stop condition met: bounded remediation evidence is complete. `TICKET-PRIORITY-003R2` completed independent QA and released only the final read-only `TICKET-PRIORITY-004` re-review; `TICKET-PRIORITY-005` remains pending.

### TICKET-PRIORITY-003R2 | Second-Remediation Independent QA | [STATUS: DONE]
**Severity**: HIGH
**Work Effort**: S
**Model / Reasoning Effort**: `gpt-5.6-sol` / `high`
**Depends On**: `TICKET-PRIORITY-002R2`
**Blocks**: `TICKET-PRIORITY-004` re-review
**Ownership Reserved**: completed independent QA lane; no remediation source, hook, configuration, or generated-file edits are authorized by this evidence record.

#### Objective, Acceptance, and Stop Condition
- Independently validate the completed second remediation, update the 16 intentional legacy-contract fixtures, and add permanent R2 regression coverage for the durable `.horo` claim protocol, cooperative-lock residual, and completed-claim/receipt persistence without reopening implementation scope.
- Decision artifact: [`decision_priority_003r2.json`](project/tests/artifacts/priority_scheduling/decision_priority_003r2.json) (schema v1; policy `2026-08-25.2`; phase `qa`; mutation mode; non-secret quota band `healthy`; `hitl_approved: true`; historical `DOING` status).
- Work Effort `S` is the delivery-size scheduling input. Reasoning effort `high` is a separate runtime-quality setting for independent QA and cannot change scheduling order.
- Completion evidence: the exact combined three-suite QA command exited `0` with `185 passed in 2.01s`; scoped diff check exited `0`. The source-fix regression confirms that deleting the active locked entry blocks same-authorization reacquisition.
- Stop condition met: independent QA closes the R2 defect path and releases only the final read-only `TICKET-PRIORITY-004` re-review. `TICKET-PRIORITY-005` remains pending until that review reaches its own terminal verdict.

### TICKET-PRIORITY-002R | Safety-Review Remediation | [STATUS: DONE]
**Severity**: CRITICAL
**Work Effort**: M
**Model / Reasoning Effort**: `gpt-5.6-sol` / `high`
**Depends On**: `TICKET-PRIORITY-003`
**Blocks**: `TICKET-PRIORITY-003R`
**Ownership Reserved**: completed developer remediation lane; scope was source remediation and local tests only.

#### Objective, Acceptance, and Stop Condition
- Remediate all five review findings: atomic, non-replayable cross-process reservation/duplicate protection; shell redirection classification; shell-expanded direct-child coverage; prefix-overlap ownership detection; and PII redaction for receipts/results.
- Decision artifact: [`decision_priority_002r.json`](project/tests/artifacts/priority_scheduling/decision_priority_002r.json) (schema v1; policy `2026-08-25.2`; mutation mode; non-secret quota band `healthy`; `hitl_approved: true`; status `DONE`).
- Fresh approval record: approval was recorded on 2026-08-25 (Asia/Bangkok) after review of all five findings. It authorizes this developer lane only for source remediation and local tests; deploy, push, secrets, and account changes remain out of scope.
- Completion evidence: only `scripts/multiagent_prompt_command.py`, `scripts/multiagent_ticket_scheduler.py`, `.claude/hooks/adaptive_dispatch_guard.py`, and `.claude/hooks/orchestrator_only_guard.py` were changed in the remediation lane. `py_compile` and scoped diff checks exited `0`; focused pytest passed `106` in `1.13s`; the five-review-findings reproductions and shell-indirection reproductions were `OK`.
- Claim behavior: local-temp claims are atomic. Stale or ambiguous claims fail closed; that residual must be independently checked by `TICKET-PRIORITY-003R`.
- Stop condition met for bounded implementation evidence. `TICKET-PRIORITY-003R` is complete with independent QA evidence; `TICKET-PRIORITY-004` is reserved for read-only re-review and `TICKET-PRIORITY-005` remains pending.

### TICKET-PRIORITY-003R | Remediation Security Regression QA | [STATUS: DONE]
**Severity**: HIGH
**Work Effort**: S
**Model / Reasoning Effort**: `gpt-5.6-sol` / `high`
**Depends On**: `TICKET-PRIORITY-002R`
**Blocks**: releases `TICKET-PRIORITY-004` re-review
**Ownership Reserved**: independent `qa_tester` security-regression lane; no remediation source, hook, configuration, or generated-file edits.

#### Objective, Acceptance, and Stop Condition
- Independently validate the completed remediation against all five review findings, shell indirection, atomic local-temp claim behavior, and fail-closed stale or ambiguous claim handling without reopening implementation scope.
- Decision artifact: [`decision_priority_003r.json`](project/tests/artifacts/priority_scheduling/decision_priority_003r.json) (schema v1; policy `2026-08-25.2`; phase `qa`; mutation mode; non-secret quota band `healthy`; `hitl_approved: true`).
- Work Effort `S` is the delivery-size scheduling input. Reasoning effort `high` is a separate runtime-quality setting for independent remediation security QA and cannot change scheduling order.
- Completion evidence: the combined focused pytest command over the three approved suites exited `0` with `173 passed` in `1.53s`; scoped diff check exited `0`; all five remediation areas were covered and the Rule 11 matrix was green.
- Stop condition met: independent QA evidence releases `TICKET-PRIORITY-004` for reserved read-only re-review. `TICKET-PRIORITY-005` remains pending; this ticket did not authorize deploy, push, authentication, secret, or account actions.

### TICKET-PRIORITY-005 | Final Sync and Reconciliation | [STATUS: PENDING]
**Severity**: MEDIUM
**Work Effort**: XS
**Model / Reasoning Effort**: `gpt-5.6-terra` / `medium`
**Depends On**: `TICKET-PRIORITY-004`
**Blocks**: Sprint closure
**Ownership**: generated ecosystem sync through prescribed script plus `PROJECT_TASKS.md` and `plans/plan.md` reconciliation

#### Objective, Acceptance, and Stop Condition
- After all legacy enforcement/governance edits, run `python3 scripts/sync_ai_agent_ecosystem.py --sync`, then `python3 scripts/sync_ai_agent_ecosystem.py --check`, focused governance tests, and `git diff --check`.
- The preliminary sync under `TICKET-PRIORITY-001` does not close this final post-implementation checkpoint.
- Stop `DONE` only after every upstream ticket has evidence and statuses match the repository; otherwise record the exact blocker/HITL action.

### Sprint Checkpoints
| Checkpoint | Owner | State | Required Evidence |
|---|---|---|---|
| `CP-PRIORITY-01` | `business_analyst` | DONE | authoritative/mirrored policy plus ecosystem sync/check `[OK]` |
| `CP-PRIORITY-02` | `developer` | DONE | syntax and scoped diff checks exited `0`; governance regression `11` passed; dispatcher regression `76` passed with `18` legacy fixtures reserved for QA; scheduler functional checks passed |
| `CP-PRIORITY-03` | `qa_tester` | DONE | baseline `18` missing-snapshot failures reproduced; focused regression `154 passed` in `1.14s`, exit `0`; scoped diff check exit `0` |
| `CP-PRIORITY-04` | `code_reviewer` | BLOCKED-R3 | final re-review verdict `NEEDS_HITL — NOT READY`; blocked pending exact R3 remediation and a new independent re-review |
| `CP-PRIORITY-04R` | `developer` | DONE | four owned remediation files; syntax and scoped diff checks exited `0`; focused pytest `106 passed` in `1.13s`; five-finding and shell-indirection reproductions `OK` |
| `CP-PRIORITY-03R` | `qa_tester` | DONE | combined focused pytest exit `0`, `173 passed` in `1.53s`; scoped diff check exit `0`; five remediation areas covered and Rule 11 matrix green |
| `CP-PRIORITY-04R2` | `developer` | DONE | one-file bounded source fix; exact regression `1 passed`; claim subset `31 passed, 83 deselected`; deleted active locked entry cannot be reacquired by the same authorization |
| `CP-PRIORITY-03R2` | `qa_tester` | DONE | exact combined three-suite QA exit `0`, `185 passed in 2.01s`; scoped diff check exit `0`; deleted active-entry reacquisition is blocked |
| `CP-PRIORITY-04R3` | `developer` | DONE | dispatcher-only change; `py_compile` and scoped diff passed; scheduler plus Claude checks `71`; focused coverage `155` with `30` expected contract failures; eleven direct reproductions passed |
| `CP-PRIORITY-03R3` | `qa_tester` | DONE | exact three-suite QA exited `0` with `185 passed in 1.79s`; lifecycle, isolated-store, and delete/reacquire coverage green |
| `CP-PRIORITY-04R4` | `developer` | DONE | `py_compile` and scoped diff passed; R4 `6`, scheduler plus Claude `71`, and prompt plus R4 `119` passed with one intentional legacy assertion delta; no Critical/High reviewer finding |
| `CP-PRIORITY-04R5` | `developer` | DONE | source frozen; `py_compile` and scoped diff passed; R4 `6`, combined `190` with one intentional legacy `ownership_sha256` assertion, and direct temporary recovery passed |
| `CP-PRIORITY-04R5-REVIEW` | `code_reviewer` | DONE — READY_FOR_PROD | no Critical/High finding; combined `213`, sync, locked-dependency, secret, and diff checks passed; wrapper timeout Medium plus reviewer Medium/Low residuals retained |
| `CP-AGY1-QUOTA-R1` | `devops` | BLOCKED — CONSUMED | one query ended `sanitization_failure`; no retry; later routing uses safe user-attested alias bands |
| `CP-MULTIAGENT-ACCEPTANCE-R1` | `orchestrator` | FAILED — SCOPE | child scope overlapped Parent A |
| `CP-MULTIAGENT-ACCEPTANCE-R2` | `orchestrator` | FAILED — PEAK | B ended before child began, so no exact `4/4` peak |
| `CP-MULTIAGENT-ACCEPTANCE-R3` | `orchestrator` | DONE | root barrier captured all four agents `running`; exact scopes/nonces/forwarding/fingerprint/no-change and triple overlap passed |
| `CP-PRIORITY-05` | `business_analyst` | PENDING — RELEASE COMPLETION | final sync/check, diff check, status reconciliation after Release Completion gates |

---

## SPRINT: Release Completion — 2026-08-26
**Grill Gate Status**: APPROVED — explicit user objective covers completing current governed changes and tickets, a safe commit/push to provisional `origin/main`, and production deployment. The audit-confirmed canonical architecture is Hugging Face Docker backend `pphothidaen/horoconsultant-core-backend` plus Vercel static UI; static deployment to that backend Space is retired. This approval authorizes planning and reservations only at this checkpoint; every external mutation remains blocked until its preceding evidence gates pass.
**Scope Audit Baseline**: branch `main`, configured `origin`, no staged changes, and a dirty worktree containing governed configuration/source/test/data/documentation changes plus new scheduling artifacts. Dispatcher preflight, CI/governance architecture, and Docker publisher provenance each require a bounded remediation. `project/api_router.py` and the two dirty data files are preserved/excluded in separate provenance blockers; no clean-up, staging, or overwrite is authorized.
**Rollback**: after a later verified release commit, use an exact `git revert <release-commit>` and restore the Hugging Face Space to its recorded prior revision; no broad reset, cleanup, or secret operation is authorized.
**Live Slots**: root coordination plus BSA reconciliation are observed; prior workflow/publisher/diagnostic lanes are frozen. Rule 11 reserves only ticket44R2 as the next useful read-only lane. Ticket45, metadata21C, final QA22, package, and every external lane remain dependency-blocked.

| Ticket ID | Owner | Severity / Work | Status | Depends On | Ownership and gate |
|---|---|---|---|---|---|
| `TICKET-RELEASE-COMPLETE-20260826-01-SCOPE` | `code_reviewer` | HIGH / S | DONE | R3 acceptance DONE | Read-only provenance audit completed; dispatcher/architecture/publisher remediations required and router/data remain excluded |
| `TICKET-RELEASE-COMPLETE-20260826-02-TARGET` | `devops` | HIGH / XS | DONE | R3 acceptance DONE | Read-only target audit completed: `origin/main`, HF Docker backend, Vercel static UI; Azure/Fly prohibited |
| `TICKET-RELEASE-COMPLETE-20260826-03-RECONCILE` | `business_analyst` | HIGH / S | DOING (RESERVED — ROLLING) | validated remediation plans | Current-ticket/status/decision reconciliation and release documentation only; source/schema/test/dependency edits excluded |
| `TICKET-RELEASE-COMPLETE-20260826-04-RELEVANT-QA` | `qa_tester` | HIGH / M | PENDING | 18 + 22 + 27 + 28 + 33 + 34 + 35 + 36 + 37 + 03 | Relevant governed-change and regression matrix; read-only test execution and sanitized evidence only |
| `TICKET-RELEASE-COMPLETE-20260826-05-FULL-QA` | `qa_tester` | HIGH / L | PENDING | 18 + 22 + 27 + 28 + 33 + 34 + 35 + 36 + 37 + 03 | Full repository QA; read-only test execution and sanitized evidence only |
| `TICKET-RELEASE-COMPLETE-20260826-06-PACKAGE` | `devops` | HIGH / S | PENDING | 04 + 05 + 26 | Secret scan and Docker HF payload dry-run only; no publish/upload |
| `TICKET-RELEASE-COMPLETE-20260826-07-REVIEW` | `code_reviewer` | CRITICAL / S | PENDING | 03 + 04 + 05 + 06 + 26 | Final code-review `READY_FOR_PROD`, commit provenance, and release-gate verdict; read-only |
| `TICKET-RELEASE-COMPLETE-20260826-08-COMMIT-PUSH` | `devops` | CRITICAL / XS | BLOCKED — EXTERNAL MUTATION | 07 | Exact scoped commit and push verification to `origin/main`; no action until all gates pass |
| `TICKET-RELEASE-COMPLETE-20260826-09-HF-DEPLOY` | `devops` | CRITICAL / S | BLOCKED — EXTERNAL MUTATION | 08 | Publish only to HF Docker backend `pphothidaen/horoconsultant-core-backend`; no action until push verification passes |
| `TICKET-RELEASE-COMPLETE-20260826-10-HEALTH-VERSION` | `devops` | HIGH / S | BLOCKED — POST-DEPLOY | 09 | Live Docker backend health and exact version verification only |
| `TICKET-RELEASE-COMPLETE-20260826-11-UI-VISUAL` | `ui_visual_tester` | HIGH / M | BLOCKED — POST-DEPLOY | 09 | Post-deploy Vercel static UI E2E/button/visual evidence only |
| `TICKET-RELEASE-COMPLETE-20260826-12-CLOSURE` | `business_analyst` | HIGH / XS | BLOCKED — FINAL EVIDENCE | 10 + 11 | Final task/plan/README/HOWTO reconciliation only after all release evidence is present |

### Release Completion Acceptance and Stop Conditions
- Every current ticket must be reconciled to evidence-backed `DONE` or an exact retained blocker; `TICKET-AGY1-SMOKE-20260826-R3` must retain its independent fresh-decision gate and cannot be inferred from acceptance success.
- Release gates are: source freeze and scope/provenance audit; relevant and full QA; zero-leak secret scan; payload dry-run; reviewer `READY_FOR_PROD`; safe exact commit; push verification; HF publish; live health/version; and post-deploy E2E/visual evidence.
- Do not stage, commit, push, upload, deploy, use credentials, or call external production endpoints before the preceding ticket evidence is `DONE`. On any failed gate, stop and return only the owning remediation ticket; do not perform unrelated destructive cleanup.

### Pre-QA Remediation Reservations
| Ticket ID | Owner | Severity / Work | Status | Exact ownership | Depends On |
|---|---|---|---|---|---|
| `TICKET-RELEASE-COMPLETE-20260826-13-DISPATCHER-PREP` | `developer` | HIGH / S | DONE — PLAN VALIDATED | `scripts/multiagent_prompt_command.py`; `.agents/config/multiagent_prompt_command.runtime-readonly-v2.yaml` read-only | 01 + 02 |
| `TICKET-RELEASE-COMPLETE-20260826-14-WORKFLOWS-PREP` | `developer` | HIGH / S | DONE — PLAN VALIDATED | `.github/workflows/azure_cost_guard.yml`, `azure_deploy.yml`, `deploy.yml`, `fly_deploy.yml`, `hf_backend_deploy.yml` read-only | 01 + 02 |
| `TICKET-RELEASE-COMPLETE-20260826-15-GOVERNANCE-PREP` | `business_analyst` | HIGH / S | DONE — PLAN VALIDATED | Rule 07, Rule 16, and the DevOps/QA/HF release skills read-only | 01 + 02 |
| `TICKET-RELEASE-COMPLETE-20260826-16-PUBLISHER-PREP` | `developer` | HIGH / S | DONE — FROZEN | Detailed Docker publisher contract validated; split into 21A–21D with one editor per source/schema/metadata/workflow unit | 01 + 02 |
| `TICKET-RELEASE-COMPLETE-20260826-17-DISPATCHER-FIX` | `developer` | CRITICAL / S | DONE — FROZEN | same two dispatcher/config files, one editor | 13 |
| `TICKET-RELEASE-COMPLETE-20260826-18-DISPATCHER-QA` | `qa_tester` | HIGH / S | DONE — FROZEN | `tests/test_multiagent_prompt_command.py`; `tests/test_multiagent_prompt_command_r4.py`; 23 structural isolated-home fixtures and marker removal accepted through ticket 37's focused/combined green evidence | 17 + 37 |
| `TICKET-RELEASE-COMPLETE-20260826-19-WORKFLOWS-FIX` | `developer` | CRITICAL / M | DONE — FROZEN | exact five-workflow group, one editor | 14 |
| `TICKET-RELEASE-COMPLETE-20260826-20-GOVERNANCE-FIX` | `business_analyst` | HIGH / M | DONE — FROZEN | Rule 07/16 and exact DevOps/QA/HF skill group; generated mirrors via sync only | 15 |
| `TICKET-RELEASE-COMPLETE-20260826-21A-PUBLISHER-CORE` | `developer` | CRITICAL / M | DONE — FROZEN | `scripts/publish_space_hf.py` only. Source SHA-256 `3483b2df51fb2b6e2127ed286c58b733ae9cb73855397c6f6d9cf33da3601da0`; source diff `1544 additions/344 deletions`. Frozen CLI persists dry-run manifest, binds live publish to manifest plus expected parent revision, persists sanitized receipt, and guards artifacts; three intentional stale publisher fixtures move only to 22A | 16 + 21B |
| `TICKET-RELEASE-COMPLETE-20260826-21B-RELEASE-SCHEMAS` | `developer` | CRITICAL / S | DONE — FROZEN | `project/schemas/release-manifest-v1.schema.json`; `project/schemas/release-receipt-v1.schema.json` only. Closed Draft 2020-12 release contract; runtime invariants remain 21A responsibility | 16 |
| `TICKET-RELEASE-COMPLETE-20260826-21C-RELEASE-METADATA` | `developer` | HIGH / XS | BLOCKED — TICKET45 IMMUTABLE SOURCE COMMIT | `project/static/version.json`; `public/version.json` only. Exact mirrors with version plus canonical `release_source_*` identity fields; no legacy commit/timestamp/status or dirty-HEAD fallback. Run only after ticket45 records the immutable local source identity; never fabricate a placeholder | 16 + 21B + 45 |
| `TICKET-RELEASE-COMPLETE-20260826-21D-PUBLISHER-WORKFLOW` | `developer` | HIGH / XS | DONE — FROZEN | `.github/workflows/hf_backend_deploy.yml` only. SHA-256 `276899e3dd6cec5531b3eb97e731f096a8998b08ec8830c81237c31b17dbf0a0`; diff 495 additions/148 deletions. YAML/Ruby, 14 shell and 8 Python/static interface checks, Actions regression 59, ecosystem check, diff check, and secret scan 0/1,913 passed; no network/deploy/push | 21A + 21B |
| `TICKET-RELEASE-COMPLETE-20260826-21D-QA2-WORKFLOW-LEGACY` | `qa_tester` | HIGH / XS | DONE — FROZEN | `project/tests/test_azure_release.py` only. The two legacy publisher/workflow assertions align with the frozen manifest/receipt/expected-parent CLI and guarded validated artifacts; independent read-only review passed against workflow SHA-256 `276899e3dd6cec5531b3eb97e731f096a8998b08ec8830c81237c31b17dbf0a0` | 21D |
| `TICKET-RELEASE-COMPLETE-20260826-22A-PUBLISHER-CORE-FIXTURE-QA` | `qa_tester` | HIGH / XS | DONE — FROZEN | `tests/test_publish_space_hf.py` only. Frozen publisher fixtures passed `34`; combined publisher plus governance pre-metadata coverage passed `44`. No final metadata/package claim is inferred | 21A + 21B |
| `TICKET-RELEASE-COMPLETE-20260826-22-PUBLISHER-QA` | `qa_tester` | HIGH / S | BLOCKED — 21C METADATA | `project/tests/test_hf_release_governance.py` only. Final integration verifies committed metadata parity, workflow handoff, HfApi-mode limitation, and the enforced `100644` baseline after ticket21C freezes | 21A + 21B + 21C + 21D + 21D-QA2 + 22A |
| `TICKET-RELEASE-COMPLETE-20260826-23-DOCS` | `business_analyst` | HIGH / S | PENDING — SOURCE FREEZE | `PROJECT_TASKS.md`, `plans/plan.md`, `README.md`, `HOWTO.md` only | 17 + 19 + 20 + 21A + 21B + 21C + 21D + 29 + 30 + 31 + 32 |
| `TICKET-RELEASE-COMPLETE-20260826-24-ROUTER-PROVENANCE` | `developer` | HIGH / XS | BLOCKED — OWNER/PROVENANCE | `project/api_router.py` preserved; never stage/edit in current release | explicit owner/provenance decision |
| `TICKET-RELEASE-COMPLETE-20260826-25-DATA-PROVENANCE` | `business_analyst` | HIGH / XS | BLOCKED — OWNER/PROVENANCE | `project/data/bazi_bazi_manual_chatml.jsonl`; `project/data/distillation_checklist.json` preserved; never stage/edit in current release | explicit owner/provenance decision |
| `TICKET-RELEASE-COMPLETE-20260826-26-CLEAN-CHECKOUT-GATE` | `qa_tester` | HIGH / M | PENDING — SOURCE FREEZE | Validated temporary clean checkout only; read-only relevant/full QA and Docker package dry-run evidence; no workspace edit, staging, publish, or upload | 18 + 22 + 23 + 27 + 28 + 33 + 34 + 35 + 36 + 37 |
| `TICKET-RELEASE-COMPLETE-20260826-27-WORKFLOW-QA` | `qa_tester` | HIGH / S | DONE — FROZEN | `project/tests/test_azure_release.py`; `project/tests/test_github_actions_regression.py` only. Azure/Fly tombstone and HF Docker workflow contract evidence: 70 + 33 passed; sync and secret scan green | 19 |
| `TICKET-RELEASE-COMPLETE-20260826-28-CLAUDE-RULE-FIX` | `business_analyst` | HIGH / XS | DONE — FROZEN | `.claude/rules/hf-static-release-verification.md` only. Docker/Vercel, Static-to-backend/Azure/Fly prohibition, atomic manifest/CAS/rollback expectation, and validated-in-process/elided-stream boundary verified | 20 |
| `TICKET-RELEASE-COMPLETE-20260826-28R2-CLAUDE-RULE-VIEWPORT-FIX` | `business_analyst` | HIGH / XS | DONE — FROZEN | `.claude/rules/hf-static-release-verification.md` only. Restored exact five canonical viewports: `desktop-4k`, `laptop-standard`, `tablet-portrait`, `mobile-ios`, `mobile-compact`; sync check green | 28 |
| `TICKET-RELEASE-COMPLETE-20260826-29-PRODUCTION-MONITOR-FIX` | `developer` | HIGH / S | DONE — FROZEN | `.github/workflows/production_monitor.yml` only. Canonical HF Docker backend and separate Vercel UI monitor contract; source freeze is complete. Live-green verification remains gated by canonical metadata ticket 21C | 19; 21C for live green |
| `TICKET-RELEASE-COMPLETE-20260826-30-FLY-ARTIFACT-RETIREMENT` | `developer` | HIGH / S | DONE — FROZEN | `fly.toml`; `scripts/trigger_all_github_actions.py` only. Active Fly config retired; dispatch script retains a non-dispatching Fly tombstone and Git preserves history | 19 |
| `TICKET-RELEASE-COMPLETE-20260826-31-GATEWAY-UI-FALLBACK-FIX` | `developer` | CRITICAL / M | DONE — FROZEN | `api/gateway.js`; `api/health.js`; `project/static/app.js`; `public/app.js` only. Azure fallback removed and static/public UI mirrors match. Separate `api/index`/admin/HITL routing audit is pending and does not expand this frozen owner scope | 20 |
| `TICKET-RELEASE-COMPLETE-20260826-32-LOCAL-RUNNER-NEUTRALIZATION` | `developer` | HIGH / S | DONE — FROZEN | `scripts/auto_deploy_all.sh`; `scripts/hermes_sdlc_runner.sh`; `scripts/agentic_pipeline.sh` only. Neutralized legacy Azure/Fly/public release behavior with retained audit output | 20 |
| `TICKET-RELEASE-COMPLETE-20260826-33-PRODUCTION-MONITOR-QA` | `qa_tester` | HIGH / XS | DONE — FROZEN | New `project/tests/test_production_monitor_release_contract.py` only; new contract completion reported after completed 33R2 | 29 + 33R2 |
| `TICKET-RELEASE-COMPLETE-20260826-33R2-WORKFLOW-ASSERTION-CORRECTION` | `qa_tester` | HIGH / XS | DONE — FROZEN | `project/tests/test_github_actions_regression.py` only. Stale LuoPan assertion corrected: 59 + 103 passed; sync/secret/diff green | 27 |
| `TICKET-RELEASE-COMPLETE-20260826-34-FLY-ARTIFACT-QA` | `qa_tester` | HIGH / XS | DONE — FROZEN | New `project/tests/test_fly_artifact_retirement.py` only; retirement/tombstone boundary passed: 74; sync/secret/diff green | 30 |
| `TICKET-RELEASE-COMPLETE-20260826-35-GATEWAY-UI-QA` | `qa_tester` | HIGH / S | DONE — FROZEN | `tests/api_gateway_cors_contract.test.mjs`; new `project/tests/test_gateway_ui_release_contract.py` only; Node 8 + Python 33 passed; sync/secret/diff green | 31 + 35R2 |
| `TICKET-RELEASE-COMPLETE-20260826-35R2-WEB-REGRESSION-ASSERTION-CORRECTION` | `qa_tester` | HIGH / XS | DONE — FROZEN | `project/tests/test_web_regression.py` only. Obsolete Azure hostname assertion corrected: 15 plus focused coverage passed; sync/secret/diff green | 31 |
| `TICKET-RELEASE-COMPLETE-20260826-36-LOCAL-RUNNER-QA` | `qa_tester` | HIGH / XS | DONE — FROZEN | New `project/tests/test_local_release_runner_contract.py` only; 15 + 16 passed; sync/secret/diff green | 32 |
| `TICKET-RELEASE-COMPLETE-20260826-37-DISPATCHER-SCHEMA-FIXTURE-QA` | `qa_tester` | HIGH / XS | DONE — FROZEN | `tests/test_multiagent_receipt_schema.py` only. Temporary mode-0700 isolated `CODEX_HOME`/`AGY_HOME` route fields without credential files; focused 3 and combined 222 passed, with uv/pycompile/diff green | 17 |
| `TICKET-RELEASE-COMPLETE-20260826-38-API-INDEX-VERCEL-PINNING` | `developer` | HIGH / S | DONE — FROZEN | `api/index.js`; `vercel.json` only. Canonical target pinning complete; removed 1,540 legacy lines without expanding into gateway/admin/HITL | 31 |
| `TICKET-RELEASE-COMPLETE-20260826-38-QA` | `qa_tester` | HIGH / S | DONE — FROZEN | `project/tests/test_cors_security.py`; `tests/api_index_vercel_contract.test.mjs` only. Node 7 + Python 5 focused, Node 15 + Python 37 adjacent; sync/diff/secret green | 38 |
| `TICKET-RELEASE-COMPLETE-20260826-39-ADMIN-HITL-ROUTING` | `developer` | HIGH / M | BLOCKED — HITL SCOPE AUDIT | `project/admin_router.py`; `project/hitl_router.py` only. Align backend security/routing only after `required_human_review=true`, `/hitl/scope-audit?source_domain=metaphysical-domain-engine` passes, and owner sign-off is recorded | 38 + HITL scope audit |
| `TICKET-RELEASE-COMPLETE-20260826-39-QA` | `qa_tester` | HIGH / S | PENDING — SOURCE FREEZE | New `project/tests/test_admin_hitl_release_routing.py` only; verify backend security/routing and required-human-review behavior | 39 |
| `TICKET-RELEASE-COMPLETE-20260826-39S-ADMIN-HITL-STATIC-AUDIT` | `code_reviewer` | HIGH / XS | BLOCKED — HITL SCOPE AUDIT | `project/static/admin.html`; `project/static/hitl.html` read-only only. Separate static-page audit; no mutation before the mandatory HITL scope audit and owner sign-off | 38 + HITL scope audit |
| `TICKET-RELEASE-COMPLETE-20260826-39S-QA` | `qa_tester` | HIGH / XS | PENDING — 39S AUDIT | New `project/tests/test_admin_hitl_static_release_contract.py` only | 39S |
| `TICKET-RELEASE-COMPLETE-20260826-40A-AZURE-COST-GUARD` | `developer` | HIGH / XS | DONE — FROZEN | `.github/workflows/azure_cost_guard.yml` only. Dormant legacy tombstone: no schedule, authentication, actions, network, or permissions | 27 |
| `TICKET-RELEASE-COMPLETE-20260826-40A-QA` | `qa_tester` | HIGH / XS | DONE — FROZEN | `project/tests/test_azure_release.py`; `project/tests/test_github_actions_regression.py` only. Reopened sequentially for both stale assertions: 70 + 114 passed; sync/secret/diff green | 40A + 27 + 33R2 |
| `TICKET-RELEASE-COMPLETE-20260826-40B1-SECRET-SYNC-ENV` | `developer` | HIGH / S | DONE — FROZEN | `scripts/sync_doppler_secrets.py`; `.env.example` only. Default validation is opt-in/no implicit `.env` or network; apply requires explicit env file; retired Azure/Fly keys are excluded while HF/Vercel entries remain | 20 |
| `TICKET-RELEASE-COMPLETE-20260826-40B1-QA` | `qa_tester` | HIGH / XS | DONE — FROZEN | New `project/tests/test_secret_sync_release_contract.py` only. Opt-in apply/env-file, no implicit `.env`/network, retired-key exclusion, HF/Vercel preservation, value redaction, and environment-example contract passed: focused 6 + adjacent 24; all gates green. The active 11-vs-13 failure remains QA40B2-only | 40B1 |
| `TICKET-RELEASE-COMPLETE-20260826-40B2-TRIGGER-INVENTORY` | `developer` | HIGH / XS | DONE — FROZEN | `scripts/trigger_all_github_actions.py` only. Final inventory is 11 active and 4 historical typed `RETIRED` entries; active dispatch has no Azure cost guard/tombstone path | 30 + 34 |
| `TICKET-RELEASE-COMPLETE-20260826-40B2-QA` | `qa_tester` | HIGH / XS | SUPERSEDED — 40B2R2 PASSED | Its original 21/1 and 91/1 source-defect result is preserved. The repair and re-run are frozen in 40B2R1/40B2R2; the unrelated publisher assertion is excluded | 40B2 + 34 + 40B2R1 |
| `TICKET-RELEASE-COMPLETE-20260826-40B2R1-TRIGGER-YAML-INVENTORY` | `developer` | HIGH / XS | DONE — FROZEN | `scripts/trigger_all_github_actions.py` only. Both `.yml` and `.yaml` candidates are inventoried and unreviewed YAML fails closed; no subprocess/network execution. Released 40B2R2 only | 40B2 |
| `TICKET-RELEASE-COMPLETE-20260826-40B2R2-QA` | `qa_tester` | HIGH / XS | DONE — FROZEN | Reused only `project/tests/test_fly_artifact_retirement.py`; `project/tests/test_trigger_inventory_retirement.py`. Frozen 11-active/4-retired contract passed focused 22/22 + combined 81/81; unrelated publisher assertion remains outside this ticket | 40B2R1 |
| `TICKET-RELEASE-COMPLETE-20260826-40C-TRIGGER-INVENTORY` | `developer` | HIGH / XS | SUPERSEDED — 40B2 | No active ownership; consolidated into 40B2 to keep one editor for `scripts/trigger_all_github_actions.py` | 40B2 |
| `TICKET-RELEASE-COMPLETE-20260826-40C-QA` | `qa_tester` | HIGH / XS | SUPERSEDED — 40B2-QA | No active ownership; consolidated into 40B2-QA | 40B2-QA |
| `TICKET-RELEASE-COMPLETE-20260826-41A-BACKEND-DIAGNOSTICS` | `developer` | MEDIUM / XS | DONE — FROZEN | `scripts/grafana_cloud_exporter.py`; `scripts/run_remote_api_live_test.py`; `scripts/test_live_e2e_network.py` only. Final hashes begin `b0b2f4b9`, `2fb600f4`, and `f4a00dcf`; lint/format/compile/diff, 3 dry CLIs, 39 mocked assertions, and 14 compatible regressions passed; secret scan was 0/1,910 with no forbidden target, PII, non-ASCII, or network action | 20 |
| `TICKET-RELEASE-COMPLETE-20260826-41A-QA` | `qa_tester` | MEDIUM / XS | DONE — FROZEN | New `project/tests/test_backend_diagnostic_release_contract.py` only. Canonical Docker/read-only/offline/fail-closed contract passed `74`; adjacent compatibility passed `16` | 41A |
| `TICKET-RELEASE-COMPLETE-20260826-41A-QA2-GRAFANA-LEGACY` | `qa_tester` | MEDIUM / XS | DONE — FROZEN | `project/tests/test_grafana_cloud_exporter.py` only. Four obsolete credential/POST expectations now enforce rejection/no-I/O behavior and canonical sanitized messages; `24 passed` | 41A |
| `TICKET-RELEASE-COMPLETE-20260826-41B-UI-DIAGNOSTICS` | `developer` | HIGH / XS | DONE — FROZEN | `scripts/test_static_hf_space_questions.py`; `scripts/run_live_e2e_hf_space.py`; `scripts/audit_ui_overlap.py`; `scripts/run_vercel_prod_curl_regression.py` only. Offline evidence passed lint/format/compile/diff; six 4/4 CLI/target/mock groups; curl 3/3; Playwright 10/10; overlap 5/5; exact five viewports; adjacent Python 15 and Node 15; ASCII/secret/PII/retired-target scans green. No live network/browser or artifact write occurred | 20 |
| `TICKET-RELEASE-COMPLETE-20260826-41B-QA` | `qa_tester` | HIGH / XS | DONE — FROZEN | New `project/tests/test_ui_diagnostic_release_contract.py` only. Canonical Vercel/Docker, offline/live opt-in, five-viewport, retired-target, and workstation exclusions passed `53`; adjacent compatibility passed `23` | 41B |
| `TICKET-RELEASE-COMPLETE-20260826-42-OPERATIONAL-DOCS` | `business_analyst` | HIGH / XS | PENDING — POST-SOURCE METADATA | `docs/RELEASE_HANDOFF_CHECKLIST.md`; `docs/RELEASE_ROLLBACK_RUNBOOK.md` only; historical docs excluded and neither file may enter ticket45 | 21A + 21B + 21C + 21D + 41A + 41B |
| `TICKET-RELEASE-COMPLETE-20260826-42-QA` | `code_reviewer` | HIGH / XS | PENDING — DOCS FREEZE | Read-only review of ticket42's two files only | 42 |
| `TICKET-RELEASE-COMPLETE-20260826-43-AI-INFERENCE-SKILL-REF` | `business_analyst` | HIGH / XS | PENDING — POST-SOURCE PACKAGING | `.agents/skills/ai-inference-verifier/SKILL.md` only; generated mirrors only through mandated sync. It and ticket43-QA are excluded from ticket45 | 41B |
| `TICKET-RELEASE-COMPLETE-20260826-43-QA` | `qa_tester` | HIGH / XS | PENDING — SKILL FREEZE | New `project/tests/test_ai_inference_skill_reference.py` only | 43 |
| `TICKET-RELEASE-COMPLETE-20260826-44-PRE-SOURCE-INTEGRATION-QA` | `qa_tester` / runtime `codex1_gateway_review` | CRITICAL / S | BLOCKED — ATTEMPT1 STALE PATH | Command1 `151 passed`; command2 `70 passed`; command3 referenced stale `project/tests/test_hf_release_governance.py`, exited `4`, and collected no tests. No source/test mutation or external action; inventory digest unchanged. Original decision/snapshot are immutable | frozen prerequisites |
| `TICKET-RELEASE-COMPLETE-20260826-44R2-PRE-SOURCE-INTEGRATION-QA` | `qa_tester` / runtime `codex1_gateway_review` | CRITICAL / S | DONE | Corrected offline matrix commands 1–9 all exited `0`; command1 independently confirmed `151 passed in 1.48s`; commands2–5/other test groups reported `337` tests in combined output in addition to command1's `151` (not treated as a total); command4 emitted one deprecation warning; JSON schemas valid; ecosystem sync and `git diff --check` passed. QA changed no files; pre-existing dirty files remained unchanged. No release approval or source-commit eligibility inferred | 21A + 21B + 21D + 22A + 41A-QA + 41A-QA2 + 41B-QA |
| `TICKET-RELEASE-COMPLETE-20260827-POINTER-CENTRALIZATION-COMMIT` | `devops` | HIGH / XS | READY — FRESH LOCAL DOCUMENTATION COMMIT | Already-completed pointer centralization in `project_tickets.md`; stage and create exactly one local commit containing exactly `project_tickets.md`. Do not stage, edit, or commit any other path. No push, deploy, publish, secrets, metadata, release evidence, or ticket45 allowlist/state change. Fresh user authorization: “investigate blocked and fix it” on 2026-08-27 authorizes this local documentation remediation only. Depends on the current intentional dirty pointer; stop if its content, path, or scope changes. Acceptance: pointer remains compatibility-only and points to canonical docs; pre-commit path check is exactly one path; one local commit records the pointer change; ticket45 remains separately blocked and its frozen allowlist is unchanged | none |
| `TICKET-RELEASE-COMPLETE-20260827-VAULT-SYNC-STATUS-COMMIT` | `devops` | HIGH / XS | READY — FRESH LOCAL GENERATED-ARTIFACT COMMIT | Generated `project/data/vault_sync_status.json` only; stage and create exactly one separate local commit containing exactly this path. No edit to generated content, source, scripts, tests, workflows, protected training data, ticket45 allowlist/state, or decision artifacts; no push, deploy, publish, credentials, secrets, or release approval. Fresh user authorization: “investigate blocked and fix it” on 2026-08-27 authorizes clearing this release-inventory blocker only. Acceptance: pre-commit diff remains exactly the `last_sync_timestamp` field change, all inventory counts/folder configuration remain unchanged, `scripts/sync_gdrive_vault.py` remains the generating owner, and the commit path set is exactly one file. Preserve ticket45's frozen allowlist and the protected data provenance blockers `project/data/bazi_bazi_manual_chatml.jsonl` and `project/data/distillation_checklist.json`; this ticket does not make either eligible. | 44R2; fresh Rule 18 decision/snapshot |
| `TICKET-RELEASE-COMPLETE-20260826-45-LOCAL-IMMUTABLE-SOURCE-COMMIT` | `devops` | CRITICAL / XS | BLOCKED — EXCLUDED/SEPARATE PATHS + FRESH MUTATION DECISION | Selectively stage exactly the frozen allowlist below and create one local commit only; record its SHA as `release_source_commit`. No push, metadata, docs, evidence artifact, unresolved path, deployment, or adjacent mutation. Pointer commit `8d29f737` and vault-status commit `8a5ab773` are separate completed dependencies, but current dirty exclusions and separately owned paths remain non-stageable for ticket45 | 44R2 |

### Current Release DAG and Rule 11 Queue

- `21A + 21B -> {21D + 21D-QA2 + 22A} (FROZEN) -> 44 (BLOCKED history) -> 44R2 -> 45 -> 21C -> 22`.
- `20 -> 41A -> {41A-QA, 41A-QA2}` and `20 -> 41B -> 41B-QA` are frozen and feed ticket44.
- `21A + 21B + 21C + 21D + 41A + 41B -> 42 -> 42-QA`; `41B -> 43 -> 43-QA`.
- Current Rule 11 result is ticket44R2 only. Ticket45 is not executable until ticket44R2 is green and a fresh mutation decision/snapshot is issued; 21C remains dependency-blocked on ticket45. RC2-004 is excluded by its quota/HITL blocker.
- Fresh Rule 11 handoff: `TICKET-RELEASE-COMPLETE-20260827-POINTER-CENTRALIZATION-COMMIT` is the sole selectable documentation remediation. Its snapshot reserves only `project_tickets.md` for one devops local commit; no other path is executable. The commit is separate from ticket45 and does not authorize push, deploy, or publish.

### Ticket44R2 exact read-only matrix

Each command must exit `0`; retain only command, exit status, and summary. Stop on the first failure. No network, secret access, file mutation, staging, or external action is allowed.

1. `python3 -m pytest -q tests/test_multiagent_prompt_command.py tests/test_multiagent_prompt_command_r4.py tests/test_multiagent_receipt_schema.py`
2. `python3 -m pytest -q project/tests/test_azure_release.py project/tests/test_github_actions_regression.py`
3. `python3 -m pytest -q tests/test_publish_space_hf.py tests/test_hf_release_governance.py`
4. `python3 -m pytest -q project/tests/test_production_monitor_release_contract.py project/tests/test_fly_artifact_retirement.py project/tests/test_gateway_ui_release_contract.py project/tests/test_local_release_runner_contract.py project/tests/test_secret_sync_release_contract.py project/tests/test_trigger_inventory_retirement.py project/tests/test_web_regression.py`
5. `python3 -m pytest -q project/tests/test_backend_diagnostic_release_contract.py project/tests/test_grafana_cloud_exporter.py project/tests/test_ui_diagnostic_release_contract.py`
6. `node --test tests/api_gateway_cors_contract.test.mjs tests/api_index_vercel_contract.test.mjs`
7. `python3 -m json.tool project/schemas/release-manifest-v1.schema.json` and `python3 -m json.tool project/schemas/release-receipt-v1.schema.json`
8. `python3 scripts/sync_ai_agent_ecosystem.py --check`
9. `git diff --check`

### Ticket44R2 reconciliation result

- **Status**: `DONE`
- **Scope owned**: Corrected pre-source integration QA matrix only; read-only evidence and this canonical task-board reconciliation. No source, test, schema, workflow, generated-file, secret, external-system, or ticket45 decision/snapshot mutation.
- **Evidence**: Commands 1–9 all exited `0`. Command1 independently confirmed `151 passed in 1.48s`. Combined output for commands2–5/other test groups reported `337` tests in addition to command1's `151`; no ambiguous combined total is asserted. Command4 emitted one deprecation warning. Both JSON schemas were valid; ecosystem sync check and `git diff --check` passed. QA changed no files, and pre-existing dirty files remained unchanged.
- **Findings**: Corrected command3 path is green. One deprecation warning was emitted by command4; no failure resulted.
- **Changed files**: QA changed none. This reconciliation is limited to `PROJECT_TASKS.md` and `plans/plan.md`; pre-existing dirty files remain untouched.
- **Residual risk**: This is offline QA evidence only. It does not approve release, establish source-commit eligibility, validate metadata21C, or authorize staging, commit, push, deploy, publish, or external health/UI checks.
- **Recommended next action**: Keep ticket45 blocked until its owner receives a fresh mutation decision/snapshot and rechecks the exact allowlist; then follow the documented dependency order.

### Ticket45 exact source allowlist

The read-only Git inventory maps every currently modified/untracked non-evidence path below to a frozen release ticket. Ticket45 may stage only these exact paths after ticket44R2 passes; `fly.toml` is an intended deletion. A fresh status/diff must match this list byte-for-path before dispatch or ticket45 remains blocked.

### Ticket45 documentation dependency

- `project_tickets.md` is now a pointer-only compatibility file. The canonical ticket registry, status board, and operational handoff remain in `PROJECT_TASKS.md`; the pointer must not receive ticket state or release evidence.
- Its intentional dirty documentation path is outside ticket45's frozen source allowlist and remains preserved as historical/current worktree evidence. This note does not alter the immutable allowlist.
- Ticket45 remains `BLOCKED` until the pointer-file documentation change is separately handled under explicit commit authorization or an approved packaging/documentation ticket. No release approval or source-commit eligibility is inferred.

- Governance20/28: `.agents/rules/07-infrastructure-constraints.md`, `.agents/rules/16-hf-static-release-verification.md`, `.agents/skills/devops-deployment/SKILL.md`, `.agents/skills/devops-deployment/evals/evals.json`, `.agents/skills/hf-static-release-verification/SKILL.md`, `.agents/skills/hf-static-release-verification/evals/evals.json`, `.agents/skills/qa-e2e-testing/SKILL.md`, `.agents/skills/qa-e2e-testing/evals/evals.json`, `.antigravity/skills/devops-deployment/SKILL.md`, `.antigravity/skills/hf-static-release-verification/SKILL.md`, `.antigravity/skills/qa-e2e-testing/SKILL.md`, `.claude/rules/hf-static-release-verification.md`.
- Workflows19/21D/29/40A: `.github/workflows/azure_cost_guard.yml`, `.github/workflows/azure_deploy.yml`, `.github/workflows/deploy.yml`, `.github/workflows/fly_deploy.yml`, `.github/workflows/hf_backend_deploy.yml`, `.github/workflows/production_monitor.yml`.
- Dispatcher17 and release schemas21B: `scripts/multiagent_prompt_command.py`, `project/schemas/release-manifest-v1.schema.json`, `project/schemas/release-receipt-v1.schema.json`.
- Publisher21A and release-safety40B: `scripts/publish_space_hf.py`, `.env.example`, `scripts/sync_doppler_secrets.py`.
- Gateway/UI31/38: `api/gateway.js`, `api/health.js`, `api/index.js`, `project/static/app.js`, `public/app.js`, `vercel.json`.
- Retirement/local-runner30/32/40B2: `fly.toml` (delete), `scripts/trigger_all_github_actions.py`, `scripts/auto_deploy_all.sh`, `scripts/hermes_sdlc_runner.sh`, `scripts/agentic_pipeline.sh`.
- Diagnostics41A/41B: `scripts/grafana_cloud_exporter.py`, `scripts/run_remote_api_live_test.py`, `scripts/test_live_e2e_network.py`, `scripts/test_static_hf_space_questions.py`, `scripts/run_live_e2e_hf_space.py`, `scripts/audit_ui_overlap.py`, `scripts/run_vercel_prod_curl_regression.py`.
- Frozen Python QA: `project/tests/test_azure_release.py`, `project/tests/test_github_actions_regression.py`, `project/tests/test_grafana_cloud_exporter.py`, `project/tests/test_web_regression.py`, `project/tests/test_backend_diagnostic_release_contract.py`, `project/tests/test_fly_artifact_retirement.py`, `project/tests/test_gateway_ui_release_contract.py`, `project/tests/test_local_release_runner_contract.py`, `project/tests/test_production_monitor_release_contract.py`, `project/tests/test_secret_sync_release_contract.py`, `project/tests/test_trigger_inventory_retirement.py`, `project/tests/test_ui_diagnostic_release_contract.py`.
- Frozen dispatcher/publisher/Node QA: `tests/test_multiagent_prompt_command.py`, `tests/test_multiagent_prompt_command_r4.py`, `tests/test_multiagent_receipt_schema.py`, `tests/test_publish_space_hf.py`, `tests/api_gateway_cors_contract.test.mjs`, `tests/api_index_vercel_contract.test.mjs`.

### Ticket45 mandatory exclusions

- Provenance blockers: `project/api_router.py`, `project/data/bazi_bazi_manual_chatml.jsonl`, `project/data/distillation_checklist.json`.
- HITL/admin blockers: `project/admin_router.py`, `project/hitl_router.py`, `project/static/admin.html`, `project/static/hitl.html`, `project/tests/test_admin_hitl_release_routing.py`, `project/tests/test_admin_hitl_static_release_contract.py`.
- Post-source metadata: `project/static/version.json`, `public/version.json`.
- Final QA/docs/skill: `project/tests/test_hf_release_governance.py`, `PROJECT_TASKS.md`, `plans/plan.md`, `README.md`, `HOWTO.md`, `docs/RELEASE_HANDOFF_CHECKLIST.md`, `docs/RELEASE_ROLLBACK_RUNBOOK.md`, `.agents/skills/ai-inference-verifier/SKILL.md`, `project/tests/test_ai_inference_skill_reference.py`.
- Packaging/evidence only: every path under `project/tests/artifacts/priority_scheduling/`, including ticket44's decision/snapshot; these do not define the deployed source identity.
- Any path not enumerated in the allowlist, any new path appearing after this inventory, and every unresolved/unknown-provenance path. Fail closed; do not infer ownership from directory proximity.

### Ticket45 re-audit — 2026-08-27

- **Status**: `BLOCKED`; the prior documentation-path blocker is cleared only for the pointer remediation dependency. Commit `8d29f7372870ddd9118b27befbf15a896a16e369` contains exactly `project_tickets.md`; `project_tickets.md` is absent from current `git status`, and no paths are staged.
- **Scope owned**: BSA re-audit of the current worktree against ticket45's immutable allowlist, mandatory exclusions, and separate ownership tickets. No source, data, scripts, tests, workflows, project-ticket pointer, generated files, external action, staging, commit, release approval, or executable decision/snapshot mutation.
- **Evidence**: Current modified/untracked inventory is exactly `PROJECT_TASKS.md`, `plans/plan.md`, `project/data/bazi_bazi_manual_chatml.jsonl`, `project/data/distillation_checklist.json`, `project/data/vault_sync_status.json`, `scripts/agent_quota_status_guard.py`, `project/tests/artifacts/priority_scheduling/decision_release_complete_20260827_pointer_centralization_commit.json`, and `project/tests/artifacts/priority_scheduling/scheduling_snapshot_release_complete_20260827_pointer_centralization_commit.json`. Pointer decision/snapshot JSON parses successfully. Ticket44R2 is recorded `DONE`; its dependency is satisfied.
- **Findings**:
  - `PROJECT_TASKS.md` and `plans/plan.md`: ticket45 mandatory exclusions; documentation ownership remains with BSA and neither is stageable.
  - `project/data/bazi_bazi_manual_chatml.jsonl` and `project/data/distillation_checklist.json`: explicit provenance blockers/mandatory exclusions; non-stageable and acceptable only as documented exclusions, not as ticket45 input.
  - `scripts/agent_quota_status_guard.py`: not in ticket45's allowlist; separately owned by `QOBS-01-PROBE` (`developer`), so non-stageable for ticket45.
  - Both pointer-centralization artifacts: under `project/tests/artifacts/priority_scheduling/`, an explicit packaging/evidence exclusion; non-stageable and not source identity.
  - `project/data/vault_sync_status.json`: no frozen allowlist entry, mandatory-exclusion entry, or separate ownership ticket found; provenance is unresolved/unknown and therefore fail-closed blocking.
- **Changed files**: Only this re-audit entry in `PROJECT_TASKS.md` and the corresponding plan entry in `plans/plan.md`; no fresh executable Rule 18 decision or Rule 11 snapshot was created.
- **Residual risk**: Pointer centralization no longer blocks ticket45, but the unknown-provenance vault status path does. The closed allowlist must not be weakened or inferred from directory proximity. No release approval or source-commit eligibility is inferred.
- **Recommended next action**: Assign and resolve ownership/provenance for `project/data/vault_sync_status.json` (or obtain an explicit contract-level exclusion), then repeat a byte-for-path inventory. Only after the inventory is fully classified and authorization remains valid may a fresh devops mutation decision and Rule 11 snapshot authorize exact allowlist staging.

### Vault sync status generated-artifact handoff — 2026-08-27

- **Status**: `DONE` for this documentation/governance handoff; the assigned devops commit remains `READY` and unexecuted.
- **Scope owned**: Exactly `project/data/vault_sync_status.json` for one separate local commit. No vault-file edit is authorized by this documentation lane.
- **Evidence**: The current vault diff is exactly `last_sync_timestamp`, from `2026-08-25T11:03:09.795736` to `2026-08-27T17:14:27.881116`; inventory counts and folder configuration are unchanged. `scripts/sync_gdrive_vault.py` explicitly owns this report path and writes `datetime.now().isoformat()`.
- **Findings**: This generated-artifact ticket clears only ownership/provenance classification. It does not alter ticket45's closed allowlist or release eligibility.
- **Changed files**: `PROJECT_TASKS.md`, `plans/plan.md`, and the new Rule 18 decision/snapshot pair under `project/tests/artifacts/priority_scheduling/`.
- **Residual risk**: The protected data provenance blockers `project/data/bazi_bazi_manual_chatml.jsonl` and `project/data/distillation_checklist.json` remain frozen and non-stageable; `project/api_router.py` remains separately protected. No source identity, release approval, or deployment evidence is established.
- **Recommended next action**: Devops may recheck the exact one-file diff, stage only `project/data/vault_sync_status.json`, and create one separate local commit. Stop on any content/path drift; do not push, deploy, publish, or update ticket45's allowlist/state.

### Ticket45 re-audit after commits 8d29f737 and 8a5ab773 — 2026-08-27

- **Status**: `BLOCKED` for ticket45; the re-audit is complete. Both commits contain exactly their named single path, and both paths are clean in the current worktree. No paths are staged.
- **Scope owned**: BSA inventory/classification only. In scope are current modified/untracked paths, ticket45's frozen allowlist, mandatory exclusions, separate ownership, and provenance gates. Out of scope are source/data/script/test/workflow edits, generated-agent edits, ticket45 staging/commit, executable decision/snapshot creation, release approval, push, deploy, publish, and external health/UI verification.
- **Evidence**: `git status --porcelain=v1 -uall` shows exactly nine current paths: `PROJECT_TASKS.md`, `plans/plan.md`, `project/data/bazi_bazi_manual_chatml.jsonl`, `project/data/distillation_checklist.json`, `scripts/agent_quota_status_guard.py`, and four scheduling artifacts under `project/tests/artifacts/priority_scheduling/`. All four artifacts parse as valid JSON; the pointer pair records exact `project_tickets.md` ownership and the vault pair records exact `project/data/vault_sync_status.json` ownership.
- **Findings / classification**:
  - `PROJECT_TASKS.md` and `plans/plan.md`: mandatory ticket45 documentation exclusions; BSA-owned and non-stageable.
  - `project/data/bazi_bazi_manual_chatml.jsonl` and `project/data/distillation_checklist.json`: explicit provenance blockers under `TICKET-RELEASE-COMPLETE-20260826-25-DATA-PROVENANCE`; non-stageable and unresolved for release provenance.
  - `scripts/agent_quota_status_guard.py`: outside the frozen allowlist and separately owned by `QOBS-01-PROBE` (`developer`). Its contract dependency is frozen under `QOBS-01-CONTRACT`, with the source/test gate still required before that lane can close; it is not ticket45-stageable.
  - The pointer-centralization decision/snapshot pair and vault-sync decision/snapshot pair: packaging/evidence-only artifacts; valid bounded evidence, not source identity, and not ticket45-stageable. The vault-status path itself is clean after `8a5ab773`.
- **Dependency result**: The inventory is fully classified, but ticket45 eligibility is not satisfied. The separately owned quota-guard path remains with `developer` under `QOBS-01-PROBE` until its source/test provenance gate closes; both data paths remain unresolved provenance blockers. No allowlist entry is added or weakened.
- **Changed files**: Only this audit reconciliation in `PROJECT_TASKS.md` and the corresponding plan record in `plans/plan.md`; no executable ticket45 decision/snapshot was created.
- **Residual risk**: Current dirty exclusions can be mistaken for release inputs, and valid scheduling artifacts can be mistaken for source identity. Neither is permitted. No `release_source_commit`, release approval, or deployment claim is established.
- **Recommended next action**: Keep ticket45 blocked. The `developer` owner should close `QOBS-01-PROBE` with its required source/test evidence; the owner of `TICKET-RELEASE-COMPLETE-20260826-25-DATA-PROVENANCE` must resolve both protected data paths. Then perform a fresh byte-for-path inventory and issue a new ticket45 mutation decision/snapshot only if the exact frozen allowlist is the sole stageable set.

### Ticket45 re-audit after QOBS source commit `943bdd8` — 2026-08-27

- **Status**: `BLOCKED`; QOBS DISPATCH and SCHEDULER are frozen, but ticket45
  remains blocked by protected provenance paths and open separate ownership.
- **Scope owned**: BSA inventory classification in `PROJECT_TASKS.md` and
  `plans/plan.md` only. No source, tests, data, scripts, workflows, generated
  files, staging, commit, decision/snapshot mutation, release approval, push,
  deploy, publish, or external action.
- **Evidence**: Commit `943bdd8` contains exactly
  `scripts/multiagent_prompt_command.py` and
  `scripts/multiagent_ticket_scheduler.py`, carries the required
  `Test-Baseline` trailer, and both source paths are clean. Current status has
  no staged paths; `git diff --check` passed.
- **Findings / classification**:
  - `PROJECT_TASKS.md` and `plans/plan.md`: BSA-owned mandatory ticket45
    documentation exclusions; non-stageable.
  - `project/data/bazi_bazi_manual_chatml.jsonl` and
    `project/data/distillation_checklist.json`: protected provenance blockers
    under `TICKET-RELEASE-COMPLETE-20260826-25-DATA-PROVENANCE`; mandatory
    exclusions, unresolved, and never ticket45 inputs.
  - `scripts/agent_quota_status_guard.py`: separately owned by
    `QOBS-01-PROBE`; outside ticket45's frozen allowlist and non-stageable.
  - All `project/tests/artifacts/priority_scheduling/` paths currently present:
    bounded decision/snapshot evidence only; non-stageable and unable to define
    source identity.
- **Dependency result**: The inventory is classified, but protected data and
  the open PROBE ownership gate remain. No allowlist entry is added or
  weakened, and no ticket45 mutation decision/snapshot is created.
- **Changed files**: Only this documentation reconciliation and its matching
  `plans/plan.md` record.
- **Residual risk**: Protected training/provenance data may be mistaken for
  release inputs, and valid QOBS evidence may be mistaken for source
  eligibility. No `release_source_commit`, release approval, or source
  eligibility is established.
- **Recommended next action**: Keep ticket45 blocked. Close QOBS-01-PROBE and
  resolve both protected data paths under their existing ownership; then rerun
  the exact byte-for-path inventory before any fresh ticket45 decision/snapshot.

---

## SPRINT: Zero-Cost Multi-Tier AI Provider Pipeline & Governance (`TICKET-ZERO-001` .. `007`)
**Grill Gate Status**: `APPROVED` (Ref: [`plans/plan.md`](plans/plan.md))
**Planning-to-Execution Gate**: `PLANNING_GATE: ACTIVE` (5-tier pipeline specified: Cloudflare -> Google AI Studio -> Groq -> Cohere -> Rust/Ollama; developer lanes eligible for dispatch)
**Sprint Tracking Lead**: Master Orchestrator (`orchestrator`)

| Ticket ID | Assigned Owner | Model / Effort Floor | Task Summary | Status | Dependencies |
|---|---|---|---|---|---|
| `TICKET-ZERO-001` | `business_analyst` | `gpt-5.6-terra` / `medium` | Author API specs, Rule 19, Skill, and governance contracts | DONE — SPECIFIED | None |
| `TICKET-ZERO-002` | `developer` (Core AI Lane) | `gpt-5.3-codex` / `high` | Refactor AIProviderRouter with ProviderPool, CircuitBreakerState, and Free Filter | DONE — VERIFIED | `TICKET-ZERO-001` |
| `TICKET-ZERO-003` | `developer` (Security Lane) | `gpt-5.3-codex` / `high` | Extend Rate Limiter (IP/User/Daily Budget) & Input Clamping (12k chars) | DONE — VERIFIED | `TICKET-ZERO-001` |
| `TICKET-ZERO-004` | `developer` (Caching Lane) | `gpt-5.3-codex` / `high` | Implement Metaphysics Semantic Cache & Rust PyO3 Safe Net | DONE — VERIFIED | `TICKET-ZERO-001` |
| `TICKET-ZERO-005` | `devops` (Admin Lane) | `gpt-5.3-codex` / `high` | Admin Dashboard Pool Health monitoring & Zero-Cost Badges | DONE — VERIFIED | `TICKET-ZERO-002` |
| `TICKET-ZERO-006` | `qa_tester` | `gpt-5.4-mini` / `medium` | Comprehensive Zero-Cost & Fail-Closed Test Suite | DONE — VERIFIED | `TICKET-ZERO-002`..`005` |
| `TICKET-ZERO-007` | `code_reviewer` & `business_analyst` | `gpt-5.3-codex` / `high` | Pre-deployment safety audit, secret scan (0 leaks), and ecosystem sync | DONE — VERIFIED | `TICKET-ZERO-006` |

---

### TICKET-ZERO-001 | `business_analyst` | [STATUS: DONE — SPECIFIED]
**Priority**: HIGH
**Selected Route**: `gpt-5.6-terra` / `medium`
**Depends On**: None
**Blocks**: `TICKET-ZERO-002`, `TICKET-ZERO-003`, `TICKET-ZERO-004`
**Owned Files**: `.agents/rules/19-zero-cost-ai-governance.md`, `.claude/rules/zero-cost-ai-governance.md`, `.agents/skills/zero-cost-ai-pipeline/SKILL.md`, `docs/specs/zero_cost_ai_spec.md`

#### Objective and Ownership
- Author and verify OpenAPI schema contracts for ProviderPool, Health Status, and Circuit Breaker states.
- Ensure Rule 19 and `zero-cost-ai-pipeline` skill adhere to Rule 14 size boundaries.
- 9-dimension Grill Intake completed and approved in `plans/plan.md`.

---

### TICKET-ZERO-002 | `developer` (Core AI Lane) | [STATUS: DONE — VERIFIED]
**Priority**: CRITICAL
**Selected Route**: `gpt-5.3-codex` / `high`
**Depends On**: `TICKET-ZERO-001`
**Blocks**: `TICKET-ZERO-005`, `TICKET-ZERO-006`
**Owned Files**: `project/core/ai_provider_router.py`, `project/api_router.py`

#### Objective and Ownership
- Implement `ProviderPool` separating key auth redundancy from multi-project quota pools.
- Attach `CircuitBreakerState` with 60s cooldown for 0ms instant 429 bypass.
- Enforce `BillingMode.FREE` fail-closed filter when `AI_ZERO_COST_ONLY=true`.
- Verified: 23/23 router unit & integration tests pass, 0 trailing whitespace, pure ASCII logging.

---

### TICKET-ZERO-003 | `developer` (Security Lane) | [STATUS: DONE — VERIFIED]
**Priority**: HIGH
**Selected Route**: `gpt-5.3-codex` / `high`
**Depends On**: `TICKET-ZERO-001`
**Blocks**: `TICKET-ZERO-006`
**Owned Files**: `project/core/rate_limiter.py`

#### Objective and Ownership
- Implement multi-tier rate limiting: IP (10 RPM), User (20 RPM), Daily Budget (40-150 req/day).
- Enforce input character clamping (<= 12,000 chars) and max output tokens (<= 1,200).
- Verified: 13/13 rate limiter tests pass, 0 trailing whitespace, pure ASCII logging.

---

### TICKET-ZERO-004 | `developer` (Caching Lane) | [STATUS: DONE — VERIFIED]
**Priority**: HIGH
**Selected Route**: `gpt-5.3-codex` / `high`
**Depends On**: `TICKET-ZERO-001`
**Blocks**: `TICKET-ZERO-006`
**Owned Files**: `project/core/semantic_cache.py`

#### Objective and Ownership
- Implement SHA-256 canonical query normalization for astrological prompts.
- Integrate Rust PyO3 engine (<1ms) fallback safe net on full free LLM capacity exhaustion.
- Verified: 24/24 semantic cache tests pass, 0.0043 ms deterministic safe net latency, pure ASCII logging.

---

### TICKET-ZERO-005 | `devops` (Admin Lane) | [STATUS: DONE — VERIFIED]
**Priority**: MEDIUM
**Selected Route**: `gpt-5.3-codex` / `high`
**Depends On**: `TICKET-ZERO-002`
**Blocks**: `TICKET-ZERO-006`
**Owned Files**: `project/admin_router.py`, `project/static/admin.html`

#### Objective and Ownership
- Expose `/api/admin/provider-pools` and `/admin/provider-pools` endpoints with live health status.
- Render visual indicators, circuit breaker states, and `[ZERO-COST POLICY: ACTIVE]` badges in admin UI.
- Verified: HTTP 200 responses with full telemetry, clean py_compile, pure ASCII logging.

---

### TICKET-ZERO-006 | `qa_tester` | [STATUS: DONE — VERIFIED]
**Priority**: HIGH
**Selected Route**: `gpt-5.4-mini` / `medium`
**Depends On**: `TICKET-ZERO-002`, `TICKET-ZERO-003`, `TICKET-ZERO-004`, `TICKET-ZERO-005`
**Blocks**: `TICKET-ZERO-007`
**Owned Files**: `project/tests/test_zero_cost_pipeline.py`, `project/tests/test_semantic_cache.py`

#### Objective and Ownership
- Write unit, integration, and stress tests verifying zero-cost fail-closed guarantee, circuit breakers, rate limits, and caching.
- Verified: 51/51 zero-cost tests passed in 1.39s (100% pass rate).

---

### TICKET-ZERO-007 | `code_reviewer` & `business_analyst` | [STATUS: DONE — VERIFIED]
**Priority**: CRITICAL
**Selected Route**: `gpt-5.3-codex` / `high`
**Depends On**: `TICKET-ZERO-006`
**Blocks**: Final Closure & Production Release
**Owned Files**: `PROJECT_TASKS.md`, `plans/plan.md`, `HANDOFF.md`

#### Objective and Ownership
- Run full pre-deployment safety audit (`python3 project/core/code_reviewer.py --review` -> READY_FOR_PROD, 1782 passed).
- Run parallel secret scan (2183 files scanned, 0 leaks, PASSED).
- Run ecosystem sync check (`python3 scripts/sync_ai_agent_ecosystem.py --check` -> 100% PASS).
- Synchronize all governance documents (`PROJECT_TASKS.md`, `plans/plan.md`, `HANDOFF.md`).

---

## SPRINT: Adaptive Multi-Agent Model & Effort Governance — 2026-08-25
**Grill Gate Status**: APPROVED FOR PLANNING (Ref: [`plans/plan.md`](plans/plan.md))
**Planning-to-Execution Gate**: `PLANNING_TO_MEDIUM_GATE: CONFIRMED` (owner confirmation received 2026-08-25)
**Sprint Tracking Lead**: Master Orchestrator (`orchestrator`)

| Ticket ID | Assigned Owner | Model / Effort Floor | Task Summary | Status | Dependencies |
|---|---|---|---|---|---|
| `TICKET-ADAPT-001` | `orchestrator` | `gpt-5.6-sol` / `xhigh` | Inspect current routing; define rubric, solution, plan, and isolated tickets | DONE | None |
| `TICKET-ADAPT-002` | Human owner / `orchestrator` | Root changes to `medium` | Confirm root orchestrator reasoning effort is `medium` | DONE | `TICKET-ADAPT-001` |
| `TICKET-ADAPT-003` | `business_analyst` | `gpt-5.6-terra` / `high` | Dedicated rules, skill, mirrors, orchestrator contract, and governance docs | DONE | `TICKET-ADAPT-002` |
| `TICKET-ADAPT-004` | `developer` | `gpt-5.6-sol` / `high` | Versioned policy/catalog/schema and fail-closed PromptCommand enforcement | DONE | `TICKET-ADAPT-003` |
| `TICKET-ADAPT-005` | `developer` (security lane) | `gpt-5.6-sol` / `high` | Extend existing orchestrator-only hook and registration | DONE | `TICKET-ADAPT-004` |
| `TICKET-ADAPT-006` | `qa_tester` | `gpt-5.6-terra` / `high` | Independent policy, dispatcher, hook, and governance regression tests | DONE | `TICKET-ADAPT-005` |
| `TICKET-ADAPT-007` | `business_analyst` editor; `code_reviewer` read-only | `terra/medium` sync; `sol/high` review | Ecosystem sync, skill eval evidence, secret scan, compatibility and bypass review | DONE | `TICKET-ADAPT-006` |

---

### TICKET-ADAPT-001 | `orchestrator` | [STATUS: DONE]
**Priority**: CRITICAL
**Selected Route**: `gpt-5.6-sol` / `xhigh`
**Depends On**: None
**Blocks**: `TICKET-ADAPT-002`

#### Objective and Ownership
- Read-only audit of model metadata, routing config, PromptCommand, hooks, rules, skills, schemas, templates, and tests.
- Own only solution architecture, the GRILL REPORT, and ticket decomposition.

#### Evidence / Acceptance Criteria
- [x] Static role defaults distinguished from effective runtime proof.
- [x] Judgment-based classification separated from deterministic enforcement.
- [x] Five-dimension rank rubric and model/effort floors recorded.
- [x] Planning-to-medium HITL gate retained independently from child routing.
- [x] File ownership is isolated for every implementation lane.

---

### TICKET-ADAPT-002 | Human owner / `orchestrator` | [STATUS: DONE]
**Priority**: CRITICAL
**Depends On**: `TICKET-ADAPT-001`
**Blocks**: `TICKET-ADAPT-003` through `TICKET-ADAPT-007`

#### Required Owner Action
1. Change the root orchestrator reasoning effort from `xhigh` to `medium` in the active Codex session/runtime.
2. Provide fresh confirmation in this conversation.

#### Acceptance Criteria
- [x] Owner explicitly confirmed the active root orchestrator effort is `medium` on 2026-08-25.
- [x] Confirmation is fresh and occurs after solution, plan, and tickets were completed.
- [x] No repository setting, historical approval, or ticket status is treated as runtime proof.

#### Stop Condition
- Confirmation satisfied the planning-to-medium gate; child selection remains independently governed by Rule 18.

---

### TICKET-ADAPT-003 | `business_analyst` | [STATUS: DONE]
**Priority**: HIGH
**Recommended Route**: `gpt-5.6-terra` / `high`
**Depends On**: `TICKET-ADAPT-002`
**Blocks**: `TICKET-ADAPT-004`

#### File Ownership
- New `.agents/rules/18-adaptive-model-effort-routing.md`.
- New `.agents/skills/adaptive-model-effort-routing/SKILL.md` and its `evals/evals.json`.
- Narrow cross-references in `.agents/rules/11-orchestrator-subagent-delegation.md`, `.agents/rules/17-multi-account-agent-orchestration.md`, `.agents/skills/orchestrator-delegation/SKILL.md`, and `.agents/skills/multi-account-agent-orchestration/SKILL.md`.
- `.claude/rules/orchestrator-subagents.md`, `.claude/rules/multi-account-agent-orchestration.md`, and a new scoped Claude adaptive-routing rule.
- `.agents/AGENTS.md`, `docs/templates/MULTIAGENT_PROMPT_COMMAND.md`, and the authoritative orchestrator agent definition.

#### Boundaries
- Do not edit dispatcher/hook/test code or generated `.codex/agents/*.toml`.
- Keep specialist artifact size limits and existing dirty/user changes intact.

#### Acceptance Criteria
- [x] Rule/skill define required decision fields, rank rubric, floor matrix, quota behavior, override rules, and planning-to-medium gate.
- [x] Skill has 3 realistic eval prompts with expected routing outcomes.
- [x] Orchestrator contract requires an explicit `DispatchDecision` before every executable lane.
- [x] Static model metadata is documented as a fallback hint, not runtime proof.

#### Evidence / Handoff
- Added Rule 18, the specialist skill/evals, required cross-references, scoped Claude mirror, catalog entry, prompt-template handoff, and static orchestrator default update.
- `git diff --check` passed. Ecosystem synchronization, dispatcher/schema enforcement, hook changes, and focused regression remain owned by `TICKET-ADAPT-004` through `TICKET-ADAPT-007`.

---

### TICKET-ADAPT-004 | `developer` | [STATUS: DONE]
**Priority**: CRITICAL
**Recommended Route**: `gpt-5.6-sol` / `high`
**Depends On**: `TICKET-ADAPT-003`
**Blocks**: `TICKET-ADAPT-005`

#### File Ownership
- `scripts/multiagent_prompt_command.py`.
- `.agents/config/multiagent_prompt_command.example.yaml`.
- New versioned `.agents/config/multiagent_model_policy.yaml`.
- New decision/receipt JSON schema under `.agents/schemas/` and narrowly required schema helpers only.

#### Detailed Instructions
1. Model a versioned lane assessment and `DispatchDecision` containing ticket/phase, five dimension ranks, quota band, alias, model, effort, rationale, policy version, and medium-gate state.
2. Compute the minimum profile from the maximum rank; validate provider/model/effort support and hard HITL blockers.
3. Revalidate inside `execute_invocation` so direct Python callers cannot bypass the gate.
4. Bind the policy version and decision digest into dry-run output, dispatch identity, prompt evidence, and execution receipt.
5. Allow legacy v1 dry-run with a warning; reject legacy execution with an actionable migration error.

#### Acceptance Criteria
- [x] Missing/invalid decisions fail before subprocess creation.
- [x] CLI overrides cannot disagree with or weaken the validated decision.
- [x] Quota can reroute only at or above the quality floor.
- [x] Provider-specific effort restrictions are enforced.
- [x] Child lane effort is evaluated independently from the root medium gate.

---

### TICKET-ADAPT-005 | `developer` (security lane) | [STATUS: DONE]
**Priority**: CRITICAL
**Recommended Route**: `gpt-5.6-sol` / `high`
**Depends On**: `TICKET-ADAPT-004`
**Blocks**: `TICKET-ADAPT-006`

#### File Ownership
- `.claude/hooks/orchestrator_only_guard.py`.
- `.claude/settings.json` only if an installed native dispatch matcher is verified.
- Hook-specific tests are owned by QA in `TICKET-ADAPT-006`, not this lane.

#### Boundaries
- Do not duplicate the scoring matrix in regex and do not expand the secrets/destructive-command guard.
- Reuse the dispatcher/policy validator; keep existing waiver and `HORO_ORCHESTRATOR_ONLY=1` behavior.

#### Acceptance Criteria
- [x] Executable dispatch without a decision or confirmed medium gate is denied.
- [x] Planning-only dry-run remains allowed.
- [x] Native Claude matcher is added only after verification against the installed tool schema.
- [x] Codex/native-runtime limitation is documented; dispatcher remains authoritative.

---

### TICKET-ADAPT-006 | `qa_tester` | [STATUS: DONE]
**Priority**: CRITICAL
**Recommended Route**: `gpt-5.6-terra` / `high`
**Depends On**: `TICKET-ADAPT-005`
**Blocks**: `TICKET-ADAPT-007`

#### File Ownership
- `tests/test_multiagent_prompt_command.py`.
- `project/tests/test_claude_governance.py`.
- `project/tests/test_agent_configurations.py`.
- `project/tests/test_ai_agent_ecosystem_sync.py`.
- New focused policy/hook test files only when needed to avoid monolithic tests.

#### Minimum Test Matrix
- [x] Missing assessment, unsupported pair, below-floor route, and mismatched CLI overrides are rejected.
- [x] Critical risk/ambiguity, low quota, unknown quota on broad work, and unconfirmed medium gate fail closed.
- [x] Confirmed root medium permits a valid lane; child high/xhigh remains independently selectable by its own floor.
- [x] Legacy dry-run compatibility and legacy execution rejection are explicit.
- [x] Decision digest/model/effort/policy version are bound to route and receipt evidence.
- [x] Hook blocks invalid execution and allows planning dry-run.

#### Evidence Expected
- Exact focused pytest command, pass count, exit code, and concise failure evidence if blocked.

---

### TICKET-ADAPT-007 | `business_analyst` + `code_reviewer` | [STATUS: DONE]
**Priority**: HIGH
**Recommended Routes**: sync/documentation `gpt-5.6-terra` / `medium`; read-only safety review `gpt-5.6-sol` / `high`
**Depends On**: `TICKET-ADAPT-006`
**Blocks**: Sprint closure

#### Ownership and Sequence
1. `business_analyst` is the sole editor for generated mirrors and governance/task status through the prescribed ecosystem sync.
2. `code_reviewer` is read-only and verifies bypass resistance, secret hygiene, model/effort support, compatibility behavior, and planning-gate evidence.

#### Verification Commands
```bash
python3 -m pytest -q tests/test_multiagent_prompt_command.py project/tests/test_claude_governance.py project/tests/test_agent_configurations.py project/tests/test_ai_agent_ecosystem_sync.py
python3 scripts/sync_ai_agent_ecosystem.py --sync
python3 scripts/sync_ai_agent_ecosystem.py --check
python3 project/core/code_reviewer.py --scan-secrets
git diff --check
```

#### Acceptance Criteria
- [x] All focused regression and ecosystem sync gates pass: `77 passed`.
- [x] New/updated skill evals demonstrate correct low-, medium-, and critical-risk routing behavior.
- [x] Secret scan reports zero leaks (1,783 files).
- [x] Code reviewer reports no bypass that can start a child below the validated quality floor.
- [x] Generated Codex files were synced, never hand-edited.

#### Closure Evidence
- Legacy local static metadata was migrated to its existing immutable source provenance without changing the source commit. Full repository suite: `904 passed, 9 skipped`.

---

## 🚀 SPRINT: Shell Environment & Multi-Account Codex Standalone Remediation — 2026-08-25
**Grill Gate Status**: ✅ APPROVED (Ref: [`plans/plan.md`](plans/plan.md))
**Sprint Tracking Lead**: Master Orchestrator (`orchestrator`)

| Ticket ID | Assigned Agent | Task Summary | Status | Dependencies |
|---|---|---|---|---|
| `TICKET-SHELL-001` | `orchestrator` | Grill Gate Approval & Architecture Specification | DONE | None |
| `TICKET-SHELL-002` | `developer` | Backup & Refactor `~/.zshrc` with 100% Backward Compatibility | DONE | `TICKET-SHELL-001` |
| `TICKET-SHELL-003` | `devops` | Standalone Codex Installation & Account Symlink Creation | DONE | `TICKET-SHELL-002` |
| `TICKET-SHELL-004` | `qa_tester` | Shell Environment & Multi-Account Execution Verification | DONE | `TICKET-SHELL-003` |
| `TICKET-SHELL-005` | `code_reviewer` | Final Safety Review & AI Ecosystem Sync Verification | DONE | `TICKET-SHELL-004` |

---

### 🎫 TICKET-SHELL-001 | `orchestrator` | [STATUS: DONE]
**Priority**: CRITICAL
**Depends On**: None
**Blocks**: `TICKET-SHELL-002`
#### Detailed Instructions
1. Grill user on requirements, backward compatibility, and standalone strategy.
2. Produce GRILL REPORT in `plans/plan.md`.
#### Acceptance Criteria
- [x] GRILL REPORT prepended to `plans/plan.md`.
- [x] Sprint tickets decomposed in `PROJECT_TASKS.md`.

---

### 🎫 TICKET-SHELL-002 | `developer` | [STATUS: DONE]
**Priority**: CRITICAL
**Depends On**: `TICKET-SHELL-001`
**Blocks**: `TICKET-SHELL-003`
#### Detailed Instructions
1. Create backup `~/.zshrc.bak_<timestamp>`.
2. Refactor `~/.zshrc` to clean up duplicate PATH exports and remove intrusive startup echo.
3. Preserve all existing aliases and functions (`codex1-3`, `agy1-3`, `*_login`, `*_logout`, `*_status`, `ssh-node*`, `tailscale-restart`, `open-unifi-ui`, `claude-local*`, `agent-run`).
#### Acceptance Criteria
- [x] Backup created and verified (`~/.zshrc.bak_20260825_142154`).
- [x] `zsh -n ~/.zshrc` passes with zero syntax errors.

---

### 🎫 TICKET-SHELL-003 | `devops` | [STATUS: DONE]
**Priority**: CRITICAL
**Depends On**: `TICKET-SHELL-002`
**Blocks**: `TICKET-SHELL-004`
#### Detailed Instructions
1. Install standalone Codex via `curl -fsSL https://chatgpt.com/codex/install.sh | sh`.
2. Symlink `~/.codex/packages` to `~/.ai-accounts/codex/account{1,2,3}/packages`.
#### Acceptance Criteria
- [x] `~/.codex/packages/standalone/current/codex` executable exists (v0.149.1).
- [x] `~/.ai-accounts/codex/account{1,2,3}/packages` symlinks point to `~/.codex/packages`.

---

### 🎫 TICKET-SHELL-004 | `qa_tester` | [STATUS: DONE]
**Priority**: CRITICAL
**Depends On**: `TICKET-SHELL-003`
**Blocks**: `TICKET-SHELL-005`
#### Detailed Instructions
1. Execute `codex1 --version`, `codex2 --version`, `codex3 --version` via zsh.
2. Verify absence of `managed standalone Codex install not found` error.
3. Verify `agent-run`, `claude-local`, `agy1-3` aliases and syntax.
#### Acceptance Criteria
- [x] Multi-account codex executions succeed without standalone missing error (`codex-cli 0.149.1` across all 3 accounts).
- [x] `codex1_status`, `codex2_status`, `codex3_status` report active login.

---

### 🎫 TICKET-SHELL-005 | `code_reviewer` | [STATUS: DONE]
**Priority**: HIGH
**Depends On**: `TICKET-SHELL-004`
**Blocks**: None
#### Detailed Instructions
1. Run `python3 scripts/sync_sdlc_agents.py --check` and `python3 scripts/sync_codex_agents.py --check`.
2. Ensure secret hygiene and zero regressions.
#### Acceptance Criteria
- [x] Agent ecosystem sync checks PASS (SDLC and Codex sync 100%).
- [x] Secret scan passed (0 leaks across 1770 files).

---

Historic completion details have been archived to [docs/RELEASE_NOTES.md](docs/RELEASE_NOTES.md).
Current sections below track active work and release gates only.
## 📋 PLANNED SPRINT: Metaphysics Learning Roadmap & Question-Forecast Alignment
**Grill Gate Status**: BLOCKED — scope is not complete while child tickets and release gates remain pending due to external/environmental blockers.
**Sprint Tracking Lead**: `orchestrator` / `business_analyst`
**Source Documents**:
- [`plans/metaphysics_learning_roadmap.md`](plans/metaphysics_learning_roadmap.md)
- [`plans/plan.md`](plans/plan.md)
- [`plans/question_forecast_alignment_spec.md`](plans/question_forecast_alignment_spec.md)
- [`plans/todo_tasks_plan.md`](plans/todo_tasks_plan.md)

**Plan Coverage Matrix**:

| Plan | Covered scope | Kanban disposition |
|---|---|---|
| `metaphysics_learning_roadmap.md` | Five branches, source ingestion, deterministic engines, fine-tuning, MCP, and UI visualizer | Implementation closed under `TICKET-META-002`/`003`; release gates remain in `TICKET-META-005`/`006` |
| `plan.md` | Phases 1–16, MLOps/provider/Grafana work, governance, multi-cloud, quality gates, and future model architecture | Historical phases are archived; active/future platform work is tracked under `TICKET-META-005` |
| `question_forecast_alignment_spec.md` | Six benchmark domains, 100-point rubric, validator threshold, prompt/debate routing | Implementation and focused validation closed under `TICKET-META-004` |
| `todo_tasks_plan.md` | Six implementation workstreams and five-phase SDLC execution flow | Workstreams have evidence under `TICKET-META-003`/`004`; release closure remains under `TICKET-META-005`/`006` |

| Ticket ID | Assigned Agent | Task Summary | Status | Dependencies |
|---|---|---|---|---|
| `TICKET-META-001` | `orchestrator` / `business_analyst` | Consolidate and execute the five-branch metaphysics roadmap, six-domain question/forecast alignment benchmark, and six TODO workstreams | BLOCKED — HITL DEPLOY | None |
| `TICKET-META-002` | `domain_master` / `developer` | Implement and test the five-branch deterministic metaphysics calculation modules | DONE | `TICKET-META-001` |
| `TICKET-META-003` | `developer` | Execute OCR/RAG ingestion, dataset generation, fine-tuning, model fusion, MCP, and visualizer integration | DONE | `TICKET-META-001` |
| `TICKET-META-004` | `developer` / `qa_tester` | Implement six-domain question/forecast alignment, focused prompting, debate routing, and validator benchmarks | DONE | `TICKET-META-001` |
| `TICKET-META-005` | `devops` / `developer` | Reconcile active/future `plan.md` platform work: providers, observability, CI/CD, governance, and release architecture | DONE | `TICKET-META-001` |
| `TICKET-META-006` | `qa_tester` / `code_reviewer` / `business_analyst` | Run full QA, security, synchronization, release evidence, and final Kanban documentation handoff | DONE | `TICKET-META-002`..`005` |
| `TICKET-META-007` | `orchestrator` / `business_analyst` | Refresh sub-agent delegation governance and Claude Code three-level command-control examples | DONE | `TICKET-META-001` |
| `TICKET-META-008` | `orchestrator` / `business_analyst` / `devops` | Preserve account-migration continuity and quota-exhaustion handoff, including active blockers, non-secret credential status, and safe resume commands | DONE | `TICKET-META-005`, `TICKET-META-006` |
| `TICKET-META-009` | `developer` / `qa_tester` | Safely upgrade Python/Rust dependency lockfiles and validate compatibility after active release gates are clear | DONE | `CP-03-AZURE`, `CP-04-PW`, `CP-05-RELEASE` |
| `TICKET-QA-PW-SMOKE-20260825` | `qa_tester` | Re-run and reconcile Vercel production smoke E2E | DONE | `G-META-006-PW` |
| `PROMPT-GOV-001` | `business_analyst` / `orchestrator` | Govern multi-account PromptCommand routing, quota/account evidence, bounded retries, HITL escalation, and synchronized governance mirrors | DONE | `TICKET-META-008`, Rule 17 |
| `TICKET-ORCH-ONLY-002` | `business_analyst` / `orchestrator`; aliases `codex1`, `codex2`, `agy1`, `agy2` | Enforce governance -> rules -> hooks hierarchy; keep root/current session orchestrator-only and obtain four distinct alias receipts | BLOCKED — HITL DISPATCH CONTRACT | Rule 17, current CORS/separation lanes |
| `TICKET-ALIAS-RC2-003` | `developer` / `qa_tester` / `code_reviewer`; aliases `codex1`, `codex2`, `agy1`, `agy2`; monitored by `orchestrator` | Implement, validate, review, then redispatch four distinct lanes with Result Contract v2 | BLOCKED — CODEX1 ATTEMPTS EXHAUSTED | `TICKET-ORCH-ONLY-002`, Rule 17 |
| `TICKET-ALIAS-RC2-004` | `developer` / `qa_tester` / `code_reviewer`; aliases are bounded read-only diagnostics, monitored by `orchestrator` | Content-free provider parse-reason taxonomy and one fresh `codex1` diagnostic authorization | TODO — OWNER AUTHORIZED / QUOTA UNKNOWN | `TICKET-ALIAS-RC2-003` immutable blocker, QA/retry gate, Rule 17 |

### TICKET-ORCH-ONLY-002 | Orchestrator-Only Control and Four-Alias Dispatch | [STATUS: BLOCKED — HITL DISPATCH CONTRACT]

**Scope**: require the root/current session to delegate all implementation,
QA, git mutation, deploy, and publish work. Its permitted work is decomposition,
dispatch, monitoring, receipt collection, conflict resolution, HITL, and final
gate decisions. **Out of scope**: application/workflow implementation by the
root, credentials, secret values, staging, commits, pushes, deploys, and
publishes. **Dependencies**: the current CORS and static/backend-separation
lanes, configured aliases, and the Claude PreToolUse hook registration.

**Success / stop condition**: Rule 17, skills/mirrors, board/plan, Claude rule,
and hook contract agree; every explicitly requested alias returns its actual
receipt or a safe `BLOCKED` result. Stop and return `NEEDS_HITL` for an
unrecorded root action, missing alias execution evidence, credentials, or an
ownership conflict.

| Alias | Bounded lane | Writable ownership | Required receipt | Status |
|---|---|---|---|---|
| `codex1` | Vercel gateway CORS independent review | None; read-only gateway-source and test review | receipt `01a03849-759b-7b21-826e-35697a0743ee`; return `0`; `1123` bytes; invalid result contract | BLOCKED after 3 attempts |
| `codex2` | HF/FastAPI CORS independent review | None; read-only backend-source and test review | receipt `01a03849-75a8-7150-98a3-1b926b818477`; return `0`; `1799` bytes; invalid result contract | BLOCKED after 3 attempts |
| `agy1` | Static frontend/HF Docker separation review | None; read-only release-routing review | final child return `1`; `376` bytes; invalid result contract | BLOCKED after 3 attempts |
| `agy2` | Cross-lane release-gate and CORS evidence review | None; read-only receipts and release boundaries | final child return `1`; `374` bytes; invalid result contract | BLOCKED after 3 attempts |

**Hierarchy**: (1) governance policy defines the root-only boundary and waiver
contract; (2) Rule 17, the multi-account skill, and Claude mirror define the
dispatch contract; (3) `.claude/settings.json` registers PreToolUse hooks that
enforce the marked Claude session. The hook is intentionally narrow and
permits monitor/dispatch activity. It recognizes a waiver only when
`HORO_ROOT_WAIVER_ID` matches `ROOT-WAIVER: <id>` recorded in both this board
and `plans/plan.md`; no waiver marker is active for this ticket.

**Runtime limitation**: Claude hooks apply only to Claude Code tool calls and
only when the launcher sets `HORO_ORCHESTRATOR_ONLY=1`. They cannot determine a
Codex root session or enforce Codex tools automatically. Codex relies on this
governance contract, alias receipts, and final gate review until a native Codex
hook exists. This limitation is a safeguard, not execution proof.

**Acceptance checklist**:

- [x] Governance -> rules -> hooks hierarchy is documented without changing application code.
- [x] Existing Claude PreToolUse registration retains secret/destructive guard and adds an orchestrator-only guard.
- [x] Guard blocks marked-root implementation edits, QA commands, git mutations, and deploy/publish commands unless a recorded waiver marker exists.
- [x] Guard permits orchestration-safe monitoring and dispatch commands.
- [x] All four alias attempts have safe terminal metadata recorded; every child result contract is invalid and every lane is `BLOCKED` after the three-attempt limit.
- [x] Focused hook tests and ecosystem `--sync` followed by `--check` are green; sync changed no generated Codex files.

**Historical closure**: these four receipts remain `BLOCKED` and do not close
the CORS/static-separation release gate. On 2026-08-25 the owner authorized a
fresh Result Contract v2 protocol and explicitly did not waive the receipts.
The authorized work continues only under `TICKET-ALIAS-RC2-003`; its retry
counters start at attempt 1 and cannot rewrite this historical record.

### TICKET-ALIAS-RC2-003 | Result Contract v2 and Four-Alias Redispatch | [STATUS: BLOCKED — CODEX1 ATTEMPTS EXHAUSTED]

**Authorization**: owner instruction received 2026-08-25 authorizes Result
Contract v2 and a terminal CLI workaround in delegated child lanes. There is
no receipt waiver and no root-action waiver. The current/root session remains
orchestrator-only and may plan, delegate, monitor, collect receipts, and decide
the gate; it must not implement, test, review, or invoke the alias CLI itself.

**In scope**: v2 schema/config/adapter implementation by an ownership-scoped
developer child; provider-native Codex structured JSON/JSONL with output-schema
support; AGY native stream-JSON parsing; independent QA and security review;
then four fresh read-only terminal dispatches. **Out of scope**: changing prior
receipts, authentication or secret inspection, application/release mutation,
commit, push, deploy, publish, or shared writable ownership.

**Two-layer contract**:

- `ExecutionReceipt` binds protocol version, dispatch ticket/attempt, alias,
  provider/adapter, objective/ownership, safe quota status, timestamps,
  exit/transport status, safe provider session/process id when available,
  output byte count/SHA-256, and normalized `WorkResult` SHA-256.
- `WorkResult` contains `Status`, `Scope owned`, `Evidence`, `Findings`,
  `Changed files`, `Residual risk`, and `Recommended next action`.

Validation is fail closed: missing/malformed fields or events, identity/digest
mismatch, ambiguous final event, secret-bearing output, nonzero execution
without a typed failure result, or exit zero without a valid `WorkResult` is
not a receipt. Free-form inference and adapter fallback require fresh HITL.

| Alias | Fresh v2 lane | Ownership | v2 attempt | Status |
|---|---|---|---|---|
| `codex1` | Vercel gateway CORS independent review | Read-only | 3 executed | BLOCKED — `invalid-child-result-contract`; no valid receipt; retry limit exhausted |
| `codex2` | HF/FastAPI CORS independent review | Read-only | 3 not invoked | NOT DISPATCHED — held after `codex1` exhaustion |
| `agy1` | Static frontend/HF Docker separation review | Read-only | 3 not invoked | NOT DISPATCHED — held after `codex1` exhaustion |
| `agy2` | Cross-lane release-gate and CORS evidence review | Read-only | 3 not invoked | NOT DISPATCHED — held after `codex1` exhaustion |

**Checklist**:

- [x] Record fresh owner authorization for Result Contract v2; no waiver.
- [x] Preserve all four prior attempts as immutable historical `BLOCKED` evidence.
- [x] Define two-layer receipt/result governance, provider-native adapters, fail-closed rules, and fresh per-alias counters.
- [x] Run ecosystem `--sync` then `--check`: 19 Codex definitions synchronized, 0 updated, 0 obsolete, and no generated `.codex/agents` change.
- [ ] Developer child implements dispatcher/config/schema/template changes within exclusive ownership.
- [ ] Developer/DevOps child supplies an approved runtime config path and an explicit read-only role or validated sandbox override; example config and default Codex `workspace-write` are rejected.
- [ ] QA child validates valid, malformed, ambiguous, nonzero-exit, identity/digest mismatch, and secret-redaction cases.
- [ ] Code reviewer verifies fail-closed behavior, retry/HITL boundaries, root-only separation, and backward compatibility.
- [x] Focused QA completed with `87 passed`.
- [x] `codex1` attempt 3 was executed through its read-only lane and failed closed as `invalid-child-result-contract`; it produced no valid receipt.
- [x] Hold `codex2`, `agy1`, and `agy2` attempt 3: none was invoked after the terminal `codex1` failure.
- [ ] Child execution lanes return four distinct schema-valid v2 receipts. BLOCKED: `codex1` has exhausted its three attempts.
- [ ] Orchestrator confirms four distinct valid receipts and decides the release gate. BLOCKED pending a fresh owner decision and new ticket.

**Checkpoint evidence (2026-08-25)**: focused QA passed (`87 passed`). The
`codex1` read-only lane executed attempt 3 and failed closed with
`invalid-child-result-contract`; no valid receipt exists. `codex2`, `agy1`, and
`agy2` attempt 3 were not invoked. Historical attempts and release evidence are
preserved above and are not relabeled by this checkpoint.

**Success / stop**: close only when implementation, QA, and review are green and
all four fresh alias lanes provide distinct schema-valid v2 receipts. This ticket
is now `BLOCKED`: `codex1` has exhausted its three-attempt limit, so no further
alias dispatch may occur under `TICKET-ALIAS-RC2-003`. A fresh owner decision
and new ticket are required before any additional alias dispatch. Stop on
ownership conflict, authentication/permission/billing, secret exposure,
adapter ambiguity, invalid receipt, or any root implementation/CLI execution.

**Read-only execution gate**: QA found that only an example dispatch config is
currently present and Codex roles default to `workspace-write`. No v2 review
alias may start until a child proves an approved runtime config path and either
an explicit read-only role or a validated provider sandbox override. Prompt
instructions are not isolation. Missing proof is `BLOCKED`, not a waivable
receipt validation warning.

**Governance evidence (2026-08-25)**: authoritative and Antigravity skill
mirrors are byte-identical. Ecosystem sync and check both returned `0`; the
generator reported 19 Codex agent definitions, 0 updated, and 0 obsolete. No
generated Codex agent file was manually edited or changed by this governance
update. Existing trailing whitespace in unrelated earlier board additions is
preserved and is not v2 evidence.

### TICKET-ALIAS-RC2-004 | Content-Free Parse-Reason Diagnostic Follow-On | [STATUS: TODO — OWNER AUTHORIZED / QUOTA UNKNOWN]

**Fresh authorization checkpoint (2026-08-25)**: after the exhausted
`TICKET-ALIAS-RC2-003` `codex1` attempts, the owner gave fresh `approve all`
authorization for this new, bounded follow-on ticket only. `RC2-003` remains
immutable `BLOCKED` history: this ticket neither reopens it nor changes any
prior counter, result, receipt, or release-gate state.

**Scheduling metadata**: **Severity: CRITICAL**. **Work Effort: S**. Quota is
`unknown`; this is a bounded-lane-only authorization, not authority for broad
dispatch. Stop immediately if the runtime reports less than 10% remaining.

**Scope grill**:

- **IN**: content-free `provider_parse_reason` taxonomy and its focused tests;
  one fresh, explicitly recorded `codex1` read-only diagnostic attempt under
  this ticket; safe terminal classification and retry/HITL documentation.
- **OUT**: raw JSONL or provider text; receipt/session/process identifiers;
  artifact or runtime paths; secrets or credentials; application/release
  changes; deployment, publishing, staging, commits, pushes, or other git
  mutation. Do not retain any of those values in the board, plan, tests, or
  diagnostic evidence.
- **Dependencies / assumptions**: `RC2-003` remains blocked; the taxonomy is
  implemented and focused-tested by separately owned developer/QA lanes; the
  read-only isolation gate and result-contract validation must pass before an
  alias is invoked; quota is still `unknown` and may not be inferred.
- **Success**: a content-free, typed parse-reason classification is covered by
  focused tests and one new `codex1` read-only attempt returns only an approved
  terminal status. A valid result may permit separately recorded, bounded
  `codex2`, `agy1`, then `agy2` attempts; it does not authorize them by itself.
- **Stop**: runtime quota below 10%, unknown/failed read-only isolation,
  invalid or ambiguous result contract, permission/authentication/billing
  issue, ownership conflict, secret exposure, or any attempt to retain
  prohibited content. Return `NEEDS_HITL` where the next action is not already
  explicitly authorized below.

**Dependency and retry sequence**:

| Order | Owner / alias | Authorized action | Gate / next state |
|---|---|---|---|
| 1 | `developer` / `qa_tester` | Implement and test only the content-free `provider_parse_reason` taxonomy. | Focused QA must pass; no provider payload retention. |
| 2 | `code_reviewer` | Read-only review of taxonomy, test coverage, redaction boundary, and retry gate. | Must accept fail-closed boundary before any alias attempt. |
| 3 | `codex1` | Exactly one fresh, read-only diagnostic attempt, recorded as `RC2-004/codex1/attempt-1`. | If invalid/ambiguous/blocked, stop this ticket and return `NEEDS_HITL`; no automatic retry. |
| 4 | `codex2` | One separately recorded, bounded read-only attempt only after a valid `codex1` result and an explicit recorded attempt authorization. | Otherwise not dispatched. |
| 5 | `agy1` | One separately recorded, bounded read-only attempt only after the preceding valid gate and explicit recorded attempt authorization. | Otherwise not dispatched. |
| 6 | `agy2` | One separately recorded, bounded read-only attempt only after the preceding valid gate and explicit recorded attempt authorization. | Otherwise not dispatched. |

**Acceptance checklist**:

- [ ] Taxonomy uses only approved, content-free `provider_parse_reason` values; no raw output, identifiers, paths, or secrets are persisted.
- [ ] Focused taxonomy tests pass under their separately owned QA lane.
- [ ] Independent review confirms read-only isolation, fail-closed parsing, and the no-retention boundary.
- [ ] Exactly one fresh `codex1` diagnostic attempt is recorded under `RC2-004`; it does not alter `RC2-003` history.

#### `TICKET-ALIAS-RC2-004-QOBS-01` | QOBS test-first umbrella | [STATUS: CONTRACT_FROZEN — PROBE_READY]

The completed root-cause and security review requires a version-pinned,
content-free QuotaObservation artifact before any RC2-004 provider attempt can
be reconsidered. The owner's `continue` confirms this bounded remediation only.
It does not observe quota, authorize a provider child, relabel the existing
`unknown` band, or reopen any RC2-003/RC2-004 attempt.

**Fresh planning proof**: `ROOT-RUNTIME-PROOF-20260827-QOBS-01` records that the
root orchestrator verified the active runtime as `gpt-5.6-sol/medium` before
handoff. No sensitive account or runtime path is retained. The proof is scoped
to this planning handoff and cannot substitute for fresh Rule 18/Rule 11
evidence at any executable child lane.

**IN**: committed test-only baseline, QOBS schema/policy contract, content-free
probe, dispatcher and receipt-v2 binding, scheduler fail-closed integration,
focused/full QA, authoritative governance updates, and final ecosystem
sync/check.
**OUT**: all provider/alias calls; deploy, publish, push, PR/merge, credentials,
secrets, account or production mutation, raw provider output, and edits outside
the exact ownership below.
**Umbrella acceptance**: the six lanes complete in dependency order; the frozen
tests and source trailers verify against the exact baseline; QOBS rejects
malformed, stale/future, replayed, contradictory, unknown, or provenance-
mismatched evidence; focused/full regression, ecosystem sync/check, and final
Git review pass. QOBS completion still does not authorize four-alias execution.

| Child lane | One mutation editor | Severity / Work | Status | Exact ownership | Depends On |
|---|---|---|---|---|---|
| `QOBS-01-TEST-BASELINE` | `qa_tester` | CRITICAL / S | DONE — TEST_BASELINE_VERIFIED | new `tests/test_quota_observation_contract.py`; new `tests/test_quota_observation_integration.py`; new `plans/test_provenance/ticket-alias-rc2-004-qobs-01.json` only | owner confirmation + this grill |
| `QOBS-01-CONTRACT` | `developer` | CRITICAL / S | DONE — FROZEN (`1515380b436fe4d676766a62bd4de4ce1db22126`) | `.agents/schemas/multiagent-quota-observation-v1.schema.json`; `.agents/schemas/multiagent-quota-observation-artifact-v1.schema.json`; `.agents/config/multiagent_model_policy.yaml` only | TEST-BASELINE committed and verified |
| `QOBS-01-PROBE` | `developer` | CRITICAL / S | READY | `scripts/agent_quota_status_guard.py` only | CONTRACT frozen |
| `QOBS-01-DISPATCH` | `developer` | CRITICAL / M | DONE — FROZEN (`943bdd8`) | `scripts/multiagent_prompt_command.py` only | CONTRACT + PROBE frozen; focused QOBS suite passed 67 |
| `QOBS-01-SCHEDULER` | `developer` | CRITICAL / S | DONE — FROZEN (`943bdd8`) | `scripts/multiagent_ticket_scheduler.py` only | CONTRACT + DISPATCH green/frozen; focused QOBS suite passed 67 |
| `QOBS-01-QA-GOVERNANCE-SYNC` | `business_analyst` mutation editor; `qa_tester` and `code_reviewer` read-only verifiers | CRITICAL / M | GATED | authoritative `.agents/rules/17-multi-account-agent-orchestration.md`; `.agents/rules/18-adaptive-model-effort-routing.md`; `.agents/skills/multi-account-agent-orchestration/SKILL.md`; `.agents/skills/adaptive-model-effort-routing/SKILL.md`; `docs/templates/MULTIAGENT_PROMPT_COMMAND.md`; generated ecosystem mirrors only through the sync script; frozen tests are read-only | all source lanes frozen |

**Fresh QOBS-01-PROBE execution checkpoint (2026-08-27)**: user authorization
is “investigate blocked and fix it”, narrowly authorizing local source
remediation only. The fresh Rule 18 decision and Rule 11 snapshot are
`project/tests/artifacts/priority_scheduling/decision_qobs_01_probe_20260827.json`
and
`project/tests/artifacts/priority_scheduling/scheduling_snapshot_qobs_01_probe_20260827.json`.
They reserve one `developer` editor for exactly
`scripts/agent_quota_status_guard.py`, with `codex1/gpt-5.6-sol/high`,
`quota_band=unknown`, and root-medium/HITL gates recorded. The lane may run
the two frozen focused tests and
`python3 scripts/test_provenance_guard.py staged`, then stage and commit only
the source path with exact trailer
`Test-Baseline: 9847234f3f2537d0b65ecb1fc9afca87ceb517a2`. No other path may be
staged. Push, deploy, publish, credentials, secrets, provider/account action,
sync, generated edits, and external action are excluded. Ticket45's frozen
allowlist and protected data provenance blockers
`project/data/bazi_bazi_manual_chatml.jsonl` and
`project/data/distillation_checklist.json` remain unchanged and blocked.

**Required result / stop**:

- `Status`: `DONE` | `BLOCKED` | `NEEDS_HITL`.
- `Scope owned`: `scripts/agent_quota_status_guard.py` only.
- `Evidence`: focused tests, staged provenance guard, exact staged path, and
  trailer-bearing commit, if reached.
- `Findings`, `Changed files`, `Residual risk`, and `Recommended next action`
  must be returned as the Rule 11 WorkResult fields.
- Stop on test/provenance/ownership/path/scope/trailer/inventory drift; use
  `NEEDS_HITL` for authorization, quota, secret, provider, account, or
  external-action ambiguity.
- Do not mark QOBS done or ticket45 eligible before the developer result.

**Fresh QOBS-01-DISPATCH implementation checkpoint (2026-08-27)**: the
current focused integration blocker is four missing fail-closed dispatcher /
receipt APIs in `scripts/multiagent_prompt_command.py` (three consumption /
receipt helpers and `validate_quota_bound_dispatch`). QOBS-01-CONTRACT is frozen
and QOBS-01-PROBE contract behavior passes. The fresh Rule 18 decision and Rule
11 snapshot are `project/tests/artifacts/priority_scheduling/decision_qobs_01_dispatch_20260827.json`
and
`project/tests/artifacts/priority_scheduling/scheduling_snapshot_qobs_01_dispatch_20260827.json`.
They reserve one `developer` editor for exactly that source file. The lane
must implement the frozen quota-observation policy and schemas, run the
required focused suite, and commit only that source file with the exact
`Test-Baseline: 9847234f3f2537d0b65ecb1fc9afca87ceb517a2` trailer. Scheduler
work is not authorized. Preserve ticket45's frozen allowlist and protected
data blockers `project/data/bazi_bazi_manual_chatml.jsonl` and
  `project/data/distillation_checklist.json` unchanged.

**Fresh QOBS-01-SCHEDULER implementation checkpoint (2026-08-27)**: the
focused integration suite currently has seven failures because
`scripts/multiagent_ticket_scheduler.py` lacks `select_tickets_with_quota`.
QOBS-01-CONTRACT is frozen, while QOBS-01-DISPATCH remains in progress and
uncommitted in its separately owned source file. The fresh Rule 18 decision and
Rule 11 scheduling snapshot are
`project/tests/artifacts/priority_scheduling/decision_qobs_01_scheduler_20260827.json`
and
`project/tests/artifacts/priority_scheduling/scheduling_snapshot_qobs_01_scheduler_20260827.json`.
They reserve one developer lane for exactly
`scripts/multiagent_ticket_scheduler.py`; the snapshot is dependency-gated and
has no active reservation until DISPATCH is green and frozen.

**Required implementation / stop criteria**: implement fail-closed quota-aware
selection against the frozen schemas/policy/tests; reject unknown, stale/future,
replayed, contradictory, provenance/digest-mismatched, legacy-v1, and otherwise
non-executable quota evidence before selection or reservation; then run the
focused QOBS suite. Do not stage or commit until dispatcher and scheduler tests
are green. Any source/path/ownership/scope/provenance/test drift is `BLOCKED`;
authorization, quota, secret, provider, account, or external-action ambiguity is
`NEEDS_HITL`. Later source commits must carry
`Test-Baseline: 9847234f3f2537d0b65ecb1fc9afca87ceb517a2`.
Preserve ticket45's frozen allowlist and both protected data provenance blockers
`project/data/bazi_bazi_manual_chatml.jsonl` and
`project/data/distillation_checklist.json`; do not mark scheduler or QOBS done
before child evidence.

**Completion reconciliation after `943bdd8` (2026-08-27)**: QOBS-01-DISPATCH
and QOBS-01-SCHEDULER are `DONE — FROZEN`. The focused QOBS
contract/integration suite passed `67`; commit `943bdd8` contains exactly
`scripts/multiagent_prompt_command.py` and
`scripts/multiagent_ticket_scheduler.py` and carries the required
`Test-Baseline: 9847234f3f2537d0b65ecb1fc9afca87ceb517a2` trailer. No paths
are staged and `git diff --check` passed. The remaining dependency chain is
`TEST-BASELINE -> CONTRACT -> PROBE -> DISPATCH (DONE) -> SCHEDULER (DONE) ->
QA/GOVERNANCE+SYNC`; QOBS is not complete because PROBE and the final
QA/GOVERNANCE+SYNC lane remain open.

**Parent-review DRAFT — QOBS status reconciliation**: The newer metadata-only
capture is in-process validation only, not a portable QOBS receipt. Although
sanitizer v1.4.0 recognizes nested bucket metadata, strict QOBS v1 cannot be
completed from it without fabricating its required complete non-derived
percentage, limit, spend, remaining, and reached fields. The later local
repair rejecting empty fabricated scheduling-snapshot digests is replay-safe
and has delegated local evidence of 81 passing tests, compilation, and a
scoped diff check. The local repair was independently reviewed PASS; this
documentation remains a DRAFT pending parent review and acceptance. This DRAFT
neither changes the historical frozen lanes nor releases PROBE,
QA/GOVERNANCE+SYNC, provider execution, dispatcher closure, or activation. No
retry is authorized; any future provider route requires separate exact HITL and
a genuine complete contract.

**Required result / stop**:

- `Status`: `DONE` | `BLOCKED` | `NEEDS_HITL`.
- `Scope owned`: `scripts/multiagent_prompt_command.py` only.
- `Evidence`: focused suite result, exact staged/committed path, trailer, and
  fail-closed API behavior.
- `Findings`, `Changed files`, `Residual risk`, and `Recommended next action`
  must be returned as the Rule 11 WorkResult fields.
- Stop as `BLOCKED` on test, provenance, ownership, path, scope, trailer, or
  inventory drift; stop as `NEEDS_HITL` on authorization, quota, secret,
  provider, account, scheduler-scope, or external-action ambiguity.
- No QOBS completion, scheduler authorization, ticket45 eligibility, or
  release approval is inferred before the developer result and later gates.

**Test-first history gate**:

1. TEST-BASELINE stages only its two tests and closed `test-provenance-v1`
   manifest, records the exact red/negative-control argv, non-zero result, and
   concise failure fingerprint, then runs:
   `python3 scripts/test_provenance_guard.py staged`.
2. The test-only baseline was committed before any source mutation at
   `9847234f3f2537d0b65ecb1fc9afca87ceb517a2`; the umbrella is
   `TEST_BASELINE_VERIFIED`.
3. After commit, verify with
   `python3 scripts/test_provenance_guard.py verify --manifest plans/test_provenance/ticket-alias-rc2-004-qobs-01.json --baseline 9847234f3f2537d0b65ecb1fc9afca87ceb517a2 --head HEAD`.
4. Frozen tests are immutable. Every later source/governance commit must first
   pass `python3 scripts/test_provenance_guard.py staged` and carry the exact
   trailer `Test-Baseline: 9847234f3f2537d0b65ecb1fc9afca87ceb517a2`.
5. If a frozen test is wrong, stop all source work. A QA-owned, independently
   reviewed, test-only superseding baseline must preserve the original and
   record its SHA, correction reason, new hashes, and new red evidence. Never
   amend, squash, delete, weaken, or silently rewrite the original test.

**Stage / provenance / final verification commands**:

```bash
git add -- tests/test_quota_observation_contract.py tests/test_quota_observation_integration.py plans/test_provenance/ticket-alias-rc2-004-qobs-01.json
python3 scripts/test_provenance_guard.py staged
python3 scripts/test_provenance_guard.py verify --manifest plans/test_provenance/ticket-alias-rc2-004-qobs-01.json --baseline 9847234f3f2537d0b65ecb1fc9afca87ceb517a2 --head HEAD
python3 scripts/test_provenance_guard.py verify --manifest plans/test_provenance/ticket-alias-rc2-004-qobs-01.json --baseline 9847234f3f2537d0b65ecb1fc9afca87ceb517a2 --head HEAD --include-worktree
python3 scripts/sync_ai_agent_ecosystem.py --sync
python3 scripts/sync_ai_agent_ecosystem.py --check
git diff --check
```

The baseline commit itself contains tests/fixtures/manifest only. Each later
commit message includes a separate trailer line:
`Test-Baseline: 9847234f3f2537d0b65ecb1fc9afca87ceb517a2`.

**Verified baseline evidence**: commit
`9847234f3f2537d0b65ecb1fc9afca87ceb517a2`, parent
`21f8a92fa30803568faeff23cfe9c8e5c7f98ecc`; the closed manifest records the
expected red result (`67 failed`, exit `1`). The history guard returned
`PASSED`, verified both frozen test hashes, and reported no issues.

**Verified CONTRACT evidence**: commit
`1515380b436fe4d676766a62bd4de4ce1db22126` contains exactly
`.agents/schemas/multiagent-quota-observation-v1.schema.json`,
`.agents/schemas/multiagent-quota-observation-artifact-v1.schema.json`, and
`.agents/config/multiagent_model_policy.yaml`; its separate trailer is
`Test-Baseline: 9847234f3f2537d0b65ecb1fc9afca87ceb517a2`. The provenance
guard returned `PASSED`, verified both frozen test hashes, and reported no
issues.

**Rule 18 / Rule 11 gate**: the previous CONTRACT reservation/digests are
historical. TEST-BASELINE is `DONE — TEST_BASELINE_VERIFIED`; CONTRACT is `DONE
— FROZEN`; PROBE alone is `READY`. DISPATCH, SCHEDULER, and QA-GOVERNANCE-SYNC
remain gated. Each later child requires a new bound decision/snapshot and
predecessor freeze; no old decision, snapshot, or planning proof is reusable.

**Frozen security contract**:

- Retain zero raw provider stream, raw/error text, account-home/runtime path, credential, identifier, or unsanitized exception; retained errors are typed content-free codes only.
- Bind alias/provider, SHA-256 account-home digest, SHA-256 resolved-executable digest, ticket, attempt, policy version, and a one-use nonce to the exact artifact. Plain paths and executable contents are forbidden.
- Use strict domain-separated canonical JSON: UTF-8, sorted keys, minimal separators, duplicate-key/non-finite rejection, and pinned schema/protocol/canonicalization/domain/policy versions.
- Enforce maximum age `<=60s`, future tolerance `<=5s`, and atomic single use. Replay, stale/future evidence, nonce mismatch, or provenance substitution is invalid.
- Inspect every applicable safe signal: all legacy and bucket primary/secondary `usedPercent`, every individual `remainingPercent`, reached/limit markers, and spend/remaining controls. Missing/invalid applicable signal, bad unit/range, or contradiction yields `unknown`.
- Exactly `10%` is `constrained`; below `10%` is `below_10_percent`. QuotaObservation protocol v1 never emits `healthy`; greater-than-10 evidence remains `constrained` pending a later approved protocol.
- DispatchDecision v1 is legacy/non-executable for QOBS-bound provider dispatch. Scheduler input rejects any observation/ticket/decision/reservation/policy contradiction; `unknown` never becomes executable by sorting.
- ExecutionReceipt v2 transitively binds and revalidates the exact artifact, digest, provenance, nonce consumption, decision, scheduling snapshot, executable, and policy at spawn and receipt validation. A copied quota band or receipt summary is insufficient.

**Acceptance / stop gates**:

- QOBS-01-CONTRACT freezes only the two closed Draft 2020-12 schemas and policy pins; JSON/metaschema plus deterministic valid/invalid samples must pass.
- QOBS-01-PROBE emits exactly one schema-valid content-free artifact or typed `unknown`, covers all signals/controls, digests paths without retention, and performs no dispatch/retry.
- QOBS-01-DISPATCH consumes the exact nonce atomically, rejects v1/provenance/digest/age/version/replay/contradiction/unknown failures, and binds receipt-v2 without fallback.
- QOBS-01-SCHEDULER fails before selection/reservation on contradiction and applies Rule 11 only after all quota gates pass.
- QOBS-01-QA-GOVERNANCE-SYNC covers canonicalization, all signals/controls, 10% boundaries, v1-never-healthy, age/future/replay, provenance digests, contradiction rejection, v1 non-execution, and receipt-v2 transitive tamper/revalidation; frozen suites are read-only.
- QOBS-01-QA-GOVERNANCE-SYNC updates authoritative rule/skill/template sources
  only after source freeze, then runs the mandated generator; generated mirrors
  must never be edited manually.
- Any prohibited retention, missing signal, contradiction, unpinned
  version/domain, replay, digest mismatch, frozen-test mutation, missing trailer,
  scope overlap, provider/network/secret/account/deploy/publish/push/release
  action, premature sync, or manual generated edit is `BLOCKED`/`NEEDS_HITL`.
  No QOBS completion alone authorizes RC2-004.
- [ ] `codex2`, `agy1`, and `agy2` remain undispatched unless each prerequisite valid result and separately recorded attempt authorization exists.
- [ ] No provider, deploy, publish, push, PR/merge, secret, account, or
  production mutation occurred.

### 🎫 PROMPT-GOV-001 | `business_analyst` / `orchestrator` | [STATUS: DONE]

**Objective**: establish auditable, ownership-scoped multi-account agent orchestration without treating routing configuration as execution proof.

**In scope**: `PROJECT_TASKS.md`, `plans/plan.md`, Rule 17, the
`multi-account-agent-orchestration` skill, its synchronized governance mirrors,
and `docs/templates/MULTIAGENT_PROMPT_COMMAND.md`.

**Out of scope**: source code, tests, deployments, publishing, authentication,
credential mutation, secret values, and external systems.

**Required evidence**: account alias/provider, non-secret quota band or status,
safe route/session metadata when available, child result, attempt number,
artifact paths, and timestamps. A rendered alias/route/model/configuration is
routing intent only and cannot close a dispatch.

**Retry/HITL policy**: retry only the same bounded actionable failure; after
three consecutive failures, or immediately for credentials, permissions,
billing, production mutation, ownership conflict, or high-impact judgment,
return `NEEDS_HITL` with the exact decision or safe operator command.

**Acceptance criteria**:

1. Rule 17 defines ownership isolation, non-secret quota/account evidence,
   retry limits, HITL triggers, result contract, and closure gate.
2. The skill has valid frontmatter, ASCII status-tag guidance, exact safe
   command paths, and `DONE`/`BLOCKED`/`NEEDS_HITL` semantics.
3. PromptCommand documentation states dry-run default, explicit execution,
   no-secret handling, and execution-proof requirements.
4. `.agents/AGENTS.md` catalogs the skill and synchronized mirrors match the
   authoritative skill/rule content.
5. `python3 scripts/sync_ai_agent_ecosystem.py --sync` completes and the final
   `--check` passes without source/test edits.

**Final closure checklist**:

- [x] Board and plan status include ticket owner, evidence, blockers, and next action.
- [x] Rule, skill, Claude mirror, and Antigravity skill mirror are synchronized.
- [x] PromptCommand template preserves ownership, quota, retry, and HITL fields.
- [x] No secret values, credential files, source, or tests were changed.
- [x] Sync, focused governance checks, and `git diff --check` pass.
- [x] Any unresolved external permission or account decision is marked `NEEDS_HITL`.

**Closure evidence (2026-08-25)**: `python3 scripts/sync_ai_agent_ecosystem.py --sync` and its embedded checks passed; the new skill quick validator passed; the authoritative skill and Antigravity mirror match; and `git diff --check` passed for the owned governance files.

## 🧩 Decoupled Release Closure Checkpoints

These checkpoints replace the previous single release-closure workstream. They are intentionally small, independently verifiable, and resumable across quota/account changes.

| Checkpoint | Owner | Scope | Exit evidence | Stop condition |
|---|---|---|---|---|
| `CP-00-DOCS` | `business_analyst` | Reconcile ticket/plan/evidence status before execution | Updated board, plans, and evidence index | **DONE** — proceed to CP-01-LOCAL |
| `CP-01-LOCAL` | `qa_tester` / `code_reviewer` | Re-run local QA, secret scan, agent sync, quality gate | Timestamped command outputs and report paths | **DONE** — local evidence green; proceed only to separately gated external checkpoints |
| `CP-02-HF` | `devops` | Verify canonical HF origin, `/health`, deterministic API | Fresh canonical probe JSON with explicit status (`project/tests/hf_canonical_reprobe_2026-08-24.json`, `vercel_reprobe_2026-08-24.json` 3/3 GREEN) | **PASS** — HF canonical & Vercel fallback verified |
| `CP-03-AZURE` | `devops` | Validate complete Azure Actions credentials and deploy | Workflow proving login, provisioning, and `/health` (Run `32630424001` SUCCESS) | **PASS** — Azure Container Apps deploy healthy |
| `CP-04-PW` | `qa_tester` | Run the bounded production smoke Playwright profile | `project/tests/prod_button_regression_report.json` (2026-08-25 05:17:45 UTC): Vercel smoke 13/13 passed, 0 failed | **DONE** — `TICKET-QA-PW-SMOKE-20260825`; full-profile coverage remains separately unfinished |
| `CP-05-RELEASE` | `orchestrator` / `devops` | Consolidate all green release gates | Single all-green release matrix across local, HF, Vercel, and Azure | **PASS** — All multi-cloud release gates cleared |
| `CP-06-HANDOFF` | `business_analyst` | Final document sync, quota-safe handoff, parent transition | Updated board, plan links, evidence index | **READY** — Ready for operator final sign-off |

### Checkpoint execution policy

1. Execute only one checkpoint per work session unless its evidence is already present.
2. At the end of every checkpoint, record status, timestamp, command/artifact, blocker, and next checkpoint.
3. When quota is below 10%, stop implementation/release work and complete only the quota-safe update in `TICKET-META-008`.
4. No checkpoint may claim another checkpoint's evidence; local green tests do not prove external deployment health.

### 🎫 TICKET-META-001 | `orchestrator` / `business_analyst` | [STATUS: BLOCKED — HITL DEPLOY]
**Priority**: CRITICAL
**Depends On**: None
**Blocks**: Final production handoff only; implementation, QA, and local release evidence are complete.

**Current status**: All historical child implementation and local QA tickets are complete. The active release candidate is governed solely by `TICKET-V3UI-007` (local version target `1.0.0.c9f9161` / `c9f9161`). It is blocked pending fresh, hash-bound evidence and explicit HITL authorization for any production mutation. `TICKET-V3UI-006` is a historical `6c351ba` baseline and cannot prove this candidate.

#### Detailed Instructions
1. **Scope and architecture** — implement the five roadmap branches and their calculation/knowledge surfaces: Three Cosmic Styles (Tai Yi, Da Liu Ren, Qi Men), Destiny Analysis (BaZi improvements, Zi Wei, Qi Zheng Si Yu), Divination (I Ching, Liu Yao, Mei Hua), Physiognomy/Feng Shui (Xuan Kong, San He, Mian Xiang), and Date Selection (Ze Ji).
2. **Knowledge pipeline** — run the OCR/Obsidian ingestion flow, maintain the RAG vector store and exported ShareGPT JSONL dataset, and preserve traceable classical-source metadata.
3. **Deterministic engines** — implement or extend the pure-Python calculation modules under `project/core/`, including deterministic unit tests for solar terms, chart placement, interactions, and fallback behavior.
4. **Model and delivery pipeline** — execute the dataset/fine-tuning, adapter-to-GGUF/Ollama fusion, MCP tool integration, and Glassmorphism dashboard visualization work described by the roadmap and `plans/todo_tasks_plan.md`.
5. **Question/forecast alignment** — implement the six benchmark domains in `plans/question_forecast_alignment_spec.md`; pass the user’s `user_query` and extracted focus into `project/core/prompt_manager.py` and `project/core/multi_agent_debate.py`; validate direct relevance, astrological consistency, canonical evidence, and actionable guidance using the 100-point rubric and `Confidence Score > 0.85` validator threshold.
6. **TODO workstreams** — complete the six deliverables in `plans/todo_tasks_plan.md`: model fusion, external provider routing, Swiss Ephemeris, batch vault ingestion, CI/CD automation, and consultant UI enhancements.
7. **SDLC handoff** — follow the repository workflow from planning through implementation, QA, release verification, and final Kanban evidence. Create child tickets for developer, QA, DevOps, domain, and review work before execution begins.
8. **Complete `plans/plan.md` coverage** — treat its historical completed phases as required traceability/evidence, and its active or future sections as execution scope:
   - Phase 1–3: all-16-discipline E2E/snapshot visualizer baseline, seven extended SVG visualizers, and the multimodal 16-discipline consensus matrix.
   - Phase 4–6: external multi-provider gateway, multilingual/i18n interpretation, production delivery/PWA/offline support, and consultation report export.
   - Phase 7–10: DaYun/LiuNian timeline and transit clock, voice TTS/STT, synastry compatibility matrix, and interactive Ze Ji calendar/date selector.
   - Phase 11–14: LuoPan/dream decoder, multi-scenario life simulation, Imperial White/Crimson UI, and live multi-turn consultant chat with grounded RAG.
   - Phase 15–16: Kaggle NumPy/BNB pipeline compatibility and the three-tier notebook AST/pre-commit/deployment safety gate.
   - Continuous MLOps, hybrid LLM provider expansion, and Grafana latency/observability tuning.
   - Skill-context governance, agent synchronization, Grafana Cloud integration, multi-cloud architecture, quality-control standards, future LLM model expansion/circuit breaking, and the ten-policy operating consensus matrix.
9. **Status reconciliation** — link each `plan.md` phase to its existing Kanban ticket and verification evidence; do not re-open phases already marked `DONE`. Any active or future item without a current ticket must receive a child ticket before implementation.

#### Acceptance Criteria
- [x] All roadmap modules and their source/algorithm boundaries are mapped to implementation files and child tickets.
- [x] OCR/RAG ingestion produces traceable Markdown, vector-store, and JSONL outputs without losing source metadata.
- [x] Calculation engines have deterministic tests covering the implemented branches and pass the project’s required pytest gate.
- [x] The six-domain benchmark contains executable cases for direct relevance, logic consistency, canonical evidence, and actionable guidance.
- [x] Prompt/debate routing preserves the user’s requested focus, and validator evidence meets `Confidence Score > 0.85`.
- [x] The six TODO workstreams have implementation, test, and release evidence recorded in the child tickets.
- [x] Every section of `plans/plan.md` is dispositioned as `DONE` with evidence, `DOING`, or `TODO` with a child ticket; no plan section is left untracked.
- [x] CI/CD, secret scan, agent synchronization, pre-deployment review, and required E2E/UI regression gates pass before release.
  - **Current status:** Local gates are GREEN — `code_reviewer --review --use-python` reports `READY_FOR_PROD` (`645 passed, 4 skipped, 6 warnings`); quality gate 4-stage PASSED (`100%`); secret scan `0` leaks (1,533 files); agent sync 100% synchronized; button regression `25/25` passed. HF canonical backend `CP-02-HF` is now **PASS** (3/3 green, 2026-08-23 11:12 +07). Remaining blockers are external: Azure RBAC (`CP-03-AZURE`) and production Playwright authorization (`CP-04-PW`) — both require operator action, not local implementation.
  - **Next action:** Execute the consolidated release gate matrix once Azure RBAC + Playwright are cleared. Local evidence bundle is ready.
  - **Gate Ref:** `G-META-001-CORE`.
- [x] `PROJECT_TASKS.md`, the four source plans, and the final delivery evidence are synchronized with the actual implementation state.
  - **Current status:** `PROJECT_TASKS.md`, `plans/plan.md`, `plans/todo_tasks_plan.md`, `plans/question_forecast_alignment_spec.md`, and `plans/metaphysics_learning_roadmap.md` are aligned with implementation state as of 2026-08-23 11:12 +07. HF canonical backend green status recorded in the checkpoint tables. Final lockstep still waits on Azure RBAC + Playwright before `CP-05-RELEASE` can fire.
  - **Next action:** Finalize the evidence bundle only after all pending items in `Unresolved Gate Recovery Actions` are completed and verified in one run.
  - **Gate Ref:** `G-META-001-SYNC`.

#### Definition of Done
This ticket is `DOING` while child tickets are being executed. It moves to `DONE` only when every child ticket is complete, all acceptance evidence is recorded, the relevant test/release gates pass, and the final Kanban/documentation synchronization is verified.

### 🎫 TICKET-META-007 | `orchestrator` / `business_analyst` | [STATUS: DONE]
**Priority**: HIGH
**Depends On**: `TICKET-META-001`
**Blocks**: Future safe delegation and Claude Code prompt reuse.

#### Scope Boundary
- **IN**:
  1. Refresh the orchestrator delegation model for a new sub-agent round.
  2. Define one clear owner per workstream: BSA/status, DevOps/release, QA/evidence, Developer/implementation, and Code Reviewer/safety.
  3. Add Claude Code three-level command governance: hooks as hard constraints, context-aware rules, and compact `CLAUDE.md` global context.
  4. Provide copy-ready prompt examples for root orchestrator, DevOps, QA, and BSA delegation.
- **OUT**:
  1. Reading or printing secret values.
  2. Rotating or syncing credentials.
  3. Running external deployment, production Playwright, or push operations.
  4. Editing generated `.codex/agents/*.toml` manually.

#### New Delegation Round Matrix
| Lane | Agent | Ownership | Current action | Stop condition |
|---|---|---|---|---|
| BSA/status | `business_analyst` | `PROJECT_TASKS.md`, `plans/**`, governance docs, skills/rules | Update task visibility and Claude Code command-governance documentation | `DONE` when docs identify ownership, evidence, blockers, and HITL actions |
| DevOps/release | `devops` | CI/CD workflows, cloud deployment evidence, secret names only | Monitor external release blockers and provide operator commands without exposing secret values | `NEEDS_HITL` if platform credential/permission update is required |
| QA/evidence | `qa_tester` | pytest/API/UI/Playwright readiness and reports | Validate whether live backend and production Playwright gates are runnable | `BLOCKED` until live backend health and production E2E authorization are available |
| Developer/implementation | `developer` | Assigned source/workflow/test files only | Patch implementation only when a verified failing gate maps to a specific file owner | `DONE` after targeted tests pass |
| Safety review | `code_reviewer` | Secret scan, safety audit, release decision support | Confirm no secret leaks and no unsafe release claim | `NEEDS_HITL` if a leak or unsafe external gate remains |

#### Acceptance Criteria
- [x] Claude Code Level 1 hook wiring exists in `.claude/settings.json`.
- [x] Context-aware Claude Code rules exist under `.claude/rules/`.
- [x] Repository governance rule exists in `.agents/rules/12-claude-code-three-level-governance.md`.
- [x] `orchestrator-delegation` skill includes the standard delegation round and copy-ready prompt examples.
- [x] `CLAUDE.md` points to the three-level governance model without becoming the only enforcement layer.
- [x] Run syntax/secret-scan validation for the changed governance files.
  - **Evidence:** `python3 -m json.tool .claude/settings.json` passed; `PYTHONPYCACHEPREFIX=/private/tmp/horo_pycache python3 -m py_compile .agents/hooks/pre_tool_check.py .agents/hooks/post_tool_audit.py` passed; Claude hook JSON spot checks deny force-push and `.env` reads; `python3 project/core/code_reviewer.py --scan-secrets` passed with `0` leaks across `1,523` files; `python3 scripts/sync_codex_agents.py --check` and `python3 scripts/sync_sdlc_agents.py --check` passed.

#### HITL Notes
- Credential, production deploy, and production Playwright execution remain HITL-gated unless the user provides current explicit authorization and required non-secret evidence.
- Any secret value printed by a CLI must be considered compromised and rotated before propagation.

### 🎫 TICKET-META-008 | `orchestrator` / `business_analyst` / `devops` | [STATUS: DONE]
**Priority**: HIGH
**Depends On**: `TICKET-META-005`, `TICKET-META-006`
**Blocks**: Safe account handoff when current assistant/account quota is exhausted.

#### Scope Boundary
- **IN**:
  1. Keep `PROJECT_TASKS.md` and `plans/plan.md` updated with account-migration status before context/quota exhaustion.
  2. Record only non-secret credential state: GitHub CLI auth validity, Doppler CLI auth availability, Telegram token/chat-id presence, and exact blocked gates.
  3. Maintain safe resume commands that do not print secret values.
  4. Ensure dirty-file policy is explicit: commit scoped work separately, review unrelated dirty files by batch, quarantine generated artifacts only after review, and clean after 7 stable days.
- **OUT**:
  1. Printing or copying secret values into documentation.
  2. Editing generated `.codex/agents/*.toml` manually.
  3. Making release claims before all external gates are green.

#### Current Account/Quota Handoff Status
- Latest scoped commits:
  - `2638d84` — Scoped Telegram bot and controller fixes.
  - `a6467e5` — Telegram notification secret config support.
  - `87ecc84` — Persist Telegram Chat ID from bot/webhook updates.
- Telegram runtime check: bot token is present locally; `TELEGRAM_CHAT_ID=804297094` is present in `.env` and verified valid via `getChat` API (`chat_type=private`, `ok=true`); `TELEGRAM_BOT_TOKEN` present (46 chars).
- GitHub CLI: `gh auth status` now reports account `pphothidaen` authenticated via keyring with `repo` and `workflow` scopes; do not print token values.
- Doppler CLI: `doppler me` reports authenticated; Doppler dry-run verified (`sync_doppler_secrets.py`).
- Local secret hygiene: expired `GH_TOKEN` was removed from `.env` and `.env.production`; latest secret scan remains `0` leaks across `1,530` files.
- Governance enforcement: `scripts/agent_quota_status_guard.py` checks `/status`/runtime quota signals; `.agents/hooks/pre_tool_check.py` and `.claude/hooks/pre_tool_guard.py` invoke it when quota status is present, and `bsa-doc-skill-management` defines the low-quota handoff workflow.

#### Documentation checkpoint result — `CP-00-DOCS` (2026-08-22 21:12 +07)
- **Status:** DONE for the owned documentation/governance scope; this does not close the parent release workstream.
- **Scope grill:** in scope was board/plan/evidence reconciliation and a safe next-ticket handoff; out of scope were source/tests/workflows, generated or legacy agent definitions, deployment, credentials, secret sync, and production E2E. Inputs were the current worktree, the canonical HF probe artifact, and existing local evidence. Success requires aligned checkpoint status, explicit blockers, non-secret credential state, and a runnable next action; stop before any external mutation or green release claim.
- **Evidence:** `git status --short`; `git diff --check`; `python3 scripts/sync_ai_agent_ecosystem.py --check` passed. `project/tests/backend-release-check-hf-canonical.json` remains authoritative and records static `404`, backend `/health` `503`, and deterministic API `503`.
- **Reconciled files:** `PROJECT_TASKS.md`, `plans/plan.md`, and `plans/todo_tasks_plan.md`. Existing unrelated `project_tickets.md` edits were preserved and not modified.
- **Next executable checkpoint:** `CP-01-LOCAL`, owned by `qa_tester` / `code_reviewer`. Use the documented local QA, secret scan, sync, and quality-gate commands; stop on any local failure and do not deploy.
- **HITL required:** owner action remains necessary for Doppler secret sync verification, review of unrelated dirty files, HF Space static CDN flap resolution, and production Playwright full-profile authorization. Telegram chat-id is verified; Doppler CLI is authenticated. None of the remaining items is claimed green here.

#### Safe Resume Commands
```bash
python3 project/core/code_reviewer.py --scan-secrets
python3 -m pytest project/tests/test_telegram_bot.py project/tests/test_secret_redaction.py project/tests/test_telegram_connection_config.py -q
python3 scripts/sync_doppler_secrets.py --env-file .env --project horo-consultant --config prd --dry-run
gh auth status
doppler me
```

#### Acceptance Criteria
- [x] Account-migration continuity ticket exists in `PROJECT_TASKS.md`.
- [x] Plan-level quota/account migration guard is recorded in `plans/plan.md`.
- [x] Governance hook/rule/skill enforcement exists for `/status` or runtime quota below 10%.
- [x] GitHub CLI is re-authenticated without printing values.
- [x] Telegram secrets are synced to GitHub Actions without printing values.
  - **Verified (2026-08-23 16:27 +07):** `TELEGRAM_CHAT_ID=804297094` is present in `.env` and confirmed valid via `getChat` API call (`chat_type=private`, `ok=true`); `TELEGRAM_BOT_TOKEN` is present (46 chars). Chat ID was previously recorded as empty in `PROJECT_TASKS.md`/`plans/plan.md` but is actually populated — docs updated below.
- [ ] Doppler CLI/API auth is available and `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` are synced without printing values.
- [x] Final handoff includes clean scoped commits and a reviewed disposition for unrelated dirty files.
  - **Reviewed disposition (2026-08-23 16:27 +07):** The 4 dirty files (`grayzone_answers.json`, `hitl_reviews.json`, `hitl_approved.jsonl`, `hitl_approved_with_metadata.jsonl`) contain only `last_updated` / `answered_at` timestamp changes — no content, schema, or answer changes. They are safe to keep dirty until a scoped HITL data commit is made; no quarantine action required.

### 🎫 TICKET-META-009 | `developer` / `qa_tester` | [STATUS: DONE]
**Priority**: MEDIUM
**Depends On**: `CP-03-AZURE`, `CP-04-PW`, `CP-05-RELEASE`
**Blocks**: None; release-gate prerequisites were green before execution.

#### Scope Boundary
- **IN**:
  1. Upgrade Python lockfile dependencies with `uv lock --upgrade` using a workspace-local cache if the default user cache is unavailable.
  2. Upgrade Rust dependencies with `cargo update --manifest-path rust_core/Cargo.toml`.
  3. Review dependency diffs before committing any version movement.
  4. Run focused compatibility checks after upgrade: dependency resolution, Rust tests that cover changed crates, Python import/API smoke checks, and any affected pytest subset.
- **OUT**:
  1. Running broad dependency upgrades while release checkpoints or operator-gated production verification are still active.
  2. Editing `requirements.txt`, `pyproject.toml`, `Cargo.toml`, or lockfiles manually unless a resolver exposes a required compatibility constraint.
  3. Combining dependency upgrade work with deployment, credential, secret, or production Playwright actions.

#### Execution Order
1. Finish or explicitly defer the release-gate blockers first: `CP-03-AZURE`, `CP-04-PW`, then `CP-05-RELEASE`.
2. Create a clean upgrade branch or isolated worktree so existing dirty files and release evidence are not mixed with dependency churn.
3. Run Python and Rust lockfile upgrades separately; record exact commands, resolver output, and changed packages.
4. Validate locally before any push: `python3 scripts/sync_ai_agent_ecosystem.py --check`, targeted pytest, Rust tests, and `git diff --check`.

#### Stop Conditions
- Stop immediately if a resolver wants to change major-version ranges that are not already allowed by `requirements.txt` or `Cargo.toml`.
- Stop if network/cache permissions are unavailable; request explicit approval rather than bypassing the dependency manager.
- Stop if any release checkpoint becomes active again; dependency upgrade remains lower priority than production recovery.

#### Acceptance Criteria
- [x] Python dependency lockfile upgraded by `env UV_CACHE_DIR=/private/tmp/horo-uv-cache uv lock --upgrade`; reviewed diff updates `idna` 3.18→3.19, `timezonefinder` 8.2.5→8.3.0, adds `timezonefinder-data` 1.2026.3, and updates `uvicorn` 0.52.3→0.52.4.
- [x] Rust lockfile upgraded by `cargo update --manifest-path rust_core/Cargo.toml`; reviewed diff updates `h2` 0.4.18→0.4.19 and `syn` 3.0.3→3.0.4.
- [x] Locked resolution passes (`uv lock --check`; `uv sync --locked --dry-run`). Focused Python compatibility suite passes `19 passed`; Rust `cargo test --locked` passes `40 passed, 7 ignored`.
- [x] `git diff --check` passes; only `uv.lock` and `rust_core/Cargo.lock` changed for this ticket. Existing visual-integrity dirty files were preserved.

#### Final evidence
- Resolver previews showed no major-version movement or manifest edits.
- No deployment, credential, secret, or production Playwright action was performed.

### 🎫 TICKET-META-002 | `domain_master` / `developer` | [STATUS: DONE]
**Priority**: CRITICAL
**Depends On**: `TICKET-META-001`
**Blocks**: `TICKET-META-004`, `TICKET-META-006`
**Closure evidence**: Archived to [`docs/RELEASE_NOTES.md`](docs/RELEASE_NOTES.md).

### 🎫 TICKET-META-003 | `developer` | [STATUS: DONE]
**Priority**: HIGH
**Depends On**: `TICKET-META-001`
**Blocks**: `TICKET-META-006`
**Closure evidence**: Archived to [`docs/RELEASE_NOTES.md`](docs/RELEASE_NOTES.md).

### 🎫 TICKET-META-004 | `developer` / `qa_tester` | [STATUS: DONE]
**Priority**: CRITICAL
**Depends On**: `TICKET-META-001`, `TICKET-META-002`
**Blocks**: `TICKET-META-006`
**Closure evidence**: Archived to [`docs/RELEASE_NOTES.md`](docs/RELEASE_NOTES.md).

### 🎫 TICKET-META-005 | `devops` / `developer` | [STATUS: DONE]
**Priority**: HIGH
**Depends On**: `TICKET-META-001`, `TICKET-META-003`
**Blocks**: `TICKET-META-006`

#### Detailed Instructions
Reconcile every active or future section of `plan.md` with implementation or a child ticket. Cover hybrid provider failover, Grafana/observability, CI/CD, multi-cloud deployment, skill and agent synchronization, release safeguards, caching/rate limits/security, and future model circuit-breaking architecture. Do not reopen historical `DONE` phases without contrary evidence.

#### Current Blocker
- None. Azure workflow, Hugging Face canonical backend, and multi-cloud configurations are fully cleared and passing.

#### Acceptance Criteria
- [x] Each active/future plan section has an owner, ticket, dependency, and measurable gate.
- [x] Provider, observability, CI/CD, security, and agent-sync checks pass for the implemented scope.
  - **Current status (DONE):** Agent sync passes (`python3 scripts/sync_sdlc_agents.py --check`, `python3 scripts/sync_codex_agents.py --check`), provider/observability/CI/security convergence verified, multi-cloud gates clear.
  - **Gate Ref:** `G-META-005-SECURE`.
- [x] Rollback and release evidence is recorded before production claims.

### 🎫 TICKET-META-006 | `qa_tester` / `code_reviewer` / `business_analyst` | [STATUS: DONE]
**Priority**: CRITICAL
**Depends On**: `TICKET-META-002`..`005`
**Blocks**: None

#### Detailed Instructions
Run the required unit, integration, UI/E2E, security, agent synchronization, pre-deployment, and documentation audits. Reconcile all four source plans against actual implementation evidence, update ticket statuses, and record the final handoff without marking incomplete work as done.

#### Current Verification Evidence
- [x] Deterministic and integration QA: `621 passed` (fresh reviewer summary at 2026-08-21 15:43:59) including engines, routing, ingestion, MCP, observability, and regression scopes.
- [x] Button and endpoint contract regression: `25/25 PASSED`.
- [x] Full local QA: current local `code_reviewer --review --use-python` run records `621 passed`, `8 skipped`, `12 warnings` and marks `overall_status: READY_FOR_PROD`.
- [x] Fresh full local pytest revalidation on 2026-08-21 records `582 passed`, `8 skipped`, and `12 warnings`; no local test failures remain.
  - **Current status:** Network-dependent and socket-dependent cases are guarded (`RUN_REMOTE_INTEGRATION`, local bind skip), so remaining failures are reduced to external-environment gate execution requirements, not local-suite determinism.
  - **Gate Ref:** `G-META-006-FULLQA`.
- [x] Browser readiness regression: `15/15 PASSED` with service-worker isolation; no product fallback is permitted.
- [x] Secret scan: `0` leaks across `1,507` files (fresh reviewer run at 2026-08-21 15:43:59).
- [x] Hugging Face static payload dry-run: `21` files, `3.75 MB`, authenticated payload audit passed.
- [x] Authorized push: remote `origin/main` advanced to `bbc5bc2`; Vercel production deployment `dpl_BpRzm5avDj4KudRYQMpxDYCMD1Zv` is READY.
- [x] HF static production workflow `32016627926` completed successfully; static payload is published for `bbc5bc2`.
- [x] Vercel API probe executed; in this run production curl checks are `2/3` with `POST /api/v1/bazi/interpret` returning `503` (`canonical_bazi_unavailable`) and missing `X-AI-Source`/`X-AI-Model` headers.
- [x] Local release-verifier routing and synthetic-monitor fallback are covered by focused regression tests: an explicit backend URL takes precedence, a canonical HF Space ID derives the backend URL when unset, and static `/index.html` fallback no longer crashes the monitor.
- [x] 2026-08-21 15:43 local revalidation: code review passed with notebook audit clean; secret scan found `0` leaks across `1,507` files, and the UI contract suite passed `25/25` checks.
- [x] Historical HF Docker deployment evidence exists for workflow `32577425927` / commit `52149b7`.
- **AUTHORITATIVE CURRENT STATUS (`CP-02-HF`):** `project/tests/hf_canonical_reprobe_2026-08-24.json` and `project/tests/vercel_reprobe_2026-08-24.json` are **3/3 GREEN** (static UI 200, backend `/health` 200, deterministic API 200). `CP-02-HF` is **PASS**.
  - **Gate Ref:** `G-META-006-BACKEND` / `CP-02-HF`.
- `CP-03-AZURE`: replace GitHub Azure credentials with complete non-secret field configuration, rerun the workflow, and verify provisioning plus `/health`.
  - **Current status:** **RESOLVED / PASS** — GitHub Actions run `32630424001` (2026-08-23 16:20 +07, commit `6c8ee89`) completed with `success`: build/push Docker, Azure login + preflight + deploy to Southeast Asia, ingress config, health verification, and Hermes headless post-deploy E2E all passed. RBAC remediation is effective in Actions runner context.
  - **Gate Ref:** `G-META-005-AZURE`.
- **Historical evidence (superseded):** `production-verification.json` reported `3/3` and `synthetic-health.json` reported `2/2` for an earlier deployment.
- [x] Release CI confirmation for the previously reported Rust formatting drift and Bandit B602 findings.
  - **Current status:** GitHub Actions `Unified CI & Quality Audit Pipeline` run `32571990179` for `056b1aa` completed successfully. Local Rust formatting, Rust vector/security tests, MLOps Python compilation, and CI Bandit command pass with no issues.
  - **Gate Ref:** `G-META-005-RUSTCI`.
- [x] Rust/Python full-review wrapper completion: wrapper command path confirmed; accepted commands are `--review --use-python` and `--review`.
  - **Current status:** `python3 project/core/code_reviewer.py --review --use-python` and `python3 project/core/code_reviewer.py --review` execute deterministically with `READY_FOR_PROD`.
  - **Gate Ref:** `G-META-006-WRAPPER`.
- [x] Live production smoke Playwright E2E: `TICKET-QA-PW-SMOKE-20260825` completed against the Vercel fallback at 2026-08-25 05:17:45 UTC with **13/13 expected smoke controls passed** and 0 failed. The smoke scope excludes the nine full-profile discipline checks; full-profile coverage remains separately unfinished. `CP-04-PW` is **DONE** for smoke scope.
  - **Gate Ref:** `G-META-006-PW`.

#### Acceptance Criteria
- [x] Required pytest, UI regression, E2E, secret scan, and code-review gates pass.
  - **Current status (PASS):** Local QA 100%, 0 leaks, HF canonical 3/3, Vercel 3/3, Azure green, Playwright verified. Consolidated release matrix is PASS (`CP-05-RELEASE`).
  - **Gate Ref:** `G-META-001-CORE`.
- [x] Agent definitions are synchronized with zero drift.
  - **Current status:** Sync checks passing (`python3 scripts/sync_sdlc_agents.py --check`, `python3 scripts/sync_codex_agents.py --check`, `python3 scripts/sync_ai_agent_ecosystem.py --check`).
  - **Gate Ref:** `G-META-001-SYNC`.
- [x] All child tickets have evidence-backed `DONE` status.
  - **Current status:** `TICKET-META-001` through `TICKET-META-008` are `DONE`.
  - **Gate Ref:** `G-META-001-SYNC`.
- [x] Parent ticket is moved to `DONE` only after the complete audit passes.
  - **Current status:** Complete multi-cloud audit passed; `CP-06-HANDOFF` is `READY`.
  - **Gate Ref:** `G-META-001-SYNC`.

### Unresolved Gate Recovery Actions (mapped to checkpoints)
- `CP-01-LOCAL` baseline is currently available from the latest evidence snapshot; rerun it only after release-affecting changes.
- Local checks completed in this workspace:
  - `cargo fmt --manifest-path rust_core/Cargo.toml --all` completed successfully.
  - `cd rust_core && cargo fmt --all -- --check` completed successfully.
  - Local `project/mlops` scan shows no `shell=True` / `os.system` subprocess anti-patterns tied to Bandit B602 in a literal string search.
- Exact CI Bandit command passes locally; retain CI run evidence under `CP-01-LOCAL`/`G-META-005-RUSTCI`.
- `CP-02-HF`: canonical artifact `project/tests/backend-release-check-hf-canonical-2026-08-23-latest.json` (2026-08-23 11:12 +07) is 3/3 GREEN, but fresh 5-sample multi-probe at 16:48 +07 shows HF **static UI (`static.hf.space`) consistently 404** while Docker backend `/health` and deterministic API remain stable 200. Vercel fallback is stable 3/3 GREEN. **Downgraded from PASS to FLAPPING** — backend healthy, static CDN path unstable. **Next action:** characterize flap window + operator decision (Vercel primary vs HF static repair); attach `project/tests/hf_static_ui_flap_characterization_2026-08-23.json`.
- `CP-03-AZURE`: replace GitHub Azure credentials with complete non-secret field configuration, rerun the workflow, and verify provisioning plus `/health`.
- `CP-04-PW`: `TICKET-QA-PW-SMOKE-20260825` is **DONE**. Playwright `chromium` ran the bounded smoke profile against the Vercel fallback (`horo-consultant-psi.vercel.app`) at 2026-08-25 05:17:45 UTC with **13/13 expected controls passed** and 0 failed; `project/tests/prod_button_regression_report.json` is the artifact. The smoke profile intentionally excludes nine discipline checks. **Separate unfinished gate:** obtain authorization and run the full profile (22 controls), then archive and assess that evidence independently.
- `CP-05-RELEASE`: run only after CP-01 through CP-04 have current evidence.
- `CP-06-HANDOFF`: synchronize docs and transition tickets only after the consolidated matrix is green.

#### Unresolved Gate Ownership & Validation
| Gate ID | Gate | Owner | Action/Validation target |
|---|---|---|---|
| `G-META-006-BACKEND` | `HF_BACKEND_SPACE_ID` + Docker/HF backend deployment smoke checks | `devops` | Explicitly approve and publish the 69.78 MB Docker payload to `pphothidaen/horoconsultant-core-backend`, then verify canonical HF `/health` and API availability. |
| `G-META-005-AZURE` | `AZURE RBAC` remediation (`Azure Container Apps — Production Deployment`) | `devops` | RBAC is granted and local Resource Group read preflight passes; fix GitHub Azure credential secrets, rerun `Azure Container Apps — Production Deployment`, and confirm both login and provisioning stages pass. |
| `G-META-005-RUSTCI` | Rust formatter + Bandit `B602` remediation (`project/mlops`) | `developer`, `code_reviewer` | Apply formatter/bandit fixes and rerun release CI to clear the red security/format gate. |
| `G-META-006-WRAPPER` | Full-review wrapper convergence | `code_reviewer` | Confirm the wrapper target command, run `python3 project/core/code_reviewer.py --review --use-python`, and confirm deterministic completion. |
||| `G-META-006-PW` | Full-profile production Playwright authorization + run | `qa_tester` | Smoke scope is closed by `TICKET-QA-PW-SMOKE-20260825`: Vercel smoke artifact at 2026-08-25 05:17:45 UTC reports 13/13 expected controls passed. **Unfinished separate gate:** capture authorization, run the 22-control full profile, archive the result, and triage any failures independently. |
| `G-META-006-FULLQA` | Full local QA + canonical-backend unavailable assertions | `qa_tester`, `code_reviewer` | Execute local full QA suite including BaZi 503-path assertions; record canonical timestamped report. |
| `G-META-005-SECURE` | Provider/observability/CI/security convergence | `devops`, `developer` | Ensure provider/observability and CI/security checks green in consolidated release gate matrix. |
| `G-META-001-CORE` | Core release gates (CI, E2E/UI, secret scan, agent sync) | `devops`, `qa_tester` | Re-run consolidated release gate matrix and verify all required gates are green before release. |
| `G-META-001-SYNC` | Final project/plan/evidence synchronization | `business_analyst`, `orchestrator` | Close remaining evidence links, confirm `PROJECT_TASKS.md` and source plans are aligned, archive final status snapshot. |

#### Required Evidence Matrix (Attach on gate completion)
| Gate ID | Required proof | Suggested artifact location |
|---|---|---|
| `G-META-006-BACKEND` | Verified environment var `HF_BACKEND_SPACE_ID`; deployment run log for Docker + canonical HF runs; endpoint probe logs for `/health` (`200` or explicit dependency-fallback `503`). | CI workflow log + smoke-test output file in release notes. |
| `G-META-005-AZURE` | Azure workflow log proving successful `azure/login` + provisioning stages after RBAC remediation. | GitHub Actions log (workflow `Azure Container Apps — Production Deployment`) archived to handoff note. |
| `G-META-005-RUSTCI` | Rust formatter and bandit reports with zero blocking findings; green release CI after fixes. | Release CI report + `cargo fmt --check` output + `bandit` report (from CI runner if local toolchain lacks Bandit). |
| `G-META-006-WRAPPER` | Wrapper transcript showing no hangs and deterministic completion; stable exit code and pass count. | Wrapper debug log + final stdout/stderr artifact. |
| `G-META-006-PW` | Signed-off authorization evidence and production Playwright run artifact proving browser E2E pass set. | Authorization evidence + Playwright report artifact path. |
| `G-META-006-FULLQA` | Timestamped local QA run with `582` passed, `8` skipped, and network-sensitivity notes for any canonical-bazi API fallback path assertion. | Local QA report snapshot, environment timestamp, and `project/tests/local_release_readiness_2026-08-17.md`. |
| `G-META-005-SECURE` | Consolidated provider/observability/CI/security matrix with all checks green. | Release gate checklist + matrix log. |
| `G-META-001-CORE` | Full consolidated release-matrix evidence with all gates green: CI, E2E/UI, secret scan, pytest, pre-deployment checks. | Release gate matrix snapshot + `PROJECT_TASKS.md` status comment. |
| `G-META-001-SYNC` | Final evidence snapshot including updated `PROJECT_TASKS.md`, links to four source plans, unresolved blockers status, and final archive. | Status archive + evidence bundle index. |

#### Gate Execution Commands (Recommended)
| Gate ID | Recommended command(s) |
|---|---|
| `G-META-006-BACKEND` | `HF_BACKEND_SPACE_ID=... python3 scripts/publish_space_hf.py --space-id \"$HF_BACKEND_SPACE_ID\" --sdk docker`<br/>`HF_BACKEND_URL=https://pphothidaen-horoconsultant-core-backend.hf.space HF_STATIC_CDN_URL=https://pphothidaen-horoconsultant-core-backend.static.hf.space python3 scripts/run_live_health_verification.py --json-output project/tests/backend-release-check-hf-canonical.json`<br/>`HF_BACKEND_URL=https://horo-consultant-psi.vercel.app python3 scripts/run_live_health_verification.py --json-output project/tests/backend-release-check.json` |
| `G-META-005-AZURE` | `gh workflow run "Azure Container Apps — Production Deployment" -f force_rebuild=true`<br/>`gh run list --workflow="Azure Container Apps — Production Deployment" --limit=1`<br/>`gh run view <run_id> --log-failed --job <deploy_job_id>` |
| `G-META-005-RUSTCI` | `cd rust_core`<br/>`cargo fmt --all -- --check`<br/>`cargo test --no-default-features --test test_vector_search`<br/>`cd ..`<br/>`bandit -r project/mlops -x project/kaggle_kernel -s B101,B404,B603,B311,B324,B110 -lll` |
| `G-META-006-WRAPPER` | `python3 project/core/code_reviewer.py --review --use-python` |
|| `G-META-006-PW` | `python3 scripts/run_prod_e2e_playwright.py --profile full`<br/>`HORO_PUBLIC_URL=https://horo-consultant-psi.vercel.app python3 scripts/run_prod_e2e_playwright.py --profile smoke`<br/>**Smoke verified 2026-08-25 05:17:45 UTC:** Vercel fallback completed 13/13 expected smoke controls, 0 failed (`TICKET-QA-PW-SMOKE-20260825`). This gate remains for the separately unfinished 22-control full-profile run. |
| `G-META-006-FULLQA` | `python3 -m pytest -q project/tests/` |
| `G-META-005-SECURE` | `python3 -m pytest project/tests/test_ai_provider_router.py project/tests/test_ai_provider_router_tier3.py project/tests/test_llm_multirouter.py -q`<br/>`python3 -m pytest project/tests/test_observability.py project/tests/test_rust_extensions.py -q`<br/>`python3 scripts/grafana_cloud_exporter.py --check-connection --dry-run` |
| `G-META-001-CORE` | `python3 scripts/run_quality_gate.py`<br/>`python3 project/core/code_reviewer.py --scan-secrets`<br/>`python3 scripts/run_button_regression.py` |
| `G-META-001-SYNC` | `git status --short PROJECT_TASKS.md plans/*.md`<br/>`git diff -- PROJECT_TASKS.md plans/metaphysics_learning_roadmap.md plans/plan.md plans/question_forecast_alignment_spec.md plans/todo_tasks_plan.md` |


## 📣 RELEASE NOTES (historical completion archive)
Full historical completion details are tracked in [docs/RELEASE_NOTES.md](docs/RELEASE_NOTES.md).

## 📋 Release Handoff Checklist
Use [docs/RELEASE_HANDOFF_CHECKLIST.md](docs/RELEASE_HANDOFF_CHECKLIST.md) for the current gate-by-gate closure matrix and remaining operator actions before marking final ticket completion.

---

## 🚀 SPRINT: Horo Architecture v3.0 — Data Contracts & WBS Bootstrap — 2026-08-24
**Grill Gate Status**: ✅ APPROVED (Ref: `/plans/plan.md` — GRILL REPORT 2026-08-24T18:11:30+07:00)  
**Sprint Tracking Lead**: orchestrator (agy2)  
**Commit**: `7e6cbe7` | **Git Tag**: `v3.0-data-contracts`

| Ticket ID | Assigned Agent | Task Summary | Status | Dependencies |
|---|---|---|---|---|
| `TICKET-HORO30-001` | `agy2` (orchestrator) | สร้าง WBS `TDD-HORO-v3.0/` structure + `01_DATA_CONTRACTS/` เต็ม + `04_TEST_PLANES/` เต็ม + `02/03` placeholder | ✅ DONE | None |
| `TICKET-HORO30-002` | `agy2` (orchestrator) | pytest validation suite (69 tests) + secret scan (0 leaks) | ✅ DONE | TICKET-HORO30-001 |
| `TICKET-HORO30-003` | `agy2` (orchestrator) | sync_ai_agent_ecosystem.py --check PASS + PROJECT_TASKS.md update | ✅ DONE | TICKET-HORO30-002 |
| `TICKET-HORO30-004` | `agy2` (orchestrator) | git commit `7e6cbe7` + tag `v3.0-data-contracts` + prepend GRILL REPORT | ✅ DONE | TICKET-HORO30-003 |

### Sprint Deliverables — All DONE ✅

| File | Description |
|---|---|
| `TDD-HORO-v3.0/01_DATA_CONTRACTS/proto/astro_kernel_service.proto` | gRPC proto3 — L1 Astro Kernel Service (5 methods, 11 messages, 2 enums) |
| `TDD-HORO-v3.0/01_DATA_CONTRACTS/schemas/claim_emission_v3.0.json` | JSON Schema draft-07 — Common Claim Emission (AtomicClaim, EpistemicTrace, ConfidenceVector, PotentialConflict) |
| `TDD-HORO-v3.0/01_DATA_CONTRACTS/schemas/convention_profile.json` | JSON Schema — Convention Profile (profile_hash, CanonicalBook, CalculationConventions, CrossDomainFirewall) |
| `TDD-HORO-v3.0/01_DATA_CONTRACTS/schemas/tri_graph_node_edge.json` | JSON Schema — Tri-Graph Ontology (G_deriv/G_sem/L_event, EdgeOntologyRegistry, LCIw/RNIw metrics) |
| `TDD-HORO-v3.0/01_DATA_CONTRACTS/grammar/horo_rule_dsl.ebnf` | EBNF Grammar — Horo Rule DSL (5-stage epistemic chain, 30+ production rules) |
| `TDD-HORO-v3.0/02_ENGINE_INTERFACES/README.md` | Placeholder — Sprint TODO |
| `TDD-HORO-v3.0/03_STORAGE_AND_EVENT_SOURCING/README.md` | Placeholder — Sprint TODO |
| `TDD-HORO-v3.0/04_TEST_PLANES_AND_ACCEPTANCE/plane_A_astronomy_golden_vectors.json` | 6 JPL DE440 golden test vectors |
| `TDD-HORO-v3.0/04_TEST_PLANES_AND_ACCEPTANCE/plane_B_tradition_conformance_cases.json` | 7 canonical conformance cases (BaZi/ZiWei/QiMen/DaLiuRen/XuanKong) |
| `TDD-HORO-v3.0/04_TEST_PLANES_AND_ACCEPTANCE/plane_C_adversarial_conflict_cases.json` | 5 adversarial/inversion attack cases |
| `TDD-HORO-v3.0/04_TEST_PLANES_AND_ACCEPTANCE/plane_D_empirical_isolation_policy.md` | Observational Data Firewall Policy (Rules D-1 through D-5) |
| `TDD-HORO-v3.0/tests/test_data_contracts.py` | 69 pytest tests — 69/69 PASSED |

### Gate Evidence
- pytest: **69/69 PASSED** in 0.03s
- Secret scan: **0 leaks**
- Ecosystem check: **[OK] All sync**
- Git commit: `7e6cbe7`
- Git tag: `v3.0-data-contracts`

### Next Sprint (Sprint 2 — COMPLETED ✅)
- `TICKET-HORO30-005`: Implement FSM `constraint_state_machine.json` in `02_ENGINE_INTERFACES/` — ✅ DONE
- `TICKET-HORO30-006`: Implement `dynamic_arbitration.json` policies — ✅ DONE
- `TICKET-HORO30-007`: Implement `audit_policy_truth_table.csv` in `02_ENGINE_INTERFACES/matrices/` — ✅ DONE
- `TICKET-HORO30-008`: Implement pytest suite `test_engine_interfaces.py` (22 tests) — ✅ DONE

---

## 🚀 SPRINT 2: Horo Architecture v3.0 — Engine Interfaces — 2026-08-24
**Grill Gate Status**: ✅ APPROVED  
**Sprint Tracking Lead**: orchestrator (agy2)  
**Deliverables Status**: ALL 4 TICKETS DONE ✅

| Ticket ID | Assigned Agent | Task Summary | Status | Dependencies |
|---|---|---|---|---|
| `TICKET-HORO30-005` | `agy2` (orchestrator) | สร้าง FSM `constraint_state_machine.json` (4-Tier: H0, H1, H2, H3, 13 states, 18 transitions) | ✅ DONE | TICKET-HORO30-004 |
| `TICKET-HORO30-006` | `agy2` (orchestrator) | สร้าง `dynamic_arbitration.json` (6 intent matrices, 4 arbitration rules ARB-01..04, HITL escalation) | ✅ DONE | TICKET-HORO30-005 |
| `TICKET-HORO30-007` | `agy2` (orchestrator) | สร้าง `audit_policy_truth_table.csv` (7 deterministic rules, 4 verdicts: PASS, WARN, RECOMPUTE, ESCALATE) | ✅ DONE | TICKET-HORO30-006 |
| `TICKET-HORO30-008` | `agy2` (orchestrator) | สร้าง `test_engine_interfaces.py` (22 tests) + Full Suite (91 tests total, 100% PASS) | ✅ DONE | TICKET-HORO30-007 |

### Sprint 2 Deliverables — All DONE ✅

| File | Description |
|---|---|
| `TDD-HORO-v3.0/02_ENGINE_INTERFACES/fsm/constraint_state_machine.json` | 4-Tier Constraint FSM (H0, H1, H2, H3, 13 states, 18 transitions, recovery loops) |
| `TDD-HORO-v3.0/02_ENGINE_INTERFACES/policies/dynamic_arbitration.json` | Dynamic Arbitration Matrix across 6 user intent categories, rules ARB-01..04, HITL criteria |
| `TDD-HORO-v3.0/02_ENGINE_INTERFACES/matrices/audit_policy_truth_table.csv` | Deterministic L6 Audit verdict lookup table (7 rules, 4 output verdicts) |
| `TDD-HORO-v3.0/02_ENGINE_INTERFACES/README.md` | Complete architectural documentation for 02_ENGINE_INTERFACES module |
| `TDD-HORO-v3.0/tests/test_engine_interfaces.py` | 22 pytest tests validating FSM, dynamic arbitration, and audit truth table |

### Quality & Safety Gate Evidence
- pytest: **91/91 PASSED** across full `TDD-HORO-v3.0/tests/` suite (0.06s)
- Secret scan: **0 leaks**
- Ecosystem check: **[OK] All sync (Antigravity & Codex 100%)**

### Next Sprint (Sprint 3 — COMPLETED ✅)
- `TICKET-HORO30-009`: Implement Neo4j Cypher schema `semantic_graph_schema.cql` — ✅ DONE
- `TICKET-HORO30-010`: Implement Derivation DAG Merkle provenance spec `derivation_dag_immutability.md` — ✅ DONE
- `TICKET-HORO30-011`: Implement Append-Only Event Ledger streaming spec `event_ledger_stream.md` — ✅ DONE
- `TICKET-HORO30-012`: Implement pytest / schema tests for storage & event sourcing (`test_storage_and_event_sourcing.py`, 14 tests) — ✅ DONE

---

## 🚀 SPRINT 3: Horo Architecture v3.0 — Storage & Event Sourcing — 2026-08-24
**Grill Gate Status**: ✅ APPROVED  
**Sprint Tracking Lead**: orchestrator (agy2)  
**Deliverables Status**: ALL 4 TICKETS DONE ✅

| Ticket ID | Assigned Agent | Task Summary | Status | Dependencies |
|---|---|---|---|---|
| `TICKET-HORO30-009` | `agy2` (orchestrator) | สร้าง Neo4j Cypher schema `semantic_graph_schema.cql` (Constraints, Indexes, Traversal queries) | ✅ DONE | TICKET-HORO30-008 |
| `TICKET-HORO30-010` | `agy2` (orchestrator) | สร้าง Merkle DAG specification `derivation_dag_immutability.md` (Acyclicity, JCS Hash Formula, R0..R4 Tiers) | ✅ DONE | TICKET-HORO30-009 |
| `TICKET-HORO30-011` | `agy2` (orchestrator) | สร้าง Event Ledger stream spec `event_ledger_stream.md` (17 canonical events, Hash chaining, Redis/Kafka) | ✅ DONE | TICKET-HORO30-010 |
| `TICKET-HORO30-012` | `agy2` (orchestrator) | สร้าง `test_storage_and_event_sourcing.py` (14 tests) + Full Suite (105 tests total, 100% PASS) | ✅ DONE | TICKET-HORO30-011 |

### Sprint 3 Deliverables — All DONE ✅

| File | Description |
|---|---|
| `TDD-HORO-v3.0/03_STORAGE_AND_EVENT_SOURCING/cypher/semantic_graph_schema.cql` | Neo4j Cypher constraints, indexes, relationship ontology, and stored traversal/audit queries |
| `TDD-HORO-v3.0/03_STORAGE_AND_EVENT_SOURCING/specs/derivation_dag_immutability.md` | Derivation DAG Merkle hash formula, topological insertion guard, and R0..R4 verification spec |
| `TDD-HORO-v3.0/03_STORAGE_AND_EVENT_SOURCING/specs/event_ledger_stream.md` | Append-Only Event Ledger streaming spec, 17 FSM event types, hash chaining recurrence & replay |
| `TDD-HORO-v3.0/03_STORAGE_AND_EVENT_SOURCING/README.md` | Complete architectural documentation for 03_STORAGE_AND_EVENT_SOURCING module |
| `TDD-HORO-v3.0/tests/test_storage_and_event_sourcing.py` | 14 pytest tests validating Cypher schema, Merkle DAG algorithms, and Event Ledger chaining |

### Quality & Safety Gate Evidence
- pytest: **105/105 PASSED** across full `TDD-HORO-v3.0/tests/` suite (0.07s)
- Secret scan: **0 leaks**
- Ecosystem check: **[OK] All sync (Antigravity & Codex 100%)**

### Next Phase: Production Agent Prompts & Runtime Adapters (Sprint 4 — COMPLETED ✅)
- `TICKET-HORO30-013`: Implement specialized prompt templates for 10 tradition domain nodes (L3/L4) — ✅ DONE
- `TICKET-HORO30-014`: Implement Consensus Engine (L5), Audit Node (L6), and Plan Composer (L7) runtime wrappers — ✅ DONE
- `TICKET-HORO30-015`: Integrate Test Plane validation suite into CI/CD regression pipeline (`test_test_planes_execution.py`) — ✅ DONE

---

## 🚀 SPRINT 4: Horo Architecture v3.0 — Agent Prompts, Runtimes & Test Planes — 2026-08-24
**Grill Gate Status**: ✅ APPROVED  
**Sprint Tracking Lead**: orchestrator (agy2)  
**Deliverables Status**: ALL TICKETS DONE ✅

| Ticket ID | Assigned Agent | Task Summary | Status | Dependencies |
|---|---|---|---|---|
| `TICKET-HORO30-013` | `agy2` (orchestrator) | สร้าง 10 Production Prompt Templates (L3/L4: BaZi, ZiWei, FengShui, BuShi, QiMen, DaLiuRen, TaiYi, QiZheng, MianXiang, ZeJi) | ✅ DONE | TICKET-HORO30-012 |
| `TICKET-HORO30-014` | `agy2` (orchestrator) | สร้าง L3–L7 Runtime Adapters (`ClaimValidator`, `ConsensusEngine`, `AuditNode`, `PlanComposer`) | ✅ DONE | TICKET-HORO30-013 |
| `TICKET-HORO30-015` | `agy2` (orchestrator) | สร้าง `test_agent_prompts_and_runtimes.py` (28 tests) + `test_test_planes_execution.py` (7 tests) + Full Suite (**140 tests total, 100% PASS**) | ✅ DONE | TICKET-HORO30-014 |

### Sprint 4 Deliverables — All DONE ✅

| File | Description |
|---|---|
| `TDD-HORO-v3.0/05_AGENT_PROMPTS_AND_RUNTIMES/prompts/*.json` | 10 specialized agent prompt templates enforcing domain firewalls, 5-stage epistemic chains, and Claim Emission schema |
| `TDD-HORO-v3.0/05_AGENT_PROMPTS_AND_RUNTIMES/runtimes/claim_validator.py` | L3/L4 Claim Validator runtime enforcing schema conformance and domain firewall checks |
| `TDD-HORO-v3.0/05_AGENT_PROMPTS_AND_RUNTIMES/runtimes/consensus_engine.py` | L5 Consensus Engine runtime executing dynamic arbitration (ARB-01..03) and Tier H2 veto filtering |
| `TDD-HORO-v3.0/05_AGENT_PROMPTS_AND_RUNTIMES/runtimes/audit_node.py` | L6 Audit Node runtime computing LCIw/RNIw, echo chamber detection, and truth table verdict lookup |
| `TDD-HORO-v3.0/05_AGENT_PROMPTS_AND_RUNTIMES/runtimes/plan_composer.py` | L7 Plan Composer synthesizing user reports and enforcing mandatory Epistemic Disclaimer verbatim |
| `TDD-HORO-v3.0/05_AGENT_PROMPTS_AND_RUNTIMES/README.md` | Architecture documentation for prompts and runtime adapters |
| `TDD-HORO-v3.0/tests/test_agent_prompts_and_runtimes.py` | 28 pytest tests validating all 10 prompt templates and L3–L7 runtime engines |
| `TDD-HORO-v3.0/tests/test_test_planes_execution.py` | 7 pytest tests executing validation across Test Planes A, B, C (Adversarial attacks), and D |

### Master Verification & Quality Gate Evidence
- 🧪 **Full Pytest Suite**: **140/140 PASSED** in 0.09s across all 5 test files
- 🔐 **Secret Scan**: **0 leaks** (1,694 files scanned via Rust Rayon)
- 🔄 **AI Agent Ecosystem Sync**: **[OK] All sync (Antigravity & Codex 100%)**
- 🏛️ **Architecture Compliance**: Horo Architecture v3.0 Frozen Baseline 100% Bootstrap Complete

---

## 🤖 Multi-Agent Execution & Delegation Evidence (2026-08-24)
- **`codex2` (Account 2, OpenAI Plus, `gpt-5.6-luna`)**:
  - **Task D1 (Telegram Dirty Files)**: 11 unit tests passed (`test_telegram_bot.py`), scoped commit created (`2638d84`).
  - **Task D2 (Quality Gate & Security Scan)**: 1,694 files scanned (0 leaks), 4-stage strict quality gate 100% passed, ecosystem sync passed.
  - **Task D3 (Playwright Smoke Verification)**: Location search verified passing (`BTN-PROD-01` PASSED), triage report generated in `project/tests/prod_button_regression_report.json`.
  - **Quota Offloading**: 96,313 tokens offloaded to OpenAI Plus account (`task-284` + `task-323`).

- **`agy1` (Account 1, Gemini 3.7 Flash Low — Replaced `codex1` for Lane 2)**:
  - **Task Q2 (Live Canonical Health Probes)**:
    - Vercel: 3/3 checks PASSED (Static UI 200, Docker Backend 200, Deterministic API 200) $\rightarrow$ `project/tests/vercel_reprobe_2026-08-24.json`
    - HF Canonical: 3/3 checks PASSED (Static UI 200, Docker Backend 200, Deterministic API 200) $\rightarrow$ `project/tests/hf_canonical_reprobe_2026-08-24.json`
  - **Task Q3 (Doppler Dry-Run)**: 50+ production secrets validated & categorized.
  - **Task Q4 (Ecosystem Check)**: 100% synchronized across all platform definitions.
  - **Quota Efficiency**: Executed via high-efficiency Gemini Flash Low model, saving Claude/GPT quotas.

- **`codex1` (Account 1, OpenAI Pro Lite `longteskondu45@gmail.com`, 93% Quota)**:
  - **Task Q-V3-01 (Full Cross-Suite Regression & Security Audit)**:
    - `TDD-HORO-v3.0/tests/`: 140/140 PASSED (100%)
    - `Secret Scan`: 0 leaks found across 1,696 files (Rust Rayon)
    - `UI & API Button Regression`: 33/33 PASSED (100%)
    - `Ecosystem Sync`: 100% synchronized
  - **Quota Offloading**: 25,850 tokens offloaded to OpenAI Pro Lite account.

---

## 🚀 PHASE 2: Core Deterministic Engine Adapter (2026-08-24)
**Lead Developer**: `codex2` (OpenAI Plus, `gpt-5.6-luna`)  
**Lead QA Auditor**: `codex1` (OpenAI Pro Lite, `gpt-5.6-luna`)  
**Status**: ✅ COMPLETED (Commit: `2ce8a43`)

| Ticket ID | Assigned Agent | Task Summary | Status |
|---|---|---|---|
| `TICKET-HORO30-016` | `codex2` (Developer) | สร้าง `project/core/v3_engine_adapter.py` (BaZi, ZiWei, QiMen, ZeJi adapters $\rightarrow$ `claim_emission_v3.0.json`) + `project/tests/test_v3_engine_adapter.py` (9 tests, 100% PASS) | ✅ DONE |
| `TICKET-HORO30-017` | `codex1` (QA) | Full Cross-Suite Regression & 33 UI/API Button Contracts Verification (100% PASS) | ✅ DONE |
| `TICKET-HORO30-018` | `codex2` (Dev) / `codex1` (QA) | สร้าง `project/routers/v3.py` (POST /calculate, GET /health, GET /schema, POST /audit) + `project/tests/test_v3_router.py` (13 tests total, 100% PASS, Commit: `06d787b`) | ✅ DONE |
| `TICKET-HORO30-019` | `codex1` (High Thinking) | เพิ่มเติม Domain Adapters ครบ 10 สำนักวิชา (XuanKong, DaLiuRen, LiuYao, TaiYi, QiZheng, MianXiang) + 10-engine pipeline router + 25 contract tests (Commit: `5339e1a`) | ✅ DONE |
| `TICKET-HORO30-020` | `codex1` (High Thinking) | พัฒนา `rust_core/src/v3_merkle_dag.rs` (SHA-256 Merkle Hashing & BFS Acyclicity Cycle Guard, `cargo test` 40/40 tests PASS, Commit: `3eb0add`) | ✅ DONE |
| `TICKET-HORO30-021` | `agy1` (UX/UI Design) | พัฒนา `project/static/v3_tokens.css` (Five Elements Semantic Color System, WCAG 2.1 AA Compliant Dark/Light Themes, Claim Card components, Commit: `3eb0add`) | ✅ DONE |
| `TICKET-HORO30-023` | `agy1` (UI Frontend) | พัฒนา `renderHoroV3Results()` ใน `project/static/app.js` & `public/app.js` แสดงผล 10 Claim Cards และ Epistemic Disclaimer Banner (Commit: `b264fb3`) | ✅ DONE |
| `TICKET-HORO30-024` | `codex1` (High Thinking) | พัฒนา PyO3 Bindings (`compute_merkle_node_hash_py`, `check_reachability_py`) ใน `rust_core/src/lib.rs` & `v3_engine_adapter.py` (24 tests PASS, Commit: `9e87014`) | ✅ DONE |
| `TICKET-HORO30-025` | `codex1` (High Thinking) | พัฒนา `project/tests/test_v3_prompt_benchmarks.py` ตรวจสอบ Golden Prompts 10 สำนักวิชา & Domain Firewalls (4 tests PASS, Commit: `b264fb3`) | ✅ DONE |
| `TICKET-HORO30-026` | `codex2` (Dev) | พัฒนา Prometheus Metrics สำหรับ Horo v3.0 ใน `project/core/observability.py` & `test_v3_observability.py` (3 tests PASS, Commit: `b264fb3`) | ✅ DONE |
| `TICKET-HORO30-027` | `codex1` (High Thinking) | พัฒนา `scripts/run_v3_e2e_consultation.py` & `test_v3_e2e_consultation.py` รัน 5 Synthetic Consultation Profiles (5/5 PASS, Commit: `cf27dbd`) | ✅ DONE |
| `TICKET-HORO30-028` | `agy1` (Docs) | พัฒนา `docs/v3_api_specification.md` (Full OpenAPI & Epistemic Derivation Specification, Commit: `cf27dbd`) | ✅ DONE |
| `TICKET-HORO30-029` | `codex2` (Dev) | พัฒนา `scripts/v3_diagnostic_cli.py` & `test_v3_diagnostic_cli.py` (Interactive Terminal CLI with Tri-Graph Output, 3 tests PASS, Commit: `cf27dbd`) | ✅ DONE |
| `TICKET-HORO30-030` | `codex1` (High Thinking) / `codex2` (DevOps) | แก้ไข Docker build contexts (`Dockerfile.hf`, `Dockerfile`), เพิ่ม `TDD-HORO-v3.0` ใน `publish_space_hf.py` และ dynamic runtime discovery ใน `v3.py` ป้องกัน `RUNTIME_ERROR` บน Hugging Face Space (Commit: `e52bafd`) | ✅ DONE |

---

## 💎 Cumulative Multi-Agent Token Savings Matrix
- **`codex1` (OpenAI Pro Lite, `gpt-5.6-luna` — High Thinking Priority)**: **375,381 tokens** offloaded across QA Verification, 10 Domain Adapters, Rust Merkle DAG, PyO3 Bindings, Prompt Benchmarks, E2E Consultation, and HF Docker Build Remediation (`task-667`).
- **`codex2` (OpenAI Plus, `gpt-5.6-luna` — Heavy Implementation)**: **291,356 tokens** offloaded across Tasks D1..D3, Engine Adapters, v3 Router, Observability Metrics, Diagnostic CLI, and Channel Auditing (`task-671`).
- **`agy1` (Antigravity Account 1, `Gemini 3.7 Flash Low`)**: 100% of Documentation Sync, Doppler Dry-run, Live Health Probes, Web Color Tokens, Frontend UI Visualizer, and Technical API Specs.
- **`agy2` (Orchestrator Session)**: **Zero heavy code-writing overhead**, pure orchestration & review mode.
- **Total Multi-Agent Tokens Offloaded**: **666,737+ tokens** (100% Zero-cost to this Antigravity session).

---

## 🚀 SPRINT: Production UI Visual Integrity — Horo v3.0 Consensus Engine — 2026-08-24
**Grill Gate Status**: ✅ APPROVED (Ref: `plans/plan.md`)
**Sprint Tracking Lead**: root orchestrator
**External Gate**: Production deployment is not authorized in this sprint; local fixes and read-only Production verification only.

| Ticket ID | Assigned Agent | Task Summary | Status | Dependencies |
|---|---|---|---|---|
| `TICKET-V3UI-001` | `orchestrator` | Baseline Production inspection, acceptance matrix, screenshot/version evidence | DONE | None |
| `TICKET-V3UI-002` | `ux_ui_designer` | WCAG/color/typography/spacing and hierarchy audit | DONE | `TICKET-V3UI-001` |
| `TICKET-V3UI-003` | `developer` | Implement isolated v3 responsive/layout/contrast remediation | DONE | `TICKET-V3UI-001` |
| `TICKET-V3UI-004` | `ui_visual_tester` | Add selected-v3 scenario, contrast/overflow/collision checks, and five-viewport captures | DONE | `TICKET-V3UI-001` |
| `TICKET-V3UI-005` | `qa_tester` / `orchestrator` | Run targeted/full regression, compare before/after, and triage console/network failures | DONE | `TICKET-V3UI-003`, `TICKET-V3UI-004` |
| `TICKET-V3UI-006` | `orchestrator` / `code_reviewer` | Historical `6c351ba` release baseline: lesson learned, sync docs, and safety review | DONE — HISTORICAL BASELINE ONLY | `TICKET-V3UI-005` |
| `TICKET-V3UI-007` | `orchestrator` / `business_analyst` / `devops` / `qa_tester` / `code_reviewer` | Release the current `c9f9161` candidate through user-authorized `release_source_commit` provenance, fail-closed local, evidence, HITL, publish, and post-deploy gates | DOING — BLOCKED ON GATES / HITL | `TICKET-V3UI-006` |

### TICKET-V3UI-001 | `orchestrator` | [STATUS: DONE]
**Priority**: CRITICAL
**Ownership**: browser evidence, `plans/plan.md`, `PROJECT_TASKS.md`, `.agents/LESSONS_LEARNED.md`
**Definition of Done**: v3 tab selected in Production; reference and live evidence captured; exact viewport/contrast/collision acceptance criteria recorded; release/version drift documented.

### TICKET-V3UI-002 | `ux_ui_designer` | [STATUS: DONE]
**Priority**: HIGH
**Ownership**: read-only review of Production evidence, `project/static/v3_tokens.css`, v3 markup in `project/static/app.js`
**Boundaries**: no file edits; no deployment; no calculation/copy changes.
**Definition of Done**: concise defect list with severity, offending selector/token, measured or reproducible evidence, and implementation-ready remediation covering light/dark, color-blind, and long multilingual content.

### TICKET-V3UI-003 | `developer` | [STATUS: DONE]
**Priority**: CRITICAL
**Ownership**: `project/static/v3_tokens.css` and only the v3 presentation block of `project/static/app.js` if CSS alone is insufficient
**Boundaries**: do not edit audit scripts/tests/docs, backend routes, computation logic, public payloads, or deploy files.
**Definition of Done**: targeted patch removes identified overflow/clipping/collision/contrast risks at all five viewports; inline styles are minimized only where required; targeted frontend tests pass.

### TICKET-V3UI-004 | `ui_visual_tester` | [STATUS: DONE]
**Priority**: CRITICAL
**Ownership**: `scripts/run_visual_layout_audit.py`, `project/tests/test_visual_layout_audit.py`, generated `project/tests/screenshots/visual_audit/**`, and `project/tests/artifacts/visual_layout_report.json`
**Boundaries**: do not edit production frontend source or governance docs; do not publish/deploy.
**Definition of Done**: selected-v3 populated scenario is deterministic; five canonical viewports captured; horizontal overflow, unintended overlap, clipping, and WCAG contrast results are present in JSON; targeted audit tests pass.

**Evidence**: deployed remote `v3-consensus` scenario ran at five canonical viewports; exact tab selected, 10 populated claims each, HTTP 200, `LAYOUT_PASS`, zero overflow/overlap/out-of-bounds/clipping/contrast failures. The current `visual_layout_report.json` is `PASSED` 5/5. Its 30 automated gradient indeterminates were closed by the documented manual screenshot review; unresolved indeterminates block release under Rule 16.

### TICKET-V3UI-005 | `qa_tester` / `orchestrator` | [STATUS: DONE]
**Priority**: CRITICAL
**Ownership**: read-only verification and generated test reports
**Definition of Done**: targeted tests, button regression, visual suite, console-error audit, `git diff --check`, and full pytest proportional to change pass; failures include concise selector/file/error evidence.

**Evidence**: visual-audit and mirrored-asset tests 13/13 passed; governance/frontend regression tests 26 passed and 5 skipped; button regression passed all controls; JavaScript syntax, `git diff --check`, fixture cleanliness, and ecosystem sync passed. Full pytest passes `792 passed, 9 skipped, 12 warnings`; code reviewer returns `READY_FOR_PROD`, with secret/Kaggle/notebook audits passed and `0` leaks. Post-deploy visual QA is 5/5 exact-tab PASS with zero layout failures.

**Telegram QA remediation**: `TelegramBotController` now resolves the default `TELEGRAM_CHAT_ID` at request time while preserving explicit constructor overrides. The notifier unit contract clears external credentials before asserting formatting, preventing real DNS/network calls. Focused Telegram/config/security tests pass `16 passed` and the prior three full-suite failures are closed.

### TICKET-V3UI-006 | `orchestrator` / `code_reviewer` | [STATUS: DONE — HISTORICAL BASELINE ONLY]
**Priority**: HIGH
**Ownership**: lesson/task/plan evidence and read-only safety review
**Definition of Done**: historical 5-Whys/root cause, prevention protocol, regression guard, artifact links, residual risks, deployed `6c351ba` SHA/HITL action, and `python3 scripts/sync_ai_agent_ecosystem.py --check` result are recorded. It is not evidence for a later candidate.

**Historical evidence only**: secret scan passed with 0 leaks; comprehensive review passed 801 tests with 0 secret/CUDA issues; publisher patch tests 5/5 passed; authorized publish completed with HTTP 200 commits; source version `1.0.0.6c351ba`, HF revision `f8aaa24ed36248c957ff35b405c3056626b28fc7`, runtime `RUNNING`. Its report, screenshot hashes, and manual review are bound to that release. Any changed source version, regenerated report, screenshot, or different HF revision requires `TICKET-V3UI-007` to repeat the applicable gates and obtain a new sign-off.

### TICKET-V3UI-007 | Current `c9f9161` HF Static Release | [STATUS: DOING — BLOCKED ON GATES / HITL]

**Sole authority**: this ticket is the only release checklist for local candidate `1.0.0.c9f9161` / `c9f9161`. Historical `TICKET-V3UI-006`, source `6c351ba`, HF revision `f8aaa24ed36248c957ff35b405c3056626b28fc7`, and their artifacts are baseline context only; none may close a row below.

**Scope**: release-affecting files deliberately selected from the current dirty worktree, including mirrored Static assets and their tests/reports only after ownership review. **Out of scope**: unrelated dirty data/RAG/HITL files, secret access or mutation, infrastructure changes, generated agent definitions, and any unapproved production mutation. **User-authorized identity decision**: immutable `release_source_commit` identifies the deployed payload; the later `packaging_commit` is evidence-only. The packaging commit must not replace the source identity on version surfaces, and no legacy commit/version/metadata fallback or override is permitted.

**Current evidence gate (open)**: `project/tests/artifacts/visual_layout_report.json` was regenerated at `2026-08-25T07:13:49Z` (SHA-256 `807d2609ca53da995bb9c1f89c565a67d867f91855a758dd139470adba9422c0`) and reports 30 gradient indeterminates. The historical post-deploy artifact records a different report hash (`083631501d9129574928fd1af8e386e706f1f20d407068adb5c4a22846bb2f68`) for `6c351ba`; therefore the historical manual review is invalid for this candidate under Rule 16.

**Required release checklist**:

- [ ] Confirm the exact release-file allowlist, exclude unrelated dirty files, and record the intended candidate version plus immutable `release_source_commit` after review.
- [ ] Commit source metadata that names its path, SHA-256 digest, version, immutable `release_source_commit`, and source revision. Do not permit a legacy fallback, environment variable, CLI default, runtime `HEAD`, or external override to replace it.
- [ ] Verify `project/static/**` and `public/**` mirrored release surfaces, including version, HTML, app, and service-worker references, are coherent for the intended commit.
- [ ] Run and archive proportional local QA, publisher regression, visual-audit regression, JavaScript syntax/parity checks, `git diff --check`, secret/safety review, and `python3 scripts/sync_ai_agent_ecosystem.py --check`; stop on the first red result.
- [ ] Capture a fresh five-viewport `v3-consensus` report and the five screenshots, record their SHA-256 values, and bind them to the immutable `release_source_commit` and timestamp.
- [ ] Resolve every automated gradient indeterminate with a new reviewer record per viewport: six findings each (30 total), report/screenshot hashes, reviewer, timestamp, visual basis, and explicit PASS or FAIL. A regenerated artifact invalidates this row.
- [ ] Obtain explicit HITL authorization before staging, selective commit, push, or publish. This ticket does not itself authorize any of those operations.
- [ ] After authorization, selectively stage only the reviewed allowlist, create and record the later `packaging_commit`, then push it; do not include unrelated dirty files. Record both identities in evidence and prove `release_source_commit` is an ancestor of `packaging_commit`.
- [ ] Publish the payload identified by `release_source_commit` to the HF Static Space, run SDK-aware Static health and exact-version verification, and save the resulting target, revision, version, both commit identities, source-metadata path/digest, and asset-parity evidence.
- [ ] Re-capture the five production viewports after publish; verify report/screenshot hashes and all version surfaces correspond exactly once to `release_source_commit`, while the evidence records the later `packaging_commit`; repeat manual gradient sign-off for the post-deploy artifacts.
- [ ] Code reviewer records a fresh fail-closed `READY_FOR_PROD` verdict only after every row above is green; orchestrator then updates the board/plan with the final evidence or records `[ERROR] BLOCKED`.

**Owners and stop conditions**: `qa_tester` owns local regression and captures; `devops` owns payload/health/version/publish evidence after authorization; `code_reviewer` owns safety and the fail-closed verdict; `business_analyst` owns evidence/ticket synchronization; `orchestrator` owns allowlist, dispatch, HITL request, and final decision. Stop and return the first failing gate to its owner. After three failed remediation cycles or any missing authorization, return `NEEDS_HITL`; never infer a pass from the historical baseline.

### Sprint Evidence & Release Decision

- Production baseline: `project/tests/artifacts/production_v3_visual_baseline_2026-08-24.json` and five selected-tab screenshots under `project/tests/screenshots/visual_audit/production_baseline/`.
- Local post-fix evidence: `project/tests/artifacts/v3_visual_post_fix_evidence_2026-08-24.json` and final compact-mobile PASS/TENSION screenshots under `project/tests/screenshots/visual_audit/post_fix/`.
- Confirmed Production risks: fourth tab/descendant clipping on compact mobile, v3-only dark-mode island, sub-AA semantic colors, fixed-height long-content clipping, UI/backend version-label drift, and stale `/index.html` PWA references.
- Release decision: **READY_FOR_PROD**. Authorized deployment and post-deploy verification are complete. The documented final manual screenshot review resolves the 30 automated gradient indeterminates for this release; an indeterminate without equivalent named reviewer sign-off is a blocking risk. The expected static simulation API 404 remains a documented non-blocking Static-SDK behavior.

### Historical Post-Deploy Update — `6c351ba` — 2026-08-25

- Release authorization received and static HF Space published successfully.
- Evidence: `project/tests/artifacts/hf_post_deploy_v3_verification_2026-08-25.json`.
- Remote asset parity: app.js, v3_tokens.css, and sw.js all match local SHA-256 values; version.json reports `1.0.0.6c351ba`.
- Release tooling is now SDK-aware: Static health checks `/` plus production `version.json`; Docker alone checks `/health`.
- Post-redeploy version coherence is PASS: `CURRENT_PAGE_VERSION`, footer, `CLIENT_APP_VERSION`, service-worker cache, and cache-busting query strings all use `1.0.0.6c351ba` / `6c351ba`; no `e432e0d` or composite labels remain.
- Fail-closed release verification requires exactly one matching value/reference on every version surface and rejects missing assets, malformed metadata, network errors, duplicate declarations, stale/composite labels, Docker version mismatches, and CLI mismatches. Publisher suite: `16 passed`; combined publisher and visual-audit regression: `24 passed`.
- Live post-hardening checks: Static health `HEALTHY`; exact version verification `PASSED` for `1.0.0.6c351ba` / `6c351ba`.
- **Historical release state: `6c351ba` was DEPLOYED — READY_FOR_PROD. This does not authorize or verify `TICKET-V3UI-007`.**

### TICKET-HFSTATIC-GOV-001 | Mandatory Release Verification Governance | [STATUS: DONE]

**Priority**: CRITICAL
**Rule / skill**: `.agents/rules/16-hf-static-release-verification.md` and `.agents/skills/hf-static-release-verification/SKILL.md`
**Scope**: make HF Static health, exact-version, publisher regression, visual regression, safety review, and ecosystem synchronization mandatory and fail-closed. No deployment is performed by this governance ticket.

| Work item | Responsible sub-agent | Acceptance evidence | Status |
|---|---|---|---|
| Publisher verifier implementation and regression coverage | `developer` | `python3 -m pytest -q tests/test_publish_space_hf.py` → `16 passed` | DONE |
| Payload, Static health, exact-version and release evidence | `devops` | Dry-run plus `--sdk static --check-health` and `--sdk static --verify-version` exit `0` | DONE |
| Five-viewport visual capture and report | `ui_visual_tester` | `desktop-4k`, `laptop-standard`, `tablet-portrait`, `mobile-ios`, `mobile-compact`; report `PASSED` 5/5 | DONE |
| Independent focused regression | `qa_tester` | Publisher + visual-audit suite → `24 passed` | DONE |
| Secret/safety verdict | `code_reviewer` | No leaks or unresolved red gate; release evidence reviewed | DONE |
| Rule, skill, ticket, plan, and catalog synchronization | `business_analyst` | Paths documented and `sync_ai_agent_ecosystem.py --check` green | DONE |
| Dispatch, retry/HITL control, final decision | `orchestrator` | No `READY_FOR_PROD` until every row is green | DONE |

**RACI**: `orchestrator` is Accountable; the listed sub-agents are Responsible for their rows; `code_reviewer`, `qa_tester`, and `business_analyst` are Consulted on safety, test, and governance evidence; the owner is Informed and becomes the HITL approver when production mutation or a three-cycle unresolved defect requires authorization.

**Mandatory release sequence**:

```bash
python3 -m pytest -q tests/test_publish_space_hf.py
python3 scripts/publish_space_hf.py --space-id pphothidaen/horoconsultant-core-backend --sdk static --dry-run
python3 scripts/publish_space_hf.py --space-id pphothidaen/horoconsultant-core-backend --sdk static --check-health
python3 scripts/publish_space_hf.py --space-id pphothidaen/horoconsultant-core-backend --sdk static --verify-version
python3 scripts/run_visual_layout_audit.py --url https://pphothidaen-horoconsultant-core-backend.static.hf.space --scenario v3-consensus --no-server
python3 -m pytest -q tests/test_publish_space_hf.py project/tests/test_visual_layout_audit.py
python3 -m pytest -q tests/test_hf_release_governance.py
python3 scripts/sync_ai_agent_ecosystem.py --check
```

**Release gate**: no `READY_FOR_PROD` if any command exits non-zero, any required artifact is missing, any version surface is stale/duplicate/composite, any required asset is unreachable, any viewport fails, or any result remains indeterminate. An indeterminate is resolved only by a named manual reviewer recording the current artifact, timestamp, review basis, and explicit pass/fail sign-off. Route failure to the responsible sub-agent; after three failed remediation cycles, stop and escalate to HITL.

**Historical evidence**: publisher `16 passed`; publisher + visual audit `24 passed`; governance contract suite passed in the implementation session (count may evolve with the contract); Static health and exact version green for `1.0.0.6c351ba` / `6c351ba`; visual report `PASSED` 5/5 with screenshots under `project/tests/screenshots/visual_audit/`; automated gradient indeterminates are closed by the documented final manual screenshot review. It cannot close `TICKET-V3UI-007`.

**Manual reviewer sign-off — 2026-08-25**: `root/orchestrator` and `code_reviewer` reviewed `project/tests/artifacts/visual_layout_report.json` plus the current five `*_horo_v3_consensus.png` screenshots. The rendered gradient status text, claim content, controls, and semantic boundaries are readable at every canonical viewport. Decision: **PASS** for the 30 automated gradient indeterminates in these artifacts only; a new capture invalidates this sign-off and requires review again.

### Planning continuation evidence — 2026-08-24

- `python3 scripts/sync_ai_agent_ecosystem.py --check`: PASS; all required platform, governance, Antigravity, and Codex synchronization checks are green.
- Focused v3 engine/router, visual-audit, rendering, and frontend regression suite: `41 passed`.
- Production-version/PWA/report-export regression suite: `11 passed, 5 skipped`; optional-browser skips are retained as environment limitations.
- `node --check project/static/app.js`, `node --check public/app.js`, and `git diff --check`: PASS.
- Planning disposition: `TICKET-META-009` and local QA `TICKET-V3UI-005` are DONE; `TICKET-V3UI-006` remains PARTIAL only for HITL deployment/post-deploy verification; `CP-06-HANDOFF` remains READY for handoff with the browser rerun limitation recorded.
- Full-suite safety review: `READY_FOR_PROD`; secret scan PASS with `0` leaks. Test-generated fixture mutations were restored before this evidence update.
- Final visual evidence review: the light PASS and explicit-dark TENSION post-fix screenshots were inspected and remain readable across the long populated v3 result surface. The tracked `visual_layout_report.json` remains the honest pre-final `WARNING` artifact; the separate post-fix evidence JSON is the authoritative local measurement record.
- No deployment, publish, credential, or secret mutation was performed; the authorized lockfile changes are limited to `uv.lock` and `rust_core/Cargo.lock` and are documented in the ticket above.

---

## 🚀 SPRINT: Pre-QA Receipt-v2 Lanes, Alias Smoke Dispatch, Formal QA & Push — 2026-08-26
**Grill Gate Status**: ✅ APPROVED (Ref: `/plans/plan.md` — GRILL REPORT 2026-08-26T02:14:00+07:00)
**Sprint Tracking Lead**: `orchestrator` (Antigravity / Claude Sonnet 4.6 Thinking)

| Ticket ID | Assigned Agent | Task Summary | Status | Dependencies |
|---|---|---|---|---|
| `TICKET-ORCH-SPRINT-001` | `developer` | Execute 4 serial pre-QA lanes (validator pkg → parser hardening → v2 adoption → v2 AGY condition) | DONE | None |
| `TICKET-ORCH-SPRINT-002` | `qa_tester` | Combined formal QA — 4-suite pytest exit 0 | DONE | `TICKET-ORCH-SPRINT-001` |
| `TICKET-ORCH-SPRINT-003` | `devops` | `git diff --check`, secret scan, ecosystem `--sync`/`--check`, atomic commit + push | DONE | `TICKET-ORCH-SPRINT-002` |
| `TICKET-ORCH-SPRINT-004` | `orchestrator` | HITL-gated `codex1` alias dispatch (RC2-004/attempt-1); chain to `codex2`/`agy1`/`agy2` only on valid receipt | TODO | `TICKET-ORCH-SPRINT-003` |

---

### 🎫 TICKET-ORCH-SPRINT-001 | `developer` | [STATUS: TODO]
**Priority**: HIGH
**Severity**: HIGH
**Work Effort**: M (serial execution of 4 bounded lanes)
**Depends On**: None
**Blocks**: `TICKET-ORCH-SPRINT-002`

#### Lane 1 — Validator Packaging (XS)
- **Owned files**: `pyproject.toml`, `requirements.txt`, `uv.lock`
- **Action**: Declare `jsonschema>=4.23,<5`; regenerate `uv.lock`; no CI workflow, source, schema, or test changes.
- **Acceptance**: `py_compile` on owned files passes; `git diff --name-only HEAD -- pyproject.toml requirements.txt uv.lock` shows only those three files; scoped diff exits 0.

#### Lane 2 — AGY Parser/Evidence Hardening (S)
- **Owned files**: `scripts/multiagent_prompt_command.py` only
- **Action**: Reject duplicate/non-finite JSON; keep failure reasons content-free; redact decoded prompt content; sanitize before finalization/hash/persistence; bind AGY process/session evidence. One sanitized `WorkResult`. No external retry.
- **Acceptance**: `py_compile scripts/multiagent_prompt_command.py` exits 0; scoped diff shows only that file; all lane-2 targeted tests remain green.

#### Lane 3 — Receipt-v2 Policy/Template Adoption (S)
- **Owned files**: `.agents/config/multiagent_model_policy.yaml`, `docs/templates/MULTIAGENT_PROMPT_COMMAND.md`
- **Action**: New governed receipts use canonical v2; v1 remains legacy; `Z` timestamp contract aligned; generated mirrors change only through prescribed sync.
- **Acceptance**: YAML and Markdown parse cleanly; scoped diff shows only those two files; no `.codex/agents/` file hand-edited.

#### Lane 4 — Receipt-v2 AGY Conditional Requirement (XS)
- **Owned files**: `.agents/schemas/multiagent-dispatch-receipt-v2.schema.json` only
- **Action**: Require `process_or_session_id` for `provider: agy`; enforce `Z` timestamp contract; preserve Codex compatibility and receipt-v1.
- **Acceptance**: Schema parses as valid JSON; `jsonschema` Draft 2020-12 metaschema validates; scoped diff shows only that file.

#### Combined Evidence
- All four lanes frozen, `py_compile` per owned file exits 0, scoped diff per lane exits 0, no unowned file changed.

---

### 🎫 TICKET-ORCH-SPRINT-002 | `qa_tester` | [STATUS: TODO]
**Priority**: HIGH
**Severity**: HIGH
**Work Effort**: M
**Depends On**: `TICKET-ORCH-SPRINT-001` (all four lanes DONE)
**Blocks**: `TICKET-ORCH-SPRINT-003`

#### Detailed Instructions
1. Run exact combined formal QA command:
   ```bash
   python3 -m pytest -q tests/test_multiagent_ticket_scheduler.py tests/test_multiagent_prompt_command.py project/tests/test_claude_governance.py tests/test_multiagent_prompt_command_r4.py
   ```
2. Record: exit code, total passed/failed/skipped counts, wall-clock duration.
3. Confirm: no new test file was modified by the QA runner.
4. Trim output to summary line only before reporting to orchestrator.

#### Acceptance Criteria
- [ ] Exit code `0`.
- [ ] Zero test failures (pre-documented expected legacy assertion deltas are allowed only if explicitly named in lane evidence).
- [ ] Scoped diff over test files exits 0 (no test modification by QA runner).

---

### 🎫 TICKET-ORCH-SPRINT-003 | `devops` | [STATUS: TODO]
**Priority**: HIGH
**Severity**: HIGH
**Work Effort**: S
**Depends On**: `TICKET-ORCH-SPRINT-002` (QA DONE)
**Blocks**: `TICKET-ORCH-SPRINT-004`

#### Detailed Instructions
1. **Diff check**: `git diff --check HEAD` — must exit 0.
2. **Secret scan**: `python3 project/core/code_reviewer.py --scan-secrets` — must report 0 leaks.
3. **Ecosystem sync**: `python3 scripts/sync_ai_agent_ecosystem.py --sync` — must exit 0 with `[OK]` for all required checks.
4. **Ecosystem verify**: `python3 scripts/sync_ai_agent_ecosystem.py --check` — must exit 0 with all `[OK]`.
5. **Stage and commit** (excluding `project/api_router.py`, `project/static/version.json`, `project/data/distillation_checklist.json`):
   ```bash
   git add -A
   git reset HEAD project/api_router.py project/static/version.json project/data/distillation_checklist.json
   git commit -m "feat(orchestration): implement pre-QA receipt-v2 lanes, parser hardening, and formal QA verification"
   ```
6. **Push**: `git push origin main` — must complete without error.

#### Acceptance Criteria
- [ ] `git diff --check HEAD` exits 0.
- [ ] Secret scan: 0 leaks.
- [ ] Ecosystem `--sync` + `--check` both exit 0 with all `[OK]`.
- [ ] Commit created with exact message; excluded files not included.
- [ ] `git push origin main` exits 0.
- [ ] `git log --oneline -1` confirms the commit SHA and message.

---

### 🎫 TICKET-ORCH-SPRINT-004 | `orchestrator` | [STATUS: TODO]
**Priority**: HIGH
**Severity**: HIGH
**Work Effort**: S
**Depends On**: `TICKET-ORCH-SPRINT-003` (commit + push DONE)
**Blocks**: None (final gate)

#### Detailed Instructions
1. Verify `TICKET-ORCH-SPRINT-003` push evidence is confirmed.
2. Confirm RC2-004 dispatch prerequisites: focused taxonomy QA (from RC2-004 spec) and read-only isolation review are satisfied or explicitly waived with reason.
3. If prerequisites met: authorize `codex1` read-only CLI lane dispatch, recording as `RC2-004/codex1/attempt-1`.
4. Gate decision on `codex1` result:
   - Valid receipt → record metadata (content-free), authorize bounded `codex2` attempt, and proceed per the RC2-004 chain.
   - Invalid contract / `NEEDS_HITL` → fail closed; record as terminal for this session; do NOT dispatch `codex2`/`agy1`/`agy2`.

#### Acceptance Criteria
- [ ] RC2-004 dispatch prerequisites evaluated and decision recorded.
- [ ] `codex1` attempt result recorded as `RC2-004/codex1/attempt-1` (valid receipt OR typed `NEEDS_HITL`).
- [ ] Gate decision documented in `plans/plan.md` and this ticket.
- [ ] No automatic retry or root-session alias invocation.

<!-- MAREF-C0-SPRINT:START -->
## SPRINT — Multi-agent Control Plane Refactor (`MAREF-000..057`)

**Date**: 2026-08-26 (Asia/Bangkok)
**Tracking lead**: `orchestrator`; C0 documents owned by `business_analyst`
**Grill Gate**: `C0 FREEZE PASS — TWO INDEPENDENT REVIEWS`;
`MAREF-010 READY — NW-SESSION-001 CHILD GRANT REQUIRED`;
`MAREF-011+ BLOCKED`
**Architecture package**: [`docs/architecture/multiagent-control-plane/README.md`](docs/architecture/multiagent-control-plane/README.md)
**Detailed acceptance/evidence/stop authority**: [C0](docs/architecture/multiagent-control-plane/tickets/c0.md), [C1](docs/architecture/multiagent-control-plane/tickets/c1.md), [C2](docs/architecture/multiagent-control-plane/tickets/c2.md), [C3](docs/architecture/multiagent-control-plane/tickets/c3.md), [C4](docs/architecture/multiagent-control-plane/tickets/c4.md), [C5](docs/architecture/multiagent-control-plane/tickets/c5.md)

The current-session Parent Grant covers frozen `MAREF-000..055` in-workspace
mutations only through per-ticket child grants bound to ticket/action/files/
owner/scope digest/max-use/expiry. It expires on new root session, `/clear`, or
app/control-process restart. It excludes MAREF-056, root direct implementation,
external/secret/paid/destructive/Git/deploy/publish/force-bypass actions. An
unchanged authenticated canonical session survives transport reconnect only;
missing proof fails closed.

The new architecture handoff is design input, not execution authorization.
Authority is CP while reads/notifications may be eventual with disclosed
staleness; implementation is modular-monolith-first with one composition root
and no Redis/Kafka/NATS or mandatory internal network hop through C5.

The security/architecture and structural native-review WorkResults both report
`PASS`. The reviewed pre-reconciliation digest set and exact evidence are in
[C0](docs/architecture/multiagent-control-plane/tickets/c0.md): 39 rows/IDs,
100 internal edges, zero cycles/missing dependencies/metadata mismatches/
relative-link failures, nine ADRs and a clean C0 scoped diff. The latest
current-session user message `เริ่ม delegate งาน` authorizes only MAREF-010 and
its exact one-file target
`docs/architecture/multiagent-control-plane/contracts/lifecycle-v1.md`.
Configured route `codex1` was selected but failed closed before alias execution.
Native collaboration is WorkResult evidence; no governed alias/provider receipt
is claimed and MAREF-011+ remains blocked.

The MAREF-010 decision digest is
`cb2cf84444b699a642969e5fb4be43829d39548b87b66531ab8f87fff5b01d6d`;
snapshot digest
`5611f252f987aef0e6f5c54c0d60e19d0aacce2cc110e5ba3d2989a4934fc39b`
is candidate/non-live. Only read-only/high runtime config is approved; mutation
mode does not enforce it, objective text is arbitrary/unbound, and temporary
self-declared approval is prohibited. No alias executed and no lifecycle file
was created.

Current-session native-fallback parent waiver `NW-SESSION-001` covers
`MAREF-010..055` in-workspace native collaboration only when governed alias
execution is unavailable for the same objective/scope-binding/receipt
limitation. Each use still requires a derived one-ticket child with exact
action/path/role/scope digest, `max_uses=1`, current-session expiry, satisfied
dependencies/ownership/Rule18, native WorkResult, scoped diff/evidence and an
independent reviewer `PASS`. Planned child `NW-SESSION-001/MAREF-010/1` is not
issued and is limited to the lifecycle-contract action and exact lifecycle path
with native `business_analyst` `gpt-5.6-sol/xhigh` intent. No execution has
occurred. The waiver accepts no alias/provider ExecutionReceipt for that native
child but waives no other gate.

Approval was recorded at `2026-08-26T12:11:01+07:00` and binds canonical
session `current runtime-enforced collaboration root thread /root`; no opaque
provider/session ID is claimed. Each numbered MAREF-010..055 completion must,
after implementation WorkResult `DONE` and independent reviewer `PASS`, receive
a separate delegated `max_uses=1` local-commit child restricted to that ticket's
reviewed files/hunks. Never commit `BLOCKED`/`NEEDS_HITL` or unrelated dirty
content; root remains orchestrator-only and no push is automatic. This support-
metadata waiver record is not a numbered MAREF completion and receives no
commit.

### Frozen checkpoint registry

Every row's measurable acceptance criteria, required evidence and exact
`DONE`/`BLOCKED`/`NEEDS_HITL` stop condition are mandatory in its linked
detailed register; the compact board row never overrides them.

| Ticket | Severity / Work Effort | Owner | Status | Depends On | Exact ownership |
|---|---|---|---|---|---|
| `MAREF-000-SESSION-SCOPE` | CRITICAL / XS | `business_analyst` | DONE — DOCUMENTATION | none | ADR-004 + MAREF delimited plan/board blocks |
| `MAREF-001-PLATFORM-MATRIX` | HIGH / S | `business_analyst` | DONE — DOCUMENTATION | 000 | platform capability matrix only |
| `MAREF-002-LEDGER-REUSE-ADR` | CRITICAL / XS | `business_analyst` | DONE — DOCUMENTATION | 001 | ADR-005 only |
| `MAREF-003-STORE-TRANSPORT-ADR` | CRITICAL / M | `business_analyst` | DONE — DOCUMENTATION (RECONCILED) | 001,002 | ADR-001/003/007/CAP-001 only |
| `MAREF-004-SECURITY-APPROVAL-ADR` | CRITICAL / M | `business_analyst` | DONE — DOCUMENTATION (RECONCILED) | 000,003 | ADR-002/004/006 only |
| `MAREF-005-SERVICE-BOUNDARY-ADR` | CRITICAL / S | `business_analyst` | DONE — DOCUMENTATION (RECONCILED) | 003,004 | ADR-008 + C0 index/DAG only |
| `MAREF-010-LIFECYCLE-CONTRACT` | CRITICAL / M | `business_analyst` | READY — NW-SESSION-001 CHILD GRANT REQUIRED | 000..005 + two C0 PASS WorkResults; planned child unissued | new lifecycle-v1 contract doc only |
| `MAREF-011-EVENT-ENVELOPE` | CRITICAL / M | `developer` | BLOCKED — 010 | 010 | new event-envelope-v1 schema only |
| `MAREF-012-APPROVAL-GRANT` | CRITICAL / M | `developer` | BLOCKED — 010 | 010 | new approval-grant-v1 schema only |
| `MAREF-013-EFFECT-SAGA-CONTRACTS` | CRITICAL / L | `developer` | BLOCKED — 010 | 010 | new effect-lease + SagaCommand/SagaReceipt schemas only |
| `MAREF-014-COMPATIBILITY-CONTRACT` | HIGH / M | `developer` | BLOCKED — 010 | 011..013 | new capability/loss schemas only |
| `MAREF-015-CONTRACT-QA` | CRITICAL / XL | `qa_tester` | BLOCKED — 011..014 | 011..014 | new control-plane contract tests/fixtures only |
| `MAREF-020-DOMAIN-CORE` | CRITICAL / L | `developer` | BLOCKED — C1 | 015 | new `project/orchestration/domain/**` + `ports/**` only |
| `MAREF-021-POSTGRES-STORE` | CRITICAL / XL | `developer` | BLOCKED — 020 | 020 | new persistence/Postgres+migrations, then sequential `pyproject.toml`/`requirements.txt`/`uv.lock` |
| `MAREF-022-SQLITE-DEV-STORE` | HIGH / M | `developer` | BLOCKED — 020 | 020 | new `adapters/persistence/sqlite.py` only |
| `MAREF-023-COMMAND-HANDLER` | CRITICAL / L | `developer` | BLOCKED — 021,022 | 020..022 | new `application/command_handler.py` only |
| `MAREF-024-LEASE-CAPACITY` | CRITICAL / L | `developer` | BLOCKED — 023 | 021,023 | new application lease/capacity allocators only |
| `MAREF-025-CORE-QA` | CRITICAL / XL | `qa_tester` | BLOCKED — 020..024 | 020..024 | new core/store/concurrency tests only |
| `MAREF-030-NATIVE-ADAPTER` | HIGH / M | `developer` | BLOCKED — C2 | 023,025 | new platform/native adapter only |
| `MAREF-031-CODEX-ADAPTER` | CRITICAL / M | `developer` | BLOCKED — C2 | 014,023,025 | new platform/Codex adapter only |
| `MAREF-032-AGY-ADAPTER` | CRITICAL / M | `developer` | BLOCKED — C2 | 014,023,025 | new platform/AGY adapter only |
| `MAREF-033-DISPATCHER-BRIDGE` | CRITICAL / L | `developer` | BLOCKED — QOBS FREEZE | 024,030..032 + QOBS-DISPATCH/QA | `scripts/multiagent_prompt_command.py` only |
| `MAREF-034-SCHEDULER-BRIDGE` | CRITICAL / L | `developer` | BLOCKED — QOBS FREEZE | 024,033 + QOBS-SCHEDULER/QA | `scripts/multiagent_ticket_scheduler.py` only |
| `MAREF-035-OPENAI-RESPONSES` | HIGH / L | `developer` | BLOCKED — C2/021 MANIFEST FREEZE | 014,021,023,025 | new platform/OpenAI adapter; conditional later dependency-manifest sublane only |
| `MAREF-036-NOTIFICATION-API` | CRITICAL / L | `developer` | BLOCKED — C2 | 021,023,025 | new adapters/API + bootstrap + one bounded `project/main.py` router hunk |
| `MAREF-037-PLATFORM-CONFORMANCE` | CRITICAL / XL | `qa_tester` | BLOCKED — 030..036 | 030..036 | new platform conformance tests/fixtures only |
| `MAREF-040-APPROVAL-SERVICE` | CRITICAL / L | `developer` security lane | BLOCKED — C2/AUTH | 012,021,023,025 + Ticket39 auth | new application approval service only |
| `MAREF-041-EFFECT-SAGA` | CRITICAL / XL | `developer` | BLOCKED — 013,040 | 013,023,024,040 | new application effect Saga/models only |
| `MAREF-042-HITL-INTEGRATION` | CRITICAL / L | `developer` | BLOCKED — TICKET39 | 040,041 + Ticket39/scope audit/QA freeze | `project/hitl_router.py` only |
| `MAREF-043-COMPENSATION-ADAPTERS` | CRITICAL / XL | `developer` | BLOCKED — 041/042 FREEZE | 041,042 | declared external-finetune/vector/training + new adapters/effects |
| `MAREF-044-GOVERNANCE-QA` | CRITICAL / XL | `qa_tester` + read-only reviewer | BLOCKED — 040..043 | 040..043 | new approval/Saga/HITL tests only |
| `MAREF-050-SHADOW-MODE` | CRITICAL / XL | `developer` | BLOCKED — 033/036/C3/C4 | 033,036,037,044 | new orchestration config + migration/shadow + one frozen bootstrap hunk |
| `MAREF-051-LEGACY-IMPORT` | HIGH / L | sequential `developer` / `business_analyst` | BLOCKED — 050 | 050 | exact import/verify/rollback scripts + import/cutover schemas and non-executable templates |
| `MAREF-052-REPLAY-RECONCILE-QA` | CRITICAL / XL | `qa_tester` | BLOCKED — 025,050,051 | 025,050,051 | exact shadow/migration-tool tests + migration fixtures |
| `MAREF-053-LOAD-CAPACITY-QA` | CRITICAL / L | `qa_tester` source; `devops` run-only | BLOCKED — 052 | 024,037,052 | exact load test + five named YAML profiles; content-addressed report only |
| `MAREF-054-GOVERNANCE-SYNC` | HIGH / L | sequential `developer` / `business_analyst` / scoped sync | BLOCKED — REPO-ONLY SYNC + FREEZE | 052,053 | exact scoped-sync tooling/test, rule/Claude rule/skill/evals/catalog/template and one mirror |
| `MAREF-055-SAFETY-REVIEW` | CRITICAL / M | `code_reviewer` | BLOCKED — 054 | 044,052..054 | read-only MAREF changed-file manifest |
| `MAREF-056-PRODUCTION-CUTOVER` | CRITICAL / L | no current owner; fresh-P4 `devops` artifacts only | BLOCKED — FRESH HITL/LATE BINDING | 055 + new target/session approval | content-addressed v1 manifest + backup/deployment/cutover receipts; no live source edit |
| `MAREF-057-POST-CUTOVER` | CRITICAL / L | `qa_tester` verification / separate-fresh-P4 `devops` rollback receipt / read-only `orchestrator` | BLOCKED — 056 + FRESH P4 DRILL | 056 | same cutover directory: versioned verification/rollback receipts only |

### Checkpoint gates and current decision

- C0: `DONE — FREEZE PASS`; independent security/architecture and structural
  review evidence is recorded without releasing C1 execution.
- MAREF-010 is `READY — NW-SESSION-001 CHILD GRANT REQUIRED`; it remains
  non-executable until exact child `NW-SESSION-001/MAREF-010/1` is issued.
  MAREF-011+ is not source/schema execution-eligible. Later lanes still require
  dependencies, ownership,
  QOBS/quota and HITL at their own scheduling checkpoints. Architecture uses
  `gpt-5.6-sol/xhigh`; normal rank-3 implementation/security uses
  `gpt-5.6-sol/high`; static config is intent only.
- PostgreSQL is production canonical authority; SQLite WAL is local/single-host
  only. REST commands + SSE notifications are default. OpenAI Responses WS is
  optional server-side model I/O with mandatory HTTP fallback, never authority.
- P0-P4 apply. `NEEDS_HITL` freezes E2-E4. Automatic/forced training remains
  blocked until the approval service/Saga is implemented and approved.
- MAREF-056/057 have no current execution ownership or concrete argv. Fresh P4
  approval must late-bind exact target/revision/files/commands/digests before
  cutover; MAREF-057 rollback/restoration needs a separate fresh P4 grant. The
  compatibility clock starts only after MAREF-057 acceptance.
- Rule18 record for this metadata-only reconciliation: schema v1,
  `MAREF-005-C0-FREEZE-EVIDENCE`, planning ranks `1/1/1/0/2`, bounded
  `quota_band=unknown`, mutation, configured intent
  `codex1/gpt-5.6-sol/xhigh`, policy `2026-08-26.1`, medium confirmation and
  HITL true. This native WorkResult is not a governed alias ExecutionReceipt.
- MAREF-010 release-metadata Rule18 record: schema v1,
  `ticket=MAREF-010-RELEASE-METADATA`, planning/mutation ranks `1/1/1/0/2`,
  bounded unknown quota, selected `codex1/gpt-5.6-sol/xhigh`, policy
  `2026-08-26.1`, root-medium confirmed and HITL approved. The decision digest
  above validates planning input only; the candidate snapshot is non-live and
  no alias receipt exists.
- `NW-SESSION-001` expires on a new root session, `/clear`, or app/control
  restart and excludes MAREF-056/057, production/external/deploy/publish/Git,
  secret/credential, paid/billing, destructive/history/permission, root
  implementation, out-of-ticket tests and force-bypass actions, except for the
  separately delegated exact post-PASS local commit described above.
  QOBS/MAREF-033 governed binding remains the non-waiver alternative.

<!-- MAREF-C0-SPRINT:END -->
<!-- RELEASE-RECOVERY-20260829:START -->
## Sprint RELEASE-RECOVERY-20260829 — BSA governance recovery

**Status**: `APPROVED` bounded documentation lane. **Ownership**: only
`plans/plan.md` and `PROJECT_TASKS.md`; prepend-only, preserve every unrelated
staged/unstaged change and every historical status below this block.

**Approved nine-dimension scope**: D1 exact ownership and release interfaces;
D2 recovery/provenance delta with no history rewrite; D3 matching markers,
suffix preservation, and `git diff --check` acceptance; D4 required metadata,
source, identity, QA, CI, rollback, and external evidence inputs; D5 one-editor
handoff to QA/reviewer/DevOps and next audit; D6 confirmed owner approval,
eight-path staged set, and capacity facts; D7 stale identity/provenance and
unsafe-claim rollback/HITL risks; D8 bounded read-only evidence and dispatch
budget; D9 no metaphysical-domain change, with human review for release gates.
All nine dimensions are resolved for this lane.

### Execution controls and release gates

- Canonical metadata: `1.0.0.e06b224`; release source: `e06b224`.
- Canonical HF Docker backend: `pphothidaen/horoconsultant-core-backend`.
  Vercel UI verification is separate and mandatory.
- Exact eight currently staged release paths:
  `.github/workflows/hf_backend_deploy.yml`, `HOWTO.md`,
  `docs/RELEASE_HANDOFF_CHECKLIST.md`, `project/tests/test_azure_release.py`,
  `project/tests/test_live_health_verification.py`,
  `project/tests/test_prod_version_e2e_release_identity.py`,
  `scripts/run_live_health_verification.py`,
  `scripts/run_prod_version_e2e.py`.
- Required test-only baseline comes first, with a closed provenance manifest;
  source and test commits remain separated. No source work proceeds before
  baseline verification.
- Gates required: QA regression/API contract, reviewer approval, rollback
  readiness, green CI, backend identity, separately verified Vercel UI, UI E2E,
  and five-viewport visual audit. Local-only checks never justify a release
  claim.
- Capacity checkpoint: `codex1` is `99 percent used`; `codex2` is
  `unauthenticated`; high-risk `gpt-5.6-sol/ultra` review is `BLOCKED` without
  an explicitly approved downgrade.

### Ticket continuity

| Ticket | Severity | Work Effort | Owner | Status | Next action |
|---|---|---|---|---|---|
| `TICKET-META-008` | HIGH | XS | `business_analyst` | `BLOCKED — quota/auth handoff required` | Preserve non-secret continuity status and blockers |
| `RELEASE-RECOVERY-20260829-PROV-AUDIT` | HIGH | S | `business_analyst` | `DONE` | Read-only provenance audit completed: 8 release paths verified, ecosystem sync 100%, 31/31 unit tests passed |
| `RELEASE-RECOVERY-20260829-QA-BASELINE` | HIGH | S | `qa_tester` | `DONE` | Verified test suite: 106 IDQ core tests passed, 221 scheduling/contract tests passed, 515 comprehensive multiagent tests passed, 0 security leaks in 2,178 scanned files |
| `RELEASE-RECOVERY-20260829-GATE-VERIFY` | HIGH | S | `devops` / `qa_tester` | `TODO / next eligible` | Gate 1-3 local verification passed; await Gate 4-5 deployment & live evidence |

**DispatchDecision v1**: digest
`19be80345b3b24fbcfeb795b14e1dac9624d2cbd818f23e3e20400545924d908`; policy
`2026-08-26.1`; alias `codex1`; model `gpt-5.6-luna`; effort `medium`; quota
`below_10_percent`; rank `1`; owner `approved`.

**Stop condition**: `DONE` only after both matching blocks exist, the two
owned files pass `git diff --check`, and no out-of-scope file changed from this
lane. Otherwise `BLOCKED` or `NEEDS_HITL`.
<!-- RELEASE-RECOVERY-20260829:END -->
