"""
pytest validation suite for Horo Architecture v3.0 — Engine Interfaces
Sprint 2: 02_ENGINE_INTERFACES (FSM, Dynamic Arbitration, Audit Truth Table)

Run: python3 -m pytest TDD-HORO-v3.0/tests/test_engine_interfaces.py -v
"""
import csv
import json
import os
import pytest

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
INTERFACES_DIR = os.path.join(BASE_DIR, "02_ENGINE_INTERFACES")


def load_json(relative_path: str) -> dict:
    full_path = os.path.join(BASE_DIR, relative_path)
    assert os.path.isfile(full_path), f"[ERROR] File not found: {full_path}"
    with open(full_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_csv(relative_path: str) -> list[dict]:
    full_path = os.path.join(BASE_DIR, relative_path)
    assert os.path.isfile(full_path), f"[ERROR] File not found: {full_path}"
    with open(full_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


# ---------------------------------------------------------------------------
# TEST GROUP 1: Constraint State Machine (FSM) Validation
# ---------------------------------------------------------------------------

class TestConstraintStateMachine:
    """Validate fsm/constraint_state_machine.json completeness and structural consistency."""

    def test_fsm_file_exists(self):
        full_path = os.path.join(INTERFACES_DIR, "fsm", "constraint_state_machine.json")
        assert os.path.isfile(full_path), "[ERROR] constraint_state_machine.json not found"

    def test_fsm_is_valid_json(self):
        data = load_json("02_ENGINE_INTERFACES/fsm/constraint_state_machine.json")
        assert isinstance(data, dict), "[ERROR] FSM spec must be a JSON object"

    def test_fsm_version(self):
        data = load_json("02_ENGINE_INTERFACES/fsm/constraint_state_machine.json")
        assert data.get("fsm_version") == "3.0.0", "[ERROR] fsm_version must be '3.0.0'"

    def test_fsm_four_tiers_present(self):
        data = load_json("02_ENGINE_INTERFACES/fsm/constraint_state_machine.json")
        tiers = data.get("tier_definitions", {})
        for tier in ["H0", "H1", "H2", "H3"]:
            assert tier in tiers, f"[ERROR] Tier '{tier}' missing from tier_definitions"

    def test_tier_h0_fatal_abort(self):
        data = load_json("02_ENGINE_INTERFACES/fsm/constraint_state_machine.json")
        h0 = data["tier_definitions"]["H0"]
        assert h0.get("severity_level") == "FATAL"
        assert h0.get("action") == "ABORT_PIPELINE_IMMEDIATE"
        assert h0.get("recovery_allowed") is False
        assert h0.get("terminal_state") == "PIPELINE_ABORTED"

    def test_tier_h1_bounded_retries(self):
        data = load_json("02_ENGINE_INTERFACES/fsm/constraint_state_machine.json")
        h1 = data["tier_definitions"]["H1"]
        assert h1.get("max_retries") <= 3, "[ERROR] H1 max_retries must be <= 3 (bounded recovery)"
        assert "QUARANTINE" in h1.get("fallback_action", "")

    def test_tier_h2_hard_exclusion(self):
        data = load_json("02_ENGINE_INTERFACES/fsm/constraint_state_machine.json")
        h2 = data["tier_definitions"]["H2"]
        assert h2.get("veto_override_allowed") is False, "[ERROR] H2 vetoes must not be overridable"
        assert "EXCLUDE" in h2.get("action", "")

    def test_tier_h3_arbitration_and_hitl(self):
        data = load_json("02_ENGINE_INTERFACES/fsm/constraint_state_machine.json")
        h3 = data["tier_definitions"]["H3"]
        assert "DYNAMIC_ARBITRATION" in h3.get("action", "")
        assert "escalation_policy" in h3
        assert h3["escalation_policy"].get("action") == "ESCALATE_TO_HITL"

    def test_fsm_states_and_transitions_integrity(self):
        data = load_json("02_ENGINE_INTERFACES/fsm/constraint_state_machine.json")
        states = data.get("states", [])
        transitions = data.get("transitions", [])

        state_ids = {s["id"] for s in states}
        assert "INIT" in state_ids
        assert "PIPELINE_COMPLETED" in state_ids
        assert "PIPELINE_ABORTED" in state_ids
        assert "HITL_ESCALATION_QUEUE" in state_ids

        # Every transition must reference valid source and target states
        for t in transitions:
            assert t["source"] in state_ids, f"[ERROR] Transition source '{t['source']}' not in states"
            assert t["target"] in state_ids, f"[ERROR] Transition target '{t['target']}' not in states"
            assert "trigger_event" in t, f"[ERROR] Transition '{t.get('transition_id')}' missing trigger_event"


# ---------------------------------------------------------------------------
# TEST GROUP 2: Dynamic Arbitration Policy Validation
# ---------------------------------------------------------------------------

class TestDynamicArbitrationPolicy:
    """Validate policies/dynamic_arbitration.json."""

    def test_policy_file_exists(self):
        full_path = os.path.join(INTERFACES_DIR, "policies", "dynamic_arbitration.json")
        assert os.path.isfile(full_path), "[ERROR] dynamic_arbitration.json not found"

    def test_policy_version(self):
        data = load_json("02_ENGINE_INTERFACES/policies/dynamic_arbitration.json")
        assert data.get("$schema_version") == "3.0.0"

    def test_intent_priority_matrix_coverage(self):
        data = load_json("02_ENGINE_INTERFACES/policies/dynamic_arbitration.json")
        matrix = data.get("intent_priority_matrix", {})
        expected_intents = [
            "STRATEGIC_TIMING_ACTION",
            "NATAL_CHARACTER_PATH",
            "SPATIAL_LOCATION_OFFICE",
            "TACTICAL_DIVINATION_EVENT",
            "HEALTH_VITALITY",
            "RELATIONSHIP_SYNASTRY"
        ]
        for intent in expected_intents:
            assert intent in matrix, f"[ERROR] Intent '{intent}' missing from priority matrix"
            hierarchy = matrix[intent].get("priority_hierarchy", [])
            assert len(hierarchy) >= 3, f"[ERROR] Intent '{intent}' must have >= 3 prioritized domains"
            # Verify ranks are ordered 1, 2, 3...
            ranks = [item["rank"] for item in hierarchy]
            assert ranks == sorted(ranks), f"[ERROR] Ranks in intent '{intent}' not strictly ascending"

    def test_strategic_timing_priority_hierarchy(self):
        data = load_json("02_ENGINE_INTERFACES/policies/dynamic_arbitration.json")
        qimen_hierarchy = data["intent_priority_matrix"]["STRATEGIC_TIMING_ACTION"]["priority_hierarchy"]
        top_domain = qimen_hierarchy[0]["domain"]
        assert top_domain == "san_shi_qi_men", \
            f"[ERROR] STRATEGIC_TIMING_ACTION rank 1 must be 'san_shi_qi_men', got {top_domain}"

    def test_natal_path_priority_hierarchy(self):
        data = load_json("02_ENGINE_INTERFACES/policies/dynamic_arbitration.json")
        bazi_hierarchy = data["intent_priority_matrix"]["NATAL_CHARACTER_PATH"]["priority_hierarchy"]
        top_domain = bazi_hierarchy[0]["domain"]
        assert top_domain == "ming_xue_bazi", \
            f"[ERROR] NATAL_CHARACTER_PATH rank 1 must be 'ming_xue_bazi', got {top_domain}"

    def test_spatial_location_priority_hierarchy(self):
        data = load_json("02_ENGINE_INTERFACES/policies/dynamic_arbitration.json")
        fengshui_hierarchy = data["intent_priority_matrix"]["SPATIAL_LOCATION_OFFICE"]["priority_hierarchy"]
        top_domain = fengshui_hierarchy[0]["domain"]
        assert top_domain == "xiang_xue_feng_shui", \
            f"[ERROR] SPATIAL_LOCATION_OFFICE rank 1 must be 'xiang_xue_feng_shui', got {top_domain}"

    def test_arbitration_rules_presence(self):
        data = load_json("02_ENGINE_INTERFACES/policies/dynamic_arbitration.json")
        rules = data.get("arbitration_rules", [])
        rule_codes = {r["rule_code"] for r in rules}
        expected_rules = [
            "ARB-01-PRIORITY-DOMINANCE",
            "ARB-02-EQUAL-RANK-TIEBREAKER",
            "ARB-03-HARD-VETO-ABSOLUTE",
            "ARB-04-CONFIRMATION-BIAS-AUDIT"
        ]
        for rule_code in expected_rules:
            assert rule_code in rule_codes, f"[ERROR] Rule '{rule_code}' missing from arbitration rules"

    def test_hitl_escalation_criteria(self):
        data = load_json("02_ENGINE_INTERFACES/policies/dynamic_arbitration.json")
        hitl = data.get("hitl_escalation_criteria", {})
        assert hitl.get("min_severity") == 0.70
        assert hitl.get("min_materiality") == 0.75
        assert hitl.get("max_score_delta") == 0.15


# ---------------------------------------------------------------------------
# TEST GROUP 3: Audit Policy Truth Table Validation
# ---------------------------------------------------------------------------

class TestAuditPolicyTruthTable:
    """Validate matrices/audit_policy_truth_table.csv."""

    def test_truth_table_file_exists(self):
        full_path = os.path.join(INTERFACES_DIR, "matrices", "audit_policy_truth_table.csv")
        assert os.path.isfile(full_path), "[ERROR] audit_policy_truth_table.csv not found"

    def test_truth_table_has_rows(self):
        rows = load_csv("02_ENGINE_INTERFACES/matrices/audit_policy_truth_table.csv")
        assert len(rows) >= 5, f"[ERROR] Truth table must have >= 5 entries, got {len(rows)}"

    def test_truth_table_columns(self):
        rows = load_csv("02_ENGINE_INTERFACES/matrices/audit_policy_truth_table.csv")
        expected_cols = [
            "rule_id", "lciw_min", "lciw_max", "rniw_min", "rniw_max",
            "unresolved_h0_h1_h2", "false_provenance_flag", "echo_chamber_detected",
            "verdict", "action_code", "description"
        ]
        for col in expected_cols:
            assert col in rows[0], f"[ERROR] Column '{col}' missing from truth table"

    def test_all_four_verdicts_covered(self):
        rows = load_csv("02_ENGINE_INTERFACES/matrices/audit_policy_truth_table.csv")
        verdicts = {r["verdict"] for r in rows}
        expected_verdicts = [
            "AUDIT_PASS",
            "AUDIT_PASS_WITH_WARNINGS",
            "AUDIT_FAIL_RECOMPUTE",
            "AUDIT_FAIL_ESCALATE"
        ]
        for verdict in expected_verdicts:
            assert verdict in verdicts, f"[ERROR] Verdict '{verdict}' missing from truth table"

    def test_audit_pass_thresholds(self):
        rows = load_csv("02_ENGINE_INTERFACES/matrices/audit_policy_truth_table.csv")
        pass_row = next(r for r in rows if r["rule_id"] == "AUDIT-01-PASS")
        assert float(pass_row["lciw_min"]) >= 0.85, "[ERROR] AUDIT_PASS lciw_min must be >= 0.85"
        assert float(pass_row["rniw_max"]) <= 0.15, "[ERROR] AUDIT_PASS rniw_max must be <= 0.15"
        assert pass_row["verdict"] == "AUDIT_PASS"
        assert pass_row["action_code"] == "COMPOSER_RELEASE"
