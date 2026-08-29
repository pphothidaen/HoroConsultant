"""Synthetic unit tests for the static AGY CLI documentation inspector v1.5.0."""
from __future__ import annotations

import json
from pathlib import Path
import sys
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
import agy_cli_docs_inspector as inspector  # noqa: E402


def test_sanitize_docs_output_extracts_flags_and_subcommands() -> None:
    sample_help = """
Usage: agy [OPTIONS] COMMAND [ARGS]...

Options:
  -p, --prompt TEXT     Send a prompt directly to the agent.
  --output-format (text|json|stream-json)  Format of the output stream.
  --json-schema SCHEMA  Validate JSON response against schema.
  -h, --help            Show this message and exit.
  -v, --version         Show version and exit.

Commands:
  status    Show agent status and quotas.
  usage     Display usage telemetry.
  config    Manage agent configuration.
"""
    res = inspector.sanitize_docs_output(sample_help, ("agy", "--help"))
    assert res["transport_status"] == "completed"
    assert "--prompt" in res["available_flags"]
    assert "--output-format" in res["available_flags"]
    assert "-p" in res["available_flags"]
    assert "status" in res["available_subcommands"]
    assert "usage" in res["available_subcommands"]
    assert "config" in res["available_subcommands"]
    fp = res["structural_fingerprint"]
    assert fp["flag_count"] >= 4
    assert fp["subcommand_count"] >= 3
    assert fp["has_status_subcommand"] is True
    assert fp["has_usage_subcommand"] is True
    assert fp["has_quota_subcommand"] is False
    assert "usage" in fp["help_sections"]
    assert "options" in fp["help_sections"]
    assert "commands" in fp["help_sections"]
    assert fp["capture_boundary"] == "stdout_stderr_in_memory"

    # Verify semantics
    assert "--output-format" in res["flag_semantics"]
    assert res["flag_semantics"]["--output-format"]["choices"] == ["json", "stream-json", "text"]
    assert "--prompt" in res["flag_semantics"]
    assert res["flag_aliases"].get("--prompt") == ["-p"]


def test_sanitize_docs_rejects_paths_fail_closed() -> None:
    for leak in ["/Users/private/config", "/home/user/.ai-accounts", "C:\\Users\\admin", "~/secret", "../config", "./agy"]:
        bad_text = f"Options:\n  --config {leak}\n"
        res = inspector.sanitize_docs_output(bad_text, ("agy", "--help"))
        assert res["transport_status"] == "parse_failure:rejected_path"
        assert res["available_flags"] == []
        assert leak not in json.dumps(res)


def test_sanitize_docs_rejects_emails_and_tokens() -> None:
    for leak in ["admin@google.com", "bearer token123", "client_secret=secret123", "AbCdEf0123456789AbCdEf0123456789"]:
        bad_text = f"Options:\n  --auth {leak}\n"
        res = inspector.sanitize_docs_output(bad_text, ("agy", "--help"))
        assert res["transport_status"].startswith("parse_failure:rejected_")
        assert res["available_flags"] == []
        assert leak not in json.dumps(res)


def test_ansi_escape_is_stripped_in_memory_and_flagged() -> None:
    ansi_help = "\x1b[32mUsage:\x1b[0m agy\n\x1b[1mOptions:\x1b[0m\n  --output-format text  Output in text\n"
    res = inspector.sanitize_docs_output(ansi_help, ("agy", "--help"))
    assert res["transport_status"] == "completed"
    assert res["structural_fingerprint"]["has_ansi_escape"] is True
    assert "--output-format" in res["available_flags"]
    assert "\\u001b" not in json.dumps(res)


def test_examples_and_descriptions_never_become_flags() -> None:
    help_with_examples = """
Usage: agy [OPTIONS] COMMAND

Options:
  -p, --prompt TEXT    Send prompt like agy -p "hello world" or key: value
  --format TYPE        Format output (e.g. --format=json or type:table)

Commands:
  inspect              Inspect agent status
"""
    res = inspector.sanitize_docs_output(help_with_examples, ("agy", "--help"))
    assert res["transport_status"] == "completed"
    assert "hello" not in res["available_flags"]
    assert "world" not in res["available_flags"]
    assert "table" not in res["available_flags"]
    assert "key" not in res["available_flags"]
    assert "value" not in res["available_flags"]
    assert "--prompt" in res["available_flags"]
    assert "--format" in res["available_flags"]
    assert "inspect" in res["available_subcommands"]


