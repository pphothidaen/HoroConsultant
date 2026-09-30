"""
project/tests/test_interpret_jobs.py
====================================
KAN-211 (M4): async job pattern for notebook-grounded interpret calls
(gemini-web-bridge api-spec §8 — 30-260s latency must not block HTTP).

  - POST /api/v2/interpret/grounded → 202 {job_id, status_url}
  - GET  /api/v2/interpret/grounded/jobs/{job_id} → queued/running/done/error
  - invalid payload answers 400 synchronously before any 202
  - unknown job → 404
  - in-memory store is bounded (oldest evicted)
"""

import pytest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from project.core.interpret_jobs import MAX_JOBS, InterpretJob, create_job, get_job
from project.main import app

client = TestClient(app)

BASE_REQ = {
    "birth_datetime": "1990-05-14 08:30:00",
    "longitude": 100.5018,
    "utc_offset_hours": 7.0,
    "query": "อาชีพที่เหมาะกับดวงนี้คืออะไร",
    "language": "th",
}


def test_create_and_get_job_lifecycle():
    job_id = create_job()
    job = get_job(job_id)
    assert isinstance(job, InterpretJob)
    assert job.status == "queued"
    assert job.result is None and job.error is None


def test_store_is_bounded():
    ids = [create_job() for _ in range(MAX_JOBS + 5)]
    assert get_job(ids[0]) is None, "oldest job must be evicted"
    assert get_job(ids[-1]) is not None


@pytest.mark.anyio
async def test_runner_marks_done_with_pipeline_result(monkeypatch):
    from project.core.interpret_jobs import run_grounded_job
    job_id = create_job()
    monkeypatch.setattr(
        "project.routers.v2.run_grounded_pipeline",
        AsyncMock(return_value={"interpretation": "คำตอบ", "metadata": {"routing": "aipass_bridge"}}),
    )
    await run_grounded_job(job_id, dict(BASE_REQ))
    job = get_job(job_id)
    assert job.status == "done"
    assert job.result["interpretation"] == "คำตอบ"
    assert job.error is None


@pytest.mark.anyio
async def test_runner_marks_error_on_pipeline_failure(monkeypatch):
    from project.core.interpret_jobs import run_grounded_job
    job_id = create_job()
    monkeypatch.setattr(
        "project.routers.v2.run_grounded_pipeline",
        AsyncMock(side_effect=RuntimeError("aipass_bridge JSON-RPC error -32000")),
    )
    await run_grounded_job(job_id, dict(BASE_REQ))
    job = get_job(job_id)
    assert job.status == "error"
    assert "JSON-RPC error" in job.error


def test_post_returns_202_with_status_url():
    with patch("project.routers.v2.run_grounded_pipeline", new=AsyncMock(
            return_value={"interpretation": "x", "metadata": {}})):
        res = client.post("/api/v2/interpret/grounded", json=BASE_REQ)
    assert res.status_code == 202
    data = res.json()
    assert data["status"] == "accepted"
    assert data["status_url"].startswith("/api/v2/interpret/grounded/jobs/")
    poll = client.get(data["status_url"])
    assert poll.status_code == 200
    assert poll.json()["status"] in {"queued", "running", "done"}


def test_invalid_datetime_answers_400_before_202():
    res = client.post("/api/v2/interpret/grounded", json=dict(BASE_REQ, birth_datetime="not-a-date"))
    assert res.status_code == 400


def test_unknown_job_is_404():
    assert client.get("/api/v2/interpret/grounded/jobs/nope").status_code == 404
