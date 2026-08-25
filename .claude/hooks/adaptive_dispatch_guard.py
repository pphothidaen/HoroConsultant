#!/usr/bin/env python3
"""Fail-closed adaptive decision check used by the Claude root guard."""

from __future__ import annotations

import importlib.util
import io
import re
import shlex
import sys
from contextlib import redirect_stderr
from pathlib import Path
from types import ModuleType
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[2]
DISPATCHER_PATH = ROOT_DIR / "scripts" / "multiagent_prompt_command.py"
SHELL_CONTROL = frozenset({";", "&&", "||", "|", "&", "(", ")"})
REDIRECTION = frozenset({">", ">>", "<", "<<"})
FORBIDDEN_SHELL_TEXT = re.compile(r"[;&|<>`$(){}\r\n]")


def _tokens(command: str) -> list[str]:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|()<>")
    lexer.whitespace_split = True
    lexer.commenters = ""
    return list(lexer)


def _is_dispatcher(token: str) -> bool:
    normalized = token.replace("\\", "/")
    return normalized == "scripts/multiagent_prompt_command.py" or normalized.endswith(
        "/scripts/multiagent_prompt_command.py"
    )


def _execute_argvs(command: str) -> tuple[list[list[str]], bool]:
    tokens = _tokens(command)
    invocations: list[list[str]] = []
    dispatcher_indices: list[int] = []
    for index, token in enumerate(tokens):
        if not _is_dispatcher(token):
            continue
        dispatcher_indices.append(index)
        stop = next(
            (
                item
                for item in range(index + 1, len(tokens))
                if tokens[item] in SHELL_CONTROL | REDIRECTION
            ),
            len(tokens),
        )
        argv = tokens[index + 1 : stop]
        if "--execute" in argv:
            invocations.append(argv)
    prefix = tokens[: dispatcher_indices[0]] if dispatcher_indices else []
    interpreter_only = not prefix or (
        len(prefix) == 1
        and re.fullmatch(r"python(?:3(?:\.\d+)?)?", Path(prefix[0]).name) is not None
    )
    dispatch_only = bool(
        len(invocations) == 1
        and len(dispatcher_indices) == 1
        and interpreter_only
        and not any(token in SHELL_CONTROL | REDIRECTION for token in tokens)
    )
    return invocations, dispatch_only


def _load_dispatcher() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "horo_multiagent_prompt_command", DISPATCHER_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("shared dispatcher validator is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    scripts_dir = str(DISPATCHER_PATH.parent)
    inserted = scripts_dir not in sys.path
    if inserted:
        sys.path.insert(0, scripts_dir)
    try:
        spec.loader.exec_module(module)
    finally:
        if inserted:
            sys.path.remove(scripts_dir)
    return module


def _resolve(value: str, cwd: Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else cwd / path


def _validate(argv: list[str], event: dict[str, Any]) -> None:
    dispatcher = _load_dispatcher()
    with redirect_stderr(io.StringIO()):
        try:
            args = dispatcher._parser().parse_args(argv)
        except SystemExit as exc:
            raise ValueError("execute arguments are incomplete or invalid") from exc
    if not args.decision:
        raise ValueError("multi-agent execute requires --decision")
    if not args.scheduling_snapshot:
        raise ValueError("multi-agent execute requires --scheduling-snapshot")

    event_cwd = event.get("cwd")
    cwd = Path(event_cwd) if isinstance(event_cwd, str) and event_cwd else Path.cwd()
    config_path = _resolve(args.config, cwd)
    config = dispatcher.load_config(config_path)
    decision = dispatcher.load_dispatch_decision(_resolve(args.decision, cwd))
    policy_override = str(_resolve(args.policy, cwd)) if args.policy else None
    policy_path = dispatcher._configured_policy_path(config_path, config, policy_override)
    policy = dispatcher.load_model_policy(policy_path)
    dispatcher._reject_disagreeing_overrides(args, decision)
    validated = dispatcher.validate_dispatch_decision(decision, policy)
    route = dispatcher.resolve_route(
        config,
        args.role,
        alias_override=validated.decision["selected_alias"],
        cli_override=args.cli,
        model_override=validated.decision["selected_model"],
        effort_override=validated.decision["selected_effort"],
    )
    dispatcher.validate_dispatch_decision(validated.decision, policy, route)
    snapshot = dispatcher.load_scheduling_snapshot(
        _resolve(args.scheduling_snapshot, cwd)
    )
    dispatcher.validate_scheduling_dispatch(
        snapshot,
        validated.decision,
        role=route.role,
        ownership=args.ownership,
    )
    if validated.decision.get("planning_to_medium_confirmed") is not True:
        raise ValueError("execute requires confirmed planning-to-medium root gate")


def enforce_adaptive_dispatch(event: dict[str, Any]) -> bool:
    """Validate every executable dispatcher segment; return true if standalone."""

    command = str(event.get("tool_input", {}).get("command", ""))
    invocations, dispatch_only = _execute_argvs(command)
    for argv in invocations:
        _validate(argv, event)
    if invocations and not dispatch_only:
        raise ValueError("executable dispatcher must be one standalone command")
    return bool(invocations) and dispatch_only


def is_standalone_dispatcher_dry_run(event: dict[str, Any]) -> bool:
    """Allow only one simple dispatcher dry-run with no shell composition."""

    command = str(event.get("tool_input", {}).get("command", ""))
    try:
        tokens = _tokens(command)
    except ValueError:
        return False
    indices = [index for index, token in enumerate(tokens) if _is_dispatcher(token)]
    if len(indices) != 1 or any(token in SHELL_CONTROL | REDIRECTION for token in tokens):
        return False
    index = indices[0]
    prefix = tokens[:index]
    if prefix and not (
        len(prefix) == 1
        and re.fullmatch(r"python(?:3(?:\.\d+)?)?", Path(prefix[0]).name)
    ):
        return False
    argv = tokens[index + 1 :]
    if "--execute" in argv:
        return False
    dispatcher = _load_dispatcher()
    with redirect_stderr(io.StringIO()):
        try:
            dispatcher._parser().parse_args(argv)
        except SystemExit:
            return False
    return True


def is_safe_monitoring_command(command: str) -> bool:
    """Recognize a deliberately small grammar of standalone read-only commands."""

    if not command.strip() or FORBIDDEN_SHELL_TEXT.search(command):
        return False
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        return False
    if tokens == ["pwd"]:
        return True
    if tokens == ["printf", "safe"]:
        return True
    if not tokens or tokens[0] != "git":
        return False
    if any(token.startswith("-") and "=" in token for token in tokens[1:]):
        return False
    allowed_exact = {
        ("status",), ("status", "--short"), ("status", "--porcelain"),
        ("branch", "--show-current"), ("rev-parse", "HEAD"),
        ("--no-pager", "diff", "--no-ext-diff", "--stat"),
        ("--no-pager", "diff", "--no-ext-diff", "--name-only"),
        ("--no-pager", "log", "-1", "--oneline"),
    }
    return tuple(tokens[1:]) in allowed_exact
