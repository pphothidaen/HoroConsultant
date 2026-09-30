"""
project/core/interpret_jobs.py
==============================
KAN-211: bounded in-memory job store for notebook-grounded interpret
calls (gemini-web-bridge api-spec §8 — a grounding chain can take
30-260s, so the HTTP request must not block; the caller polls).

Single-process by design at this stage: the gateway's concurrency-1
bridge is the real bottleneck, so a distributed store would add state
without adding throughput. Jobs are evicted oldest-first.
"""

from __future__ import annotations

import uuid
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

MAX_JOBS = 100


@dataclass
class InterpretJob:
    id: str
    status: str = "queued"          # queued | running | done | error
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


_JOBS: "OrderedDict[str, InterpretJob]" = OrderedDict()


def create_job() -> str:
    job_id = uuid.uuid4().hex
    _JOBS[job_id] = InterpretJob(id=job_id)
    while len(_JOBS) > MAX_JOBS:
        _JOBS.popitem(last=False)
    return job_id


def get_job(job_id: str) -> Optional[InterpretJob]:
    return _JOBS.get(job_id)


def _update(job_id: str, **fields) -> None:
    job = _JOBS.get(job_id)
    if job is None:
        return
    for k, v in fields.items():
        setattr(job, k, v)


async def run_grounded_job(job_id: str, req_dict: Dict[str, Any]) -> None:
    """Execute the grounded interpret pipeline for a queued job.

    Imported lazily so the job store stays import-light and the pipeline
    (routers.v2.run_grounded_pipeline) is the single source of truth.
    """
    from project.routers.v2 import run_grounded_pipeline

    _update(job_id, status="running")
    try:
        result = await run_grounded_pipeline(req_dict)
        _update(job_id, status="done", result=result)
    except Exception as exc:  # noqa: BLE001 — the error IS the payload
        _update(job_id, status="error", error=str(exc)[:500])
