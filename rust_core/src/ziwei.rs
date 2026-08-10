/*!
 * rust_core/src/ziwei.rs
 * Zi Wei Dou Shu (紫微斗數) 14 Primary Stars & 12 Palaces Matrix Calculation Engine in Rust.
 */

#[cfg(feature = "python")]
use pyo3::prelude::*;



pub fn calculate_ming_shen_gong_rust(lunar_month: i32, hour_branch_idx: usize) -> (usize, usize) {
    let m = (lunar_month - 1) as usize;
    let ming_idx = (2 + m + 12 - (hour_branch_idx % 12)) % 12;
    let shen_idx = (2 + m + (hour_branch_idx % 12)) % 12;
    (ming_idx, shen_idx)
}

/// Calculate Ming Gong and Shen Gong branch indices.
#[cfg(feature = "python")]
#[pyfunction]
pub fn calculate_ming_shen_gong(
    py: Python<'_>,
    lunar_month: i32,
    hour_branch_idx: usize,
) -> PyResult<(usize, usize)> {
    let result = py.allow_threads(move || {
        calculate_ming_shen_gong_rust(lunar_month, hour_branch_idx)
    });
    Ok(result)
}

/// Calculate Zi Wei Star branch index based on Bureau Number and Lunar Day.
#[cfg(feature = "python")]
#[pyfunction]
pub fn calculate_zi_wei_star_branch(
    py: Python<'_>,
    bureau_number: i32,
    lunar_day: i32,
) -> PyResult<usize> {
    let result = py.allow_threads(move || {
        if bureau_number <= 0 {
            return 2usize;
        }
        let mut quotient = lunar_day / bureau_number;
        let remainder = lunar_day % bureau_number;
        let branch_idx = if remainder != 0 {
            let add_count = bureau_number - remainder;
            let total = lunar_day + add_count;
            quotient = total / bureau_number;
            if add_count % 2 == 1 {
                (2 + quotient - 1 + 12 - (add_count % 12)) % 12
            } else {
                (2 + quotient - 1 + add_count) % 12
            }
        } else {
            (2 + quotient - 1) % 12
        };
        branch_idx as usize
    });
    Ok(result)
}

/// Compute 14 Primary Stars placement for all 12 Earth Branches in Rust.
/// Returns a vector of tuples: (branch_idx, list_of_star_names)
#[cfg(feature = "python")]
#[pyfunction]
pub fn calculate_14_main_stars(
    py: Python<'_>,
    zi_wei_idx: usize,
) -> PyResult<Vec<(usize, Vec<String>)>> {
    let result = py.allow_threads(move || {
        let tian_fu_idx = (4 + 12 - (zi_wei_idx % 12)) % 12;

        let zi_wei_stars = [
            ("紫微", zi_wei_idx % 12),
            ("天機", (zi_wei_idx + 12 - 1) % 12),
            ("太陽", (zi_wei_idx + 12 - 3) % 12),
            ("武曲", (zi_wei_idx + 12 - 4) % 12),
            ("天同", (zi_wei_idx + 12 - 5) % 12),
            ("廉貞", (zi_wei_idx + 12 - 8) % 12),
        ];

        let tian_fu_stars = [
            ("天府", tian_fu_idx % 12),
            ("太陰", (tian_fu_idx + 1) % 12),
            ("貪狼", (tian_fu_idx + 2) % 12),
            ("巨門", (tian_fu_idx + 3) % 12),
            ("天相", (tian_fu_idx + 4) % 12),
            ("天梁", (tian_fu_idx + 5) % 12),
            ("七殺", (tian_fu_idx + 6) % 12),
            ("破軍", (tian_fu_idx + 10) % 12),
        ];

        let mut grid: Vec<Vec<String>> = vec![Vec::new(); 12];
        for (name, b_idx) in zi_wei_stars.iter().chain(tian_fu_stars.iter()) {
            grid[*b_idx].push(name.to_string());
        }

        grid.into_iter()
            .enumerate()
            .map(|(b_idx, stars)| (b_idx, stars))
            .collect()
    });
    Ok(result)
}
