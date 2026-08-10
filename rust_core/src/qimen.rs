/*!
 * rust_core/src/qimen.rs
 * Qi Men Dun Jia (奇門遁甲) 4-Plate 9-Palace Matrix Calculation Engine in Rust.
 */

#[cfg(feature = "python")]
use pyo3::prelude::*;
use serde_json::{json, Value};

const NINE_STARS: [&str; 9] = [
    "天蓬", "天芮", "天衝", "天輔", "天禽", "天心", "天柱", "天任", "天英",
];
const EIGHT_DOORS: [&str; 8] = [
    "休門", "生門", "傷門", "杜門", "景門", "死門", "驚門", "開門",
];
const EIGHT_SPIRITS: [&str; 8] = [
    "值符", "騰蛇", "太陰", "六合", "白虎", "玄武", "九地", "九天",
];
const PERIMETER_PALACES: [usize; 8] = [1, 8, 3, 4, 9, 2, 7, 6];

pub fn qimen_matrix_rust(
    dun_is_yang: bool,
    ju_number: i32,
) -> Vec<(i32, String, String, String, String)> {
    let stems_order = ["戊", "己", "庚", "辛", "壬", "癸", "丁", "丙", "乙"];
    let mut earth_plate = ["戊"; 10];
    for (index, &stem) in stems_order.iter().enumerate() {
        let palace = if dun_is_yang {
            (ju_number + index as i32 - 1).rem_euclid(9) + 1
        } else {
            (ju_number - index as i32 - 1).rem_euclid(9) + 1
        };
        earth_plate[palace as usize] = stem;
    }
    let mut doors = ["生門"; 10];
    let mut spirits = ["值符"; 10];
    for (index, &palace) in PERIMETER_PALACES.iter().enumerate() {
        doors[palace] = EIGHT_DOORS[index];
        spirits[palace] = EIGHT_SPIRITS[index];
    }
    (1..=9)
        .map(|palace| {
            (
                palace as i32,
                earth_plate[palace].to_string(),
                NINE_STARS[palace - 1].to_string(),
                doors[palace].to_string(),
                spirits[palace].to_string(),
            )
        })
        .collect()
}

fn determine_solar_term(month: i32, day: i32) -> &'static str {
    const TERM_DATES: [(i32, i32, &str); 24] = [
        (1, 6, "小寒"),
        (1, 20, "大寒"),
        (2, 4, "立春"),
        (2, 19, "雨水"),
        (3, 6, "驚蟄"),
        (3, 21, "春分"),
        (4, 5, "清明"),
        (4, 20, "谷雨"),
        (5, 6, "立夏"),
        (5, 21, "小滿"),
        (6, 6, "芒種"),
        (6, 21, "夏至"),
        (7, 7, "小暑"),
        (7, 23, "大暑"),
        (8, 7, "立秋"),
        (8, 23, "處暑"),
        (9, 7, "白露"),
        (9, 23, "秋分"),
        (10, 8, "寒露"),
        (10, 23, "霜降"),
        (11, 7, "立冬"),
        (11, 22, "小雪"),
        (12, 7, "大雪"),
        (12, 22, "冬至"),
    ];
    TERM_DATES
        .iter()
        .rev()
        .find_map(|&(candidate_month, candidate_day, term)| {
            ((month, day) >= (candidate_month, candidate_day)).then_some(term)
        })
        .unwrap_or("冬至")
}

fn dun_and_ju(term: &str) -> (&'static str, [i32; 3]) {
    match term {
        "冬至" | "驚蟄" => ("Yang", [1, 7, 4]),
        "清明" | "立夏" => ("Yang", [4, 1, 7]),
        "小寒" => ("Yang", [2, 8, 5]),
        "大寒" => ("Yang", [3, 9, 6]),
        "立春" => ("Yang", [8, 5, 2]),
        "雨水" => ("Yang", [9, 6, 3]),
        "谷雨" | "小滿" => ("Yang", [5, 2, 8]),
        "芒種" => ("Yang", [6, 3, 9]),
        "夏至" | "白露" => ("Yin", [9, 3, 6]),
        "小暑" => ("Yin", [8, 2, 5]),
        "大暑" => ("Yin", [7, 1, 4]),
        "立秋" => ("Yin", [2, 5, 8]),
        "處暑" => ("Yin", [1, 4, 7]),
        "秋分" => ("Yin", [7, 1, 4]),
        "寒露" | "立冬" => ("Yin", [6, 9, 3]),
        "霜降" => ("Yin", [5, 8, 2]),
        _ => ("Yang", [1, 7, 4]),
    }
}

/// Build the complete Qi Men response schema used by the Python API.
pub fn calculate_qimen_chart_rust(
    year: i32,
    month: i32,
    day: i32,
    hour: i32,
    solar_term: Option<&str>,
    calculation_timestamp: &str,
) -> Value {
    let term = solar_term.unwrap_or_else(|| determine_solar_term(month, day));
    let (dun_type, ju_options) = dun_and_ju(term);
    let yuan_index = ((day % 15) / 5).clamp(0, 2) as usize;
    let ju_number = ju_options[yuan_index];
    let palaces: Vec<Value> = qimen_matrix_rust(dun_type == "Yang", ju_number)
        .into_iter()
        .map(|(palace_number, earth_stem, star, door, spirit)| {
            json!({
                "palace_number": palace_number,
                "earth_stem": earth_stem,
                "star": star,
                "door": door,
                "spirit": spirit,
            })
        })
        .collect();
    json!({
        "engine": "QiMenEngine",
        "datetime": format!("{year:04}-{month:02}-{day:02} {hour:02}:00"),
        "solar_term": term,
        "dun_type": dun_type,
        "ju_number": ju_number,
        "palaces": palaces,
        "engine_name": "Qi Men Dun Jia Engine",
        "system_type": "san_shi",
        "calculation_timestamp": calculation_timestamp,
    })
}

pub fn qimen_9palace_matrix_rust(ju_number: i32) -> Vec<Vec<String>> {
    let dun_is_yang = ju_number > 0;
    let stems_order = ["戊", "己", "庚", "辛", "壬", "癸", "丁", "丙", "乙"];
    let mut earth_plate = ["戊"; 10];

    for (i, &stem) in stems_order.iter().enumerate() {
        let palace = if dun_is_yang {
            (ju_number.abs() + i as i32 - 1).rem_euclid(9) + 1
        } else {
            (ju_number.abs() - i as i32 - 1).rem_euclid(9) + 1
        };
        earth_plate[palace as usize] = stem;
    }

    let mut result = Vec::with_capacity(9);
    for p in 1..=9 {
        let row = vec![
            format!("Palace {}", p),
            earth_plate[p].to_string(),
            NINE_STARS[(p - 1) % 9].to_string(),
            EIGHT_DOORS[(p - 1) % 8].to_string(),
            EIGHT_SPIRITS[(p - 1) % 8].to_string(),
        ];
        result.push(row);
    }
    result
}

/// Calculate complete Qi Men Dun Jia 9-Palace 4-Plate matrix in Rust.
/// Returns list of tuples: (palace_num, earth_stem, star_name, door_name, spirit_name)
#[cfg(feature = "python")]
#[pyfunction]
pub fn qimen_9palace_matrix(
    py: Python<'_>,
    dun_is_yang: bool,
    ju_number: i32,
) -> PyResult<Vec<(i32, String, String, String, String)>> {
    let result = py.allow_threads(move || {
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
        result
    });
    Ok(result)
}
