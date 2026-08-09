/*!
 * rust_core/src/svg.rs
 * High-Performance Rust SVG Vector Chart Rendering Engine.
 * Generates standalone, pixel-perfect SVG charts for BaZi 4 Pillars, Zodiac Wheels, and Metaphysical Grids.
 */

use pyo3::prelude::*;

static ELEMENT_COLORS: &[(&str, &str)] = &[
    ("Wood", "#10b981"),
    ("Fire", "#ef4444"),
    ("Earth", "#d97706"),
    ("Metal", "#38bdf8"),
    ("Water", "#8b5cf6"),
];

/// High-performance Rust BaZi 4 Pillars SVG Generator.
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

static ZODIAC_THAI_SHORT: &[&str] = &[
    "เมษ", "พฤษภ", "เมถุน", "กรกฎ", "สิงห์", "กันย์",
    "ตุลย์", "พิจิก", "ธนู", "มังกร", "กุมภ์", "มีน"
];

/// High-performance Rust 12 Zodiac Wheel SVG Generator.
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
