/*!
 * rust_core/src/iching.rs
 * High-performance I Ching 64 Hexagrams & Liu Yao matrix core.
 */

#[cfg(feature = "python")]
use pyo3::prelude::*;
use serde_json::{json, Value};

const FIVE_RELATIVES: [&str; 5] = ["父母", "兄弟", "子孫", "妻財", "官鬼"];
const SIX_ANIMALS: [&str; 6] = ["青龍", "朱雀", "勾陳", "騰蛇", "白虎", "玄武"];

fn hexagram_name(bits: &str) -> (&'static str, &'static str) {
    match bits {
        "111111" => ("乾為天", "大吉"),
        "000000" => ("坤為地", "順利"),
        "100010" => ("水雷屯", "宜守"),
        "010001" => ("山水蒙", "啓蒙"),
        "111010" => ("水天需", "等待"),
        "010111" => ("天水訟", "謹慎"),
        "010000" => ("地水師", "律己"),
        "000010" => ("水地比", "親和"),
        "111011" => ("風天小畜", "積蓄"),
        "110111" => ("天澤履", "禮儀"),
        "111000" => ("地天泰", "通達"),
        "000111" => ("天地否", "閉塞"),
        "101111" => ("天火同人", "和諧"),
        "111101" => ("火天大有", "豐盛"),
        _ => ("本卦", "吉"),
    }
}

/// Build the complete I Ching/Liu Yao response without panicking on malformed
/// line arrays.
pub fn calculate_iching_chart_rust(
    day_stem: &str,
    lines: &[i32],
    calculation_timestamp: &str,
) -> Result<Value, String> {
    if lines.len() != 6 {
        return Err("I Ching requires exactly six lines".to_string());
    }
    if let Some(invalid) = lines.iter().find(|&&line| !matches!(line, 6..=9)) {
        return Err(format!("invalid I Ching line value: {invalid}"));
    }
    let mut primary = String::with_capacity(6);
    let mut transformed = String::with_capacity(6);
    for &line in lines {
        if matches!(line, 7 | 9) {
            primary.push('1');
            transformed.push(if line == 9 { '0' } else { '1' });
        } else {
            primary.push('0');
            transformed.push(if line == 6 { '1' } else { '0' });
        }
    }
    let (primary_name, primary_nature) = hexagram_name(&primary);
    let transformed_name = match hexagram_name(&transformed).0 {
        "本卦" => "變卦",
        name => name,
    };
    let start_animal = match day_stem {
        "甲" | "乙" => "青龍",
        "丙" | "丁" => "朱雀",
        "戊" => "勾陳",
        "己" => "騰蛇",
        "庚" | "辛" => "白虎",
        "壬" | "癸" => "玄武",
        _ => "青龍",
    };
    let start_index = SIX_ANIMALS
        .iter()
        .position(|&animal| animal == start_animal)
        .unwrap_or(0);
    let six_lines: Vec<Value> = lines
        .iter()
        .enumerate()
        .map(|(index, &line)| {
            json!({
                "line_number": index + 1,
                "line_value": line,
                "line_type": if matches!(line, 7 | 9) { "陽爻" } else { "陰爻" },
                "is_moving": matches!(line, 6 | 9),
                "relative": FIVE_RELATIVES[index % 5],
                "animal": SIX_ANIMALS[(start_index + index) % 6],
            })
        })
        .collect();
    Ok(json!({
        "engine": "IChingEngine",
        "day_stem": day_stem,
        "raw_lines": lines,
        "primary_hexagram": {
            "binary": primary,
            "name": primary_name,
            "nature": primary_nature,
        },
        "transformed_hexagram": {
            "binary": transformed,
            "name": transformed_name,
        },
        "six_lines": six_lines,
        "engine_name": "I Ching & Liu Yao Engine",
        "system_type": "pu_shi",
        "calculation_timestamp": calculation_timestamp,
    }))
}

pub fn parse_hexagram_trigrams_rust(val: u8) -> (u8, u8) {
    let lower = val & 0b111;
    let upper = (val >> 3) & 0b111;
    (upper, lower)
}

/// Convert 6-bit binary string (e.g. "111111") to Trigrams (Upper, Lower).
#[cfg(feature = "python")]
#[pyfunction]
pub fn parse_hexagram_trigrams(binary_str: &str) -> PyResult<(String, String)> {
    let lower_code = &binary_str[0..3.min(binary_str.len())];
    let upper_code = if binary_str.len() >= 6 {
        &binary_str[3..6]
    } else {
        "000"
    };

    let get_trigram = |code: &str| match code {
        "000" => "坤 (Kun/Earth)",
        "001" => "震 (Zhen/Thunder)",
        "010" => "坎 (Kan/Water)",
        "011" => "兌 (Dui/Lake)",
        "100" => "艮 (Gen/Mountain)",
        "101" => "離 (Li/Fire)",
        "110" => "巽 (Xun/Wind)",
        "111" => "乾 (Qian/Heaven)",
        _ => "坤 (Kun/Earth)",
    };

    Ok((
        get_trigram(upper_code).to_string(),
        get_trigram(lower_code).to_string(),
    ))
}
