# AGY Bucket Admission v1

**Status: DRAFT / PENDING_APPROVAL**
**Protocol:** `horoconsultant.agy-bucket-admission.v1`
**Artifact type:** approval-ready, test-first HITL package
**Activation:** prohibited until explicit owner approval and all gates below pass

## 1. Scope and approval gate

### In scope

This contract defines the first, observation-only protocol phase for admitting
structured AGY bucket observations into a future scheduling and receipt flow.
It defines the candidate schema, artifact, guard, policy, receipt-v3 boundary,
retention controls, QA-owned red baseline, and HITL handoff conditions.

### Explicitly out of scope

- Provider execution (`S5`).
- Dispatcher execution (`CLOSED`).
- Activation (`activation_prohibited: true`).
- Scheduler, prompt, or capacity changes in the first phase.
- Provider retry or fallback.
- Deployment, push, or commit, except the explicitly authorized test-only
  baseline commit described in Section 6.
- Policy weakening, implicit inference, conversion, or substitution between
  protocols.

### Inputs, assumptions, and dependencies

- The source domain is `metaphysical-domain-engine`.
- Current snapshot basis: repository `HEAD`
  `ecd37d71b89cbda6161a44626cf49ea063c3b5df`, observed on `2026-08-28`.
  Hashes and state below are current-snapshot evidence, not implementation
  proof.
- QOBS v1 remains the authoritative six-signal contract and requires 18
  six-signal paths.
- AGY structured buckets expose only `remaining_fraction`, `reset_time`, and
  `disabled`.
- Receipt-v2 is closed and immutable.
- Existing QOBS schemas and the frozen QOBS integration test are immutable.
- The existing sanitizer source remains an independently tracked working-tree
  path and is not part of the next implementation allowlist. Its required
  pre-edit digest is:
  `afc7cc6951944b806767c361501fa5934b5b9a24d20ad902a40302465a3a88ed`.
- A human owner must approve this draft, the red baseline, unresolved conflicts,
  low-consensus cases, and any later integration phase.

### Success criteria and stop condition

Success requires every acceptance criterion in Section 9 to be evidenced, the
HITL scope-audit gate to report `summary.pass_gate_check=true`, and owner
sign-off to be recorded for all unresolved items. Stop immediately on any
missing evidence, hash drift, schema ambiguity, failed negative test, failed
human-review requirement, or attempted execution/activation.

## 2. Problem and root cause

QOBS v1 requires 18 six-signal paths. AGY structured buckets provide only
`remaining_fraction`, `reset_time`, and `disabled`; they do not provide the
required six-signal paths. Receipt-v2 is closed. Therefore this protocol MUST
perform no conversion, completion, interpolation, or inference. A bucket
observation is admitted only as the explicitly defined structured observation,
never as QOBS data and never as a receipt-v2 object.

## 3. Approved decisions

These decisions are proposed for approval and are binding only after owner
sign-off:

1. A Gemini model is eligible only when both `gemini-weekly` and `gemini-5h`
   are present on the same model alias.
2. The eligibility comparator is strict: `remaining_fraction > 0.10` for both
   required Gemini buckets. Exactly `0.10` is ineligible.
3. A third-party model is not permanently barred by category. Every route must
   have an explicit model-ID mapping. Current `3p-weekly=0` and
   `3p-5h=disabled` MUST fail closed.
4. Retention excludes raw output, fraction, reset, paths, credentials, and any
   equivalent reconstructable provider payload. Retention keeps only digests,
   an availability enum, and minimum expiry/provenance control metadata.
5. No observation can satisfy QOBS v1, create a provider decision, authorize a
   dispatcher action, or substitute for receipt-v2.

## 4. Candidate closed artifacts

### Exact source allowlist for the next implementation lane

The committed QA manifest defines this exact source allowlist for the next
implementation lane. These are candidate paths only; this contract does not
assert that any source exists or that implementation is complete:

- `scripts/agy_bucket_admission.py`
- `scripts/multiagent_receipt_v3.py`
- `.agents/schemas/multiagent-agy-bucket-admission-v1.schema.json`
- `.agents/schemas/multiagent-dispatch-receipt-v3.schema.json`

Later scheduler, prompt, or capacity integration requires a fresh separate
HITL package, fresh hashes, explicit ownership release, and owner sign-off.

### Current-state ownership, hash, and provenance inventory

