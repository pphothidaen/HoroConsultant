"""
project/routers/synastry.py
===========================
API Router for Dual-Profile Multi-Domain Synastry & Partner Compatibility.
"""

from __future__ import annotations
import logging
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from project.core.bazi_engine import BaZiEngine
from project.core.synastry_engine import SynastryEngine

logger = logging.getLogger("synastry_api")
synastry_router = APIRouter(prefix="/api/v1/synastry", tags=["Synastry & Partner Compatibility"])

bazi_eng = BaZiEngine()


class ProfileInput(BaseModel):
    name: Optional[str] = Field("Person", description="Profile name")
    birth_datetime: str = Field(..., description="YYYY-MM-DD HH:MM:SS format")
    longitude: float = Field(100.493, description="Longitude for TST correction")
    utc_offset_hours: float = Field(7.0, description="UTC timezone offset in hours")
    gender: Optional[str] = Field("male", description="Gender: male | female")


class SynastryRequest(BaseModel):
    person_a: ProfileInput = Field(..., description="Person A Profile")
    person_b: ProfileInput = Field(..., description="Person B Profile")
    relation_type: Optional[str] = Field("romantic", description="romantic | business | friendship")
    language: Optional[str] = Field("th", description="Response language: th | en | zh")


@synastry_router.post("/analyze")
def analyze_synastry(req: SynastryRequest) -> Dict[str, Any]:
    """Calculate BaZi synastry, elemental affinity, and multi-tier compatibility between two profiles."""
    try:
        def parse_dt(dt_str: str) -> datetime:
            cleaned = dt_str.replace("T", " ").strip()
            if len(cleaned) == 10:
                cleaned += " 12:00:00"
            elif len(cleaned) == 16:
                cleaned += ":00"
            return datetime.strptime(cleaned, "%Y-%m-%d %H:%M:%S")

        dt_a = parse_dt(req.person_a.birth_datetime)
        dt_b = parse_dt(req.person_b.birth_datetime)

        chart_a = bazi_eng.calculate(
            dt=dt_a,
            longitude=req.person_a.longitude,
            utc_offset_hours=req.person_a.utc_offset_hours,
            gender=req.person_a.gender or "male"
        )
        chart_b = bazi_eng.calculate(
            dt=dt_b,
            longitude=req.person_b.longitude,
            utc_offset_hours=req.person_b.utc_offset_hours,
            gender=req.person_b.gender or "female"
        )

        dict_a = chart_a.model_dump() if hasattr(chart_a, "model_dump") else (chart_a.dict() if hasattr(chart_a, "dict") else dict(chart_a))
        dict_b = chart_b.model_dump() if hasattr(chart_b, "model_dump") else (chart_b.dict() if hasattr(chart_b, "dict") else dict(chart_b))

        result = SynastryEngine.calculate_synastry(dict_a, dict_b)
        result["person_a"]["name"] = req.person_a.name or "Person A"
        result["person_b"]["name"] = req.person_b.name or "Person B"
        result["relation_type"] = req.relation_type
        result["language"] = req.language
        return result
    except Exception as e:
        logger.error(f"[SYNASTRY] Error analyzing synastry: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Synastry calculation failed: {str(e)}")
