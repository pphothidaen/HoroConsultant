"""Synthetic, provider-free tests for the direct AGY /usage sanitizer v1.6.0."""
from __future__ import annotations

import json
import hashlib
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest


sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
import agy_usage_quota_sanitizer as sanitizer  # noqa: E402


CAPTURED_AT = "2026-08-28T12:00:00+07:00"
OUTER_FIELDS = {
    "alias",
    "captured_at",
    "timezone",
    "buckets",
    "exit_status",
    "transport_status",
    "parser_version",
    "required_human_review",
    "structural_fingerprint",
}
BUCKET_FIELDS = {
    "label",
    "remaining_fraction",
    "remaining_percent",
    "safe_band",
    "reset_time",
    "reset_in_seconds",
}
FINGERPRINT_FIELDS = {
    "line_count",
    "has_ansi_escape",
    "detected_layout",
    "line_structures",
    "first_token_types",
    "value_shapes",
}


def sanitize(text: str, alias: str = "agy1") -> dict:
    return sanitizer.sanitize_usage_output(text, alias, captured_at=CAPTURED_AT)


def assert_content_free_failure(result: dict, forbidden: str = "") -> None:
    encoded = json.dumps(result, sort_keys=True)
    assert set(result) <= OUTER_FIELDS
    assert result["buckets"] == []
    assert result["required_human_review"] is True
    assert result["transport_status"] != "completed"
    if "structural_fingerprint" in result and result["structural_fingerprint"] is not None:
        assert set(result["structural_fingerprint"]) == FINGERPRINT_FIELDS
    if forbidden:
        assert forbidden not in encoded


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            "Requests: 1,500 / 1,500\nTokens: 1,000,000 / 1,000,000\nReset: 5 hours\n[Esc] Close\n",
            {"label": "Requests", "remaining_percent": 100},
        ),
        (
            "Usage\nGemini Pro: 63% remaining, resets in 2h 5m\n",
            {"label": "Gemini Pro", "remaining_percent": 63, "reset_in_seconds": 7500},
        ),
        (
            "Gemini 2.5 Pro: [████████░░] 88%\nGemini 2.5 Flash: [██████████] 100% (resets in 5h)\nTier: Pro\nPress Esc to close\n",
            {"label": "Gemini 2.5 Pro", "remaining_percent": 88},
        ),
        (
            "Gemini Pro: [░░░░░░░░░░] 0%\n",
            {"label": "Gemini Pro", "remaining_percent": 0},
        ),
        (
            "Gemini Pro: Available (88%)\nStatus: Active\n",
            {"label": "Gemini Pro", "remaining_percent": 88},
        ),
        (
            "Gemini Flash: OK [88%]\nWindow: 5h\n",
            {"label": "Gemini Flash", "remaining_percent": 88},
        ),
        (
            "Gemini Pro: 88% of daily limit\nQuota: quota exceeded\n",
            {"label": "Gemini Pro", "remaining_percent": 88},
        ),
        (
            "Gemini Pro: Resets at 15:00 (88%)\n",
            {"label": "Gemini Pro", "remaining_percent": 88},
        ),
        (
            "Daily Quota: 1200 of 1500 remaining\nLegacy: --\n",
            {"label": "Daily Quota", "remaining_percent": 80},
        ),
        (
            "Model: Gemini 2.5 Pro\nRemaining: 88%\nWindow: 5h\n[Esc] Close\n",
            {"label": "Gemini 2.5 Pro", "remaining_percent": 88},
        ),
        (
            "Daily Quota: 1200 / 1500 remaining\nStatus: Active\n",
            {"label": "Daily Quota", "remaining_percent": 80},
        ),
        (
            "Gemini Flash: 0.25 remaining fraction\nGemini Pro: healthy\n",
            {"label": "Gemini Flash", "remaining_fraction": 0.25},
        ),
        (
            "Model                  Remaining    Reset\nGemini 2.5 Pro         88%          2h 15m\n",
            {"label": "Gemini 2.5 Pro", "remaining_percent": 88, "reset_in_seconds": 8100},
        ),
        (
            "| Model | Remaining | Reset |\n| Gemini Pro | 63% | in 2h 5m |\n",
            {"label": "Gemini Pro", "remaining_percent": 63, "reset_in_seconds": 7500},
        ),
        (
            "┌──────────────┬────────────┬────────────┐\n"
            "│ Model        │ Remaining  │ Reset      │\n"
            "├──────────────┼────────────┼────────────┤\n"
            "│ Gemini Pro   │ 88%        │ 2026-08-28T15:00:00Z │\n"
            "└──────────────┴────────────┴────────────┘\n",
            {"label": "Gemini Pro", "remaining_percent": 88, "reset_time": "2026-08-28T15:00:00Z"},
        ),
        (
            "• Gemini Pro: 88% (resets in 2h 15m)\n",
            {"label": "Gemini Pro", "remaining_percent": 88, "reset_in_seconds": 8100},
        ),
        (
            "gemini-flash      100%\n",
            {"label": "gemini-flash", "remaining_percent": 100},
        ),
    ],
)
def test_success_variants_are_allowlisted(text: str, expected: dict) -> None:
    result = sanitize(text)
    assert result["transport_status"] == "completed"
    assert expected in result["buckets"]
    assert set(result) == OUTER_FIELDS
    assert set(result["structural_fingerprint"]) == FINGERPRINT_FIELDS
    for bucket in result["buckets"]:
        assert set(bucket) <= BUCKET_FIELDS
        assert len({"remaining_fraction", "remaining_percent", "safe_band"} & set(bucket)) == 1


