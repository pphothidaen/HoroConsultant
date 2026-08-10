/*!
 * rust_core/src/solar.rs
 * True Solar Time and Equation of Time calculations.
 *
 * Formula: TST = LMT + EoT
 *          LMT = Clock_Time + 4 * (longitude - standard_meridian) minutes
 *
 * The complete calculation uses the NOAA Spencer 1971 fractional-year
 * formula and mirrors project/core/solar_time.py. The day-of-year function is
 * retained as a compatibility kernel for the existing PyO3 API.
 */

use chrono::{Datelike, Duration, NaiveDateTime, Timelike};
#[cfg(feature = "python")]
use pyo3::prelude::*;
use serde::{Deserialize, Serialize};
use std::error::Error;
use std::f64::consts::PI;
use std::fmt::{Display, Formatter};

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SolarTimeError(pub String);

impl Display for SolarTimeError {
    fn fmt(&self, formatter: &mut Formatter<'_>) -> std::fmt::Result {
        formatter.write_str(&self.0)
    }
}

impl Error for SolarTimeError {}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SolarTimeResult {
    pub input_datetime: String,
    pub longitude: f64,
    pub utc_offset_hours: f64,
    pub standard_meridian: f64,
    pub longitude_offset_minutes: f64,
    pub eot_minutes: f64,
    pub lmt_datetime: String,
    pub tst_datetime: String,
    pub tst_hour: u32,
    pub tst_minute: u32,
    pub tst_second: u32,
}

fn round_to(value: f64, decimal_places: i32) -> f64 {
    let scale = 10_f64.powi(decimal_places);
    (value * scale).round_ties_even() / scale
}

fn fractional_year_gamma(dt: NaiveDateTime) -> f64 {
    let days_in_year = if dt.date().leap_year() { 366.0 } else { 365.0 };
    let fraction =
        dt.hour() as f64 / 24.0 + dt.minute() as f64 / 1_440.0 + dt.second() as f64 / 86_400.0;
    (2.0 * PI / days_in_year) * (dt.ordinal() as f64 - 1.0 + fraction)
}

/// Compute Equation of Time minutes for a complete local datetime.
pub fn calculate_equation_of_time(dt: NaiveDateTime) -> f64 {
    let gamma = fractional_year_gamma(dt);
    round_to(
        229.18
            * (0.000075 + 0.001868 * gamma.cos()
                - 0.032077 * gamma.sin()
                - 0.014615 * (2.0 * gamma).cos()
                - 0.040849 * (2.0 * gamma).sin()),
        4,
    )
}

/// Compute Equation of Time minutes from day-of-year for the legacy PyO3 API.
pub fn equation_of_time_rust(day_of_year: i32) -> f64 {
    let gamma = 2.0 * PI * ((day_of_year - 1) as f64) / 365.0;
    229.18
        * (0.000075 + 0.001868 * gamma.cos()
            - 0.032077 * gamma.sin()
            - 0.014615 * (2.0 * gamma).cos()
            - 0.040849 * (2.0 * gamma).sin())
}

fn checked_add_minutes(dt: NaiveDateTime, minutes: f64) -> Result<NaiveDateTime, SolarTimeError> {
    let microseconds = (minutes * 60.0 * 1_000_000.0).round_ties_even();
    if !microseconds.is_finite() || microseconds < i64::MIN as f64 || microseconds > i64::MAX as f64
    {
        return Err(SolarTimeError(
            "solar-time offset is out of range".to_string(),
        ));
    }
    dt.checked_add_signed(Duration::microseconds(microseconds as i64))
        .ok_or_else(|| SolarTimeError("solar-time datetime is out of range".to_string()))
}

/// Calculate the complete True Solar Time response used by the Python engine.
pub fn calculate_true_solar_time(
    dt: NaiveDateTime,
    longitude: f64,
    utc_offset_hours: f64,
) -> Result<SolarTimeResult, SolarTimeError> {
    if !longitude.is_finite() || !(-180.0..=180.0).contains(&longitude) {
        return Err(SolarTimeError(
            "longitude must be finite and between -180 and 180".to_string(),
        ));
    }
    if !utc_offset_hours.is_finite() || !(-14.0..=14.0).contains(&utc_offset_hours) {
        return Err(SolarTimeError(
            "utc_offset_hours must be finite and between -14 and 14".to_string(),
        ));
    }

    let standard_meridian = utc_offset_hours * 15.0;
    let longitude_offset_minutes = (longitude - standard_meridian) * 4.0;
    let eot_minutes = calculate_equation_of_time(dt);
    let lmt = checked_add_minutes(dt, longitude_offset_minutes)?;
    let tst = checked_add_minutes(dt, longitude_offset_minutes + eot_minutes)?;
    let format = "%Y-%m-%d %H:%M:%S";

    Ok(SolarTimeResult {
        input_datetime: dt.format(format).to_string(),
        longitude,
        utc_offset_hours,
        standard_meridian,
        longitude_offset_minutes: round_to(longitude_offset_minutes, 4),
        eot_minutes,
        lmt_datetime: lmt.format(format).to_string(),
        tst_datetime: tst.format(format).to_string(),
        tst_hour: tst.hour(),
        tst_minute: tst.minute(),
        tst_second: tst.second(),
    })
}

#[cfg(feature = "python")]
#[pyfunction]
pub fn equation_of_time(day_of_year: i32) -> PyResult<f64> {
    Ok(equation_of_time_rust(day_of_year))
}
