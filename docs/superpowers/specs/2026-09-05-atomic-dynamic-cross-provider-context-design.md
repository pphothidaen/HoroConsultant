# Atomic Dynamic Cross-Provider Context Design

**Status:** `APPROVED_FOR_RED_PREPARATION`
**Ticket state:** parent `DOING -- A draft rebuild only`; `TICKET-CONTEXT-OPT-001-A` is `DOING -- DRAFT_REBUILD_REQUIRED`; `TICKET-CONTEXT-OPT-001-B` is `BLOCKED_SECURITY_CONTRACT_CORRECTION` until an independent review accepts this corrected contract and A is complete.
**Authority:** Owner approval on 2026-09-05 covers planning, delegation, bounded local implementation/testing/review, repository-local cross-provider synchronization, credential-free OS-no-network local probes, and later release-QA resumption. Exactly one local QA-owned test/eval-fixture/provenance baseline commit is authorized after assertion-level RED and independent review. It contains exactly 39 paths: the exact 29-path context portion plus the exact 10-path dispatch portion. No second or other commit and no push is authorized. Every source/config/generated/runtime-evidence change remains uncommitted. Tag, deploy, publish, destructive Git, secret action, external account mutation, and provider jobs remain unauthorized.
**Canonical ticket:** `TICKET-CONTEXT-OPT-001`

## Authority and supersession

This specification, `ATOMIC_TICKET.md`, `plans/plan.md`, and the four linked context plans are normative. SDD reports 10 and 11 are correction inputs; task 17 at SHA-256 `bbc84f46516b023d1b24d40604319f8688ad4415c679e7d907f8ea91e6b0f176` and task 18 at SHA-256 `c7ae2047d2d6bef138f05d20a38227e43d96fdf2630fab83e35c33511ca4f6bd` require this C3 correction. The independently corrected QA index `task-8-qa-test-map.md` at SHA-256 `ef121715ed30de79be2d1f198bb29e01b6ba84bc298fd5db0de1c7ba8c879b5b` plus its six embedded-hash contract files is the RED handoff. Task 19 at SHA-256 `52c191c36b42a8cfefd047e24924fdce34789164896c75a6f1611e4e9c163276` releases the pinned Skill Budget source ownership without a false `DONE`. Reports 4, 7, and the incompatible operator directions in report 9 are `SUPERSEDED/HISTORICAL INPUT ONLY`: they cannot define bootstrap skills, reviewer capability, alias policy, registry shape, quota routing, or frozen expectations. In particular, this ticket does not create `agent_runtime_registry.v1.json`, migrate alias/capacity maps, or update `TICKET-META-008` for its continuity state.

## Outcome and exclusions

Build a lean, fail-closed Horo context resolver with additive role/phase/action/all-path depth; immutable security/API/release/metaphysics minimums; one-way deterministic provider rendering; a local inspection-only Codex adapter; and typed local context evidence.

The closed world covers `horo_skill`. `provider_plugin` and `runtime_tool` remain disjoint attestations. Root Horo bootstrap is exactly `requirement-grill-gate`, `agile-governance`, `orchestrator-delegation`, and `anti-cognitive-decay`; `bsa-doc-skill-management` is BA-role-only. The only enabled provider-plugin exception is the exact pinned Superpowers identity; optional plugin request fields are invalid. Browser-family tools are runtime tools and never satisfy a Horo dependency.

Out of scope and frozen by byte/semantic guards:

- provider alias, capacity, broker, quota-pool, model, effort, account-purpose, and dispatchability policy;
- application/API/metaphysics behavior and all production `project/**`, `rust_core/**`, `api/index.js`, `vercel.json`, UI, router, schema, calculation, and deployment-target files;
- plugin/cache/account-home mutation; provider login, canary, model/network work; secret reads or values;
- unauthorized commit, push, tag, deploy, publish, release, destructive Git, and external messages.

