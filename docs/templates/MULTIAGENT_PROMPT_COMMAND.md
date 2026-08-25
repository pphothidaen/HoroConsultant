# Reusable Multi-agent PromptCommand

This template lets an orchestrator render one ownership-scoped prompt and route it to a registered Codex CLI or AGY CLI account. It is project-agnostic, dry-run by default, invokes no shell, and never infers credentials or changes authentication state.

## Copy into another project

Copy these files while preserving their relative paths:

- `scripts/multiagent_prompt_command.py`
- `.agents/config/multiagent_prompt_command.example.yaml`
- `.agents/config/multiagent_model_policy.yaml`
- `.agents/schemas/multiagent-work-result-v2.schema.json`
- `.agents/schemas/multiagent-dispatch-decision-v1.schema.json`
- `.agents/schemas/multiagent-dispatch-receipt-v2.schema.json`
- `.agents/schemas/multiagent-dispatch-receipt-v1.schema.json`

Install PyYAML in the target project's environment, copy the example to a project-local configuration, and replace the example home paths with existing CLI homes. Do not put tokens, cookies, emails, or passwords in YAML.

```bash
python -m pip install PyYAML
cp .agents/config/multiagent_prompt_command.example.yaml .agents/config/multiagent_prompt_command.yaml
```

The names `codex1`, `codex2`, `agy1`, and `agy2` may be zsh functions on a workstation. PromptCommand deliberately does not call those functions. Each account selects the real `codex` or `agy` executable and supplies only its configured `CODEX_HOME` or `AGY_HOME` to that child process. `${HOME}` is the sole supported environment expansion.

## Configuration model

```yaml
accounts:
  codex1:
    cli: codex
    command: codex
    home_env: CODEX_HOME
    home_path: ${HOME}/.ai-accounts/codex/account1
    allow_provider_swap: false  # set true to permit agy CLI via this alias
  agy1:
    cli: agy
    command: agy
    home_env: AGY_HOME
    home_path: ${HOME}/.ai-accounts/agy/account1
roles:
  implementation:
    alias: codex1
    cli: codex
    model: gpt-5.6-luna
    effort: medium
    sandbox: workspace-write
  research:
    alias: agy1
    cli: agy
    model: Gemini 3.7 Flash (High)
    mode: plan
    sandbox: true
```

An orchestrator may override `--alias`, `--cli`, `--model`, or `--effort`. The alias must already exist in `accounts`, and its registered CLI must match the selected CLI. This prevents an account label from silently selecting unrelated credentials.

When `allow_provider_swap: true` is set on an account, the role or `--cli` override may select the other provider. The effective `home_env` and adapter are derived from the **effective CLI**, not the registered account CLI. This is fail-closed: absent or `false` preserves the strict mismatch error.


## Dry-run examples

Dry-run is the default. `--print-command` is available for explicitness. Output is structured JSON and says `rendered-route-not-execution-proof`. It replaces the prompt with `<PROMPT_STDIN>` and prints only environment-variable names, never the prompt, objective, or account-home value.

```bash
python scripts/multiagent_prompt_command.py --config .agents/config/multiagent_prompt_command.yaml --role implementation --objective "Implement ticket T-101" --ownership "src/widget.py and tests/test_widget.py" --print-command

python scripts/multiagent_prompt_command.py --config .agents/config/multiagent_prompt_command.yaml --role implementation --alias codex2 --objective "Fix the parser" --ownership "src/parser.py" --evidence "Focused pytest and git diff"

python scripts/multiagent_prompt_command.py --config .agents/config/multiagent_prompt_command.yaml --role research --alias agy1 --objective "Review primary-source constraints" --ownership "Read-only report"

python scripts/multiagent_prompt_command.py --config .agents/config/multiagent_prompt_command.yaml --role qa_review --alias agy2 --objective "Audit release evidence" --ownership "Read-only verification"
```

