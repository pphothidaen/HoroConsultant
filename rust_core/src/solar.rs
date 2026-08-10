/*!
 * rust_core/src/solar.rs
 * Equation of Time (EoT) calculation in Rust (NOAA Spencer 1971 formula).
 */

#[cfg(feature = "python")]
use pyo3::prelude::*;
use std::f64::consts::PI;

/// Compute Equation of Time minutes using the NOAA Spencer 1971 formula.
pub fn equation_of_time_rust(day_of_year: i32) -> f64 {
    let gamma = 2.0 * PI * ((day_of_year - 1) as f64) / 365.0;
    229.18
        * (0.000075
            + 0.001868 * gamma.cos()
            - 0.032077 * gamma.sin()
            - 0.014615 * (2.0 * gamma).cos()
            - 0.040849 * (2.0 * gamma).sin())
}

#[cfg(feature = "python")]
#[pyfunction]
pub fn equation_of_time(day_of_year: i32) -> PyResult<f64> {
    Ok(equation_of_time_rust(day_of_year))
}
