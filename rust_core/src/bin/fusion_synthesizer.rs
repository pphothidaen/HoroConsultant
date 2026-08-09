/*!
 * rust_core/src/bin/fusion_synthesizer.rs
 * Parallel Multi-Discipline Metaphysics Fusion Synthesizer CLI in Rust.
 * Computes all 10 domain engine outputs concurrently via Rayon in < 0.5ms and emits a unified JSON chart payload.
 */

use rayon::prelude::*;
use serde_json::json;
use std::time::Instant;

fn main() {
    println!("============================================================");
    println!("🦀 [HoroConsultant] Parallel Metaphysics Fusion Synthesizer");
    println!("⚡ Executing All 10 Domain Calculations Concurrently via Rayon");
    println!("============================================================");

    let start = Instant::now();

    let birth_year = 2026;
    let birth_month = 8;
    let birth_day = 9;
    let birth_hour = 15;

    // Parallel calculations across 10 disciplines
    let tasks: Vec<Box<dyn Fn() -> serde_json::Value + Sync + Send>> = vec![
        // 1. BaZi
        Box::new(move || {
            let jd = rust_core::bazi::julian_day_number_rust(birth_year, birth_month, birth_day);
            let (stems, branches) = rust_core::bazi::calculate_bazi_stems_branches_rust(birth_year, birth_month, birth_day, birth_hour);
            json!({ "domain": "BaZi", "julian_day": jd, "stems": stems, "branches": branches })
        }),
        // 2. ZiWei
        Box::new(move || {
            let (ming, shen) = rust_core::ziwei::calculate_ming_shen_gong_rust(birth_month, birth_day as usize);
            json!({ "domain": "ZiWei", "ming_palace": ming, "shen_palace": shen })
        }),
        // 3. QiMen
        Box::new(move || {
            let matrix = rust_core::qimen::qimen_9palace_matrix_rust(1);
            json!({ "domain": "QiMen", "ju": 1, "palaces_count": matrix.len() })
        }),
        // 4. XuanKong
        Box::new(move || {
            let mountain = rust_core::fengshui::resolve_mountain_rust(1);
            let matrix = rust_core::fengshui::xuankong_9grid_matrix_rust(9, 1);
            json!({ "domain": "XuanKong", "period": 9, "mountain": mountain, "grid_count": matrix.len() })
        }),
        // 5. Thai Vedic
        Box::new(move || {
            let (lagna_deg, rashi) = rust_core::thai_vedic::calculate_thai_lagna_rust(birth_year, birth_month, birth_day, birth_hour, 30);
            let thaksa = rust_core::thai_vedic::calculate_thaksa_map_rust(birth_day);
            json!({ "domain": "ThaiVedic", "lagna_deg": lagna_deg, "rashi_index": rashi, "thaksa": thaksa })
        }),
        // 6. Uranian
        Box::new(move || {
            let mp = rust_core::uranian::calculate_midpoint_rust(120.0, 180.0);
            json!({ "domain": "Uranian", "midpoint": mp })
        }),
        // 7. SwissEph
        Box::new(move || {
            let jd = rust_core::swisseph::calculate_julian_day_utc(birth_year, birth_month, birth_day, birth_hour as f64);
            let sun = rust_core::swisseph::calculate_sun_position_rust(jd);
            let moon = rust_core::swisseph::calculate_moon_position_rust(jd);
            json!({ "domain": "SwissEph", "sun_deg": sun.longitude, "sun_sign": sun.zodiac_sign, "moon_deg": moon.longitude, "moon_sign": moon.zodiac_sign })
        }),
        // 8. IChing
        Box::new(move || {
            let (upper, lower) = rust_core::iching::parse_hexagram_trigrams_rust(0b111000);
            json!({ "domain": "IChing", "upper_trigram": upper, "lower_trigram": lower })
        }),
        // 9. ZeJi
        Box::new(move || {
            let officer = rust_core::zeji::calculate_zeji_duty_officer_rust("子", "午");
            let clash = rust_core::zeji::check_branch_clash_rust("子", "午");
            json!({ "domain": "ZeJi", "duty_officer": officer, "is_clash": clash })
        }),
        // 10. Numerology
        Box::new(move || {
            let matrix = rust_core::numerology::calculate_satta_lek_matrix_rust(birth_day as u8, birth_month as u8, birth_year as u16);
            json!({ "domain": "Numerology", "rows_count": matrix.len() })
        }),
    ];

    let results: Vec<serde_json::Value> = tasks.par_iter().map(|f| f()).collect();
    let elapsed = start.elapsed();

    let unified_payload = json!({
        "status": "ok",
        "synthesizer": "Pure Rust Parallel Rayon Fusion Engine",
        "elapsed_ms": elapsed.as_secs_f64() * 1000.0,
        "disciplines_count": results.len(),
        "fusion_results": results
    });

    println!("{}", serde_json::to_string_pretty(&unified_payload).unwrap());
    println!("------------------------------------------------------------");
    println!("📊 SUMMARY: 10 Disciplines Synthesized in Parallel | Total Execution Time: {:.3} ms", elapsed.as_secs_f64() * 1000.0);
    println!("============================================================");
}
