"""
project/main.py — FastAPI Application Entry Point
Computational Metaphysics Engine
"""

from __future__ import annotations

import os
import json
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from typing   import Optional

from fastapi             import FastAPI, HTTPException, Query
from fastapi.responses   import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic            import BaseModel, Field
from project.admin_router import admin_router
from project.hitl_router  import hitl_router

from project.core.bazi_engine import BaZiEngine
from project.api_router        import HybridRouter

import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from project.rag.vector_store import get_vector_store
from scripts.sync_gdrive_vault import check_and_run_if_missed, sync_all
from project.validator import PredictionValidator

# ---------------------------------------------------------------------------
# App setup & Scheduler
# ---------------------------------------------------------------------------
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("main")

engine    = BaZiEngine()
router    = HybridRouter()
validator = PredictionValidator()
scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting Computational Metaphysics Engine API...")

    # 1. Startup Catch-Up Check (if system was powered off at midnight)
    if os.getenv("AUTO_SYNC_ON_STARTUP", "true").lower() in ("true", "1", "yes"):
        logger.info("🔍 Checking for missed Google Drive syncs on startup...")
        asyncio.create_task(asyncio.to_thread(check_and_run_if_missed))

    # 2. Midnight Cron Scheduler Setup
    if os.getenv("AUTO_SYNC_ENABLED", "true").lower() in ("true", "1", "yes"):
        cron_expr = os.getenv("AUTO_SYNC_CRON", "0 0 * * *")
        try:
            scheduler.add_job(
                func=lambda: asyncio.run(asyncio.to_thread(sync_all)),
                trigger=CronTrigger.from_crontab(cron_expr),
                id="midnight_gdrive_sync",
                name="Daily Midnight Google Drive Sync & Ingestion",
                replace_existing=True,
            )
            scheduler.start()
            logger.info(f"⏰ Midnight Auto-Sync Scheduler active: cron='{cron_expr}'")
        except Exception as e:
            logger.error(f"❌ Failed to start auto-sync scheduler: {e}")

    yield

    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("🛑 Auto-sync scheduler shut down.")


app = FastAPI(
    title       = "Computational Metaphysics Engine",
    description = "BaZi Four Pillars of Destiny API with True Solar Time, AI Interpretation & Gemini Validator",
    version     = "1.0.0",
    docs_url    = "/docs",
    redoc_url   = "/redoc",
    lifespan    = lifespan,
)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Register Admin Panel router
app.include_router(admin_router)

# Register HITL Review Studio router
app.include_router(hitl_router)


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------

class BaZiRequest(BaseModel):
    birth_datetime:    str   = Field(..., json_schema_extra={"example": "1990-05-15 14:30:00"},
                                     description="Local datetime YYYY-MM-DD HH:MM:SS")
    longitude:         float = Field(..., json_schema_extra={"example": 100.4930}, ge=-180.0, le=180.0)
    utc_offset_hours:  float = Field(..., json_schema_extra={"example": 7.0}, ge=-12.0, le=14.0)
    unknown_hour:      bool  = Field(False, description="Enable probabilistic matrix mode")


class InterpretRequest(BaZiRequest):
    query:             Optional[str] = Field(None, json_schema_extra={"example": "Analyse my Day Master strength and career prospects"})
    enable_validation: bool          = Field(False, description="Cross-validate prediction via Gemini Validator Agent")


class ValidateRequest(BaseModel):
    bazi_chart:             dict         = Field(..., description="Structured BaZi chart JSON from /calculate")
    initial_interpretation: str          = Field(..., description="Initial interpretation text to be validated")
    query:                  Optional[str]= Field(None, description="Optional user query context")


class LocationResolveRequest(BaseModel):
    location: str = Field(..., description="Location string (e.g. 'บางกะปิ, กรุงเทพ')")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", response_class=FileResponse, tags=["UI"])
async def serve_ui():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse(content={"status": "ok", "service": "Computational Metaphysics Engine"})


@app.get("/admin", response_class=FileResponse, tags=["Admin UI"])
async def serve_admin():
    """Serve the Knowledge Source Management Admin Panel."""
    admin_path = os.path.join(STATIC_DIR, "admin.html")
    if os.path.exists(admin_path):
        return FileResponse(admin_path)
    return JSONResponse(content={"status": "error", "message": "Admin panel not found"})


@app.get("/hitl-studio", response_class=FileResponse, tags=["Admin UI"])
async def serve_hitl():
    """Serve the HITL Review Studio UI."""
    hitl_path = os.path.join(STATIC_DIR, "hitl.html")
    if os.path.exists(hitl_path):
        return FileResponse(hitl_path)
    return JSONResponse(content={"status": "error", "message": "HITL studio not found"})


@app.get("/health", tags=["system"])
async def health():
    from project.core.fast_math import RUST_AVAILABLE, get_cache_stats
    adapter_exists = os.path.exists("project/models/qwen2.5-bazi-adapter/adapters.safetensors")
    vector_chunks = 0
    try:
        vs = get_vector_store()
        vector_chunks = vs.index.ntotal if vs and hasattr(vs, "index") and vs.index else 0
    except Exception:
        pass

    return {
        "status": "ok",
        "service": "Computational Metaphysics Engine",
        "version": "1.0.0",
        "rust_acceleration": RUST_AVAILABLE,
        "adapter_available": adapter_exists,
        "vector_store_chunks": vector_chunks,
        "cache_stats": get_cache_stats(),
    }


@app.post("/api/v1/bazi/calculate", tags=["BaZi"])
async def calculate_bazi(req: BaZiRequest):
    """
    Compute the Four Pillars of Destiny chart.
    Returns structured JSON with TST, pillars, hidden stems, and Five Elements scores.
    """
    try:
        dt     = datetime.strptime(req.birth_datetime, "%Y-%m-%d %H:%M:%S")
        result = engine.calculate(
            dt               = dt,
            longitude        = req.longitude,
            utc_offset_hours = req.utc_offset_hours,
            unknown_hour     = req.unknown_hour,
        )
        return JSONResponse(content=result)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception("BaZi calculation error")
        raise HTTPException(status_code=500, detail="Internal calculation error")


@app.post("/api/v1/bazi/interpret", tags=["BaZi", "AI"])
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


@app.post("/api/v1/bazi/validate", tags=["BaZi", "AI Validation"])
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


@app.get("/api/v1/eot", tags=["solar"])
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


@app.post("/api/v1/location/resolve", tags=["location"])
async def resolve_location(req: LocationResolveRequest):
    """
    Resolve a location string to longitude, latitude and UTC offset.
    """
    from geopy.geocoders import Nominatim
    from timezonefinder import TimezoneFinder
    from datetime import datetime
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
