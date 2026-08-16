"""
solar_time.py — True Solar Time (TST) Calculation Module
=========================================================
Formula:  TST = LMT + EoT
         LMT = Clock_Time + 4 * (λ − Λ_std)   [minutes]
         EoT = Equation of Time                 [minutes]

Reference: NOAA Solar Calculator algorithm
"""

import math
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any

# ---------------------------------------------------------------------------
# Data Containers
# ---------------------------------------------------------------------------

@dataclass
class SolarTimeResult:
    """Structured result from True Solar Time calculation."""
    input_datetime:            str
    longitude:                 float   # geographic longitude (deg, + east)
    utc_offset_hours:          float   # e.g. +7.0 for UTC+7
    standard_meridian:         float   # utc_offset * 15  (deg)
    longitude_offset_minutes:  float   # 4 * (λ − Λ_std)
    eot_minutes:               float   # Equation of Time (min)
    lmt_datetime:              str     # Local Mean Time
    tst_datetime:              str     # True Solar Time (main output)
    tst_hour:                  int
    tst_minute:                int
    tst_second:                int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Equation of Time (NOAA Spencer algorithm)
# ---------------------------------------------------------------------------

def _fractional_year_gamma(dt: datetime) -> float:
    """Fractional year γ in radians for the given datetime."""
    is_leap = (dt.year % 4 == 0 and dt.year % 100 != 0) or (dt.year % 400 == 0)
    days_in_year = 366.0 if is_leap else 365.0
    doy  = dt.timetuple().tm_yday
    frac = dt.hour / 24.0 + dt.minute / 1440.0 + dt.second / 86400.0
    return (2.0 * math.pi / days_in_year) * (doy - 1 + frac)


def calculate_equation_of_time(dt: datetime) -> float:
    """
    Compute the Equation of Time (EoT) in minutes using the NOAA algorithm.

    Returns minutes (+ve → solar noon before clock noon).
    """
    γ = _fractional_year_gamma(dt)
    eot = 229.18 * (
        0.000075
        + 0.001868 * math.cos(γ)
        - 0.032077 * math.sin(γ)
        - 0.014615 * math.cos(2 * γ)
        - 0.040849 * math.sin(2 * γ)
    )
    return round(eot, 4)


# ---------------------------------------------------------------------------
# True Solar Time
# ---------------------------------------------------------------------------

def calculate_true_solar_time(
    dt:               datetime,
    longitude:        float,
    utc_offset_hours: float,
) -> SolarTimeResult:
    """
    Calculate True Solar Time (TST).

    Parameters
    ----------
    dt               : Local clock datetime (naive, tz defined by utc_offset_hours)
    longitude        : Geographic longitude in degrees, positive = East
    utc_offset_hours : Timezone offset, e.g. 7.0 for Bangkok (UTC+7)

    Returns
    -------
    SolarTimeResult  : Full breakdown + TST datetime string
    """
    Λ_std   = utc_offset_hours * 15.0              # standard meridian (deg)
    δλ_min  = (longitude - Λ_std) * 4.0            # longitude correction (min)
    eot     = calculate_equation_of_time(dt)        # EoT (min)

    lmt_dt  = dt + timedelta(minutes=δλ_min)
    tst_dt  = dt + timedelta(minutes=δλ_min + eot)

    return SolarTimeResult(
        input_datetime           = dt.strftime("%Y-%m-%d %H:%M:%S"),
        longitude                = longitude,
        utc_offset_hours         = utc_offset_hours,
        standard_meridian        = Λ_std,
        longitude_offset_minutes = round(δλ_min, 4),
        eot_minutes              = eot,
        lmt_datetime             = lmt_dt.strftime("%Y-%m-%d %H:%M:%S"),
        tst_datetime             = tst_dt.strftime("%Y-%m-%d %H:%M:%S"),
        tst_hour                 = tst_dt.hour,
        tst_minute               = tst_dt.minute,
        tst_second               = tst_dt.second,
    )


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="True Solar Time Calculator")
    parser.add_argument("--dt",        required=True, help="Local datetime YYYY-MM-DD HH:MM:SS")
    parser.add_argument("--longitude", required=True, type=float, help="Longitude (deg, + east)")
    parser.add_argument("--utc",       required=True, type=float, help="UTC offset hours (e.g. 7)")
    args = parser.parse_args()

    dt_obj = datetime.strptime(args.dt, "%Y-%m-%d %H:%M:%S")
    result = calculate_true_solar_time(dt_obj, args.longitude, args.utc)
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
