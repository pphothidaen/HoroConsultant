"""
project/routers — Decoupled Modular FastAPI APIRouter Blueprints
Computational Metaphysics Engine
"""

from project.routers.astrology import astrology_router
from project.routers.debate import debate_router

__all__ = ["astrology_router", "debate_router"]
