from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/{path:path}")
@app.get("/")
async def health(path: str = ""):
    return JSONResponse(
        status_code=200,
        content={
            "status": "ok",
            "service": "Computational Metaphysics Engine",
            "version": "1.0.0"
        },
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

handler = app
app = app
