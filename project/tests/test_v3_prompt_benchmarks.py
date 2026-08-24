"""Golden benchmarks for the ten Horo v3.0 metaphysics prompt templates."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PROMPTS_DIR = (
    REPOSITORY_ROOT
    / "TDD-HORO-v3.0"
    / "05_AGENT_PROMPTS_AND_RUNTIMES"
    / "prompts"
)
RUNTIMES_DIR = PROMPTS_DIR.parent
if str(RUNTIMES_DIR) not in sys.path:
    sys.path.insert(0, str(RUNTIMES_DIR))

from runtimes.claim_validator import ClaimValidator, DOMAIN_FIREWALLS  # noqa: E402


PROMPT_CONTRACTS = {
    "bazi_node_prompt.json": ("@Horo_BaZi_Node", "ming_xue_bazi", "L3", "BAZI-"),
    "ziwei_node_prompt.json": ("@Horo_ZiWei_Node", "ming_xue_ziwei", "L3", "ZIWEI-"),
    "fengshui_node_prompt.json": (
        "@Horo_FengShui_Node",
        "xiang_xue_feng_shui",
        "L3",
        "XUANKONG-",
    ),
    "bushi_node_prompt.json": ("@Horo_BuShi_Node", "bu_shi_liu_yao", "L3", "LIUYAO-"),
    "qimen_node_prompt.json": ("@Horo_QiMen_Node", "san_shi_qi_men", "L4", "QIMEN-"),
    "daliuren_node_prompt.json": (
        "@Horo_DaLiuRen_Node",
        "san_shi_da_liu_ren",
        "L4",
        "DALIUREN-",
    ),
    "taiyi_node_prompt.json": ("@Horo_TaiYi_Node", "san_shi_tai_yi", "L4", "TAIYI-"),
    "qizheng_node_prompt.json": (
        "@Horo_QiZheng_Node",
        "ming_xue_qi_zheng",
        "L4",
        "QIZHENG-",
    ),
    "mianxiang_node_prompt.json": (
        "@Horo_MianXiang_Node",
        "xiang_xue_mian_xiang",
        "L4",
        "MIANXIANG-",
    ),
    "zeji_node_prompt.json": ("@Horo_ZeJi_Node", "ze_ji_xue", "L4", "ZEJI-"),
}

REQUIRED_PROMPT_FIELDS = {
    "node_id",
    "layer",
    "tradition_domain",
    "tradition_name",
    "canonical_corpus",
    "system_prompt",
    "domain_firewall",
}
REQUIRED_FIREWALL_FIELDS = {
    "forbidden_domains",
    "forbidden_terms",
    "forbidden_assumptions",
    "allowed_constructs",
}
RULE_ID_PATTERN = re.compile(r"^[A-Z]+-[A-Z]+-[0-9]{3,6}$")


def load_prompt(filename: str) -> dict[str, Any]:
    """Load one golden prompt and preserve JSON parse errors in pytest output."""
    path = PROMPTS_DIR / filename
    assert path.is_file(), f"[ERROR] Missing prompt file: {path}"
    with path.open(encoding="utf-8") as prompt_file:
        payload = json.load(prompt_file)
    assert isinstance(payload, dict), f"[ERROR] Prompt is not a JSON object: {filename}"
    return payload


def sample_emission(prompt: dict[str, Any]) -> dict[str, Any]:
    """Support the current key and the ticket's alternate benchmark naming."""
    for key in ("few_shot_example", "sample_emission", "example_claim_emission"):
        value = prompt.get(key)
        if isinstance(value, dict):
            return value
    pytest.fail("Prompt has no few_shot_example, sample_emission, or example_claim_emission")


def test_all_prompt_files_load_and_match_required_contract():
    """Test 1: all ten golden templates parse and expose their prompt contract."""
    assert set(PROMPT_CONTRACTS) == {path.name for path in PROMPTS_DIR.glob("*.json")}
    for filename, (node_id, domain, layer, _rule_prefix) in PROMPT_CONTRACTS.items():
        prompt = load_prompt(filename)
        assert REQUIRED_PROMPT_FIELDS <= prompt.keys(), filename
        assert (prompt["node_id"], prompt["tradition_domain"], prompt["layer"]) == (
            node_id,
            domain,
            layer,
        )
        assert isinstance(prompt["canonical_corpus"], list) and prompt["canonical_corpus"]
        assert isinstance(prompt["system_prompt"], str) and len(prompt["system_prompt"]) > 50
        assert isinstance(sample_emission(prompt), dict)


def test_all_prompt_firewalls_define_assumptions_and_constructs():
    """Test 2: every domain firewall declares both sides of its construct boundary."""
    for filename in PROMPT_CONTRACTS:
        firewall = load_prompt(filename)["domain_firewall"]
        assert isinstance(firewall, dict), filename
        assert REQUIRED_FIREWALL_FIELDS <= firewall.keys(), filename
        for field in REQUIRED_FIREWALL_FIELDS:
            assert isinstance(firewall[field], list) and firewall[field], f"{filename}: {field}"


def test_every_golden_emission_passes_claim_validator():
    """Test 3: every claim in all ten golden emissions passes the runtime validator."""
    for filename in PROMPT_CONTRACTS:
        valid, violations = ClaimValidator.validate_emission_payload(sample_emission(load_prompt(filename)))
        assert valid, f"{filename}: {violations}"


def test_golden_claims_use_canonical_corpora_and_valid_rules():
    """Test 4: provenance cites a validator-approved corpus and a v3 rule ID."""
    for filename, (_node_id, domain, _layer, rule_prefix) in PROMPT_CONTRACTS.items():
        prompt = load_prompt(filename)
        emission = sample_emission(prompt)
        canonical = set(DOMAIN_FIREWALLS[domain]["canonical_corpora"])
        prompt_canonical = set(prompt["canonical_corpus"])
        assert prompt_canonical & canonical, f"{filename}: no recognized canonical corpus"

        for claim in emission["claims"]:
            trace = claim["epistemic_trace"]
            assert trace["source_corpus"] in canonical, f"{filename}: non-canonical corpus"
            assert trace["source_corpus"] in prompt_canonical, f"{filename}: source not declared by prompt"
            rule_id = trace["applied_rule_id"]
            assert RULE_ID_PATTERN.fullmatch(rule_id), f"{filename}: invalid rule ID {rule_id!r}"
            assert rule_id.startswith(rule_prefix), f"{filename}: wrong rule family {rule_id!r}"
