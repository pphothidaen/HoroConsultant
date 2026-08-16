/*!
 * rust_core/src/uranian.rs
 * High-performance Western & Uranian Astrology midpoint & aspect math core.
 */

#[cfg(feature = "python")]
use pyo3::prelude::*;

#[cfg(feature = "python")]
static WESTERN_ZODIAC: [&str; 12] = [
    "Aries (เมษ)", "Taurus (พฤษภ)", "Gemini (เมถุน)", "Cancer (กรกฎ)",
    "Leo (สิงห์)", "Virgo (กันย์)", "Libra (ตุลย์)", "Scorpio (พิจิก)",
    "Sagittarius (ธนู)", "Capricorn (มังกร)", "Aquarius (กุมภ์)", "Pisces (มีน)"
];

pub fn calculate_midpoint_rust(deg1: f64, deg2: f64) -> f64 {
    let sum = (deg1 + deg2) / 2.0;
    sum.rem_euclid(360.0)
}

/// Resolve celestial longitude (0-360°) to Zodiac Sign & degree inside sign.
#[cfg(feature = "python")]
#[pyfunction]
pub fn resolve_western_zodiac(degree: f64) -> PyResult<(String, f64)> {
    let deg = degree.rem_euclid(360.0);
    let sign_idx = (deg / 30.0).floor() as usize;
    let in_sign_deg = deg % 30.0;
    Ok((WESTERN_ZODIAC[sign_idx % 12].to_string(), in_sign_deg))
}

/// Calculate Uranian midpoint (A + B) / 2 normalized to 0..360°.
#[cfg(feature = "python")]
#[pyfunction]
pub fn calculate_midpoint(deg1: f64, deg2: f64) -> PyResult<f64> {
    let sum = (deg1 + deg2) / 2.0;
    Ok(sum.rem_euclid(360.0))
}

/// Calculate Uranian Sensitive Point (A + B - C) normalized to 0..360°.
#[cfg(feature = "python")]
#[pyfunction]
pub fn calculate_sensitive_point(deg_a: f64, deg_b: f64, deg_c: f64) -> PyResult<f64> {
    let res = deg_a + deg_b - deg_c;
    Ok(res.rem_euclid(360.0))
}
