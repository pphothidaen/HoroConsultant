use chrono::NaiveDate;
use rust_core::bazi::{calculate_bazi, BaziInput};
use rust_core::solar::calculate_true_solar_time;
use serde_json::{json, Value};
use std::io::{BufRead, BufReader, Write};
use std::process::{Command, Stdio};
use std::time::Instant;

#[allow(clippy::too_many_arguments)]
fn input(
    year: i32,
    month: u32,
    day: u32,
    hour: u32,
    minute: u32,
    second: u32,
    longitude: f64,
    utc_offset_hours: f64,
    unknown_hour: bool,
) -> BaziInput {
    BaziInput {
        year,
        month,
        day,
        hour,
        minute,
        second,
        longitude,
        utc_offset_hours,
        unknown_hour,
    }
}

#[test]
fn bangkok_chart_matches_literal_python_oracle() {
    // Break caught: a fixed/default pillar or non-seasonal score reaches the API.
    let chart = calculate_bazi(&input(1990, 5, 15, 14, 30, 0, 100.493, 7.0, false))
        .expect("valid Bangkok chart");
    let actual = serde_json::to_value(chart).expect("serializable chart");

    assert_eq!(
        actual["solar_time_info"],
        json!({
            "input_datetime": "1990-05-15 14:30:00",
            "longitude": 100.493,
            "utc_offset_hours": 7.0,
            "standard_meridian": 105.0,
            "longitude_offset_minutes": -18.028,
            "eot_minutes": 3.9239,
            "lmt_datetime": "1990-05-15 14:11:58",
            "tst_datetime": "1990-05-15 14:15:53",
            "tst_hour": 14,
            "tst_minute": 15,
            "tst_second": 53
        })
    );
    assert_json_close(
        &compact_pillars(&actual["pillars"]),
        &json!({
            "year": {
                "label": "Year",
                "stem": {"char": "庚", "pinyin": "Gēng", "element": "Metal", "polarity": "Yang"},
                "branch": {"char": "午", "pinyin": "Wǔ", "animal": "Horse", "element": "Fire", "polarity": "Yang", "hour_start": 11},
                "hidden_stems": [
                    {"stem": "丁", "element": "Fire", "weight": 0.7},
                    {"stem": "己", "element": "Earth", "weight": 0.3}
                ]
            },
            "month": {
                "label": "Month",
                "stem": {"char": "辛", "pinyin": "Xīn", "element": "Metal", "polarity": "Yin"},
                "branch": {"char": "巳", "pinyin": "Sì", "animal": "Snake", "element": "Fire", "polarity": "Yin", "hour_start": 9},
                "hidden_stems": [
                    {"stem": "丙", "element": "Fire", "weight": 0.6},
                    {"stem": "戊", "element": "Earth", "weight": 0.3},
                    {"stem": "庚", "element": "Metal", "weight": 0.1}
                ]
            },
            "day": {
                "label": "Day",
                "stem": {"char": "庚", "pinyin": "Gēng", "element": "Metal", "polarity": "Yang"},
                "branch": {"char": "辰", "pinyin": "Chén", "animal": "Dragon", "element": "Earth", "polarity": "Yang", "hour_start": 7},
                "hidden_stems": [
                    {"stem": "戊", "element": "Earth", "weight": 0.6},
                    {"stem": "乙", "element": "Wood", "weight": 0.3},
                    {"stem": "癸", "element": "Water", "weight": 0.1}
                ]
            },
            "hour": {
                "label": "Hour",
                "stem": {"char": "癸", "pinyin": "Guǐ", "element": "Water", "polarity": "Yin"},
                "branch": {"char": "未", "pinyin": "Wèi", "animal": "Goat", "element": "Earth", "polarity": "Yin", "hour_start": 13},
                "hidden_stems": [
                    {"stem": "己", "element": "Earth", "weight": 0.6},
                    {"stem": "丁", "element": "Fire", "weight": 0.3},
                    {"stem": "乙", "element": "Wood", "weight": 0.1}
                ]
            }
        }),
        "$.pillars",
    );
    assert_json_close(
        &actual["five_elements"],
        &json!({
            "scores": {"Wood": 6.6, "Fire": 36.0, "Earth": 32.4, "Metal": 22.05, "Water": 6.9},
            "percentages": {"Wood": 6.35, "Fire": 34.63, "Earth": 31.17, "Metal": 21.21, "Water": 6.64},
            "dominant_element": "Fire",
            "weakest_element": "Wood",
            "total_raw": 103.95
        }),
        "$.five_elements",
    );
    assert_eq!(
        actual["day_master"],
        json!({"stem": "庚", "element": "Metal", "polarity": "Yang", "pinyin": "Gēng"})
    );
    assert_eq!(actual["engine_version"], "1.0.0");
    assert_eq!(actual["engine_name"], "BaZi Engine");
    assert_eq!(actual["system_type"], "ming_xue");
    assert_eq!(actual["is_probabilistic"], false);
    assert!(actual["calculation_timestamp"].as_str().is_some());
}

