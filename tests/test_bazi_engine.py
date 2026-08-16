"""
tests/test_bazi_engine.py — BaZi Engine Reference Tests
"""

from __future__ import annotations
from datetime import datetime
import pytest

from project.core.bazi_engine import BaZiEngine


def test_bazi_reference_test_case():
    engine = BaZiEngine()
    result = engine.calculate(
        dt=datetime(1985, 8, 26, 23, 3, 0),
        longitude=99.91,
        utc_offset_hours=7.0,
        gender="male",
        name="ป๋อง",
        surname="กพล",
        dayun_formula="ravi",
    )
    chart = result.chart_data
    assert chart["pillars"]["hour"]["stem"]["char"] == "辛"
    assert chart["pillars"]["day"]["stem"]["char"] == "丁"
    assert chart["pillars"]["month"]["stem"]["char"] == "甲"
    assert chart["pillars"]["year"]["stem"]["char"] == "乙"
    assert chart["ming_gua"]["kua_number"] == 6
    assert chart["dayun"]["cycles"][0]["stem"] == "癸"
    assert chart["dayun"]["cycles"][0]["branch"] == "未"