This table is the exact current-snapshot inventory for every candidate path in
this package. The stated snapshot time is `2026-08-28` (clock time not
recorded). For existing paths marked unstaged modified, the listed values are
`working_tree_snapshot` SHA-256 hashes captured at that snapshot time; they are
not HEAD blob hashes. For existing paths marked clean, the listed values are
clean/HEAD-compatible SHA-256 hashes at that snapshot. `ABSENT` means absent at
the snapshot above; it is not a claim that implementation is complete. For new
candidates, owner and provenance remain pending the QA baseline. The table is
an approval input, not an implementation authorization.

| Candidate path | Snapshot state | SHA-256 at snapshot (working_tree_snapshot for modified; clean/HEAD-compatible for clean) | Current owner / scope | Provenance / baseline disposition |
|---|---|---|---|---|
| `.agents/config/multiagent_model_policy.yaml` | Existing; clean; untouched | `1d1038599e3529fe1fd693a5b7e050c1d31e037d2aae9a8396ba6f83d3592ca0` | Frozen; read-only | Existing authoritative policy; no baseline edit |
| `scripts/agy_json_usage_sanitizer.py` | Existing; unstaged modified | `afc7cc6951944b806767c361501fa5934b5b9a24d20ad902a40302465a3a88ed` | Developer owns only after fresh scope check | Existing source candidate; fresh pre-edit hash and ownership release required |
| `scripts/multiagent_prompt_command.py` | Existing; unstaged modified | `6cd637271ec0b21dda1f0b0bb748496f7d45eb0d889ad13aa145c4201dd06cbb` | Excluded from this phase | Existing modified path; no provenance transfer or edit |
| `scripts/multiagent_ticket_scheduler.py` | Existing; unstaged modified | `1c935d2c660cc4a0cc476117647122336ac78a2b19f847b62b485550bd49c06e` | Excluded from this phase | Existing modified path; no provenance transfer or edit |
| `tests/test_agy_json_usage_sanitizer.py` | Existing; unstaged modified | `ec2e1bd4416a0a15c231e5b99a6ef81fc2ea4705fb757303ed23ce0b581a77ab` | Excluded; new test file is used | Existing modified test; excluded from this baseline |
| `tests/test_multiagent_receipt_schema.py` | Existing; clean | `65afda7dd7224f0cf58869fcd4cb09ac1ad3c73faa3f38e906f59a30d4bf32f0` | Frozen; read-only | Existing frozen receipt test; excluded from edits |
| `tests/test_quota_observation_contract.py` | Existing; clean | `6d5ff2a42d35c3facb4f32f43a907ae3f4eb8f38e477e8b2a0edee56fdd07e60` | Frozen; read-only | Existing frozen QOBS contract test; excluded from edits |
| `tests/test_quota_observation_integration.py` | Existing; unstaged modified | `ff03b49c7fc54abce48ee51679eb81ce999509755a6b0fce9dc356ed0192333a` | Frozen QOBS owner scope; excluded | Existing modified QOBS integration test; excluded from this phase |
| `.agents/schemas/multiagent-agy-bucket-observation-v1.schema.json` | New candidate; ABSENT | `ABSENT` | Developer owns protocol source after `TEST_BASELINE_VERIFIED`; pending baseline | New candidate; owner/provenance pending QA baseline |
| `.agents/schemas/multiagent-agy-bucket-observation-artifact-v1.schema.json` | New candidate; ABSENT | `ABSENT` | Developer owns protocol source after `TEST_BASELINE_VERIFIED`; pending baseline | New candidate; owner/provenance pending QA baseline |
| `.agents/schemas/multiagent-dispatch-receipt-v3.schema.json` | New candidate; ABSENT | `ABSENT` | Developer owns protocol source after `TEST_BASELINE_VERIFIED`; pending baseline | New candidate; owner/provenance pending QA baseline |
| `scripts/agy_bucket_admission_guard.py` | New candidate; ABSENT | `ABSENT` | Developer owns protocol source after `TEST_BASELINE_VERIFIED`; pending baseline | New candidate; owner/provenance pending QA baseline |
| `.agents/config/agy_bucket_admission_policy.json` | New candidate; ABSENT | `ABSENT` | Developer owns protocol source after `TEST_BASELINE_VERIFIED`; pending baseline | New candidate; owner/provenance pending QA baseline |
| `tests/test_agy_bucket_admission_sanitizer.py` | New candidate; ABSENT | `ABSENT` | QA owns baseline tests/manifest; pending baseline | New QA baseline candidate; red evidence and provenance pending |
| `tests/test_agy_bucket_admission_guard.py` | New candidate; ABSENT | `ABSENT` | QA owns baseline tests/manifest; pending baseline | New QA baseline candidate; red evidence and provenance pending |
| `tests/test_agy_bucket_admission_integration.py` | New candidate; ABSENT | `ABSENT` | QA owns baseline tests/manifest; pending baseline | New QA baseline candidate; red evidence and provenance pending |
| `tests/test_multiagent_receipt_v3_schema.py` | New candidate; ABSENT | `ABSENT` | QA owns baseline tests/manifest; pending baseline | New QA baseline candidate; red evidence and provenance pending |
| `plans/test_provenance/ticket-agy-bucket-admission-v1.json` | New candidate; ABSENT | `ABSENT` | QA owns baseline tests/manifest; pending baseline | New QA baseline manifest candidate; provenance pending |

