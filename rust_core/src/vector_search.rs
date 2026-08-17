/*!
 * rust_core/src/vector_search.rs
 * High-performance FAISS dense vector similarity search in Rust.
 * Supports Parallel Dot Product (Cosine Similarity) & L2 Euclidean Distance with SIMD auto-vectorization.
 */

#[cfg(feature = "python")]
use pyo3::prelude::*;
use rayon::prelude::*;

/// SIMD-friendly dot product calculation (Cosine Similarity for unit vectors).
#[inline(always)]
fn dot_product_simd(a: &[f32], b: &[f32]) -> f32 {
    let len = a.len().min(b.len());
    let mut sum = 0.0f32;
    // Chunk in groups of 8 for auto-vectorization
    let chunks = len / 8;
    for c in 0..chunks {
        let i = c * 8;
        sum += a[i] * b[i]
            + a[i + 1] * b[i + 1]
            + a[i + 2] * b[i + 2]
            + a[i + 3] * b[i + 3]
            + a[i + 4] * b[i + 4]
            + a[i + 5] * b[i + 5]
            + a[i + 6] * b[i + 6]
            + a[i + 7] * b[i + 7];
    }
    for i in (chunks * 8)..len {
        sum += a[i] * b[i];
    }
    sum
}

/// SIMD-friendly squared L2 Euclidean distance calculation.
#[inline(always)]
#[cfg(feature = "python")]
fn l2_squared_simd(a: &[f32], b: &[f32]) -> f32 {
    let len = a.len().min(b.len());
    let mut sum = 0.0f32;
    let chunks = len / 8;
    for c in 0..chunks {
        let i = c * 8;
        let d0 = a[i] - b[i];
        let d1 = a[i + 1] - b[i + 1];
        let d2 = a[i + 2] - b[i + 2];
        let d3 = a[i + 3] - b[i + 3];
        let d4 = a[i + 4] - b[i + 4];
        let d5 = a[i + 5] - b[i + 5];
        let d6 = a[i + 6] - b[i + 6];
        let d7 = a[i + 7] - b[i + 7];
        sum += d0 * d0 + d1 * d1 + d2 * d2 + d3 * d3 + d4 * d4 + d5 * d5 + d6 * d6 + d7 * d7;
    }
    for i in (chunks * 8)..len {
        let d = a[i] - b[i];
        sum += d * d;
    }
    sum
}

/// Parallel dense vector similarity search over embedding matrix using Dot Product (Cosine Similarity).
pub fn dense_vector_search_rust(
    query_vec: &[f32],
    doc_matrix: &[Vec<f32>],
    top_k: usize,
    threshold: f32,
) -> Vec<(usize, f32)> {
    if query_vec.is_empty() || doc_matrix.is_empty() {
        return Vec::new();
    }

    let mut scored: Vec<(usize, f32)> = doc_matrix
        .par_iter()
        .enumerate()
        .map(|(idx, doc_vec)| {
            let dot = dot_product_simd(query_vec, doc_vec);
            (idx, dot)
        })
        .filter(|&(_, score)| score >= threshold)
        .collect();

    scored.sort_unstable_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
    scored.truncate(top_k);

    scored
}

#[cfg(feature = "python")]
#[pyfunction]
pub fn dense_vector_search(
    py: Python<'_>,
    query_vec: Vec<f32>,
    doc_matrix: Vec<Vec<f32>>,
    top_k: usize,
    threshold: f32,
) -> PyResult<Vec<(usize, f32)>> {
    let result = py
        .allow_threads(move || dense_vector_search_rust(&query_vec, &doc_matrix, top_k, threshold));
    Ok(result)
}

/// Parallel dense vector search using L2 Euclidean Distance.
#[cfg(feature = "python")]
#[pyfunction]
pub fn dense_vector_search_l2(
    py: Python<'_>,
    query_vec: Vec<f32>,
    doc_matrix: Vec<Vec<f32>>,
    top_k: usize,
    max_distance: f32,
) -> PyResult<Vec<(usize, f32)>> {
    let result = py.allow_threads(move || {
        if query_vec.is_empty() || doc_matrix.is_empty() {
            return Vec::new();
        }

        let max_sq = max_distance * max_distance;

        let mut scored: Vec<(usize, f32)> = doc_matrix
            .par_iter()
            .enumerate()
            .map(|(idx, doc_vec)| {
                let dist_sq = l2_squared_simd(&query_vec, doc_vec);
                (idx, dist_sq.sqrt())
            })
            .filter(|&(_, dist)| dist <= max_sq.sqrt())
            .collect();

        // Sort ascending by distance (smallest distance first)
        scored.sort_unstable_by(|a, b| a.1.partial_cmp(&b.1).unwrap_or(std::cmp::Ordering::Equal));
        scored.truncate(top_k);

        scored
    });
    Ok(result)
}
