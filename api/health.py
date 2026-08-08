import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from project.main import app
    handler = app
except Exception as e:
    err_msg = traceback.format_exc()
    from fastapi import FastAPI
    from fastapi.responses import PlainTextResponse
    app = FastAPI()

    @app.api_route("/{path:path}", methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"])
    async def debug_error(path: str):
        return PlainTextResponse(f"HEALTH IMPORT ERROR:\n{err_msg}", status_code=500)
    handler = app
