import sys
from pathlib import Path

# Add project root directory to sys.path for Vercel Serverless Lambda environment
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from project.main import app
except Exception as e:
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    app = FastAPI()

    @app.api_route("/{path:path}", methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"])
    async def fallback_catchall(path: str):
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"Initialization failure: {str(e)}"},
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )
