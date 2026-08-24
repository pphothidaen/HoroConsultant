"""
pytest validation suite for Horo Architecture v3.0 — Storage and Event Sourcing
Sprint 3: 03_STORAGE_AND_EVENT_SOURCING (Cypher schema, Merkle DAG spec, Event Ledger stream spec)

Run: python3 -m pytest TDD-HORO-v3.0/tests/test_storage_and_event_sourcing.py -v
"""
import hashlib
import json
import os
import pytest

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
STORAGE_DIR = os.path.join(BASE_DIR, "03_STORAGE_AND_EVENT_SOURCING")


def file_text(relative_path: str) -> str:
    full_path = os.path.join(BASE_DIR, relative_path)
    assert os.path.isfile(full_path), f"[ERROR] File not found: {full_path}"
    with open(full_path, "r", encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# TEST GROUP 1: Neo4j Cypher Schema Validation
# ---------------------------------------------------------------------------

class TestCypherSchema:
    """Validate cypher/semantic_graph_schema.cql structure and constraints."""

    def test_cypher_file_exists(self):
        full_path = os.path.join(STORAGE_DIR, "cypher", "semantic_graph_schema.cql")
        assert os.path.isfile(full_path), "[ERROR] semantic_graph_schema.cql not found"

    def test_uniqueness_constraints_present(self):
        content = file_text("03_STORAGE_AND_EVENT_SOURCING/cypher/semantic_graph_schema.cql")
        expected_constraints = [
            "c_session_id_unique",
            "c_deriv_node_uid_unique",
            "c_claim_id_unique",
            "c_rule_id_unique",
            "c_passage_id_unique",
            "c_event_uid_unique",
            "c_agent_node_id_unique"
        ]
        for c in expected_constraints:
            assert c in content, f"[ERROR] Constraint '{c}' missing from Cypher schema"

    def test_indexes_present(self):
        content = file_text("03_STORAGE_AND_EVENT_SOURCING/cypher/semantic_graph_schema.cql")
        expected_indexes = [
            "idx_claim_domain",
            "idx_claim_materiality",
            "idx_claim_session",
            "idx_deriv_content_hash",
            "idx_event_sequence"
        ]
        for idx in expected_indexes:
            assert idx in content, f"[ERROR] Index '{idx}' missing from Cypher schema"

    def test_relationship_types_documented(self):
        content = file_text("03_STORAGE_AND_EVENT_SOURCING/cypher/semantic_graph_schema.cql")
        for rel in [":CONTRADICTS", ":SUPERCEDES", ":SUPPORTS", ":QUALIFIES", ":DERIVES_FROM"]:
            assert rel in content, f"[ERROR] Relationship type '{rel}' missing from Cypher schema"

    def test_audit_queries_present(self):
        content = file_text("03_STORAGE_AND_EVENT_SOURCING/cypher/semantic_graph_schema.cql")
        assert "LCIw" in content, "[ERROR] LCIw calculation query missing"
        assert "RNIw" in content, "[ERROR] RNIw calculation query missing"
        assert "DERIVES_FROM" in content, "[ERROR] Derivation traceback query missing"


# ---------------------------------------------------------------------------
# TEST GROUP 2: Derivation DAG Immutability Spec Validation
# ---------------------------------------------------------------------------

class TestDerivationDAGSpec:
    """Validate specs/derivation_dag_immutability.md."""

    def test_spec_file_exists(self):
        full_path = os.path.join(STORAGE_DIR, "specs", "derivation_dag_immutability.md")
        assert os.path.isfile(full_path), "[ERROR] derivation_dag_immutability.md not found"

    def test_merkle_hash_formula_present(self):
        content = file_text("03_STORAGE_AND_EVENT_SOURCING/specs/derivation_dag_immutability.md")
        assert "SHA256" in content
        assert "JCS" in content or "Canonical" in content

    def test_acyclicity_invariant_present(self):
        content = file_text("03_STORAGE_AND_EVENT_SOURCING/specs/derivation_dag_immutability.md")
        assert "Acyclicity" in content or "acyclic" in content
        assert "Reachable" in content or "cycle" in content

    def test_reproducibility_tiers_present(self):
        content = file_text("03_STORAGE_AND_EVENT_SOURCING/specs/derivation_dag_immutability.md")
        for tier in ["$R_0$", "$R_1$", "$R_2$", "$R_3$", "$R_4$"]:
            assert tier in content, f"[ERROR] Reproducibility tier '{tier}' missing from spec"


# ---------------------------------------------------------------------------
# TEST GROUP 3: Event Ledger Stream Spec Validation
# ---------------------------------------------------------------------------

class TestEventLedgerStreamSpec:
    """Validate specs/event_ledger_stream.md."""

    def test_spec_file_exists(self):
        full_path = os.path.join(STORAGE_DIR, "specs", "event_ledger_stream.md")
        assert os.path.isfile(full_path), "[ERROR] event_ledger_stream.md not found"

    def test_17_canonical_event_types_present(self):
        content = file_text("03_STORAGE_AND_EVENT_SOURCING/specs/event_ledger_stream.md")
        expected_events = [
            "PIPELINE_STARTED",
            "L2_CALCULATION_COMPLETED",
            "CLAIM_EMITTED",
            "FSM_H0_TRIGGERED",
            "FSM_H1_TRIGGERED",
            "FSM_H1_RECOMPUTE",
            "FSM_H1_QUARANTINE",
            "FSM_H2_EXCLUSION",
            "FSM_H3_ARBITRATION",
            "FSM_H3_HITL_ESCALATION",
            "AUDIT_PASS",
            "AUDIT_PASS_WITH_WARNINGS",
            "AUDIT_FAIL_RECOMPUTE",
            "AUDIT_FAIL_ESCALATE",
            "COMPOSER_OUTPUT_EMITTED",
            "PIPELINE_COMPLETED",
            "PIPELINE_ABORTED"
        ]
        for ev in expected_events:
            assert ev in content, f"[ERROR] Canonical event type '{ev}' missing from ledger spec"

    def test_hash_chaining_formula(self):
        content = file_text("03_STORAGE_AND_EVENT_SOURCING/specs/event_ledger_stream.md")
        assert "h_n = " in content or "h_n" in content
        assert "previous_event_hash" in content
        assert "sequence_number" in content


# ---------------------------------------------------------------------------
# TEST GROUP 4: Functional Cryptographic Verification Algorithms
# ---------------------------------------------------------------------------

class TestFunctionalAlgorithms:
    """Test executable Python algorithms implementing Merkle DAG and Event Ledger specifications."""

    def test_merkle_dag_node_hashing(self):
        """Verify Merkle DAG hash computation is deterministic and changes when parent changes."""
        def compute_node_hash(payload: dict, parent_hashes: list[str]) -> str:
            canonical_json = json.dumps(payload, sort_keys=True, separators=(',', ':'))
            sorted_parents = "".join(sorted(parent_hashes)) if parent_hashes else "ROOT_NODE"
            combined = canonical_json.encode('utf-8') + b"||" + sorted_parents.encode('utf-8')
            return hashlib.sha256(combined).hexdigest()

        # Root node
        root_payload = {"stage": "L1", "utc": "2026-08-24T12:00:00Z", "lat": 13.75}
        h_root = compute_node_hash(root_payload, [])
        assert len(h_root) == 64

        # Child node
        child_payload = {"stage": "L2", "bazi_year": "BingWu"}
        h_child = compute_node_hash(child_payload, [h_root])
        assert len(h_child) == 64
        assert h_child != h_root

        # Determinism check
        assert compute_node_hash(root_payload, []) == h_root
        assert compute_node_hash(child_payload, [h_root]) == h_child

    def test_event_ledger_hash_chaining_and_tamper_detection(self):
        """Verify that event ledger hash-chaining correctly detects tampering."""
        def hash_event(prev_hash: str, seq: int, session_id: str, ev_type: str, payload: dict) -> str:
            canonical_payload = json.dumps(payload, sort_keys=True, separators=(',', ':'))
            blob = f"{prev_hash}\x00{seq}\x00{session_id}\x00{ev_type}\x00{canonical_payload}".encode('utf-8')
            return hashlib.sha256(blob).hexdigest()

        session = "11111111-1111-4111-a111-111111111111"
        genesis = "0" * 64

        # Event 1: PIPELINE_STARTED
        e1_payload = {"user": "test_user"}
        h1 = hash_event(genesis, 1, session, "PIPELINE_STARTED", e1_payload)

        # Event 2: L2_CALCULATION_COMPLETED
        e2_payload = {"pillars": "complete"}
        h2 = hash_event(h1, 2, session, "L2_CALCULATION_COMPLETED", e2_payload)

        # Event 3: CLAIM_EMITTED
        e3_payload = {"claim_count": 5}
        h3 = hash_event(h2, 3, session, "CLAIM_EMITTED", e3_payload)

        # Verify chain
        assert len(h1) == 64 and len(h2) == 64 and len(h3) == 64

        # Tampering simulation: alter e2 payload
        tampered_e2_payload = {"pillars": "corrupted"}
        recomputed_h2 = hash_event(h1, 2, session, "L2_CALCULATION_COMPLETED", tampered_e2_payload)
        assert recomputed_h2 != h2, "[ERROR] Tampering was not detected in hash chain!"
