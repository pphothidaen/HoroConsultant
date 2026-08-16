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

pub mod astrological_audit;
pub mod bazi;
pub mod astrological_audit;
pub mod bazi;
pub mod chunker;
pub mod fengshui;
pub mod iching;
pub mod liuren;
pub mod liu_yao;
pub mod meihua;
pub mod numerology;
pub mod observability;
pub mod qimen;
pub mod sanhe;
pub mod security_audit;
#[cfg(feature = "server")]
pub mod server;
pub mod solar;
pub mod svg;
pub mod swisseph;
pub mod tai_yi;
pub mod tfidf;
pub mod thai_vedic;
pub mod uranian;
pub mod vector_search;
pub mod zeji;
pub mod ziwei;

pub use astrological_audit::*;
pub use bazi::*;
pub use fengshui::*;
pub use iching::*;
pub use liuren::*;
pub use liu_yao::*;
pub use meihua::*;
pub use numerology::*;
#[cfg(feature = "python")]
pub use observability::*;
pub use qimen::*;
pub use sanhe::*;
pub use security_audit::*;
pub use solar::*;
#[cfg(feature = "python")]
pub use svg::*;
pub use swisseph::*;
pub use tai_yi::*;
pub use thai_vedic::*;
pub use uranian::*;
pub use vector_search::*;
pub use zeji::*;
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
    "mei_hua_hexagram_from_time",
    "san_he_resolve_mountain",
    "san_he_water_method",
    "tai_yi_accumulated_years",
    "tai_yi_star_palace",
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
    let mut active_kernels = identity.kernels.to_vec();
    #[cfg(feature = "server")]
    active_kernels.push("start_rust_axum_server");
    m.add("__version__", identity.version)?;
    m.add("__kernels__", active_kernels)?;

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
    m.add_function(wrap_pyfunction!(liu_yao::liu_yao_najia, m)?)?;
    m.add_function(wrap_pyfunction!(liu_yao::liu_yao_five_relatives, m)?)?;

    // Da Liu Ren
    m.add_function(wrap_pyfunction!(liuren::calculate_liuren_heaven_plate, m)?)?;

    // Imperial Calendar Date Selection (Ze Ji)
    m.add_function(wrap_pyfunction!(zeji::calculate_zeji_duty_officer, m)?)?;
    m.add_function(wrap_pyfunction!(zeji::check_branch_clash, m)?)?;

    // Numerology (Satta-Lek)
    m.add_function(wrap_pyfunction!(numerology::calculate_satta_lek_matrix, m)?)?;

    // Mei Hua Yi Shu (Plum Blossom)
    m.add_function(wrap_pyfunction!(meihua::mei_hua_hexagram_from_time, m)?)?;

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

    // San He
    m.add_function(wrap_pyfunction!(sanhe::san_he_resolve_mountain, m)?)?;
    m.add_function(wrap_pyfunction!(sanhe::san_he_water_method, m)?)?;

    // Tai Yi Engine
    m.add_function(wrap_pyfunction!(tai_yi::tai_yi_accumulated_years, m)?)?;
    m.add_function(wrap_pyfunction!(tai_yi::tai_yi_star_palace, m)?)?;

    Ok(())
}
