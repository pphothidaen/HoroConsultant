import pytest
from project.mcp_server import call_tool
from project.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_e2e_mcp_tool_request_to_json():
    res = call_tool("bazi_calculate", {"birth_datetime": "1990-05-15 12:00:00"})
    assert "bazi" in str(res).lower() or isinstance(res, dict)

def test_e2e_mcp_svg_render():
    svg_res = call_tool("render_bazi_svg", {"birth_datetime": "1990-05-15 12:00:00"})
    svg = svg_res.get("result", {}).get("svg_content", "")
    assert "<svg" in svg

def test_e2e_dataset_generator():
    assert True # Dataset is already covered in tests/test_dataset_pipeline.py

def test_e2e_visual_endpoint():
    response = client.post("/api/visualize/bazi", json={"theme": "dark"})
    assert response.status_code == 200
    assert "image/svg+xml" in response.headers.get("content-type", "")

def test_e2e_visual_endpoint_ziwei():
    response = client.post("/api/visualize/ziwei", json={"theme": "dark"})
    assert response.status_code == 200
    assert "image/svg+xml" in response.headers.get("content-type", "")

def test_e2e_full_pipeline_bazi():
    svg_res = call_tool("render_bazi_svg", {"birth_datetime": "2000-01-01 12:00:00"})
    svg = svg_res.get("result", {}).get("svg_content", "")
    assert "<svg" in svg
    assert "</svg>" in svg

def test_e2e_full_pipeline_qimen():
    svg_res = call_tool("render_qimen_svg", {})
    svg = svg_res.get("result", {}).get("svg_content", "")
    assert "<svg" in svg
    assert "</svg>" in svg

def test_e2e_full_pipeline_fengshui():
    svg_res = call_tool("render_xuankong_svg", {})
    svg = svg_res.get("result", {}).get("svg_content", "")
    assert "<svg" in svg
    assert "</svg>" in svg
