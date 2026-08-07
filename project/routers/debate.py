"""
project/routers/debate.py — Multi-Agent Debate & Interpretation Endpoints
Computational Metaphysics Engine
"""

from __future__ import annotations

import json
import logging
import asyncio
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from project.core.bazi_engine import BaZiEngine
from project.api_router import HybridRouter
from project.validator import PredictionValidator

logger = logging.getLogger("routers.debate")

debate_router = APIRouter()

engine    = BaZiEngine()
router    = HybridRouter()
validator = PredictionValidator()


# ---------------------------------------------------------------------------
# Request / Response Schemas
# ---------------------------------------------------------------------------

class InterpretRequest(BaseModel):
    birth_datetime:    str   = Field(..., json_schema_extra={"example": "1990-05-15 14:30:00"},
                                     description="Local datetime YYYY-MM-DD HH:MM:SS")
    longitude:         float = Field(..., json_schema_extra={"example": 100.4930}, ge=-180.0, le=180.0)
    utc_offset_hours:  float = Field(..., json_schema_extra={"example": 7.0}, ge=-12.0, le=14.0)
    unknown_hour:      bool  = Field(False, description="Enable probabilistic matrix mode")
    query:             Optional[str] = Field(None, json_schema_extra={"example": "Analyse my Day Master strength and career prospects"})
    enable_validation: bool          = Field(False, description="Cross-validate prediction via Gemini Validator Agent")


class ValidateRequest(BaseModel):
    bazi_chart:             dict         = Field(..., description="Structured BaZi chart JSON from /calculate")
    initial_interpretation: str          = Field(..., description="Initial interpretation text to be validated")
    query:                  Optional[str]= Field(None, description="Optional user query context")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@debate_router.post("/api/v1/bazi/interpret", tags=["BaZi", "AI"])
async def interpret_bazi(req: InterpretRequest):
    """
    Calculate BaZi chart then pass to AI for natural-language interpretation.
    Optionally cross-validates via Gemini Prediction Validator if enable_validation=True.
    """
    try:
        dt     = datetime.strptime(req.birth_datetime, "%Y-%m-%d %H:%M:%S")
        chart  = engine.calculate(
            dt               = dt,
            longitude        = req.longitude,
            utc_offset_hours = req.utc_offset_hours,
            unknown_hour     = req.unknown_hour,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    dm   = chart["day_master"]
    fe   = chart.get("five_elements", {})
    pcts = fe.get("percentages", {})

    prompt = (
        f"BaZi Chart for birth: {req.birth_datetime} "
        f"(Longitude {req.longitude}°, UTC{req.utc_offset_hours:+.1f})\n\n"
        f"Day Master: {dm['stem']} ({dm['element']}, {dm['polarity']})\n"
        f"Five Elements: {json.dumps(pcts, ensure_ascii=False)}\n\n"
        f"User Query: {req.query or 'Provide a comprehensive life reading.'}"
    )

    ai_result = router.generate(
        prompt             = prompt,
        system_instruction = (
            "You are a master BaZi consultant. Provide a structured, insightful "
            "reading citing relevant classical principles. Be concise but thorough."
        ),
    )

    initial_text = ai_result.get("text") or ""
    validation_report = None

    if req.enable_validation and initial_text:
        logger.info("🛡️ Running Gemini Prediction Validator...")
        validation_report = await asyncio.to_thread(
            validator.validate,
            bazi_chart=chart,
            initial_interpretation=initial_text,
            user_query=req.query or "",
        )

    return JSONResponse(content={
        "chart":              chart,
        "interpretation":     initial_text,
        "model_used":         ai_result.get("model_used"),
        "route":              ai_result.get("route"),
        "latency_ms":         ai_result.get("latency_ms"),
        "validation_report":  validation_report,
    })


@debate_router.post("/api/v1/bazi/validate", tags=["BaZi", "AI Validation"])
async def validate_prediction(req: ValidateRequest):
    """
    Cross-validate an existing BaZi calculation and interpretation using Gemini Prediction Validator Agent.
    """
    report = await asyncio.to_thread(
        validator.validate,
        bazi_chart=req.bazi_chart,
        initial_interpretation=req.initial_interpretation,
        user_query=req.query or "",
    )
    return JSONResponse(content=report)