#[test]
fn true_solar_time_crosses_date_and_uses_fractional_leap_year_eot() {
    // Break caught: integer-day/365-day EoT or missing longitude correction.
    let dt = NaiveDate::from_ymd_opt(2026, 2, 3)
        .unwrap()
        .and_hms_opt(23, 58, 30)
        .unwrap();
    let result = calculate_true_solar_time(dt, 120.0, 7.0).expect("valid solar time");
    assert_eq!(result.standard_meridian, 105.0);
    assert_eq!(result.longitude_offset_minutes, 60.0);
    assert_eq!(result.eot_minutes, -13.614);
    assert_eq!(result.lmt_datetime, "2026-02-04 00:58:30");
    assert_eq!(result.tst_datetime, "2026-02-04 00:44:53");

    let leap_dt = NaiveDate::from_ymd_opt(2000, 2, 29)
        .unwrap()
        .and_hms_opt(23, 30, 0)
        .unwrap();
    let leap = calculate_true_solar_time(leap_dt, 180.0, 14.0).expect("valid leap date");
    assert_eq!(leap.eot_minutes, -12.7579);
    assert_eq!(leap.tst_datetime, "2000-02-29 21:17:14");
}

#[test]
fn li_chun_and_true_solar_date_rollover_change_all_affected_pillars() {
    // Break caught: pillars use input clock date rather than the corrected TST date.
    let before =
        calculate_bazi(&input(2026, 2, 4, 0, 0, 0, 105.0, 7.0, false)).expect("valid chart");
    let after =
        calculate_bazi(&input(2026, 2, 4, 12, 0, 0, 105.0, 7.0, false)).expect("valid chart");
    let rollover =
        calculate_bazi(&input(2026, 2, 3, 23, 58, 30, 120.0, 7.0, false)).expect("valid chart");

    assert_eq!(before.pillars.year.stem.character, "乙");
    assert_eq!(before.pillars.year.branch.character, "巳");
    assert_eq!(before.pillars.month.branch.character, "丑");
    assert_eq!(before.pillars.day.stem.character, "戊");
    assert_eq!(before.pillars.hour.as_ref().unwrap().branch.character, "子");

    assert_eq!(after.pillars.year.stem.character, "丙");
    assert_eq!(after.pillars.year.branch.character, "午");
    assert_eq!(after.pillars.month.branch.character, "寅");
    assert_eq!(after.pillars.day.stem.character, "己");
    assert_eq!(after.pillars.hour.as_ref().unwrap().branch.character, "午");

    assert_eq!(rollover.solar_time_info.tst_datetime, "2026-02-04 00:44:53");
    assert_eq!(rollover.pillars.day.stem.character, "己");
    assert_eq!(rollover.pillars.hour.as_ref().unwrap().stem.character, "甲");
    assert_eq!(
        rollover.pillars.hour.as_ref().unwrap().branch.character,
        "子"
    );
}

#[test]
fn singapore_and_timezone_extremes_match_literal_pillars() {
    // Break caught: standard meridian or negative/extreme timezone math is omitted.
    let singapore = calculate_bazi(&input(2000, 1, 1, 8, 0, 0, 103.82, 8.0, false))
        .expect("valid Singapore chart");
    assert_eq!(singapore.solar_time_info.standard_meridian, 120.0);
    assert_eq!(
        singapore.solar_time_info.tst_datetime,
        "2000-01-01 06:52:13"
    );
    assert_eq!(singapore.pillars.year.stem.character, "己");
    assert_eq!(singapore.pillars.month.branch.character, "丑");
    assert_eq!(singapore.pillars.day.stem.character, "戊");
    assert_eq!(
        singapore.pillars.hour.as_ref().unwrap().branch.character,
        "卯"
    );
    assert_eq!(
        singapore.five_elements.as_ref().unwrap().dominant_element,
        "Earth"
    );

    let extreme = calculate_bazi(&input(2024, 12, 31, 23, 59, 59, -180.0, -12.0, false))
        .expect("valid date-line chart");
    assert_eq!(extreme.solar_time_info.standard_meridian, -180.0);
    assert_eq!(extreme.solar_time_info.tst_datetime, "2024-12-31 23:57:04");
    assert_eq!(
        extreme.pillars.hour.as_ref().unwrap().branch.character,
        "子"
    );
}

