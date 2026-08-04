"""
project/tests/test_swiss_ephemeris.py
======================================
Tests for Swiss Ephemeris module and fallback.
"""

from datetime import datetime
from project.core.swiss_ephemeris import get_solar_position_ephemeris, SWISS_EPHEMERIS_AVAILABLE


def test_get_solar_position_ephemeris_output():
    dt = datetime(2026, 8, 4, 12, 0, 0)
    res = get_solar_position_ephemeris(dt, longitude=100.5018, latitude=13.7563)

    assert "source" in res
    assert "sun_longitude_deg" in res
    assert isinstance(res["sun_longitude_deg"], float)
    assert 0.0 <= res["sun_longitude_deg"] <= 360.0
