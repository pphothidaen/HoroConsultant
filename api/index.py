import sys
import logging
from pathlib import Path

# Add project root directory to sys.path for Vercel Serverless Lambda environment
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api.index")

# Lazy loader for project.main app
_main_app = None

def get_main_app():
    global _main_app
    if _main_app is None:
        try:
            from project.main import app as imported_app
            _main_app = imported_app
            logger.info("✅ Successfully lazy-loaded project.main app")
        except Exception as e:
            logger.error(f"❌ Error lazy-loading project.main app: {e}", exc_info=True)
            _main_app = False
    return _main_app if _main_app is not False else None

app = FastAPI(title="Computational Metaphysics Engine Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"])
async def gateway_router(request: Request, path: str = ""):
    main_app = get_main_app()
    if main_app:
        return await main_app(request.scope, request.receive, request._send)
    
    # Fallback health response
    clean_path = path.strip("/")
    if request.method == "GET" and clean_path in ("", "health", "api/health", "api/v1/health"):
        return JSONResponse(
            content={"status": "ok", "service": "Computational Metaphysics Engine", "gateway": "Vercel"},
            headers={"Access-Control-Allow-Origin": "*"}
        )
    
    return JSONResponse(
        status_code=500,
        content={"error": "Backend initialization failed", "path": path},
        headers={"Access-Control-Allow-Origin": "*"}
    )

handler = app
