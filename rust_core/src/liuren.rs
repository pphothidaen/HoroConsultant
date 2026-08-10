/*!
 * rust_core/src/liuren.rs
 * High-performance Da Liu Ren (大六壬) Heaven Plate matrix core.
 */

#[cfg(feature = "python")]
use pyo3::prelude::*;

static BRANCHES: [&str; 12] = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"];

pub fn calculate_liuren_heaven_plate_rust(month_general_branch: &str, hour_branch: &str) -> Vec<String> {
    let gen_idx = BRANCHES.iter().position(|&b| b == month_general_branch).unwrap_or(0);
    let hour_idx = BRANCHES.iter().position(|&b| b == hour_branch).unwrap_or(0);

    let mut heaven_plate = Vec::with_capacity(12);
    for i in 0..12 {
        let earth_b = BRANCHES[(hour_idx + i) % 12];
        let heaven_b = BRANCHES[(gen_idx + i) % 12];
        heaven_plate.push(format!("Earth {} -> Heaven {}", earth_b, heaven_b));
    }
    heaven_plate
}

/// Calculate Da Liu Ren Heaven Plate mapping (Earth Branch -> Heaven Branch).
#[cfg(feature = "python")]
#[pyfunction]
pub fn calculate_liuren_heaven_plate(month_general_branch: &str, hour_branch: &str) -> PyResult<Vec<(String, String)>> {
    let gen_idx = BRANCHES.iter().position(|&b| b == month_general_branch).unwrap_or(0);
    let hour_idx = BRANCHES.iter().position(|&b| b == hour_branch).unwrap_or(0);

    let mut heaven_plate = Vec::with_capacity(12);
    for i in 0..12 {
        let earth_b = BRANCHES[(hour_idx + i) % 12];
        let heaven_b = BRANCHES[(gen_idx + i) % 12];
        heaven_plate.push((earth_b.to_string(), heaven_b.to_string()));
    }

    Ok(heaven_plate)
}
