/*!
 * rust_core/src/svg.rs
 * High-Performance Rust SVG Vector Chart Rendering Engine.
 * Generates standalone, pixel-perfect SVG charts for BaZi 4 Pillars, Zodiac Wheels, and Metaphysical Grids.
 */

#[cfg(feature = "python")]
use pyo3::prelude::*;
use serde_json::Value;

static ELEMENT_COLORS: &[(&str, &str)] = &[
    ("Wood", "#10b981"),
    ("Fire", "#ef4444"),
    ("Earth", "#d97706"),
    ("Metal", "#38bdf8"),
    ("Water", "#8b5cf6"),
];

fn string_at<'a>(chart: &'a Value, pointer: &str) -> &'a str {
    chart.pointer(pointer).and_then(Value::as_str).unwrap_or("")
}

fn number_at(chart: &Value, pointer: &str) -> f64 {
    chart
        .pointer(pointer)
        .and_then(Value::as_f64)
        .unwrap_or(0.0)
}

fn element_color(element: &str) -> &'static str {
    ELEMENT_COLORS
        .iter()
        .find_map(|&(name, color)| (name == element).then_some(color))
        .unwrap_or("#ffffff")
}

/// Render a complete BaZi chart without depending on PyO3.
///
/// The gateway can pass the same serialized chart object returned by the
/// calculation engine.  Keeping the chart as `serde_json::Value` makes the
/// renderer a direct wire-contract consumer and prevents the old lossy
/// title/total-only bridge.
pub fn render_bazi_svg(chart: &Value, title: &str) -> String {
    let day_master_stem = string_at(chart, "/day_master/stem");
    let day_master_element = string_at(chart, "/day_master/element");
    let day_master_polarity = string_at(chart, "/day_master/polarity");
    let tst = string_at(chart, "/solar_time_info/tst_datetime");
    let mut svg = String::with_capacity(8192);

    svg.push_str(r##"<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" width="100%" height="100%">"##);
    svg.push_str(r##"<defs><linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#0a0c16"/><stop offset="100%" stop-color="#12182b"/></linearGradient><filter id="glow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="4" result="blur"/><feComposite in="SourceGraphic" in2="blur" operator="over"/></filter></defs>"##);
    svg.push_str(r##"<rect width="800" height="600" rx="16" fill="url(#bgGrad)" stroke="#334155" stroke-width="2"/>"##);
    svg.push_str(&format!(r##"<text x="400" y="45" font-family="Prompt, sans-serif" font-size="22" font-weight="bold" fill="#fbbf24" text-anchor="middle" filter="url(#glow)">☯ {title}</text>"##));
    svg.push_str(&format!(r##"<text x="400" y="75" font-family="Prompt, sans-serif" font-size="13" fill="#94a3b8" text-anchor="middle">True Solar Time (TST): {tst} | Day Master: {day_master_stem} ({day_master_element} {day_master_polarity})</text>"##));
    svg.push_str(r##"<g transform="translate(60, 100)">"##);

    let pillars = [
        ("hour", "เสายาม"),
        ("day", "เสาวัน"),
        ("month", "เสาเดือน"),
        ("year", "เสาปี"),
    ];
    for (index, (key, label)) in pillars.iter().enumerate() {
        let x = index * 160;
        let stem_char = string_at(chart, &format!("/pillars/{key}/stem/char"));
        let stem_pinyin = string_at(chart, &format!("/pillars/{key}/stem/pinyin"));
        let stem_element = string_at(chart, &format!("/pillars/{key}/stem/element"));
        let branch_char = string_at(chart, &format!("/pillars/{key}/branch/char"));
        let branch_pinyin = string_at(chart, &format!("/pillars/{key}/branch/pinyin"));
        let branch_animal = string_at(chart, &format!("/pillars/{key}/branch/animal"));
        let branch_element = string_at(chart, &format!("/pillars/{key}/branch/element"));
        let stem_color = element_color(stem_element);
        let branch_color = element_color(branch_element);

        svg.push_str(&format!(r##"<rect x="{}" y="10" width="140" height="320" rx="12" fill="#1e293b" fill-opacity="0.6" stroke="#475569" stroke-width="1.5"/>"##, x + 10));
        svg.push_str(&format!(r##"<text x="{}" y="35" font-family="Prompt, sans-serif" font-size="14" font-weight="bold" fill="#94a3b8" text-anchor="middle">{label}</text>"##, x + 80));
        svg.push_str(&format!(r##"<rect x="{}" y="50" width="110" height="110" rx="10" fill="{stem_color}" fill-opacity="0.15" stroke="{stem_color}" stroke-width="2"/>"##, x + 25));
        svg.push_str(&format!(r##"<text x="{}" y="115" font-family="sans-serif" font-size="46" font-weight="bold" fill="{stem_color}" text-anchor="middle">{stem_char}</text>"##, x + 80));
        svg.push_str(&format!(r##"<text x="{}" y="145" font-family="Prompt, sans-serif" font-size="12" fill="#e2e8f0" text-anchor="middle">{stem_pinyin} ({stem_element})</text>"##, x + 80));
        svg.push_str(&format!(r##"<rect x="{}" y="180" width="110" height="110" rx="10" fill="{branch_color}" fill-opacity="0.15" stroke="{branch_color}" stroke-width="2"/>"##, x + 25));
        svg.push_str(&format!(r##"<text x="{}" y="245" font-family="sans-serif" font-size="46" font-weight="bold" fill="{branch_color}" text-anchor="middle">{branch_char}</text>"##, x + 80));
        svg.push_str(&format!(r##"<text x="{}" y="275" font-family="Prompt, sans-serif" font-size="12" fill="#e2e8f0" text-anchor="middle">{branch_pinyin} ({branch_animal})</text>"##, x + 80));
    }
    svg.push_str("</g>");
    svg.push_str(r##"<g transform="translate(60, 450)"><text x="0" y="0" font-family="Prompt, sans-serif" font-size="15" font-weight="bold" fill="#fbbf24">⚖️ สัดส่วนสมดุล 5 ธาตุ (Five Elements Harmony)</text>"##);
    for (index, &(element, color)) in ELEMENT_COLORS.iter().enumerate() {
        let percentage = number_at(chart, &format!("/five_elements/percentages/{element}"));
        let x = index * 135;
        let width = (percentage / 100.0 * 120.0) as i32;
        svg.push_str(&format!(r##"<text x="{x}" y="28" font-family="Prompt, sans-serif" font-size="12" fill="{color}">{element}: {percentage:.1}%</text><rect x="{x}" y="35" width="120" height="10" rx="5" fill="#334155"/><rect x="{x}" y="35" width="{width}" height="10" rx="5" fill="{color}"/>"##));
    }
    svg.push_str("</g></svg>");
    svg
}

/// Render all supplied Zi Wei palaces, including stars and Si Hua mutators.
pub fn render_ziwei_svg(chart: &Value, title: &str) -> String {
    let bureau = string_at(chart, "/five_element_bureau");
    let ming_branch = string_at(chart, "/ming_gong_branch");
    let shen_branch = string_at(chart, "/shen_gong_branch");
    let mut svg = String::with_capacity(8192);
    svg.push_str(r##"<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 800" width="100%" height="100%"><rect width="800" height="800" rx="16" fill="#0c0718" stroke="#a855f7" stroke-width="2"/>"##);
    svg.push_str(&format!(r##"<text x="400" y="45" font-family="Prompt, sans-serif" font-size="22" font-weight="bold" fill="#c084fc" text-anchor="middle">🔮 {title}</text><text x="400" y="75" font-family="Prompt, sans-serif" font-size="13" fill="#e9d5ff" text-anchor="middle">五行局: {bureau} | 命宮: {ming_branch} | 身宮: {shen_branch}</text>"##));
    svg.push_str(r##"<rect x="250" y="250" width="300" height="300" rx="12" fill="#180e29" stroke="#9333ea" stroke-width="2"/><text x="400" y="380" font-family="sans-serif" font-size="36" font-weight="bold" fill="#c084fc" text-anchor="middle">紫微斗數</text><text x="400" y="420" font-family="Prompt, sans-serif" font-size="14" fill="#a855f7" text-anchor="middle">Computational Metaphysics Engine</text><g transform="translate(40, 100)">"##);

    let grid_coordinates = [
        (3, 0),
        (2, 0),
        (1, 0),
        (0, 0),
        (0, 1),
        (0, 2),
        (0, 3),
        (1, 3),
        (2, 3),
        (3, 3),
        (3, 2),
        (3, 1),
    ];
    if let Some(palaces) = chart.get("palaces").and_then(Value::as_array) {
        for (index, palace) in palaces.iter().take(12).enumerate() {
            let (column, row) = grid_coordinates[index];
            let x = column * 180;
            let y = row * 160;
            let is_ming = palace
                .get("is_ming_gong")
                .and_then(Value::as_bool)
                .unwrap_or(false);
            let is_shen = palace
                .get("is_shen_gong")
                .and_then(Value::as_bool)
                .unwrap_or(false);
            let stroke = if is_ming {
                "#eab308"
            } else if is_shen {
                "#ec4899"
            } else {
                "#4c1d95"
            };
            let background = if is_ming { "#2e1065" } else { "#1e1b4b" };
            let palace_name = palace
                .get("palace_name")
                .and_then(Value::as_str)
                .unwrap_or("");
            let branch = palace
                .get("earth_branch")
                .and_then(Value::as_str)
                .unwrap_or("");
            let stars = palace
                .get("stars")
                .and_then(Value::as_array)
                .map(|items| {
                    items
                        .iter()
                        .filter_map(Value::as_str)
                        .collect::<Vec<_>>()
                        .join(" ")
                })
                .filter(|text| !text.is_empty())
                .unwrap_or_else(|| "無主星".to_string());
            let mutators = palace
                .get("mutators")
                .and_then(Value::as_array)
                .map(|items| {
                    items
                        .iter()
                        .filter_map(Value::as_str)
                        .collect::<Vec<_>>()
                        .join(" ")
                })
                .unwrap_or_default();

            svg.push_str(&format!(r##"<rect x="{x}" y="{y}" width="170" height="150" rx="8" fill="{background}" stroke="{stroke}" stroke-width="2"/><text x="{}" y="{}" font-family="Prompt, sans-serif" font-size="14" font-weight="bold" fill="#fef08a">{palace_name} ({branch})</text><text x="{}" y="{}" font-family="sans-serif" font-size="16" font-weight="bold" fill="#c084fc">{stars}</text>"##, x + 10, y + 25, x + 10, y + 65));
            if !mutators.is_empty() {
                svg.push_str(&format!(r##"<text x="{}" y="{}" font-family="Prompt, sans-serif" font-size="12" fill="#f43f5e">四化: {mutators}</text>"##, x + 10, y + 105));
            }
        }
    }
    svg.push_str("</g></svg>");
    svg
}

/// Render Qi Men palaces with earth stem, star, door, and spirit intact.
pub fn render_qimen_svg(chart: &Value, title: &str) -> String {
    let solar_term = string_at(chart, "/solar_term");
    let dun_type = string_at(chart, "/dun_type");
    let ju_number = chart.get("ju_number").and_then(Value::as_i64).unwrap_or(1);
    let mut svg = String::with_capacity(6144);
    svg.push_str(r##"<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="100%" height="100%"><rect width="600" height="600" rx="16" fill="#09131d" stroke="#3b82f6" stroke-width="2"/>"##);
    svg.push_str(&format!(r##"<text x="300" y="40" font-family="Prompt, sans-serif" font-size="20" font-weight="bold" fill="#60a5fa" text-anchor="middle">⚡ {title}</text><text x="300" y="65" font-family="Prompt, sans-serif" font-size="12" fill="#93c5fd" text-anchor="middle">節氣: {solar_term} | 陰陽遁: {dun_type}遁 {ju_number}局</text><g transform="translate(45, 90)">"##));
    let grid_map = [
        (1, 1, 2),
        (2, 2, 0),
        (3, 0, 1),
        (4, 0, 0),
        (5, 1, 1),
        (6, 2, 2),
        (7, 2, 1),
        (8, 0, 2),
        (9, 1, 0),
    ];
    if let Some(palaces) = chart.get("palaces").and_then(Value::as_array) {
        for palace in palaces {
            let number = palace
                .get("palace_number")
                .and_then(Value::as_i64)
                .unwrap_or(5);
            let (_, column, row) = grid_map
                .iter()
                .find(|&&(candidate, _, _)| candidate == number)
                .copied()
                .unwrap_or((5, 1, 1));
            let x = column * 170;
            let y = row * 155;
            let stem = palace
                .get("earth_stem")
                .and_then(Value::as_str)
                .unwrap_or("");
            let star = palace.get("star").and_then(Value::as_str).unwrap_or("");
            let door = palace.get("door").and_then(Value::as_str).unwrap_or("");
            let spirit = palace.get("spirit").and_then(Value::as_str).unwrap_or("");
            svg.push_str(&format!(r##"<rect x="{x}" y="{y}" width="160" height="145" rx="8" fill="#1e293b" stroke="#1d4ed8" stroke-width="1.5"/><text x="{}" y="{}" font-family="Prompt, sans-serif" font-size="13" font-weight="bold" fill="#93c5fd">宮位 {number}</text><text x="{}" y="{}" font-family="sans-serif" font-size="12" fill="#e2e8f0">天干: {stem}</text><text x="{}" y="{}" font-family="sans-serif" font-size="14" fill="#38bdf8">九星: {star}</text><text x="{}" y="{}" font-family="sans-serif" font-size="14" fill="#4ade80">八門: {door}</text><text x="{}" y="{}" font-family="sans-serif" font-size="14" fill="#fbbf24">八神: {spirit}</text>"##, x + 10, y + 20, x + 90, y + 20, x + 10, y + 50, x + 10, y + 82, x + 10, y + 114));
        }
    }
    svg.push_str("</g></svg>");
    svg
}

/// Render Xuan Kong mountain metadata and every three-star palace tuple.
pub fn render_xuankong_svg(chart: &Value, title: &str) -> String {
    let period = chart.get("period").and_then(Value::as_i64).unwrap_or(9);
    let facing = string_at(chart, "/facing_mountain");
    let sitting = string_at(chart, "/sitting_mountain");
    let mut svg = String::with_capacity(6144);
    svg.push_str(r##"<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="100%" height="100%"><rect width="600" height="600" rx="16" fill="#1a0914" stroke="#ec4899" stroke-width="2"/>"##);
    svg.push_str(&format!(r##"<text x="300" y="40" font-family="Prompt, sans-serif" font-size="20" font-weight="bold" fill="#f472b6" text-anchor="middle">🏯 {title}</text><text x="300" y="65" font-family="Prompt, sans-serif" font-size="12" fill="#fbcfe8" text-anchor="middle">九運: 第 {period} 運 | 向首: {facing} | 坐山: {sitting}</text><g transform="translate(45, 90)">"##));
    let grid_map = [
        (4, 0, 0),
        (9, 1, 0),
        (2, 2, 0),
        (3, 0, 1),
        (5, 1, 1),
        (7, 2, 1),
        (8, 0, 2),
        (1, 1, 2),
        (6, 2, 2),
    ];
    if let Some(palaces) = chart.get("grid_palaces").and_then(Value::as_array) {
        for palace in palaces {
            let number = palace
                .get("palace_number")
                .and_then(Value::as_i64)
                .unwrap_or(5);
            let (_, column, row) = grid_map
                .iter()
                .find(|&&(candidate, _, _)| candidate == number)
                .copied()
                .unwrap_or((5, 1, 1));
            let x = column * 170;
            let y = row * 155;
            let direction = palace
                .get("direction")
                .and_then(Value::as_str)
                .unwrap_or("");
            let name = palace
                .get("palace_name")
                .and_then(Value::as_str)
                .unwrap_or("");
            let sitting_star = palace
                .get("sitting_star")
                .and_then(Value::as_i64)
                .unwrap_or(0);
            let facing_star = palace
                .get("facing_star")
                .and_then(Value::as_i64)
                .unwrap_or(0);
            let base_star = palace.get("base_star").and_then(Value::as_i64).unwrap_or(0);
            svg.push_str(&format!(r##"<rect x="{x}" y="{y}" width="160" height="145" rx="8" fill="#2d1222" stroke="#be185d" stroke-width="1.5"/><text x="{}" y="{}" font-family="Prompt, sans-serif" font-size="14" font-weight="bold" fill="#fbcfe8">{direction} ({name})</text><text x="{}" y="{}" font-family="sans-serif" font-size="16" font-weight="bold" fill="#38bdf8">山星: {sitting_star}</text><text x="{}" y="{}" font-family="sans-serif" font-size="16" font-weight="bold" fill="#f43f5e">向星: {facing_star}</text><text x="{}" y="{}" font-family="sans-serif" font-size="15" font-weight="bold" fill="#fbbf24">運星: {base_star}</text>"##, x + 10, y + 25, x + 10, y + 65, x + 85, y + 65, x + 45, y + 110));
        }
    }
    svg.push_str("</g></svg>");
    svg
}

/// High-performance Rust BaZi 4 Pillars SVG Generator.
#[cfg(feature = "python")]
#[pyfunction]
pub fn build_bazi_svg_rust(
    py: Python<'_>,
    title: String,
    day_master_stem: String,
    day_master_element: String,
    tst_datetime: String,
    total_elements_sum: f32,
    hour_pillar: (String, String),
    day_pillar: (String, String),
    month_pillar: (String, String),
    year_pillar: (String, String),
) -> PyResult<String> {
    let result = py.allow_threads(move || {
        let mut svg = String::with_capacity(8192);

        svg.push_str(r##"<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" width="100%" height="100%">"##);
        svg.push_str(r##"<defs><linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">"##);
        svg.push_str(r##"<stop offset="0%" stop-color="#0a0c16"/><stop offset="100%" stop-color="#12182b"/>"##);
        svg.push_str(r##"</linearGradient><filter id="glow" x="-20%" y="-20%" width="140%" height="140%">"##);
        svg.push_str(r##"<feGaussianBlur stdDeviation="4" result="blur"/><feComposite in="SourceGraphic" in2="blur" operator="over"/>"##);
        svg.push_str(r##"</filter></defs>"##);

        // Background
        svg.push_str(r##"<rect width="800" height="600" fill="url(#bgGrad)" rx="16"/>"##);
        svg.push_str(r##"<rect x="12" y="12" width="776" height="576" fill="none" stroke="#1e293b" stroke-width="2" rx="12"/>"##);

        // Header Title
        svg.push_str(&format!(
            r##"<text x="400" y="52" fill="#f8fafc" font-family="sans-serif" font-size="22" font-weight="bold" text-anchor="middle" filter="url(#glow)">{}</text>"##,
            title
        ));

        // Subtitle / TST Info
        svg.push_str(&format!(
            r##"<text x="400" y="80" fill="#94a3b8" font-family="sans-serif" font-size="13" text-anchor="middle">True Solar Time (TST): {} | Day Master: {} ({})</text>"##,
            tst_datetime, day_master_stem, day_master_element
        ));

        // 4 Pillars Cards
        let pillars = [
            ("เสายาม", &hour_pillar.0, &hour_pillar.1, 80),
            ("เสาวัน", &day_pillar.0, &day_pillar.1, 240),
            ("เสาเดือน", &month_pillar.0, &month_pillar.1, 400),
            ("เสาปี", &year_pillar.0, &year_pillar.1, 560),
        ];

        for (label, stem, branch, x) in pillars {
            svg.push_str(&format!(
                r##"<g transform="translate({}, 110)">"##, x
            ));
            svg.push_str(r##"<rect width="140" height="260" fill="#1e293b" rx="12" stroke="#334155" stroke-width="1.5"/>"##);
            svg.push_str(&format!(
                r##"<rect width="140" height="36" fill="#0f172a" rx="12" opacity="0.8"/><text x="70" y="24" fill="#cbd5e1" font-family="sans-serif" font-size="14" font-weight="bold" text-anchor="middle">{}</text>"##,
                label
            ));
            // Stem (ก้านฟ้า)
            svg.push_str(&format!(
                r##"<text x="70" y="115" fill="#38bdf8" font-family="sans-serif" font-size="42" font-weight="bold" text-anchor="middle">{}</text>"##,
                stem
            ));
            // Branch (กิ่งดิน)
            svg.push_str(&format!(
                r##"<text x="70" y="200" fill="#10b981" font-family="sans-serif" font-size="42" font-weight="bold" text-anchor="middle">{}</text>"##,
                branch
            ));
            svg.push_str("</g>");
        }

        // Five Elements Summary Bar
        svg.push_str(r##"<g transform="translate(60, 420)">"##);
        svg.push_str(&format!(
            r##"<text x="0" y="0" fill="#cbd5e1" font-family="sans-serif" font-size="14" font-weight="bold">สมดุล 5 ธาตุ (Five Elements Harmony Total: {:.1}%):</text>"##,
            total_elements_sum
        ));
        svg.push_str(r##"<rect x="0" y="15" width="680" height="24" fill="#0f172a" rx="6" stroke="#334155"/>"##);

        let mut curr_x = 0.0;
        for (name, color) in ELEMENT_COLORS {
            let width = 136.0; // Equal distribution bar segment
            svg.push_str(&format!(
                r##"<rect x="{:.1}" y="15" width="{:.1}" height="24" fill="{}" opacity="0.85"/>"##,
                curr_x, width, color
            ));
            svg.push_str(&format!(
                r##"<text x="{:.1}" y="32" fill="#ffffff" font-family="sans-serif" font-size="11" font-weight="bold" text-anchor="middle">{}</text>"##,
                curr_x + (width / 2.0), name
            ));
            curr_x += width;
        }
        svg.push_str("</g>");

        // Footer Watermark
        svg.push_str(r##"<text x="400" y="565" fill="#475569" font-family="sans-serif" font-size="12" text-anchor="middle">Computational Metaphysics Engine • Rust High-Performance Renderer</text>"##);
        svg.push_str("</svg>");

        svg
    });
    Ok(result)
}

#[cfg(feature = "python")]
static ZODIAC_THAI_SHORT: &[&str] = &[
    "เมษ",
    "พฤษภ",
    "เมถุน",
    "กรกฎ",
    "สิงห์",
    "กันย์",
    "ตุลย์",
    "พิจิก",
    "ธนู",
    "มังกร",
    "กุมภ์",
    "มีน",
];

/// High-performance Rust 12 Zodiac Wheel SVG Generator.
#[cfg(feature = "python")]
#[pyfunction]
pub fn build_zodiac_svg_rust(py: Python<'_>, title: String) -> PyResult<String> {
    let result = py.allow_threads(move || {
        let mut svg = String::with_capacity(4096);

        svg.push_str(r##"<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="100%" height="100%">"##);
        svg.push_str(r##"<rect width="600" height="600" rx="16" fill="#0b0f19" stroke="#0284c7" stroke-width="2"/>"##);
        svg.push_str(&format!(
            r##"<text x="300" y="40" font-family="sans-serif" font-size="20" font-weight="bold" fill="#38bdf8" text-anchor="middle">🌌 {}</text>"##,
            title
        ));
        svg.push_str(r##"<g transform="translate(300, 310)">"##);
        svg.push_str(r##"<circle r="220" fill="none" stroke="#334155" stroke-width="3"/>"##);
        svg.push_str(r##"<circle r="140" fill="none" stroke="#0284c7" stroke-dasharray="4,4" stroke-width="1.5"/>"##);
        svg.push_str(r##"<circle r="60" fill="#1e293b" stroke="#38bdf8" stroke-width="2"/>"##);
        svg.push_str(r##"<text x="0" y="5" font-family="sans-serif" font-size="22" font-weight="bold" fill="#fbbf24" text-anchor="middle">☯</text>"##);

        for i in 0..12 {
            let angle = (i as f64) * (360.0 / 12.0) - 90.0;
            let rad = angle.to_radians();
            let x_outer = 220.0 * rad.cos();
            let y_outer = 220.0 * rad.sin();
            let x_inner = 60.0 * rad.cos();
            let y_inner = 60.0 * rad.sin();

            let mid_rad = (angle + 15.0).to_radians();
            let x_text = 180.0 * mid_rad.cos();
            let y_text = 180.0 * mid_rad.sin();

            svg.push_str(&format!(
                r##"<line x1="{:.1}" y1="{:.1}" x2="{:.1}" y2="{:.1}" stroke="#334155" stroke-width="1.5"/>"##,
                x_inner, y_inner, x_outer, y_outer
            ));
            svg.push_str(&format!(
                r##"<text x="{:.1}" y="{:.1}" font-family="sans-serif" font-size="11" fill="#e2e8f0" text-anchor="middle" dominant-baseline="central">{}</text>"##,
                x_text, y_text, ZODIAC_THAI_SHORT[i]
            ));
        }

        svg.push_str("</g></svg>");
        svg
    });
    Ok(result)
}

/// High-performance Rust Zi Wei Dou Shu 12 Palaces Chart SVG Generator.
#[cfg(feature = "python")]
#[pyfunction]
pub fn build_ziwei_svg_rust(
    py: Python<'_>,
    title: String,
    bureau: String,
    ming_branch: String,
    shen_branch: String,
) -> PyResult<String> {
    let result = py.allow_threads(move || {
        let mut svg = String::with_capacity(6144);

        svg.push_str(r##"<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 800" width="100%" height="100%">"##);
        svg.push_str(r##"<rect width="800" height="800" rx="16" fill="#0c0718" stroke="#a855f7" stroke-width="2"/>"##);
        svg.push_str(&format!(
            r##"<text x="400" y="45" font-family="sans-serif" font-size="22" font-weight="bold" fill="#c084fc" text-anchor="middle">🔮 {}</text>"##,
            title
        ));
        svg.push_str(&format!(
            r##"<text x="400" y="75" font-family="sans-serif" font-size="13" fill="#e9d5ff" text-anchor="middle">五行局: {} | 命宮: {} | 身宮: {}</text>"##,
            bureau, ming_branch, shen_branch
        ));

        // Outer 12 Palaces Grid Frame
        svg.push_str(r##"<rect x="50" y="100" width="700" height="650" fill="none" stroke="#6b21a8" stroke-width="2" rx="8"/>"##);

        // Center Palace (Heaven/Earth Core)
        svg.push_str(r##"<rect x="225" y="262.5" width="350" height="325" fill="#180e29" stroke="#9333ea" stroke-width="1.5" rx="8"/>"##);
        svg.push_str(r##"<text x="400" y="415" font-family="sans-serif" font-size="28" font-weight="bold" fill="#f0abfc" text-anchor="middle">紫微斗數 太極中宮</text>"##);
        svg.push_str(r##"<text x="400" y="445" font-family="sans-serif" font-size="14" fill="#a855f7" text-anchor="middle">Rust Metaphysics Grid Acceleration Engine</text>"##);
        svg.push_str("</svg>");
        svg
    });
    Ok(result)
}

/// High-performance Rust Qi Men Dun Jia 9-Grid SVG Generator.
#[cfg(feature = "python")]
#[pyfunction]
pub fn build_qimen_svg_rust(
    py: Python<'_>,
    title: String,
    solar_term: String,
    dun_type: String,
    ju_num: i32,
) -> PyResult<String> {
    let result = py.allow_threads(move || {
        let mut svg = String::with_capacity(4096);

        svg.push_str(r##"<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="100%" height="100%">"##);
        svg.push_str(r##"<rect width="600" height="600" rx="16" fill="#09131d" stroke="#3b82f6" stroke-width="2"/>"##);
        svg.push_str(&format!(
            r##"<text x="300" y="40" font-family="sans-serif" font-size="20" font-weight="bold" fill="#60a5fa" text-anchor="middle">⚡ {}</text>"##,
            title
        ));
        svg.push_str(&format!(
            r##"<text x="300" y="65" font-family="sans-serif" font-size="12" fill="#93c5fd" text-anchor="middle">節氣: {} | 陰陽遁: {}遁 {}局</text>"##,
            solar_term, dun_type, ju_num
        ));

        svg.push_str(r##"<g transform="translate(45, 90)">"##);
        let grid_coords = [
            (4, 0, 0), (9, 1, 0), (2, 2, 0),
            (3, 0, 1), (5, 1, 1), (7, 2, 1),
            (8, 0, 2), (1, 1, 2), (6, 2, 2),
        ];

        for (p_num, col, row) in grid_coords {
            let x = col * 170;
            let y = row * 155;
            svg.push_str(&format!(
                r##"<rect x="{}" y="{}" width="160" height="145" rx="8" fill="#1e293b" stroke="#1d4ed8" stroke-width="1.5"/>"##,
                x, y
            ));
            svg.push_str(&format!(
                r##"<text x="{}" y="{}" font-family="sans-serif" font-size="13" font-weight="bold" fill="#93c5fd">宮位 {}</text>"##,
                x + 10, y + 25, p_num
            ));
            svg.push_str(&format!(
                r##"<text x="{}" y="{}" font-family="sans-serif" font-size="13" fill="#fbbf24">奇門 9 宮 (Rust)</text>"##,
                x + 10, y + 75
            ));
        }

        svg.push_str("</g></svg>");
        svg
    });
    Ok(result)
}

/// High-performance Rust Xuan Kong Flying Stars 9-Grid SVG Generator.
#[cfg(feature = "python")]
#[pyfunction]
pub fn build_xuankong_svg_rust(
    py: Python<'_>,
    title: String,
    facing_degree: f32,
    period: i32,
) -> PyResult<String> {
    let result = py.allow_threads(move || {
        let mut svg = String::with_capacity(4096);

        svg.push_str(r##"<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="100%" height="100%">"##);
        svg.push_str(r##"<rect width="600" height="600" rx="16" fill="#0f172a" stroke="#10b981" stroke-width="2"/>"##);
        svg.push_str(&format!(
            r##"<text x="300" y="40" font-family="sans-serif" font-size="20" font-weight="bold" fill="#34d399" text-anchor="middle">風水 {}</text>"##,
            title
        ));
        svg.push_str(&format!(
            r##"<text x="300" y="65" font-family="sans-serif" font-size="12" fill="#6ee7b7" text-anchor="middle">Facing: {:.1}° | Period: {}</text>"##,
            facing_degree, period
        ));

        svg.push_str(r##"<g transform="translate(45, 90)">"##);
        let grid_positions = [
            (4, 0, 0), (9, 1, 0), (2, 2, 0),
            (3, 0, 1), (5, 1, 1), (7, 2, 1),
            (8, 0, 2), (1, 1, 2), (6, 2, 2),
        ];

        for (p_num, col, row) in grid_positions {
            let x = col * 170;
            let y = row * 155;
            svg.push_str(&format!(
                r##"<rect x="{}" y="{}" width="160" height="145" rx="8" fill="#1e293b" stroke="#059669" stroke-width="1.5"/>"##,
                x, y
            ));
            svg.push_str(&format!(
                r##"<text x="{}" y="{}" font-family="sans-serif" font-size="14" font-weight="bold" fill="#a7f3d0">宮位 {}</text>"##,
                x + 10, y + 25, p_num
            ));
        }

        svg.push_str("</g></svg>");
        svg
    });
    Ok(result)
}
