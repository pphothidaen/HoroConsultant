from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Health Check Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
@app.get("/api/health")
@app.get("/api/v1/health")
@app.get("/")
async def health():
    return {
        "status": "ok",
        "service": "Computational Metaphysics Engine",
        "version": "1.0.0"
    }

# Vercel handler alias
handler = app
