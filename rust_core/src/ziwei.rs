/*!
 * rust_core/src/ziwei.rs
 * Zi Wei Dou Shu (紫微斗數) 14 Primary Stars & 12 Palaces Matrix Calculation Engine in Rust.
 */

#[cfg(feature = "python")]
use pyo3::prelude::*;
use serde_json::{json, Map, Value};

const STEMS: [&str; 10] = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"];
const BRANCHES: [&str; 12] = [
    "子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥",
];
const PALACE_NAMES: [&str; 12] = [
    "命宮",
    "兄弟宮",
    "夫妻宮",
    "子女宮",
    "財帛宮",
    "疾厄宮",
    "遷移宮",
    "交友宮",
    "官祿宮",
    "田宅宮",
    "福德宮",
    "父母宮",
];

pub fn calculate_ming_shen_gong_rust(lunar_month: i32, hour_branch_idx: usize) -> (usize, usize) {
    let m = (lunar_month - 1) as usize;
    let ming_idx = (2 + m + 12 - (hour_branch_idx % 12)) % 12;
    let shen_idx = (2 + m + (hour_branch_idx % 12)) % 12;
    (ming_idx, shen_idx)
}

pub fn calculate_zi_wei_star_branch_rust(bureau_number: i32, lunar_day: i32) -> usize {
    if bureau_number <= 0 {
        return 2;
    }
    let mut quotient = lunar_day / bureau_number;
    let remainder = lunar_day % bureau_number;
    let branch_idx = if remainder != 0 {
        let add_count = bureau_number - remainder;
        quotient = (lunar_day + add_count) / bureau_number;
        if add_count % 2 == 1 {
            (2 + quotient - 1 - add_count).rem_euclid(12)
        } else {
            (2 + quotient - 1 + add_count).rem_euclid(12)
        }
    } else {
        (2 + quotient - 1).rem_euclid(12)
    };
    branch_idx as usize
}

pub fn calculate_14_main_stars_rust(zi_wei_idx: usize) -> Vec<(usize, Vec<String>)> {
    let zi_wei_idx = zi_wei_idx % 12;
    let tian_fu_idx = (4 + 12 - zi_wei_idx) % 12;
    let zi_wei_stars = [
        ("紫微", zi_wei_idx),
        ("天機", (zi_wei_idx + 11) % 12),
        ("太陽", (zi_wei_idx + 9) % 12),
        ("武曲", (zi_wei_idx + 8) % 12),
        ("天同", (zi_wei_idx + 7) % 12),
        ("廉貞", (zi_wei_idx + 4) % 12),
    ];
    let tian_fu_stars = [
        ("天府", tian_fu_idx),
        ("太陰", (tian_fu_idx + 1) % 12),
        ("貪狼", (tian_fu_idx + 2) % 12),
        ("巨門", (tian_fu_idx + 3) % 12),
        ("天相", (tian_fu_idx + 4) % 12),
        ("天梁", (tian_fu_idx + 5) % 12),
        ("七殺", (tian_fu_idx + 6) % 12),
        ("破軍", (tian_fu_idx + 10) % 12),
    ];
    let mut grid = vec![Vec::new(); 12];
    for &(name, branch_index) in zi_wei_stars.iter().chain(tian_fu_stars.iter()) {
        grid[branch_index].push(name.to_string());
    }
    grid.into_iter().enumerate().collect()
}

fn five_element_bureau(year_stem: &str, ming_branch: &str) -> (&'static str, i32) {
    let start_stem = match year_stem {
        "甲" | "己" => "丙",
        "乙" | "庚" => "戊",
        "丙" | "辛" => "庚",
        "丁" | "壬" => "壬",
        _ => "甲",
    };
    let start_index = STEMS
        .iter()
        .position(|&stem| stem == start_stem)
        .unwrap_or(2);
    let branch_index = BRANCHES
        .iter()
        .position(|&branch| branch == ming_branch)
        .unwrap_or(2);
    let ming_stem = STEMS[(start_index + (branch_index + 10) % 12) % 10];
    let pair = format!("{ming_stem}{ming_branch}");
    let water = [
        "甲寅", "乙卯", "壬戌", "癸亥", "丙午", "丁未", "甲申", "乙酉", "壬辰", "癸巳",
    ];
    let wood = [
        "戊辰", "己巳", "壬午", "癸未", "庚寅", "辛卯", "戊戌", "己亥", "壬子", "癸丑",
    ];
    let metal = [
        "甲子", "乙丑", "壬申", "癸酉", "庚辰", "辛巳", "甲午", "乙未", "壬寅", "癸卯",
    ];
    let earth = [
        "丙辰", "丁巳", "庚午", "辛未", "戊申", "己酉", "丙戌", "丁亥", "庚子", "辛丑",
    ];
    if water.contains(&pair.as_str()) {
        ("水二局", 2)
    } else if wood.contains(&pair.as_str()) {
        ("木三局", 3)
    } else if metal.contains(&pair.as_str()) {
        ("金四局", 4)
    } else if earth.contains(&pair.as_str()) {
        ("土五局", 5)
    } else {
        ("火六局", 6)
    }
}

