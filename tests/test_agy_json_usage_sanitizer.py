"""Synthetic unit tests for the AGY JSON usage quota sanitizer v1.2.0."""
from __future__ import annotations

import json
from pathlib import Path
import sys
from types import SimpleNamespace
import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
import agy_json_usage_sanitizer as sanitizer  # noqa: E402


def test_sanitize_response_string_with_ratios_and_percentages() -> None:
    sample_json = json.dumps({
        "command": "usage",
        "conversation_id": "abc-123",
        "duration_seconds": 0,
        "num_turns": 1,
        "status": "completed",
        "usage": {
            "input_tokens": 0,
            "output_tokens": 0,
            "thinking_tokens": 0,
            "cache_read_tokens": 0,
            "total_tokens": 0
        },
        "response": "Fast queries: 85%\nRequests today: 120/1500\nModel quota: [██████░░] 75%\nReset in: 5 hours\n"
    })
    res = sanitizer.sanitize_json_usage_payload(sample_json, ("agy", "--output-format", "json", "-p", "/usage"))
    assert res["transport_status"] == "completed"
    assert res["quota_status"] == "observed"
    assert res["session_token_usage"]["total_tokens"] == 0
    metrics = res["account_quota_metrics"]
    assert len(metrics) >= 3
    fp = res["structural_fingerprint"]
    assert fp["root_type"] == "dict"
    assert fp["response_type"] == "string"
    assert fp["has_session_overhead_usage"] is True
    assert fp["has_account_quota_metrics"] is True
    assert fp["account_quota_buckets_count"] >= 3


def test_sanitize_response_dict_with_quota_fields() -> None:
    sample_json = json.dumps({
        "status": "completed",
        "usage": {"total_tokens": 0},
        "response": {
            "remaining_percent": 80.0,
            "limit": 1000,
            "used": 200
        }
    })
    res = sanitizer.sanitize_json_usage_payload(sample_json, ("agy", "--output-format", "json", "-p", "/usage"))
    assert res["transport_status"] == "completed"
    assert res["quota_status"] == "observed"
    metrics = res["account_quota_metrics"]
    assert len(metrics) == 3
    fp = res["structural_fingerprint"]
    assert fp["response_type"] == "dict"


def test_sanitize_empty_response_marks_quota_unknown() -> None:
    sample_json = json.dumps({
        "command": "usage",
        "status": "completed",
        "usage": {"total_tokens": 0},
        "response": "No specific quota information available in this view.\n"
    })
    res = sanitizer.sanitize_json_usage_payload(sample_json, ("agy", "--output-format", "json", "-p", "/usage"))
    assert res["transport_status"] == "completed"
    assert res["quota_status"] == "unknown"
    assert res["account_quota_metrics"] == []
    assert res["structural_fingerprint"]["has_account_quota_metrics"] is False


def test_sanitize_rejects_array_root_fail_closed() -> None:
    sample_json = json.dumps([
        {"category": "standard", "remaining": 90, "limit": 100}
    ])
    res = sanitizer.sanitize_json_usage_payload(sample_json, ("agy", "--output-format", "json", "-p", "/usage"))
    assert res["transport_status"] == "parse_failure:unsupported_root_json_type_requires_dict"
    assert res["account_quota_metrics"] == []


def test_sanitize_rejects_paths_fail_closed() -> None:
    for leak in ["/Users/private/config", "/home/user/.ai-accounts/token", "C:\\Users\\admin\\creds", "~/secrets.json"]:
        bad_json = json.dumps({"quota": 100, "config_path": leak})
        res = sanitizer.sanitize_json_usage_payload(bad_json, ("agy", "--output-format", "json", "-p", "/usage"))
        assert res["transport_status"] == "parse_failure:rejected_path"
        assert res["account_quota_metrics"] == []
        assert leak not in json.dumps(res)


def test_sanitize_rejects_path_in_response_fail_closed() -> None:
    bad_json = json.dumps({"response": "Config file at /home/user/.ai-accounts/token\n"})
    res = sanitizer.sanitize_json_usage_payload(bad_json, ("agy", "--output-format", "json", "-p", "/usage"))
    assert res["transport_status"] == "parse_failure:rejected_path"
    assert res["account_quota_metrics"] == []


def test_sanitize_rejects_credentials_fail_closed() -> None:
    for leak in ["bearer token123", "client_secret=secret123", "api_key=secretkey999"]:
        bad_json = json.dumps({"remaining": 50, "auth_header": leak})
        res = sanitizer.sanitize_json_usage_payload(bad_json, ("agy", "--output-format", "json", "-p", "/usage"))
        assert res["transport_status"].startswith("parse_failure:rejected_")
        assert res["account_quota_metrics"] == []


def test_sanitize_rejects_emails_and_tokens() -> None:
    for leak in ["user@domain.com", "AbCdEf0123456789AbCdEf0123456789"]:
        bad_json = json.dumps({"quota": 50, "user_id": leak})
        res = sanitizer.sanitize_json_usage_payload(bad_json, ("agy", "--output-format", "json", "-p", "/usage"))
        assert res["transport_status"].startswith("parse_failure:rejected_")
        assert res["account_quota_metrics"] == []


def test_sanitize_strips_ansi() -> None:
    ansi_json = "\x1b[32m{\x1b[0m\"status\": \"completed\", \"response\": \"Fast: 80%\"\x1b[32m}\x1b[0m"
    res = sanitizer.sanitize_json_usage_payload(ansi_json, ("agy", "--output-format", "json", "-p", "/usage"))
    assert res["transport_status"] == "completed"
    assert res["quota_status"] == "observed"


def test_sanitize_handles_invalid_json_syntax() -> None:
    bad_syntax = "Not a JSON: key=val"
    res = sanitizer.sanitize_json_usage_payload(bad_syntax, ("agy", "--output-format", "json", "-p", "/usage"))
    assert res["transport_status"] == "parse_failure:invalid_json_syntax"


def test_sanitize_handles_empty_payload() -> None:
    res = sanitizer.sanitize_json_usage_payload("", ("agy", "--output-format", "json", "-p", "/usage"))
    assert res["transport_status"] == "parse_failure:empty_payload"


def test_run_probe_executes_allowed_command_only() -> None:
    calls = []

    def fake_runner(*args, **kwargs):
        calls.append((args, kwargs))
        return SimpleNamespace(returncode=0, stdout=b'{"response": "quota: 80%"}', stderr=b"")

    res = sanitizer.run_json_usage_probe(("agy", "--output-format", "json", "-p", "/usage"), runner=fake_runner)
    assert res["transport_status"] == "completed"
    assert len(calls) == 1

    res_disallowed = sanitizer.run_json_usage_probe(("agy", "-p", "/something_else"), runner=fake_runner)
    assert res_disallowed["transport_status"] == "invalid_command"


def test_run_probe_handles_timeout_and_nonzero_exit() -> None:
    def timeout_runner(*args, **kwargs):
        raise sanitizer.subprocess.TimeoutExpired(args[0], kwargs["timeout"])

    res_to = sanitizer.run_json_usage_probe(("agy", "--output-format", "json", "-p", "/usage"), runner=timeout_runner)
    assert res_to["transport_status"] == "timeout"
    assert res_to["exit_status"] is None

    def nonzero_runner(*args, **kwargs):
        return SimpleNamespace(returncode=1, stdout=b"", stderr=b"")

    res_nz = sanitizer.run_json_usage_probe(("agy", "--output-format", "json", "-p", "/usage"), runner=nonzero_runner)
    assert res_nz["transport_status"] == "nonzero_exit"
    assert res_nz["exit_status"] == 1
