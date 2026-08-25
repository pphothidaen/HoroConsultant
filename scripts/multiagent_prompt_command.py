#!/usr/bin/env python3
"""Render and optionally execute account-routed Codex or AGY sub-agent prompts.

The account registry is explicit: an alias selects a configured CLI executable and
an optional CLI home directory.  No shell aliases, credentials, or login state are
inferred or modified.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
from typing import Any, Mapping, Sequence

import yaml


VALID_CLIS = {"codex", "agy"}
VALID_EFFORTS = {"low", "medium", "high", "xhigh", "max", "ultra"}
VALID_AGY_EFFORTS = {"low", "medium", "high"}
VALID_AGY_MODES = {"accept-edits", "plan"}
VALID_SANDBOXES = {"read-only", "workspace-write", "danger-full-access"}
VALID_HOME_ENV = {"codex": "CODEX_HOME", "agy": "AGY_HOME"}
VALID_RESULT_STATUSES = {"DONE", "BLOCKED", "NEEDS_HITL"}
# Configuration selects from this fixed, approved terminal-account set; it
# cannot grant an additional account alias execution authority.
GOVERNED_ACCOUNT_ALIASES = frozenset({"codex1", "codex2", "agy1", "agy2"})
RESULT_FIELDS = {
    "status",
    "scope_owned",
    "evidence",
    "findings",
    "changed_files",
    "residual_risk",
    "recommended_next_action",
}
SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
SAFE_COMMAND = re.compile(r"^(?:[A-Za-z0-9_.-]+|/[A-Za-z0-9_./-]+)$")
SAFE_SESSION_ID = re.compile(
    r"(?:child[-_ ]?(?:process|session)|(?:process|session)[-_ ]?id)\s*[:=]\s*"
    r"([A-Za-z0-9_.-]{1,128})",
    re.IGNORECASE,
)

DEFAULT_OWNERSHIP = "Only the files and responsibilities explicitly assigned in this prompt."
DEFAULT_BOUNDARIES = "Do not modify credentials, authentication state, or files outside ownership."
DEFAULT_EVIDENCE = "Return commands run, exit codes, and paths to resulting artifacts."
DEFAULT_STOP_CONDITION = (
    "Stop and report BLOCKED when authorization, credentials, or assigned scope is missing."
)
COORDINATION_SENTENCE = (
    "You are not alone in the codebase. Do not revert edits made by others; "
    "adjust your work to accommodate concurrent changes. Work only within the assigned ownership."
)

# A process-local guard prevents accidental duplicate dispatches while allowing
# separate invocations of this utility to use the same configured account.
_DISPATCHED_KEYS: set[str] = set()


class ConfigurationError(ValueError):
    """Raised when routing configuration or an override is invalid."""


@dataclass(frozen=True)
class Route:
    """Resolved role-to-account route."""

    role: str
    alias: str
    cli: str
    command: str
    home_env: str | None
    home_path: str | None
    model: str | None
    effort: str | None
    mode: str | None
    sandbox: str | bool | None


@dataclass(frozen=True)
class Invocation:
    """A shell-free subprocess invocation."""

    route: Route
    argv: tuple[str, ...]
    prompt_stdin: str
    cwd: str
    env_overrides: Mapping[str, str]


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ConfigurationError(f"{label} must be a mapping")
    return value


def _optional_safe_name(value: Any, label: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not SAFE_NAME.fullmatch(value):
        raise ConfigurationError(f"{label} contains unsupported characters")
    return value


def _expand_home_path(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise ConfigurationError("home_path must be a non-empty string")
    home = os.environ.get("HOME")
    if value == "${HOME}" or value.startswith("${HOME}/"):
        if not home:
            raise ConfigurationError("HOME is unavailable for ${HOME} expansion")
        value = home + value[len("${HOME}") :]
    if "$" in value or "~" in value:
        raise ConfigurationError("home_path supports only a leading ${HOME} expansion")
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise ConfigurationError("home_path must resolve to an absolute path")
    return str(path)


def load_config(path: str | os.PathLike[str]) -> Mapping[str, Any]:
    """Load a YAML routing configuration without interpreting custom YAML objects."""

    config_path = Path(path)
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    return _mapping(data, "configuration")


def resolve_route(
    config: Mapping[str, Any],
    role: str,
    *,
    alias_override: str | None = None,
    cli_override: str | None = None,
    model_override: str | None = None,
    effort_override: str | None = None,
) -> Route:
    """Resolve a role and validated orchestrator overrides into an account route."""

    roles = _mapping(config.get("roles"), "roles")
    accounts = _mapping(config.get("accounts"), "accounts")
    if set(accounts) - GOVERNED_ACCOUNT_ALIASES:
        raise ConfigurationError("accounts contains an alias outside the approved account alias allowlist")
    if role not in roles:
        raise ConfigurationError(f"unknown role: {role}")
    role_config = _mapping(roles[role], f"roles.{role}")

    configured_alias = role_config.get("alias")
    alias = configured_alias if alias_override is None else alias_override
    if not isinstance(alias, str) or not SAFE_NAME.fullmatch(alias):
        raise ConfigurationError("role alias is missing or invalid")
    if alias not in accounts:
        raise ConfigurationError(f"unknown account alias: {alias}")
    if alias not in GOVERNED_ACCOUNT_ALIASES:
        raise ConfigurationError(f"alias is outside the approved account alias allowlist: {alias}")
    account = _mapping(accounts[alias], f"accounts.{alias}")

    account_cli = account.get("cli")
    role_cli = role_config.get("cli", account_cli)
    cli = role_cli if cli_override is None else cli_override
    if cli not in VALID_CLIS:
        raise ConfigurationError(f"unsupported CLI: {cli}")
    if account_cli not in VALID_CLIS:
        raise ConfigurationError(f"accounts.{alias}.cli must be codex or agy")
    if cli != account_cli:
        raise ConfigurationError(
            f"account alias {alias} is registered for {account_cli}, not {cli}"
        )

    command = account.get("command", cli)
    if not isinstance(command, str) or not SAFE_COMMAND.fullmatch(command):
        raise ConfigurationError("account command must be one executable path without arguments")

    expected_home_env = VALID_HOME_ENV[cli]
    home_env = account.get("home_env")
    if home_env is not None and home_env != expected_home_env:
        raise ConfigurationError(f"{cli} accounts may set only {expected_home_env}")
    home_path = _expand_home_path(account.get("home_path"))
    if bool(home_env) != bool(home_path):
        raise ConfigurationError("home_env and home_path must be configured together")

    model = _optional_safe_name(
        role_config.get("model") if model_override is None else model_override,
        "model",
    )
    effort = _optional_safe_name(
        role_config.get("effort") if effort_override is None else effort_override,
        "effort",
    )
    if effort is not None and effort not in VALID_EFFORTS:
        raise ConfigurationError(f"unsupported reasoning effort: {effort}")
    mode = _optional_safe_name(role_config.get("mode"), "mode")
    raw_sandbox = role_config.get("sandbox")
    if cli == "agy":
        if effort is not None and effort not in VALID_AGY_EFFORTS:
            raise ConfigurationError(f"unsupported AGY reasoning effort: {effort}")
        if mode is not None and mode not in VALID_AGY_MODES:
            raise ConfigurationError(f"unsupported AGY mode: {mode}")
        if raw_sandbox is not None and not isinstance(raw_sandbox, bool):
            raise ConfigurationError("AGY sandbox must be true or false")
        sandbox: str | bool | None = raw_sandbox
    else:
        sandbox = _optional_safe_name(raw_sandbox, "sandbox")
        if sandbox is not None and sandbox not in VALID_SANDBOXES:
            raise ConfigurationError(f"unsupported sandbox: {sandbox}")

    return Route(
        role=role,
        alias=alias,
        cli=cli,
        command=command,
        home_env=home_env,
        home_path=home_path,
        model=model,
        effort=effort,
        mode=mode,
        sandbox=sandbox,
    )


def render_prompt(
    *,
    objective: str,
    ownership: str = DEFAULT_OWNERSHIP,
    boundaries: str = DEFAULT_BOUNDARIES,
    evidence: str = DEFAULT_EVIDENCE,
    stop_condition: str = DEFAULT_STOP_CONDITION,
) -> str:
    """Render the common orchestration and result contract."""

    if not objective.strip():
        raise ConfigurationError("objective must not be empty")
    return "\n".join(
        [
            "You are a sub-agent working under an orchestrator.",
            "",
            f"Objective: {objective}",
            f"Ownership: {ownership}",
            f"Boundaries: {boundaries}",
            f"Evidence required: {evidence}",
            f"Stop condition: {stop_condition}",
            "",
            f"Coordination: {COORDINATION_SENTENCE}",
            "",
            "Result contract:",
            "- status: DONE | BLOCKED | NEEDS_HITL",
            "- scope_owned: files or responsibilities assigned",
            "- evidence: commands, outcomes, and artifact references",
            "- findings: verified conclusions",
            "- changed_files: changed paths or none",
            "- residual_risk: remaining risk or none",
            "- recommended_next_action: one concrete next action",
        ]
    )


def build_invocation(route: Route, prompt: str, project_dir: str | os.PathLike[str]) -> Invocation:
    """Build exact argv and process-local environment overrides; never a shell command."""

    project_path = Path(project_dir).resolve()
    if not project_path.exists() or not project_path.is_dir():
        raise ConfigurationError("project_dir must exist and be a directory")
    cwd = str(project_path)
    argv = [route.command]
    if route.cli == "codex":
        argv.extend(["exec", "-C", cwd])
        if route.sandbox:
            argv.extend(["-s", route.sandbox])
        if route.model:
            argv.extend(["-m", route.model])
        if route.effort:
            argv.extend(["-c", f'model_reasoning_effort="{route.effort}"'])
        argv.append("-")
    else:
        if route.mode:
            argv.extend(["--mode", route.mode])
        if route.sandbox:
            argv.append("--sandbox")
        if route.model:
            argv.extend(["--model", route.model])
        if route.effort:
            argv.extend(["--effort", route.effort])
        argv.extend(["--print", "--input-format", "text", "--output-format", "json"])

    env_overrides: dict[str, str] = {}
    if route.home_env and route.home_path:
        env_overrides[route.home_env] = route.home_path
    return Invocation(
        route=route,
        argv=tuple(argv),
        prompt_stdin=prompt,
        cwd=cwd,
        env_overrides=env_overrides,
    )


def _dispatch_key(invocation: Invocation) -> str:
    """Return a stable, non-secret identity for one exact dispatch request."""

    material = json.dumps(
        {
            "argv": invocation.argv,
            "cwd": invocation.cwd,
            "prompt": invocation.prompt_stdin,
            "env": sorted(invocation.env_overrides.items()),
        },
        ensure_ascii=False,
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def normalize_result(
    payload: str | bytes | Mapping[str, Any] | None,
    *,
    returncode: int = 0,
) -> dict[str, Any]:
    """Validate and normalize the mandatory sub-agent result contract.

    The CLI must emit one JSON object.  In particular, status-like text or a
    missing evidence section is never silently treated as a successful result.
    """

    if payload is None or payload == "" or payload == b"":
        return {
            "status": "BLOCKED",
            "scope_owned": "unspecified",
            "evidence": {
                "commands": [],
                "outcomes": [
                    f"subprocess exit code: {returncode}",
                    "sub-agent returned empty stdout; result contract was not emitted",
                ],
                "artifacts": [],
            },
            "findings": ["No canonical sub-agent result was available to verify."],
            "changed_files": [],
            "residual_risk": "result contract compliance is unverified",
            "recommended_next_action": "rerun the sub-agent and require a JSON result with status and evidence",
        }
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8", errors="replace")
    if isinstance(payload, str):
        try:
            value = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ConfigurationError("sub-agent result is not valid JSON") from exc
    else:
        value = payload
    result = _mapping(value, "sub-agent result")
    missing = RESULT_FIELDS - set(result)
    if missing:
        raise ConfigurationError(
            "sub-agent result missing fields: " + ", ".join(sorted(missing))
        )
    status = str(result["status"]).strip().upper().replace("-", "_").replace(" ", "_")
    if status not in VALID_RESULT_STATUSES:
        raise ConfigurationError("sub-agent result status must be DONE, BLOCKED, or NEEDS_HITL")
    if not isinstance(result["scope_owned"], (str, list, tuple)) or not result["scope_owned"]:
        raise ConfigurationError("sub-agent result scope_owned must be non-empty")
    evidence = _mapping(result["evidence"], "sub-agent result evidence")
    for key in ("commands", "outcomes", "artifacts"):
        if key not in evidence or not isinstance(evidence[key], list):
            raise ConfigurationError(f"sub-agent result evidence.{key} must be a list")
    if not isinstance(result["findings"], (str, list, tuple)):
        raise ConfigurationError("sub-agent result findings must be text or a list")
    if not isinstance(result["changed_files"], (str, list, tuple)):
        raise ConfigurationError("sub-agent result changed_files must be text or a list")
    if not isinstance(result["residual_risk"], str) or not result["residual_risk"].strip():
        raise ConfigurationError("sub-agent result residual_risk must be non-empty text")
    if (
        not isinstance(result["recommended_next_action"], str)
        or not result["recommended_next_action"].strip()
    ):
        raise ConfigurationError("sub-agent result recommended_next_action must be non-empty text")
    normalized = dict(result)
    normalized["status"] = status
    normalized["evidence"] = dict(evidence)
    return normalized


def validate_execution_preflight(invocation: Invocation) -> None:
    """Require a runnable executable and existing configured CLI home before launch."""

    executable = invocation.route.command
    if "/" in executable:
        executable_path = Path(executable)
        if not executable_path.is_file() or not os.access(executable_path, os.X_OK):
            raise ConfigurationError(f"configured {invocation.route.cli} executable is unavailable")
    elif shutil.which(executable) is None:
        raise ConfigurationError(f"configured {invocation.route.cli} executable is unavailable")
    if invocation.route.home_path and not Path(invocation.route.home_path).is_dir():
        raise ConfigurationError(f"configured {invocation.route.home_env} directory does not exist")


def execute_invocation(invocation: Invocation) -> subprocess.CompletedProcess[str]:
    """Execute argv directly with a process-local environment and no shell."""

    validate_execution_preflight(invocation)
    dispatch_key = _dispatch_key(invocation)
    if dispatch_key in _DISPATCHED_KEYS:
        raise ConfigurationError("duplicate dispatch rejected for this process")
    _DISPATCHED_KEYS.add(dispatch_key)
    env = os.environ.copy()
    env.pop("CODEX_HOME", None)
    env.pop("AGY_HOME", None)
    env.update(invocation.env_overrides)
    return subprocess.run(
        list(invocation.argv),
        cwd=invocation.cwd,
        env=env,
        input=invocation.prompt_stdin,
        text=True,
        check=False,
        shell=False,
    )


def _redact_preview(value: str, invocation: Invocation) -> str:
    """Redact local paths from dry-run output while retaining argv structure."""

    redacted = value.replace(invocation.cwd, "<PROJECT_DIR>")
    for path in invocation.env_overrides.values():
        redacted = redacted.replace(path, "<CLI_HOME>")
    return redacted


def _safe_execution_evidence(
    result: subprocess.CompletedProcess[str],
) -> dict[str, Any]:
    """Return non-secret proof produced by an actual completed child process."""

    stdout = result.stdout or ""
    stderr = result.stderr or ""
    evidence: dict[str, Any] = {
        "source": "actual-subprocess-result",
        "returncode": result.returncode,
        # A digest is safe to retain even if a provider response contains
        # sensitive text; it proves a non-empty child result without logging it.
        "child_result_sha256": hashlib.sha256(stdout.encode("utf-8")).hexdigest(),
        "child_result_bytes": len(stdout.encode("utf-8")),
    }
    session_match = SAFE_SESSION_ID.search(stderr)
    if session_match:
        evidence["process_or_session_id"] = session_match.group(1)
    return evidence


def _canonical_blocked_result(
    route: Route,
    *,
    failure_class: str,
    recommended_next_action: str,
) -> dict[str, Any]:
    """Create a safe canonical record for a failed preflight/start attempt."""

    return {
        "status": "BLOCKED",
        "alias": route.alias,
        "execution_evidence": {
            "source": "no-child-ran",
            "failure_class": failure_class,
        },
        "scope_owned": "configured terminal dispatch",
        "evidence": {
            "commands": [],
            "outcomes": ["configured child process did not start"],
            "artifacts": [],
        },
        "findings": ["No actual child run is claimed."],
        "changed_files": [],
        "residual_risk": "the selected account alias could not execute the bounded task",
        "recommended_next_action": recommended_next_action,
    }


def _completed_result(
    normalized: Mapping[str, Any], result: subprocess.CompletedProcess[str]
) -> dict[str, Any]:
    """Attach subprocess proof and prevent unsupported DONE claims."""

    completed = dict(normalized)
    execution_evidence = _safe_execution_evidence(result)
    completed["execution_evidence"] = execution_evidence
    if completed["status"] == "DONE" and (
        result.returncode != 0 or not execution_evidence["child_result_bytes"]
    ):
        completed["status"] = "BLOCKED"
        completed["residual_risk"] = "child execution did not provide successful result evidence"
        completed["recommended_next_action"] = (
            "rerun the selected alias and retain a non-empty child result"
        )
    return completed


def _redact_result_value(value: Any, invocation: Invocation) -> Any:
    """Prevent child-controlled output from echoing prompt, homes, or secrets."""

    if isinstance(value, str):
        redacted = value.replace(invocation.prompt_stdin, "<PROMPT_REDACTED>")
        redacted = _redact_preview(redacted, invocation)
        # Keep the filter deliberately narrow so ordinary findings remain
        # useful, while credential-shaped values are never emitted by this
        # governance command.
        redacted = re.sub(
            r"(?i)\b(?:token|cookie|api[_-]?key|authorization)\s*[:=]\s*[^\s,;]+",
            "<SECRET_REDACTED>",
            redacted,
        )
        return redacted
    if isinstance(value, list):
        return [_redact_result_value(item, invocation) for item in value]
    if isinstance(value, tuple):
        return [_redact_result_value(item, invocation) for item in value]
    if isinstance(value, Mapping):
        return {str(key): _redact_result_value(item, invocation) for key, item in value.items()}
    return value


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="Path to PromptCommand YAML")
    parser.add_argument("--role", required=True, help="Configured orchestration role")
    parser.add_argument("--objective", required=True)
    parser.add_argument("--ownership", default=DEFAULT_OWNERSHIP)
    parser.add_argument("--boundaries", default=DEFAULT_BOUNDARIES)
    parser.add_argument("--evidence", default=DEFAULT_EVIDENCE)
    parser.add_argument("--stop-condition", default=DEFAULT_STOP_CONDITION)
    parser.add_argument("--project-dir", default=".")
    parser.add_argument("--alias", help="Override with another configured account alias")
    parser.add_argument("--cli", choices=sorted(VALID_CLIS), help="Validated CLI override")
    parser.add_argument("--model", help="Validated model override")
    parser.add_argument("--effort", choices=sorted(VALID_EFFORTS))
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--print-command", action="store_true", help="Render only (default)")
    action.add_argument("--execute", action="store_true", help="Run the rendered argv")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        config = load_config(args.config)
        route = resolve_route(
            config,
            args.role,
            alias_override=args.alias,
            cli_override=args.cli,
            model_override=args.model,
            effort_override=args.effort,
        )
        prompt = render_prompt(
            objective=args.objective,
            ownership=args.ownership,
            boundaries=args.boundaries,
            evidence=args.evidence,
            stop_condition=args.stop_condition,
        )
        invocation = build_invocation(route, prompt, args.project_dir)
    except (ConfigurationError, OSError, yaml.YAMLError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2

    argv_preview = [_redact_preview(arg, invocation) for arg in invocation.argv]
    argv_preview.append("<PROMPT_STDIN>")
    rendered = {
        "status": "rendered-route-not-execution-proof",
        "role": route.role,
        "alias": route.alias,
        "cli": route.cli,
        "cwd": "<PROJECT_DIR>",
        "env_keys": sorted(invocation.env_overrides),
        "argv": argv_preview,
        "command": shlex.join(argv_preview),
    }
    print(json.dumps(rendered, ensure_ascii=False, indent=2))
    if not args.execute:
        print("[OK] Dry-run only; no subprocess was started.")
        return 0

    try:
        result = execute_invocation(invocation)
    except (ConfigurationError, OSError) as exc:
        print(
            json.dumps(
                _canonical_blocked_result(
                    route,
                    failure_class="executable-unavailable-or-preflight-failed",
                    recommended_next_action=(
                        "verify the selected alias CLI installation and retry the same bounded task"
                    ),
                ),
                ensure_ascii=False,
                indent=2,
            )
        )
        # Do not expose the exception: it may contain account-home or host
        # details.  The canonical record above is the operator-facing outcome.
        print(f"[ERROR] Unable to start configured {route.cli} executable.", file=sys.stderr)
        return 127
    try:
        normalized = normalize_result(result.stdout, returncode=result.returncode)
    except ConfigurationError as exc:
        print(
            json.dumps(
                _canonical_blocked_result(
                    route,
                    failure_class="invalid-child-result-contract",
                    recommended_next_action="rerun the selected alias and require the JSON result contract",
                ),
                ensure_ascii=False,
                indent=2,
            )
        )
        print("[ERROR] Invalid sub-agent result contract.", file=sys.stderr)
        return 3
    completed = _completed_result(normalized, result)
    print(json.dumps(_redact_result_value(completed, invocation), ensure_ascii=False, indent=2))
    if result.returncode == 0:
        print("[OK] Sub-agent command completed.")
    else:
        print(f"[ERROR] Sub-agent command exited with code {result.returncode}.", file=sys.stderr)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
