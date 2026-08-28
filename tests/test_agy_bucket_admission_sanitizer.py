"""RED contract tests for the content-free AGY bucket admission boundary."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from scripts.agy_bucket_admission import (
    AdmissionError,
    admit_bucket_snapshot,
    retained_availability,
)


UTC = timezone.utc
NOW = datetime(2026, 8, 28, 5, 0, tzinfo=UTC)


def bucket(alias="agy1", **overrides):
    value = {
        "alias": alias,
        "model_id": "gemini-3.1-pro-high",
        "buckets": {
            "gemini-weekly": {"remaining_fraction": 0.50, "disabled": False},
            "gemini-5h": {"remaining_fraction": 0.50, "disabled": False},
            "3p-weekly": {"remaining_fraction": 0.50, "disabled": False},
            "3p-5h": {"remaining_fraction": 0.50, "disabled": False},
        },
        "observed_at": "2026-08-28T05:00:00Z",
        "provenance": {"kind": "provider_status", "fresh": True},
    }
    value.update(overrides)
    return value


def test_input_is_closed_and_contains_only_safe_structured_fields():
    unsafe = bucket(
        raw_output="provider secret output",
        response_text="verbatim response",
        credential="bearer secret",
        path="/home/user/.config/token",
        account_identifier="person@example.com",
        group_name="Gemini Models",
        group_description="private account group",
    )
    with pytest.raises(AdmissionError):
        admit_bucket_snapshot(unsafe, now=NOW)


def test_safe_input_does_not_retain_raw_or_sensitive_values():
    result = admit_bucket_snapshot(bucket(), now=NOW)
    encoded = json.dumps(result, sort_keys=True)
    for secret in ("provider secret output", "verbatim response", "bearer secret", "/home/user/.config/token", "person@example.com"):
        assert secret not in encoded
    assert set(result) <= {"alias", "model_id", "availability", "observed_at", "provenance_digest"}


@pytest.mark.parametrize("fraction", [0.10, 0, -0.1])
def test_gemini_requires_strictly_more_than_ten_percent(fraction):
    value = bucket(buckets={
        "gemini-weekly": {"remaining_fraction": fraction, "disabled": False},
        "gemini-5h": {"remaining_fraction": 0.50, "disabled": False},
    })
    result = admit_bucket_snapshot(value, now=NOW)
    assert result["availability"] == "blocked"


def test_gemini_requires_both_buckets_same_alias_and_not_disabled():
    for alias in ("agy2", "wrong-alias"):
        value = bucket(alias=alias)
        if alias == "wrong-alias":
            value["model_id"] = "gemini-3.1-pro-high"
        assert admit_bucket_snapshot(value, now=NOW)["availability"] == "blocked"
    disabled = bucket()
    disabled["buckets"]["gemini-5h"]["disabled"] = True
    assert admit_bucket_snapshot(disabled, now=NOW)["availability"] == "blocked"


@pytest.mark.parametrize("observed_at", [
    "2026-08-28T03:00:00Z",  # stale
    "2026-08-28T05:00:01Z",  # future
    "not-a-timestamp",
])
def test_stale_future_and_malformed_status_fail_closed(observed_at):
    result = admit_bucket_snapshot(bucket(observed_at=observed_at), now=NOW, max_age=timedelta(minutes=30))
    assert result["availability"] == "blocked"


@pytest.mark.parametrize("mutation", [
    lambda b: b["buckets"].update({"gemini-weekly-copy": b["buckets"]["gemini-weekly"]}),
    lambda b: b["buckets"].update({"unknown": {"remaining_fraction": 0.9, "disabled": False}}),
    lambda b: b.__setitem__("model_id", "qwen-3"),
])
def test_duplicate_unknown_and_model_mismatch_fail_closed(mutation):
    value = bucket()
    mutation(value)
    assert admit_bucket_snapshot(value, now=NOW)["availability"] == "blocked"


def test_third_party_requires_explicit_model_to_bucket_mapping_and_is_not_category_blocked():
    value = bucket(model_id="third-party-model")
    value["buckets"] = {"3p-weekly": {"remaining_fraction": 0.50, "disabled": False}, "3p-5h": {"remaining_fraction": 0.50, "disabled": False}}
    assert admit_bucket_snapshot(value, now=NOW)["availability"] == "blocked"
    assert admit_bucket_snapshot(value, model_bucket_map={"third-party-model": ("3p-weekly", "3p-5h")}, now=NOW)["availability"] == "available"


def test_third_party_zero_weekly_or_disabled_five_hour_is_blocked():
    value = bucket(model_id="third-party-model")
    value["buckets"] = {"3p-weekly": {"remaining_fraction": 0, "disabled": False}, "3p-5h": {"remaining_fraction": 0.50, "disabled": False}}
    mapping = {"third-party-model": ("3p-weekly", "3p-5h")}
    assert admit_bucket_snapshot(value, model_bucket_map=mapping, now=NOW)["availability"] == "blocked"
    value["buckets"]["3p-weekly"]["remaining_fraction"] = 0.50
    value["buckets"]["3p-5h"]["disabled"] = True
    assert admit_bucket_snapshot(value, model_bucket_map=mapping, now=NOW)["availability"] == "blocked"


def test_retention_is_digest_availability_freshness_and_provenance_only():
    retained = retained_availability(bucket(), now=NOW)
    assert set(retained) <= {"digest", "availability", "freshness", "provenance"}
    encoded = json.dumps(retained, sort_keys=True).lower()
    for forbidden in ("fraction", "reset", "stream", "credential", "path", "account", "percent"):
        assert forbidden not in encoded
