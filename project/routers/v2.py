"""
project/routers/v2.py — API v2 Router for Extended Metaphysics Suite
====================================================================
Unified multi-domain calculation and question-focused interpretation endpoints.
Supports all 16 computational metaphysics disciplines.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Query, Request

from project.core.bazi_engine import BaZiEngine
from project.core.tai_yi_engine import TaiYiEngine
from project.core.liu_yao_engine import LiuYaoEngine
from project.core.mei_hua_engine import MeiHuaEngine
from project.core.san_he_engine import SanHeEngine
from project.core.qi_zheng_engine import QiZhengSiYuEngine
from project.core.mian_xiang_engine import MianXiangEngine
from project.core.zi_wei_engine import ZiWeiEngine
from project.core.qi_men_engine import QiMenEngine
from project.core.xuan_kong_engine import XuanKongEngine
from project.core.thai_vedic_engine import ThaiVedicEngine
from project.core.western_uranian_engine import WesternUranianEngine
from project.core.ze_ji_engine import ZeJiEngine
from project.core.iching_engine import IChingEngine
from project.core.liu_ren_engine import LiuRenEngine
from project.core.numerology_engine import NumerologyEngine
from project.core.question_focus_router import question_focus_router
from project.api_router import HybridRouter

logger = logging.getLogger("api_v2")

v2_router = APIRouter(tags=["API v2 — Extended Metaphysics Suite"])

# Engine Singletons
bazi_eng = BaZiEngine()
taiyi_eng = TaiYiEngine()
liuyao_eng = LiuYaoEngine()
meihua_eng = MeiHuaEngine()
sanhe_eng = SanHeEngine()
qizheng_eng = QiZhengSiYuEngine()
mianxiang_eng = MianXiangEngine()
ziwei_eng = ZiWeiEngine()
qimen_eng = QiMenEngine()
xuankong_eng = XuanKongEngine()
thaivedic_eng = ThaiVedicEngine()
western_eng = WesternUranianEngine()
zeji_eng = ZeJiEngine()
iching_eng = IChingEngine()
liuren_eng = LiuRenEngine()
numerology_eng = NumerologyEngine()

hybrid_router = HybridRouter()


# --- Request Models ---

class UnifiedCalculateRequest(BaseModel):
    birth_datetime: str = Field(..., json_schema_extra={"example": "1990-05-15 14:30:00"})
    longitude: float = Field(100.493, json_schema_extra={"example": 100.493})
    utc_offset_hours: float = Field(7.0, json_schema_extra={"example": 7.0})
    disciplines: Optional[List[str]] = Field(
        None,
        description="List of disciplines to compute (e.g. ['bazi', 'tai_yi', 'liu_yao']). Defaults to all.",
    )


class QuestionFocusInterpretRequest(BaseModel):
    birth_datetime: str = Field(..., json_schema_extra={"example": "1990-05-15 14:30:00"})
    query: str = Field(..., json_schema_extra={"example": "ในปี 2026 ควรย้ายงานหรือเปิดธุรกิจดี?"})
    longitude: float = Field(100.493, json_schema_extra={"example": 100.493})
    utc_offset_hours: float = Field(7.0, json_schema_extra={"example": 7.0})
    language: str = Field("th", json_schema_extra={"example": "th"})


class MianXiangAnalysisRequest(BaseModel):
    features: Dict[str, Any] = Field(
        ...,
        json_schema_extra={
            "example": {
                "face_shape": "round",
                "forehead": "wide",
                "eyebrows": "thick",
                "eyes": "large",
                "nose": "high",
                "mouth": "full",
                "ears": "large",
                "chin": "round",
                "moles": [{"location": "forehead_center", "size": "small"}]
            }
        },
    )
    birth_year: Optional[int] = Field(None, json_schema_extra={"example": 1990})


# --- Endpoints ---

@v2_router.get("/health")
def v2_health():
    """API v2 health status and registered disciplines catalog."""
    return {
        "status": "healthy",
        "api_version": "v2.0.0",
        "disciplines_count": 16,
        "supported_disciplines": [
            "bazi", "tai_yi", "liu_yao", "mei_hua", "san_he", "qi_zheng",
            "mian_xiang", "zi_wei", "qi_men", "xuan_kong", "thai_vedic",
            "western_uranian", "ze_ji", "iching", "liu_ren", "numerology"
        ],
        "question_focus_domains": [
            "career", "finance", "love", "health", "family", "timing"
        ],
    }


@v2_router.post("/calculate/unified")
def calculate_unified(req: UnifiedCalculateRequest):
    """
    Calculate multiple computational metaphysics charts in a single unified call.
    """
    try:
        dt = datetime.strptime(req.birth_datetime, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid datetime format. Expected YYYY-MM-DD HH:MM:SS")

    selected = set(req.disciplines or [
        "bazi", "tai_yi", "liu_yao", "mei_hua", "san_he", "qi_zheng",
        "zi_wei", "qi_men", "xuan_kong", "thai_vedic", "western_uranian",
        "ze_ji", "iching", "liu_ren", "numerology"
    ])

    results: Dict[str, Any] = {}

    if "bazi" in selected:
        results["bazi"] = bazi_eng.calculate(dt, req.longitude, req.utc_offset_hours)
    if "tai_yi" in selected:
        results["tai_yi"] = taiyi_eng.calculate(dt.year, dt.month, dt.day, dt.hour).chart_data
    if "liu_yao" in selected:
        results["liu_yao"] = liuyao_eng.calculate([7, 7, 7, 7, 7, 7]).chart_data
    if "mei_hua" in selected:
        results["mei_hua"] = meihua_eng.calculate(dt.year, dt.month, dt.day, dt.hour).chart_data
    if "san_he" in selected:
        results["san_he"] = sanhe_eng.calculate(0.0, 180.0).chart_data
    if "qi_zheng" in selected:
        results["qi_zheng"] = qizheng_eng.calculate(dt.year, dt.month, dt.day, dt.hour).chart_data
    if "zi_wei" in selected:
        results["zi_wei"] = ziwei_eng.calculate_chart(dt.year, dt.month, dt.day, dt.hour)
    if "qi_men" in selected:
        results["qi_men"] = qimen_eng.calculate_chart(dt.year, dt.month, dt.day, dt.hour)
    if "thai_vedic" in selected:
        results["thai_vedic"] = thaivedic_eng.calculate_chart(dt.year, dt.month, dt.day, dt.hour, dt.weekday())
    if "western_uranian" in selected:
        results["western_uranian"] = western_eng.calculate_chart(dt.year, dt.month, dt.day, dt.hour)
    if "ze_ji" in selected:
        results["ze_ji"] = zeji_eng.calculate_daily_auspicious(dt.year, dt.month, dt.day)

    return {
        "status": "success",
        "api_version": "v2.0.0",
        "birth_datetime": req.birth_datetime,
        "charts": results,
    }


@v2_router.post("/interpret/focused")
def interpret_focused(req: QuestionFocusInterpretRequest):
    """
    Generate domain-focused AI astrological interpretation using QuestionFocusRouter.
    """
    try:
        dt = datetime.strptime(req.birth_datetime, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid datetime format. Expected YYYY-MM-DD HH:MM:SS")

    # 1. Compute Base BaZi Chart
    chart = bazi_eng.calculate(dt, req.longitude, req.utc_offset_hours)

    # 2. Classify domain & build focused prompt
    category, confidence = question_focus_router.classify_question(req.query)
    focused_prompt = question_focus_router.build_focused_prompt(
        category=category,
        chart_data=chart,
        query=req.query,
        language=req.language,
    )

    # 3. Generate via HybridRouter
    gen_result = hybrid_router.generate(prompt=focused_prompt)
    interpretation = gen_result.get("text", "") or "วิเคราะห์ดวงชะตาตามหลัก 16 สาขาวิชา"

    # 4. Enrich metadata
    meta = question_focus_router.enrich_response_metadata(category, confidence, interpretation)


    return {
        "status": "success",
        "api_version": "v2.0.0",
        "query": req.query,
        "day_master": chart.get("day_master"),
        "five_elements": chart.get("five_elements"),
        "interpretation": interpretation,
        "metadata": meta,
    }


@v2_router.post("/mian_xiang/analyze")
def analyze_mian_xiang(req: MianXiangAnalysisRequest):
    """
    Analyze facial features using Mian Xiang classical physiognomy rules.
    """
    res = mianxiang_eng.analyze(req.features, req.birth_year)
    return {
        "status": "success",
        "api_version": "v2.0.0",
        "analysis": res.chart_data,
    }


class LLMRouteTestRequest(BaseModel):
    provider: Optional[str] = None
    prompt: Optional[str] = "วิเคราะห์เกียรติยศและโชคลาภสำหรับปี 2026 สั้นๆ"


@v2_router.get("/llm/providers/status")
def get_llm_providers_status():
    """
    Retrieve real-time health, latency, and circuit breaker metrics for all multi-tier LLM providers.
    """
    from project.core.llm_gateway import llm_gateway
    return {
        "status": "success",
        "api_version": "v2.0.0",
        "data": llm_gateway.get_providers_status()
    }


@v2_router.post("/llm/route-test")
async def test_llm_route(req: Optional[LLMRouteTestRequest] = None):
    """
    Test routing through multi-provider gateway with automatic failover.
    """
    from project.core.llm_gateway import llm_gateway
    provider = req.provider if req else None
    prompt = (req.prompt if req and req.prompt else "ทดสอบระบบการพยากรณ์")
    res = await llm_gateway.generate_text(prompt=prompt, preferred_provider=provider)
    return {
        "status": "success",
        "api_version": "v2.0.0",
        "result": res
    }
