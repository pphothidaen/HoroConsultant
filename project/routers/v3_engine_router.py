"""Horo Architecture v3.0 Engine Router Integration.

Provides unified routing aggregator and backwards-compatible exports for
v3 computational metaphysics engines and the unified reading API router.
"""

from __future__ import annotations

from fastapi import APIRouter

from project.routers.unified_reading_router import (
    create_unified_reading,
    unified_reading_router,
)
from project.routers.v3 import (
    V3AuditRequest,
    V3CalculateRequest,
    audit_v3,
    calculate_v3,
    v3_health,
    v3_router,
    v3_schema,
)

v3_engine_router = APIRouter(tags=["Horo Architecture v3.0 Engine"])
v3_engine_router.include_router(v3_router)
v3_engine_router.include_router(unified_reading_router)

__all__ = [
    "V3AuditRequest",
    "V3CalculateRequest",
    "audit_v3",
    "calculate_v3",
    "create_unified_reading",
    "unified_reading_router",
    "v3_engine_router",
    "v3_health",
    "v3_router",
    "v3_schema",
]
