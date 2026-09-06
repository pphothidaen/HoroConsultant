# Context Provider Rendering and Local Runtime Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans task-by-task. Source work requires `TEST_BASELINE_VERIFIED` first.

**Goal:** Render canonical context one way, enforce a local inspection-only Codex boundary, and produce sanitized Codex/Claude/AGY evidence plus static Antigravity parity.

**Architecture:** The renderer consumes only the strict resolver result and emits a complete source/artifact manifest. Pure checks calculate in memory; native probes are separate Task G effects. All filesystem and subprocess boundaries fail closed.

**Spec:** `docs/superpowers/specs/2026-09-05-atomic-dynamic-cross-provider-context-design.md`

**Current authority:** Task 17 SHA-256 `bbc84f46516b023d1b24d40604319f8688ad4415c679e7d907f8ea91e6b0f176`; task 18 SHA-256 `c7ae2047d2d6bef138f05d20a38227e43d96fdf2630fab83e35c33511ca4f6bd`; task 19 ownership-release SHA-256 `52c191c36b42a8cfefd047e24924fdce34789164896c75a6f1611e4e9c163276`. Exactly one local QA-owned test/eval-fixture/provenance baseline commit is authorized after assertion-level RED and independent review. It contains exactly 39 paths: the exact 29-path context portion plus the exact 10-path dispatch portion. No second or other commit and no push is authorized. Every source/config/generated/runtime-evidence change remains uncommitted.

## Normative JSON identity

Every ingress rejects duplicate keys, `NaN`, `Infinity`, `-Infinity`, and any key/string not already Unicode NFC. Canonical bytes are exactly `json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")` with no newline. Domain-separated SHA-256 uses, verbatim: `b"horo-context:scope-skill-registry:v1\0"`, `b"horo-context:approved-ticket-context:v1\0"`, `b"horo-context:scope-skill-manifest:v1\0"`, `b"horo-context:evidence:v1\0"`, and `b"horo-context:capability-index:v1\0"`. Raw artifact hashes cover exact bytes without a prefix. Manifest self-digest removes only `manifest_sha256`, canonicalizes the remaining object, and uses the manifest prefix; the manifest is outside its artifact inventory.

## Task B provider/security RED requirements

**Owner:** `qa_tester`; files are frozen paths from the registry plan.

- [ ] In `tests/test_context_profile_native_activation.py`, cover B5: malicious PATH and `PYTHONPATH`; caller executable; writable/symlinked executable parent; unsupported version; shell metacharacters; leading global options; second profile; config/cwd/exec/login/search/model/network flags; empty/oversized argv; timeout/signal/oversized streams; token/proxy/provider-home/env canaries; forbidden network/write attempt; and internal fake seam only. Assert only local `debug prompt-input`, absolute pinned executable, literal `shell=False` argv, controlled cwd/limits, minimal environment, `0700` home, `0600` files, and nonzero `UNAVAILABLE`/`UNKNOWN` when isolation is unproved.
- [ ] In the same file, cover B6: exactly one JSON document and JSON Pointer `/0/content/0/text`; wrong/multiple prompt nodes; duplicate/non-finite/non-NFC/trailing JSON; absent/duplicate/nested/escaped/marker-like skills blocks; duplicate/conflicting IDs; control/ellipsis/truncation/warnings on either stream; full canonical/materialized inventory; rogue workspace/global skill; symlink/frontmatter mismatch; cross-namespace collision; plugin/runtime ID in Horo requests; optional plugin request/role binding; descriptor mismatch; and Superpowers-named Horo collision.
- [ ] In `tests/test_context_profile_generation.py` and `project/tests/test_context_profile_ecosystem_sync.py`, cover B3/B4/B7: all five digest prefixes and exact canonical algorithm; complete source/artifact inventory; manifest self-digest; byte/semantic drift; managed-root missing/stale/extra/case collision; source/target/ancestor symlink and hardlink; type/race/snapshot attacks; safe atomic replace; marker safety; and no deletion/overwrite of extra/unowned files.
- [ ] Approved-context tests reject unmanifested, caller-selected, wrong-fixed-path, wrong-ticket/lane, stale, linked, nonregular, escaped, and digest-mismatched records, but do not reject solely because the correct D-owned manifest-bound record is Git-untracked. Include `test_approved_context_is_code_fixed_manifest_bound_and_not_caller_selected` and `test_git_tracking_state_is_not_authority_or_execution_evidence`.
- [ ] Prove pure `sync_ai_agent_ecosystem.py --check` launches no provider/external subprocess, creates no directory/lock/temp, performs no write/chmod/touch/replace/watch, and leaves full temporary repository plus canary home/cache/temp roots identical in names, links, bytes, modes, mtimes, and entries. Raw child output, prompts, env, paths, terminal control, tokens, and emails never enter public errors, receipts, or digest input.
- [ ] In `tests/test_context_profile_hierarchy_runtime.py`, enforce the exact `ProviderContextProbeV1` field allowlist and `PASS|UNAVAILABLE|UNKNOWN` semantics for Codex/Claude/AGY; Antigravity is static-parity only. `UNAVAILABLE` and `UNKNOWN` are nonzero.

