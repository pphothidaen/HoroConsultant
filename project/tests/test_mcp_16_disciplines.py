"""
project/tests/test_mcp_16_disciplines.py — Comprehensive Test Suite for M1 Deliverables
=====================================================================================
Tests:
1. All 16 Metaphysics calculation engines via MCP tools (`HoroMCPTools` and `call_tool`)
2. All 18 Dynamic SVG visualizers via MCP tools
3. Question Focus Router (`question_focus_route`) and 8-Master Debate (`metaphysics_debate`)
4. MCP Server manifest compliance (`get_mcp_manifest()`)
5. FastAPI route handlers in `project.api_router` (`/api/calculate/{discipline}`, `/api/mcp/manifest`, `/api/mcp/call`, `/api/route/focus`, `/api/debate/synthesize`)
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from project.api_router import api_router
from project.mcp_server import HoroMCPTools, call_tool, get_mcp_manifest


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(api_router)
    return TestClient(app)


# ==============================================================================
# 1. 16 Calculations MCP Contract Tests
# ==============================================================================

def test_mcp_16_calculations_direct():
    # 1. BaZi
    bazi = HoroMCPTools.bazi_calculate("1990-05-15 14:30:00")
    assert "day_master" in bazi and "pillars" in bazi

    # 2. Zi Wei
    ziwei = HoroMCPTools.ziwei_calculate(1990, 5, 15, 14, "male")
    assert "ming_gong_branch" in ziwei or "palaces" in ziwei

    # 3. Qi Men
    qimen = HoroMCPTools.qimen_calculate(2026, 8, 7, 14)
    assert "solar_term" in qimen or "nine_palaces" in qimen or "palaces" in qimen

    # 4. Liu Ren
    liuren = HoroMCPTools.liuren_calculate("甲", "子", "正月", "午")
    assert "three_transmissions" in liuren or "four_lessons" in liuren

    # 5. Tai Yi
    taiyi = HoroMCPTools.tai_yi_calculate(2026, 5, 15, 14)
    assert isinstance(taiyi, dict) and len(taiyi) > 0

    # 6. I Ching
    iching = HoroMCPTools.iching_calculate("甲", seed=42)
    assert "primary_hexagram" in iching

    # 7. Liu Yao
    liuyao = HoroMCPTools.liu_yao_calculate([7, 7, 7, 7, 7, 7], 0)
    assert isinstance(liuyao, dict) and len(liuyao) > 0

    # 8. Mei Hua
    meihua = HoroMCPTools.mei_hua_calculate(2026, 5, 15, 14)
    assert isinstance(meihua, dict) and len(meihua) > 0

    # 9. Xuan Kong
    xuankong = HoroMCPTools.xuankong_calculate(180.0, 9)
    assert "sitting_mountain" in xuankong or "facing_mountain" in xuankong

    # 10. San He
    sanhe = HoroMCPTools.san_he_calculate(0.0, 180.0)
    assert "twelve_stages_map" in sanhe or "sitting_mountain" in sanhe

    # 11. Ze Ji
    zeji = HoroMCPTools.zeji_calculate("午", "申", "寅", "子")
    assert "duty_officer" in zeji and "rating_stars" in zeji

    # 12. Mian Xiang
    mianxiang = HoroMCPTools.mian_xiang_analyze({"face_shape": "round", "forehead": "high_broad"})
    assert "face_element" in mianxiang or "twelve_palaces" in mianxiang

    # 13. Thai-Vedic
    thaivedic = HoroMCPTools.thaivedic_calculate(1990, 5, 15, 14, 2)
    assert "thai_lagna" in thaivedic or "maha_thaksa" in thaivedic

    # 14. Western Uranian
    western = HoroMCPTools.western_calculate(1990, 5, 15, 14)
    assert "planets_tropical" in western or "uranian_tnps" in western

    # 15. Numerology
    numerology = HoroMCPTools.numerology_calculate("0812345678", 2, 6, 7)
    assert "satta_lek" in numerology and "chaldean_score" in numerology

    # 16. Qi Zheng Si Yu
    qizheng = HoroMCPTools.qi_zheng_calculate(2026, 5, 15, 14)
    assert "planets" in qizheng or "shadow_stars" in qizheng or isinstance(qizheng, dict)


# ==============================================================================
# 2. 18 Dynamic SVG Visualizers MCP Contract Tests
# ==============================================================================

def test_mcp_18_svg_visualizers():
    svg_tools = [
        "render_bazi_svg",
        "render_ziwei_svg",
        "render_qimen_svg",
        "render_liuren_svg",
        "render_tai_yi_svg",
        "render_iching_svg",
        "render_liu_yao_svg",
        "render_meihua_svg",
        "render_xuankong_svg",
        "render_sanhe_svg",
        "render_zeji_svg",
        "render_mianxiang_svg",
        "render_thaivedic_svg",
        "render_western_svg",
        "render_numerology_svg",
        "render_qizheng_svg",
        "render_zodiac_wheel_svg",
        "render_multimodal_matrix_svg",
    ]

    for tool_name in svg_tools:
        res = call_tool(tool_name, {"save_to_disk": False})
        assert res["success"] is True, f"Failed tool: {tool_name} with error: {res.get('error')}"
        data = res["result"]
        assert "svg_content" in data
        assert "<svg" in data["svg_content"]
        assert "</svg>" in data["svg_content"]
        assert "viewBox" in data
        assert "aspect_ratio" in data
        assert "visual_components" in data


# ==============================================================================
# 3. Question Focus Router & Debate Synthesis Contract Tests
# ==============================================================================

def test_question_focus_router_and_debate():
    # Focus Router
    res_focus = call_tool("question_focus_route", {"query": "ปี 2026 ควรย้ายงานหรือทำธุรกิจดี?"})
    assert res_focus["success"] is True
    focus_data = res_focus["result"]
    assert focus_data["classified_domain"] == "career"
    assert "focus_directives" in focus_data
    assert "recommended_engines" in focus_data

    # Multi-Agent Debate
    res_debate = call_tool("metaphysics_debate", {"query": "วิเคราะห์ดวงชะตาและฤกษ์ยามขยายกิจการ", "birth_datetime": "1990-05-15 14:30:00"})
    assert res_debate["success"] is True
    debate_data = res_debate["result"]
    assert debate_data["status"] == "DEBATE_COMPLETED"
    assert "consensus_matrix" in debate_data
    assert "domain_perspectives" in debate_data
    assert "orchestrator_synthesis" in debate_data


# ==============================================================================
# 4. Manifest Integrity Test
# ==============================================================================

def test_mcp_manifest_all_36_tools():
    manifest = get_mcp_manifest()
    assert manifest["name"] == "horo-consultant-mcp"
    assert len(manifest["tools"]) >= 36
    tool_names = {t["name"] for t in manifest["tools"]}
    
    expected_tools = [
        "bazi_calculate", "ziwei_calculate", "qimen_calculate", "liuren_calculate",
        "tai_yi_calculate", "iching_calculate", "liu_yao_calculate", "mei_hua_calculate",
        "xuankong_calculate", "san_he_calculate", "zeji_calculate", "mian_xiang_analyze",
        "thaivedic_calculate", "western_calculate", "numerology_calculate", "qi_zheng_calculate",
        "render_bazi_svg", "render_ziwei_svg", "render_qimen_svg", "render_liuren_svg",
        "render_tai_yi_svg", "render_iching_svg", "render_liu_yao_svg", "render_meihua_svg",
        "render_xuankong_svg", "render_sanhe_svg", "render_zeji_svg", "render_mianxiang_svg",
        "render_thaivedic_svg", "render_western_svg", "render_numerology_svg", "render_qizheng_svg",
        "render_zodiac_wheel_svg", "render_multimodal_matrix_svg",
        "question_focus_route", "metaphysics_debate"
    ]
    for exp in expected_tools:
        assert exp in tool_names, f"Tool '{exp}' is missing from MCP manifest"


# ==============================================================================
# 5. FastAPI Endpoints Integration Test
# ==============================================================================

def test_fastapi_endpoints(client):
    # Manifest
    r_manifest = client.get("/api/mcp/manifest")
    assert r_manifest.status_code == 200
    assert len(r_manifest.json().get("tools", [])) >= 36

    # MCP Call Tool
    r_call = client.post("/api/mcp/call", json={"tool_name": "bazi_calculate", "arguments": {"birth_datetime": "1990-05-15 14:30:00"}})
    assert r_call.status_code == 200
    assert r_call.json()["success"] is True

    # Focus Router
    r_focus = client.post("/api/route/focus", json={"query": "ความรักและการแต่งงานปีนี้"})
    assert r_focus.status_code == 200
    assert r_focus.json()["classified_domain"] == "love"

    # Debate Synthesize
    r_debate = client.post("/api/debate/synthesize", json={"query": "วิเคราะห์ดวงชะตาภาพรวม"})
    assert r_debate.status_code == 200
    assert r_debate.json()["status"] == "DEBATE_COMPLETED"

    # Universal Calculate /api/calculate/{discipline}
    disciplines = [
        ("bazi", {"birth_datetime": "1990-05-15 14:30:00"}),
        ("ziwei", {"year": 1990, "month": 5, "day": 15, "hour": 14}),
        ("qimen", {"year": 2026, "month": 8, "day": 7, "hour": 14}),
        ("liuren", {"day_stem": "甲", "day_branch": "子"}),
        ("taiyi", {"year": 2026, "month": 5, "day": 15, "hour": 14}),
        ("iching", {"day_stem": "甲", "seed": 42}),
        ("liuyao", {"lines": [7, 7, 7, 7, 7, 7]}),
        ("meihua", {"year": 2026, "month": 5, "day": 15, "hour": 14}),
        ("xuankong", {"facing_degree": 180.0, "period": 9}),
        ("sanhe", {"sitting_degree": 0.0, "facing_degree": 180.0}),
        ("zeji", {"year_branch": "午", "month_branch": "申", "day_branch": "寅"}),
        ("mianxiang", {"features": {"face_shape": "round"}}),
        ("thaivedic", {"year": 1990, "month": 5, "day": 15, "hour": 14}),
        ("western", {"year": 1990, "month": 5, "day": 15, "hour": 14}),
        ("numerology", {"text": "0812345678"}),
        ("qizheng", {"year": 2026, "month": 5, "day": 15, "hour": 14}),
    ]

    for disc, payload in disciplines:
        r_post = client.post(f"/api/calculate/{disc}", json=payload)
        assert r_post.status_code == 200, f"Universal POST failed for {disc}: {r_post.text}"

    # Dedicated calculation endpoints
    r_bazi = client.post("/api/calculate/bazi", json={"birth_datetime": "1990-05-15 14:30:00"})
    assert r_bazi.status_code == 200
    assert "day_master" in r_bazi.json()

    r_ziwei = client.post("/api/calculate/ziwei", json={"year": 1990, "month": 5, "day": 15, "hour": 14, "gender": "male"})
    assert r_ziwei.status_code == 200