HEAD blob hashes for modified files are intentionally not used as
before-mutation hashes. Immediately before any future mutation, a fresh exact
hash and ownership check is required for the target file; any drift or
ownership conflict blocks the mutation.

The documentation owner is BSA after source freeze. No owner may treat a
pending, absent, or modified path as proof of implementation. Any hash drift,
ownership conflict, or provenance gap blocks handoff.

The following four candidates are closed and require separate implementation
and QA approval:

- `scripts/agy_bucket_admission.py`
- `scripts/multiagent_receipt_v3.py`
- `.agents/schemas/multiagent-agy-bucket-admission-v1.schema.json`
- `.agents/schemas/multiagent-dispatch-receipt-v3.schema.json`

Before any source edit, verify a fresh SHA-256 and ownership release for the
target against the committed QA manifest. The existing sanitizer and all
working-tree paths in the inventory are not permission to edit QOBS,
receipt-v2, scheduler, prompt, or capacity code.

## 5. Protocol and data boundaries

The protocol name and version are exactly:

`horoconsultant.agy-bucket-admission.v1`

The guard MUST reject any object that is not explicitly identified as this
protocol and artifact version. It MUST reject QOBS-v1 objects, receipt-v2
objects, and unversioned or cross-protocol substitutions. It MUST fail closed
when required evidence is absent or contradictory.

Admission is observational only. It does not imply health, authorization,
capacity, availability beyond the permitted enum, provider reachability, or
execution permission. `healthy` MUST NOT be caller-controlled evidence.

## 6. Test-first baseline and ownership

The committed QA baseline manifest is authoritative. Its baseline files are
QA-owned:

| Baseline path | SHA-256 |
|---|---|
| `tests/test_agy_bucket_admission_sanitizer.py` | `dae35395e5e01064ffea5719ad644164afde75629e948edb4e0565d66708e5ac` |
| `tests/test_agy_bucket_admission_guard.py` | `f0042fbb434de8a2bc4ccea4b5437485747e88a2d4846fd88917bdac33718dd4` |
| `tests/test_agy_bucket_admission_integration.py` | `234a63b01c8a71df0f511085a3e15debe2ae65a2fd28b35155ccc45ac4e6cf02` |
| `tests/test_multiagent_receipt_v3_schema.py` | `de9c129a501a58586b3b03b44bc60a62df14fffcdc157eb401fb0fe2d4e4934b` |
| Manifest: `plans/test_provenance/ticket-agy-bucket-admission-v1.json` | `baseline_commit: acbe196bc4b93294ed5c35060907567e45f67ece` |

The manifest baseline parent is
`ecd37d71b89cbda6161a44626cf49ea063c3b5df`; `provenance_status: VERIFIED`.

Before any source edit under repository Rule 02, QA MUST create the baseline,
capture red evidence, record exact before hashes (or `ABSENT` markers) for
every baseline input and test file, record ownership and provenance, and use
the committed one test-only baseline commit above. No other commit is
authorized by this contract. The baseline red evidence is: `pytest` exit 2,
with four expected `ModuleNotFoundError` collection errors and no
provider/dispatcher execution. The baseline must prove that the candidate
behavior is not already implemented and must identify the owner and timestamp
for each evidence item. After the baseline, every source commit MUST carry a
`Test-Baseline` trailer referencing the verified baseline. The frozen QOBS
integration test MUST NOT be modified by this ticket. Existing receipt-v2 and
QOBS schemas remain immutable.

