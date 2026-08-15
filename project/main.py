"""
project/main.py — FastAPI Application Entry Point
Computational Metaphysics Engine
"""

from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from project.admin_router import admin_router
from project.api_router import router
from project.hitl_router import hitl_router
from project.routers import astrology_router, debate_router, mlops_router


try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False

from project.rag.vector_store import get_vector_store
from scripts.sync_gdrive_vault import check_and_run_if_missed, sync_all

# ---------------------------------------------------------------------------
# Logging & Scheduler
# ---------------------------------------------------------------------------
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("main")
scheduler = AsyncIOScheduler() if APSCHEDULER_AVAILABLE else None


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting Computational Metaphysics Engine API...")

    # 1. Startup Catch-Up Check (if system was powered off at midnight)
    if os.getenv("AUTO_SYNC_ON_STARTUP", "false").lower() in ("true", "1", "yes"):
        logger.info("🔍 Checking for missed Google Drive syncs on startup...")
        asyncio.create_task(asyncio.to_thread(check_and_run_if_missed))

    # 2. Midnight Cron Scheduler Setup
    if APSCHEDULER_AVAILABLE and os.getenv("AUTO_SYNC_ENABLED", "false").lower() in ("true", "1", "yes"):
        cron_expr = os.getenv("AUTO_SYNC_CRON", "0 0 * * *")
        try:
            if scheduler:
                scheduler.add_job(
                    func=lambda: asyncio.run(asyncio.to_thread(sync_all)),
                    trigger=CronTrigger.from_crontab(cron_expr),
                    id="midnight_gdrive_sync",
                    name="Daily Midnight Google Drive Sync & Ingestion",
                    replace_existing=True,
                )
                scheduler.start()
        except Exception as e:
            logger.error(f"❌ Failed to start auto-sync scheduler: {e}")

    # 3. Vector DB & FAISS Index Warmup (eliminates cold-start latency)
    if os.getenv("SKIP_FAISS_WARMUP", "false").lower() != "true":
        try:
            logger.info("⚡ Pre-warming FAISS Vector Store & Rust Search Index...")
            asyncio.create_task(asyncio.to_thread(get_vector_store))
        except Exception as e:
            logger.warning(f"Vector store warmup note: {e}")
    else:
        logger.info("⏩ Skipping FAISS Vector Store pre-warm (SKIP_FAISS_WARMUP=true)")

    yield

    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("🛑 Auto-sync scheduler shut down.")


from fastapi.middleware.cors import CORSMiddleware

from project.core.config import get_app_version, get_git_commit_hash
from project.core.cors import get_allowed_origins
from project.core.observability import setup_observability_middleware

app = FastAPI(
    title       = "Computational Metaphysics Engine",
    description = "Modular 10-Domain Metaphysical Calculation, AI Debate & Multi-Agent Engine",
    version     = get_app_version(),
    docs_url    = "/docs",
    redoc_url   = "/redoc",
    lifespan    = lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    allow_credentials=True,
)

from fastapi import Request


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global unhandled exception on {request.url.path}: {exc}", exc_info=True)
    origin = request.headers.get("origin", "*")
    headers = {"Access-Control-Allow-Credentials": "true"}
    if origin:
        headers["Access-Control-Allow-Origin"] = origin
    headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {exc!s}"},
        headers=headers,
    )

setup_observability_middleware(app)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(STATIC_DIR):
    try:
        app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    except Exception as e:
        logger.warning(f"StaticFiles mount skipped: {e}")

from project.core.rate_limiter import rate_limiter
from project.routers.v2 import v2_router

# Rate Limiting Middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "127.0.0.1"
    path = request.url.path
    # Allow static assets and health checks without rate limit restriction
    if not path.startswith("/static") and path not in ("/", "/health", "/metrics", "/app.js", "/style.css"):
        allowed, reason = rate_limiter.check_rate_limit(client_ip, path)
        if not allowed:
            return JSONResponse(status_code=429, content={"detail": f"Rate limit exceeded: {reason}"})
    return await call_next(request)

# Register Modular Routers
app.include_router(admin_router)
app.include_router(hitl_router)
app.include_router(astrology_router)
app.include_router(debate_router)
app.include_router(mlops_router)
app.include_router(v2_router, prefix="/api/v2")



# ---------------------------------------------------------------------------
# UI & Core System Endpoints
# ---------------------------------------------------------------------------

@app.get("/", response_class=FileResponse, tags=["UI"])
async def serve_ui():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse(content={"status": "ok", "service": "Computational Metaphysics Engine"})


@app.get("/app.js", response_class=FileResponse, include_in_schema=False)
async def serve_app_js():
    return FileResponse(os.path.join(STATIC_DIR, "app.js"))


@app.get("/style.css", response_class=FileResponse, include_in_schema=False)
async def serve_style_css():
    return FileResponse(os.path.join(STATIC_DIR, "style.css"))


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


@app.post("/api/v1/telegram/webhook", tags=["Telegram Controller"])
async def telegram_webhook(payload: dict):
    """Handles incoming Telegram updates & admin commands (Decision 2)."""
    message = payload.get("message", {})
    text = message.get("text", "")
    chat = message.get("chat", {})
    chat_id = str(chat.get("id", ""))

    from project.mlops.notifications.telegram_controller import telegram_controller
    response_text = telegram_controller.handle_command(text, chat_id)

    # If Telegram bot token is configured, send reply directly
    if chat_id and telegram_controller.token:
        from project.mlops.notifications.webhook_notifier import WebhookNotifier
        notifier = WebhookNotifier()
        notifier.send_direct_message(response_text, chat_id=chat_id)

    return JSONResponse(content={"status": "processed", "response": response_text})


@app.get("/health", tags=["system"])
@app.get("/api/v1/health", tags=["system"])
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
        "version": get_app_version(),
        "git_commit": get_git_commit_hash(),
        "rust_acceleration": RUST_AVAILABLE,
        "adapter_available": adapter_exists,
        "vector_store_chunks": vector_chunks,
        "cache_stats": get_cache_stats(),
    }