The exact policy-byte freeze covers `.agents/config/agent_broker.v1.json`, `.agents/config/full_capacity_guard.v2.json`, `.agents/config/multiagent_model_policy.yaml`, `.agents/config/multiagent_prompt_command.example.yaml`, `.agents/config/multiagent_prompt_command.luna-one-shot.yaml`, `.agents/config/multiagent_prompt_command.runtime-readonly-v2.yaml`, `.agents/config/multiagent_prompt_command.runtime-readonly-v3.yaml`, `.agents/config/multiagent_prompt_command.yaml`, `.agents/config/native_lane_capacity.v1.json`, `.agents/config/s3_capacity_policy.json`, `.agents/hooks/full_capacity_guard.py`, `scripts/agent_broker_wrapper.py`, `scripts/codex_quota_workaround.py`, `scripts/install_agent_broker.py`, `scripts/multiagent_broker_bridge.py`, `scripts/multiagent_capacity.py`, and `scripts/multiagent_prompt_command.py`. Task A records raw hashes and parsed alias/purpose/capacity semantics; every later lane requires identical bytes and semantics. For shared `scripts/agent_quota_status_guard.py` and `scripts/sync_codex_account_configs.py`, characterization freezes `ACCOUNT_CONFIGS`, alias sets, and external-write behavior while context-only validation changes proceed. No registry field may represent account, alias, capacity, quota pool, model, effort, broker route, dispatchability, external home, or wrapper executable.

`TICKET-CONTEXT-ALIAS-002` remains separately `BLOCKED_NEEDS_HITL`. Current aliases are historical measurement labels only; this ticket invents no executable alias.

## Canonical JSON and digest contract

Every JSON ingress first uses a duplicate-key-rejecting parser and rejects `NaN`, `Infinity`, and `-Infinity`. It walks every key and string recursively, computes Unicode NFC, and rejects the document if any input string is not already NFC. Security identity objects contain no floats.

Canonical bytes are exactly:

```python
json.dumps(
    value,
    sort_keys=True,
    separators=(",", ":"),
    ensure_ascii=True,
    allow_nan=False,
).encode("utf-8")
```

There is no trailing newline. Domain-separated SHA-256 is `sha256(prefix + canonical_bytes).hexdigest()` with these exact ASCII prefixes, each ending in NUL:

| Identity | Prefix |
|---|---|
| registry | `b"horo-context:scope-skill-registry:v1\0"` |
| approved context | `b"horo-context:approved-ticket-context:v1\0"` |
| manifest | `b"horo-context:scope-skill-manifest:v1\0"` |
| sanitized evidence | `b"horo-context:evidence:v1\0"` |
| capability index | `b"horo-context:capability-index:v1\0"` |

Rendered artifact hashes are plain SHA-256 over the exact file bytes, without a prefix. The manifest is not in its own artifact inventory. Its `manifest_sha256` is calculated by removing only that field, canonicalizing the remainder, and using the manifest prefix.

## Canonical authority model

`.agents/config/scope_skill_registry.v1.json` is the manually edited scope/capability authority, validated by `.agents/schemas/scope-skill-registry-v1.schema.json`. It defines the disjoint `horo_skill`, `provider_plugin`, and `runtime_tool` namespaces; roles; phases; actions; additive scopes; dependencies/conflicts; providers; compatibility routers; and strengthen-only registry closures. Unknown fields and identifiers fail closed.

Mandatory closure minimums are immutable code constants. Registry data may add requirements but cannot remove a closure, weaken a trigger, remove a required capability/rule/evidence type, or authorize an excluded action. Missing or weakened minimums return `BLOCKED: MISSING_MANDATORY_GATE`.

Each approved ticket has exactly one authority record beneath the code-fixed root `.agents/context/tickets/`. This ticket's only record is `.agents/context/tickets/TICKET-CONTEXT-OPT-001.v1.json`, validated by `.agents/schemas/approved-ticket-context-v1.schema.json`. The resolver selects it from normalized `ticket_id` plus `lane_id`; neither caller nor environment supplies an authority path.

Admission rejects an unmanifested, caller-selected, wrong-code-fixed-path, wrong-ticket/lane, stale, symlinked/hardlinked, nonregular, escaped, or digest-mismatched record before child launch. It does not reject solely because Git reports the correct D-owned, manifest-bound record as untracked: Git tracking state is neither authority nor execution evidence. RED includes `test_approved_context_is_code_fixed_manifest_bound_and_not_caller_selected` and `test_git_tracking_state_is_not_authority_or_execution_evidence`.

`ApprovedTicketContextV1` is a closed object containing:

```text
schema_version, ticket_id, revision, ticket_sha256, plan_sha256, lanes
```

