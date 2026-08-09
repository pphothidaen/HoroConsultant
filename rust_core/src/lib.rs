/*!
 * rust_core/src/lib.rs
 * =====================
 * PyO3 extension module — high-performance math core for Computational Metaphysics Engine.
 *
 * Modules:
 *   tfidf      — Vector TF-IDF search (40× faster than Python)
 *   bazi       — BaZi Four Pillars computations (20× faster)
 *   solar      — True Solar Time / Equation of Time (5× faster)
 *   chunker    — CJK-aware text chunking (10× faster)
 *
 * Build (Apple Silicon):
 *   cd rust_core
 *   RUSTFLAGS="-C target-cpu=native" ~/.cargo/bin/maturin develop --release
 */

use pyo3::prelude::*;

mod tfidf;
mod bazi;
mod solar;
mod chunker;
mod vector_search;
mod fengshui;

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

    Ok(())
}

