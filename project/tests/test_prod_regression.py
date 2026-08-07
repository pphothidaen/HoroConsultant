"""
project/tests/test_prod_regression.py
======================================
Production System Regression & Verification Suite for HoroConsultant.

Verifies:
1. Option 1B Architecture: Vercel Gateway Configuration (`vercel.json`).
2. Option 2A + Vector Purge Engine: Data Footprint & Purge Cleanup.
3. Option 3C & Attached Debates: 8 Domain Masters Output + Orchestrator Synthesis + HITL Routing.
4. Core API Endpoints: Health check, BaZi, ZiWei, QiMen, Da Liu Ren, IChing calculations.
"""

from __future__ import annotations

import json
from pathlib import Path
from fastapi.testclient import TestClient

from project.main import app
from project.core.multi_agent_debate import MetaphysicsDebateEngine
from scripts.cleanup_vector_store import audit_storage, purge_and_cleanup

ROOT = Path(__file__).resolve().parents[2]
client = TestClient(app)


def test_option_1b_vercel_gateway_config():
    """Verify Option 1B Vercel Gateway configuration file."""
    vercel_file = ROOT / "vercel.json"
    assert vercel_file.exists(), "vercel.json missing"
    
    data = json.loads(vercel_file.read_text(encoding="utf-8"))
    assert "rewrites" in data, "rewrites missing in vercel.json"
    
    rewrites = data["rewrites"]
    has_hf_route = any("/api/hf/" in r.get("source", "") for r in rewrites)
    assert has_hf_route, "Option 1B proxy route /api/hf/ not found in vercel.json"


def test_option_2a_vector_purge_engine():
    """Verify Option 2A Vector Purge Engine storage audit and dry-run execution."""
    audit_res = audit_storage()
    assert "vector_store_bytes" in audit_res
    assert "total_bytes" in audit_res
    
    total_mb = audit_res["total_bytes"] / (1024 * 1024)
    assert total_mb < 500.0, f"Vector storage exceeded 500MB limit ({total_mb:.2f} MB)"
    
    success = purge_and_cleanup(dry_run=True)
    assert success is True, "Purge engine dry-run audit failed"


def test_option_3c_multi_agent_debate_and_attached_perspectives():
    """Verify Option 3C debate engine attaches all 8 domain perspectives + Orchestrator synthesis."""
    engine = MetaphysicsDebateEngine()
    context = {"query": "วิเคราะห์ดวงชะตาเพื่อวางแผนธุรกิจ", "birth_datetime": "1992-08-18 10:15:00", "force_hitl": True}
    
    res = engine.run_peer_debate(context)
    assert res["status"] == "DEBATE_COMPLETED"
    
    # Verify attached 8 domain perspectives
    perspectives = res["domain_perspectives"]
    expected_domains = [
        "san_shi_master", "ming_xue_master", "pu_shi_master",
        "xiang_xue_master", "ze_ji_master", "thai_vedic_master",
        "western_astro_master", "numerology_master"
    ]
    for domain in expected_domains:
        assert domain in perspectives, f"Missing domain perspective: {domain}"
        assert "branch" in perspectives[domain]
        assert "analysis" in perspectives[domain]
        assert "canonical_citations" in perspectives[domain]
    
    # Verify Orchestrator Synthesis & HITL routing
    synthesis = res["orchestrator_synthesis"]
    assert "consensus_facts" in synthesis
    assert "analytical_counter_queries" in synthesis
    assert synthesis["hitl_routing"] is not None
    assert synthesis["hitl_routing"]["status"] == "QUEUED_FOR_HUMAN_REVIEW"


def test_core_fastapi_endpoints_regression():
    """Verify core FastAPI endpoints respond cleanly."""
    # Health check
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
    
    # BaZi calculation
    bazi_payload = {
        "birth_datetime": "1990-05-15 14:30:00",
        "longitude": 100.4930,
        "utc_offset_hours": 7.0,
        "unknown_hour": False,
        "enable_validation": False,
        "query": "ทดสอบระบบ"
    }
    res = client.post("/api/v1/bazi/interpret", json=bazi_payload)
    assert res.status_code == 200
    data = res.json()
    assert "chart" in data
    assert "interpretation" in data
    
    # ZiWei calculation
    res = client.get("/api/v1/ziwei/calculate?year=1990&month=5&day=15&hour=14&gender=male")
    assert res.status_code == 200
    assert "ming_gong_branch" in res.json()
    
    # QiMen calculation
    res = client.get("/api/v1/qimen/calculate?year=2026&month=8&day=7&hour=14")
    assert res.status_code == 200
    assert "solar_term" in res.json()
    
    # Da Liu Ren calculation
    res = client.get("/api/v1/liuren/calculate?day_stem=甲&day_branch=子&month_general=正月&hour_branch=午")
    assert res.status_code == 200
    assert "three_transmissions" in res.json()
    
    # IChing calculation
    res = client.get("/api/v1/iching/calculate?day_stem=甲")
    assert res.status_code == 200
    assert "primary_hexagram" in res.json()