fn si_hua_for_stem(year_stem: &str) -> [(&'static str, &'static str); 4] {
    match year_stem {
        "甲" => [
            ("化祿", "廉貞"),
            ("化權", "破軍"),
            ("化科", "武曲"),
            ("化忌", "太陽"),
        ],
        "乙" => [
            ("化祿", "天機"),
            ("化權", "天梁"),
            ("化科", "紫微"),
            ("化忌", "太陰"),
        ],
        "丙" => [
            ("化祿", "天同"),
            ("化權", "天機"),
            ("化科", "文昌"),
            ("化忌", "廉貞"),
        ],
        "丁" => [
            ("化祿", "太陰"),
            ("化權", "天同"),
            ("化科", "天機"),
            ("化忌", "巨門"),
        ],
        "戊" => [
            ("化祿", "貪狼"),
            ("化權", "太陰"),
            ("化科", "右弼"),
            ("化忌", "天機"),
        ],
        "己" => [
            ("化祿", "武曲"),
            ("化權", "貪狼"),
            ("化科", "天梁"),
            ("化忌", "文曲"),
        ],
        "庚" => [
            ("化祿", "太陽"),
            ("化權", "武曲"),
            ("化科", "太陰"),
            ("化忌", "天同"),
        ],
        "辛" => [
            ("化祿", "巨門"),
            ("化權", "太陽"),
            ("化科", "文曲"),
            ("化忌", "文昌"),
        ],
        "壬" => [
            ("化祿", "天梁"),
            ("化權", "紫微"),
            ("化科", "左輔"),
            ("化忌", "武曲"),
        ],
        _ => [
            ("化祿", "破軍"),
            ("化權", "巨門"),
            ("化科", "太陰"),
            ("化忌", "貪狼"),
        ],
    }
}

/// Build the complete Zi Wei response using the same deterministic oracle as
/// the Python engine. Gender is retained for wire compatibility but does not
/// alter the current chart formula.
pub fn calculate_ziwei_chart_rust(
    year: i32,
    month: i32,
    day: i32,
    hour: i32,
    _gender: &str,
    calculation_timestamp: &str,
) -> Value {
    let cycle_year = i64::from(year) - 4;
    let stem_index = cycle_year.rem_euclid(10) as usize;
    let year_branch_index = cycle_year.rem_euclid(12) as usize;
    let year_stem = STEMS[stem_index];
    let year_branch = BRANCHES[year_branch_index];
    let hour_branch_index = ((i64::from(hour) + 1).div_euclid(2)).rem_euclid(12) as usize;
    let hour_branch = BRANCHES[hour_branch_index];
    let lunar_month = month.clamp(1, 12);
    let lunar_day = day.clamp(1, 30);
    let (ming_index, shen_index) = calculate_ming_shen_gong_rust(lunar_month, hour_branch_index);
    let ming_branch = BRANCHES[ming_index];
    let shen_branch = BRANCHES[shen_index];
    let (bureau_name, bureau_number) = five_element_bureau(year_stem, ming_branch);
    let zi_wei_index = calculate_zi_wei_star_branch_rust(bureau_number, lunar_day);
    let zi_wei_branch = BRANCHES[zi_wei_index];
    let tian_fu_branch = BRANCHES[(16 - zi_wei_index) % 12];
    let star_grid = calculate_14_main_stars_rust(zi_wei_index);
    let si_hua = si_hua_for_stem(year_stem);

    let palaces: Vec<Value> = PALACE_NAMES
        .iter()
        .enumerate()
        .map(|(index, &palace_name)| {
            let palace_branch_index = (ming_index + 12 - index) % 12;
            let stars = &star_grid[palace_branch_index].1;
            let mutators: Vec<String> = si_hua
                .iter()
                .filter(|(_, star)| stars.iter().any(|candidate| candidate == star))
                .map(|(mutator, star)| format!("{star}{mutator}"))
                .collect();
            json!({
                "palace_name": palace_name,
                "earth_branch": BRANCHES[palace_branch_index],
                "stars": stars,
                "mutators": mutators,
                "is_ming_gong": palace_branch_index == ming_index,
                "is_shen_gong": palace_branch_index == shen_index,
            })
        })
        .collect();
    let mut si_hua_json = Map::new();
    for &(mutator, star) in &si_hua {
        si_hua_json.insert(mutator.to_string(), json!(star));
    }

    json!({
        "engine": "ZiWeiEngine",
        "birth_solar": format!("{year:04}-{month:02}-{day:02} {hour:02}:00"),
        "year_stem_branch": format!("{year_stem}{year_branch}"),
        "hour_branch": hour_branch,
        "ming_gong_branch": ming_branch,
        "shen_gong_branch": shen_branch,
        "five_element_bureau": bureau_name,
        "zi_wei_star_branch": zi_wei_branch,
        "tian_fu_star_branch": tian_fu_branch,
        "si_hua": si_hua_json,
        "palaces": palaces,
        "engine_name": "Zi Wei Dou Shu Engine",
        "system_type": "ming_xue",
        "calculation_timestamp": calculation_timestamp,
    })
}

/// Calculate Ming Gong and Shen Gong branch indices.
#[cfg(feature = "python")]
#[pyfunction]
pub fn calculate_ming_shen_gong(
    py: Python<'_>,
    lunar_month: i32,
    hour_branch_idx: usize,
) -> PyResult<(usize, usize)> {
    let result =
        py.allow_threads(move || calculate_ming_shen_gong_rust(lunar_month, hour_branch_idx));
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
