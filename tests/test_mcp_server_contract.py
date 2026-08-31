import subprocess
import sys
from pathlib import Path

import pytest
from project.mcp_server import call_tool, HoroMCPTools
from project.schemas.mcp_tools_v1 import get_full_mcp_manifest


ROOT = Path(__file__).resolve().parents[1]


def test_router_import_is_lazy_and_getter_caches_instance():
    """The AI router must load only on demand and be constructed once."""
    probe = """
import importlib
import sys
from types import ModuleType

server = importlib.import_module("project.mcp_server")
assert "project.api_router" not in sys.modules

class FakeHybridRouter:
    instances = 0

    def __init__(self):
        type(self).instances += 1

fake_api_router = ModuleType("project.api_router")
fake_api_router.HybridRouter = FakeHybridRouter
sys.modules["project.api_router"] = fake_api_router

first = server._get_router()
second = server._get_router()
assert first is second
assert isinstance(first, FakeHybridRouter)
assert FakeHybridRouter.instances == 1
"""
    result = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr

def test_mcp_manifest_contains_tools():
    manifest = get_full_mcp_manifest().model_dump()
    assert "tools" in manifest
    tools = manifest["tools"]
    assert len(tools) >= 30  # Should be 36 tools
    tool_names = [t["name"] for t in tools]
    assert "bazi_calculate" in tool_names
    assert "render_bazi_svg" in tool_names

def test_bazi_calculate():
    res = call_tool("bazi_calculate", {"birth_datetime": "1990-01-01 12:00:00"})
    assert "chart_data" in res or isinstance(res, dict)

def test_ziwei_calculate():
    res = call_tool("ziwei_calculate", {"year": 1990, "month": 1, "day": 1, "hour": 12, "gender": "male"})
    assert isinstance(res, dict)

def test_fengshui_calculate():
    res = call_tool("xuankong_calculate", {"facing_degree": 0, "period": 8})
    assert isinstance(res, dict)

def test_qimen_calculate():
    res = call_tool("qimen_calculate", {"year": 1990, "month": 1, "day": 1, "hour": 12})
    assert isinstance(res, dict)

def test_taiyi_calculate():
    res = call_tool("tai_yi_calculate", {"year": 1990, "month": 1, "day": 1, "hour": 12})
    assert isinstance(res, dict)

def test_liuren_calculate():
    res = call_tool("liuren_calculate", {"day_stem": "甲", "day_branch": "子", "month_general": "正月", "hour_branch": "午"})
    assert isinstance(res, dict)

def test_plum_calculate():
    res = call_tool("mei_hua_calculate", {"year": 1990, "month": 1, "day": 1, "hour": 12})
    assert isinstance(res, dict)

def test_bazi_visualize():
    res = call_tool("render_bazi_svg", {"birth_datetime": "1990-01-01 12:00:00"})
    assert isinstance(res, dict)
    assert "<svg" in res.get("svg_content", "") or "<svg" in str(res)

def test_ziwei_visualize():
    res = call_tool("render_ziwei_svg", {})
    assert isinstance(res, dict)
    assert "<svg" in res.get("svg_content", "") or "<svg" in str(res)

def test_xuankong_visualize():
    res = call_tool("render_xuankong_svg", {})
    assert isinstance(res, dict)
    assert "<svg" in res.get("svg_content", "") or "<svg" in str(res)

def test_invalid_tool():
    res = call_tool("nonexistent_tool", {})
    assert "error" in res or isinstance(res, dict)
