#!/usr/bin/env python3
"""Run one static AGY CLI documentation & flag semantics inspection behind a fail-closed boundary.

This module executes only the literal command ``agy --help`` or ``agy --version``
to inspect available CLI flags and their static semantics without running model tasks,
prompts, mutations, or account quota operations. It is completely account-agnostic.
Provider stdout and stderr streams are combined only in subprocess memory.
The public JSON emits allowlisted flag names, subcommands, safe flag semantics/choices,
and structural fingerprinting.
"""
from __future__ import annotations

import json
import hashlib
import os
import re
import subprocess
import sys
from datetime import datetime
from typing import Any, Callable, Mapping, Sequence
from zoneinfo import ZoneInfo


INSPECTOR_VERSION = "agy-cli-docs-inspector-v1.5.0"
INSPECTOR_VERSION_SHA256 = hashlib.sha256(INSPECTOR_VERSION.encode("ascii")).hexdigest()
TIMEZONE = "Asia/Bangkok"
DEFAULT_TIMEOUT_SECONDS = 60.0
ALLOWED_COMMANDS = (
    ("agy", "--help"),
    ("agy", "--version"),
    ("agy", "-v"),
)

TARGET_SEMANTIC_FLAGS = frozenset(
    {
        "-p",
        "-i",
        "-c",
        "--print",
        "--prompt",
        "--output-format",
        "--input-format",
        "--json-schema",
        "--prompt-interactive",
        "--disable-slash-commands",
        "--continue",
        "--mode",
        "--model",
        "--effort",
    }
)

_ANSI_RE = re.compile(r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\))")
_EMAIL_RE = re.compile(r"(?i)(?<![\w.+-])[\w.+-]+@[a-z0-9-]+(?:\.[a-z0-9-]+)+")
_PATH_RE = re.compile(
    r"(?i)(?:\b[a-z]:\\[^\r\n\t ]+|(?<![\w.])/(?:users|home|root|private|tmp|var|etc|opt)/[^\r\n\t ]+|file://|~[/\\]|\.\.[/\\]|\./)"
)
_CREDENTIAL_RE = re.compile(
    r"(?i)\b(?:api[_ -]?key|access[_ -]?token|refresh[_ -]?token|client[_ -]?secret|"
    r"authorization|bearer|password|passwd|cookie|session[_ -]?token|private[_ -]?key)\b"
)
_TOKEN_LIKE_RE = re.compile(
    r"(?<![A-Za-z0-9_-])(?=[A-Za-z0-9_+/=-]{32,}(?![A-Za-z0-9_+/=-]))"
    r"(?=[A-Za-z0-9_+/=-]*[A-Za-z])(?=[A-Za-z0-9_+/=-]*\d)[A-Za-z0-9_+/=-]+"
)

_STRICT_FLAG_RE = re.compile(r"(?<!\w)(-[a-z]|--[a-z][a-z0-9-]*)\b")
_SUBCOMMAND_LINE_RE = re.compile(r"^\s{2,}(?P<cmd>[a-z][a-z0-9_-]{1,32})(?:\s{2,}|\s*$)(?P<desc>.*)$")
_CHOICES_RE = re.compile(r"\[(?P<choices>[a-zA-Z0-9_|/, -]+)\]|\((?P<choices2>[a-zA-Z0-9_|/, -]+)\)")


