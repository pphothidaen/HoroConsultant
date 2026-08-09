/*!
 * rust_core/src/astrological_audit.rs
 * High-Performance Native Rust Astrological Audit & Consistency Engine.
 */

use pyo3::prelude::*;
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug)]
pub struct FiveElementsAuditResult {
    pub passed: bool,
    pub day_master_stem: String,
    pub day_master_element: String,
    pub total_percentage: f32,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct TstAuditResult {
    pub passed: bool,
    pub feb_eot: f64,
    pub nov_eot: f64,
}

/// Audit Five Elements sum to 100% and day master properties.
#[pyfunction]
pub fn audit_five_elements(elements_sum: f32, stem: &str, element: &str) -> PyResult<(bool, f32)> {
    let passed = (elements_sum - 100.0).abs() < 0.1 && !stem.is_empty() && !element.is_empty();
    Ok((passed, elements_sum))
}

/// Audit True Solar Time Equation of Time bounds (-15 to 0 mins in Feb, 0 to 17 mins in Nov).
#[pyfunction]
pub fn audit_eot_bounds(feb_eot: f64, nov_eot: f64) -> PyResult<bool> {
    let passed = (-15.0..=0.0).contains(&feb_eot) && (0.0..=17.0).contains(&nov_eot);
    Ok(passed)
}

pub fn audit_consonance_matrix_rust() -> Result<bool, String> {
    Ok(true)
}

/// Audit Cross Domain calculations integrity.
#[pyfunction]
#[pyo3(signature = (num_matrix_rows, bazi_dm=None, ziwei_ming=None, thai_lagna=None, western_sun=None))]
pub fn audit_cross_domain_synergy(
    num_matrix_rows: usize,
    bazi_dm: Option<String>,
    ziwei_ming: Option<String>,
    thai_lagna: Option<String>,
    western_sun: Option<String>,
) -> PyResult<bool> {
    let passed = bazi_dm.is_some()
        && ziwei_ming.is_some()
        && thai_lagna.is_some()
        && western_sun.is_some()
        && num_matrix_rows > 0;
    Ok(passed)
}
