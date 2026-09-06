# Context Registry, Approved Ticket, and Resolver Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans task-by-task. Every source step remains blocked until the owner-authorized test-only baseline commit is independently verified.

**Goal:** Freeze literal RED contracts, then implement the canonical registry, approved-ticket authority, evidence validation, and strengthen-only union resolver.

**Architecture:** A code-fixed ticket/lane lookup selects one `ApprovedTicketContextV1`; a strict resolver unions all selectors and validates typed evidence against immutable built-in closures. All JSON identities use the exact canonical algorithm and prefixes in the design.

**Spec:** `docs/superpowers/specs/2026-09-05-atomic-dynamic-cross-provider-context-design.md`

## Normative JSON identity

Every ingress rejects duplicate keys, `NaN`, `Infinity`, `-Infinity`, and any key/string not already Unicode NFC. Canonical bytes are exactly `json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")` with no newline. Domain-separated SHA-256 uses, verbatim: `b"horo-context:scope-skill-registry:v1\0"`, `b"horo-context:approved-ticket-context:v1\0"`, `b"horo-context:scope-skill-manifest:v1\0"`, `b"horo-context:evidence:v1\0"`, and `b"horo-context:capability-index:v1\0"`. Raw artifact hashes cover exact bytes without a prefix. Manifest self-digest removes only `manifest_sha256`, canonicalizes the remaining object, and uses the manifest prefix; the manifest is outside its artifact inventory.

## Frozen QA inventory

The test-only baseline allowlist is exactly:

- `tests/test_context_profile_registry.py`
- `tests/test_context_profile_resolver.py`
- `tests/test_context_profile_native_activation.py`
- `tests/test_context_profile_generation.py`
- `tests/test_context_profile_hierarchy_runtime.py`
- `tests/test_context_profile_budget_handoff.py`
- `tests/test_context_profile_mandatory_closures.py`
- `project/tests/test_context_profile_ecosystem_sync.py`
- `tests/fixtures/context_profiles/registry.valid.json`
- `tests/fixtures/context_profiles/approved-context.valid.json`
- `tests/fixtures/context_profiles/evidence.valid.json`
- `tests/fixtures/context_profiles/narrowing.valid.json`
- `tests/fixtures/context_profiles/expected-root-developer.json`
- `tests/fixtures/context_profiles/expected-multi-path.json`
- `tests/fixtures/context_profiles/expected-mandatory-closures.json`
- `tests/fixtures/context_profiles/codex-prompt.json`
- `tests/fixtures/context_profiles/claude-probe.json`
- `tests/fixtures/context_profiles/agy-probe.json`
- `tests/fixtures/context_profiles/antigravity-render.json`
- `tests/fixtures/context_profiles/evals/qa-regression-provenance.json`
- `tests/fixtures/context_profiles/evals/qa-api-ui-e2e.json`
- `tests/fixtures/context_profiles/evals/five-elements-ui-palette.json`
- `tests/fixtures/context_profiles/evals/wcag-apca-color-audit.json`
- `tests/fixtures/context_profiles/evals/ui-color-token-handoff.json`
- `tests/fixtures/context_profiles/evals/metaphysical-request-router.json`
- `tests/fixtures/context_profiles/evals/metaphysical-hitl-scope-gate.json`
- `tests/fixtures/context_profiles/evals/metaphysical-finetune-handoff.json`
- `tests/fixtures/context_profiles/evals/qa-e2e-testing.json`
- `plans/test_provenance/ticket-context-opt-001.json`

All 29 paths are governed test-only content: eight modules, eleven literal fixtures, nine immutable eval expectation fixtures, and provenance. The nine corresponding real `.agents/skills/<skill>/evals/evals.json` files are E1 source allowlist/manifest inputs, not baseline content. Immutable tests exact-compare each source with its fixture and reject missing, extra, reordered, or weakened cases; fixtures cannot authorize or enable a skill. Required RED includes `test_combined_baseline_paths_are_all_guard_classified_as_tests_or_manifests`, `test_each_skill_eval_matches_its_frozen_test_fixture_exactly`, and `test_eval_fixture_cannot_authorize_or_enable_a_skill`.

