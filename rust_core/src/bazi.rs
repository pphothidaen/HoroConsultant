/*!
 * rust_core/src/bazi.rs
 * Deterministic BaZi Four Pillars, hidden stems, and Five Elements scoring.
 *
 * This module mirrors project/core/bazi_engine.py. Pure calculation kernels
 * compile without default features; PyO3 compatibility wrappers remain behind
 * the `python` feature.
 */

use crate::solar::{calculate_true_solar_time, SolarTimeResult};
use chrono::{Datelike, NaiveDate, NaiveDateTime, Timelike, Utc};
#[cfg(feature = "python")]
use pyo3::prelude::*;
use serde::{Deserialize, Serialize};
#[cfg(feature = "python")]
use std::collections::HashMap;
use std::error::Error;
use std::fmt::{Display, Formatter};

const ELEMENTS: [&str; 5] = ["Wood", "Fire", "Earth", "Metal", "Water"];

#[derive(Clone, Copy)]
struct StemLookup {
    character: &'static str,
    pinyin: &'static str,
    element: &'static str,
    polarity: &'static str,
}

const STEMS: [StemLookup; 10] = [
    StemLookup {
        character: "甲",
        pinyin: "Jiǎ",
        element: "Wood",
        polarity: "Yang",
    },
    StemLookup {
        character: "乙",
        pinyin: "Yǐ",
        element: "Wood",
        polarity: "Yin",
    },
    StemLookup {
        character: "丙",
        pinyin: "Bǐng",
        element: "Fire",
        polarity: "Yang",
    },
    StemLookup {
        character: "丁",
        pinyin: "Dīng",
        element: "Fire",
        polarity: "Yin",
    },
    StemLookup {
        character: "戊",
        pinyin: "Wù",
        element: "Earth",
        polarity: "Yang",
    },
    StemLookup {
        character: "己",
        pinyin: "Jǐ",
        element: "Earth",
        polarity: "Yin",
    },
    StemLookup {
        character: "庚",
        pinyin: "Gēng",
        element: "Metal",
        polarity: "Yang",
    },
    StemLookup {
        character: "辛",
        pinyin: "Xīn",
        element: "Metal",
        polarity: "Yin",
    },
    StemLookup {
        character: "壬",
        pinyin: "Rén",
        element: "Water",
        polarity: "Yang",
    },
    StemLookup {
        character: "癸",
        pinyin: "Guǐ",
        element: "Water",
        polarity: "Yin",
    },
];

#[derive(Clone, Copy)]
struct BranchLookup {
    character: &'static str,
    pinyin: &'static str,
    animal: &'static str,
    element: &'static str,
    polarity: &'static str,
    hour_start: u32,
}

const BRANCHES: [BranchLookup; 12] = [
    BranchLookup {
        character: "子",
        pinyin: "Zǐ",
        animal: "Rat",
        element: "Water",
        polarity: "Yang",
        hour_start: 23,
    },
    BranchLookup {
        character: "丑",
        pinyin: "Chǒu",
        animal: "Ox",
        element: "Earth",
        polarity: "Yin",
        hour_start: 1,
    },
    BranchLookup {
        character: "寅",
        pinyin: "Yín",
        animal: "Tiger",
        element: "Wood",
        polarity: "Yang",
        hour_start: 3,
    },
    BranchLookup {
        character: "卯",
        pinyin: "Mǎo",
        animal: "Rabbit",
        element: "Wood",
        polarity: "Yin",
        hour_start: 5,
    },
    BranchLookup {
        character: "辰",
        pinyin: "Chén",
        animal: "Dragon",
        element: "Earth",
        polarity: "Yang",
        hour_start: 7,
    },
    BranchLookup {
        character: "巳",
        pinyin: "Sì",
        animal: "Snake",
        element: "Fire",
        polarity: "Yin",
        hour_start: 9,
    },
    BranchLookup {
        character: "午",
        pinyin: "Wǔ",
        animal: "Horse",
        element: "Fire",
        polarity: "Yang",
        hour_start: 11,
    },
    BranchLookup {
        character: "未",
        pinyin: "Wèi",
        animal: "Goat",
        element: "Earth",
        polarity: "Yin",
        hour_start: 13,
    },
    BranchLookup {
        character: "申",
        pinyin: "Shēn",
        animal: "Monkey",
        element: "Metal",
        polarity: "Yang",
        hour_start: 15,
    },
    BranchLookup {
        character: "酉",
        pinyin: "Yǒu",
        animal: "Rooster",
        element: "Metal",
        polarity: "Yin",
        hour_start: 17,
    },
    BranchLookup {
        character: "戌",
        pinyin: "Xū",
        animal: "Dog",
        element: "Earth",
        polarity: "Yang",
        hour_start: 19,
    },
    BranchLookup {
        character: "亥",
        pinyin: "Hài",
        animal: "Pig",
        element: "Water",
        polarity: "Yin",
        hour_start: 21,
    },
];

