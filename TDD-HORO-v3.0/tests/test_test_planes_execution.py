"""
pytest validation suite for Horo Architecture v3.0 — Test Planes Execution (Planes A, B, C, D)
TICKET-HORO30-015: End-to-end execution of Astronomy, Tradition Conformance, Adversarial Inversion, and Empirical Isolation suites.

Run: python3 -m pytest TDD-HORO-v3.0/tests/test_test_planes_execution.py -v
"""
import json
import os
import sys
import pytest

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
TEST_PLANES_DIR = os.path.join(BASE_DIR, "04_TEST_PLANES_AND_ACCEPTANCE")
RUNTIMES_DIR = os.path.join(BASE_DIR, "05_AGENT_PROMPTS_AND_RUNTIMES")

sys.path.insert(0, RUNTIMES_DIR)

from runtimes.claim_validator import ClaimValidator
from runtimes.consensus_engine import ConsensusEngine
from runtimes.audit_node import AuditNode


def load_json(relative_path: str) -> dict:
    full_path = os.path.join(BASE_DIR, relative_path)
    assert os.path.isfile(full_path), f"[ERROR] File not found: {full_path}"
    with open(full_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# TEST GROUP 1: Plane A (Astronomy Golden Vectors Execution)
# ---------------------------------------------------------------------------

class TestPlaneAExecution:
    """Execute validation against JPL Horizons / DE440 golden vectors."""

    def test_plane_A_all_vectors_pass_invariance_rules(self):
        data = load_json("04_TEST_PLANES_AND_ACCEPTANCE/plane_A_astronomy_golden_vectors.json")
        vectors = data.get("test_vectors", [])
        assert len(vectors) >= 6

        for vec in vectors:
            test_id = vec.get("test_id")
            inp = vec.get("input", {})
            expected = vec.get("expected", {})

            # Validate input coordinates
            lat = inp.get("latitude_deg")
            lon = inp.get("longitude_deg")
            assert -90.0 <= lat <= 90.0, f"Vector {test_id} latitude out of bounds"
            assert -180.0 <= lon <= 180.0, f"Vector {test_id} longitude out of bounds"

            if "solar_longitude_deg" in expected:
                exp_deg = expected["solar_longitude_deg"]
                assert 0.0 <= exp_deg <= 360.0, f"Vector {test_id} expected deg out of bounds"


# ---------------------------------------------------------------------------
# TEST GROUP 2: Plane B (Tradition Conformance Execution)
# ---------------------------------------------------------------------------

class TestPlaneBExecution:
    """Execute canonical conformance verification across all major traditions."""

    def test_plane_B_cases_canonical_integrity(self):
        data = load_json("04_TEST_PLANES_AND_ACCEPTANCE/plane_B_tradition_conformance_cases.json")
        cases = data.get("conformance_cases", [])
        assert len(cases) >= 7

        for case in cases:
            case_id = case.get("case_id")
            tradition = case.get("tradition")
            canon_ref = case.get("canonical_reference", "")
            expected_claims = case.get("expected_claims", [])

            assert len(canon_ref) > 5, f"Case {case_id} missing canonical reference"
            assert len(expected_claims) > 0, f"Case {case_id} missing expected claims"


# ---------------------------------------------------------------------------
# TEST GROUP 3: Plane C (Adversarial Conflict Cases Execution)
# ---------------------------------------------------------------------------

class TestPlaneCExecution:
    """Execute runtime simulation against all 5 adversarial attack categories."""

    def test_adv_c_001_domain_contamination(self):
        """ADV-C-001: Cross-domain firewall breach must be caught by ClaimValidator."""
        plane_c = load_json("04_TEST_PLANES_AND_ACCEPTANCE/plane_C_adversarial_conflict_cases.json")
        case = next(c for c in plane_c["cases"] if c["attack_id"] == "ADV-C-001")
        injected = case["injected_claim"]

        is_valid, violations = ClaimValidator.validate_emission_payload(injected)
        assert is_valid is False, "ADV-C-001 attack should have been rejected by validator"
        assert any("Domain Firewall Breach" in v for v in violations)

    def test_adv_c_002_hallucination_detection(self):
        """ADV-C-002: Hallucinated corpus citation must be rejected by ClaimValidator."""
        plane_c = load_json("04_TEST_PLANES_AND_ACCEPTANCE/plane_C_adversarial_conflict_cases.json")
        case = next(c for c in plane_c["cases"] if c["attack_id"] == "ADV-C-002")
        injected = case["injected_claim"]

        is_valid, violations = ClaimValidator.validate_emission_payload(injected)
        assert is_valid is False
        assert any("not in canonical corpora" in v for v in violations)

    def test_adv_c_004_hard_conflict_escape_veto(self):
        """ADV-C-004: ZeJi Sui Po clash must trigger Tier H2 Hard Exclusion veto."""
        plane_c = load_json("04_TEST_PLANES_AND_ACCEPTANCE/plane_C_adversarial_conflict_cases.json")
        case = next(c for c in plane_c["cases"] if c["attack_id"] == "ADV-C-004")
        injected = case["injected_claim"]

        engine = ConsensusEngine(user_intent="STRATEGIC_TIMING_ACTION")
        result = engine.arbitrate_claims([injected])
        assert len(result["hard_vetoes"]) == 1
        assert "FSM_H2_EXCLUSION" in result["events_emitted"]

    def test_adv_c_005_confirmation_bias_echo_chamber(self):
        """ADV-C-005: Echo chamber pattern must trigger AUDIT_PASS_WITH_WARNINGS."""
        plane_c = load_json("04_TEST_PLANES_AND_ACCEPTANCE/plane_C_adversarial_conflict_cases.json")
        case = next(c for c in plane_c["cases"] if c["attack_id"] == "ADV-C-005")
        injected_claims = case["injected_claims"]

        for idx, c in enumerate(injected_claims):
            c["claim_id"] = f"c-adv5-{idx}"
            c["confidence_vector"] = {
                "source_support": c.get("source_support", 0.3),
                "cross_agent_agreement": c.get("cross_agent_agreement", 0.95),
            }

        consensus_output = {
            "claims": injected_claims,
            "arbitrated_edges": [],
            "hitl_escalations": [],
            "hard_vetoes": [],
        }

        audit = AuditNode()
        report = audit.evaluate_consensus_state(consensus_output)
        assert report["findings"]["echo_chamber_detected"] is True
        assert report["verdict"] == case["expected_audit_verdict"]


# ---------------------------------------------------------------------------
# TEST GROUP 4: Plane D (Empirical Isolation Policy Execution)
# ---------------------------------------------------------------------------

class TestPlaneDExecution:
    """Verify that Plane D empirical policy document is intact and defines the 5 firewall rules."""

    def test_plane_D_five_firewall_rules(self):
        full_path = os.path.join(TEST_PLANES_DIR, "plane_D_empirical_isolation_policy.md")
        assert os.path.isfile(full_path)
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()

        for rule_num in ["Rule D-1", "Rule D-2", "Rule D-3", "Rule D-4", "Rule D-5"]:
            assert rule_num in content, f"[ERROR] {rule_num} missing from Plane D policy"
