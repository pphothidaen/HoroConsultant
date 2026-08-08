"""
project/routers/astrology.py — Metaphysical Engine Calculation Endpoints
Computational Metaphysics Engine
"""

from __future__ import annotations

import logging
import asyncio
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from project.core.bazi_engine import BaZiEngine
from project.core.zi_wei_engine import ZiWeiEngine
from project.core.qi_men_engine import QiMenEngine
from project.core.liu_ren_engine import LiuRenEngine
from project.core.iching_engine import IChingEngine
from project.core.xuan_kong_engine import XuanKongEngine
from project.core.ze_ji_engine import ZeJiEngine
from project.core.thai_vedic_engine import ThaiVedicEngine
from project.core.western_uranian_engine import WesternUranianEngine
from project.core.numerology_engine import NumerologyEngine

from project.core.svg_generator import (
    generate_bazi_svg,
    generate_zodiac_wheel_svg,
    generate_ziwei_svg,
    generate_qimen_svg,
    generate_liuren_svg,
    generate_iching_svg,
    generate_xuankong_svg,
    generate_zeji_svg,
    generate_thaivedic_svg,
    generate_western_svg,
    generate_numerology_svg,
)

logger = logging.getLogger("routers.astrology")

astrology_router = APIRouter()

# Engine instances
bazi_engine       = BaZiEngine()
ziwei_engine      = ZiWeiEngine()
qimen_engine      = QiMenEngine()
liuren_engine     = LiuRenEngine()
iching_engine     = IChingEngine()
xuankong_engine   = XuanKongEngine()
zeji_engine       = ZeJiEngine()
thaivedic_engine  = ThaiVedicEngine()
western_engine    = WesternUranianEngine()
numerology_engine = NumerologyEngine()


# ---------------------------------------------------------------------------
# Request / Response Schemas
# ---------------------------------------------------------------------------

class BaZiRequest(BaseModel):
    birth_datetime:   str   = Field(..., json_schema_extra={"example": "1990-05-15 14:30:00"},
                                     description="Local datetime YYYY-MM-DD HH:MM:SS")
    longitude:        float = Field(..., json_schema_extra={"example": 100.4930}, ge=-180.0, le=180.0)
    utc_offset_hours: float = Field(..., json_schema_extra={"example": 7.0}, ge=-12.0, le=14.0)
    unknown_hour:     bool  = Field(False, description="Enable probabilistic matrix mode")


class LocationResolveRequest(BaseModel):
    location: str = Field(..., description="Location string (e.g. 'บางกะปิ, กรุงเทพ')")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@astrology_router.post("/api/v1/bazi/calculate", tags=["BaZi"])
async def calculate_bazi(req: BaZiRequest):
    """
    Compute the Four Pillars of Destiny chart.
    Returns structured JSON with TST, pillars, hidden stems, Five Elements scores, and SVG content.
    """
    try:
        dt     = datetime.strptime(req.birth_datetime, "%Y-%m-%d %H:%M:%S")
        result = bazi_engine.calculate(
            dt               = dt,
            longitude        = req.longitude,
            utc_offset_hours = req.utc_offset_hours,
            unknown_hour     = req.unknown_hour,
        )
        data = result.to_dict()
        data["svg_content"] = generate_bazi_svg(data)
        data["zodiac_svg"]  = generate_zodiac_wheel_svg(data)
        return JSONResponse(content=data)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception("BaZi calculation error")
        raise HTTPException(status_code=500, detail="Internal calculation error")


@astrology_router.get("/api/v1/ziwei/calculate", tags=["Zi Wei Dou Shu"])
async def calculate_ziwei(year: int = 1990, month: int = 5, day: int = 15, hour: int = 14, gender: str = "male"):
    """Calculate Zi Wei Dou Shu birth chart (12 Palaces, 14 Main Stars, Si Hua) with SVG vector."""
    chart = ziwei_engine.calculate_chart(year, month, day, hour, gender).to_dict()
    chart["svg_content"] = generate_ziwei_svg(chart)
    return JSONResponse(content=chart)


@astrology_router.get("/api/v1/qimen/calculate", tags=["Qi Men Dun Jia"])
async def calculate_qimen(year: int = 2026, month: int = 8, day: int = 7, hour: int = 14):
    """Calculate Qi Men Dun Jia 4-Plate chart (Yang/Yin Dun 18 Ju, 9 Stars, 8 Doors, 8 Spirits) with SVG."""
    chart = qimen_engine.calculate_chart(year, month, day, hour).to_dict()
    chart["svg_content"] = generate_qimen_svg(chart)
    return JSONResponse(content=chart)


@astrology_router.get("/api/v1/liuren/calculate", tags=["Da Liu Ren"])
async def calculate_liuren(day_stem: str = "甲", day_branch: str = "子", month_general: str = "正月", hour_branch: str = "午"):
    """Calculate Da Liu Ren chart (Earth/Heaven Plate, 4 Lessons, 3 Transmissions, 12 Generals) with SVG."""
    chart = liuren_engine.calculate_chart(day_stem, day_branch, month_general, hour_branch).to_dict()
    chart["svg_content"] = generate_liuren_svg(chart)
    return JSONResponse(content=chart)


