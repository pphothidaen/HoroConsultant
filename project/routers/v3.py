"""FastAPI endpoints for Horo Architecture v3.0."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from project.core.bazi_engine import BaZiEngine
from project.core.liu_ren_engine import LiuRenEngine
from project.core.liu_yao_engine import LiuYaoEngine
from project.core.mian_xiang_engine import MianXiangEngine
from project.core.qi_men_engine import QiMenEngine
from project.core.qi_zheng_engine import QiZhengSiYuEngine
from project.core.tai_yi_engine import TaiYiEngine
from project.core.v3_engine_adapter import (
    adapt_bazi_to_claims,
    adapt_daliuren_to_claims,
    adapt_qimen_to_claims,
    adapt_liuyao_to_claims,
    adapt_mianxiang_to_claims,
    adapt_qizheng_to_claims,
    adapt_taiyi_to_claims,
    adapt_xuankong_to_claims,
    adapt_zeji_to_claims,
    adapt_ziwei_to_claims,
)
from project.core.xuan_kong_engine import XuanKongEngine
from project.core.ze_ji_engine import ZeJiEngine
from project.core.zi_wei_engine import ZiWeiEngine


def _find_v3_root() -> Path | None:
    """Find the TDD runtime tree across local and container working directories."""
    candidates = [
        Path(os.getenv("HORO_TDD_ROOT", "")) if os.getenv("HORO_TDD_ROOT") else None,
        Path(__file__).resolve().parents[2] / "TDD-HORO-v3.0",
        Path.cwd() / "TDD-HORO-v3.0",
        Path("/app/TDD-HORO-v3.0"),
        Path("/code/TDD-HORO-v3.0"),
    ]
    for candidate in candidates:
        if candidate and (candidate / "05_AGENT_PROMPTS_AND_RUNTIMES" / "runtimes").is_dir():
            return candidate
    return None


_V3_ROOT = _find_v3_root()
_RUNTIMES_DIR = (
    _V3_ROOT / "05_AGENT_PROMPTS_AND_RUNTIMES"
    if _V3_ROOT
    else Path("/__missing_horo_tdd_v3_runtime__")
)
_RUNTIME_IMPORT_ERROR: ImportError | None = None

if _RUNTIMES_DIR.is_dir() and str(_RUNTIMES_DIR) not in sys.path:
    sys.path.insert(0, str(_RUNTIMES_DIR))

try:
    from runtimes.audit_node import AuditNode  # type: ignore[no-redef]  # noqa: E402
    from runtimes.claim_validator import ClaimValidator  # type: ignore[no-redef]  # noqa: E402
    from runtimes.consensus_engine import ConsensusEngine  # type: ignore[no-redef]  # noqa: E402
    from runtimes.plan_composer import PlanComposer  # type: ignore[no-redef]  # noqa: E402
except (ImportError, ModuleNotFoundError) as exc:
    _RUNTIME_IMPORT_ERROR = exc
    AuditNode = None  # type: ignore[assignment,misc]
    ClaimValidator = None  # type: ignore[assignment,misc]
    ConsensusEngine = None  # type: ignore[assignment,misc]
    PlanComposer = None  # type: ignore[assignment,misc]


v3_router = APIRouter(tags=["Horo Architecture v3.0"])

_SCHEMA_PATH = (
    _V3_ROOT / "01_DATA_CONTRACTS" / "schemas" / "claim_emission_v3.0.json"
    if _V3_ROOT
    else Path("/__missing_horo_tdd_v3_schema__")
)
_ACTIVE_DOMAINS = ["BaZi", "ZiWei", "QiMen", "ZeJi", "XuanKong", "DaLiuRen", "LiuYao", "TaiYi", "QiZheng", "MianXiang"]


class V3CalculateRequest(BaseModel):
    birth_datetime: Any = Field(..., description="ISO 8601 datetime string or Unix timestamp")
    latitude: float
    longitude: float
    tz_offset: float = 7.0
    user_intent: str = "STRATEGIC_TIMING_ACTION"
    language: str = "th"


class V3AuditRequest(BaseModel):
    emissions: list[dict[str, Any]] = Field(default_factory=list)


def _require_v3_runtimes() -> None:
    """Convert missing deployment assets into an explicit API error, not import failure."""
    if _RUNTIME_IMPORT_ERROR is not None:
        raise HTTPException(status_code=503, detail="v3 runtime assets are unavailable") from _RUNTIME_IMPORT_ERROR


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


def _birth_stem(chart: dict[str, Any], pillar: str) -> str:
    return chart["pillars"][pillar]["stem"]["char"]


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
    xuankong = XuanKongEngine().calculate_chart(req.longitude, period=9)
    daliuren = LiuRenEngine().calculate_chart(
        _birth_stem(bazi, "day"),
        _birth_branch(bazi, "day"),
        ["正月", "二月", "三月", "四月", "五月", "六月", "七月", "八月", "九月", "十月", "十一月", "十二月"][dt.month - 1],
        _birth_branch(bazi, "hour"),
    )
    # v3 requests do not yet carry a cast hexagram or facial feature payload.
    # These canonical inputs keep the adapter pipeline deterministic until those
    # request fields are introduced.
    liuyao = LiuYaoEngine().calculate([6, 7, 8, 9, 7, 8], day_stem_idx=0, month_branch_idx=dt.month - 1)
    taiyi = TaiYiEngine().calculate(dt.year, dt.month, dt.day, dt.hour)
    qizheng = QiZhengSiYuEngine().calculate(
        dt.year, dt.month, dt.day, dt.hour, req.longitude, req.latitude
    )
    mianxiang = MianXiangEngine().calculate(
        {"face_shape": "oval", "forehead": "average", "nose": "average"},
        birth_year=dt.year,
    )
    emissions = [
        adapt_bazi_to_claims(bazi, session_id=session_id),
        adapt_ziwei_to_claims(ziwei, session_id=session_id),
        adapt_qimen_to_claims(qimen, session_id=session_id),
        adapt_zeji_to_claims(zeji, session_id=session_id),
        adapt_xuankong_to_claims(xuankong, session_id=session_id),
        adapt_daliuren_to_claims(daliuren, session_id=session_id),
        adapt_liuyao_to_claims(liuyao, session_id=session_id),
        adapt_taiyi_to_claims(taiyi, session_id=session_id),
        adapt_qizheng_to_claims(qizheng, session_id=session_id),
        adapt_mianxiang_to_claims(mianxiang, session_id=session_id),
    ]
    charts = {
        "bazi": bazi, "ziwei": ziwei, "qimen": qimen, "zeji": zeji,
        "xuankong": xuankong, "daliuren": daliuren, "liuyao": liuyao,
        "taiyi": taiyi, "qizheng": qizheng, "mianxiang": mianxiang,
    }
    return emissions, charts, session_id


@v3_router.post("/calculate")
def calculate_v3(req: V3CalculateRequest) -> dict[str, Any]:
    _require_v3_runtimes()
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
    if not _SCHEMA_PATH.is_file():
        raise HTTPException(status_code=500, detail="v3 claim schema is unavailable")
    try:
        return json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=500, detail="v3 claim schema is unavailable") from exc


@v3_router.post("/audit")
def audit_v3(req: V3AuditRequest) -> dict[str, Any]:
    _require_v3_runtimes()
    consensus = ConsensusEngine().arbitrate_claims(req.emissions)
    audit = AuditNode().evaluate_consensus_state(consensus)
    return {"verdict": audit["verdict"], "metrics": audit["metrics"], "findings": audit["findings"]}


__all__ = ["v3_router"]
