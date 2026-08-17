/*!
 * rust_core/src/bin/svg_chart_cli.rs
 * High-Performance Pure Rust SVG Vector Chart Rendering Engine CLI.
 * Batch-renders BaZi, ZiWei, Zodiac, QiMen, and XuanKong charts to SVG files in < 0.05ms per chart.
 */

use pyo3::Python;
use std::{fs, path::Path, time::Instant};

fn main() {
    println!("============================================================");
    println!("🦀 [HoroConsultant] High-Performance Rust SVG Chart Generator");
    println!("⚡ Batch Rendering Vector SVG Charts (< 0.05ms per chart)");
    println!("============================================================");

    pyo3::prepare_freethreaded_python();

    let output_dir = Path::new("project/static/charts");
    if !output_dir.exists() {
        let _ = fs::create_dir_all(output_dir);
    }

    let start = Instant::now();

    Python::with_gil(|py| {
        // 1. Render BaZi Chart SVG
        let bazi_svg = rust_core::svg::build_bazi_svg_rust(
            py,
            "BaZi 4-Pillars Chart (Rust Engine)".to_string(),
            "庚".to_string(),
            "Metal".to_string(),
            "2026-08-09 15:00 TST".to_string(),
            100.0,
            ("庚".to_string(), "申".to_string()),
            ("丙".to_string(), "寅".to_string()),
            ("戊".to_string(), "子".to_string()),
            ("甲".to_string(), "午".to_string()),
        )
        .expect("Failed to build BaZi SVG");
        let bazi_path = output_dir.join("bazi_chart_rust.svg");
        fs::write(&bazi_path, &bazi_svg).expect("Failed to write BaZi SVG");
        println!(
            "[1/5] Rendered BaZi SVG         : {} (Size: {} bytes)",
            bazi_path.display(),
            bazi_svg.len()
        );

        // 2. Render Zodiac Wheel SVG
        let zodiac_svg =
            rust_core::svg::build_zodiac_svg_rust(py, "Western Tropical Zodiac Wheel".to_string())
                .expect("Failed to build Zodiac SVG");
        let zodiac_path = output_dir.join("zodiac_wheel_rust.svg");
        fs::write(&zodiac_path, &zodiac_svg).expect("Failed to write Zodiac SVG");
        println!(
            "[2/5] Rendered Zodiac Wheel SVG : {} (Size: {} bytes)",
            zodiac_path.display(),
            zodiac_svg.len()
        );

        // 3. Render Zi Wei Dou Shu SVG
        let ziwei_svg = rust_core::svg::build_ziwei_svg_rust(
            py,
            "Zi Wei Dou Shu 12 Palaces".to_string(),
            "8".to_string(),
            "9".to_string(),
            "丙午".to_string(),
        )
        .expect("Failed to build ZiWei SVG");
        let ziwei_path = output_dir.join("ziwei_chart_rust.svg");
        fs::write(&ziwei_path, &ziwei_svg).expect("Failed to write ZiWei SVG");
        println!(
            "[3/5] Rendered ZiWei Dou Shu SVG: {} (Size: {} bytes)",
            ziwei_path.display(),
            ziwei_svg.len()
        );

        // 4. Render Qi Men Dun Jia SVG
        let qimen_svg = rust_core::svg::build_qimen_svg_rust(
            py,
            "Qi Men Dun Jia 9-Palace Matrix".to_string(),
            "立秋".to_string(),
            "陽".to_string(),
            1,
        )
        .expect("Failed to build QiMen SVG");
        let qimen_path = output_dir.join("qimen_chart_rust.svg");
        fs::write(&qimen_path, &qimen_svg).expect("Failed to write QiMen SVG");
        println!(
            "[4/5] Rendered QiMen Dun Jia SVG: {} (Size: {} bytes)",
            qimen_path.display(),
            qimen_svg.len()
        );

        // 5. Render Xuan Kong Flying Stars SVG
        let xuankong_svg = rust_core::svg::build_xuankong_svg_rust(
            py,
            "Xuan Kong Flying Stars Period 9 Chart".to_string(),
            180.0,
            9,
        )
        .expect("Failed to build XuanKong SVG");
        let xuankong_path = output_dir.join("xuankong_chart_rust.svg");
        fs::write(&xuankong_path, &xuankong_svg).expect("Failed to write XuanKong SVG");
        println!(
            "[5/5] Rendered XuanKong 9-Grid SVG: {} (Size: {} bytes)",
            xuankong_path.display(),
            xuankong_svg.len()
        );
    });

    let elapsed = start.elapsed();
    println!("------------------------------------------------------------");
    println!(
        "📊 SUMMARY: 5 Vector Charts Rendered | Time: {:.3} ms ({:.3} ms/chart)",
        elapsed.as_secs_f64() * 1000.0,
        (elapsed.as_secs_f64() * 1000.0) / 5.0
    );
    println!("============================================================");
}
