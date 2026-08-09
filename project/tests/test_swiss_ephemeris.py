"""
project/tests/test_swiss_ephemeris.py
======================================
Tests for Swiss Ephemeris module and fallback.
"""

from datetime import datetime

from project.core.swiss_ephemeris import (
    get_solar_position_ephemeris,
)


def test_get_solar_position_ephemeris_output():
    dt = datetime(2026, 8, 4, 12, 0, 0)
    res = get_solar_position_ephemeris(dt, longitude=100.5018, latitude=13.7563)

    assert "source" in res
    assert "sun_longitude_deg" in res
    assert isinstance(res["sun_longitude_deg"], float)
    assert 0.0 <= res["sun_longitude_deg"] <= 360.0


def test_calculate_qi_zheng_si_yu():
    from project.core.swiss_ephemeris import calculate_qi_zheng_si_yu
    dt = datetime(2026, 8, 7, 14, 0, 0)
    res = calculate_qi_zheng_si_yu(dt)

    assert res["engine"] == "QiZhengSiYuEphemeris"
    assert "planets_longitudes" in res
    assert len(res["planets_longitudes"]) == 11
    assert "日 (Sun)" in res["planets_longitudes"]
    assert "羅睺 (Rahu)" in res["planets_longitudes"]