QA owns the baseline tests and manifest. Developer owns protocol source only
after `TEST_BASELINE_VERIFIED`. BSA owns this contract and related
documentation only after source freeze. Any owner, hash, or provenance
discrepancy blocks implementation handoff.

The later integration phase is a separate HITL decision. It may modify
scheduler, prompt, or capacity behavior only after fresh hashes, explicit
ownership release, and a new approval package.

## 7. Required negative-test matrix

The QA baseline MUST include failing cases for:

- missing, duplicate, and extra fields;
- invalid units;
- NaN and Infinity values;
- stale and future timestamps or reset values;
- alias, model, and bucket mismatch;
- disabled state and the strict threshold boundary (`0.10`);
- nonce replay and concurrency;
- raw retention of output, fraction, reset, paths, credentials, or equivalent
  payload;
- QOBS and receipt-v2 cross-protocol substitution;
- subprocess invocation when an artifact is invalid.

It MUST also demonstrate that `3p-weekly=0` and `3p-5h=disabled` fail closed,
that Gemini requires both buckets on the same alias, and that every third-party
route has an explicit model-ID mapping.

## 8. Explicit execution exclusions

```text
provider_execution: S5
dispatcher_execution: CLOSED
activation_prohibited: true
```

There is no provider retry or fallback. There is no deployment, push, or
commit, except the explicitly authorized QA-only baseline commit in Section 6.
There is no policy weakening. Invalid, stale, ambiguous, conflicting, or
low-consensus material is rejected or routed to human review; it is never
silently normalized.

## 9. HITL review and acceptance criteria

Conflict, low-consensus, and force-review cases MUST set
`required_human_review=True`. Before implementation handoff, the following
gate MUST pass:

`/hitl/scope-audit?source_domain=metaphysical-domain-engine`

with `summary.pass_gate_check=true`. Unresolved items remain blocked until
owner sign-off is recorded.

This document is not implementation authorization until all of the following
explicit approval gates pass: the current-state ownership/hash/provenance
inventory in Section 4 is complete, the QA red baseline and one test-only
baseline commit are recorded, the HITL scope audit passes with
`summary.pass_gate_check=true`, and owner sign-off is recorded for every
unresolved item.

Approval requires evidence that:

1. The protocol identifier is exact and immutable.
2. QOBS v1, receipt-v2, the frozen QOBS integration test, and all unrelated
   files remain unchanged.
3. The sanitizer pre-edit SHA-256 matches the required digest.
4. All four allowlisted candidate source paths and all five QA-owned baseline
   files are enumerated with owners, exact hashes, and provenance.
5. The baseline contains red evidence before source edits and was committed
   only through the authorized QA test-only baseline commit.
6. Strict Gemini dual-bucket eligibility and third-party explicit mapping are
   enforced fail closed.
7. Retention contains only the approved digest, enum, expiry, and provenance
   control metadata.
8. Every negative test in Section 7 passes, including no subprocess execution
   for invalid artifacts.
9. No provider, dispatcher, retry, fallback, scheduler, prompt, capacity,
   deployment, push, or activation action occurred.
10. HITL scope audit passed and every unresolved item has owner sign-off.

## 10. Later-phase blockers

The following blockers MUST remain visible and unresolved until a separate HITL
package addresses them:

- caller-controlled `healthy` evidence;
- reserve-gate timing;
- atomic queue, lease, and idempotency semantics;
- receipt-v3 binding.

Fresh hashes and ownership release are mandatory before any later integration
change. A failed blocker gate is a stop condition, not a reason to infer a
default or weaken policy.

## 11. Current evidence

- Committed QA baseline: `provenance_status: VERIFIED`.
- Red evidence: `pytest` exit 2, with four expected
  `ModuleNotFoundError` collection errors and no provider/dispatcher
  execution.
- This is baseline evidence only. It does not claim source exists, tests are
  green, or provide provider proof, AGY proof, dispatcher proof, activation
  proof, or approval.

## 12. Approval record

```text
status: DRAFT/PENDING_APPROVAL
source_domain: metaphysical-domain-engine
owner_sign_off: PENDING
hitl_scope_audit: PENDING
summary.pass_gate_check: PENDING
baseline_commit: acbe196bc4b93294ed5c35060907567e45f67ece
baseline_parent: ecd37d71b89cbda6161a44626cf49ea063c3b5df
provenance_status: VERIFIED
implementation_handoff: BLOCKED
activation_prohibited: true
```

No account email, raw provider output, conversation ID, credential, secret, or
provider-specific sensitive path may be added to this contract or its evidence.
