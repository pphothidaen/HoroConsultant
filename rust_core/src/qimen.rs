/*!
 * rust_core/src/qimen.rs
 * Qi Men Dun Jia (奇門遁甲) 4-Plate 9-Palace Matrix Calculation Engine in Rust.
 */

use pyo3::prelude::*;

const NINE_STARS: [&str; 9] = ["天蓬", "天芮", "天衝", "天輔", "天禽", "天心", "天柱", "天任", "天英"];
const EIGHT_DOORS: [&str; 8] = ["休門", "生門", "傷門", "杜門", "景門", "死門", "驚門", "開門"];
const EIGHT_SPIRITS: [&str; 8] = ["值符", "騰蛇", "太陰", "六合", "白虎", "玄武", "九地", "九天"];
const PERIMETER_PALACES: [usize; 8] = [1, 8, 3, 4, 9, 2, 7, 6];

/// Calculate complete Qi Men Dun Jia 9-Palace 4-Plate matrix in Rust.
/// Returns list of tuples: (palace_num, earth_stem, star_name, door_name, spirit_name)
#[pyfunction]
pub fn qimen_9palace_matrix(dun_is_yang: bool, ju_number: i32) -> PyResult<Vec<(i32, String, String, String, String)>> {
    let stems_order = ["戊", "己", "庚", "辛", "壬", "癸", "丁", "丙", "乙"];
    let mut earth_plate = ["戊"; 10]; // 1-indexed by palace_num

    for (i, &stem) in stems_order.iter().enumerate() {
        let palace = if dun_is_yang {
            (ju_number + i as i32 - 1).rem_euclid(9) + 1
        } else {
            (ju_number - i as i32 - 1).rem_euclid(9) + 1
        };
        earth_plate[palace as usize] = stem;
    }

    let mut stars_plate = ["天輔"; 10];
    for (idx, &star) in NINE_STARS.iter().enumerate() {
        let p = (idx % 9) + 1;
        stars_plate[p] = star;
    }

    let mut doors_plate = ["生門"; 10];
    for (idx, &door) in EIGHT_DOORS.iter().enumerate() {
        let p = PERIMETER_PALACES[idx % 8];
        doors_plate[p] = door;
    }

    let mut spirits_plate = ["值符"; 10];
    for (idx, &spirit) in EIGHT_SPIRITS.iter().enumerate() {
        let p = PERIMETER_PALACES[idx % 8];
        spirits_plate[p] = spirit;
    }

    let mut result = Vec::with_capacity(9);
    for p in 1..=9 {
        result.push((
            p as i32,
            earth_plate[p].to_string(),
            stars_plate[p].to_string(),
            doors_plate[p].to_string(),
            spirits_plate[p].to_string(),
        ));
    }

    Ok(result)
}
