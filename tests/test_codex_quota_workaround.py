"""Tests for codex_quota_workaround.py 4-tier model and rescue helpers."""

from __future__ import annotations

import pytest
from scripts.codex_quota_workaround import (
    classify_quota_tier,
    get_account_home,
    KNOWN_ACCOUNTS,
)


def test_known_accounts():
    assert "codex1" in KNOWN_ACCOUNTS
    assert "codex2" in KNOWN_ACCOUNTS
    assert "codex3" in KNOWN_ACCOUNTS


def test_get_account_home():
    assert get_account_home("codex1").endswith("account1")
    assert get_account_home("codex2").endswith("account2")
    assert get_account_home("codex3").endswith("account3")


def test_classify_tier_1_green():
    burn_rate = {"alias": "codex2", "tokens_1h": 500, "load_band": "IDLE"}
    res = classify_quota_tier(burn_rate)
    assert res["tier"] == 1
    assert res["tier_code"] == "TIER_1_GREEN"
    assert res["max_concurrency"] == 3
    assert res["poll_interval_sec"] == 600
    assert res["status"] == "NORMAL"


def test_classify_tier_2_amber():
    burn_rate = {"alias": "codex1", "tokens_1h": 2_500_000, "load_band": "MODERATE"}
    res = classify_quota_tier(burn_rate)
    assert res["tier"] == 2
    assert res["tier_code"] == "TIER_2_AMBER"
    assert res["max_concurrency"] == 2
    assert res["poll_interval_sec"] == 120
    assert res["status"] == "WARNING"


def test_classify_tier_2_by_quota_percent():
    burn_rate = {"alias": "codex1", "tokens_1h": 100, "load_band": "LOW"}
    res = classify_quota_tier(burn_rate, quota_percent=35.0)
    assert res["tier"] == 2
    assert res["tier_code"] == "TIER_2_AMBER"


def test_classify_tier_3_orange():
    burn_rate = {"alias": "codex1", "tokens_1h": 15_000_000, "load_band": "HEAVY"}
    res = classify_quota_tier(burn_rate)
    assert res["tier"] == 3
    assert res["tier_code"] == "TIER_3_ORANGE"
    assert res["max_concurrency"] == 1
    assert res["poll_interval_sec"] == 30
    assert res["status"] == "CRITICAL"


def test_classify_tier_3_by_quota_percent():
    burn_rate = {"alias": "codex1", "tokens_1h": 100, "load_band": "LOW"}
    res = classify_quota_tier(burn_rate, quota_percent=15.0)
    assert res["tier"] == 3
    assert res["tier_code"] == "TIER_3_ORANGE"


def test_classify_tier_4_red_by_probe():
    burn_rate = {"alias": "codex1", "tokens_1h": 100, "load_band": "LOW"}
    probe = {"rate_limited": True, "probe_status": "RATE_LIMITED"}
    res = classify_quota_tier(burn_rate, probe=probe)
    assert res["tier"] == 4
    assert res["tier_code"] == "TIER_4_RED"
    assert res["max_concurrency"] == 0
    assert res["poll_interval_sec"] == 0
    assert res["status"] == "EXHAUSTED"


def test_classify_tier_4_red_by_quota():
    burn_rate = {"alias": "codex1", "tokens_1h": 100, "load_band": "LOW"}
    res = classify_quota_tier(burn_rate, quota_percent=8.0)
    assert res["tier"] == 4
    assert res["tier_code"] == "TIER_4_RED"


def test_classify_tier_4_red_by_unauth():
    burn_rate = {"alias": "codex1", "tokens_1h": 100, "load_band": "LOW"}
    auth = {"status": "UNAUTHENTICATED"}
    res = classify_quota_tier(burn_rate, auth=auth)
    assert res["tier"] == 4
    assert res["tier_code"] == "TIER_4_RED"