@astrology_router.get("/api/v1/iching/calculate", tags=["I Ching"])
async def calculate_iching(day_stem: str = "甲", seed: Optional[int] = None):
    """Cast I Ching Hexagram and compute Liu Yao setup (6 Lines, 6 Animals, 5 Relatives) with SVG."""
    lines = iching_engine.cast_lines(seed=seed)
    chart = iching_engine.calculate_liu_yao(day_stem, lines).to_dict()
    chart["svg_content"] = generate_iching_svg(chart)
    return JSONResponse(content=chart)


@astrology_router.get("/api/v1/xuankong/calculate", tags=["Xuan Kong Flying Stars"])
async def calculate_xuankong(facing_degree: float = 180.0, period: int = 9):
    """Calculate Xuan Kong Flying Stars Period 9 9-Grid chart with SVG."""
    chart = xuankong_engine.calculate_chart(facing_degree, period).to_dict()
    chart["svg_content"] = generate_xuankong_svg(chart)
    return JSONResponse(content=chart)


@astrology_router.get("/api/v1/zeji/calculate", tags=["Date Selection"])
async def calculate_zeji(year_branch: str = "午", month_branch: str = "申", day_branch: str = "寅", user_birth_branch: Optional[str] = "子"):
    """Calculate Date Selection suitability via 12 Duty Officers and Clash checks with SVG."""
    chart = zeji_engine.check_suitability(year_branch, month_branch, day_branch, user_birth_branch).to_dict()
    chart["svg_content"] = generate_zeji_svg(chart)
    return JSONResponse(content=chart)


@astrology_router.get("/api/v1/thaivedic/calculate", tags=["Thai & Vedic Astrology"])
async def calculate_thaivedic(year: int = 1990, month: int = 5, day: int = 15, hour: int = 14, day_of_week: int = 2):
    """Calculate Thai Suriyayart 10 Lagna, Maha Thaksa, 27 Nakshatras & Vimshottari Dasha with SVG."""
    chart = thaivedic_engine.calculate_chart(year, month, day, hour, day_of_week).to_dict()
    chart["svg_content"] = generate_thaivedic_svg(chart)
    return JSONResponse(content=chart)


@astrology_router.get("/api/v1/western/calculate", tags=["Western & Uranian Astrology"])
async def calculate_western(year: int = 1990, month: int = 5, day: int = 15, hour: int = 14):
    """Calculate Western Tropical Planetary Aspects, Uranian 8 TNPs & Midpoint Formula with SVG."""
    chart = western_engine.calculate_chart(year, month, day, hour).to_dict()
    chart["svg_content"] = generate_western_svg(chart)
    return JSONResponse(content=chart)


@astrology_router.get("/api/v1/numerology/calculate", tags=["Numerology & Satta-Lek"])
async def calculate_numerology(text: str = "0812345678", day_num: int = 2, lunar_month: int = 6, year_zodiac_num: int = 7):
    """Calculate Satta-Lek 7-Base 4-Row Matrix & Chaldean Numerology Scoring with SVG."""
    satta_lek = numerology_engine.calculate_satta_lek(day_num, lunar_month, year_zodiac_num).to_dict()
    score     = numerology_engine.score_text_or_number(text).to_dict()
    chart     = {"satta_lek": satta_lek, "chaldean_score": score}
    chart["svg_content"] = generate_numerology_svg(chart)
    return JSONResponse(content=chart)


@astrology_router.get("/api/v1/eot", tags=["solar"])
async def equation_of_time(
    date: str = Query(..., examples=["2026-08-03"], description="Date YYYY-MM-DD")
):
    """Return Equation of Time in minutes for a given date."""
    from project.core.solar_time import calculate_equation_of_time
    try:
        dt  = datetime.strptime(date, "%Y-%m-%d")
        eot = calculate_equation_of_time(dt)
        return {"date": date, "eot_minutes": eot}
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid date format, use YYYY-MM-DD")


@astrology_router.post("/api/v1/location/resolve", tags=["location"])
async def resolve_location(req: LocationResolveRequest):
    """
    Resolve a location string to longitude, latitude and UTC offset.
    """
    from geopy.geocoders import Nominatim
    from timezonefinder import TimezoneFinder
    import zoneinfo

    geolocator = Nominatim(user_agent="horo_consultant")
    location_data = await asyncio.to_thread(geolocator.geocode, req.location)
    
    if not location_data:
        raise HTTPException(status_code=404, detail="Location not found")
        
    lat = location_data.latitude
    lon = location_data.longitude
    
    tf = TimezoneFinder()
    tz_name = tf.timezone_at(lng=lon, lat=lat)
    if not tz_name:
        raise HTTPException(status_code=404, detail="Timezone not found for location")
        
    tz = zoneinfo.ZoneInfo(tz_name)
    now = datetime.now(tz)
    utc_offset_hours = now.utcoffset().total_seconds() / 3600.0
    
    return {
        "location": location_data.address,
        "latitude": lat,
        "longitude": lon,
        "timezone": tz_name,
        "utc_offset_hours": utc_offset_hours
    }
