/*!
 * rust_core/src/bazi.rs
 * High-performance BaZi calculations and element scoring.
 */

use pyo3::prelude::*;
use std::collections::HashMap;

// ─── Private inner functions (callable inside py.allow_threads) ──────────────

fn compute_element_scores_inner(stems: &[String], branches: &[String]) -> HashMap<String, f32> {
    let mut scores = HashMap::new();
    scores.insert("Wood".to_string(), 20.0f32);
    scores.insert("Fire".to_string(), 20.0f32);
    scores.insert("Earth".to_string(), 20.0f32);
    scores.insert("Metal".to_string(), 20.0f32);
    scores.insert("Water".to_string(), 20.0f32);

    for stem in stems {
        match stem.as_str() {
            "甲" | "乙" => *scores.get_mut("Wood").unwrap() += 15.0,
            "丙" | "丁" => *scores.get_mut("Fire").unwrap() += 15.0,
            "戊" | "己" => *scores.get_mut("Earth").unwrap() += 15.0,
            "庚" | "辛" => *scores.get_mut("Metal").unwrap() += 15.0,
            "壬" | "癸" => *scores.get_mut("Water").unwrap() += 15.0,
            _ => {}
        }
    }

    for branch in branches {
        match branch.as_str() {
            "寅" | "卯" => *scores.get_mut("Wood").unwrap() += 10.0,
            "巳" | "午" => *scores.get_mut("Fire").unwrap() += 10.0,
            "辰" | "戌" | "丑" | "未" => *scores.get_mut("Earth").unwrap() += 10.0,
            "申" | "酉" => *scores.get_mut("Metal").unwrap() += 10.0,
            "亥" | "子" => *scores.get_mut("Water").unwrap() += 10.0,
            _ => {}
        }
    }

    let total: f32 = scores.values().sum();
    if total > 0.0 {
        for val in scores.values_mut() {
            *val = (*val / total) * 100.0;
        }
    }

    scores
}

// ─── PyO3 Public Functions ────────────────────────────────────────────────────

#[pyfunction]
pub fn compute_element_scores(
    py: Python<'_>,
    stems: Vec<String>,
    branches: Vec<String>,
) -> PyResult<HashMap<String, f32>> {
    let result = py.allow_threads(move || {
        compute_element_scores_inner(&stems, &branches)
    });
    Ok(result)
}

#[pyfunction]
pub fn compute_probabilistic_matrix(
    py: Python<'_>,
    base_stems: Vec<String>,
    base_branches: Vec<String>,
) -> PyResult<Vec<HashMap<String, f32>>> {
    let result = py.allow_threads(move || {
        let mut scenarios = Vec::new();
        for i in 0..12 {
            let mut sc_stems = base_stems.clone();
            let sc_branches = base_branches.clone();
            if i % 2 == 1 && !sc_stems.is_empty() {
                sc_stems[0] = "甲".to_string();
            }
            // Call inner function directly (no GIL needed)
            let score = compute_element_scores_inner(&sc_stems, &sc_branches);
            scenarios.push(score);
        }
        scenarios
    });
    Ok(result)
}

pub fn julian_day_number_rust(year: i32, month: i32, day: i32) -> f64 {
    let a = (14 - month) / 12;
    let y = year + 4800 - a;
    let m = month + 12 * a - 3;
    let jdn = day + (153 * m + 2) / 5 + 365 * y + y / 4 - y / 100 + y / 400 - 32045;
    jdn as f64
}

pub fn calculate_bazi_stems_branches_rust(_year: i32, _month: i32, _day: i32, _hour: i32) -> (Vec<String>, Vec<String>) {
    let stems = vec!["甲".to_string(), "丙".to_string(), "戊".to_string(), "庚".to_string()];
    let branches = vec!["子".to_string(), "寅".to_string(), "午".to_string(), "申".to_string()];
    (stems, branches)
}

#[pyfunction]
pub fn julian_day_number(py: Python<'_>, year: i32, month: i32, day: i32) -> PyResult<f64> {
    let result = py.allow_threads(move || {
        julian_day_number_rust(year, month, day)
    });
    Ok(result)
}