`ticket_sha256` is raw SHA-256 over the exact UTF-8 bytes from the single `CONTEXT-OPT-001-20260905:START` marker through its matching `END` marker in `ATOMIC_TICKET.md`; `plan_sha256` uses the same rule in `plans/plan.md`. Missing, duplicate, nested, or reordered markers fail. A later canonical state edit makes the approved record stale; any further launch requires a new monotonically increasing revision by the D owner plus independent review, never caller recomputation.

Each lane is closed and contains exactly:

```text
lane_id, role, phase, actions, touched_paths, requested_horo_skills,
source_domain, risk_flags, allowed_child_command_class, exclusions,
evidence_refs
```

`actions`, `touched_paths`, `requested_horo_skills`, `risk_flags`, `exclusions`, and `evidence_refs` are explicit arrays, never inferred omissions. There is no provider-plugin request field. A closed narrowing request may supply only subsets of the approved lane's actions, paths, and requested Horo skills. It cannot change role, phase, domain, risks, command class, exclusions, evidence, ticket, or lane. The adapter derives command-sensitive actions from the literal child argv and requires those actions to be approved even when omitted from a narrowing request.

## EvidenceRefV1 and mandatory closures

`.agents/schemas/evidence-ref-v1.schema.json` defines a closed `EvidenceRefV1` with exactly:

```text
type, path, schema_version, sha256, subject_ticket, subject_domain,
subject_revision, issued_at, expires_at, owner_role, reviewer_role
```

`expires_at` may be an explicit JSON `null` only for immutable evidence types. Each path is normalized repository-relative and contained. Evidence is a regular non-symlink file; the resolver reads bounded bytes once, hashes and parses the same buffer, validates its declared schema, and binds digest, subject ticket/domain/revision, freshness, owner, and reviewer. Missing, stale, wrong-ticket/domain/revision/owner, duplicate, extra, malformed, indeterminate, symlinked, or digest-mismatched evidence fails closed. Caller booleans such as `passed=true` are unknown fields, not evidence. Evidence hashes cover sanitized canonical evidence only, never raw provider output, prompts, transcripts, environment, or secrets.

Immutable closures require:

| Closure | Trigger and minimum |
|---|---|
| Security/source | Approved context, independently verified immutable RED baseline before source, one editor, repository-only secret scan, read-only review, and hard denials for secret/account/external mutation. |
| API | Every router/API/schema/OpenAPI/golden path injects Pydantic v2 validation, compatibility, structured errors, CORS/security headers, OpenAPI golden, and API/UI QA. |
| Release | Release actions remain denied here. A future release requires HF Docker backend, verified Vercel UI, exact version plus `release_source_commit`, publisher/governance tests, five current viewports, rollback identities, and distinct DevOps/QA/reviewer/orchestrator evidence. |
| Metaphysics | Exact domain and deterministic tool grounding. Ambiguity, boundary hour, severe conflict, low consensus, force review, or training promotion requires a fresh scope-audit receipt with `required_human_review=true`, `summary.pass_gate_check=true`, and separately bound owner sign-off. |

## Resolution and path safety

Resolution is the union of root + role + phase + every approved/derived action + every touched path and all broad-to-narrow ancestor scopes + transitive dependencies + immutable closures. Duplicate/path order does not change output. Descendants may strengthen but never subtract root or closure policy.

Only normalized repository-relative POSIX paths are accepted. Reject empty, `.`, `..`, NUL/control, backslash, absolute/drive/UNC, case-colliding, ambiguous glob, and escaping paths. Existing sources and every ancestor use `lstat`; symlinks, non-regular files, broken links, and final files with `st_nlink > 1` are rejected. Open without following the final symlink where supported; bound reads are size-limited and recheck device, inode, size, and nanosecond mtime before/after. Missing probe leaves resolve from the deepest existing ancestor, which must also be contained and non-symlinked. Hash and parse the same byte buffer.

Physical scoped files remain only at real boundaries: root, `project/core/`, `project/routers/`, `project/static/`, `rust_core/`, and `scripts/`. No `tests/AGENTS.md` is created without a separately proven boundary.

## One-way rendering and manifest

Canonical `.agents` sources render one way to Codex, Claude, AGY, and Antigravity. Provider mirrors, mtimes, caches, and installed profiles are never upstream authority. The exact manifest inventories:

- the three schemas, registry, and approved ticket context;
- every selected nested role JSON from the exact 21-path allowlist in the skill-migration plan;
- every selected canonical `SKILL.md` and `.agents/rules/*.md` body;
- `scripts/render_agent_context_profiles.py` and every imported renderer module;
- the capability index and every generated Codex/Claude/AGY/Antigravity artifact.

Every entry is a sorted repository-relative path with an exact raw-byte digest. Before rendering, source paths are snapshot-checked; immediately before each materialization the same source snapshot is rechecked. Managed roots are exactly `.codex/agents/`, `.claude/agents/`, `.claude/rules/`, `.claude/skills/`, `.agy/agents/`, `.agy/rules/`, `.agy/skills/`, `.antigravity/agents/`, `.antigravity/skills/`, plus manifest-listed marker sections in exactly `AGENTS.md`, `project/core/AGENTS.md`, `project/routers/AGENTS.md`, `project/static/AGENTS.md`, `rust_core/AGENTS.md`, `scripts/AGENTS.md`, `CLAUDE.md`, and `AGY.md`.

Sync never deletes or overwrites an unmanifested/runtime-effective or unowned extra. It reports the path and stops for owner action. Writes use a same-directory `0600` temporary file, file `fsync`, parent/target revalidation, atomic `os.replace`, directory `fsync`, and an explicitly approved final mode. Targets with symlink ancestors, non-regular type, or link count greater than one are rejected. Marker replacement rejects missing, duplicate, nested, or reordered marker pairs and proves all outside bytes unchanged.

`scripts/sync_ai_agent_ecosystem.py --check` computes expected bytes in memory only. It never launches a provider, creates directories/locks/temp files, writes/chmods/touches/replaces, starts watchers, reads account homes/rollouts/transcripts, or mutates any repository/external byte. Native probes belong only to Task G.

## Local adapter and provider evidence

`scripts/codex_role.py` exposes only the pinned local child operation `debug prompt-input`. It accepts `ticket_id`, `lane_id`, and optional subset-narrowing flags; it accepts no arbitrary delimiter/passthrough, executable, config, cwd, profile, plugin, `exec`, login, model, search, or network option. The absolute executable and supported version are code-pinned and validated as a regular executable beneath a non-writable trusted parent. The test fake is injected only through an internal dependency seam.

Launch uses `shell=False`, literal argv, repository-root cwd, a 30-second timeout, argv at most 8 KiB, stdout at most 4 MiB, stderr at most 64 KiB, and an environment containing only `HOME`, `CODEX_HOME`, and `TMPDIR` set to the single adapter-created mode-`0700` probe root plus `LANG=C`, `LC_ALL=C`, and `TERM=dumb`. Auth/token/proxy variables, `PATH`, `PYTHONPATH`, `GIT_*`, `LD_*`, `DYLD_*`, provider homes, and all other inherited values are stripped. Strict JSON/evidence inputs are at most 256 KiB each; any selected source/generated artifact is at most 2 MiB and the total manifest-bound source/artifact bytes at most 32 MiB. Temporary files are `0600`; contents are never logged. `--no-network` must be OS-enforced. If a supported local inspection cannot be proven isolated, the result is nonzero `UNAVAILABLE` or `UNKNOWN`.

For adapter `codex-debug-prompt-input-v1`, stdout is exactly one bounded JSON document with no trailing non-whitespace bytes. The only prompt JSON node is JSON Pointer `/0/content/0/text`: root array length one, one object, `content` array length one, one text object, and no competing prompt/system node. The text contains exactly one non-nested `<skills_instructions>` block. Strict extraction rejects malformed/escaped/nested/marker-like tags, duplicate IDs/names, control text, truncation/ellipsis, warnings on either stream, unknown schema, and namespace collisions. Exact canonical and materialized skill inventories are independently enumerated; unregistered, mismatched-frontmatter, symlinked, rogue workspace/global, or unbound skills block.

`ProviderContextProbeV1` has only:

```text
schema_version, provider, adapter_version, registry_sha256,
approved_context_sha256, normalized_scopes, horo_skills, provider_plugins,
runtime_tools, result, reason_code, exit_code, issued_at, expires_at,
sanitized_evidence_sha256
```

