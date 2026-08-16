"""
project/routers/simulation.py
=============================
API Router for Life Path Multi-Scenario Simulation & What-If Analyzer.
"""

from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from project.core.simulation_engine import SimulationEngine

logger = logging.getLogger("simulation_api")
simulation_router = APIRouter(tags=["Life Path Simulation & What-If Analyzer"])


class SimulateRequest(BaseModel):
    birth_datetime: str = Field(..., description="User's birth datetime in ISO format YYYY-MM-DD HH:MM:SS")
    scenario_ids: Optional[List[str]] = Field(default_factory=lambda: ["corporate_stay", "tech_startup", "business_startup"], description="List of preset scenario IDs")
    custom_scenarios: Optional[List[Dict[str, Any]]] = Field(None, description="Custom user-defined scenarios")
    start_year: int = Field(2026, description="Starting transit year (default 2026)")
    horizon_years: int = Field(3, description="Evaluation horizon in years (1 - 5)")
    day_master: Optional[str] = Field(None, description="User's Day Master Stem")


@simulation_router.get("/api/v1/simulation/preset-scenarios")
def get_preset_scenarios() -> List[Dict[str, Any]]:
    """Return catalog of life decision simulation templates."""
    try:
        return SimulationEngine.get_presets()
    except Exception as e:
        logger.error(f"[SIMULATION] Error fetching presets: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@simulation_router.post("/api/v1/simulation/simulate-scenarios")
def simulate_scenarios(req: SimulateRequest) -> Dict[str, Any]:
    """Execute comparative multi-year life decision simulation across multiple paths."""
    try:
        return SimulationEngine.simulate_scenarios(
            birth_datetime=req.birth_datetime,
            scenario_ids=req.scenario_ids,
            custom_scenarios=req.custom_scenarios,
            start_year=req.start_year,
            horizon_years=req.horizon_years,
            day_master=req.day_master or "甲 (Jia Wood)"
        )
    except Exception as e:
        logger.error(f"[SIMULATION] Error running simulation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