// Hidden Stems (藏干): (stem index, fractional weight).
const HIDDEN_STEMS: [&[(usize, f32)]; 12] = [
    &[(9, 1.0)],
    &[(5, 0.6), (9, 0.3), (7, 0.1)],
    &[(0, 0.6), (2, 0.3), (4, 0.1)],
    &[(1, 1.0)],
    &[(4, 0.6), (1, 0.3), (9, 0.1)],
    &[(2, 0.6), (4, 0.3), (6, 0.1)],
    &[(3, 0.7), (5, 0.3)],
    &[(5, 0.6), (3, 0.3), (1, 0.1)],
    &[(6, 0.6), (8, 0.3), (4, 0.1)],
    &[(7, 1.0)],
    &[(4, 0.6), (7, 0.3), (3, 0.1)],
    &[(8, 0.7), (0, 0.3)],
];

// Rows and columns are Wood, Fire, Earth, Metal, Water.
const SEASONAL_MULTIPLIERS: [[f32; 5]; 5] = [
    [1.5, 1.2, 0.8, 0.6, 1.1],
    [1.1, 1.5, 1.2, 0.7, 0.6],
    [0.8, 1.1, 1.5, 1.2, 0.7],
    [0.7, 0.6, 1.1, 1.5, 1.2],
    [1.2, 0.6, 0.7, 1.1, 1.5],
];

