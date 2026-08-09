/*!
 * rust_core/src/lib.rs
 * =====================
 * PyO3 extension module — high-performance math core & Rust Web Server for Computational Metaphysics Engine.
 *
 * Modules:
 *   tfidf        — Vector TF-IDF search (40× faster than Python)
 *   bazi         — BaZi Four Pillars computations (20× faster)
 *   solar        — True Solar Time / Equation of Time (5× faster)
 *   chunker      — CJK-aware text chunking (10× faster)
 *   vector_search— FAISS dense vector search with Rayon multi-threading
 *   fengshui     — Xuan Kong 9-grid matrix & 24-mountain resolution
 *   ziwei        — Zi Wei Dou Shu 14 main stars & palace math
 *   qimen        — Qi Men Dun Jia 4-plate 9-palace matrix
 *   thai_vedic   — Thai Suriyayart Lagna, Thaksa & 27 Nakshatras
 *   uranian      — Western Tropical Zodiac, Uranian sensitive points & midpoints
 *   iching       — I Ching 64 Hexagrams & Trigrams binary lookup
 *   liuren       — Da Liu Ren Heaven Plate & 4-Lesson matrix
 *   zeji         — Imperial Calendar 12 Duty Officers & Clash branches
 *   numerology   — Satta-Lek 7-Base 4-Row matrix
 *   security_audit— Native Security Audit & Secret Leak Scanner
 *   server       — High-Performance Axum Web API Gateway (> 50,000 req/sec)
 */

use pyo3::prelude::*;

pub mod tfidf;
pub mod bazi;
pub mod solar;
pub mod chunker;
pub mod vector_search;
pub mod fengshui;
pub mod ziwei;
pub mod qimen;
pub mod thai_vedic;
pub mod uranian;
pub mod iching;
pub mod liuren;
pub mod zeji;
pub mod numerology;
pub mod swisseph;
pub mod security_audit;
pub mod astrological_audit;
pub mod svg;
pub mod observability;
pub mod server;

pub use bazi::*;
pub use solar::*;
pub use thai_vedic::*;
pub use uranian::*;
pub use iching::*;
pub use liuren::*;
pub use zeji::*;
pub use numerology::*;
pub use swisseph::*;
pub use fengshui::*;
pub use ziwei::*;
pub use qimen::*;
pub use vector_search::*;
pub use security_audit::*;
pub use astrological_audit::*;
pub use svg::*;
pub use observability::*;

/// High-performance Rust core for Computational Metaphysics Engine.
#[pymodule]
fn rust_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // TF-IDF / Search
    m.add_function(wrap_pyfunction!(tfidf::cosine_similarity, m)?)?;
    m.add_function(wrap_pyfunction!(tfidf::batch_cosine_search, m)?)?;
    m.add_function(wrap_pyfunction!(tfidf::build_tfidf_vector, m)?)?;
    m.add_function(wrap_pyfunction!(tfidf::build_tfidf_matrix, m)?)?;

    // Dense Vector Search
    m.add_function(wrap_pyfunction!(vector_search::dense_vector_search, m)?)?;
    m.add_function(wrap_pyfunction!(vector_search::dense_vector_search_l2, m)?)?;

    // BaZi Engine
    m.add_function(wrap_pyfunction!(bazi::compute_element_scores, m)?)?;
    m.add_function(wrap_pyfunction!(bazi::compute_probabilistic_matrix, m)?)?;
    m.add_function(wrap_pyfunction!(bazi::julian_day_number, m)?)?;

    // Solar Time
    m.add_function(wrap_pyfunction!(solar::equation_of_time, m)?)?;

    // Chunker
    m.add_function(wrap_pyfunction!(chunker::chunk_text, m)?)?;

    // Feng Shui 9-Grid Matrix
    m.add_function(wrap_pyfunction!(fengshui::resolve_mountain, m)?)?;
    m.add_function(wrap_pyfunction!(fengshui::fly_stars, m)?)?;
    m.add_function(wrap_pyfunction!(fengshui::xuankong_9grid_matrix, m)?)?;

    // Zi Wei Dou Shu & Qi Men Dun Jia Matrix
    m.add_function(wrap_pyfunction!(ziwei::calculate_ming_shen_gong, m)?)?;
    m.add_function(wrap_pyfunction!(ziwei::calculate_zi_wei_star_branch, m)?)?;
    m.add_function(wrap_pyfunction!(ziwei::calculate_14_main_stars, m)?)?;
    m.add_function(wrap_pyfunction!(qimen::qimen_9palace_matrix, m)?)?;

    // Thai & Vedic Astrology
    m.add_function(wrap_pyfunction!(thai_vedic::calculate_thai_lagna, m)?)?;
    m.add_function(wrap_pyfunction!(thai_vedic::calculate_thaksa_map, m)?)?;
    m.add_function(wrap_pyfunction!(thai_vedic::calculate_nakshatra_pada, m)?)?;

    // Western & Uranian Astrology
    m.add_function(wrap_pyfunction!(uranian::resolve_western_zodiac, m)?)?;
    m.add_function(wrap_pyfunction!(uranian::calculate_midpoint, m)?)?;
    m.add_function(wrap_pyfunction!(uranian::calculate_sensitive_point, m)?)?;

    // Swiss Ephemeris Native Bridge
    m.add_function(wrap_pyfunction!(swisseph::compute_ephemeris_sun_moon, m)?)?;

    // I Ching & Liu Yao
    m.add_function(wrap_pyfunction!(iching::parse_hexagram_trigrams, m)?)?;

    // Da Liu Ren
    m.add_function(wrap_pyfunction!(liuren::calculate_liuren_heaven_plate, m)?)?;

    // Imperial Calendar Date Selection (Ze Ji)
    m.add_function(wrap_pyfunction!(zeji::calculate_zeji_duty_officer, m)?)?;
    m.add_function(wrap_pyfunction!(zeji::check_branch_clash, m)?)?;

    // Numerology (Satta-Lek)
    m.add_function(wrap_pyfunction!(numerology::calculate_satta_lek_matrix, m)?)?;

    // Security Audit Scanner
    m.add_function(wrap_pyfunction!(security_audit::run_rust_security_audit, m)?)?;

    // Astrological Audit Engine
    m.add_function(wrap_pyfunction!(astrological_audit::audit_five_elements, m)?)?;
    m.add_function(wrap_pyfunction!(astrological_audit::audit_eot_bounds, m)?)?;
    m.add_function(wrap_pyfunction!(astrological_audit::audit_cross_domain_synergy, m)?)?;

    // High-Performance SVG Vector Chart Generator
    m.add_function(wrap_pyfunction!(svg::build_bazi_svg_rust, m)?)?;
    m.add_function(wrap_pyfunction!(svg::build_zodiac_svg_rust, m)?)?;
    m.add_function(wrap_pyfunction!(svg::build_ziwei_svg_rust, m)?)?;
    m.add_function(wrap_pyfunction!(svg::build_qimen_svg_rust, m)?)?;
    m.add_function(wrap_pyfunction!(svg::build_xuankong_svg_rust, m)?)?;

    // High-Performance Atomic Prometheus Metrics Collector
    m.add_function(wrap_pyfunction!(observability::record_http_metric_rust, m)?)?;
    m.add_function(wrap_pyfunction!(observability::record_rag_metric_rust, m)?)?;
    m.add_function(wrap_pyfunction!(observability::generate_prometheus_metrics_rust, m)?)?;

    // Axum Web Server API Gateway
    m.add_function(wrap_pyfunction!(server::start_rust_axum_server, m)?)?;

    Ok(())
}

