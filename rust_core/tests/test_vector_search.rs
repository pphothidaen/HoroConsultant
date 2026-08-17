/*!
 * rust_core/tests/test_vector_search.rs
 * Native Rust test suite for FAISS dense vector search & Security Audit.
 */

#[test]
fn test_rust_dense_vector_search() {
    let query_vec = vec![1.0, 0.0, 0.0];
    let doc_matrix = vec![
        vec![1.0, 0.0, 0.0],
        vec![0.0, 1.0, 0.0],
        vec![0.8, 0.6, 0.0],
    ];

    let hits = rust_core::vector_search::dense_vector_search_rust(&query_vec, &doc_matrix, 2, 0.0);
    assert_eq!(hits.len(), 2);
    assert_eq!(hits[0].0, 0); // Perfect match index
    assert!((hits[0].1 - 1.0).abs() < 1e-3);
    assert_eq!(hits[1].0, 2); // 0.8 dot product index
}

#[test]
fn test_rust_security_audit_scanner() {
    let (passed, scanned_count, findings) =
        rust_core::security_audit::scan_directory_secrets_rust(".").unwrap();
    assert!(scanned_count > 0);
    assert!(passed || !findings.is_empty());
}
