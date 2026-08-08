import sys
import traceback
import logging
from pathlib import Path

# Add project root directory to sys.path for Vercel Serverless Lambda environment
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from project.main import app

@app.middleware("http")
async def catch_exceptions_middleware(request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        err_msg = traceback.format_exc()
        logging.error(f"Unhandled Request Error: {err_msg}")
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(f"REQUEST EXECUTION ERROR:\n{err_msg}", status_code=500)

# Export ASGI handler for Vercel Serverless Function
handler = app
app = app
