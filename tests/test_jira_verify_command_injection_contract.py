"""Contract test: Jira verification-command execution must not use shell=True (KAN-293).

M4 of Phase 0 Foundation Hardening (KAN-290, Epic KAN-289).

Red Team CRITICAL-4: command injection. sync_jira_hermes.py:process_task() reads a
free-text "Verification Command" custom field from Jira and executes it via
subprocess.run(verify_cmd, shell=True). Because Jira fields are attacker-writable
(any user who can edit the issue can set the field), `shell=True` turns that field
into arbitrary shell execution on the host running the sync.

The safe contract:
  * the verification command is split with shlex.split() and executed in argv form
    (no shell, no shell metacharacter interpretation);
  * the executable is restricted to an allowlist (pytest by default);
  * a command containing shell metacharacters (`;`, `&&`, `|`, `` ` ``, `$`, etc.)
    is REJECTED with a clear error instead of executed;
  * the result is never used to make a transition decision without a successful,
    non-shell exit.

This test reads the source file directly (AST-free, text-based) so it cannot be
fooled by monkeypatching, and asserts the source-level invariant.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "sync_jira_hermes.py"


def _read_source() -> str:
    assert TARGET.is_file(), f"{TARGET} must exist"
    return TARGET.read_text(encoding="utf-8")


def _process_task_source() -> str:
    """Extract the process_task function body for focused assertions."""
    src = _read_source()
    m = re.search(r"def process_task\(.*?\n(?=\ndef |\nclass |\Z)", src, re.S)
    assert m, "process_task function not found"
    return m.group(0)


# ── shell=True must be gone ──────────────────────────────────────────────

def test_process_task_has_no_shell_true() -> None:
    body = _process_task_source()
    assert "shell=True" not in body, (
        "process_task must NOT use shell=True — it executes an attacker-controllable "
        "Jira custom field (command injection, M4/KAN-293)"
    )


def test_subprocess_call_uses_argv_not_string() -> None:
    body = _process_task_source()
    m = re.search(r"subprocess\.run\(\s*([^)]*)\)", body, re.S)
    assert m, "subprocess.run call not found in process_task"
    call_args = m.group(1)
    # Must not pass a bare string command with shell=True
    assert "shell=True" not in call_args, "subprocess.run must not set shell=True"
    # Must use shlex.split or an allowlist helper before running
    assert re.search(r"shlex\.split|build_verify_argv|ALLOWED_VERIFY", body), (
        "verify command must be parsed with shlex.split / an allowlist helper, "
        "not passed to a shell"
    )


# ── allowlist + metacharacter rejection exist ────────────────────────────

def test_verify_executable_allowlist_exists() -> None:
    src = _read_source()
    # An allowlist of permitted executables must be defined
    assert re.search(r"ALLOWED_VERIFY_EXECUTABLES\s*=\s*(frozenset|set|tuple)?\s*\(?\s*[\[\{]", src), (
        "An ALLOWED_VERIFY_EXECUTABLES allowlist must be defined (M4/KAN-293)"
    )


def test_metacharacters_are_rejected() -> None:
    body = _process_task_source()
    # The source must reference a metacharacter/shell-injection check
    assert re.search(r"metachar|SHELL_META|is_shell_injection|reject", body, re.I), (
        "process_task must reject shell metacharacters in the verify command (M4/KAN-293)"
    )


# ── transition decision cannot be made on a shell result ─────────────────

def test_transition_uses_returncode_not_shell_output() -> None:
    body = _process_task_source()
    # The 'Done' transition must be gated on a real returncode, and the
    # execution path must not depend on shell interpretation
    assert "returncode" in body, "process_task must inspect subprocess returncode"
    assert "shell=True" not in body