#[test]
fn unknown_hour_matches_literal_python_scenario_matrix() {
    // Break caught: unknown-hour mode returns a fixed hour or incomplete scenarios.
    let chart = calculate_bazi(&input(1990, 11, 7, 0, 5, 0, 100.493, 7.0, true))
        .expect("valid unknown-hour chart");
    assert!(chart.is_probabilistic);
    assert!(chart.pillars.hour.is_none());
    assert!(chart.five_elements.is_none());
    assert!(chart.element_scores.is_none());
    let scenarios = chart.probabilistic_matrix.expect("scenario matrix");
    assert_eq!(scenarios.len(), 12);
    assert_eq!(scenarios[0].hour_branch, "子");
    assert_eq!(scenarios[0].hour_window, "23:00–01:00");
    assert_eq!(scenarios[0].probability_weight, 0.083333);
    assert_eq!(scenarios[0].hour_pillar.stem.character, "戊");
    assert_eq!(scenarios[0].five_elements.scores.water, 60.75);
    assert_eq!(scenarios[0].five_elements.dominant_element, "Water");
    assert_eq!(scenarios[11].hour_branch, "亥");
    assert_eq!(scenarios[11].hour_window, "21:00–23:00");
    assert_eq!(scenarios[11].hour_pillar.stem.character, "己");
    assert_eq!(scenarios[11].five_elements.percentages.water, 51.8);
    let total: f64 = scenarios
        .iter()
        .map(|scenario| scenario.probability_weight)
        .sum();
    assert!((total - 0.999996).abs() <= 1e-9);
}

#[test]
fn invalid_inputs_return_errors_without_panicking() {
    // Break caught: malformed dates/coordinates panic or silently normalize.
    let invalid = [
        input(2023, 2, 29, 0, 0, 0, 0.0, 0.0, false),
        input(2024, 13, 1, 0, 0, 0, 0.0, 0.0, false),
        input(2024, 1, 1, 24, 0, 0, 0.0, 0.0, false),
        input(2024, 1, 1, 0, 60, 0, 0.0, 0.0, false),
        input(2024, 1, 1, 0, 0, 60, 0.0, 0.0, false),
        input(2024, 1, 1, 0, 0, 0, 180.0001, 0.0, false),
        input(2024, 1, 1, 0, 0, 0, 0.0, 14.0001, false),
        input(2024, 1, 1, 0, 0, 0, f64::NAN, 0.0, false),
    ];
    for candidate in invalid {
        let outcome = std::panic::catch_unwind(|| calculate_bazi(&candidate));
        assert!(outcome.is_ok(), "invalid input panicked: {candidate:?}");
        assert!(
            outcome.unwrap().is_err(),
            "invalid input was accepted: {candidate:?}"
        );
    }
}

fn assert_json_close(actual: &Value, expected: &Value, path: &str) {
    match (actual, expected) {
        (Value::Number(a), Value::Number(e)) if a.is_f64() || e.is_f64() => {
            let delta = (a.as_f64().unwrap() - e.as_f64().unwrap()).abs();
            assert!(delta <= 1e-6, "float mismatch at {path}: {a} != {e}");
        }
        (Value::Array(a), Value::Array(e)) => {
            assert_eq!(a.len(), e.len(), "array length mismatch at {path}");
            for (index, (av, ev)) in a.iter().zip(e).enumerate() {
                assert_json_close(av, ev, &format!("{path}[{index}]"));
            }
        }
        (Value::Object(a), Value::Object(e)) => {
            assert_eq!(a.len(), e.len(), "object size mismatch at {path}");
            for (key, ev) in e {
                let next = format!("{path}.{key}");
                assert_json_close(
                    a.get(key).unwrap_or_else(|| panic!("missing {next}")),
                    ev,
                    &next,
                );
            }
        }
        _ => assert_eq!(actual, expected, "value mismatch at {path}"),
    }
}

