# Reusable Multi-agent PromptCommand

This template lets an orchestrator render one ownership-scoped prompt and route it to a registered Codex CLI or AGY CLI account. It is project-agnostic, dry-run by default, invokes no shell, and never infers credentials or changes authentication state.

## Copy into another project

Copy these files while preserving their relative paths:

- `scripts/multiagent_prompt_command.py`
- `.agents/config/multiagent_prompt_command.example.yaml`

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

## Dry-run examples

Dry-run is the default. `--print-command` is available for explicitness. Output is structured JSON and says `rendered-route-not-execution-proof`. It replaces the prompt with `<PROMPT_STDIN>` and prints only environment-variable names, never the prompt, objective, or account-home value.

```bash
python scripts/multiagent_prompt_command.py --config .agents/config/multiagent_prompt_command.yaml --role implementation --objective "Implement ticket T-101" --ownership "src/widget.py and tests/test_widget.py" --print-command

python scripts/multiagent_prompt_command.py --config .agents/config/multiagent_prompt_command.yaml --role implementation --alias codex2 --objective "Fix the parser" --ownership "src/parser.py" --evidence "Focused pytest and git diff"

python scripts/multiagent_prompt_command.py --config .agents/config/multiagent_prompt_command.yaml --role research --alias agy1 --objective "Review primary-source constraints" --ownership "Read-only report"

python scripts/multiagent_prompt_command.py --config .agents/config/multiagent_prompt_command.yaml --role qa_review --alias agy2 --objective "Audit release evidence" --ownership "Read-only verification"
```

Inspect the rendered route before adding `--execute`. Execution uses `subprocess.run(argv, shell=False, input=prompt)` and inherits the current environment except for the process-local CLI home override. Codex consumes stdin through its `-` prompt argument. AGY consumes a one-line NDJSON `user` event through `--input-format stream-json --output-format stream-json`; PromptCommand validates the terminal AGY event and then validates its `response` against the shared JSON result contract. Prompt content therefore never enters the process list. Execution requires both the executable and configured CLI-home directory to exist; dry-run remains portable and does not require the account directory.

```bash
python scripts/multiagent_prompt_command.py --config .agents/config/multiagent_prompt_command.yaml --role implementation --objective "Implement ticket T-101" --ownership "src/widget.py and tests/test_widget.py" --execute
```

## Orchestrator and quota guidance

Route bounded implementation, QA, and research work to accounts with suitable remaining quota. Reserve the current orchestrator session for decomposition, conflict resolution, acceptance decisions, and synthesis. Prefer high-remaining five-hour and weekly pools, avoid splitting ownership of the same file across accounts, and re-check provider-reported quota before a large dispatch.

Quota numbers are planning inputs only. PromptCommand does not query quotas, authenticate accounts, or guarantee which human account a CLI home currently represents. A rendered alias, a Hermes routing label, or YAML configuration is not proof of account execution. Execution evidence must include the spawned command's result, provider/session telemetry where available, and the sub-agent's standard result contract.

Hermes can consume the same role-to-alias policy, but Hermes must have its own running gateway, authenticated provider profiles, and audit telemetry. Without those runtime controls, a Hermes alias remains a configuration label.

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

## Final closure checklist

- [ ] Ticket acceptance criteria and owner are recorded in `PROJECT_TASKS.md` and `plans/plan.md`.
- [ ] Child result, attempt count, timestamp, safe quota/account status, and evidence links are attached.
- [ ] No secret values, credentials, source, tests, or external systems were changed without explicit scope.
- [ ] Required rule/skill/catalog mirrors are synchronized and the ecosystem sync check passes.
- [ ] Any unresolved permission, credential, billing, ownership, or high-impact decision is marked `NEEDS_HITL`.
