"""api/main.py — Lightweight Vercel Edge Stub"""

def handler(request=None, response=None):
    return {
        "status": "ok",
        "service": "Computational Metaphysics Engine",
        "version": "1.0.0",
        "gateway": "vercel-edge"
    }

app = handler
