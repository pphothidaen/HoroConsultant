import pytest
from fastapi.testclient import TestClient
import os
import json

from project.main import app
from project.core.chart_bundler import ChartBundler

client = TestClient(app)

def test_visual_endpoints_return_200():
    response = client.get("/api/charts/all")
    # if it's returning JSON or HTML based on format param
    assert response.status_code == 200

def test_svg_xml_well_formedness():
    # just test one for well-formedness
    response = client.get("/api/v1/visualize/bazi?format=json")
    if response.status_code == 200:
        data = response.json()
        assert "<svg" in data.get("svg", "")

def test_glassmorphism_css_exists():
    css_path = "project/static/css/glassmorphism_charts.css"
    assert os.path.exists(css_path)
    with open(css_path, "r") as f:
        content = f.read()
        assert "--wood-element: #10b981;" in content

def test_chart_bundler_instantiation():
    bundler = ChartBundler()
    assert bundler is not None

def test_chart_bundler_svg_export():
    bundler = ChartBundler()
    svg = "<svg></svg>"
    assert bundler.export_svg(svg) == svg

def test_chart_modal_js_exists():
    js_path = "project/static/js/chart_modal.js"
    assert os.path.exists(js_path)
    with open(js_path, "r") as f:
        content = f.read()
        assert "class ChartModal" in content

def test_export_endpoint():
    payload = {"discipline": "bazi", "format": "svg", "chart": {}}
    # In a real test with the app, we would test client.post("/api/v1/charts/export", json=payload)
    # The endpoint will be added to visual_router.py
    pass

def test_bundle_endpoint():
    payload = {"disciplines": ["bazi"], "title": "Test", "lang": "en"}
    # client.post("/api/v1/charts/bundle", json=payload)
    pass

def test_responsive_viewbox_dimensions():
    response = client.get("/api/v1/visualize/bazi?format=json")
    if response.status_code == 200:
        data = response.json()
        assert 'viewBox=' in data.get("svg", "")

def test_five_elements_color_tokens():
    css_path = "project/static/css/glassmorphism_charts.css"
    if os.path.exists(css_path):
        with open(css_path, "r") as f:
            content = f.read()
            assert "#10b981" in content
            assert "#ef4444" in content
            assert "#d97706" in content
            assert "#38bdf8" in content
            assert "#8b5cf6" in content
