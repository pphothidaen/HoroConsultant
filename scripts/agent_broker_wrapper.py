#!/usr/bin/env python3
"""Strict broker wrapper client for macOS AI accounts (BRK-B2-020).

Dispatches strictly to the on-demand Swift agent-broker or the Python broker bridge
while enforcing the six canonical aliases (agy1..agy3, codex1..codex3).

Key Guarantees:
- Strictly validates canonical aliases from executable basename or --alias flag.
- Preserves exact argument array without shell eval or string interpolation (shell=False).
- Fails closed on unknown flags or non-allowlisted aliases with pure ASCII error messages.
- Never inspects, extracts, or prints secret values.
- Seamlessly falls back to typed session-only broker bridge when native broker binary is unavailable.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BRIDGE_SCRIPT = ROOT / "scripts" / "multiagent_broker_bridge.py"

CANONICAL_ALIASES: tuple[str, ...] = (
    "agy1",
    "agy2",
    "agy3",
    "codex1",
    "codex2",
    "codex3",
)


def _error(message: str, exit_code: int = 2) -> int:
    """Emit pure ASCII error message to stderr and return exit code."""
    safe_msg = message.encode("ascii", "replace").decode("ascii")
    print(f"[ERROR] {safe_msg}", file=sys.stderr)
    return exit_code


def is_canonical_alias(name: str) -> bool:
    """Check if alias name is one of the six canonical aliases."""
    return name in CANONICAL_ALIASES


def resolve_broker_executable(custom_path: Path | None = None) -> Path | None:
    """Resolve executable path to the Swift agent broker binary with integrity checks."""
    if custom_path is not None:
        p = Path(custom_path)
        if (
            p.is_file()
            and not p.is_symlink()
            and os.access(p, os.X_OK)
        ):
            return p
        return None

    # Check environment override
    env_broker = os.environ.get("AGENT_BROKER_PATH") or os.environ.get("AI_ACCOUNT_BROKER_PATH")
    if env_broker:
        p = Path(env_broker)
        if p.is_file() and not p.is_symlink() and os.access(p, os.X_OK):
            return p

    # Standard candidate locations
    candidates = [
        ROOT / "tools" / "agent-broker" / ".build" / "release" / "agent-broker",
        ROOT / "tools" / "agent-broker" / ".build" / "debug" / "agent-broker",
        ROOT / "tools" / "agent-broker" / "agent-broker",
        ROOT / "tools" / "agent-broker" / "bin" / "agent-broker",
        Path("/Library/Application Support/HoroConsultant/AccountBroker/bin/agent-broker"),
        Path.home() / "Library/Application Support/HoroConsultant/AccountBroker/bin/agent-broker",
    ]

    for candidate in candidates:
        if candidate.is_file() and not candidate.is_symlink() and os.access(candidate, os.X_OK):
            return candidate

    # Check PATH binaries
    for binary_name in ("agent-broker", "ai-account-keychain-broker"):
        which_path = shutil.which(binary_name)
        if which_path:
            p = Path(which_path)
            if p.is_file() and not p.is_symlink() and os.access(p, os.X_OK):
                return p

    return None


def dispatch_broker(
    alias: str,
    forward_argv: list[str],
    *,
    broker_path: Path | None = None,
    session_only: bool = False,
) -> int:
    """Dispatch command to agent-broker or python broker bridge using shell=False."""
    if not is_canonical_alias(alias):
        return _error(f"Unauthorized alias '{alias}'. Must be one of: {list(CANONICAL_ALIASES)}", exit_code=2)

    broker_bin = resolve_broker_executable(broker_path)

    # 1. Native Broker Binary Dispatch
    if broker_bin is not None:
        cmd = [str(broker_bin), alias, "--", *forward_argv]
        env = dict(os.environ)
        if session_only:
            env["AGENT_BROKER_SESSION_ONLY"] = "1"
        try:
            result = subprocess.run(
                cmd,
                shell=False,
                env=env,
                check=False,
            )
            return result.returncode
        except OSError as exc:
            return _error(f"Failed to execute broker binary: {exc}", exit_code=1)

    # 2. Python Broker Bridge Fallback
    if BRIDGE_SCRIPT.is_file():
        bridge_cmd = [
            sys.executable,
            str(BRIDGE_SCRIPT),
            "--alias",
            alias,
        ]
        if session_only:
            bridge_cmd.append("--session-only")
        bridge_cmd.extend(["--", *forward_argv])

        try:
            result = subprocess.run(
                bridge_cmd,
                shell=False,
                check=False,
            )
            return result.returncode
        except OSError as exc:
            return _error(f"Failed to execute Python broker bridge: {exc}", exit_code=1)

    return _error("Neither agent-broker binary nor Python broker bridge is available", exit_code=1)


def parse_client_arguments(argv: list[str]) -> tuple[str | None, Path | None, bool, list[str]]:
    """Strictly parse arguments for wrapper client mode, rejecting unknown flags."""
    alias: str | None = None
    broker_path: Path | None = None
    session_only: bool = False
    forward_argv: list[str] = []

    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--":
            forward_argv = argv[i + 1:]
            break
        elif arg == "--alias":
            if i + 1 >= len(argv):
                raise ValueError("Missing value for --alias")
            alias = argv[i + 1]
            i += 2
        elif arg.startswith("--alias="):
            alias = arg.split("=", 1)[1]
            i += 1
        elif arg == "--broker-path":
            if i + 1 >= len(argv):
                raise ValueError("Missing value for --broker-path")
            broker_path = Path(argv[i + 1])
            i += 2
        elif arg.startswith("--broker-path="):
            broker_path = Path(arg.split("=", 1)[1])
            i += 1
        elif arg == "--session-only":
            session_only = True
            i += 1
        elif arg in ("-h", "--help"):
            print("Usage: agent_broker_wrapper.py --alias <alias> [--broker-path <path>] [--session-only] -- <args...>")
            sys.exit(0)
        else:
            raise ValueError(f"Unknown or unapproved option '{arg}'")

    return alias, broker_path, session_only, forward_argv


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    # Check invocation mode via basename
    invoked_name = Path(sys.argv[0]).name
    # Handle possible extension or stem
    invoked_stem = Path(sys.argv[0]).stem

    if is_canonical_alias(invoked_name):
        alias = invoked_name
        return dispatch_broker(alias, argv)
    elif is_canonical_alias(invoked_stem):
        alias = invoked_stem
        return dispatch_broker(alias, argv)

    # Invoked as client script (e.g. agent_broker_wrapper.py)
    try:
        alias, broker_path, session_only, forward_argv = parse_client_arguments(argv)
    except ValueError as exc:
        return _error(str(exc), exit_code=2)

    if alias is None:
        return _error("Canonical alias must be specified via basename or --alias", exit_code=2)

    if not is_canonical_alias(alias):
        return _error(f"Invalid alias '{alias}'. Must be one of: {list(CANONICAL_ALIASES)}", exit_code=2)

    return dispatch_broker(
        alias,
        forward_argv,
        broker_path=broker_path,
        session_only=session_only,
    )


if __name__ == "__main__":
    raise SystemExit(main())
