"""
project/tests/test_simulation_engine.py
=======================================
Unit and integration tests for Life Path Multi-Scenario Simulation & What-If Analyzer:
  1. Test simulation algorithm math, elemental boost, and ROI ranking.
  2. Test custom scenario evaluations over 3-year and 5-year horizons.
  3. Test API endpoints GET /api/v1/simulation/preset-scenarios & POST /api/v1/simulation/simulate-scenarios.
  4. Test HTML, CSS, JS, and i18n DOM integration in static and public folders.
"""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from project.core.simulation_engine import SimulationEngine, simulation_engine, PRESET_SCENARIOS, TRANSIT_YEARS
from project.main import app

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
client = TestClient(app)


class TestSimulationAlgorithms:
    """Test multi-scenario forecast mathematics and ranking."""

    def test_get_presets(self):
        presets = SimulationEngine.get_presets()
        assert len(presets) >= 4
        ids = [p["id"] for p in presets]
        assert "corporate_stay" in ids
        assert "tech_startup" in ids
        assert "business_startup" in ids
        assert "overseas_relocation" in ids

    def test_simulate_default_scenarios_3_years(self):
        res = SimulationEngine.simulate_scenarios(
            birth_datetime="1990-05-15 14:30:00",
            scenario_ids=["corporate_stay", "tech_startup", "business_startup"],
            start_year=2026,
            horizon_years=3
        )
        assert res["scenarios_count"] == 3
        assert len(res["years_evaluated"]) == 3
        assert res["years_evaluated"] == [2026, 2027, 2028]
        assert "optimal_scenario_id" in res
        assert "optimal_summary" in res
        assert len(res["results"]) == 3
        # Check first result has highest score
        assert res["results"][0]["composite_roi"] >= res["results"][1]["composite_roi"]

    def test_simulate_custom_scenarios_5_years(self):
        custom = [
            {
                "id": "custom_real_estate",
                "title": "ลงทุนในอสังหาริมทรัพย์และที่ดิน",
                "elements": ["Earth", "Metal"],
                "base_wealth": 85,
                "base_career": 70,
                "base_stability": 80,
                "base_innovation": 50,
                "risk_tier": "LOW"
            }
        ]
        res = SimulationEngine.simulate_scenarios(
            birth_datetime="1995-08-20 10:00:00",
            custom_scenarios=custom,
            start_year=2026,
            horizon_years=5
        )
        assert res["scenarios_count"] == 1
        assert len(res["years_evaluated"]) == 5
        assert res["results"][0]["scenario_id"] == "custom_real_estate"


class TestSimulationAPIEndpoints:
    """Test FastAPI simulation routes."""

    def test_get_preset_scenarios_endpoint(self):
        resp = client.get("/api/v1/simulation/preset-scenarios")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 4

    def test_simulate_scenarios_endpoint(self):
        payload = {
            "birth_datetime": "1990-05-15 14:30:00",
            "scenario_ids": ["corporate_stay", "tech_startup"],
            "start_year": 2026,
            "horizon_years": 3
        }
        resp = client.post("/api/v1/simulation/simulate-scenarios", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "optimal_scenario_id" in data
        assert len(data["results"]) == 2


class TestSimulationDOMIntegration:
    """Verify HTML, JS, CSS, and i18n bindings."""

    def test_index_html_has_simulation_elements(self):
        for subpath in ["project/static/index.html", "public/index.html"]:
            html = (PROJECT_ROOT / subpath).read_text(encoding="utf-8")
            assert 'id="scenario-simulation-card"' in html
            assert 'id="sim-horizon-badge"' in html
            assert 'id="btn-run-simulation"' in html
            assert 'id="simulation-results-box"' in html

    def test_app_js_has_simulation_functions(self):
        for subpath in ["project/static/app.js", "public/app.js"]:
            js = (PROJECT_ROOT / subpath).read_text(encoding="utf-8")
            assert "runScenarioSimulation" in js
            assert "renderSimulationComparison" in js
            assert "setSimulationHorizon" in js

    def test_i18n_has_simulation_keys(self):
        for subpath in ["project/static/i18n.js", "public/i18n.js"]:
            content = (PROJECT_ROOT / subpath).read_text(encoding="utf-8")
            assert "sim_title" in content
            assert "sim_desc" in content
            assert "btn_run_sim" in content