def test_four_line_observed_layout_with_comma_numbers_and_footer_succeeds() -> None:
    raw = (
        "Requests: 1,500 / 1,500\n"
        "Tokens: 1,000,000 / 1,000,000\n"
        "Reset: 5 hours\n"
        "Press Esc to close\n"
    )
    result = sanitize(raw)
    assert result["transport_status"] == "completed"
    assert len(result["buckets"]) == 2
    assert result["buckets"][0] == {"label": "Requests", "remaining_percent": 100}
    assert result["buckets"][1] == {"label": "Tokens", "remaining_percent": 100}
    fp = result["structural_fingerprint"]
    assert fp["line_count"] == 4
    assert fp["detected_layout"] == "key_value"
    assert "count_ratio" in fp["value_shapes"]
    assert "non_quota_value" in fp["value_shapes"]
    assert "none" in fp["value_shapes"]


def test_ansi_is_stripped_only_in_memory() -> None:
    raw = "\x1b[32mGemini Pro: 88% remaining\x1b[0m\n"
    result = sanitize(raw)
    assert result["buckets"] == [{"label": "Gemini Pro", "remaining_percent": 88}]
    assert result["structural_fingerprint"]["has_ansi_escape"] is True
    assert "\\u001b" not in json.dumps(result)


def test_known_tui_decorations_and_prompts_are_ignored() -> None:
    raw = "╭────────────╮\n❯\nUsage\nGemini Pro: 88% remaining\nPress Esc to close\n╰────────────╯\n"
    result = sanitize(raw)
    assert result["transport_status"] == "completed"
    assert result["buckets"] == [{"label": "Gemini Pro", "remaining_percent": 88}]


def test_unknown_decorative_or_prompt_text_is_rejected() -> None:
    for raw in ("???\n", "Type anything here\n"):
        result = sanitize(raw)
        assert result["transport_status"] == "parse_failure:unexpected_line"
        assert_content_free_failure(result)
    assert sanitize("\x1b[99m\n")["transport_status"] == "parse_failure:empty_output"


