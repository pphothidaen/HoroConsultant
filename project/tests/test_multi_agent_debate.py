"""
project/tests/test_multi_agent_debate.py
========================================
Unit tests for MetaphysicsDebateEngine (Multi-Agent Peer Debate & HITL Router).
"""

from __future__ import annotations

from project.core.multi_agent_debate import MetaphysicsDebateEngine, CANONICAL_TEXTS


def test_debate_engine_initialization():
    engine = MetaphysicsDebateEngine()
    assert "san_shi" in CANONICAL_TEXTS
    assert "ming_xue" in CANONICAL_TEXTS
    assert "pu_shi" in CANONICAL_TEXTS
    assert "xiang_xue" in CANONICAL_TEXTS
    assert "ze_ji" in CANONICAL_TEXTS


def test_peer_debate_execution():
    engine = MetaphysicsDebateEngine()
    res = engine.run_peer_debate({"query": "วิเคราะห์ผังดวง 5 สายวิชา", "birth_datetime": "1990-05-15 14:30:00"})

    assert res["status"] == "DEBATE_COMPLETED"
    perspectives = res["domain_perspectives"]
    assert "san_shi_master" in perspectives
    assert "ming_xue_master" in perspectives
    assert "pu_shi_master" in perspectives
    assert "xiang_xue_master" in perspectives
    assert "ze_ji_master" in perspectives

    synthesis = res["orchestrator_synthesis"]
    assert len(synthesis["consensus_facts"]) > 0
    assert len(synthesis["analytical_counter_queries"]) > 0
    assert synthesis["hitl_routing"]["status"] == "QUEUED_FOR_HUMAN_REVIEW"
