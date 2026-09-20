"""
project/tests/test_debate_validation.py
========================================
Regression coverage for the validation-bypass bug in
``project/routers/debate.py`` (interpret_bazi endpoint).

Root cause
----------
The original code did::

    validation_report = None
    if not validation_report:        # <-- always True (None is falsy)
        validation_report = { ... hardcoded APPROVED report ... }

Because ``validation_report`` was initialised to ``None``, the guard
``if not validation_report`` was always ``True``, so the external
``PredictionValidator.validate`` was *never* called even when the caller
sent ``enable_validation=True``. The flag was effectively ignored.

Fix
---
Branch on ``req.enable_validation``:
    * True  -> call ``validator.validate(chart, initial_text, query)``
    * False -> use the deterministic local (hardcoded) APPROVED report
"""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from project.main import app

client = TestClient(app)

# ``validator`` is a module-level singleton in routers/debate.py; we patch its
# ``validate`` method to avoid real network calls to the Gemini API.
_VALIDATE_TARGET = "project.routers.debate.validator.validate"

_MOCK_AI = {
    "text": "บทวิเคราะห์ทดสอบ Day Master เป็น 庚ธาตุทอง",
    "model_used": "mock-model",
    "route": "mock_route",
    "latency_ms": 10,
}

_FALLBACK_REPORT_KEYS = {"validation_status", "confidence_score",
                         "peer_perspective", "refined_interpretation"}


def _base_payload(**overrides: object) -> dict:
    payload: dict = {
        "birth_datetime": "1990-05-15 14:30:00",
        "longitude": 100.493,
        "utc_offset_hours": 7.0,
        "unknown_hour": False,
        "query": "วิเคราะห์ความแข็งแรงของ Day Master และอาชีพการงาน",
    }
    payload.update(overrides)
    return payload


# ---------------------------------------------------------------------------
# enable_validation=True  ->  external validator MUST be invoked
# ---------------------------------------------------------------------------
def test_enable_validation_true_calls_validator():
    """enable_validation=True must invoke validator.validate and surface its
    return value verbatim as ``validation_report``."""
    fake_report = {
        "validation_status": "PASSED",
        "confidence_score": 0.91,
        "peer_perspective": "Gemini External Audit perspective",
        "element_logic_audit": "ok",
        "refined_interpretation": "refined interpretation",
    }
    with patch("project.main.router.generate", return_value=_MOCK_AI), \
         patch(_VALIDATE_TARGET, return_value=fake_report) as mock_validate:
        res = client.post(
            "/api/v1/bazi/interpret",
            json=_base_payload(enable_validation=True),
        )

    assert res.status_code == 200, res.text
    data = res.json()
    # The validator's return value is passed through untouched.
    assert data["validation_report"] == fake_report
    mock_validate.assert_called_once()


def test_enable_validation_true_passes_chart_and_query():
    """validator.validate must receive the *calculated* chart and the query."""
    with patch("project.main.router.generate", return_value=_MOCK_AI), \
         patch(_VALIDATE_TARGET,
              return_value={"validation_status": "PASSED"}) as m:
        res = client.post(
            "/api/v1/bazi/interpret",
            json=_base_payload(enable_validation=True, query="career"),
        )

    assert res.status_code == 200, res.text
    _, kwargs = m.call_args
    chart = kwargs["bazi_chart"]
    # Real engine output, not a stub.
    assert "day_master" in chart and "pillars" in chart
    assert chart["day_master"]["stem"] == "庚"
    assert kwargs["initial_interpretation"] == _MOCK_AI["text"]
    assert kwargs["user_query"] == "career"


def test_enable_validation_true_falls_back_when_validator_returns_none():
    """Even if the validator returns a falsy report, that value is respected
    (no silent re-substitution to the hardcoded fallback)."""
    with patch("project.main.router.generate", return_value=_MOCK_AI), \
         patch(_VALIDATE_TARGET, return_value=None) as m:
        res = client.post(
            "/api/v1/bazi/interpret",
            json=_base_payload(enable_validation=True),
        )
    assert res.status_code == 200, res.text
    # A None report is passed through (the API surface still contains the key).
    assert res.json()["validation_report"] is None
    m.assert_called_once()


# ---------------------------------------------------------------------------
# enable_validation=False  ->  validator MUST NOT be called (deterministic)
# ---------------------------------------------------------------------------
def test_enable_validation_false_uses_fallback():
    """enable_validation=False must use the hardcoded APPROVED report and must
    NOT call validator.validate (no network)."""
    with patch("project.main.router.generate", return_value=_MOCK_AI), \
         patch(_VALIDATE_TARGET) as mock_validate:
        res = client.post(
            "/api/v1/bazi/interpret",
            json=_base_payload(enable_validation=False),
        )

    assert res.status_code == 200, res.text
    data = res.json()
    report = data["validation_report"]
    assert set(report.keys()) == _FALLBACK_REPORT_KEYS
    assert report["validation_status"] == "APPROVED"
    assert report["confidence_score"] == 0.96
    mock_validate.assert_not_called()


def test_enable_validation_default_is_false():
    """Omitting enable_validation defaults to False (fallback path)."""
    payload = _base_payload()
    payload.pop("enable_validation", None)
    with patch("project.main.router.generate", return_value=_MOCK_AI), \
         patch(_VALIDATE_TARGET) as mock_validate:
        res = client.post("/api/v1/bazi/interpret", json=payload)

    assert res.status_code == 200, res.text
    assert res.json()["validation_report"]["validation_status"] == "APPROVED"
    mock_validate.assert_not_called()


# ---------------------------------------------------------------------------
# Bug regression guard: the old always-True branch is gone.
# ---------------------------------------------------------------------------
def test_validator_is_actually_called_when_enabled():
    """Direct guard against the original bug: a call counter proves validate()
    is reached on the enable_validation=True path."""
    calls = []

    def _spy(*args, **kwargs):
        calls.append(kwargs)
        return {"validation_status": "PASSED"}

    with patch("project.main.router.generate", return_value=_MOCK_AI), \
         patch(_VALIDATE_TARGET, side_effect=_spy):
        client.post(
            "/api/v1/bazi/interpret",
            json=_base_payload(enable_validation=True),
        )

    assert len(calls) == 1
    assert "bazi_chart" in calls[0]
    assert "initial_interpretation" in calls[0]
    assert "user_query" in calls[0]
