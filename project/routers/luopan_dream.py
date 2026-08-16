"""
project/routers/luopan_dream.py
===============================
API Router for LuoPan 24-Mountain Compass, Period 9 Heatmap & Dream Decoder.
"""

from __future__ import annotations
import logging
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from project.core.luopan_dream_engine import LuoPanDreamEngine

logger = logging.getLogger("luopan_dream_api")
luopan_dream_router = APIRouter(tags=["LuoPan Compass & Dream Interpretation"])


class LuoPanRequest(BaseModel):
    facing_degree: float = Field(180.0, description="Facing compass degree (0 - 360)")
    period: int = Field(9, description="Feng Shui Period (default 9: 2024-2043)")


class DreamRequest(BaseModel):
    dream_text: str = Field(..., description="Description of the dream in Thai or English")
    user_day_master: Optional[str] = Field(None, description="User's BaZi Day Master Stem")


@luopan_dream_router.post("/api/v1/luopan/calculate")
def calculate_luopan(req: LuoPanRequest) -> Dict[str, Any]:
    """Calculate 24-Mountain compass orientation and Period 9 Flying Star 9-Palace sector heatmap."""
    try:
        return LuoPanDreamEngine.calculate_luopan_heatmap(
            facing_degree=req.facing_degree,
            period=req.period
        )
    except Exception as e:
        logger.error(f"[LUOPAN] Error calculating luopan: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@luopan_dream_router.post("/api/v1/dream/interpret")
def interpret_dream(req: DreamRequest) -> Dict[str, Any]:
    """Decode dream symbolism into I Ching 64 Hexagrams and Sattaleka lucky omen numbers."""
    try:
        return LuoPanDreamEngine.interpret_dream(
            dream_text=req.dream_text,
            user_day_master=req.user_day_master
        )
    except Exception as e:
        logger.error(f"[DREAM] Error interpreting dream: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
