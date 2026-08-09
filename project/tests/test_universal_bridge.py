# project/tests/test_universal_bridge.py
# ===========================================================================
# Computational Metaphysics Engine — Universal Bridge Test Suite
# ===========================================================================

from project.core.universal_runtime_bridge import (
    UniversalMetaphysicsBridge,
    universal_bridge,
)
from scripts.sync_sdlc_agents import sync_all_agents


def test_sdlc_agents_sync_check():
    """Verify that all SDLC agent definitions are 100% synchronized across frameworks."""
    is_synced = sync_all_agents(check_only=True)
    assert is_synced is True, "SDLC Agent definitions are out of sync"


def test_universal_bridge_thclaws_mode(monkeypatch):
    """Test Universal Bridge in thclaws mode."""
    # Fast mock for LLM generation to avoid HTTP network delay in pytest
    from project.mcp_server import router
    monkeypatch.setattr(router, "generate", lambda prompt, system_instruction: {
        "text": "Mock thClaws local reading for unit testing.",
        "route": "mock_thclaws_route"
    })

    bridge = UniversalMetaphysicsBridge(default_mode="thclaws")
    res = bridge.run(birth_datetime="1990-05-15 14:30:00", query="ทดสอบระบบ thclaws")
    
    assert res["mode"] == "thclaws"
    assert "chart" in res
    assert "day_master" in res["chart"]
    assert "interpretation" in res
    assert res["route_used"] == "mock_thclaws_route"


def test_universal_bridge_agy_subagent_mode(monkeypatch):
    """Test Universal Bridge in agy_subagent mode."""
    from project.mcp_server import router, validator
    monkeypatch.setattr(router, "generate", lambda prompt, system_instruction: {
        "text": "Mock AGY reading.",
        "route": "mock_agy_route"
    })
    monkeypatch.setattr(validator, "validate", lambda bazi_chart, initial_interpretation, user_query: {
        "validation_status": "PASSED",
        "confidence_score": 0.95,
        "refined_analysis": "Audited AGY reading."
    })

    bridge = UniversalMetaphysicsBridge(default_mode="agy")
    res = bridge.run(birth_datetime="1990-05-15 14:30:00", query="ทดสอบระบบ agy")
    
    assert res["mode"] == "agy_subagent"
    assert "chart" in res
    assert "validation_report" in res
    assert res["validation_report"]["validation_status"] == "PASSED"


def test_universal_bridge_hybrid_mode(monkeypatch):
    """Test Universal Bridge in hybrid mode (Local thClaws + Cloud AGY Audit)."""
    from project.mcp_server import router, validator
    monkeypatch.setattr(router, "generate", lambda prompt, system_instruction: {
        "text": "Mock Hybrid initial reading.",
        "route": "mock_hybrid_route"
    })
    monkeypatch.setattr(validator, "validate", lambda bazi_chart, initial_interpretation, user_query: {
        "validation_status": "PASSED",
        "confidence_score": 0.98,
        "refined_analysis": "Final audited hybrid reading."
    })

    res = universal_bridge.run(birth_datetime="1990-05-15 14:30:00", query="ทดสอบระบบ hybrid", mode="hybrid")
    
    assert res["mode"] == "hybrid"
    assert "chart" in res
    assert res["final_audited_reading"] == "Final audited hybrid reading."
    assert res["route_used"] == "hybrid_thclaws_and_agy_mcp"
