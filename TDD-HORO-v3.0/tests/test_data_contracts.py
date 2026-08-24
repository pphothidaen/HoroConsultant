"""
pytest validation suite for Horo Architecture v3.0 — Data Contracts
TICKET-HORO30-002: Schema conformance and structural integrity tests

Run: python3 -m pytest TDD-HORO-v3.0/tests/test_data_contracts.py -v
"""
import json
import os
import re
import pytest

# Base path to TDD-HORO-v3.0 directory
BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
CONTRACTS_DIR = os.path.join(BASE_DIR, "01_DATA_CONTRACTS")
TEST_PLANES_DIR = os.path.join(BASE_DIR, "04_TEST_PLANES_AND_ACCEPTANCE")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_json(relative_path: str) -> dict:
    """Load and parse a JSON file relative to BASE_DIR."""
    full_path = os.path.join(BASE_DIR, relative_path)
    assert os.path.isfile(full_path), f"[ERROR] Required file not found: {full_path}"
    with open(full_path, "r", encoding="utf-8") as f:
        return json.load(f)


def file_exists(relative_path: str) -> bool:
    return os.path.isfile(os.path.join(BASE_DIR, relative_path))


def file_text(relative_path: str) -> str:
    full_path = os.path.join(BASE_DIR, relative_path)
    assert os.path.isfile(full_path), f"[ERROR] Required file not found: {full_path}"
    with open(full_path, "r", encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# TEST GROUP 1: Directory Structure Integrity
# ---------------------------------------------------------------------------

class TestDirectoryStructure:
    """Verify WBS directory structure is complete."""

    def test_wbs_root_exists(self):
        assert os.path.isdir(BASE_DIR), "[ERROR] TDD-HORO-v3.0/ root directory missing"

    def test_01_data_contracts_exists(self):
        assert os.path.isdir(os.path.join(BASE_DIR, "01_DATA_CONTRACTS")), \
            "[ERROR] 01_DATA_CONTRACTS/ missing"

    def test_01_proto_subdir(self):
        assert os.path.isdir(os.path.join(CONTRACTS_DIR, "proto")), \
            "[ERROR] 01_DATA_CONTRACTS/proto/ missing"

    def test_01_schemas_subdir(self):
        assert os.path.isdir(os.path.join(CONTRACTS_DIR, "schemas")), \
            "[ERROR] 01_DATA_CONTRACTS/schemas/ missing"

    def test_01_grammar_subdir(self):
        assert os.path.isdir(os.path.join(CONTRACTS_DIR, "grammar")), \
            "[ERROR] 01_DATA_CONTRACTS/grammar/ missing"

    def test_02_engine_interfaces_exists(self):
        assert os.path.isdir(os.path.join(BASE_DIR, "02_ENGINE_INTERFACES")), \
            "[ERROR] 02_ENGINE_INTERFACES/ missing"

    def test_03_storage_exists(self):
        assert os.path.isdir(os.path.join(BASE_DIR, "03_STORAGE_AND_EVENT_SOURCING")), \
            "[ERROR] 03_STORAGE_AND_EVENT_SOURCING/ missing"

    def test_04_test_planes_exists(self):
        assert os.path.isdir(TEST_PLANES_DIR), \
            "[ERROR] 04_TEST_PLANES_AND_ACCEPTANCE/ missing"


# ---------------------------------------------------------------------------
# TEST GROUP 2: Proto File Validation
# ---------------------------------------------------------------------------

class TestProtoFile:
    """Validate astro_kernel_service.proto syntax and required declarations."""

    def test_proto_file_exists(self):
        assert file_exists("01_DATA_CONTRACTS/proto/astro_kernel_service.proto"), \
            "[ERROR] astro_kernel_service.proto not found"

    def test_proto3_syntax_declared(self):
        content = file_text("01_DATA_CONTRACTS/proto/astro_kernel_service.proto")
        assert 'syntax = "proto3"' in content, \
            '[ERROR] proto3 syntax declaration missing — must contain: syntax = "proto3"'

    def test_service_definition_present(self):
        content = file_text("01_DATA_CONTRACTS/proto/astro_kernel_service.proto")
        assert "service AstroKernelService" in content, \
            "[ERROR] AstroKernelService service definition not found"

    def test_compute_solar_longitude_rpc(self):
        content = file_text("01_DATA_CONTRACTS/proto/astro_kernel_service.proto")
        assert "ComputeSolarLongitude" in content, \
            "[ERROR] ComputeSolarLongitude RPC method not declared"

    def test_compute_planetary_positions_rpc(self):
        content = file_text("01_DATA_CONTRACTS/proto/astro_kernel_service.proto")
        assert "ComputePlanetaryPositions" in content, \
            "[ERROR] ComputePlanetaryPositions RPC method not declared"

    def test_convert_timescale_rpc(self):
        content = file_text("01_DATA_CONTRACTS/proto/astro_kernel_service.proto")
        assert "ConvertTimescale" in content, \
            "[ERROR] ConvertTimescale RPC method not declared"

    def test_astro_request_message(self):
        content = file_text("01_DATA_CONTRACTS/proto/astro_kernel_service.proto")
        assert "message AstroRequest" in content, \
            "[ERROR] AstroRequest message not defined"

    def test_planet_id_enum(self):
        content = file_text("01_DATA_CONTRACTS/proto/astro_kernel_service.proto")
        assert "enum PlanetID" in content, \
            "[ERROR] PlanetID enum not defined"


# ---------------------------------------------------------------------------
# TEST GROUP 3: Claim Emission Schema Validation
# ---------------------------------------------------------------------------

class TestClaimEmissionSchema:
    """Validate claim_emission_v3.0.json structure and required fields."""

    def test_schema_file_exists(self):
        assert file_exists("01_DATA_CONTRACTS/schemas/claim_emission_v3.0.json"), \
            "[ERROR] claim_emission_v3.0.json not found"

    def test_schema_is_valid_json(self):
        schema = load_json("01_DATA_CONTRACTS/schemas/claim_emission_v3.0.json")
        assert isinstance(schema, dict), "[ERROR] claim_emission_v3.0.json is not a valid JSON object"

    def test_schema_version_field(self):
        schema = load_json("01_DATA_CONTRACTS/schemas/claim_emission_v3.0.json")
        assert schema.get("$schema_version") == "3.0.0", \
            "[ERROR] $schema_version must be '3.0.0'"

    def test_required_top_level_fields(self):
        schema = load_json("01_DATA_CONTRACTS/schemas/claim_emission_v3.0.json")
        required = schema.get("required", [])
        for field in ["node_id", "tradition_domain", "claims"]:
            assert field in required, f"[ERROR] Required field '{field}' missing from schema"

    def test_atomic_claim_definition(self):
        schema = load_json("01_DATA_CONTRACTS/schemas/claim_emission_v3.0.json")
        defs = schema.get("definitions", {})
        assert "AtomicClaim" in defs, "[ERROR] AtomicClaim definition missing from schema"

    def test_epistemic_trace_definition(self):
        schema = load_json("01_DATA_CONTRACTS/schemas/claim_emission_v3.0.json")
        defs = schema.get("definitions", {})
        assert "EpistemicTrace" in defs, "[ERROR] EpistemicTrace definition missing"

    def test_confidence_vector_definition(self):
        schema = load_json("01_DATA_CONTRACTS/schemas/claim_emission_v3.0.json")
        defs = schema.get("definitions", {})
        assert "ConfidenceVector" in defs, "[ERROR] ConfidenceVector definition missing"

    def test_confidence_vector_has_5_dimensions(self):
        schema = load_json("01_DATA_CONTRACTS/schemas/claim_emission_v3.0.json")
        cv = schema["definitions"]["ConfidenceVector"]["properties"]
        expected_dims = [
            "calculation_integrity", "rule_match_strength",
            "source_support", "interpretation_stability", "cross_agent_agreement"
        ]
        for dim in expected_dims:
            assert dim in cv, f"[ERROR] Confidence vector dimension '{dim}' missing"

    def test_potential_conflict_definition(self):
        schema = load_json("01_DATA_CONTRACTS/schemas/claim_emission_v3.0.json")
        defs = schema.get("definitions", {})
        assert "PotentialConflict" in defs, "[ERROR] PotentialConflict definition missing"

    def test_tradition_domain_enum_completeness(self):
        schema = load_json("01_DATA_CONTRACTS/schemas/claim_emission_v3.0.json")
        enum_values = schema["properties"]["tradition_domain"]["enum"]
        expected_domains = [
            "ming_xue_bazi", "ming_xue_ziwei", "ming_xue_qi_zheng",
            "san_shi_qi_men", "san_shi_da_liu_ren", "san_shi_tai_yi",
            "xiang_xue_feng_shui", "xiang_xue_mian_xiang",
            "ze_ji_xue", "bu_shi_liu_yao"
        ]
        for domain in expected_domains:
            assert domain in enum_values, \
                f"[ERROR] Tradition domain '{domain}' missing from enum"

    def test_sample_valid_claim_object(self):
        """Structural test: manually verify a sample claim object has correct fields."""
        sample_claim = {
            "node_id": "@Horo_BaZi_Node",
            "tradition_domain": "ming_xue_bazi",
            "claims": [
                {
                    "claim_id": "12345678-1234-4123-a123-123456789012",
                    "materiality_weight": 0.85,
                    "epistemic_trace": {
                        "source_corpus": "滴天髓",
                        "locator": "论身强",
                        "applied_rule_id": "BAZI-STRENGTH-001",
                        "derived_from_calc_hash": "a" * 64
                    },
                    "statement": "Day Master Geng-Metal is Strong per BAZI-STRENGTH-001",
                    "confidence_vector": {
                        "calculation_integrity": 1.0,
                        "rule_match_strength": 0.9,
                        "source_support": 0.85,
                        "interpretation_stability": 0.8,
                        "cross_agent_agreement": 0.0
                    },
                    "potential_conflicts": []
                }
            ]
        }
        # Structural assertions
        assert sample_claim["node_id"].startswith("@Horo_")
        assert 0.0 <= sample_claim["claims"][0]["materiality_weight"] <= 1.0
        cv = sample_claim["claims"][0]["confidence_vector"]
        for v in cv.values():
            assert 0.0 <= v <= 1.0, f"[ERROR] Confidence value {v} out of [0,1] range"


# ---------------------------------------------------------------------------
# TEST GROUP 4: Convention Profile Schema Validation
# ---------------------------------------------------------------------------

class TestConventionProfileSchema:
    """Validate convention_profile.json structure."""

    def test_schema_file_exists(self):
        assert file_exists("01_DATA_CONTRACTS/schemas/convention_profile.json"), \
            "[ERROR] convention_profile.json not found"

    def test_schema_is_valid_json(self):
        schema = load_json("01_DATA_CONTRACTS/schemas/convention_profile.json")
        assert isinstance(schema, dict), "[ERROR] convention_profile.json is not valid JSON"

    def test_schema_version(self):
        schema = load_json("01_DATA_CONTRACTS/schemas/convention_profile.json")
        assert schema.get("$schema_version") == "3.0.0", \
            "[ERROR] $schema_version must be '3.0.0'"

    def test_profile_hash_field_exists(self):
        schema = load_json("01_DATA_CONTRACTS/schemas/convention_profile.json")
        props = schema.get("properties", {})
        assert "profile_hash" in props, "[ERROR] profile_hash field missing — required for reproducibility"

    def test_profile_hash_pattern_sha256(self):
        schema = load_json("01_DATA_CONTRACTS/schemas/convention_profile.json")
        hash_pattern = schema["properties"]["profile_hash"].get("pattern", "")
        assert "a-f0-9" in hash_pattern and "64" in hash_pattern, \
            "[ERROR] profile_hash pattern should match SHA-256 hex format ([a-f0-9]{64})"

    def test_canonical_corpus_array(self):
        schema = load_json("01_DATA_CONTRACTS/schemas/convention_profile.json")
        props = schema.get("properties", {})
        assert "canonical_corpus" in props, "[ERROR] canonical_corpus field missing"
        assert props["canonical_corpus"]["type"] == "array", \
            "[ERROR] canonical_corpus must be an array"

    def test_canonical_book_definition(self):
        schema = load_json("01_DATA_CONTRACTS/schemas/convention_profile.json")
        defs = schema.get("definitions", {})
        assert "CanonicalBook" in defs, "[ERROR] CanonicalBook definition missing"

    def test_calculation_conventions_definition(self):
        schema = load_json("01_DATA_CONTRACTS/schemas/convention_profile.json")
        defs = schema.get("definitions", {})
        assert "CalculationConventions" in defs, "[ERROR] CalculationConventions definition missing"


# ---------------------------------------------------------------------------
# TEST GROUP 5: Tri-Graph Node/Edge Schema Validation
# ---------------------------------------------------------------------------

class TestTriGraphSchema:
    """Validate tri_graph_node_edge.json edge ontology completeness."""

    def test_schema_file_exists(self):
        assert file_exists("01_DATA_CONTRACTS/schemas/tri_graph_node_edge.json"), \
            "[ERROR] tri_graph_node_edge.json not found"

    def test_schema_is_valid_json(self):
        schema = load_json("01_DATA_CONTRACTS/schemas/tri_graph_node_edge.json")
        assert isinstance(schema, dict), "[ERROR] tri_graph_node_edge.json is not valid JSON"

    def test_schema_version(self):
        schema = load_json("01_DATA_CONTRACTS/schemas/tri_graph_node_edge.json")
        assert schema.get("$schema_version") == "3.0.0"

    def test_edge_ontology_registry_present(self):
        schema = load_json("01_DATA_CONTRACTS/schemas/tri_graph_node_edge.json")
        defs = schema.get("definitions", {})
        assert "EdgeOntologyRegistry" in defs, "[ERROR] EdgeOntologyRegistry missing"

    def test_edge_type_contradicts(self):
        schema = load_json("01_DATA_CONTRACTS/schemas/tri_graph_node_edge.json")
        ontology = schema["definitions"]["EdgeOntologyRegistry"]["properties"]
        assert "contradicts" in ontology, "[ERROR] 'contradicts' edge type missing"

    def test_edge_type_supports(self):
        schema = load_json("01_DATA_CONTRACTS/schemas/tri_graph_node_edge.json")
        ontology = schema["definitions"]["EdgeOntologyRegistry"]["properties"]
        assert "supports" in ontology, "[ERROR] 'supports' edge type missing"

    def test_edge_type_qualifies(self):
        schema = load_json("01_DATA_CONTRACTS/schemas/tri_graph_node_edge.json")
        ontology = schema["definitions"]["EdgeOntologyRegistry"]["properties"]
        assert "qualifies" in ontology, "[ERROR] 'qualifies' edge type missing"

    def test_edge_type_supersedes(self):
        schema = load_json("01_DATA_CONTRACTS/schemas/tri_graph_node_edge.json")
        ontology = schema["definitions"]["EdgeOntologyRegistry"]["properties"]
        assert "supersedes" in ontology, "[ERROR] 'supersedes' edge type missing"

    def test_contradicts_is_symmetric(self):
        schema = load_json("01_DATA_CONTRACTS/schemas/tri_graph_node_edge.json")
        contradicts = schema["definitions"]["EdgeOntologyRegistry"]["properties"]["contradicts"]
        assert contradicts["properties"]["symmetric"]["const"] is True, \
            "[ERROR] 'contradicts' edge must be symmetric=true"

    def test_contradicts_is_not_transitive(self):
        schema = load_json("01_DATA_CONTRACTS/schemas/tri_graph_node_edge.json")
        contradicts = schema["definitions"]["EdgeOntologyRegistry"]["properties"]["contradicts"]
        assert contradicts["properties"]["transitive"]["const"] is False, \
            "[ERROR] 'contradicts' edge must be transitive=false"

    def test_supersedes_is_transitive(self):
        schema = load_json("01_DATA_CONTRACTS/schemas/tri_graph_node_edge.json")
        supersedes = schema["definitions"]["EdgeOntologyRegistry"]["properties"]["supersedes"]
        assert supersedes["properties"]["transitive"]["const"] is True, \
            "[ERROR] 'supersedes' edge must be transitive=true"

    def test_supersedes_subtypes(self):
        schema = load_json("01_DATA_CONTRACTS/schemas/tri_graph_node_edge.json")
        supersedes = schema["definitions"]["EdgeOntologyRegistry"]["properties"]["supersedes"]
        subtypes = supersedes["properties"]["subtypes"]["const"]
        assert "direct_supersedes" in subtypes, "[ERROR] direct_supersedes subtype missing"
        assert "effective_supersedes" in subtypes, "[ERROR] effective_supersedes subtype missing"

    def test_audit_metrics_present(self):
        schema = load_json("01_DATA_CONTRACTS/schemas/tri_graph_node_edge.json")
        defs = schema.get("definitions", {})
        assert "AuditMetrics" in defs, "[ERROR] AuditMetrics definition missing"

    def test_lciw_threshold(self):
        schema = load_json("01_DATA_CONTRACTS/schemas/tri_graph_node_edge.json")
        lcw = schema["definitions"]["AuditMetrics"]["properties"]["LCIw"]["properties"]
        assert lcw["threshold_pass"]["const"] == 0.85, \
            "[ERROR] LCIw AUDIT_PASS threshold must be 0.85"

    def test_rniw_threshold(self):
        schema = load_json("01_DATA_CONTRACTS/schemas/tri_graph_node_edge.json")
        rni = schema["definitions"]["AuditMetrics"]["properties"]["RNIw"]["properties"]
        assert rni["threshold_pass"]["const"] == 0.15, \
            "[ERROR] RNIw AUDIT_PASS threshold must be 0.15"


# ---------------------------------------------------------------------------
# TEST GROUP 6: EBNF Grammar Validation
# ---------------------------------------------------------------------------

class TestEBNFGrammar:
    """Validate horo_rule_dsl.ebnf structure and production rule count."""

    def test_ebnf_file_exists(self):
        assert file_exists("01_DATA_CONTRACTS/grammar/horo_rule_dsl.ebnf"), \
            "[ERROR] horo_rule_dsl.ebnf not found"

    def test_ebnf_has_minimum_productions(self):
        content = file_text("01_DATA_CONTRACTS/grammar/horo_rule_dsl.ebnf")
        # Count production rules: lines containing "=" that are not inside comments
        non_comment_lines = [l for l in content.split("\n")
                             if not l.strip().startswith("(*") and "=" in l and ";" in l]
        assert len(non_comment_lines) >= 10, \
            f"[ERROR] EBNF must have >= 10 production rules, found {len(non_comment_lines)}"

    def test_ebnf_has_rule_definition(self):
        content = file_text("01_DATA_CONTRACTS/grammar/horo_rule_dsl.ebnf")
        assert "rule_definition" in content, "[ERROR] rule_definition production missing"

    def test_ebnf_has_epistemic_chain_elements(self):
        content = file_text("01_DATA_CONTRACTS/grammar/horo_rule_dsl.ebnf")
        for term in ["claim_emission", "rule_body", "condition_block", "action_block"]:
            assert term in content, f"[ERROR] EBNF production '{term}' missing"

    def test_ebnf_has_emit_claim_action(self):
        content = file_text("01_DATA_CONTRACTS/grammar/horo_rule_dsl.ebnf")
        assert "EMIT_CLAIM" in content, "[ERROR] EMIT_CLAIM action not defined in grammar"

    def test_ebnf_has_tradition_domain_enum(self):
        content = file_text("01_DATA_CONTRACTS/grammar/horo_rule_dsl.ebnf")
        assert "ming_xue_bazi" in content, "[ERROR] ming_xue_bazi not in tradition_domain enum"

    def test_ebnf_has_fsm_trigger(self):
        content = file_text("01_DATA_CONTRACTS/grammar/horo_rule_dsl.ebnf")
        assert "TRIGGER_FSM" in content, "[ERROR] TRIGGER_FSM action not defined"


# ---------------------------------------------------------------------------
# TEST GROUP 7: Test Plane Files Validation
# ---------------------------------------------------------------------------

class TestTestPlaneFiles:
    """Verify all Test Plane files exist and have correct structure."""

    def test_plane_A_exists(self):
        assert file_exists("04_TEST_PLANES_AND_ACCEPTANCE/plane_A_astronomy_golden_vectors.json"), \
            "[ERROR] plane_A_astronomy_golden_vectors.json missing"

    def test_plane_A_has_test_vectors(self):
        data = load_json("04_TEST_PLANES_AND_ACCEPTANCE/plane_A_astronomy_golden_vectors.json")
        vectors = data.get("test_vectors", [])
        assert len(vectors) >= 3, f"[ERROR] Plane A must have >= 3 test vectors, found {len(vectors)}"

    def test_plane_A_vector_structure(self):
        data = load_json("04_TEST_PLANES_AND_ACCEPTANCE/plane_A_astronomy_golden_vectors.json")
        for v in data["test_vectors"]:
            assert "test_id" in v, "[ERROR] test_id missing from Plane A vector"
            assert "input" in v, "[ERROR] input missing from Plane A vector"
            assert "source" in v, "[ERROR] source missing from Plane A vector"

    def test_plane_B_exists(self):
        assert file_exists("04_TEST_PLANES_AND_ACCEPTANCE/plane_B_tradition_conformance_cases.json"), \
            "[ERROR] plane_B_tradition_conformance_cases.json missing"

    def test_plane_B_has_cases(self):
        data = load_json("04_TEST_PLANES_AND_ACCEPTANCE/plane_B_tradition_conformance_cases.json")
        cases = data.get("conformance_cases", [])
        assert len(cases) >= 5, f"[ERROR] Plane B must have >= 5 conformance cases, found {len(cases)}"

    def test_plane_C_exists(self):
        assert file_exists("04_TEST_PLANES_AND_ACCEPTANCE/plane_C_adversarial_conflict_cases.json"), \
            "[ERROR] plane_C_adversarial_conflict_cases.json missing"

    def test_plane_C_has_cases(self):
        data = load_json("04_TEST_PLANES_AND_ACCEPTANCE/plane_C_adversarial_conflict_cases.json")
        cases = data.get("cases", [])
        assert len(cases) >= 5, f"[ERROR] Plane C must have >= 5 adversarial cases, found {len(cases)}"

    def test_plane_C_adversarial_categories(self):
        data = load_json("04_TEST_PLANES_AND_ACCEPTANCE/plane_C_adversarial_conflict_cases.json")
        for case in data["cases"]:
            assert "attack_type" in case, f"[ERROR] attack_type missing in case {case.get('attack_id')}"
            assert "expected_fsm_response" in case, \
                f"[ERROR] expected_fsm_response missing in case {case.get('attack_id')}"
            assert "expected_audit_verdict" in case, \
                f"[ERROR] expected_audit_verdict missing in case {case.get('attack_id')}"

    def test_plane_D_exists(self):
        assert file_exists("04_TEST_PLANES_AND_ACCEPTANCE/plane_D_empirical_isolation_policy.md"), \
            "[ERROR] plane_D_empirical_isolation_policy.md missing"

    def test_plane_D_has_firewall_rules(self):
        content = file_text("04_TEST_PLANES_AND_ACCEPTANCE/plane_D_empirical_isolation_policy.md")
        assert "Rule D-1" in content, "[ERROR] Rule D-1 missing from empirical isolation policy"
        assert "Firewall" in content or "firewall" in content, \
            "[ERROR] Firewall rules not mentioned in Plane D policy"


# ---------------------------------------------------------------------------
# TEST GROUP 8: Placeholder Directories
# ---------------------------------------------------------------------------

class TestPlaceholderDirectories:
    """Verify placeholder READMEs exist for deferred sprint directories."""

    def test_02_readme_exists(self):
        assert file_exists("02_ENGINE_INTERFACES/README.md"), \
            "[ERROR] 02_ENGINE_INTERFACES/README.md placeholder missing"

    def test_03_readme_exists(self):
        assert file_exists("03_STORAGE_AND_EVENT_SOURCING/README.md"), \
            "[ERROR] 03_STORAGE_AND_EVENT_SOURCING/README.md placeholder missing"