Run these RED files separately with bytecode/cache disabled and record assertion-level fingerprints in `plans/test_provenance/ticket-context-opt-001.json`. They do not admit Task F before the owner-authorized baseline commit and post-commit review.

## Task F: Renderer, pure checks, adapter, and probes

**Ticket/state:** `TICKET-CONTEXT-OPT-001-F`, blocked by D, E1, E2, and `TEST_BASELINE_VERIFIED`; task 19 has released the pinned Skill Budget source ownership, but all other dependencies remain closed.
**Owner:** `developer`

**Create exactly:**

- `scripts/render_agent_context_profiles.py`
- `scripts/codex_role.py`
- `scripts/probe_agent_context_runtime.py`

**Modify exactly:**

- `scripts/sync_sdlc_agents.py`
- `scripts/sync_codex_agents.py`
- `scripts/sync_codex_account_configs.py`
- `scripts/sync_claude_agy_parity.py`
- `scripts/sync_ai_agent_ecosystem.py`
- `scripts/agent_quota_status_guard.py`
- `scripts/context_handoff.py`

**Interfaces:**

```python
def render_context_profiles(resolution: ContextResolutionV1, output_root: Path, targets: tuple[str, ...]) -> RenderManifestV1: ...
def check_context_profiles(resolution: ContextResolutionV1, output_root: Path, targets: tuple[str, ...]) -> tuple[CheckResult, ...]: ...
def run_codex_prompt_input(ticket_id: str, lane_id: str, narrowing: NarrowingRequestV1 | None) -> ProviderContextProbeV1: ...
def probe_provider_context(provider: Literal["codex", "claude", "agy"], ticket_id: str, lane_id: str) -> ProviderContextProbeV1: ...
```

`scripts/optimize_codex_skill_budget.py` is not owned or modified by this ticket. Task 19 leaves `TICKET-SKILL-BUDGET-002` at `BLOCKED_NONREPRODUCIBLE / VERIFIED_LOCAL_CODE_CONTRACT / LIVE_CONFIG_DRIFT`, never `DONE`, and releases exclusive future ownership of `scripts/sync_codex_account_configs.py` to Context F at 23,004 bytes, SHA-256 `4d37513698a48f400e71e0e113c69e073aa9c74e6b2479494c89e76758aaee79`, blob `9d9e9f0f4988a9f58063082b259836b8cb114d96`. Forty-four focused tests pass, but three current read-only checks exit 1 because codex3 lacks eight disable registrations; the old receipt is stale. Codex3 remediation is a separate sequential operational lane, and no account sync may overlap F. Recheck every F path against A's device/inode/size/mtime/hash/owner snapshot immediately before opening the lane.

- [ ] Implement strict canonical input via `scripts/resolve_agent_context.py`. Registry, approved context, evidence, index, and manifest use the design's exact algorithms/prefixes; raw artifact hashes use exact bytes. Manifest excludes itself and self-digests the unsigned payload.
- [ ] Inventory the three schemas, registry, approved context, every selected nested role JSON, selected skill/rule body, renderer entrypoint/import, capability index, and every generated artifact. Sort exact repository-relative paths; reject duplicate/case-colliding/missing/stale/extra entries and unchanged digest with changed normalized semantics.
- [ ] Render only from canonical `.agents` to Codex/Claude/AGY/Antigravity. Remove mtime/newer-mirror authority. Managed roots are exactly those in the design. Predict source/output snapshots before writes; recheck source snapshot before each materialization.
- [ ] Implement bounded same-buffer hash/parse and ancestor/final `lstat` containment. Reject symlink, hardlink, non-regular, broken, escaping, unsafe, or race-changed objects. Use same-directory `0600` temp, file fsync, target/parent recheck, atomic replace, directory fsync, and explicit final mode. Report extra/unowned artifacts without deletion/overwrite. Replace only one valid generated marker pair and prove outside bytes identical.
- [ ] Make `sync_ai_agent_ecosystem.py --check` and every delegated check calculation-only and byte-pure: no provider, subprocess with write effects, directory/lock/temp creation, write/chmod/utime/replace/watcher, account-home/rollout/transcript access, or evidence update. Provider/runtime probes are never invoked by check.
- [ ] Make the existing sync scripts thin typed consumers. `sync_codex_account_configs.py` may calculate repository profile expectations but cannot write external account homes here. Alias labels remain historical budget targets; no alias/capacity/account-purpose constant changes.
- [ ] Implement `scripts/codex_role.py` with only this production CLI:

```text
python3 scripts/codex_role.py --ticket-id TICKET-CONTEXT-OPT-001 --lane-id TICKET-CONTEXT-OPT-001-G --narrow-action context.inspect.codex-prompt --narrow-path project/routers/__context_probe__ --narrow-horo-skill qa-regression-provenance debug prompt-input
```

Reject every other command/flag and optional plugin field. Select the approved record from the code-fixed root, validate ticket/plan/evidence/registry/manifest/profile hashes and exact inventories, derive action `context.inspect.codex-prompt` from the literal argv, and reject unknown role/profile with exit `64` before launch.

- [ ] Pin the absolute Codex executable and adapter version in code; validate trusted non-writable ancestry and regular executable type. Launch with `shell=False`, literal argv, repository cwd, bounded timeout/argv/streams, and minimal allowlisted locale/temp/home environment after stripping auth/token/proxy, `PYTHONPATH`, `GIT_*`, `LD_*`, `DYLD_*`, provider homes, and everything unneeded. Fake injection exists only as an internal test seam.
- [ ] Create isolated `0700` temp home and `0600` files. Require OS-enforced no-network. Parse one strict bounded document at `/0/content/0/text`, one exact skills block, all canonical/materialized skills, and disjoint exact namespace sets. Sanitize before evidence hashing; never persist raw streams/prompt/env/home.
- [ ] Implement `scripts/probe_agent_context_runtime.py` for only `codex`, `claude`, or `agy`, selected from code-pinned version adapters and the approved ticket/lane. Help text never supplies commands. Codex uses the same isolated `debug prompt-input`; Claude/AGY use a documented local operation plus OS network isolation or return nonzero `UNAVAILABLE`/`UNKNOWN`.
- [ ] Emit `ProviderContextProbeV1` with exactly: `schema_version`, `provider`, `adapter_version`, `registry_sha256`, `approved_context_sha256`, `normalized_scopes`, `horo_skills`, `provider_plugins`, `runtime_tools`, `result`, `reason_code`, `exit_code`, `issued_at`, `expires_at`, `sanitized_evidence_sha256`. The last field removes only itself, canonicalizes the remaining closed fields, and uses the evidence prefix. Antigravity has no runtime-probe receipt.
- [ ] Keep dispatch health distinct from context probes. Create `.agents/schemas/multiagent-activation-health-evidence-v1.schema.json` only in the dispatch Task C lane. Its closed `ActivationHealthEvidenceV1` fields are exactly `schema_version`, `artifact_type`, `evidence_id`, `ticket`, `attempt_id`, `admission_id`, `alias`, `provider`, `session_id`, `source_kind`, `source_identity_sha256`, `result`, `reason_code`, `issued_at`, `expires_at`, `owner_role`, `reviewer_role`, `sanitized_evidence_sha256`; only fresh `PASS`, TTL <=120 seconds, distinct owner/reviewer, and `provider_native_health_receipt|platform_native_health_receipt` are eligible from a code-fixed owner-only source with B4 protections. Reject quota/config/help/cache/argv/exit/context-probe/claim/grant/prose sources. Bind its digest into `RuntimeAdmissionV1` and cross-bind policy, command, objective, ownership, route, decision, scheduling snapshot, runtime config, claim, grant, consume, receipt, and all four store identities. Ordinary activation remains globally CLOSED.
- [ ] Dispatch RED must include `test_activation_health_evidence_v1_is_closed_same_buffer_digest_bound_and_fresh`, `test_config_quota_help_cache_argv_exit_and_owner_claim_are_not_health_evidence`, `test_runtime_admission_health_mismatch_blocks_before_consume_and_popen`, `test_scoped_admission_does_not_open_other_attempt_alias_or_global_runtime`, `test_runtime_admission_cross_binds_all_four_store_identities`, and `test_missing_unknown_blocked_stale_future_self_reviewed_or_replayed_health_has_zero_starts`. Current authority provides no eligible health evidence; missing/UNKNOWN/BLOCKED starts zero children.
- [ ] Harden quota/handoff validation: absent/contradictory signal is `UNKNOWN`; thresholds are remaining percentage; unsafe summary is disallowed without separate authority; complete active ticket/plan precedes derived handoff; incomplete/stale handoff never authorizes provider work.
- [ ] Run all eight context modules, relevant existing sync/budget/handoff neighbors, and Python compilation for the ten F scripts. Frozen baseline bytes/hashes must remain unchanged.

## Task G: Repository sync, budget, and local probe receipts

**Ticket/state:** `TICKET-CONTEXT-OPT-001-G`, blocked by F GREEN and a conflict-free predicted manifest.
**Owner:** `devops`

**Writable files:** only exact generated artifacts resolved and ownership-cleared by the signed manifest plus:

- `plans/evidence/context-opt-001/render-check.json`
- `plans/evidence/context-opt-001/budget-report.json`
- `plans/evidence/context-opt-001/runtime-probe-codex.json`
- `plans/evidence/context-opt-001/runtime-probe-claude.json`
- `plans/evidence/context-opt-001/runtime-probe-agy.json`
- `plans/evidence/context-opt-001/antigravity-render-parity.json`

- [ ] At the phase checkpoint, revalidate host 27% AMBER separately from codex1/agy1 96% five-hour and agy2 75.21% weekly/100% five-hour owner observations. None is execution proof and none may substitute for another pool. Repository-local sync and authorized credential-free OS-no-network probes proceed only while fresh. After documentation freeze and local isolation/receipt validation, reserve codex1 for security re-audit, agy1 for hierarchy/parity, and agy2 preferably for semantic QA; otherwise return UNKNOWN without dispatch.
- [ ] Resolve the complete manifest target list, compare every source/output snapshot and current owner, then run only `python3 scripts/sync_ai_agent_ecosystem.py --sync --target context-profiles`. Stop rather than overwrite/delete an extra, changed, or unowned path.
- [ ] Snapshot repository and canary roots, run `env PYTHONDONTWRITEBYTECODE=1 python3 scripts/sync_ai_agent_ecosystem.py --check`, and prove no name/link/byte/mode/mtime/entry change and no provider launch.
- [ ] Measure every base/focused/compatibility profile in isolated roots. Record catalog characters, count, selected-body characters, total prompt characters, truncation count, and shortening warning. Every total is numeric `<=8000`, truncation is zero, warning absent, and mandatory closures remain present.
- [ ] Run local probes only with OS network isolation:

```bash
python3 scripts/probe_agent_context_runtime.py --provider codex --ticket-id TICKET-CONTEXT-OPT-001 --lane-id TICKET-CONTEXT-OPT-001-G --no-network
python3 scripts/probe_agent_context_runtime.py --provider claude --ticket-id TICKET-CONTEXT-OPT-001 --lane-id TICKET-CONTEXT-OPT-001-G --no-network
python3 scripts/probe_agent_context_runtime.py --provider agy --ticket-id TICKET-CONTEXT-OPT-001 --lane-id TICKET-CONTEXT-OPT-001-G --no-network
```

Each receipt must be fresh, closed, sanitized, digest-bound, and `PASS`. `UNAVAILABLE`/`UNKNOWN` blocks local verification. Independently parse Antigravity output into its static parity receipt; do not call it runtime evidence.

## Task H: Independent local-verification receipts

**Ticket/state:** `TICKET-CONTEXT-OPT-001-H`, blocked by G

| Sequential owner | Exact writable receipt | Read-only responsibility |
|---|---|---|
| `qa_tester` | `plans/evidence/context-opt-001/qa-verdict.json` | All frozen focused tests/evals, neighbor suites, manifest/probe/budget semantics, containment, provenance. |
| `code_reviewer` | `plans/evidence/context-opt-001/code-review-verdict.json` | Repository-only secret scan, least privilege, B1-B7, source/exclusion/diff review; no deployment capability. |
| `ba_auditor` | `plans/evidence/context-opt-001/ba-audit-verdict.json` | DoR/DoD, owners, digests, lifecycle, quota/handoff, documentation and release boundary. |

- [ ] QA verifies all 29 frozen baseline paths/hashes, context and neighbor suites, pure check, exact namespaces, closures, renderer semantics, all three runtime receipts, static Antigravity parity, and no alias/application drift.
- [ ] Reviewer verifies no secret/account/transcript access, no extra capability/artifact, no source ownership violation, no unsafe subprocess/filesystem path, and no unauthorized Git/release action.
- [ ] BA requires unanimous current receipts, `README.md`/`HOWTO.md`, final canonical ticket/plan update, then operator-derived valid handoff. The only local terminal state is `VERIFIED_LOCAL`; never mark `DONE` or release.

## Post-local release-QA resumption

After `VERIFIED_LOCAL`, existing release-QA owners first re-run `git rev-parse HEAD`, `git status --short`, and `python3 scripts/context_handoff.py validate --input HANDOFF.md`. Interrupted results remain `UNKNOWN`. Only the already-planned read-only audit lanes may resume; release source remediation and release remain blocked. Rule 21 `DONE`, release notes, tag, push, clean-tree, deployment, and production evidence requirements remain fully intact.

## Stop conditions

Stop on baseline/source/owner drift, mismatch from the pinned Task-19 Skill Budget source identity, concurrent account sync, missing manifest target, unsafe file type/link/race, check mutation, prompt/parser ambiguity, unstripped environment, unproved network isolation, unsanitized evidence, `UNAVAILABLE`/`UNKNOWN`, alias/capacity/application change, or any unauthorized commit/push/tag/deploy/publish/secret/provider/account action.