Inspect the rendered route before adding `--execute`. Legacy invocations remain
dry-run compatible, while v2 execution requires `--decision` and records
`--attempt-id` (default `1`). Codex emits JSONL under `--json
--output-schema`; AGY consumes a one-line NDJSON `user` event and emits typed
`init`, `step_update`, and terminal `result` events under its stream-JSON mode.
PromptCommand applies the shared WorkResult schema and rejects malformed,
missing, duplicate, or ambiguous terminal events rather than inferring a result
from provider prose. The prompt stays on stdin and never enters the process
list. Execution also requires the executable and configured CLI-home directory
to exist; dry-run remains portable and does not require the account directory.

```bash
python scripts/multiagent_prompt_command.py --config .agents/config/multiagent_prompt_command.yaml --role implementation --objective "Implement ticket T-101" --ownership "src/widget.py and tests/test_widget.py" --decision dispatch-decision.yaml --attempt-id 1 --execute
```

Executable runtime configuration is opt-in. A non-example config must declare
the protocol approval below. For `work_mode: read_only`, a Codex role must also
resolve to `sandbox: read-only`; an AGY role must resolve to `mode: plan` with
`sandbox: true`. Missing approval, an example filename, or a writable or
ambiguous sandbox fails before the provider process starts.

```yaml
runtime:
  approved_for_execution: true
  protocol_version: 2
```

## Orchestrator and quota guidance

Route bounded implementation, QA, and research work to accounts with suitable remaining quota. Reserve the current orchestrator session for decomposition, conflict resolution, acceptance decisions, and synthesis. Prefer high-remaining five-hour and weekly pools, avoid splitting ownership of the same file across accounts, and re-check provider-reported quota before a large dispatch.

### Maximum useful parallelism

Use available slots for independent, evidence-bearing lanes; do not fill them
with redundant, stale, speculative, dependency-blocked, or ownership-conflicting
work. A role may have multiple instances and a child may create another bounded
lane only within the total slot limit. Decompose into the smallest coherent task
without artificial fragmentation. After reserving each lane's file/module
ownership, recompute Rule 11 before selecting another; reuse released slots for
the next eligible independent lane.

For a single-file change, one source editor may run alongside a read-only
QA-prep or reviewer. Final QA and release decisions wait for source freeze and
declared dependencies. Live status must include active lanes, owned scope,
waits/blockers, and `active/available` slots. Capacity never overrides quota,
HITL, dependency, ownership, external-action, or receipt-proof gates.

Quota numbers are planning inputs only. PromptCommand does not query quotas, authenticate accounts, or guarantee which human account a CLI home currently represents. A rendered alias, a Hermes routing label, or YAML configuration is not proof of account execution. Execution evidence must include the spawned command's result, provider/session telemetry where available, and the sub-agent's standard result contract.

Hermes can consume the same role-to-alias policy, but Hermes must have its own running gateway, authenticated provider profiles, and audit telemetry. Without those runtime controls, a Hermes alias remains a configuration label.

## Adaptive model and effort decision

Before `--execute`, the orchestrator must supply a Rule 18 versioned
`DispatchDecision`: ticket/phase and lane, semantic ranks for scope,
complexity, risk, ambiguity, and evidence, non-secret quota band, selected
provider/model/effort, minimum floor, policy version, root-medium state,
rationale, and normalized decision digest. The dispatcher ticket owns the CLI
arguments/schema enforcement; this template documents the required handoff.

The maximum rank sets the floor. Quota may select only a catalog-approved
equal-or-stronger provider profile, never silently downgrade it. Critical risk,
unresolved high ambiguity, required human review, unknown quota for broad work,
unsupported capability, or an unconfirmed root-medium gate is `BLOCKED` or
`NEEDS_HITL`. Static role metadata, aliases, rendered commands, and dry-runs
are routing intent only; bind the policy version and digest to the actual route,
receipt, and child result for runtime proof. The historical dry-run
`dispatch_receipt` key is retained for consumers, but its value is route intent,
not an `ExecutionReceipt`.

## Ticket, retry, and HITL fields

Every rendered prompt should carry the ticket ID, objective, one-editor file
ownership, explicit exclusions, non-secret account/provider and quota status,
evidence expected, and stop condition. The child must return `DONE`, `BLOCKED`,
or `NEEDS_HITL` with the standard result fields below. A retry is for the same
bounded actionable failure only; record the attempt number and exact evidence.
After three consecutive failed remediation attempts, or immediately for
credentials, permissions, billing, production mutation, ownership conflict, or
high-impact judgment, pause and request HITL with the exact decision or safe
operator command. Do not infer execution from a rendered command.