fn compact_pillars(value: &Value) -> Value {
    let mut compact = value.clone();
    for pillar_key in ["year", "month", "day", "hour"] {
        if let Some(pillar) = compact.get_mut(pillar_key).and_then(Value::as_object_mut) {
            pillar.remove("ten_god");
            pillar.remove("ten_god_info");
            pillar.remove("pillar_phase");
            pillar.remove("stars");
            if let Some(hidden_stems) = pillar.get_mut("hidden_stems").and_then(Value::as_array_mut)
            {
                for hidden_stem in hidden_stems {
                    if let Some(hidden_stem_object) = hidden_stem.as_object_mut() {
                        hidden_stem_object.remove("ten_god");
                    }
                }
            }
        }
    }
    compact
}

#[test]
fn one_hundred_thousand_invalid_inputs_never_panic_or_succeed() {
    // Break caught: broad malformed input reaches unchecked calendar arithmetic.
    let mut state = 0x5EED_BA21_2026_u64;
    for index in 0..100_000_u64 {
        state = state
            .wrapping_mul(6_364_136_223_846_793_005)
            .wrapping_add(1);
        let mut candidate = input(2024, 1, 1, 12, 30, 30, 0.0, 0.0, index % 2 == 0);
        match index % 10 {
            0 => candidate.month = 13 + (state % 1_000) as u32,
            1 => candidate.day = 32 + (state % 1_000) as u32,
            2 => candidate.hour = 24 + (state % 1_000) as u32,
            3 => candidate.minute = 60 + (state % 1_000) as u32,
            4 => candidate.second = 60 + (state % 1_000) as u32,
            5 => {
                candidate.year = if state & 1 == 0 {
                    0
                } else {
                    10_000 + (state % 10_000) as i32
                }
            }
            6 => candidate.longitude = 180.000001 + (state % 1_000) as f64,
            7 => candidate.utc_offset_hours = 14.000001 + (state % 1_000) as f64,
            8 => candidate.longitude = f64::NAN,
            _ => candidate.utc_offset_hours = f64::INFINITY,
        }
        let outcome = std::panic::catch_unwind(|| calculate_bazi(&candidate));
        assert!(outcome.is_ok(), "fuzz case {index} panicked");
        assert!(outcome.unwrap().is_err(), "fuzz case {index} was accepted");
    }
}

fn project_root() -> std::path::PathBuf {
    std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .expect("rust_core has project parent")
        .to_path_buf()
}

fn input_from_json(value: &Value) -> BaziInput {
    serde_json::from_value(value.clone()).expect("oracle emitted a valid BaziInput")
}

#[test]
#[ignore = "explicit deterministic 10,000-case Python/Rust parity gate"]
fn ten_thousand_cases_match_python_oracle() {
    let root = project_root();
    let mut child = Command::new("python3")
        .arg("rust_core/tests/python_bazi_oracle.py")
        .arg("--count")
        .arg("10000")
        .arg("--seed")
        .arg("3122737190")
        .current_dir(&root)
        .env("HORO_ALLOW_PYTHON_FALLBACK", "1")
        .stdout(Stdio::piped())
        .spawn()
        .expect("start Python oracle");
    let stdout = child.stdout.take().expect("captured oracle stdout");
    let mut compared = 0_usize;
    for line in BufReader::new(stdout).lines() {
        let record: Value =
            serde_json::from_str(&line.expect("read oracle line")).expect("parse oracle JSON");
        let rust_input = input_from_json(&record["input"]);
        let rust_chart = calculate_bazi(&rust_input).expect("oracle case is valid");
        let mut actual = serde_json::to_value(rust_chart).expect("serialize Rust chart");
        actual
            .as_object_mut()
            .expect("chart object")
            .remove("calculation_timestamp");
        assert_json_close(&actual, &record["chart"], &format!("$[{compared}]"));
        compared += 1;
    }
    let status = child.wait().expect("wait for Python oracle");
    assert!(status.success(), "Python oracle failed: {status}");
    assert_eq!(compared, 10_000);
}

fn percentile_95(samples: &mut [u128]) -> u128 {
    samples.sort_unstable();
    samples[(samples.len() - 1) * 95 / 100]
}

