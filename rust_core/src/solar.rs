/*!
 * rust_core/src/solar.rs
 * Equation of Time (EoT) calculation in Rust (NOAA Spencer 1971 formula).
 */

use pyo3::prelude::*;
use std::f64::consts::PI;

#[pyfunction]
pub fn equation_of_time(day_of_year: i32) -> PyResult<f64> {
    let gamma = 2.0 * PI * ((day_of_year - 1) as f64) / 365.0;
    let eot_minutes = 229.18
        * (0.000075
            + 0.001868 * gamma.cos()
            - 0.032077 * gamma.sin()
            - 0.014615 * (2.0 * gamma).cos()
            - 0.040849 * (2.0 * gamma).sin());
    Ok(eot_minutes)
}
