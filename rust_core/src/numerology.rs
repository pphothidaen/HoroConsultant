/*!
 * rust_core/src/numerology.rs
 * High-performance Satta-Lek (สัตตเลข 7 ฐาน 4 แถว) & Chaldean Numerology matrix core.
 */

#[cfg(feature = "python")]
use pyo3::prelude::*;

pub fn calculate_satta_lek_matrix_rust(day_num: u8, month_num: u8, year_num: u16) -> Vec<Vec<u8>> {
    let mut row1 = Vec::with_capacity(7);
    let mut row2 = Vec::with_capacity(7);
    let mut row3 = Vec::with_capacity(7);
    let mut row4 = Vec::with_capacity(7);

    for i in 0..7 {
        let v1 = (day_num as u16 + i - 1) % 7 + 1;
        let v2 = (month_num as u16 + i - 1) % 7 + 1;
        let v3 = (year_num + i - 1) % 7 + 1;
        let v4 = v1 + v2 + v3;

        row1.push(v1 as u8);
        row2.push(v2 as u8);
        row3.push(v3 as u8);
        row4.push(v4 as u8);
    }
    vec![row1, row2, row3, row4]
}

/// Calculate Satta-Lek 7-Base 4-Row Matrix.
/// Returns 4 vectors representing (Row 1 Day Base, Row 2 Month Base, Row 3 Year Base, Row 4 Sum Base).
#[cfg(feature = "python")]
#[pyfunction]
pub fn calculate_satta_lek_matrix(
    py: Python<'_>,
    day_num: u32,
    lunar_month: u32,
    year_zodiac_num: u32,
) -> PyResult<(Vec<u32>, Vec<u32>, Vec<u32>, Vec<u32>)> {
    let result = py.allow_threads(move || {
        let mut row1 = Vec::with_capacity(7);
        let mut row2 = Vec::with_capacity(7);
        let mut row3 = Vec::with_capacity(7);
        let mut row4 = Vec::with_capacity(7);

        for i in 0..7 {
            let v1 = (day_num + i - 1) % 7 + 1;
            let v2 = (lunar_month + i - 1) % 7 + 1;
            let v3 = (year_zodiac_num + i - 1) % 7 + 1;
            let v4 = v1 + v2 + v3;

            row1.push(v1);
            row2.push(v2);
            row3.push(v3);
            row4.push(v4);
        }

        (row1, row2, row3, row4)
    });
    Ok(result)
}
