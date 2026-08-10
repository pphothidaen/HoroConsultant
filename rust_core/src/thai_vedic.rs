/*!
 * rust_core/src/thai_vedic.rs
 * High-performance Thai & Vedic Astrology calculation core.
 */

#[cfg(feature = "python")]
use pyo3::prelude::*;

#[cfg(feature = "python")]
static ZODIAC_THAI: [&str; 12] = [
    "เมษ", "พฤษภ", "เมถุน", "กรกฎ", "สิงห์", "กันย์",
    "ตุลย์", "พิจิก", "ธนู", "มังกร", "กุมภ์", "มีน"
];

#[cfg(feature = "python")]
static THAKSA_STEPS: [&str; 8] = ["บริวาร", "อายุ", "เดช", "ศรี", "มูละ", "อุตสาหะ", "มนตรี", "กาลกิณี"];
static PLANET_DAYS: [&str; 8] = ["อาทิตย์ (1)", "จันทร์ (2)", "อังคาร (3)", "พุธ (4)", "เสาร์ (7)", "พฤหัสบดี (5)", "ราหู (8)", "ศุกร์ (6)"];

#[cfg(feature = "python")]
static NAKSHATRAS: [&str; 27] = [
    "อัศวินี (Ashwini)", "ภรณี (Bharani)", "กฤตติกา (Krittika)", "โรหิณี (Rohini)",
    "มฤคศิระ (Mrigashira)", "อาร์ทรา (Ardra)", "ปุนัพพสุ (Punarvasu)", "ปุษยะ (Pushya)",
    "อาศเลษา (Ashlesha)", "มาฆะ (Magha)", "บุรพผลคุนี (Purva Phalguni)", "อุตตรผลคุนี (Uttara Phalguni)",
    "หัสตะ (Hasta)", "จิตรา (Chitra)", "สวาตี (Swati)", "วิศาขา (Vishakha)",
    "อนุราธะ (Anuradha)", "เชษฐา (Jyeshtha)", "มูละ (Mula)", "บุรพษาฒ (Purva Ashadha)",
    "อุตตราษาฒ (Uttara Ashadha)", "ศรวณะ (Shravana)", "ธนิษฐา (Dhanishta)", "ศตภิษัจ (Shatabhisha)",
    "บุรพภัทรบท (Purva Bhadrapada)", "อุตตรภัทรบท (Uttara Bhadrapada)", "เรวดี (Revati)"
];

pub fn calculate_thai_lagna_rust(
    _year: i32,
    month: i32,
    _day: i32,
    hour: i32,
    _minute: i32,
) -> (f64, usize) {
    let sun_house_idx = (month - 4).rem_euclid(12) as usize;
    let hour_offset = ((hour - 6).div_euclid(2)).rem_euclid(12) as usize;
    let lagna_idx = (sun_house_idx + hour_offset) % 12;
    let deg = (lagna_idx as f64 * 30.0) + 15.0;
    (deg, lagna_idx)
}

pub fn calculate_thaksa_map_rust(day: i32) -> String {
    let day_idx = day as usize % 8;
    PLANET_DAYS[day_idx].to_string()
}

/// Calculate Lagna house index and Zodiac sign name.
#[cfg(feature = "python")]
#[pyfunction]
pub fn calculate_thai_lagna(birth_hour: i32, birth_month: i32) -> PyResult<(String, usize)> {
    let sun_house_idx = (birth_month - 4).rem_euclid(12) as usize;
    let hour_offset = ((birth_hour - 6).div_euclid(2)).rem_euclid(12) as usize;
    let lagna_idx = (sun_house_idx + hour_offset) % 12;
    Ok((ZODIAC_THAI[lagna_idx].to_string(), lagna_idx))
}

/// Calculate Maha Thaksa planet mapping.
#[cfg(feature = "python")]
#[pyfunction]
pub fn calculate_thaksa_map(day_of_week: usize) -> PyResult<Vec<(String, String)>> {
    let start_planet_idx = day_of_week % 8;
    let mut map = Vec::with_capacity(8);
    for (i, step) in THAKSA_STEPS.iter().enumerate() {
        let planet = PLANET_DAYS[(start_planet_idx + i) % 8];
        map.push((step.to_string(), planet.to_string()));
    }
    Ok(map)
}

/// Calculate 27 Nakshatra name, index, and pada.
#[cfg(feature = "python")]
#[pyfunction]
pub fn calculate_nakshatra_pada(moon_degree: f64) -> PyResult<(String, usize, usize)> {
    let nak_span = 13.333333333333334;
    let nak_idx = ((moon_degree / nak_span).floor() as usize) % 27;
    let rem_deg = moon_degree % nak_span;
    let pada = ((rem_deg / 3.3333333333333335).floor() as usize + 1).min(4);
    Ok((NAKSHATRAS[nak_idx].to_string(), nak_idx + 1, pada))
}
