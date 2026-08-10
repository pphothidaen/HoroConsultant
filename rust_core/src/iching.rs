/*!
 * rust_core/src/iching.rs
 * High-performance I Ching 64 Hexagrams & Liu Yao matrix core.
 */

#[cfg(feature = "python")]
use pyo3::prelude::*;

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
    let upper_code = if binary_str.len() >= 6 { &binary_str[3..6] } else { "000" };

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

    Ok((get_trigram(upper_code).to_string(), get_trigram(lower_code).to_string()))
}
