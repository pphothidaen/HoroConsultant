"""Contract tests for deterministic engine -> Horo v3.0 claim adapters."""

from datetime import datetime
import os
import sys
from uuid import UUID

import pytest


RUNTIMES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "TDD-HORO-v3.0", "05_AGENT_PROMPTS_AND_RUNTIMES")
sys.path.insert(0, os.path.abspath(RUNTIMES_DIR))

from project.core.bazi_engine import BaZiEngine
from project.core.qi_men_engine import QiMenEngine
from project.core.ze_ji_engine import ZeJiEngine
from project.core.zi_wei_engine import ZiWeiEngine
from project.core.v3_engine_adapter import (
    adapt_bazi_to_claims,
    adapt_qimen_to_claims,
    adapt_zeji_to_claims,
    adapt_ziwei_to_claims,
)

from runtimes.claim_validator import ClaimValidator


ADAPTER_CASES = [
    ("bazi", lambda: BaZiEngine().calculate(datetime(1990, 5, 15, 14), 103.8, 7.0, include_dayun=False)),
    ("ziwei", lambda: ZiWeiEngine().calculate_chart(1990, 5, 15, 14)),
    ("qimen", lambda: QiMenEngine().calculate_chart(2026, 8, 7, 14)),
    ("zeji", lambda: ZeJiEngine().check_suitability("午", "申", "寅", "子")),
]


@pytest.mark.parametrize("name, build_result", ADAPTER_CASES)
def test_adapter_emission_passes_claim_validator(name, build_result):
    adapter = {
        "bazi": adapt_bazi_to_claims,
        "ziwei": adapt_ziwei_to_claims,
        "qimen": adapt_qimen_to_claims,
        "zeji": adapt_zeji_to_claims,
    }[name]
    payload = adapter(build_result(), session_id="12345678-1234-4234-8234-123456789abc")

    valid, violations = ClaimValidator.validate_emission_payload(payload)
    assert valid, violations
    assert payload["claims"]
    assert payload["session_id"] == "12345678-1234-4234-8234-123456789abc"


@pytest.mark.parametrize("name, build_result", ADAPTER_CASES)
def test_adapter_emission_has_contract_metadata(name, build_result):
    adapter = {
        "bazi": adapt_bazi_to_claims,
        "ziwei": adapt_ziwei_to_claims,
        "qimen": adapt_qimen_to_claims,
        "zeji": adapt_zeji_to_claims,
    }[name]
    payload = adapter(build_result())
    claim = payload["claims"][0]
    trace = claim["epistemic_trace"]

    UUID(payload["session_id"])
    assert datetime.fromisoformat(payload["emitted_at_utc"].replace("Z", "+00:00")).tzinfo is not None
    assert len(payload["input_state_hash"]) == 64
    assert trace["derived_from_calc_hash"] == payload["input_state_hash"]
    assert len(claim["claim_id"]) == 64
    assert set(claim["confidence_vector"]) == {
        "calculation_integrity",
        "rule_match_strength",
        "source_support",
        "interpretation_stability",
        "cross_agent_agreement",
    }


def test_adapters_reject_non_mapping_engine_results():
    with pytest.raises(TypeError):
        adapt_bazi_to_claims(["not", "a", "result"])