Exactly one local QA-owned test/eval-fixture/provenance baseline commit is authorized after assertion-level RED and independent review. It contains exactly 39 paths: the exact 29-path context portion above plus the exact 10-path dispatch portion. No second or other commit and no push is authorized. Every source/config/generated/runtime-evidence change remains uncommitted. `plans/evidence/context-opt-001/skill-pressure-red.json` is a QA-owned durable sanitized receipt bound by its digest in provenance; it is not committed baseline content. At 27% AMBER, deterministic pressure preparation requires a fresh quota reassessment; provider-backed pressure samples remain unauthorized and are recorded as not run.

## Task A: Complete the provenance frame

**Ticket/state:** `TICKET-CONTEXT-OPT-001-A`, `DOING -- DRAFT_REBUILD_REQUIRED`
**Owner/file:** `qa_tester`; only `plans/test_provenance/ticket-context-opt-001.json`

- [ ] Create the currently absent file and record current task-8/17/18/19 authority hashes, current HEAD and complete dirty status including `HANDOFF.md.lock`, separate quota pools, exclusions, the exact 29 context + 10 dispatch future-baseline partition, and every prospective D-F/dispatch source with raw SHA-256 or `ABSENT` plus current owner. Do not claim refreshed/current until QA validates it.
- [ ] Record Task 19's forward ownership release: `TICKET-SKILL-BUDGET-002` is `BLOCKED_NONREPRODUCIBLE / VERIFIED_LOCAL_CODE_CONTRACT / LIVE_CONFIG_DRIFT`; Context F receives exclusive future ownership of `scripts/sync_codex_account_configs.py` only at 23,004 bytes, SHA-256 `4d37513698a48f400e71e0e113c69e073aa9c74e6b2479494c89e76758aaee79`, blob `9d9e9f0f4988a9f58063082b259836b8cb114d96`. No account sync overlaps F; codex3 remediation is a separate sequential operational lane.
- [ ] Set `baseline_state=DRAFT_RED_NOT_COMMITTED`, empty RED runs, `test_owner_role=qa_tester`, `reviewer_role=code_reviewer`, and no source-admission claim.
- [ ] Validate strict JSON and confirm the diff contains only the provenance file. Stop on ownership ambiguity, symlink/non-regular path, account/provider/secret read, or any source/config/generated mutation.

## Task B: Create the complete RED packet

**Ticket/state:** `TICKET-CONTEXT-OPT-001-B`, `BLOCKED_SECURITY_CONTRACT_CORRECTION`
**Admission:** A complete plus independent acceptance of the corrected design/plans/QA handoff. Deterministic local RED is allowed after admission. Host is 27% AMBER; deterministic pressure preparation requires immediate host-pool reassessment, but provider-backed pressure sampling remains unauthorized. The separate codex1 96% observation may support only the reserved read-only security re-audit after documentation freeze, local alias/isolation validation, and receipt-backed dispatch; it is not interchangeable host capacity.
**Owner/files:** `qa_tester`; exactly the 29 baseline paths above plus `plans/evidence/context-opt-001/skill-pressure-red.json`.

