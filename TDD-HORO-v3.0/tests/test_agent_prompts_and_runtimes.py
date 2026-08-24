"""
pytest validation suite for Horo Architecture v3.0 — Agent Prompts & Runtime Adapters
Sprint 4: 05_AGENT_PROMPTS_AND_RUNTIMES (10 Prompt Templates, ClaimValidator, ConsensusEngine, AuditNode, PlanComposer)

Run: python3 -m pytest TDD-HORO-v3.0/tests/test_agent_prompts_and_runtimes.py -v
"""
import json
import os
import sys
import pytest

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
PROMPTS_DIR = os.path.join(BASE_DIR, "05_AGENT_PROMPTS_AND_RUNTIMES", "prompts")
RUNTIMES_DIR = os.path.join(BASE_DIR, "05_AGENT_PROMPTS_AND_RUNTIMES")

sys.path.insert(0, RUNTIMES_DIR)

from runtimes.claim_validator import ClaimValidator
from runtimes.consensus_engine import ConsensusEngine
from runtimes.audit_node import AuditNode
from runtimes.plan_composer import PlanComposer, MANDATORY_EPISTEMIC_DISCLAIMER_TH, MANDATORY_EPISTEMIC_DISCLAIMER_EN


def load_json(relative_path: str) -> dict:
    full_path = os.path.join(BASE_DIR, relative_path)
    assert os.path.isfile(full_path), f"[ERROR] File not found: {full_path}"
    with open(full_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# TEST GROUP 1: Prompt Templates Validation (All 10 Nodes)
# ---------------------------------------------------------------------------

class TestPromptTemplates:
    """Validate all 10 specialized agent prompt templates."""

    EXPECTED_PROMPTS = [
        ("bazi_node_prompt.json", "@Horo_BaZi_Node", "ming_xue_bazi", "L3"),
        ("ziwei_node_prompt.json", "@Horo_ZiWei_Node", "ming_xue_ziwei", "L3"),
        ("fengshui_node_prompt.json", "@Horo_FengShui_Node", "xiang_xue_feng_shui", "L3"),
        ("bushi_node_prompt.json", "@Horo_BuShi_Node", "bu_shi_liu_yao", "L3"),
        ("qimen_node_prompt.json", "@Horo_QiMen_Node", "san_shi_qi_men", "L4"),
        ("daliuren_node_prompt.json", "@Horo_DaLiuRen_Node", "san_shi_da_liu_ren", "L4"),
        ("taiyi_node_prompt.json", "@Horo_TaiYi_Node", "san_shi_tai_yi", "L4"),
        ("qizheng_node_prompt.json", "@Horo_QiZheng_Node", "ming_xue_qi_zheng", "L4"),
        ("mianxiang_node_prompt.json", "@Horo_MianXiang_Node", "xiang_xue_mian_xiang", "L4"),
        ("zeji_node_prompt.json", "@Horo_ZeJi_Node", "ze_ji_xue", "L4"),
    ]

    @pytest.mark.parametrize("filename,expected_node_id,expected_domain,expected_layer", EXPECTED_PROMPTS)
    def test_prompt_file_structure(self, filename, expected_node_id, expected_domain, expected_layer):
        data = load_json(f"05_AGENT_PROMPTS_AND_RUNTIMES/prompts/{filename}")
        assert data.get("node_id") == expected_node_id
        assert data.get("tradition_domain") == expected_domain
        assert data.get("layer") == expected_layer
        assert "system_prompt" in data and len(data["system_prompt"]) > 50
        assert "canonical_corpus" in data and len(data["canonical_corpus"]) > 0
        assert "domain_firewall" in data

    @pytest.mark.parametrize("filename,expected_node_id,expected_domain,expected_layer", EXPECTED_PROMPTS)
    def test_prompt_example_emission_validity(self, filename, expected_node_id, expected_domain, expected_layer):
        data = load_json(f"05_AGENT_PROMPTS_AND_RUNTIMES/prompts/{filename}")
        example = data.get("example_claim_emission")
        assert example is not None, f"Missing example_claim_emission in {filename}"
        is_valid, violations = ClaimValidator.validate_emission_payload(example)
        assert is_valid is True, f"Example in {filename} failed validation: {violations}"


# ---------------------------------------------------------------------------
# TEST GROUP 2: ClaimValidator Runtime Logic
# ---------------------------------------------------------------------------

class TestClaimValidatorRuntime:
    """Test firewall violation rejection, schema enforcement, and confidence validation."""

    def test_firewall_breach_detection(self):
        """BaZi node referencing ZiWei '化禄' must be rejected."""
        breach_payload = {
            "node_id": "@Horo_BaZi_Node",
            "tradition_domain": "ming_xue_bazi",
            "claims": [
                {
                    "claim_id": "11111111-1111-4111-a111-111111111111",
                    "materiality_weight": 0.8,
                    "epistemic_trace": {
                        "source_corpus": "滴天髓",
                        "locator": "卷一",
                        "applied_rule_id": "BAZI-001",
                        "derived_from_calc_hash": "a" * 64,
                    },
                    "statement": "The Day Master shows 化禄 transformation into wealth",
                    "confidence_vector": {
                        "calculation_integrity": 1.0,
                        "rule_match_strength": 0.9,
                        "source_support": 0.9,
                        "interpretation_stability": 0.9,
                        "cross_agent_agreement": 0.0,
                    },
                }
            ],
        }
        is_valid, violations = ClaimValidator.validate_emission_payload(breach_payload)
        assert is_valid is False
        assert any("Domain Firewall Breach" in v for v in violations)

    def test_invalid_canonical_corpus_rejected(self):
        """Claim citing non-existent corpus must be rejected."""
        fake_corpus_payload = {
            "node_id": "@Horo_QiMen_Node",
            "tradition_domain": "san_shi_qi_men",
            "claims": [
                {
                    "claim_id": "22222222-2222-4222-a222-222222222222",
                    "materiality_weight": 0.8,
                    "epistemic_trace": {
                        "source_corpus": "FakeUnknownBook",
                        "locator": "Chapter 1",
                        "applied_rule_id": "QIMEN-001",
                        "derived_from_calc_hash": "a" * 64,
                    },
                    "statement": "Open Gate active in East sector indicating smooth journey",
                    "confidence_vector": {
                        "calculation_integrity": 1.0,
                        "rule_match_strength": 0.9,
                        "source_support": 0.9,
                        "interpretation_stability": 0.9,
                        "cross_agent_agreement": 0.0,
                    },
                }
            ],
        }
        is_valid, violations = ClaimValidator.validate_emission_payload(fake_corpus_payload)
        assert is_valid is False
        assert any("not in canonical corpora" in v for v in violations)


# ---------------------------------------------------------------------------
# TEST GROUP 3: ConsensusEngine Runtime Logic
# ---------------------------------------------------------------------------

class TestConsensusEngineRuntime:
    """Test L5 consensus, priority dominance arbitration, and hard exclusion handling."""

    def test_priority_dominance_arbitration(self):
        """In STRATEGIC_TIMING_ACTION intent, QiMen supersedes BaZi."""
        qimen_claim = {
            "claim_id": "qimen-c1",
            "materiality_weight": 0.90,
            "statement": "Strategic aggressive push in East sector is auspicious",
            "epistemic_trace": {"source_corpus": "烟波钓叟歌", "applied_rule_id": "QIMEN-001", "derived_from_calc_hash": "a" * 64},
            "confidence_vector": {"calculation_integrity": 1.0, "source_support": 0.9, "rule_match_strength": 0.9, "interpretation_stability": 0.9, "cross_agent_agreement": 0.0},
            "potential_conflicts": [{"target_domain": "ming_xue_bazi", "conflict_nature": "BaZi suggests caution", "severity": 0.8}],
        }
        bazi_claim = {
            "claim_id": "bazi-c1",
            "materiality_weight": 0.80,
            "statement": "Day Master is weak, caution advised",
            "epistemic_trace": {"source_corpus": "滴天髓", "applied_rule_id": "BAZI-001", "derived_from_calc_hash": "a" * 64},
            "confidence_vector": {"calculation_integrity": 1.0, "source_support": 0.85, "rule_match_strength": 0.85, "interpretation_stability": 0.85, "cross_agent_agreement": 0.0},
            "potential_conflicts": [{"target_domain": "san_shi_qi_men", "conflict_nature": "QiMen suggests aggression", "severity": 0.8}],
        }

        emissions = [
            {"node_id": "@Horo_QiMen_Node", "tradition_domain": "san_shi_qi_men", "claims": [qimen_claim]},
            {"node_id": "@Horo_BaZi_Node", "tradition_domain": "ming_xue_bazi", "claims": [bazi_claim]},
        ]

        engine = ConsensusEngine(user_intent="STRATEGIC_TIMING_ACTION")
        result = engine.arbitrate_claims(emissions)

        assert result["total_claims"] == 2
        assert len(result["arbitrated_edges"]) == 1
        edge = result["arbitrated_edges"][0]
        assert edge["edge_type"] == "supersedes"
        assert edge["winning_domain"] == "san_shi_qi_men"
        assert edge["source_claim_id"] == "qimen-c1"
        assert edge["target_claim_id"] == "bazi-c1"
        assert "FSM_H3_ARBITRATION" in result["events_emitted"]

    def test_hard_exclusion_handling(self):
        """ZeJi hard exclusion veto must be detected and recorded."""
        zeji_veto = {
            "claim_id": "zeji-veto-1",
            "materiality_weight": 1.0,
            "claim_type": "hard_exclusion",
            "statement": "Year Branch clash (Sui Po) detected, date excluded",
            "epistemic_trace": {"source_corpus": "协纪辨方书", "applied_rule_id": "ZEJI-VETO-001", "derived_from_calc_hash": "a" * 64},
            "confidence_vector": {"calculation_integrity": 1.0, "source_support": 0.98, "rule_match_strength": 1.0, "interpretation_stability": 0.98, "cross_agent_agreement": 0.0},
        }
        emissions = [
            {"node_id": "@Horo_ZeJi_Node", "tradition_domain": "ze_ji_xue", "claims": [zeji_veto]}
        ]

        engine = ConsensusEngine(user_intent="STRATEGIC_TIMING_ACTION")
        result = engine.arbitrate_claims(emissions)

        assert len(result["hard_vetoes"]) == 1
        assert "FSM_H2_EXCLUSION" in result["events_emitted"]


# ---------------------------------------------------------------------------
# TEST GROUP 4: AuditNode & Inversion Thinking Logic
# ---------------------------------------------------------------------------

class TestAuditNodeRuntime:
    """Test L6 audit node evaluations, metrics calculations, and verdict assignment."""

    def test_audit_pass_verdict(self):
        consensus_data = {
            "claims": [
                {
                    "claim_id": "c1",
                    "materiality_weight": 0.9,
                    "confidence_vector": {"source_support": 0.9, "cross_agent_agreement": 0.8},
                    "is_quarantined": False,
                }
            ],
            "arbitrated_edges": [],
            "hitl_escalations": [],
            "hard_vetoes": [],
        }
        audit = AuditNode()
        report = audit.evaluate_consensus_state(consensus_data)
        assert report["verdict"] == "AUDIT_PASS"
        assert report["metrics"]["lciw"] >= 0.85
        assert report["metrics"]["rniw"] <= 0.15
        assert report["can_proceed_to_composer"] is True

    def test_echo_chamber_detection(self):
        """High cross_agent_agreement with low source_support triggers AUDIT_PASS_WITH_WARNINGS."""
        consensus_data = {
            "claims": [
                {
                    "claim_id": "c1",
                    "materiality_weight": 0.9,
                    "confidence_vector": {"source_support": 0.30, "cross_agent_agreement": 0.95},
                    "is_quarantined": False,
                }
            ],
            "arbitrated_edges": [],
            "hitl_escalations": [],
            "hard_vetoes": [],
        }
        audit = AuditNode()
        report = audit.evaluate_consensus_state(consensus_data)
        assert report["findings"]["echo_chamber_detected"] is True
        assert report["verdict"] == "AUDIT_PASS_WITH_WARNINGS"


# ---------------------------------------------------------------------------
# TEST GROUP 5: PlanComposer & Mandatory Epistemic Disclaimer
# ---------------------------------------------------------------------------

class TestPlanComposerRuntime:
    """Test L7 plan composer output synthesis and mandatory disclaimer verification."""

    def test_composer_generates_report_with_disclaimer(self):
        consensus_output = {
            "session_id": "11111111-1111-4111-a111-111111111111",
            "user_intent": "STRATEGIC_TIMING_ACTION",
            "claims": [
                {
                    "claim_id": "c1",
                    "_domain": "san_shi_qi_men",
                    "statement": "Open Gate active in East sector",
                    "materiality_weight": 0.9,
                    "epistemic_trace": {"source_corpus": "烟波钓叟歌", "applied_rule_id": "QIMEN-001"},
                }
            ],
            "hard_vetoes": [
                {
                    "statement": "Candidate moment clashes with year branch",
                    "epistemic_trace": {"source_corpus": "协纪辨方书", "applied_rule_id": "ZEJI-VETO-001"},
                }
            ],
            "arbitrated_edges": [],
        }
        audit_output = {
            "verdict": "AUDIT_PASS",
            "can_proceed_to_composer": True,
            "metrics": {"lciw": 1.0, "rniw": 0.0},
            "findings": {"warnings": []},
        }

        composer = PlanComposer()
        report_th = composer.compose_final_report(consensus_output, audit_output, language="th")
        assert report_th["status"] == "COMPLETED"
        assert report_th["has_epistemic_disclaimer"] is True
        assert MANDATORY_EPISTEMIC_DISCLAIMER_TH in report_th["report_markdown"]
        assert "Hard Exclusion Gate" in report_th["report_markdown"]

        report_en = composer.compose_final_report(consensus_output, audit_output, language="en")
        assert report_en["has_epistemic_disclaimer"] is True
        assert MANDATORY_EPISTEMIC_DISCLAIMER_EN in report_en["report_markdown"]

    def test_composer_rejects_failed_audit(self):
        consensus_output = {"claims": []}
        failed_audit = {"verdict": "AUDIT_FAIL_RECOMPUTE", "can_proceed_to_composer": False}
        composer = PlanComposer()
        with pytest.raises(PermissionError):
            composer.compose_final_report(consensus_output, failed_audit)
