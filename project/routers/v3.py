"""FastAPI endpoints for Horo Architecture v3.0."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from project.core.bazi_engine import BaZiEngine
from project.core.qi_men_engine import QiMenEngine
from project.core.v3_engine_adapter import (
    adapt_bazi_to_claims,
    adapt_qimen_to_claims,
    adapt_zeji_to_claims,
    adapt_ziwei_to_claims,
)
from project.core.ze_ji_engine import ZeJiEngine
from project.core.zi_wei_engine import ZiWeiEngine


_RUNTIMES_DIR = Path(__file__).resolve().parents[2] / "TDD-HORO-v3.0" / "05_AGENT_PROMPTS_AND_RUNTIMES"
if str(_RUNTIMES_DIR) not in sys.path:
    sys.path.insert(0, str(_RUNTIMES_DIR))

from runtimes.audit_node import AuditNode  # noqa: E402
from runtimes.consensus_engine import ConsensusEngine  # noqa: E402
from runtimes.plan_composer import PlanComposer  # noqa: E402


v3_router = APIRouter(tags=["Horo Architecture v3.0"])

_SCHEMA_PATH = _RUNTIMES_DIR.parents[0] / "01_DATA_CONTRACTS" / "schemas" / "claim_emission_v3.0.json"
_ACTIVE_DOMAINS = ["BaZi", "ZiWei", "QiMen", "ZeJi"]


class V3CalculateRequest(BaseModel):
    birth_datetime: Any = Field(..., description="ISO 8601 datetime string or Unix timestamp")
    latitude: float
    longitude: float
    tz_offset: float = 7.0
    user_intent: str = "STRATEGIC_TIMING_ACTION"
    language: str = "th"


class V3AuditRequest(BaseModel):
    emissions: list[dict[str, Any]] = Field(default_factory=list)


def _parse_birth_datetime(value: Any, tz_offset: float) -> datetime:
    """Parse ISO input or Unix timestamp into the local clock used by engines."""
    try:
        if isinstance(value, bool):
            raise ValueError
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(float(value), tz=timezone.utc).astimezone(
                timezone(timedelta(hours=tz_offset))
            ).replace(tzinfo=None)
        text = str(value).strip()
        try:
            return datetime.fromtimestamp(float(text), tz=timezone.utc).astimezone(
                timezone(timedelta(hours=tz_offset))
            ).replace(tzinfo=None)
        except ValueError:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
            if parsed.tzinfo is not None:
                parsed = parsed.astimezone(timezone(timedelta(hours=tz_offset))).replace(tzinfo=None)
            return parsed
    except (TypeError, ValueError, OverflowError) as exc:
        raise HTTPException(status_code=400, detail="Invalid birth_datetime; use ISO 8601 or Unix timestamp") from exc


def _birth_branch(chart: dict[str, Any], pillar: str) -> str:
    return chart["pillars"][pillar]["branch"]["char"]


def _calculate_emissions(req: V3CalculateRequest) -> tuple[list[dict[str, Any]], dict[str, Any], str]:
    dt = _parse_birth_datetime(req.birth_datetime, req.tz_offset)
    session_id = str(uuid4())

    bazi = BaZiEngine().calculate(dt, req.longitude, req.tz_offset)
    ziwei = ZiWeiEngine().calculate_chart(dt.year, dt.month, dt.day, dt.hour)
    qimen = QiMenEngine().calculate_chart(dt.year, dt.month, dt.day, dt.hour)
    zeji = ZeJiEngine().check_suitability(
        _birth_branch(bazi, "year"),
        _birth_branch(bazi, "month"),
        _birth_branch(bazi, "day"),
        _birth_branch(bazi, "year"),
    )
    emissions = [
        adapt_bazi_to_claims(bazi, session_id=session_id),
        adapt_ziwei_to_claims(ziwei, session_id=session_id),
        adapt_qimen_to_claims(qimen, session_id=session_id),
        adapt_zeji_to_claims(zeji, session_id=session_id),
    ]
    charts = {"bazi": bazi, "ziwei": ziwei, "qimen": qimen, "zeji": zeji}
    return emissions, charts, session_id


@v3_router.post("/calculate")
def calculate_v3(req: V3CalculateRequest) -> dict[str, Any]:
    emissions, charts, session_id = _calculate_emissions(req)
    consensus = ConsensusEngine(req.user_intent).arbitrate_claims(emissions)
    audit = AuditNode().evaluate_consensus_state(consensus)
    try:
        composed = PlanComposer().compose_final_report(consensus, audit, req.language)
    except PermissionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        **composed,
        "status": "COMPLETED",
        "audit_metrics": audit["metrics"],
        "audit_findings": audit["findings"],
        "has_epistemic_disclaimer": True,
        "emissions": emissions,
        "charts": charts,
    }


@v3_router.get("/health")
def v3_health() -> dict[str, Any]:
    return {"status": "HEALTHY", "version": "3.0.0", "active_domains": _ACTIVE_DOMAINS}


@v3_router.get("/schema")
def v3_schema() -> dict[str, Any]:
    try:
        return json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=500, detail="v3 claim schema is unavailable") from exc


@v3_router.post("/audit")
def audit_v3(req: V3AuditRequest) -> dict[str, Any]:
    consensus = ConsensusEngine().arbitrate_claims(req.emissions)
    audit = AuditNode().evaluate_consensus_state(consensus)
    return {"verdict": audit["verdict"], "metrics": audit["metrics"], "findings": audit["findings"]}


__all__ = ["v3_router"]
