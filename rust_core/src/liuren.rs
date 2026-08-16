/*!
 * rust_core/src/liuren.rs
 * High-performance Da Liu Ren (大六壬) Heaven Plate matrix core.
 */

#[cfg(feature = "python")]
use pyo3::prelude::*;
use serde_json::{json, Map, Value};

static BRANCHES: [&str; 12] = [
    "子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥",
];
static HEAVENLY_GENERALS: [&str; 12] = [
    "貴人", "螣蛇", "朱雀", "六合", "勾陳", "青龍", "天空", "白虎", "太常", "玄武", "太陰", "天后",
];

fn heaven_plate_pairs(
    month_general_branch: &str,
    hour_branch: &str,
) -> Result<Vec<(String, String)>, String> {
    let general_index = BRANCHES
        .iter()
        .position(|&branch| branch == month_general_branch)
        .ok_or_else(|| format!("invalid month-general branch: {month_general_branch}"))?;
    let hour_index = BRANCHES
        .iter()
        .position(|&branch| branch == hour_branch)
        .ok_or_else(|| format!("invalid hour branch: {hour_branch}"))?;
    Ok((0..12)
        .map(|index| {
            (
                BRANCHES[(hour_index + index) % 12].to_string(),
                BRANCHES[(general_index + index) % 12].to_string(),
            )
        })
        .collect())
}

/// Build the complete Da Liu Ren response schema used by the Python engine.
pub fn calculate_liuren_chart_rust(
    day_stem: &str,
    day_branch: &str,
    month_general: &str,
    hour_branch: &str,
    calculation_timestamp: &str,
) -> Result<Value, String> {
    let month_general_branch = match month_general {
        "正月" => "亥",
        "二月" => "戌",
        "三月" => "酉",
        "四月" => "申",
        "五月" => "未",
        "六月" => "午",
        "七月" => "巳",
        "八月" => "辰",
        "九月" => "卯",
        "十月" => "寅",
        "十一月" => "丑",
        "十二月" => "子",
        _ => "亥",
    };
    let pairs = heaven_plate_pairs(month_general_branch, hour_branch)?;
    let mut heaven_plate = Map::new();
    for (earth, heaven) in pairs {
        heaven_plate.insert(earth, json!(heaven));
    }
    let parasitic_branch = match day_stem {
        "甲" => "寅",
        "乙" => "辰",
        "丙" | "戊" => "巳",
        "丁" | "己" => "未",
        "庚" => "申",
        "辛" => "戌",
        "壬" => "亥",
        "癸" => "丑",
        _ => "寅",
    };
    let heaven_over = |branch: &str, fallback: &'static str| {
        heaven_plate
            .get(branch)
            .and_then(Value::as_str)
            .unwrap_or(fallback)
            .to_string()
    };
    let lesson_one_top = heaven_over(parasitic_branch, "寅");
    let lesson_two_top = heaven_over(&lesson_one_top, "寅");
    let lesson_three_top = heaven_over(day_branch, "子");
    let lesson_four_top = heaven_over(&lesson_three_top, "子");
    let four_lessons = vec![
        json!({"lesson_name":"第一課 (干上)","bottom":day_stem,"top":lesson_one_top}),
        json!({"lesson_name":"第二課 (干上上)","bottom":lesson_one_top,"top":lesson_two_top}),
        json!({"lesson_name":"第三課 (支上)","bottom":day_branch,"top":lesson_three_top}),
        json!({"lesson_name":"第四課 (支上上)","bottom":lesson_three_top,"top":lesson_four_top}),
    ];
    let first_transmission = four_lessons[0]["top"].as_str().unwrap_or("寅");
    let middle_transmission = heaven_over(first_transmission, "子");
    let final_transmission = heaven_over(&middle_transmission, "子");
    let noble_index = BRANCHES
        .iter()
        .position(|&branch| branch == month_general_branch)
        .unwrap_or(0);
    let mut generals_plate = Map::new();
    for (index, &general) in HEAVENLY_GENERALS.iter().enumerate() {
        generals_plate.insert(
            BRANCHES[(noble_index + index) % 12].to_string(),
            json!(general),
        );
    }

    Ok(json!({
        "engine": "LiuRenEngine",
        "day_stem_branch": format!("{day_stem}{day_branch}"),
        "month_general": format!("{month_general} ({month_general_branch})"),
        "hour_branch": hour_branch,
        "heaven_plate": heaven_plate,
        "four_lessons": four_lessons,
        "three_transmissions": {
            "初傳 (發端)": first_transmission,
            "中傳 (移革)": middle_transmission,
            "末傳 (歸結)": final_transmission,
        },
        "generals_plate": generals_plate,
        "engine_name": "Da Liu Ren Engine",
        "system_type": "san_shi",
        "calculation_timestamp": calculation_timestamp,
    }))
}

pub fn calculate_liuren_heaven_plate_rust(
    month_general_branch: &str,
    hour_branch: &str,
) -> Vec<String> {
    let gen_idx = BRANCHES
        .iter()
        .position(|&b| b == month_general_branch)
        .unwrap_or(0);
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
pub fn calculate_liuren_heaven_plate(
    month_general_branch: &str,
    hour_branch: &str,
) -> PyResult<Vec<(String, String)>> {
    let gen_idx = BRANCHES
        .iter()
        .position(|&b| b == month_general_branch)
        .unwrap_or(0);
    let hour_idx = BRANCHES.iter().position(|&b| b == hour_branch).unwrap_or(0);

    let mut heaven_plate = Vec::with_capacity(12);
    for i in 0..12 {
        let earth_b = BRANCHES[(hour_idx + i) % 12];
        let heaven_b = BRANCHES[(gen_idx + i) % 12];
        heaven_plate.push((earth_b.to_string(), heaven_b.to_string()));
    }

    Ok(heaven_plate)
}
