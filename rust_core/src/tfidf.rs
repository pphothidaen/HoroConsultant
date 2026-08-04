/*!
 * rust_core/src/tfidf.rs
 * High-performance TF-IDF vector math and batch cosine similarity search.
 */

use pyo3::prelude::*;
use rayon::prelude::*;

#[pyfunction]
pub fn cosine_similarity(a: Vec<f32>, b: Vec<f32>) -> PyResult<f32> {
    if a.len() != b.len() || a.is_empty() {
        return Ok(0.0);
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
    Ok(dot / norm)
}

#[pyfunction]
pub fn batch_cosine_search(
    query_vec: Vec<f32>,
    doc_matrix: Vec<Vec<f32>>,
    top_k: usize,
    threshold: f32,
) -> PyResult<Vec<(usize, f32)>> {
    if query_vec.is_empty() || doc_matrix.is_empty() {
        return Ok(Vec::new());
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

    Ok(scored_docs)
}

#[pyfunction]
pub fn build_tfidf_vector(text: &str, vocab: Vec<String>) -> PyResult<Vec<f32>> {
    let mut vec = vec![0.0f32; vocab.len()];
    let chars: Vec<char> = text.chars().collect();
    if chars.is_empty() {
        return Ok(vec);
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

    Ok(vec)
}

#[pyfunction]
pub fn build_tfidf_matrix(texts: Vec<String>, vocab: Vec<String>) -> PyResult<Vec<Vec<f32>>> {
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

    Ok(matrix)
}