def test_parser_version_and_version_hash_are_pinned() -> None:
    assert sanitizer.PARSER_VERSION == "agy-usage-sanitizer-v1.6.0"
    assert sanitizer.PARSER_VERSION_SHA256 == hashlib.sha256(
        sanitizer.PARSER_VERSION.encode("ascii")
    ).hexdigest()
    assert sanitize("Gemini Pro: 88% remaining\n")["parser_version"] == sanitizer.PARSER_VERSION


def test_observed_compact_panel_metadata_is_allowlisted() -> None:
    result = sanitize("model_family=gemini\nremaining_percent=63%\n")
    assert result["transport_status"] == "completed"
    assert result["buckets"] == [{"label": "gemini", "remaining_percent": 63}]


def test_observed_model_metadata_variant_is_allowlisted() -> None:
    result = sanitize("model=gemini-3.7\nremaining_percent: 63%\n")
    assert result["transport_status"] == "completed"
    assert result["buckets"] == [{"label": "gemini-3.7", "remaining_percent": 63}]


def test_unitless_remaining_and_ambiguous_model_metadata_fail_closed() -> None:
    for raw, failure_type in (
        ("model=gemini-3.7\nremaining=39\n", "unexpected_key_value"),
        (
            "model=gemini-3.7\nmodel=gemini-flash\nremaining_percent=63%\n",
            "duplicate_model_metadata",
        ),
    ):
        result = sanitize(raw)
        assert result["transport_status"] == f"parse_failure:{failure_type}"
        assert_content_free_failure(result, raw.strip())


@pytest.mark.parametrize(
    ("text", "failure_type"),
    [
        ("Usage\n", "missing_bucket"),
        ("Gemini Pro: 50% remaining\nGemini Pro: 49% remaining\n", "duplicate_bucket"),
        ("Gemini Pro: invalid_token_value_xyz\n", "unexpected_key_value"),
        ("not quota output\n", "unexpected_line"),
        ("A,B\n", "unexpected_line"),
        ("1,2,3\n", "unexpected_line"),
        ("v1,000\n", "unexpected_line"),
        ("Model: v1,000\n", "invalid_model_metadata"),
        ("Gemini Pro: v1,000\n", "unexpected_key_value"),
        ("Reset: 5 hours\n", "missing_bucket"),
        ("", "empty_output"),
        ("\n\n", "empty_output"),
    ],
)
def test_missing_duplicate_unexpected_ambiguous_and_malformed_fail_closed(text: str, failure_type: str) -> None:
    result = sanitize(text)
    assert result["transport_status"] == f"parse_failure:{failure_type}"
    assert_content_free_failure(result, text.strip())


@pytest.mark.parametrize(
    ("sensitive", "failure_type"),
    [
        ("person@example.com", "rejected_pii"),
        ("/Users/private/account/config.json", "rejected_path"),
        ("Path: /home/user/.ai-accounts/agy/account1", "rejected_path"),
        ("access_token=abc123", "rejected_credential_like"),
        ("Bearer abc123", "rejected_credential_like"),
        ("Sign in using a browser", "rejected_auth_prompt"),
        ("AbCdEf0123456789AbCdEf0123456789", "rejected_credential_like"),
    ],
)
def test_sensitive_auth_path_and_token_text_never_leaks(sensitive: str, failure_type: str) -> None:
    raw = f"Gemini Pro: 50% remaining\n{sensitive}\n"
    result = sanitize(raw)
    assert result["transport_status"] == f"parse_failure:{failure_type}"
    assert_content_free_failure(result, sensitive)


def test_alias_rejection_never_echoes_untrusted_alias() -> None:
    malicious = "agy3-person@example.com"
    result = sanitize("Gemini Pro: 50% remaining\n", malicious)
    assert result["alias"] is None
    assert result["transport_status"] == "invalid_alias"
    assert malicious not in json.dumps(result)


