use pyo3::prelude::*;

const MOUNTAINS_24: [&str; 24] = [
    "壬", "子", "癸", "丑", "艮", "寅", "甲", "卯",
    "乙", "辰", "巽", "巳", "丙", "午", "丁", "未",
    "坤", "申", "庚", "酉", "辛", "戌", "乾", "亥"
];

#[pyfunction]
pub fn san_he_resolve_mountain(degree: f64) -> usize {
    let mut deg = (degree % 360.0 + 360.0) % 360.0;
    let mut shifted = (deg + 22.5) % 360.0;
    if shifted < 0.0 {
        shifted += 360.0;
    }
    let idx = (shifted / 15.0).floor() as usize;
    idx % 24
}

#[pyfunction]
pub fn san_he_water_method(sitting_idx: usize, water_exit_idx: usize) -> Vec<String> {
    let stages = [
        "長生", "沐浴", "冠帶", "臨官", "帝旺", "衰", 
        "病", "死", "墓", "絕", "胎", "養"
    ];
    let diff = (water_exit_idx + 24 - sitting_idx) % 24;
    let stage_idx = diff / 2;
    vec![
        stages[stage_idx].to_string(),
        format!("Sitting: {}", MOUNTAINS_24[sitting_idx]),
        format!("Water Exit: {}", MOUNTAINS_24[water_exit_idx])
    ]
}
