/*!
 * rust_core/src/zeji.rs
 * High-performance Imperial Calendar Date Selection (擇吉學) Duty Officers matrix core.
 */

#[cfg(feature = "python")]
use pyo3::prelude::*;

static BRANCHES: [&str; 12] = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"];

static DUTY_OFFICERS: [&str; 12] = [
    "建日", "除日", "滿日", "平日", "定日", "執日",
    "破日", "危日", "成日", "收日", "開日", "閉日"
];

pub fn calculate_zeji_duty_officer_rust(month_branch: &str, day_branch: &str) -> String {
    let month_idx = BRANCHES.iter().position(|&b| b == month_branch).unwrap_or(0);
    let day_idx = BRANCHES.iter().position(|&b| b == day_branch).unwrap_or(0);
    let officer_idx = (day_idx + 12 - month_idx) % 12;
    DUTY_OFFICERS[officer_idx].to_string()
}

pub fn check_branch_clash_rust(day_branch: &str, target_branch: &str) -> bool {
    let day_idx = BRANCHES.iter().position(|&b| b == day_branch).unwrap_or(0);
    let target_idx = BRANCHES.iter().position(|&b| b == target_branch).unwrap_or(0);
    (day_idx + 6) % 12 == target_idx
}

/// Calculate 12 Duty Officer name for Date Selection based on Month Branch and Day Branch.
#[cfg(feature = "python")]
#[pyfunction]
pub fn calculate_zeji_duty_officer(
    py: Python<'_>,
    month_branch: &str,
    day_branch: &str,
) -> PyResult<String> {
    let month_branch = month_branch.to_owned();
    let day_branch = day_branch.to_owned();
    let result = py.allow_threads(move || {
        let month_idx = BRANCHES.iter().position(|&b| b == month_branch).unwrap_or(0);
        let day_idx = BRANCHES.iter().position(|&b| b == day_branch).unwrap_or(0);
        let officer_idx = (day_idx + 12 - month_idx) % 12;
        DUTY_OFFICERS[officer_idx].to_string()
    });
    Ok(result)
}

/// Check if Day Branch conflicts (clashes) with Month Branch (Month Breaker 月破) or Year Branch (Year Breaker 歲破).
#[cfg(feature = "python")]
#[pyfunction]
pub fn check_branch_clash(
    py: Python<'_>,
    day_branch: &str,
    target_branch: &str,
) -> PyResult<bool> {
    let day_branch = day_branch.to_owned();
    let target_branch = target_branch.to_owned();
    let result = py.allow_threads(move || {
        let day_idx = BRANCHES.iter().position(|&b| b == day_branch).unwrap_or(0);
        let target_idx = BRANCHES.iter().position(|&b| b == target_branch).unwrap_or(0);
        // Opposite branches clash (distance of 6)
        (day_idx + 6) % 12 == target_idx
    });
    Ok(result)
}
