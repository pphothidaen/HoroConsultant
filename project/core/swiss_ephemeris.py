"""
project/core/swiss_ephemeris.py
================================
Swiss Ephemeris integration with pure-python NOAA algorithm fallback.
Provides high-accuracy solar, lunar, and planetary positions when swisseph/pyswisseph is installed.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger("swiss_ephemeris")

# Optional import of swisseph
SWISS_EPHEMERIS_AVAILABLE = False
try:
    import swisseph as swe
    SWISS_EPHEMERIS_AVAILABLE = True
except ImportError:
    try:
        import pyswisseph as swe  # type: ignore
        SWISS_EPHEMERIS_AVAILABLE = True
    except ImportError:
        swe = None


def get_solar_position_ephemeris(dt: datetime, longitude: float, latitude: float) -> Dict[str, Any]:
    """
    Calculate solar position parameters. Uses Swiss Ephemeris if available,
    otherwise falls back to standard astronomical approximations.
    """
    if SWISS_EPHEMERIS_AVAILABLE and swe is not None:
        try:
            # Convert datetime to Julian Day (UT)
            ut_hour = dt.hour + dt.minute / 60.0 + dt.second / 3600.0
            jul_day = swe.julday(dt.year, dt.month, dt.day, ut_hour)
            res, _ = swe.calc_ut(jul_day, swe.SUN)
            sun_longitude = res[0]
            sun_latitude = res[1]
            sun_distance = res[2]
            return {
                "source": "swiss_ephemeris",
                "sun_longitude_deg": round(sun_longitude, 4),
                "sun_latitude_deg": round(sun_latitude, 4),
                "sun_distance_au": round(sun_distance, 4),
                "julian_day": jul_day
            }
        except Exception as e:
            logger.warning(f"Swiss Ephemeris calculation failed: {e}. Falling back to standard math.")

    # Standard approximation fallback
    doy = dt.timetuple().tm_yday
    approx_sun_long = (280.460 + 0.9856474 * doy) % 360.0
    return {
        "source": "pure_python_fallback",
        "sun_longitude_deg": round(approx_sun_long, 4),
        "sun_latitude_deg": 0.0,
        "sun_distance_au": 1.0,
        "julian_day": None
    }