const SOLAR_MONTH_STARTS: [(u32, u32); 12] = [
    (1, 6),
    (2, 4),
    (3, 6),
    (4, 5),
    (5, 6),
    (6, 7),
    (7, 7),
    (8, 8),
    (9, 8),
    (10, 8),
    (11, 7),
    (12, 7),
];

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BaziInput {
    pub year: i32,
    pub month: u32,
    pub day: u32,
    pub hour: u32,
    pub minute: u32,
    pub second: u32,
    pub longitude: f64,
    pub utc_offset_hours: f64,
    #[serde(default)]
    pub unknown_hour: bool,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BaziError(pub String);

impl Display for BaziError {
    fn fmt(&self, formatter: &mut Formatter<'_>) -> std::fmt::Result {
        formatter.write_str(&self.0)
    }
}

impl Error for BaziError {}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct StemData {
    #[serde(rename = "char")]
    pub character: String,
    pub pinyin: String,
    pub element: String,
    pub polarity: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BranchData {
    #[serde(rename = "char")]
    pub character: String,
    pub pinyin: String,
    pub animal: String,
    pub element: String,
    pub polarity: String,
    pub hour_start: u32,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct HiddenStemData {
    pub stem: String,
    pub element: String,
    pub weight: f64,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct PillarData {
    pub label: String,
    pub stem: StemData,
    pub branch: BranchData,
    pub hidden_stems: Vec<HiddenStemData>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Pillars {
    pub year: PillarData,
    pub month: PillarData,
    pub day: PillarData,
    pub hour: Option<PillarData>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct DayMaster {
    pub stem: String,
    pub element: String,
    pub polarity: String,
    pub pinyin: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ElementValues {
    #[serde(rename = "Wood")]
    pub wood: f64,
    #[serde(rename = "Fire")]
    pub fire: f64,
    #[serde(rename = "Earth")]
    pub earth: f64,
    #[serde(rename = "Metal")]
    pub metal: f64,
    #[serde(rename = "Water")]
    pub water: f64,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct FiveElements {
    pub scores: ElementValues,
    pub percentages: ElementValues,
    pub dominant_element: String,
    pub weakest_element: String,
    pub total_raw: f64,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ProbabilisticScenario {
    pub hour_branch: String,
    pub hour_branch_pinyin: String,
    pub animal: String,
    pub hour_window: String,
    pub probability_weight: f64,
    pub hour_pillar: PillarData,
    pub five_elements: FiveElements,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct LegacyElementScores {
    pub wood: f64,
    pub fire: f64,
    pub earth: f64,
    pub metal: f64,
    pub water: f64,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BaziChart {
    pub engine_version: String,
    pub solar_time_info: SolarTimeResult,
    pub day_master: DayMaster,
    pub pillars: Pillars,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub five_elements: Option<FiveElements>,
    pub is_probabilistic: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub probabilistic_matrix: Option<Vec<ProbabilisticScenario>>,
    pub engine_name: String,
    pub system_type: String,
    pub calculation_timestamp: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub element_scores: Option<LegacyElementScores>,
}

fn stem_data(index: usize) -> StemData {
    let stem = STEMS[index % 10];
    StemData {
        character: stem.character.to_string(),
        pinyin: stem.pinyin.to_string(),
        element: stem.element.to_string(),
        polarity: stem.polarity.to_string(),
    }
}

fn branch_data(index: usize) -> BranchData {
    let branch = BRANCHES[index % 12];
    BranchData {
        character: branch.character.to_string(),
        pinyin: branch.pinyin.to_string(),
        animal: branch.animal.to_string(),
        element: branch.element.to_string(),
        polarity: branch.polarity.to_string(),
        hour_start: branch.hour_start,
    }
}

fn pillar_data(stem_index: usize, branch_index: usize, label: &str) -> PillarData {
    let hidden_stems = HIDDEN_STEMS[branch_index % 12]
        .iter()
        .map(|(index, weight)| HiddenStemData {
            stem: STEMS[*index].character.to_string(),
            element: STEMS[*index].element.to_string(),
            weight: round_two(*weight),
        })
        .collect();
    PillarData {
        label: label.to_string(),
        stem: stem_data(stem_index),
        branch: branch_data(branch_index),
        hidden_stems,
    }
}

fn year_stem_branch(year: i32, month: u32, day: u32) -> (usize, usize) {
    let effective_year = year - i32::from(month < 2 || (month == 2 && day < 4));
    (
        (effective_year - 4).rem_euclid(10) as usize,
        (effective_year - 4).rem_euclid(12) as usize,
    )
}

fn month_branch_index(month: u32, day: u32) -> usize {
    for (index, (start_month, start_day)) in SOLAR_MONTH_STARTS.iter().enumerate().rev() {
        if month > *start_month || (month == *start_month && day >= *start_day) {
            return (index + 1) % 12;
        }
    }
    1
}

fn month_stem_branch(year_stem: usize, month: u32, day: u32) -> (usize, usize) {
    let branch = month_branch_index(month, day);
    let tiger_base = [2, 4, 6, 8, 0][year_stem % 5];
    let offset = (branch + 12 - 2) % 12;
    ((tiger_base + offset) % 10, branch)
}

fn day_stem_branch(dt: NaiveDateTime) -> (usize, usize) {
    let jdn = julian_day_number_rust(dt.year(), dt.month() as i32, dt.day() as i32) as i64;
    (
        ((jdn + 9).rem_euclid(10)) as usize,
        ((jdn + 1).rem_euclid(12)) as usize,
    )
}

fn hour_branch_from_tst(hour: u32) -> usize {
    if hour == 23 {
        0
    } else {
        hour.div_ceil(2) as usize
    }
}

fn hour_stem_branch(day_stem: usize, hour: u32) -> (usize, usize) {
    let branch = hour_branch_from_tst(hour);
    let rat_base = [0, 2, 4, 6, 8][day_stem % 5];
    ((rat_base + branch) % 10, branch)
}

fn element_index(element: &str) -> usize {
    ELEMENTS
        .iter()
        .position(|candidate| *candidate == element)
        .unwrap_or(0)
}

fn round_two(value: f32) -> f64 {
    (f64::from(value) * 100.0).round_ties_even() / 100.0
}

fn values(raw: [f64; 5]) -> ElementValues {
    ElementValues {
        wood: raw[0],
        fire: raw[1],
        earth: raw[2],
        metal: raw[3],
        water: raw[4],
    }
}

fn compute_five_elements(
    stem_indices: &[usize],
    branch_indices: &[usize],
    season_element: &str,
) -> FiveElements {
    let mut raw = [0.0_f32; 5];
    for stem in stem_indices {
        raw[(stem % 10) / 2] += 10.0;
    }
    for branch in branch_indices {
        for (stem, weight) in HIDDEN_STEMS[branch % 12] {
            raw[stem / 2] += 15.0 * weight;
        }
    }

    let multiplier = SEASONAL_MULTIPLIERS[element_index(season_element)];
    let mut adjusted = [0.0_f32; 5];
    for index in 0..5 {
        adjusted[index] = raw[index] * multiplier[index];
    }
    let mut total: f32 = adjusted.iter().sum();
    if total < 1e-9 {
        total = 1.0;
    }
    let mut rounded_adjusted = [0.0_f64; 5];
    let mut percentages = [0.0_f64; 5];
    for index in 0..5 {
        percentages[index] = round_two(adjusted[index] / total * 100.0);
        rounded_adjusted[index] = round_two(adjusted[index]);
    }
    let dominant = adjusted
        .iter()
        .enumerate()
        .max_by(|left, right| left.1.total_cmp(right.1).then_with(|| right.0.cmp(&left.0)))
        .map(|(index, _)| index)
        .unwrap_or(0);
    let weakest = adjusted
        .iter()
        .enumerate()
        .min_by(|left, right| left.1.total_cmp(right.1).then_with(|| left.0.cmp(&right.0)))
        .map(|(index, _)| index)
        .unwrap_or(0);

    FiveElements {
        scores: values(rounded_adjusted),
        percentages: values(percentages),
        dominant_element: ELEMENTS[dominant].to_string(),
        weakest_element: ELEMENTS[weakest].to_string(),
        total_raw: round_two(total),
    }
}

fn validate_datetime(input: &BaziInput) -> Result<NaiveDateTime, BaziError> {
    if !(1..=9_999).contains(&input.year) {
        return Err(BaziError("year must be between 1 and 9999".to_string()));
    }
    NaiveDate::from_ymd_opt(input.year, input.month, input.day)
        .and_then(|date| date.and_hms_opt(input.hour, input.minute, input.second))
        .ok_or_else(|| BaziError("invalid Gregorian date or clock time".to_string()))
}

/// Compute a complete BaZi response with the same serialized schema as Python.
pub fn calculate_bazi(input: &BaziInput) -> Result<BaziChart, BaziError> {
    let dt = validate_datetime(input)?;
    let solar_time_info = calculate_true_solar_time(dt, input.longitude, input.utc_offset_hours)
        .map_err(|error| BaziError(error.to_string()))?;
    let tst = NaiveDateTime::parse_from_str(&solar_time_info.tst_datetime, "%Y-%m-%d %H:%M:%S")
        .map_err(|error| BaziError(format!("invalid corrected datetime: {error}")))?;

    let (year_stem, year_branch) = year_stem_branch(tst.year(), tst.month(), tst.day());
    let (month_stem, month_branch) = month_stem_branch(year_stem, tst.month(), tst.day());
    let (day_stem, day_branch) = day_stem_branch(tst);
    let year_pillar = pillar_data(year_stem, year_branch, "Year");
    let month_pillar = pillar_data(month_stem, month_branch, "Month");
    let day_pillar = pillar_data(day_stem, day_branch, "Day");
    let day_lookup = STEMS[day_stem];
    let day_master = DayMaster {
        stem: day_lookup.character.to_string(),
        element: day_lookup.element.to_string(),
        polarity: day_lookup.polarity.to_string(),
        pinyin: day_lookup.pinyin.to_string(),
    };
    let season_element = BRANCHES[month_branch].element;

    let (hour, five_elements, probabilistic_matrix, element_scores) = if input.unknown_hour {
        let scenarios = (0..12)
            .map(|hour_branch| {
                let hour_stem = ([0, 2, 4, 6, 8][day_stem % 5] + hour_branch) % 10;
                let branch = BRANCHES[hour_branch];
                ProbabilisticScenario {
                    hour_branch: branch.character.to_string(),
                    hour_branch_pinyin: branch.pinyin.to_string(),
                    animal: branch.animal.to_string(),
                    hour_window: format!(
                        "{:02}:00–{:02}:00",
                        branch.hour_start,
                        (branch.hour_start + 2) % 24
                    ),
                    probability_weight: 0.083333,
                    hour_pillar: pillar_data(hour_stem, hour_branch, "Hour"),
                    five_elements: compute_five_elements(
                        &[year_stem, month_stem, day_stem, hour_stem],
                        &[year_branch, month_branch, day_branch, hour_branch],
                        season_element,
                    ),
                }
            })
            .collect();
        (None, None, Some(scenarios), None)
    } else {
        let (hour_stem, hour_branch) = hour_stem_branch(day_stem, tst.hour());
        let scores = compute_five_elements(
            &[year_stem, month_stem, day_stem, hour_stem],
            &[year_branch, month_branch, day_branch, hour_branch],
            season_element,
        );
        (
            Some(pillar_data(hour_stem, hour_branch, "Hour")),
            Some(scores),
            None,
            Some(LegacyElementScores {
                wood: 0.0,
                fire: 0.0,
                earth: 0.0,
                metal: 0.0,
                water: 0.0,
            }),
        )
    };

    Ok(BaziChart {
        engine_version: "1.0.0".to_string(),
        solar_time_info,
        day_master,
        pillars: Pillars {
            year: year_pillar,
            month: month_pillar,
            day: day_pillar,
            hour,
        },
        five_elements,
        is_probabilistic: input.unknown_hour,
        probabilistic_matrix,
        engine_name: "BaZi Engine".to_string(),
        system_type: "ming_xue".to_string(),
        calculation_timestamp: Utc::now().format("%Y-%m-%dT%H:%M:%S%.6f+00:00").to_string(),
        element_scores,
    })
}

pub fn julian_day_number_rust(year: i32, month: i32, day: i32) -> f64 {
    let a = (14 - month) / 12;
    let y = year + 4800 - a;
    let m = month + 12 * a - 3;
    let jdn = day + (153 * m + 2) / 5 + 365 * y + y / 4 - y / 100 + y / 400 - 32045;
    jdn as f64
}

/// Compatibility API for callers that provide clock time without location.
pub fn calculate_bazi_stems_branches_rust(
    year: i32,
    month: i32,
    day: i32,
    hour: i32,
) -> (Vec<String>, Vec<String>) {
    let Some(dt) = NaiveDate::from_ymd_opt(year, month as u32, day as u32)
        .and_then(|date| date.and_hms_opt(hour as u32, 0, 0))
    else {
        return (Vec::new(), Vec::new());
    };
    let (year_stem, year_branch) = year_stem_branch(year, month as u32, day as u32);
    let (month_stem, month_branch) = month_stem_branch(year_stem, month as u32, day as u32);
    let (day_stem, day_branch) = day_stem_branch(dt);
    let (hour_stem, hour_branch) = hour_stem_branch(day_stem, hour as u32);
    (
        [year_stem, month_stem, day_stem, hour_stem]
            .into_iter()
            .map(|index| STEMS[index].character.to_string())
            .collect(),
        [year_branch, month_branch, day_branch, hour_branch]
            .into_iter()
            .map(|index| BRANCHES[index].character.to_string())
            .collect(),
    )
}

#[cfg(feature = "python")]
fn stem_index(character: &str) -> Option<usize> {
    STEMS.iter().position(|stem| stem.character == character)
}

#[cfg(feature = "python")]
fn branch_index(character: &str) -> Option<usize> {
    BRANCHES
        .iter()
        .position(|branch| branch.character == character)
}

#[cfg(feature = "python")]
fn compute_element_scores_inner(stems: &[String], branches: &[String]) -> HashMap<String, f32> {
    let stem_indices: Vec<_> = stems.iter().filter_map(|stem| stem_index(stem)).collect();
    let branch_indices: Vec<_> = branches
        .iter()
        .filter_map(|branch| branch_index(branch))
        .collect();
    let season = branch_indices
        .get(1)
        .map(|index| BRANCHES[*index].element)
        .unwrap_or("Wood");
    let scores = compute_five_elements(&stem_indices, &branch_indices, season).percentages;
    HashMap::from([
        ("Wood".to_string(), scores.wood as f32),
        ("Fire".to_string(), scores.fire as f32),
        ("Earth".to_string(), scores.earth as f32),
        ("Metal".to_string(), scores.metal as f32),
        ("Water".to_string(), scores.water as f32),
    ])
}

#[cfg(feature = "python")]
#[pyfunction]
pub fn compute_element_scores(
    py: Python<'_>,
    stems: Vec<String>,
    branches: Vec<String>,
) -> PyResult<HashMap<String, f32>> {
    Ok(py.allow_threads(move || compute_element_scores_inner(&stems, &branches)))
}

#[cfg(feature = "python")]
#[pyfunction]
pub fn compute_probabilistic_matrix(
    py: Python<'_>,
    base_stems: Vec<String>,
    base_branches: Vec<String>,
) -> PyResult<Vec<HashMap<String, f32>>> {
    Ok(py.allow_threads(move || {
        (0..12)
            .map(|hour_branch| {
                let mut stems = base_stems.clone();
                let mut branches = base_branches.clone();
                let day_stem = stems.get(2).and_then(|stem| stem_index(stem)).unwrap_or(0);
                let hour_stem = ([0, 2, 4, 6, 8][day_stem % 5] + hour_branch) % 10;
                stems.push(STEMS[hour_stem].character.to_string());
                branches.push(BRANCHES[hour_branch].character.to_string());
                compute_element_scores_inner(&stems, &branches)
            })
            .collect()
    }))
}

#[cfg(feature = "python")]
#[pyfunction]
pub fn julian_day_number(py: Python<'_>, year: i32, month: i32, day: i32) -> PyResult<f64> {
    Ok(py.allow_threads(move || julian_day_number_rust(year, month, day)))
}
