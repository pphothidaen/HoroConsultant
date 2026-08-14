/*!
 * rust_core/src/tai_yi.rs
 * Tai Yi Shen Shu (太乙神數) Calculation Engine in Rust.
 */

use pyo3::prelude::*;

/// Calculate Tai Yi Accumulated Years (太乙積年)
#[pyfunction]
pub fn tai_yi_accumulated_years(year: i32) -> i32 {
    let mut y = year;
    // Epoch offset is -4 (Wait, "accumulated = (year - 4) % 72" in user prompt)
    // "accumulated = (year - 4) % 72"
    let mut acc = (y - 4) % 72;
    if acc < 0 {
        acc += 72;
    }
    acc
}

/// Calculate 16-Path Tai Yi Star positioning
#[pyfunction]
pub fn tai_yi_star_palace(accumulated: i32) -> i32 {
    // "Place Tai Yi star in palace using (accumulated_years % 16) path index"
    let mut path = accumulated % 16;
    if path < 0 {
        path += 16;
    }
    // Mapping from path (0-15) to palace (1-9) is not fully specified, 
    // let's return path for now, or just use path as the palace.
    // The prompt says "using (accumulated_years % 16) path index". I'll return the index.
    path
}
