/*!
 * rust_core/src/fengshui.rs
 * Xuan Kong Flying Stars (玄空風水) 9-Grid Matrix Calculation Engine in Rust.
 */

use pyo3::prelude::*;

const MOUNTAINS: [(&str, f32, f32, &str, &str); 24] = [
    ("壬", 337.5, 352.5, "坎", "陽"),
    ("子", 352.5, 7.5, "坎", "陰"),
    ("癸", 7.5, 22.5, "坎", "陰"),
    ("丑", 22.5, 37.5, "艮", "陰"),
    ("艮", 37.5, 52.5, "艮", "陽"),
    ("寅", 52.5, 67.5, "艮", "陽"),
    ("甲", 67.5, 82.5, "震", "陽"),
    ("卯", 82.5, 97.5, "震", "陰"),
    ("乙", 97.5, 112.5, "震", "陰"),
    ("辰", 112.5, 127.5, "巽", "陰"),
    ("巽", 127.5, 142.5, "巽", "陽"),
    ("巳", 142.5, 157.5, "巽", "陽"),
    ("丙", 157.5, 172.5, "離", "陽"),
    ("午", 172.5, 187.5, "離", "陰"),
    ("丁", 187.5, 202.5, "離", "陰"),
    ("未", 202.5, 217.5, "坤", "陰"),
    ("坤", 217.5, 232.5, "坤", "陽"),
    ("申", 232.5, 247.5, "坤", "陽"),
    ("庚", 247.5, 262.5, "兌", "陽"),
    ("酉", 262.5, 277.5, "兌", "陰"),
    ("辛", 277.5, 292.5, "兌", "陰"),
    ("戌", 292.5, 307.5, "乾", "陰"),
    ("乾", 307.5, 322.5, "乾", "陽"),
    ("亥", 322.5, 337.5, "乾", "陽"),
];

// ─── Private inner functions (callable inside py.allow_threads) ──────────────

fn resolve_mountain_inner(degree: f32) -> (String, String, String) {
    let mut deg = degree % 360.0;
    if deg < 0.0 {
        deg += 360.0;
    }
    for (name, start, end, trigram, yinyang) in MOUNTAINS {
        if start > end {
            if deg >= start || deg < end {
                return (name.to_string(), trigram.to_string(), yinyang.to_string());
            }
        } else if deg >= start && deg < end {
            return (name.to_string(), trigram.to_string(), yinyang.to_string());
        }
    }
    ("子".to_string(), "坎".to_string(), "陰".to_string())
}

fn fly_stars_inner(center_star: i32, is_forward: bool) -> Vec<(i32, i32)> {
    let palace_sequence = [5, 6, 7, 8, 9, 1, 2, 3, 4];
    let mut res = Vec::with_capacity(9);
    for (idx, &palace) in palace_sequence.iter().enumerate() {
        let star = if is_forward {
            (center_star + idx as i32 - 1).rem_euclid(9) + 1
        } else {
            (center_star - idx as i32 - 1).rem_euclid(9) + 1
        };
        res.push((palace, star));
    }
    res
}

fn xuankong_9grid_impl(facing_degree: f32, _period: i32) -> Vec<(i32, i32, i32, i32)> {
    let (_f_name, _f_tri, f_yy) = resolve_mountain_inner(facing_degree);
    let (_s_name, _s_tri, s_yy) = resolve_mountain_inner(facing_degree + 180.0);

    // Period 9 base chart: palace -> base star
    let base_chart: [i32; 10] = [0, 5, 6, 7, 8, 9, 1, 2, 3, 4]; // 1-indexed by palace_num

    let center_sitting_star = base_chart[5]; // 9
    let center_facing_star = base_chart[9];  // 4

    let sitting_is_forward = s_yy == "陽";
    let facing_is_forward = f_yy == "陽";

    let sitting_tracks = fly_stars_inner(center_sitting_star, sitting_is_forward);
    let facing_tracks = fly_stars_inner(center_facing_star, facing_is_forward);

    let mut sit_map = [0i32; 10];
    for (p, s) in sitting_tracks {
        sit_map[p as usize] = s;
    }

    let mut face_map = [0i32; 10];
    for (p, s) in facing_tracks {
        face_map[p as usize] = s;
    }

    let mut grid = Vec::with_capacity(9);
    for p in 1..=9 {
        let base = base_chart[p];
        let sit = sit_map[p];
        let face = face_map[p];
        grid.push((p as i32, base, sit, face));
    }
    grid
}

pub fn resolve_mountain_rust(mountain_index: usize) -> String {
    let idx = mountain_index % 24;
    MOUNTAINS[idx].0.to_string()
}

pub fn xuankong_9grid_matrix_rust(period: i32, mountain_index: usize) -> Vec<Vec<i32>> {
    let facing_degree = (mountain_index % 24) as f32 * 15.0;
    let grid = xuankong_9grid_impl(facing_degree, period);
    grid.into_iter().map(|(p, b, s, f)| vec![p, b, s, f]).collect()
}

// ─── PyO3 Public Functions ────────────────────────────────────────────────────

/// Resolve degree to 24 Mountain (Name, Trigram, YinYang)
#[pyfunction]
pub fn resolve_mountain(py: Python<'_>, degree: f32) -> PyResult<(String, String, String)> {
    let result = py.allow_threads(move || resolve_mountain_inner(degree));
    Ok(result)
}

/// Calculate 9-palace flying star tracks for a given center star.
/// Sequence of Luo Shu palaces: 5, 6, 7, 8, 9, 1, 2, 3, 4
#[pyfunction]
pub fn fly_stars(py: Python<'_>, center_star: i32, is_forward: bool) -> PyResult<Vec<(i32, i32)>> {
    let result = py.allow_threads(move || fly_stars_inner(center_star, is_forward));
    Ok(result)
}

/// Calculate complete Xuan Kong Flying Star 9-Grid matrix for Period 9.
/// Returns a list of tuples: (palace_num, base_star, sitting_star, facing_star)
#[pyfunction]
pub fn xuankong_9grid_matrix(
    py: Python<'_>,
    facing_degree: f32,
    period: i32,
) -> PyResult<Vec<(i32, i32, i32, i32)>> {
    let result = py.allow_threads(move || xuankong_9grid_impl(facing_degree, period));
    Ok(result)
}

