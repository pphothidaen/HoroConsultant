/*!
 * rust_core/src/chunker.rs
 * Fast Unicode / CJK-aware text chunking.
 */

use pyo3::prelude::*;

#[pyfunction]
pub fn chunk_text(text: &str, chunk_size: usize, overlap: usize) -> PyResult<Vec<String>> {
    let chars: Vec<char> = text.chars().collect();
    let mut chunks = Vec::new();
    if chars.is_empty() || chunk_size == 0 {
        return Ok(chunks);
    }

    let step = if chunk_size > overlap { chunk_size - overlap } else { 1 };
    let mut start = 0;

    while start < chars.len() {
        let end = (start + chunk_size).min(chars.len());
        let chunk: String = chars[start..end].iter().collect();
        chunks.push(chunk);
        if end == chars.len() {
            break;
        }
        start += step;
    }

    Ok(chunks)
}