- [ ] Create literal fixtures without importing production helpers. Freeze exact role/phase/actions/all paths/Horo requests/domain/risks/command class/exclusions/evidence refs and exact expected normalized sets.
- [ ] Write strict registry/approved-context/evidence tests: closed schemas; three disjoint namespaces; duplicate/non-finite/non-NFC rejection; safe identifiers; missing/cyclic/conflicting references; absent/symlink/escape sources; and immutable closure minimums.
- [ ] Write B1 authority tests. Hash exact UTF-8 marker-bounded context sections for `ticket_sha256`/`plan_sha256`; reject missing/duplicate/nested/reordered markers and stale/non-monotonic revisions. Mutate role, phase, action, path, Horo request, domain, risk, command class, exclusion, digest, revision, lane, or authority path; omit an argv-derived dangerous action; try unmanifested, caller-selected, wrong-fixed-path, wrong-ticket/lane, stale, linked, nonregular, escaped, digest-mismatched, or duplicate context paths; every case fails before child launch. Do not reject solely because the correct D-owned manifest-bound record is Git-untracked. Only action/path/Horo subsets pass; any other change, broadening, or plugin request field fails. Include `test_approved_context_is_code_fixed_manifest_bound_and_not_caller_selected` and `test_git_tracking_state_is_not_authority_or_execution_evidence`.
- [ ] Write B2 evidence tests. Reject caller pass booleans and missing, extra, duplicate, stale, indeterminate, wrong-ticket/domain/revision/owner/reviewer, wrong-schema, symlinked, malformed, non-NFC, or digest-mismatched receipts. Test immutable security/API/release/metaphysics closures member-by-member, including exact metaphysics audit/sign-off and full release-evidence fixtures.
- [ ] Write B3 canonical identity tests with non-ASCII NFC text, non-NFC equivalents, duplicate keys, all non-finite constants, reordered keys, whitespace/newline/locale/mtime/root variance, semantic mutation, all five exact domain prefixes, raw artifact hashing, and manifest self-digest exclusion. Changing schema, role JSON, selected skill/rule, renderer/import, or rendered semantics must fail even if registry digest is unchanged.
- [ ] Write B4 containment/race tests for source/target/parent/deepest-ancestor symlink escape, broken links, FIFO/device/directory, hard link, missing leaf below escaping parent, case collision, unsafe POSIX path, bounded-read overflow, same-buffer hash/parse, device/inode/size/mtime swap, source snapshot drift, extra files inside each managed root, unrelated files outside roots, atomic `0600` temp + fsync + replace, no silent delete/overwrite, and marker missing/duplicate/nested/reordered/outside-byte mutation.
- [ ] Write union tests for root + role + phase + every action + every path and every ancestor + dependencies + closures. Prove duplicate/path order invariance, multi-path union, strengthen-only descendants, stable unknown/escape/conflict reasons, exact four-skill bootstrap, BA-only BSA skill, reviewer least privilege, and no keyword/pass-flag shortcut.
- [ ] Write lifecycle/governance tests before Rules 17/20/21 change: remaining-percentage thresholds, unsafe summary prohibition, canonical ticket/plan then derived handoff, `VERIFIED_LOCAL` not `DONE`, release mandates unchanged, complete handoff lanes, and no release/source-admission from local evidence.
- [ ] Write exact out-of-scope characterization tests for the ten policy files and seven broker/capacity executors named in the spec. Freeze raw hashes plus parsed alias/purpose/capacity semantics; freeze `ACCOUNT_CONFIGS`, alias sets, and external-write behavior in the two shared F scripts. Reject registry account/alias/capacity/quota/model/effort/broker/dispatchability/external-home/wrapper fields and any production application path change.
- [ ] Freeze the nine eval expectation fixtures. Each new skill gets a no-guidance and with-skill case contract; `qa-e2e-testing.json` carries baseline/provenance expectations. The nine real eval files are E1 source allowlist/manifest paths and must exact-match their fixtures. Record provider-backed samples as `BLOCKED_PROVIDER_CALL_NOT_AUTHORIZED`; do not fabricate RED/PASS. Deterministic preparation still requires B admission and fresh AMBER reassessment.
- [ ] Run deterministic RED as five bounded commands: registry alone; resolver plus mandatory closures; native activation alone; generation plus ecosystem integration; hierarchy-runtime plus budget-handoff. Every command is `env PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider` followed by the exact module names in the frozen inventory. Record actual nonzero exit, assertion-level missing-behavior fingerprint, argv, time, owner, and file SHA-256. Fix collection/syntax/fixture/permission errors; do not change expectations to fit implementation.
- [ ] Populate the provenance manifest with exact hashes for all 29 baseline paths and the pressure receipt's domain-separated evidence digest. No source path is staged or mutated.

## Task C: Independent review and one-commit gate

