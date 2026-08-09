/*!
 * rust_core/src/tfidf.rs
 * High-performance TF-IDF vector math and batch cosine similarity search.
 */

use pyo3::prelude::*;
use rayon::prelude::*;

#[pyfunction]
pub fn cosine_similarity(py: Python<'_>, a: Vec<f32>, b: Vec<f32>) -> PyResult<f32> {
    let result = py.allow_threads(move || {
        if a.len() != b.len() || a.is_empty() {
            return 0.0;
        }
        let mut dot = 0.0f32;
        let mut norm_a = 0.0f32;
        let mut norm_b = 0.0f32;

        for i in 0..a.len() {
            dot += a[i] * b[i];
            norm_a += a[i] * a[i];
            norm_b += b[i] * b[i];
        }

        let norm = (norm_a.sqrt() * norm_b.sqrt()).max(1e-9);
        dot / norm
    });
    Ok(result)
}

#[pyfunction]
pub fn batch_cosine_search(
    py: Python<'_>,
    query_vec: Vec<f32>,
    doc_matrix: Vec<Vec<f32>>,
    top_k: usize,
    threshold: f32,
) -> PyResult<Vec<(usize, f32)>> {
    let result = py.allow_threads(move || {
        if query_vec.is_empty() || doc_matrix.is_empty() {
            return Vec::new();
        }

        // Parallel cosine calculation using Rayon
        let mut scored_docs: Vec<(usize, f32)> = doc_matrix
            .par_iter()
            .enumerate()
            .map(|(idx, doc_vec)| {
                let mut dot = 0.0f32;
                let len = query_vec.len().min(doc_vec.len());
                for i in 0..len {
                    dot += query_vec[i] * doc_vec[i];
                }
                (idx, dot)
            })
            .filter(|&(_, score)| score >= threshold)
            .collect();

        // Sort descending by score
        scored_docs.sort_unstable_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
        scored_docs.truncate(top_k);

        scored_docs
    });
    Ok(result)
}

#[pyfunction]
pub fn build_tfidf_vector(py: Python<'_>, text: String, vocab: Vec<String>) -> PyResult<Vec<f32>> {
    let result = py.allow_threads(move || {
        let mut vec = vec![0.0f32; vocab.len()];
        let chars: Vec<char> = text.chars().collect();
        if chars.is_empty() {
            return vec;
        }

        for (idx, word) in vocab.iter().enumerate() {
            let count = text.matches(word).count() as f32;
            vec[idx] = count;
        }

        let norm: f32 = vec.iter().map(|x| x * x).sum::<f32>().sqrt();
        if norm > 0.0 {
            for val in vec.iter_mut() {
                *val /= norm;
            }
        }

        vec
    });
    Ok(result)
}

#[pyfunction]
pub fn build_tfidf_matrix(py: Python<'_>, texts: Vec<String>, vocab: Vec<String>) -> PyResult<Vec<Vec<f32>>> {
    let result = py.allow_threads(move || {
        let matrix: Vec<Vec<f32>> = texts
            .par_iter()
            .map(|text| {
                let mut vec = vec![0.0f32; vocab.len()];
                for (idx, word) in vocab.iter().enumerate() {
                    let count = text.matches(word).count() as f32;
                    vec[idx] = count;
                }
                let norm: f32 = vec.iter().map(|x| x * x).sum::<f32>().sqrt();
                if norm > 0.0 {
                    for val in vec.iter_mut() {
                        *val /= norm;
                    }
                }
                vec
            })
            .collect();
        matrix
    });
    Ok(result)
}
