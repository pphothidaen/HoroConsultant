"""Literal FastAPI contract fixtures consumed by the Rust gateway tests."""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("HORO_ALLOW_PYTHON_FALLBACK", "1")
os.environ.setdefault("SKIP_FAISS_WARMUP", "true")

from fastapi.testclient import TestClient

import project.core.svg_generator as svg_generator
from project.main import app
from project.routers.astrology import BaZiRequest, calculate_bazi


GOLDEN_DIR = Path(__file__).parent / "goldens"


def test_python_openapi_matches_captured_literal_golden() -> None:
    """A method, path, or schema drift must invalidate the gateway baseline."""
    golden = json.loads((GOLDEN_DIR / "openapi.json").read_text(encoding="utf-8"))

    assert app.openapi() == golden
    assert len(golden["paths"]) == 42


def test_python_bazi_response_matches_captured_literal_golden(monkeypatch) -> None:
    """A public BaZi field or SVG drift must invalidate the native response fixture."""
    monkeypatch.setattr(svg_generator, "RUST_AVAILABLE", False)
    request = BaZiRequest(
        birth_datetime="1990-05-15 14:30:00",
        longitude=100.493,
        utc_offset_hours=7.0,
        unknown_hour=False,
    )

    response = asyncio.run(calculate_bazi(request))
    actual = json.loads(response.body)
    actual["calculation_timestamp"] = "<timestamp>"
    golden = json.loads((GOLDEN_DIR / "bazi_response.json").read_text(encoding="utf-8"))

    assert actual == golden


def test_internal_bazi_renderer_is_hidden_and_preserves_svg_bytes(monkeypatch) -> None:
    """Removing the localhost renderer must break native BaZi response compatibility."""
    golden = json.loads((GOLDEN_DIR / "bazi_response.json").read_text(encoding="utf-8"))
    chart = {
        key: value
        for key, value in golden.items()
        if key not in {"svg_content", "zodiac_svg"}
    }
    monkeypatch.setattr(svg_generator, "RUST_AVAILABLE", True)
    monkeypatch.setattr(
        svg_generator,
        "rust_core",
        SimpleNamespace(
            build_bazi_svg_rust=lambda *args: "lossy-native-bazi-svg",
            build_zodiac_svg_rust=lambda *args: "lossy-native-zodiac-svg",
        ),
    )
    client = TestClient(app, client=("127.0.0.1", 50000))

    response = client.post("/_internal/v1/bazi/render", json=chart)

    assert response.status_code == 200
    assert response.json() == {
        "svg_content": golden["svg_content"],
        "zodiac_svg": golden["zodiac_svg"],
    }
    assert "/_internal/v1/bazi/render" not in app.openapi()["paths"]


def test_internal_bazi_renderer_rejects_non_loopback_clients() -> None:
    """The compatibility renderer must remain inaccessible off loopback."""
    client = TestClient(app, client=("203.0.113.10", 50000))

    response = client.post("/_internal/v1/bazi/render", json={})

    assert response.status_code == 404


def test_explicit_worker_sync_controls_survive_dotenv_imports() -> None:
    """A checked-in .env must not reactivate external sync in the worker."""
    environment = os.environ.copy()
    environment.update(
        {
            "AUTO_SYNC_ON_STARTUP": "false",
            "AUTO_SYNC_ENABLED": "false",
            "HORO_ALLOW_PYTHON_FALLBACK": "1",
            "SKIP_FAISS_WARMUP": "true",
        }
    )
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import os; import project.main; "
                "print(os.environ['AUTO_SYNC_ON_STARTUP'] + '|' + "
                "os.environ['AUTO_SYNC_ENABLED'])"
            ),
        ],
        check=True,
        capture_output=True,
        env=environment,
        text=True,
    )

    assert completed.stdout.strip().splitlines()[-1] == "false|false"