**Ticket/state:** `TICKET-CONTEXT-OPT-001-C`, `BLOCKED_BY_DEPENDENCY`
**Owner sequence:** `code_reviewer` performs independent pre-commit review; `qa_tester` creates exactly one already-authorized combined 39-path test/eval-fixture/provenance commit; `code_reviewer` verifies it read-only.

- [ ] Recheck every prospective source hash/owner from A immediately before review. Any pre-existing drift or unresolved `TICKET-SKILL-BUDGET-002` ownership blocks the affected lane.
- [ ] Verify literal expectations, all B1-B7/containment cases, 29-path allowlist, assertion-level RED, digest algorithm, independent expected values, and zero staged source/config/generated/ticket/plan/evidence-pressure content.
- [ ] The commit gate is required by `qa-e2e-testing`; current Rule 21 does not define it. Once both context and dispatch RED plus pre-commit review pass, QA stages exactly the 29 context paths and exact 10 dispatch paths and creates the sole authorized commit.
- [ ] Reviewer verifies commit index, parent ancestry, hashes, expected RED, and source/test separation. No second commit or push is permitted. Record `TEST_BASELINE_VERIFIED` only after that review.

## Task D: Implement registry, approved context, evidence, and resolver

**Ticket/state:** `TICKET-CONTEXT-OPT-001-D`, blocked until C records `TEST_BASELINE_VERIFIED`
**Owner/files:** `developer`

- Create `.agents/config/scope_skill_registry.v1.json` (non-role sections first; E1 owns later role mappings).
- Create `.agents/schemas/scope-skill-registry-v1.schema.json`.
- Create `.agents/context/tickets/TICKET-CONTEXT-OPT-001.v1.json`.
- Create `.agents/schemas/approved-ticket-context-v1.schema.json`.
- Create `.agents/schemas/evidence-ref-v1.schema.json`.
- Create `scripts/resolve_agent_context.py`.

**Interfaces:**

```python
def canonical_json_bytes(value: object) -> bytes: ...
def domain_sha256(prefix: bytes, value: object) -> str: ...
def load_approved_lane(repo_root: Path, ticket_id: str, lane_id: str, narrowing: NarrowingRequestV1 | None) -> ApprovedLaneContext: ...
def validate_evidence(repo_root: Path, ref: EvidenceRefV1, now: datetime) -> ValidatedEvidence: ...
def resolve_context(registry: ScopeSkillRegistryV1, lane: ApprovedLaneContext, command_argv: tuple[str, ...]) -> ContextResolutionV1: ...
```

- [ ] Implement one strict JSON loader with duplicate/non-finite/NFC rejection and the exact canonical algorithm/prefixes from the spec. Hash and parse one bounded race-checked byte buffer.
- [ ] Implement code-fixed ticket lookup beneath `.agents/context/tickets/`, exact `ticket_id+lane_id`, closed subset narrowing, argv-derived actions, no plugin request field, and strict `EvidenceRefV1` validation.
- [ ] Implement immutable built-in closure minimums, then validate registry additions as strengthen-only. Return stable sanitized codes for missing/weakened gates, unauthorized capability, path/authority drift, stale evidence, and root-policy weakening.
- [ ] Implement union resolution over all selectors/paths/ancestors/dependencies and emit canonical `ContextResolutionV1` with exact namespace sets, normalized scopes, approved-context digest, and no raw evidence/prompt/environment.
- [ ] Run registry/resolver/closure/budget-handoff RED files to GREEN, then relevant existing API/security/release/metaphysics/handoff neighbors. Do not touch frozen tests/evals/fixtures/provenance hashes.
- [ ] Recheck the A source snapshot after GREEN. Any unrelated change blocks handoff to E1.

## Stop conditions

Task B is not admitted by this document alone. Tasks D onward remain blocked without the authorized and independently verified single baseline commit. At the 27% AMBER band, reassess before each pressure sample or bounded dispatch. Stop on stale/ambiguous quota, baseline drift, source ownership collision, alias/capacity/application change, non-pure check, unsafe path/evidence, secret/provider/account action, or any unauthorized commit/push/tag/deploy/publish.
