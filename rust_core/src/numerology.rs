/*!
 * rust_core/src/numerology.rs
 * High-performance Satta-Lek (สัตตเลข 7 ฐาน 4 แถว) & Chaldean Numerology matrix core.
 */

#[cfg(feature = "python")]
use pyo3::prelude::*;
use serde_json::{json, Value};

const SATTA_LEK_HOUSES: [&str; 7] = ["อัตตา", "หินะ", "ธนัง", "ปิตา", "มาตา", "โภคา", "มัชฌิมา"];

/// Build the complete Satta-Lek response schema with overflow-safe modular
/// arithmetic for arbitrary signed JSON integers.
pub fn calculate_satta_lek_chart_rust(
    day_num: i64,
    lunar_month: i64,
    year_zodiac_num: i64,
    calculation_timestamp: &str,
) -> Result<Value, String> {
    let mut matrix = Vec::with_capacity(7);
    for (index, &house_name) in SATTA_LEK_HOUSES.iter().enumerate() {
        let offset = index as i128;
        let row1 = (i128::from(day_num) + offset - 1).rem_euclid(7) as i64 + 1;
        let row2 = (i128::from(lunar_month) + offset - 1).rem_euclid(7) as i64 + 1;
        let row3 = (i128::from(year_zodiac_num) + offset - 1).rem_euclid(7) as i64 + 1;
        matrix.push(json!({
            "house_name": house_name,
            "row1_day": row1,
            "row2_month": row2,
            "row3_year": row3,
            "row4_sum": row1 + row2 + row3,
        }));
    }
    Ok(json!({
        "engine": "SattaLekEngine",
        "day_num": day_num,
        "lunar_month": lunar_month,
        "year_zodiac_num": year_zodiac_num,
        "matrix_7_base": matrix,
        "engine_name": "Numerology & Satta-Lek Engine",
        "system_type": "numerology",
        "calculation_timestamp": calculation_timestamp,
    }))
}

fn chaldean_value(character: char) -> Option<i64> {
    match character {
        'A' | 'I' | 'J' | 'Q' | 'Y' => Some(1),
        'B' | 'K' | 'R' => Some(2),
        'C' | 'G' | 'L' | 'S' => Some(3),
        'D' | 'M' | 'T' => Some(4),
        'E' | 'H' | 'N' | 'X' => Some(5),
        'U' | 'V' | 'W' => Some(6),
        'O' | 'Z' => Some(7),
        'F' | 'P' => Some(8),
        'ก' | 'ฎ' | 'ฒ' | 'ด' | 'ะ' | 'า' | 'ิ' | 'ึ' | 'ุ' | '่' => Some(1),
        'ข' | 'ฌ' | 'ต' | 'บ' | 'ป' | 'ำ' | 'ี' | 'ื' | 'ู' | 'เ' | 'แ' | 'โ' | 'ใ' | 'ไ' | '้' => {
            Some(2)
        }
        'ค' | 'ถ' | 'ผ' | 'ส' | '๊' => Some(3),
        'ฆ' | 'ญ' | 'ฑ' | 'ท' | 'พ' | 'ภ' | 'ร' | 'ั' | '๋' => Some(4),
        'ง' | 'ณ' | 'ธ' | 'น' | 'ม' | 'ห' => Some(5),
        'จ' | 'ล' | 'ว' | 'ฬ' | 'อ' => Some(6),
        'ฉ' | 'ฝ' | 'ฟ' | 'ศ' | 'ษ' => Some(7),
        'ช' | 'ฏ' | 'ย' | '็' => Some(8),
        'ซ' | 'ฐ' | 'ฮ' | '์' => Some(9),
        _ => None,
    }
}

fn number_meaning(root: i64) -> &'static str {
    match root {
        1 => "อาทิตย์ (1) - ความเป็นผู้นำ เกียรติยศ อำนาจ การเปิิดโลก",
        2 => "จันทร์ (2) - เสน่ห์ เมตตา ความอ่อนโยน ความรู้สึก ไวต่ออารมณ์",
        3 => "อังคาร (3) - ความกล้าหาญ ขยัน ลุย ปฏิกิริยาไว การแข่งขัน",
        4 => "พุธ (4) - การสื่อสาร เจรจา วาจาเป็นทรัพย์ ความคิดสร้างสรรค์",
        5 => "พฤหัสบดี (5) - ปัญญา คุณธรรม การเรียนรู้ ความยุติธรรม ผู้ใหญ่เมตตา",
        6 => "ศุกร์ (6) - ความสุข ความรัก ศิลปะ ความอุดมสมบูรณ์ ทรัพย์สิน",
        7 => "เสาร์ (7) - ความอดทน รอบคอบ โครงสร้าง อสังหาริมทรัพย์ ความรับผิดชอบ",
        8 => "ราหู (8) - ความชาญฉลาด พลิกผัน โชคลาภกะทันหัน ความทะเยอทะยาน",
        9 => "เกตุ (9) - สิ่งศักดิ์สิทธิ์ คุ้มครอง ลางสังหรณ์ เทคโนโลยี ทางนวัตกรรม",
        _ => "เลขมงคลสมดุล",
    }
}

/// Score a name, phone number, or license plate using the complete Python
/// Chaldean mapping.
pub fn calculate_numerology_score_rust(text: &str, calculation_timestamp: &str) -> Value {
    let total: i64 = text
        .chars()
        .map(|character| {
            character
                .to_digit(10)
                .map(i64::from)
                .or_else(|| chaldean_value(character))
                .unwrap_or(0)
        })
        .sum();
    let mut root = total;
    while root > 9 {
        root = root
            .to_string()
            .bytes()
            .map(|byte| i64::from(byte - b'0'))
            .sum();
    }
    json!({
        "engine": "ChaldeanNumerologyEngine",
        "input_text": text,
        "total_score": total,
        "reduced_root_digit": root,
        "digit_meaning": number_meaning(root),
        "engine_name": "Numerology & Satta-Lek Engine",
        "system_type": "numerology",
        "calculation_timestamp": calculation_timestamp,
    })
}

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
