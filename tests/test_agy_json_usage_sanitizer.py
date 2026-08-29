"""Synthetic unit tests for the AGY JSON usage quota sanitizer v1.4.0."""
from __future__ import annotations

import json
from pathlib import Path
import sys
from types import SimpleNamespace

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


def test_sanitize_documented_nested_quota_schema() -> None:
    sample_json = json.dumps({
        "status": "completed",
        "usage": {"total_tokens": 0},
        "quota": {
            "gemini-weekly": {
                "remaining_fraction": 0.9378,
                "reset_time": "2026-07-06T07:50:32Z",
                "reset_in_seconds": 560580,
            }
        },
    })
    res = sanitizer.sanitize_json_usage_payload(sample_json, ("agy", "--output-format", "json", "-p", "/usage"))
    assert res["quota_status"] == "observed"
    assert res["account_quota_metrics"] == [{
        "bucket": "gemini-weekly",
        "source": "top_level_quota_schema",
        "remaining_fraction": 0.9378,
        "reset_time": "2026-07-06T07:50:32Z",
        "reset_in_seconds": 560580,
    }]


def test_sanitize_nested_quota_in_response_and_percent() -> None:
    sample_json = json.dumps({
        "response": {
            "quota": {"gemini-daily": {"remaining_percent": "63%"}},
        }
    })
    res = sanitizer.sanitize_json_usage_payload(sample_json, ("agy", "--output-format", "json", "-p", "/usage"))
    assert res["quota_status"] == "observed"
    assert res["account_quota_metrics"] == [{
        "bucket": "gemini-daily",
        "source": "response_quota_schema",
        "remaining_percent": 63,
    }]


def test_sanitize_response_string_preserves_documented_units() -> None:
    sample_json = json.dumps({
        "response": "remaining_fraction: 0.5\nremaining_ratio: 0.25\nremaining_percent: 63%\n"
    })
    res = sanitizer.sanitize_json_usage_payload(sample_json, ("agy", "--output-format", "json", "-p", "/usage"))
    assert res["quota_status"] == "observed"
    assert [m["remaining_fraction"] for m in res["account_quota_metrics"] if "remaining_fraction" in m] == [0.5]
    assert [m["remaining_ratio"] for m in res["account_quota_metrics"] if "remaining_ratio" in m] == [0.25]
    assert [m["remaining_percent"] for m in res["account_quota_metrics"] if "remaining_percent" in m] == [63]


def test_sanitize_actual_command_data_groups_buckets_payload() -> None:
    sample_json = json.dumps({
        "conversation_id": "",
        "status": "SUCCESS",
        "response": "Gemini Models\\tWeekly Limit Remaining\\t63%\\t2026-08-29T17:33:23Z",
        "usage": {"total_tokens": 0},
        "command": {
            "name": "usage",
            "data": {
                "groups": [{
                    "name": "Gemini Models",
                    "buckets": [
                        {
                            "id": "gemini-weekly",
                            "name": "Weekly Limit Remaining",
                            "window": "weekly",
                            "remaining_fraction": 0.6338797807693481,
                            "reset_time": "2026-08-29T17:33:23Z",
                        },
                        {
                            "id": "gemini-5h",
                            "name": "Five Hour Limit Remaining",
                            "window": "5h",
                            "remaining_fraction": 0.9966928958892822,
                            "reset_time": "2026-08-28T10:29:09Z",
                        },
                    ],
                }, {
                    "name": "Claude and GPT models",
                    "buckets": [{
                        "id": "3p-weekly",
                        "name": "Weekly Limit Remaining",
                        "window": "weekly",
                        "remaining_fraction": 0,
                        "reset_time": "2026-08-30T14:11:52Z",
                    }, {
                        "id": "3p-5h",
                        "name": "Five Hour Limit Remaining",
                        "window": "5h",
                        "disabled": True,
                        "remaining_fraction": 1,
                    }],
                }]
            }
        },
    })
    res = sanitizer.sanitize_json_usage_payload(sample_json, ("agy", "--output-format", "json", "-p", "/usage"))
    assert res["quota_status"] == "observed"
    metrics = {m["bucket"]: m for m in res["account_quota_metrics"] if m["source"] == "command_data_groups"}
    assert metrics["gemini-weekly"]["remaining_fraction"] == 0.6338797807693481
    assert metrics["gemini-5h"]["reset_time"] == "2026-08-28T10:29:09Z"
    assert metrics["3p-weekly"]["remaining_fraction"] == 0
    assert metrics["3p-5h"]["disabled"] is True


def test_sanitize_command_bucket_rejects_ambiguous_or_unknown_fields() -> None:
    for bucket in [
        {"id": "gemini-weekly", "remaining_fraction": 63},
        {"id": "gemini-weekly", "remaining_fraction": 0.5, "concurrency": 3},
        {"id": "gemini-weekly", "remaining_fraction": 0.5, "disabled": "false"},
    ]:
        payload = {"command": {"data": {"groups": [{"buckets": [bucket]}]}}}
        res = sanitizer.sanitize_json_usage_payload(
            json.dumps(payload), ("agy", "--output-format", "json", "-p", "/usage")
        )
        assert res["quota_status"] == "unknown"
        assert res["account_quota_metrics"] == []


def test_sanitize_rejects_ambiguous_documented_quota_units() -> None:
    for quota_bucket in [
        {"remaining_fraction": 63},
        {"remaining_ratio": 63},
        {"remaining_fraction": 0.5, "remaining_percent": 50},
        {"reset_time": "5 hours"},
    ]:
        res = sanitizer.sanitize_json_usage_payload(
            json.dumps({"quota": {"gemini-weekly": quota_bucket}}),
            ("agy", "--output-format", "json", "-p", "/usage"),
        )
        assert res["quota_status"] == "unknown"
        assert res["account_quota_metrics"] == []


def test_sanitize_rejects_boolean_documented_quota_values() -> None:
    for quota_bucket in [
        {"remaining_fraction": True},
        {"remaining_percent": True},
        {"remaining_ratio": True},
        {"remaining_fraction": 0.5, "reset_in_seconds": True},
    ]:
        res = sanitizer.sanitize_json_usage_payload(
            json.dumps({"quota": {"gemini-weekly": quota_bucket}}),
            ("agy", "--output-format", "json", "-p", "/usage"),
        )
        assert res["quota_status"] == "unknown"
        assert res["account_quota_metrics"] == []


def test_sanitize_documented_schema_never_infers_concurrency() -> None:
    sample_json = json.dumps({
        "quota": {"gemini-weekly": {"remaining_fraction": 0.5, "concurrent": 3}}
    })
    res = sanitizer.sanitize_json_usage_payload(sample_json, ("agy", "--output-format", "json", "-p", "/usage"))
    assert res["quota_status"] == "unknown"
    assert res["account_quota_metrics"] == []
    assert "concurrency" not in json.dumps(res).lower()


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
