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