`schema_version` is `provider-context-probe-v1`; `provider` is `codex`, `claude`, or `agy`; timestamps are UTC RFC 3339 and `expires_at` must be later than `issued_at`; `reason_code` is a stable uppercase ASCII slug; exit code is zero only for `PASS`. `registry_sha256` and `approved_context_sha256` use their named domain prefixes. `sanitized_evidence_sha256` removes only itself, canonicalizes the other closed fields, and uses the evidence prefix. Codex, Claude, and AGY require fresh supported local runtime probes. `UNAVAILABLE` and `UNKNOWN` are nonzero and never pass-by-skip. Antigravity receives independently parsed static semantic render parity only, with no provider-runtime claim. No raw stdout/stderr or environment enters receipts.

Dispatch activation uses a separate closed `.agents/schemas/multiagent-activation-health-evidence-v1.schema.json`. `ActivationHealthEvidenceV1` contains exactly `schema_version`, `artifact_type`, `evidence_id`, `ticket`, `attempt_id`, `admission_id`, `alias`, `provider`, `session_id`, `source_kind`, `source_identity_sha256`, `result`, `reason_code`, `issued_at`, `expires_at`, `owner_role`, `reviewer_role`, and `sanitized_evidence_sha256`. `result` is `PASS|UNKNOWN|BLOCKED`, but only `PASS` is eligible; `expires_at` is mandatory and at most 120 seconds after `issued_at`; owner and reviewer must differ. A bounded same buffer is hashed, parsed, canonicalized, and schema-validated from the code-fixed `activation-health` child of an owner-only durable root with the same B4 link/type/containment/race protections. `source_kind` is only `provider_native_health_receipt|platform_native_health_receipt`; quota, configuration, help, cache, argv, exit status, context probes, claims, grants, and prose are not health evidence. The sanitized health digest binds into `RuntimeAdmissionV1`; its admission digest cross-binds policy, command, objective, ownership, route, decision, scheduling snapshot, runtime config, claim, grant, consume, receipt, and all four store identities. Ordinary activation remains globally `CLOSED`; current authority contains no eligible health observation, so missing/`UNKNOWN`/`BLOCKED` starts zero children.

Required dispatch RED is `test_activation_health_evidence_v1_is_closed_same_buffer_digest_bound_and_fresh`, `test_config_quota_help_cache_argv_exit_and_owner_claim_are_not_health_evidence`, `test_runtime_admission_health_mismatch_blocks_before_consume_and_popen`, `test_scoped_admission_does_not_open_other_attempt_alias_or_global_runtime`, `test_runtime_admission_cross_binds_all_four_store_identities`, and `test_missing_unknown_blocked_stale_future_self_reviewed_or_replayed_health_has_zero_starts`.

## Skill, governance, and lifecycle design

Only eight focused skills are added: `qa-regression-provenance`, `qa-api-ui-e2e`, `five-elements-ui-palette`, `wcag-apca-color-audit`, `ui-color-token-handoff`, `metaphysical-request-router`, `metaphysical-hitl-scope-gate`, and `metaphysical-finetune-handoff`. Existing `qa-e2e-testing`, `web-color-design`, and `metaphysical-domain-engine` become workflow-free compatibility routers. No other catalog split is allowed.

The 29-path context baseline contains eight context test modules, eleven literal fixtures, nine immutable expectation fixtures under `tests/fixtures/context_profiles/evals/`, and `plans/test_provenance/ticket-context-opt-001.json`. The expectation fixtures are exactly `qa-regression-provenance.json`, `qa-api-ui-e2e.json`, `five-elements-ui-palette.json`, `wcag-apca-color-audit.json`, `ui-color-token-handoff.json`, `metaphysical-request-router.json`, `metaphysical-hitl-scope-gate.json`, `metaphysical-finetune-handoff.json`, and `qa-e2e-testing.json`. The nine corresponding real `.agents/skills/<skill>/evals/evals.json` files are E1 source allowlist/manifest inputs, not baseline content; immutable tests exact-compare each source to its fixture and reject missing, extra, reordered, or weakened cases. Fixtures cannot authorize or enable a skill. Required RED includes `test_combined_baseline_paths_are_all_guard_classified_as_tests_or_manifests`, `test_each_skill_eval_matches_its_frozen_test_fixture_exactly`, and `test_eval_fixture_cannot_authorize_or_enable_a_skill`. The durable QA-owned pressure receipt is `plans/evidence/context-opt-001/skill-pressure-red.json`; it is digest-bound evidence but not committed baseline content. At the 27% AMBER observation, deterministic pressure preparation requires fresh reassessment; provider-backed pressure sampling remains unauthorized and is recorded as not run.