## Safety and result contract

Every prompt includes explicit ownership, boundaries, evidence, a stop condition, the concurrent-work coordination warning, and this result structure:

- `status: DONE | BLOCKED | NEEDS_HITL`
- `scope_owned`
- `evidence`
- `findings`
- `changed_files`
- `residual_risk`
- `recommended_next_action`

Unknown roles/accounts, mismatched CLIs, unsupported options, arbitrary environment variables, and unsafe home expansions fail before subprocess creation. PromptCommand never runs login/logout commands and never writes CLI authentication files.

Successful v2 parsing returns two independently validated objects:

- `execution_receipt`: protocol/ticket/attempt identity, provider adapter,
  objective/ownership, safe quota state, timestamps and transport status, raw
  output byte count/SHA-256, and normalized result SHA-256.
- `work_result`: exactly the seven standard result fields above.

The dispatcher rejects identity or digest disagreement, additional or missing
contract fields, secret-shaped content, exit zero without a valid result, and a
nonzero exit paired with `DONE`. A nonzero exit may retain a receipt only when
the native adapter returns a schema-valid `BLOCKED` or `NEEDS_HITL` result.

### Public outcome and portable-evidence boundary

The public `ExecutionOutcome` is validated in-process. Its public
`stdout`/`stderr` are elided. Consequently, the receipt, WorkResult, and public
outcome are not an independently portable or offline-verifiable evidence
bundle. `portable=True` does not change that: any portable/offline verification
claim still requires a separately retained, trusted, exact raw-stdout record.
No approved private retention channel currently exists. Never restore, log, or
persist raw streams to bypass this boundary.

For a successful AGY result, report **validated in-process only**. Do not claim
portable verification, offline verification, or receipt-only verification. This
is a Medium residual risk. An encrypted, access-controlled raw-output sidecar
is only a future design option requiring separate scope, retention/trust
design, and HITL; it is not implemented by PromptCommand.

### ExecutionReceipt contract: receipt-v2 for new governed work

`result_contract.receipt_schema` selects
`multiagent-dispatch-receipt-v2.schema.json` for every newly governed
execution receipt. Receipt-v1 is retained only at
`result_contract.legacy_receipt_schema` for explicit legacy handling. Do not
change receipt-v1 identity, reinterpret a historical v1 field under v2
semantics, convert a historical receipt to v2, or retroactively validate one
as v2. Privacy migration may preserve terminal replay state and the original
record digest, but that does not create a v2 receipt; only a new governed
execution can emit one.

Receipt-v2 carries a closed, privacy-sanitized embedded `claim_proof`.
`dispatch_claim_sha256` and `claim_proof_sha256` are both the SHA-256 of the
canonical embedded ClaimProof and must be equal. Neither is a digest of the
full persisted claim record. `claim_proof_scope` is exactly
`digest-integrity-not-authenticity`: the embedded proof supports portable
integrity checks, while authenticity requires the separate strict-local
claim-store validation path.

The Rule 11 scheduling selection is bound twice: the top-level
`scheduling_snapshot_sha256` and the ClaimProof value must match. Receipt and
ClaimProof timestamps are UTC RFC 3339 values using the mandatory `Z` suffix.
For AGY receipts, the sanitized native `process_or_session_id` is mandatory
and must be bound to parsed native evidence; it is not required for compatible
Codex receipts. Do not place raw prompts, ownership paths, provider output, or
sensitive identifiers in a receipt, claim proof, or status evidence.

## Final closure checklist

- [ ] Ticket acceptance criteria and owner are recorded in `PROJECT_TASKS.md` and `plans/plan.md`.
- [ ] Child result, attempt count, timestamp, safe quota/account status, and evidence links are attached.
- [ ] No secret values, credentials, source, tests, or external systems were changed without explicit scope.
- [ ] Required rule/skill/catalog mirrors are synchronized and the ecosystem sync check passes.
- [ ] Any unresolved permission, credential, billing, ownership, or high-impact decision is marked `NEEDS_HITL`.