def test_structural_fingerprint_contains_zero_raw_values() -> None:
    raw = "Model: GeminiSecretModel\nRemaining: 50%\nTier: SecretTier\n"
    result = sanitize(raw)
    fp = result.get("structural_fingerprint")
    assert fp is not None
    assert "GeminiSecretModel" not in json.dumps(fp)
    assert "SecretTier" not in json.dumps(fp)
    assert fp["line_count"] == 3
    assert "embedded_percentage" in fp["value_shapes"] or "percentage" in fp["value_shapes"] or "non_quota_value" in fp["value_shapes"]


def test_runner_invokes_exactly_one_literal_command_with_inherited_environment() -> None:
    calls: list[tuple] = []

    def fake_runner(*args, **kwargs):
        calls.append((args, kwargs))
        return SimpleNamespace(returncode=0, stdout=b"Gemini Pro: 71% remaining\n", stderr=b"never-read")

    result = sanitizer.run_usage_probe(
        "agy2",
        timeout_seconds=60,
        runner=fake_runner,
        environ={"AGY_HOME": "/not-emitted"},
    )
    assert result["transport_status"] == "completed"
    assert result["buckets"][0]["remaining_percent"] == 71
    assert len(calls) == 1
    args, kwargs = calls[0]
    assert args == (["agy", "-p", "/usage"],)
    assert kwargs == {
        "capture_output": True,
        "check": False,
        "shell": False,
        "timeout": 60.0,
    }
    assert "env" not in kwargs
    assert "/not-emitted" not in json.dumps(result)


def test_runner_timeout_is_single_shot_and_content_free() -> None:
    calls = 0

    def timeout_runner(*args, **kwargs):
        nonlocal calls
        calls += 1
        raise subprocess.TimeoutExpired(args[0], kwargs["timeout"], output=b"RAW_TIMEOUT_SECRET")

    result = sanitizer.run_usage_probe(
        "agy1", runner=timeout_runner, environ={"AGY_HOME": "not-emitted"}
    )
    assert calls == 1
    assert result["transport_status"] == "timeout"
    assert_content_free_failure(result, "RAW_TIMEOUT_SECRET")


def test_runner_nonzero_does_not_read_or_leak_streams() -> None:
    calls = 0

    def failed_runner(*args, **kwargs):
        nonlocal calls
        calls += 1
        return SimpleNamespace(returncode=7, stdout=b"RAW_STDOUT_SECRET", stderr=b"RAW_STDERR_SECRET")

    result = sanitizer.run_usage_probe(
        "agy1", runner=failed_runner, environ={"AGY_HOME": "not-emitted"}
    )
    assert calls == 1
    assert result["exit_status"] == 7
    assert result["transport_status"] == "nonzero_exit"
    assert_content_free_failure(result, "RAW_STDOUT_SECRET")
    assert "RAW_STDERR_SECRET" not in json.dumps(result)


def test_runner_fails_before_invocation_without_account_home_or_valid_alias() -> None:
    def forbidden_runner(*args, **kwargs):
        raise AssertionError("runner must not be called")

    missing_home = sanitizer.run_usage_probe("agy1", runner=forbidden_runner, environ={})
    invalid_alias = sanitizer.run_usage_probe(
        "codex1", runner=forbidden_runner, environ={"AGY_HOME": "not-emitted"}
    )
    assert missing_home["transport_status"] == "environment_missing"
    assert invalid_alias["transport_status"] == "invalid_alias"
    assert_content_free_failure(missing_home)
    assert_content_free_failure(invalid_alias)


def test_main_stdout_is_compact_json_and_stderr_is_empty(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        sanitizer,
        "run_usage_probe",
        lambda alias, timeout_seconds: sanitizer.sanitize_usage_output(
            "Gemini Pro: 90% remaining\n", alias, captured_at=CAPTURED_AT
        ),
    )
    assert sanitizer.main(["--alias", "agy1"]) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert "\n" not in captured.out.rstrip("\n")
    assert set(json.loads(captured.out)) == OUTER_FIELDS
