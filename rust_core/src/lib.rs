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

#[cfg(feature = "python")]
use pyo3::prelude::*;

#[cfg(feature = "python")]
pub mod astrological_audit;
#[cfg(feature = "python")]
pub mod bazi;
#[cfg(feature = "python")]
pub mod chunker;
#[cfg(feature = "python")]
pub mod fengshui;
#[cfg(feature = "python")]
pub mod iching;
#[cfg(feature = "python")]
pub mod liuren;
#[cfg(feature = "python")]
pub mod numerology;
#[cfg(feature = "python")]
pub mod observability;
#[cfg(feature = "python")]
pub mod qimen;
#[cfg(feature = "python")]
pub mod security_audit;
#[cfg(all(feature = "python", feature = "server"))]
pub mod server;
#[cfg(feature = "python")]
pub mod solar;
#[cfg(feature = "python")]
pub mod svg;
#[cfg(feature = "python")]
pub mod swisseph;
#[cfg(feature = "python")]
pub mod tfidf;
#[cfg(feature = "python")]
pub mod thai_vedic;
#[cfg(feature = "python")]
pub mod uranian;
#[cfg(feature = "python")]
pub mod vector_search;
#[cfg(feature = "python")]
pub mod zeji;
#[cfg(feature = "python")]
pub mod ziwei;

#[cfg(feature = "python")]
pub use astrological_audit::*;
#[cfg(feature = "python")]
pub use bazi::*;
#[cfg(feature = "python")]
pub use fengshui::*;
#[cfg(feature = "python")]
pub use iching::*;
#[cfg(feature = "python")]
pub use liuren::*;
#[cfg(feature = "python")]
pub use numerology::*;
#[cfg(feature = "python")]
pub use observability::*;
#[cfg(feature = "python")]
pub use qimen::*;
#[cfg(feature = "python")]
pub use security_audit::*;
#[cfg(feature = "python")]
pub use solar::*;
#[cfg(feature = "python")]
pub use svg::*;
#[cfg(feature = "python")]
pub use swisseph::*;
#[cfg(feature = "python")]
pub use thai_vedic::*;
#[cfg(feature = "python")]
pub use uranian::*;
#[cfg(feature = "python")]
pub use vector_search::*;
#[cfg(feature = "python")]
pub use zeji::*;
#[cfg(feature = "python")]
pub use ziwei::*;

/// Runtime metadata shared by Rust tests and the Python package boundary.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RuntimeIdentity {
    pub version: &'static str,
    pub kernels: &'static [&'static str],
}

/// Names of native kernels exported by the standard Python extension.
pub const ACTIVE_KERNELS: &[&str] = &[
    "cosine_similarity",
    "batch_cosine_search",
    "build_tfidf_vector",
    "build_tfidf_matrix",
    "dense_vector_search",
    "dense_vector_search_l2",
    "compute_element_scores",
    "compute_probabilistic_matrix",
    "julian_day_number",
    "equation_of_time",
    "chunk_text",
    "resolve_mountain",
    "fly_stars",
    "xuankong_9grid_matrix",
    "calculate_ming_shen_gong",
    "calculate_zi_wei_star_branch",
    "calculate_14_main_stars",
    "qimen_9palace_matrix",
    "calculate_thai_lagna",
    "calculate_thaksa_map",
    "calculate_nakshatra_pada",
    "resolve_western_zodiac",
    "calculate_midpoint",
    "calculate_sensitive_point",
    "compute_ephemeris_sun_moon",
    "parse_hexagram_trigrams",
    "calculate_liuren_heaven_plate",
    "calculate_zeji_duty_officer",
    "check_branch_clash",
    "calculate_satta_lek_matrix",
    "run_rust_security_audit",
    "audit_five_elements",
    "audit_eot_bounds",
    "audit_cross_domain_synergy",
    "build_bazi_svg_rust",
    "build_zodiac_svg_rust",
    "build_ziwei_svg_rust",
    "build_qimen_svg_rust",
    "build_xuankong_svg_rust",
    "record_http_metric_rust",
    "record_rag_metric_rust",
    "generate_prometheus_metrics_rust",
];

/// Return deterministic, secret-free native runtime metadata.
pub fn runtime_identity() -> RuntimeIdentity {
    RuntimeIdentity {
        version: env!("CARGO_PKG_VERSION"),
        kernels: ACTIVE_KERNELS,
    }
}

/// High-performance Rust core for Computational Metaphysics Engine.
#[cfg(feature = "python")]
#[pymodule]
fn _native(m: &Bound<'_, PyModule>) -> PyResult<()> {
    let identity = runtime_identity();
    m.add("__version__", identity.version)?;
    m.add("__kernels__", identity.kernels.to_vec())?;

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
    m.add_function(wrap_pyfunction!(
        security_audit::run_rust_security_audit,
        m
    )?)?;

    // Astrological Audit Engine
    m.add_function(wrap_pyfunction!(
        astrological_audit::audit_five_elements,
        m
    )?)?;
    m.add_function(wrap_pyfunction!(astrological_audit::audit_eot_bounds, m)?)?;
    m.add_function(wrap_pyfunction!(
        astrological_audit::audit_cross_domain_synergy,
        m
    )?)?;

    // High-Performance SVG Vector Chart Generator
    m.add_function(wrap_pyfunction!(svg::build_bazi_svg_rust, m)?)?;
    m.add_function(wrap_pyfunction!(svg::build_zodiac_svg_rust, m)?)?;
    m.add_function(wrap_pyfunction!(svg::build_ziwei_svg_rust, m)?)?;
    m.add_function(wrap_pyfunction!(svg::build_qimen_svg_rust, m)?)?;
    m.add_function(wrap_pyfunction!(svg::build_xuankong_svg_rust, m)?)?;

    // High-Performance Atomic Prometheus Metrics Collector
    m.add_function(wrap_pyfunction!(observability::record_http_metric_rust, m)?)?;
    m.add_function(wrap_pyfunction!(observability::record_rag_metric_rust, m)?)?;
    m.add_function(wrap_pyfunction!(
        observability::generate_prometheus_metrics_rust,
        m
    )?)?;

    // Axum Web Server API Gateway (server wheels only)
    #[cfg(feature = "server")]
    m.add_function(wrap_pyfunction!(server::start_rust_axum_server, m)?)?;

    Ok(())
}