A test-first governance lane updates canonical Rules 17, 20, and 21 plus `multi-account-agent-orchestration`. It defines all quota thresholds as remaining percentage, active ticket/plan first then derived `HANDOFF.md`, and prohibits `codex_quota_workaround.py --mode summary` without separate login-status/rollout-read authority. Rule 21 keeps `DONE` and release/sprint tag/push/release-note/clean-tree requirements intact. It adds `VERIFIED_LOCAL` as a non-release terminal state: all local context work/evidence verified, but no release completion or DONE claim. `VERIFIED_LOCAL` may unlock only fresh read-only release-QA audits.

The test-only commit gate comes from `qa-e2e-testing`, not current Rule 21. Exactly one local QA-owned test/eval-fixture/provenance baseline commit is authorized after assertion-level RED and independent review. It contains exactly 39 paths: the exact 29-path context portion plus the exact 10-path dispatch portion. No second or other commit and no push is authorized. Every source/config/generated/runtime-evidence change remains uncommitted. The pressure receipt, ticket/plan, and unrelated dirty work stay out. Source mutation remains blocked until that commit and independent post-commit verification exist.

## Admission, verification, and stop

Task A alone is active as `DOING -- DRAFT_REBUILD_REQUIRED`. Its provenance file is absent under the current authority; QA must create `DRAFT_RED_NOT_COMMITTED` with current authority hashes, current HEAD/status including lock state, separate quota pools, the exact 29+10 future-baseline partition, prospective source paths with raw hash or `ABSENT` and owner, exclusions, and empty RED runs. Do not call it refreshed/current until QA validates it. Task B remains `BLOCKED_SECURITY_CONTRACT_CORRECTION` until A is complete and an independent reviewer accepts B1-B7, the exact frozen inventory, immutable closure model, JSON/digest contract, containment tests, and ownership lanes. Quota is `AMBER` at 27% remaining from the owner-supplied phase-boundary observation at `2026-09-05T04:19:20Z`; guard exit 0 reported `signal_present=true`, `source=argument`, `handoff_required=false`, and `docs_ok=true`. This is capacity evidence only, never provider execution proof. Reassess before each bounded dispatch, deterministic pressure-preparation step, and long-running task; do not run provider-backed pressure samples.

Auxiliary pools remain separate: codex1 five-hour 96% left (reset 14:44 Asia/Bangkok, observed `2026-09-05T11:20:48+07:00`); agy1 five-hour 96% left in the same window; agy2 weekly 75.21% left (about 133h58m to refresh) and five-hour 100% left in this phase. Never aggregate them with host capacity. After documentation freeze, codex1 is reserved for bounded read-only security re-audit, agy1 for bounded hierarchy/parity audit, and agy2 preferably for bounded cross-provider semantic QA, but only after local alias/config isolation validation, exact receipt-bound dispatch, and fresh pool-specific recheck. These observations prove no authentication, isolation, executability, model, or provider execution; failed validation returns UNKNOWN.

Local completion target is `VERIFIED_LOCAL`, never `DONE`. It requires A-H evidence, frozen committed baseline predating source, all focused/neighbor tests green, exact inventories/digests, pure checks, three fresh local runtime probe `PASS` receipts, static Antigravity parity, budgets `<=8000` with zero shortening/truncation, three independent H receipts, docs updated, exclusions preserved, and final quota/handoff checkpoint. `UNAVAILABLE`/`UNKNOWN` probe evidence blocks `VERIFIED_LOCAL`.

After `VERIFIED_LOCAL`, release-QA read-only audits may resume only after fresh HEAD/worktree and derived handoff validation; interrupted results remain `UNKNOWN`. Release, release source remediation, and Rule 21 `DONE` remain blocked behind their own gates. Stop on contract/digest/path/ownership drift, unknown capability, non-NFC or unsafe JSON, extra artifact/skill, missing closure/evidence, quota ambiguity before high-cost work, external/secret/provider action, or any unauthorized Git/release/application mutation.
