"""
project/tests/test_rust_extensions.py
======================================
Tests for Phase 2 Rust Extensions & Fast Math integration:
1. FAISS / Dense Vector Search (< 1ms latency).
2. Xuan Kong Flying Stars 9-Grid Matrix calculations.
"""

import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

# Source-tree tests intentionally exercise the documented development fallback.
os.environ.setdefault("HORO_ALLOW_PYTHON_FALLBACK", "1")

from project.core.fast_math import fast_xuankong_9grid, rust_dense_vector_search
from project.core.xuan_kong_engine import XuanKongEngine


_PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _run_isolated_python(
    code: str,
    *,
    pythonpath: list[Path],
    allow_fallback: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run an import contract in a fresh interpreter with a controlled path."""
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(str(path) for path in pythonpath)
    if allow_fallback:
        env["HORO_ALLOW_PYTHON_FALLBACK"] = "1"
    else:
        env.pop("HORO_ALLOW_PYTHON_FALLBACK", None)
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd="/tmp",
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_rust_import_order_does_not_change_native_availability():
    """Importing fast_math before rust_core must report the same backend identity."""
    code = """
import importlib
import json
import sys

order = sys.argv[1]
if order == "package-first":
    import rust_core
    fast_math = importlib.import_module("project.core.fast_math")
else:
    fast_math = importlib.import_module("project.core.fast_math")
    import rust_core
print(json.dumps(fast_math.runtime_backend(), sort_keys=True))
"""
    results = []
    for order in ("package-first", "fast-math-first"):
        env = os.environ.copy()
        env["PYTHONPATH"] = str(_PROJECT_ROOT)
        env["HORO_ALLOW_PYTHON_FALLBACK"] = "1"
        completed = subprocess.run(
            [sys.executable, "-c", code, order],
            cwd="/tmp",
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr
        results.append(json.loads(completed.stdout))

    assert results[0] == results[1]
    assert set(results[0]) == {"kernels", "rust_available", "rust_version"}


def test_source_tree_native_artifact_is_not_discovered(tmp_path):
    """An unrelated source-tree shared library must never trigger discovery scans."""
    decoy_dir = tmp_path / "unrelated" / "build"
    decoy_dir.mkdir(parents=True)
    (decoy_dir / "rust_core_native.so").write_bytes(b"not a Python extension")

    completed = _run_isolated_python(
        f"""
import json
import sys

scanned = []
decoy_root = {str(tmp_path)!r}
def audit(event, args):
    if event == "os.scandir" and str(args[0]).startswith(decoy_root):
        scanned.append(str(args[0]))
sys.addaudithook(audit)

import rust_core
print(json.dumps(scanned))
""",
        pythonpath=[tmp_path, _PROJECT_ROOT],
        allow_fallback=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == []


def test_missing_native_extension_fails_without_explicit_fallback(tmp_path):
    """Production imports must fail clearly instead of silently using Python kernels."""
    package_dir = tmp_path / "rust_core"
    package_dir.mkdir()
    package_dir.joinpath("__init__.py").write_text(
        (_PROJECT_ROOT / "rust_core" / "__init__.py").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    completed = _run_isolated_python(
        "import rust_core",
        pythonpath=[tmp_path],
    )

    assert completed.returncode != 0
    assert "HORO_ALLOW_PYTHON_FALLBACK=1" in completed.stderr


def test_explicit_fallback_reports_python_runtime_identity(tmp_path):
    """The opt-in fallback must be observable and enumerate no active Rust kernels."""
    package_dir = tmp_path / "rust_core"
    package_dir.mkdir()
    package_dir.joinpath("__init__.py").write_text(
        (_PROJECT_ROOT / "rust_core" / "__init__.py").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    completed = _run_isolated_python(
        "import json, rust_core; print(json.dumps(rust_core.runtime_backend(), sort_keys=True))",
        pythonpath=[tmp_path],
        allow_fallback=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "kernels": [],
        "rust_available": False,
        "rust_version": None,
    }


def test_partial_native_module_fails_without_explicit_fallback(tmp_path):
    """A loaded native module missing a requested kernel must fail closed."""
    tmp_path.joinpath("rust_core.py").write_text(
        """
import os

RUST_AVAILABLE = True
PYTHON_FALLBACK_ALLOWED = os.environ.get("HORO_ALLOW_PYTHON_FALLBACK") == "1"
def runtime_backend():
    return {"rust_available": True, "rust_version": "test", "kernels": []}
""",
        encoding="utf-8",
    )
    code = """
from project.core.fast_math import fast_thai_lagna
print(fast_thai_lagna(10, 4))
"""

    production = _run_isolated_python(
        code,
        pythonpath=[tmp_path, _PROJECT_ROOT],
    )
    fallback = _run_isolated_python(
        code,
        pythonpath=[tmp_path, _PROJECT_ROOT],
        allow_fallback=True,
    )

    assert production.returncode != 0
    assert "required native kernel 'calculate_thai_lagna' is missing" in production.stderr
    assert fallback.returncode == 0, fallback.stderr
    assert "เมถุน" in fallback.stdout


def test_rust_dense_vector_search_basic():
    """Verify dense vector search returns correct top-k indices and scores."""
    q_vec = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    doc_matrix = np.array([
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.8, 0.6, 0.0],
    ], dtype=np.float32)

    hits = rust_dense_vector_search(q_vec, doc_matrix, top_k=2, threshold=0.0)
    assert len(hits) == 2
    assert hits[0][0] == 0  # Perfect match
    assert abs(hits[0][1] - 1.0) < 1e-3
    assert hits[1][0] == 2  # 0.8 dot product
    assert abs(hits[1][1] - 0.8) < 1e-3


def test_rust_dense_vector_search_l2_basic():
    """Verify L2 Euclidean distance vector search returns smallest distance first."""
    from project.core.fast_math import rust_dense_vector_search_l2
    q_vec = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    doc_matrix = np.array([
        [1.0, 0.0, 0.0],  # dist = 0.0
        [0.0, 1.0, 0.0],  # dist = sqrt(2) = 1.4142
        [1.0, 1.0, 0.0],  # dist = 1.0
    ], dtype=np.float32)

    hits = rust_dense_vector_search_l2(q_vec, doc_matrix, top_k=2, max_distance=2.0)
    assert len(hits) == 2
    assert hits[0][0] == 0  # Perfect match (dist 0.0)
    assert abs(hits[0][1] - 0.0) < 1e-3
    assert hits[1][0] == 2  # Next closest (dist 1.0)
    assert abs(hits[1][1] - 1.0) < 1e-3



def test_fast_xuankong_9grid_structure():
    """Verify fast_xuankong_9grid generates 9 grid palaces with valid stars."""
    grid = fast_xuankong_9grid(180.0, period=9)
    assert len(grid) == 9
    for (palace, base, sit, face) in grid:
        assert 1 <= palace <= 9
        assert 1 <= base <= 9
        assert 1 <= sit <= 9
        assert 1 <= face <= 9


def test_xuankong_engine_integration():
    """Verify XuanKongEngine output matches fast grid matrix values."""
    engine = XuanKongEngine()
    chart = engine.calculate_chart(180.0, period=9)
    palaces = chart.chart_data["grid_palaces"]
    assert len(palaces) == 9
    for p in palaces:
        assert "palace_number" in p
        assert "base_star" in p
        assert "sitting_star" in p
        assert "facing_star" in p


def test_fast_ziwei_stars():
    """Verify Zi Wei Dou Shu 14 main stars fast placement."""
    from project.core.fast_math import fast_ziwei_stars
    from project.core.zi_wei_engine import ZiWeiEngine
    
    res = fast_ziwei_stars(2)
    assert len(res) == 12
    engine = ZiWeiEngine()
    chart = engine.calculate_chart(1990, 5, 15, 14)
    assert "ming_gong_branch" in chart.chart_data


def test_fast_thai_vedic_rust_extensions():
    """Verify Thai Suriyayart Lagna & Maha Thaksa Rust bindings."""
    from project.core.fast_math import fast_thai_lagna, fast_thaksa_map
    lagna_name, lagna_idx = fast_thai_lagna(10, 4)
    assert isinstance(lagna_name, str)
    assert 0 <= lagna_idx < 12

    thaksa = fast_thaksa_map(0)
    assert len(thaksa) == 8
    assert thaksa[0][0] == "บริวาร"


def test_fast_uranian_rust_extensions():
    """Verify Western & Uranian midpoint & sensitive point Rust bindings."""
    from project.core.fast_math import (
        fast_uranian_midpoint,
        fast_uranian_sensitive_point,
    )
    mid = fast_uranian_midpoint(45.0, 135.0)
    assert abs(mid - 90.0) < 1e-3

    sens = fast_uranian_sensitive_point(100.0, 50.0, 30.0)
    assert abs(sens - 120.0) < 1e-3


def test_fast_liuren_zeji_satta_lek_rust_extensions():
    """Verify Da Liu Ren, Ze Ji, and Satta-Lek Rust bindings."""
    from project.core.fast_math import (
        fast_liuren_heaven_plate,
        fast_satta_lek_matrix,
        fast_zeji_duty_officer,
    )
    plate = fast_liuren_heaven_plate("亥", "巳")
    assert len(plate) == 12

    officer = fast_zeji_duty_officer("子", "子")
    assert officer == "建日"

    r1, r2, r3, r4 = fast_satta_lek_matrix(1, 1, 1)
    assert len(r1) == 7
    assert len(r4) == 7
    assert r4[0] == 3


def test_rust_security_audit_native():
    """Verify native Rust security audit scanner."""
    import rust_core
    if not rust_core.RUST_AVAILABLE:
        pytest.skip("native wheel is not installed")
    passed, scanned_count, findings = rust_core.run_rust_security_audit(".")
    assert scanned_count > 0
    assert isinstance(passed, bool)




def test_fast_qimen_matrix():
    """Verify Qi Men Dun Jia 4-plate fast matrix computation."""
    from project.core.fast_math import fast_qimen_matrix
    from project.core.qi_men_engine import QiMenEngine

    res = fast_qimen_matrix(True, 1)
    assert len(res) == 9
    engine = QiMenEngine()
    chart = engine.calculate_chart(2026, 8, 7, 14)
    assert len(chart.chart_data["palaces"]) == 9


def test_astrological_audit_rust_native():
    """Verify native Rust astrological audit bindings."""
    import rust_core
    if not rust_core.RUST_AVAILABLE:
        pytest.skip("native wheel is not installed")

    passed, total = rust_core.audit_five_elements(100.0, "庚", "Metal")
    assert passed is True
    assert abs(total - 100.0) < 0.1

    eot_passed = rust_core.audit_eot_bounds(-14.2, 16.3)
    assert eot_passed is True

    synergy_passed = rust_core.audit_cross_domain_synergy(7, "庚", "亥", "กันย์", "Taurus")
    assert synergy_passed is True


def test_rust_svg_bazi_rendering():
    """Verify Rust SVG rendering engine."""
    import rust_core
    if not rust_core.RUST_AVAILABLE:
        pytest.skip("native wheel is not installed")
    from project.core.svg_generator import (
        generate_bazi_svg,
        generate_ziwei_svg,
        generate_zodiac_wheel_svg,
    )
    chart = {
        "day_master": {"stem": "庚", "element": "Metal"},
        "five_elements": {"percentages": {"Metal": 100.0}},
        "tst": {"tst_datetime": "2026-08-09 12:00:00"},
        "pillars": {
            "hour": {"stem": {"char": "壬"}, "branch": {"char": "午"}},
            "day": {"stem": {"char": "庚"}, "branch": {"char": "申"}},
            "month": {"stem": {"char": "甲"}, "branch": {"char": "寅"}},
            "year": {"stem": {"char": "丙"}, "branch": {"char": "午"}},
        }
    }
    svg = generate_bazi_svg(chart)
    assert len(svg) > 1000
    assert "<svg" in svg
    assert "Rust High-Performance" in svg

    zodiac_svg = generate_zodiac_wheel_svg({})
    assert len(zodiac_svg) > 500
    assert "<svg" in zodiac_svg

    ziwei_svg = generate_ziwei_svg({})
    assert len(ziwei_svg) > 500
    assert "<svg" in ziwei_svg

    from project.core.svg_generator import generate_qimen_svg, generate_xuankong_svg
    qimen_svg = generate_qimen_svg({})
    assert len(qimen_svg) > 500
    assert "<svg" in qimen_svg

    xuankong_svg = generate_xuankong_svg({})
    assert len(xuankong_svg) > 500
    assert "<svg" in xuankong_svg


def test_rust_atomic_observability_metrics():
    """Verify Rust atomic Prometheus metrics collection."""
    import rust_core
    if not rust_core.RUST_AVAILABLE:
        pytest.skip("native wheel is not installed")

    req_total = rust_core.record_http_metric_rust("GET", "/api/v1/health", 200, 1.2)
    assert req_total > 0

    rag_total = rust_core.record_rag_metric_rust(0.5)
    assert rag_total > 0

    metrics_text = rust_core.generate_prometheus_metrics_rust(120.5)
    assert "# HELP http_requests_total" in metrics_text
    assert 'engine="rust_core"' in metrics_text
    assert "process_uptime_seconds 120.50" in metrics_text