def test_run_docs_inspection_executes_allowed_command_only() -> None:
    calls = []

    def fake_runner(*args, **kwargs):
        calls.append((args, kwargs))
        return SimpleNamespace(returncode=0, stdout=b"Usage: agy\nOptions:\n  -h, --help\n", stderr=b"")

    res = inspector.run_docs_inspection(("agy", "--help"), runner=fake_runner)
    assert res["transport_status"] == "completed"
    assert len(calls) == 1
    assert calls[0][0] == (["agy", "--help"],)

    res_disallowed = inspector.run_docs_inspection(("agy", "do_something_else"), runner=fake_runner)
    assert res_disallowed["transport_status"] == "invalid_command"


def test_run_docs_inspection_handles_timeout_and_nonzero_exit() -> None:
    def timeout_runner(*args, **kwargs):
        raise inspector.subprocess.TimeoutExpired(args[0], kwargs["timeout"])

    res_to = inspector.run_docs_inspection(("agy", "--help"), runner=timeout_runner)
    assert res_to["transport_status"] == "timeout"
    assert res_to["exit_status"] is None

    def nonzero_runner(*args, **kwargs):
        return SimpleNamespace(returncode=2, stdout=b"", stderr=b"")

    res_nz = inspector.run_docs_inspection(("agy", "--help"), runner=nonzero_runner)
    assert res_nz["transport_status"] == "nonzero_exit"
    assert res_nz["exit_status"] == 2


def test_account_scope_is_explicitly_account_agnostic() -> None:
    res = inspector.sanitize_docs_output("Usage: agy\nOptions:\n  --help\n", ("agy", "--help"))
    assert res["account_scope"] == "account_agnostic_static_docs_only"


def test_subcommands_with_path_chars_never_become_subcommands() -> None:
    text = "Commands:\n  ./bin/agy   Run binary\n  sub/cmd     Invalid\n  validcmd    Valid command\n"
    res = inspector.sanitize_docs_output(text, ("agy", "--help"))
    assert res["transport_status"] == "parse_failure:rejected_path"


def test_version_command_parsing() -> None:
    text = "agy version 2.5.0\n"
    res = inspector.sanitize_docs_output(text, ("agy", "--version"))
    assert res["transport_status"] == "completed"
    assert res["target_command"] == ["agy", "--version"]


def test_runner_captures_help_emitted_to_stderr_only() -> None:
    def stderr_runner(*args, **kwargs):
        return SimpleNamespace(returncode=0, stdout=b"", stderr=b"Usage: agy\nOptions:\n  --output-format json  Output json\n")

    res = inspector.run_docs_inspection(("agy", "--help"), runner=stderr_runner)
    assert res["transport_status"] == "completed"
    assert "--output-format" in res["available_flags"]
    fp = res["structural_fingerprint"]
    assert fp["stdout_nonempty"] is False
    assert fp["stderr_nonempty"] is True
    assert fp["combined_stream_bytes"] > 0


def test_runner_rejects_stderr_path_leak_fail_closed() -> None:
    def leak_runner(*args, **kwargs):
        return SimpleNamespace(returncode=0, stdout=b"Usage: agy\n", stderr=b"Config at /home/user/.ai-accounts/agy\n")

    res = inspector.run_docs_inspection(("agy", "--help"), runner=leak_runner)
    assert res["transport_status"] == "parse_failure:rejected_path"
    assert res["available_flags"] == []
    assert "/home/user" not in json.dumps(res)


def test_runner_strips_ansi_from_stderr_only() -> None:
    def ansi_stderr_runner(*args, **kwargs):
        return SimpleNamespace(returncode=0, stdout=b"", stderr=b"\x1b[33mOptions:\x1b[0m\n  --mode code  Run in code mode\n")

    res = inspector.run_docs_inspection(("agy", "--help"), runner=ansi_stderr_runner)
    assert res["transport_status"] == "completed"
    assert res["structural_fingerprint"]["has_ansi_escape"] is True
    assert "--mode" in res["available_flags"]
