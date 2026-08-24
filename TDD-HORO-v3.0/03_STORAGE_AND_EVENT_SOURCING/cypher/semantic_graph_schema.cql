// ============================================================
// Horo Architecture v3.0 — Semantic Property Graph (G_sem) Schema
// Database Engine: Neo4j 5.x+
// Schema Version: 3.0.0
// Status: FROZEN BASELINE
// Git Tag: v3.0-storage-and-event-sourcing
// ============================================================

// ------------------------------------------------------------
// 1. UNIQUENESS & EXISTENCE CONSTRAINTS
// ------------------------------------------------------------

// Session uniqueness
CREATE CONSTRAINT c_session_id_unique IF NOT EXISTS
FOR (s:Session) REQUIRE s.session_id IS UNIQUE;

// Derivation Node UID uniqueness (G_deriv)
CREATE CONSTRAINT c_deriv_node_uid_unique IF NOT EXISTS
FOR (d:DerivationNode) REQUIRE d.node_uid IS UNIQUE;

// Semantic Claim UID uniqueness (G_sem)
CREATE CONSTRAINT c_claim_id_unique IF NOT EXISTS
FOR (c:Claim) REQUIRE c.claim_id IS UNIQUE;

// Formal Rule ID uniqueness
CREATE CONSTRAINT c_rule_id_unique IF NOT EXISTS
FOR (r:Rule) REQUIRE r.rule_id IS UNIQUE;

// Canonical Corpus Passage ID uniqueness
CREATE CONSTRAINT c_passage_id_unique IF NOT EXISTS
FOR (p:CorpusPassage) REQUIRE p.passage_id IS UNIQUE;

// Event Ledger UID uniqueness (L_event)
CREATE CONSTRAINT c_event_uid_unique IF NOT EXISTS
FOR (e:EventNode) REQUIRE e.node_uid IS UNIQUE;

// Agent Node ID uniqueness
CREATE CONSTRAINT c_agent_node_id_unique IF NOT EXISTS
FOR (a:AgentNode) REQUIRE a.node_id IS UNIQUE;


// ------------------------------------------------------------
// 2. SEARCH & TRAVERSAL INDEXES
// ------------------------------------------------------------

// Fast lookup by tradition domain
CREATE INDEX idx_claim_domain IF NOT EXISTS
FOR (c:Claim) ON (c.tradition_domain);

// Fast filtering by materiality weight for LCIw/RNIw calculations
CREATE INDEX idx_claim_materiality IF NOT EXISTS
FOR (c:Claim) ON (c.materiality_weight);

// Fast session-scoped claim retrieval
CREATE INDEX idx_claim_session IF NOT EXISTS
FOR (c:Claim) ON (c.session_id);

// Derivation hash lookup for Merkle DAG verification
CREATE INDEX idx_deriv_content_hash IF NOT EXISTS
FOR (d:DerivationNode) ON (d.content_hash);

// Event sequencing index for L_event stream replay
CREATE INDEX idx_event_sequence IF NOT EXISTS
FOR (e:EventNode) ON (e.session_id, e.sequence_number);

// Rule category index
CREATE INDEX idx_rule_category IF NOT EXISTS
FOR (r:Rule) ON (r.tradition_domain, r.category);


// ------------------------------------------------------------
// 3. NODE TAXONOMY & PROPERTY SPECIFICATION
// ------------------------------------------------------------

/*
Node Labels and Expected Properties:

(:Session {
    session_id: String (UUIDv4),
    created_at_utc: DateTime,
    user_intent: String,
    reproducibility_level: String (R0..R4),
    status: String (ACTIVE | COMPLETED | ABORTED)
})

(:AgentNode {
    node_id: String (e.g. '@Horo_BaZi_Node'),
    tradition_domain: String,
    layer: String (L3 | L4 | L5 | L6 | L7),
    model_identifier: String
})

(:DerivationNode {
    node_uid: String (SHA256 hash or UUID),
    graph_type: 'G_deriv',
    pipeline_stage: String (L0..L7),
    node_type: String (AstroState | CompiledRule | ClaimEmission | ConventionProfile | L2CalculationOutput),
    content_hash: String (SHA256),
    payload_ref: String,
    created_at_utc: DateTime,
    immutable: Boolean (true)
})

(:SemanticNode:Claim {
    claim_id: String (UUIDv4 or SHA256),
    graph_type: 'G_sem',
    session_id: String (UUIDv4),
    tradition_domain: String,
    materiality_weight: Float (0.0..1.0),
    statement: String,
    claim_type: String,
    calc_integrity: Float,
    rule_match_strength: Float,
    source_support: Float,
    interp_stability: Float,
    cross_agent_agreement: Float,
    is_quarantined: Boolean,
    created_at_utc: DateTime
})

(:SemanticNode:Rule {
    rule_id: String (e.g. 'BAZI-STRENGTH-001'),
    graph_type: 'G_sem',
    tradition_domain: String,
    category: String,
    authority_tier: Integer (1..3),
    version: String
})

(:SemanticNode:CorpusPassage {
    passage_id: String,
    source_corpus: String (e.g. '滴天髓'),
    locator: String,
    original_text: String,
    tradition_domain: String
})

(:EventNode {
    node_uid: String (SHA256),
    graph_type: 'L_event',
    session_id: String (UUIDv4),
    sequence_number: Integer,
    event_type: String,
    previous_event_hash: String (SHA256),
    event_hash: String (SHA256),
    payload_json: String,
    created_at_utc: DateTime,
    immutable: Boolean (true)
})
*/