#[test]
#[ignore = "explicit complete-calculation ROI benchmark"]
fn benchmark_complete_calculation_reports_roi_gates() {
    const COUNT: usize = 2_000;
    let root = project_root();
    let requests: Vec<_> = (0..COUNT)
        .map(|index| {
            let day = 1 + (index % 28) as u32;
            serde_json::to_string(&input(
                1901 + (index % 199) as i32,
                1 + (index % 12) as u32,
                day,
                (index % 24) as u32,
                (index % 60) as u32,
                ((index * 17) % 60) as u32,
                -180.0 + ((index * 1_000_003) % 360_000_001) as f64 / 1_000_000.0,
                [-12.0, -9.5, -5.0, 0.0, 5.5, 7.0, 8.0, 9.5, 14.0][index % 9],
                index % 97 == 0,
            ))
            .unwrap()
        })
        .collect();
    let mut python_child = Command::new("python3")
        .arg("rust_core/tests/python_bazi_oracle.py")
        .arg("--benchmark")
        .arg("--count")
        .arg(COUNT.to_string())
        .current_dir(&root)
        .env("HORO_ALLOW_PYTHON_FALLBACK", "1")
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .spawn()
        .expect("start Python benchmark");
    {
        let stdin = python_child.stdin.as_mut().expect("Python benchmark stdin");
        for payload in &requests {
            writeln!(stdin, "{payload}").expect("write benchmark request");
        }
    }
    drop(python_child.stdin.take());
    let output = python_child
        .wait_with_output()
        .expect("wait for Python benchmark");
    assert!(output.status.success(), "Python benchmark failed");
    let python: Value = serde_json::from_slice(&output.stdout).expect("Python benchmark JSON");

    for payload in requests.iter().take(20) {
        let request: BaziInput = serde_json::from_str(payload).unwrap();
        let chart = calculate_bazi(&request).unwrap();
        let _ = serde_json::to_vec(&chart).unwrap();
    }

    let cpu_start = process_cpu_time_ns();
    let mut wall_samples = Vec::with_capacity(COUNT);
    for payload in &requests {
        let start = Instant::now();
        let request: BaziInput = serde_json::from_str(payload).unwrap();
        let chart = calculate_bazi(&request).unwrap();
        let _ = serde_json::to_vec(&chart).unwrap();
        wall_samples.push(start.elapsed().as_nanos());
    }
    let rust_cpu_per_request = (process_cpu_time_ns() - cpu_start) as f64 / COUNT as f64;
    let rust_p95 = percentile_95(&mut wall_samples) as f64;
    let python_p95 = python["p95_ns"].as_f64().unwrap();
    let python_cpu = python["cpu_per_request_ns"].as_f64().unwrap();
    let p95_improvement = 1.0 - rust_p95 / python_p95;
    let cpu_reduction = 1.0 - rust_cpu_per_request / python_cpu;
    let decision = if p95_improvement >= 0.20 && cpu_reduction >= 0.30 {
        "QUALIFIED"
    } else {
        "PARKED"
    };
    println!(
        "[INFO] BAZI_ROI decision={decision} rust_p95_ns={rust_p95:.0} python_p95_ns={python_p95:.0} p95_improvement={:.2}% rust_cpu_per_request_ns={rust_cpu_per_request:.0} python_cpu_per_request_ns={python_cpu:.0} cpu_reduction={:.2}%",
        p95_improvement * 100.0,
        cpu_reduction * 100.0,
    );
    assert_eq!(
        decision, "QUALIFIED",
        "PARKED: complete request work missed one or both ROI gates"
    );
}

#[cfg(any(target_os = "linux", target_os = "macos"))]
fn process_cpu_time_ns() -> u128 {
    #[repr(C)]
    struct Timespec {
        seconds: i64,
        nanoseconds: i64,
    }
    unsafe extern "C" {
        fn clock_gettime(clock_id: i32, time: *mut Timespec) -> i32;
    }
    #[cfg(target_os = "linux")]
    const CLOCK_PROCESS_CPUTIME_ID: i32 = 2;
    #[cfg(target_os = "macos")]
    const CLOCK_PROCESS_CPUTIME_ID: i32 = 12;
    let mut time = Timespec {
        seconds: 0,
        nanoseconds: 0,
    };
    // SAFETY: clock_gettime writes one initialized Timespec to a valid pointer.
    let status = unsafe { clock_gettime(CLOCK_PROCESS_CPUTIME_ID, &mut time) };
    assert_eq!(status, 0, "clock_gettime failed");
    time.seconds as u128 * 1_000_000_000 + time.nanoseconds as u128
}

#[cfg(not(any(target_os = "linux", target_os = "macos")))]
fn process_cpu_time_ns() -> u128 {
    Instant::now().elapsed().as_nanos()
}
