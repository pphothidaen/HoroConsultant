/*!
 * rust_core/src/vector_search.rs
 * High-performance FAISS dense vector similarity search in Rust.
 */

use pyo3::prelude::*;
use rayon::prelude::*;

/// Parallel dense vector similarity search over embedding matrix.
/// Computes inner product (cosine similarity for normalized vectors) in parallel using Rayon.
#[pyfunction]
pub fn dense_vector_search(
    query_vec: Vec<f32>,
    doc_matrix: Vec<Vec<f32>>,
    top_k: usize,
    threshold: f32,
) -> PyResult<Vec<(usize, f32)>> {
    if query_vec.is_empty() || doc_matrix.is_empty() {
        return Ok(Vec::new());
    }

    let q_len = query_vec.len();

    let mut scored: Vec<(usize, f32)> = doc_matrix
        .par_iter()
        .enumerate()
        .map(|(idx, doc_vec)| {
            let len = q_len.min(doc_vec.len());
            let mut dot = 0.0f32;
            for i in 0..len {
                dot += query_vec[i] * doc_vec[i];
            }
            (idx, dot)
        })
        .filter(|&(_, score)| score >= threshold)
        .collect();

    scored.sort_unstable_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
    scored.truncate(top_k);

    Ok(scored)
}