// ------------------------------------------------------------
// 4. RELATIONSHIP ONTOLOGY & PROPERTIES
// ------------------------------------------------------------

/*
Relationship Types and Invariants:

(:Claim)-[:CONTRADICTS {
    severity: Float (0.0..1.0),
    resolved: Boolean,
    arbitration_rule: String,
    resolved_at_utc: DateTime
}]->(:Claim)
[Invariant: Symmetric in semantics, recorded bidirectionally or queried undirected]

(:Claim)-[:SUPERCEDES {
    subtype: String ('direct_supersedes' | 'effective_supersedes'),
    priority_delta: Integer,
    direct: Boolean,
    created_at_utc: DateTime
}]->(:Claim)
[Invariant: Monotonically directed, transitive closure valid]

(:Claim)-[:SUPPORTS {
    strength: Float (0.0..1.0)
}]->(:Claim)

(:Claim)-[:QUALIFIES {
    condition: String,
    scope_limitation: String
}]->(:Claim)

(:DerivationNode)-[:DERIVES_FROM {
    step_index: Integer,
    calc_hash: String
}]->(:DerivationNode)
[Invariant: Strictly acyclic DAG in G_deriv]

(:Claim)-[:APPLIED_RULE]->(:Rule)
(:Rule)-[:GROUNDED_IN]->(:CorpusPassage)
(:Claim)-[:EMITTED_BY]->(:AgentNode)
(:EventNode)-[:PRECEDES]->(:EventNode)
*/


// ------------------------------------------------------------
// 5. CANONICAL GRAPH TRAVERSAL & AUDIT QUERIES
// ------------------------------------------------------------

// Query 1: Verify G_deriv Acyclicity (Must return 0 rows)
// MATCH path = (d:DerivationNode)-[:DERIVES_FROM*]->(d)
// RETURN count(path) AS cycle_count;

// Query 2: Extract Active Unresolved Conflict Clusters
// MATCH (c1:Claim {session_id: $session_id})-[r:CONTRADICTS]-(c2:Claim {session_id: $session_id})
// WHERE r.resolved = false
// RETURN c1.claim_id AS claim_a, c1.tradition_domain AS domain_a,
//        c2.claim_id AS claim_b, c2.tradition_domain AS domain_b,
//        r.severity AS conflict_severity,
//        c1.materiality_weight AS materiality_a, c2.materiality_weight AS materiality_b;

// Query 3: Real-Time Audit Metrics Calculation (LCIw and RNIw)
// MATCH (c:Claim {session_id: $session_id})
// WITH collect(c) AS all_claims,
//      sum(c.materiality_weight) AS total_materiality,
//      sum(CASE WHEN c.source_support = 0.0 OR c.is_quarantined = true THEN c.materiality_weight ELSE 0.0 END) AS ungrounded_materiality
// OPTIONAL MATCH (c1:Claim {session_id: $session_id})-[r:CONTRADICTS]-(c2:Claim {session_id: $session_id})
// WHERE r.resolved = false
// WITH total_materiality, ungrounded_materiality,
//      coalesce(sum(r.severity * CASE WHEN c1.materiality_weight > c2.materiality_weight THEN c1.materiality_weight ELSE c2.materiality_weight END), 0.0) AS conflict_mass,
//      coalesce(sum(CASE WHEN c1.materiality_weight > c2.materiality_weight THEN c1.materiality_weight ELSE c2.materiality_weight END), 1.0) AS total_conflict_weight
// RETURN
//      (ungrounded_materiality / CASE WHEN total_materiality > 0 THEN total_materiality ELSE 1.0 END) AS RNIw,
//      (1.0 - (conflict_mass / total_conflict_weight)) AS LCIw;

// Query 4: Full Epistemic Provenance Traceback
// MATCH (c:Claim {claim_id: $claim_id})-[:APPLIED_RULE]->(r:Rule)-[:GROUNDED_IN]->(p:CorpusPassage)
// MATCH (c)-[:EMITTED_BY]->(a:AgentNode)
// RETURN c.statement AS claim_statement,
//        a.node_id AS emitting_agent,
//        r.rule_id AS applied_rule,
//        p.source_corpus AS canon_source,
//        p.locator AS canon_locator,
//        p.original_text AS canon_text;