class _InspectFailure(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _timestamp() -> str:
    return datetime.now(ZoneInfo(TIMEZONE)).isoformat(timespec="seconds")


def _reject_sensitive_text(text: str) -> None:
    if _EMAIL_RE.search(text):
        raise _InspectFailure("rejected_pii")
    if _PATH_RE.search(text):
        raise _InspectFailure("rejected_path")
    if _CREDENTIAL_RE.search(text) or _TOKEN_LIKE_RE.search(text):
        raise _InspectFailure("rejected_credential_like")


def _sanitize_short_purpose(text: str) -> str:
    """Sanitize short purpose text to contain only safe alphanumeric/punctuation words."""
    words = []
    for word in text.split():
        clean_word = word.strip(".,;:()[]\"'")
        if any(bad in clean_word for bad in ("/", "\\", "~", "@")):
            continue
        if _EMAIL_RE.search(clean_word) or _CREDENTIAL_RE.search(clean_word):
            continue
        if re.fullmatch(r"[a-zA-Z0-9_-]+", clean_word):
            words.append(clean_word)
        if len(words) >= 12:
            break
    return " ".join(words)


def sanitize_docs_output(
    raw_output: str,
    target_cmd: Sequence[str],
    *,
    captured_at: str | None = None,
    stream_metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Parse static CLI help/version text into allowlisted flags, subcommands, and semantics."""
    captured_at = captured_at or _timestamp()
    stream_meta = dict(stream_metadata or {})
    default_fp = {
        "line_count": 0,
        "has_ansi_escape": False,
        "help_sections": [],
        "flag_count": 0,
        "subcommand_count": 0,
        "has_json_flag": False,
        "has_quota_subcommand": False,
        "has_status_subcommand": False,
        "has_usage_subcommand": False,
        "stdout_nonempty": stream_meta.get("stdout_nonempty", False),
        "stderr_nonempty": stream_meta.get("stderr_nonempty", False),
        "combined_stream_bytes": stream_meta.get("combined_stream_bytes", 0),
        "capture_boundary": "stdout_stderr_in_memory",
    }

    if not isinstance(raw_output, str) or not raw_output.strip():
        return {
            "captured_at": captured_at,
            "timezone": TIMEZONE,
            "target_command": list(target_cmd),
            "transport_status": "parse_failure:empty_output",
            "exit_status": 0,
            "inspector_version": INSPECTOR_VERSION,
            "account_scope": "account_agnostic_static_docs_only",
            "available_flags": [],
            "available_subcommands": [],
            "flag_semantics": {},
            "flag_aliases": {},
            "structural_fingerprint": default_fp,
            "required_human_review": True,
        }

    has_ansi = bool(_ANSI_RE.search(raw_output))
    try:
        _reject_sensitive_text(raw_output)
        text = _ANSI_RE.sub("", raw_output)
        _reject_sensitive_text(text)

        lines = [line.rstrip() for line in text.splitlines() if line.strip()]
        flags_found: set[str] = set()
        subcommands_found: set[str] = set()
        sections_found: list[str] = []
        flag_semantics: dict[str, dict[str, Any]] = {}
        flag_aliases: dict[str, list[str]] = {}

        in_subcommands_section = False
        in_options_section = False

        for line in lines:
            line_l = line.lower().strip()
            # Identify help sections safely
            if line_l.startswith("usage:"):
                if "usage" not in sections_found:
                    sections_found.append("usage")
                continue
            if line_l.startswith(("commands:", "subcommands:")):
                if "commands" not in sections_found:
                    sections_found.append("commands")
                in_subcommands_section = True
                in_options_section = False
                continue
            if line_l.startswith(("options:", "flags:", "global options:")):
                sec_name = "global_options" if "global" in line_l else "options"
                if sec_name not in sections_found:
                    sections_found.append(sec_name)
                in_options_section = True
                in_subcommands_section = False
                continue

            # Extract flags and their line-level semantics
            if in_options_section or not in_subcommands_section:
                line_clean = line.strip()
                # Find all flags on this line
                line_flags = [
                    f for f in _STRICT_FLAG_RE.findall(line_clean)
                    if not any(bad in f for bad in ("/", "\\", "~", "@", "."))
                ]
                for flag in line_flags:
                    flags_found.add(flag)

                # If multiple flags on same line (e.g. -p, --print), record aliases
                if len(line_flags) > 1:
                    primary = next((f for f in line_flags if f.startswith("--")), line_flags[0])
                    aliases = [f for f in line_flags if f != primary]
                    if primary not in flag_aliases:
                        flag_aliases[primary] = []
                    for a in aliases:
                        if a not in flag_aliases[primary]:
                            flag_aliases[primary].append(a)

                # Check if any flag on this line is in our target semantics allowlist
                target_matched = [f for f in line_flags if f in TARGET_SEMANTIC_FLAGS]
                if target_matched:
                    # Extract choices if present: e.g. [text|json] or (text|json)
                    choices: list[str] = []
                    m_choices = _CHOICES_RE.search(line_clean)
                    if m_choices:
                        raw_c = m_choices.group("choices") or m_choices.group("choices2")
                        for item in re.split(r"[|/, ]+", raw_c):
                            item_clean = item.strip()
                            if re.fullmatch(r"[a-z0-9_-]{1,24}", item_clean):
                                choices.append(item_clean)

                    # Extract short description (after double spaces or tab)
                    short_desc = ""
                    parts = re.split(r"\s{2,}|\t+", line_clean, maxsplit=1)
                    if len(parts) > 1:
                        short_desc = _sanitize_short_purpose(parts[1])

                    for t_flag in target_matched:
                        entry: dict[str, Any] = {}
                        if short_desc:
                            entry["short_purpose"] = short_desc
                        if choices:
                            entry["choices"] = sorted(set(choices))
                        flag_semantics[t_flag] = entry

            # Extract subcommands
            if in_subcommands_section:
                m_sub = _SUBCOMMAND_LINE_RE.match(line)
                if m_sub:
                    cmd_name = m_sub.group("cmd").strip()
                    if not any(bad in cmd_name for bad in ("/", "\\", "~", "@", ".")):
                        if re.fullmatch(r"[a-z][a-z0-9_-]{0,31}", cmd_name):
                            subcommands_found.add(cmd_name)

        has_json = bool({"--json", "-j"} & flags_found)
        has_quota = "quota" in subcommands_found or "--quota" in flags_found
        has_status = "status" in subcommands_found or "--status" in flags_found
        has_usage = "usage" in subcommands_found or "--usage" in flags_found

        fp = {
            "line_count": len(lines),
            "has_ansi_escape": has_ansi,
            "help_sections": sections_found,
            "flag_count": len(flags_found),
            "subcommand_count": len(subcommands_found),
            "has_json_flag": has_json,
            "has_quota_subcommand": has_quota,
            "has_status_subcommand": has_status,
            "has_usage_subcommand": has_usage,
            "stdout_nonempty": stream_meta.get("stdout_nonempty", False),
            "stderr_nonempty": stream_meta.get("stderr_nonempty", False),
            "combined_stream_bytes": stream_meta.get("combined_stream_bytes", len(raw_output.encode("utf-8"))),
            "capture_boundary": "stdout_stderr_in_memory",
        }

        return {
            "captured_at": captured_at,
            "timezone": TIMEZONE,
            "target_command": list(target_cmd),
            "transport_status": "completed",
            "exit_status": 0,
            "inspector_version": INSPECTOR_VERSION,
            "account_scope": "account_agnostic_static_docs_only",
            "available_flags": sorted(flags_found),
            "available_subcommands": sorted(subcommands_found),
            "flag_semantics": flag_semantics,
            "flag_aliases": flag_aliases,
            "structural_fingerprint": fp,
            "required_human_review": True,
        }

    except _InspectFailure as failure:
        return {
            "captured_at": captured_at,
            "timezone": TIMEZONE,
            "target_command": list(target_cmd),
            "transport_status": f"parse_failure:{failure.code}",
            "exit_status": 0,
            "inspector_version": INSPECTOR_VERSION,
            "account_scope": "account_agnostic_static_docs_only",
            "available_flags": [],
            "available_subcommands": [],
            "flag_semantics": {},
            "flag_aliases": {},
            "structural_fingerprint": default_fp,
            "required_human_review": True,
        }


def run_docs_inspection(
    cmd: Sequence[str] = ("agy", "--help"),
    *,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    runner: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Execute static command and sanitize directly in memory.

    Completely account-agnostic: does not read or pass AGY_HOME or credentials.
    Combines stdout and stderr streams in memory.
    """
    captured_at = _timestamp()
    cmd_tuple = tuple(cmd)
    if cmd_tuple not in ALLOWED_COMMANDS:
        return {
            "captured_at": captured_at,
            "timezone": TIMEZONE,
            "target_command": list(cmd),
            "transport_status": "invalid_command",
            "exit_status": "not_started",
            "inspector_version": INSPECTOR_VERSION,
            "account_scope": "account_agnostic_static_docs_only",
            "available_flags": [],
            "available_subcommands": [],
            "flag_semantics": {},
            "flag_aliases": {},
            "required_human_review": True,
        }

    execute = subprocess.run if runner is None else runner
    try:
        completed = execute(
            list(cmd),
            capture_output=True,
            check=False,
            shell=False,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        return {
            "captured_at": captured_at,
            "timezone": TIMEZONE,
            "target_command": list(cmd),
            "transport_status": "timeout",
            "exit_status": None,
            "inspector_version": INSPECTOR_VERSION,
            "account_scope": "account_agnostic_static_docs_only",
            "available_flags": [],
            "available_subcommands": [],
            "flag_semantics": {},
            "flag_aliases": {},
            "required_human_review": True,
        }
    except Exception:
        return {
            "captured_at": captured_at,
            "timezone": TIMEZONE,
            "target_command": list(cmd),
            "transport_status": "runner_error",
            "exit_status": "not_started",
            "inspector_version": INSPECTOR_VERSION,
            "account_scope": "account_agnostic_static_docs_only",
            "available_flags": [],
            "available_subcommands": [],
            "flag_semantics": {},
            "flag_aliases": {},
            "required_human_review": True,
        }

    return_code = getattr(completed, "returncode", None)
    if return_code != 0:
        return {
            "captured_at": captured_at,
            "timezone": TIMEZONE,
            "target_command": list(cmd),
            "transport_status": "nonzero_exit",
            "exit_status": return_code,
            "inspector_version": INSPECTOR_VERSION,
            "account_scope": "account_agnostic_static_docs_only",
            "available_flags": [],
            "available_subcommands": [],
            "flag_semantics": {},
            "flag_aliases": {},
            "required_human_review": True,
        }

    stdout_bytes = getattr(completed, "stdout", b"") or b""
    stderr_bytes = getattr(completed, "stderr", b"") or b""
    if isinstance(stdout_bytes, str):
        stdout_bytes = stdout_bytes.encode("utf-8", errors="replace")
    if isinstance(stderr_bytes, str):
        stderr_bytes = stderr_bytes.encode("utf-8", errors="replace")

    stdout_nonempty = bool(stdout_bytes and stdout_bytes.strip())
    stderr_nonempty = bool(stderr_bytes and stderr_bytes.strip())
    combined_bytes = (stdout_bytes + b"\n" + stderr_bytes) if (stdout_bytes and stderr_bytes) else (stdout_bytes or stderr_bytes)
    combined_text = combined_bytes.decode("utf-8", errors="replace")

    stream_meta = {
        "stdout_nonempty": stdout_nonempty,
        "stderr_nonempty": stderr_nonempty,
        "combined_stream_bytes": len(combined_bytes),
        "capture_boundary": "stdout_stderr_in_memory",
    }

    return sanitize_docs_output(combined_text, cmd, captured_at=captured_at, stream_metadata=stream_meta)


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    cmd = ("agy", "--help")
    if "--version" in args or "-v" in args:
        cmd = ("agy", "--version")
    res = run_docs_inspection(cmd, timeout_seconds=DEFAULT_TIMEOUT_SECONDS)
    sys.stdout.write(json.dumps(res, ensure_ascii=True, separators=(",", ":")) + "\n")
    return 0 if res["transport_status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
