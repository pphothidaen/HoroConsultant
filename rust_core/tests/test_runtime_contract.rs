/*!
 * Runtime packaging contract tests for the Rust library and PyO3 boundary.
 */

#[test]
fn runtime_identity_lists_real_exported_kernels() {
    let identity = rust_core::runtime_identity();

    assert_eq!(identity.version, env!("CARGO_PKG_VERSION"));
    assert!(identity.kernels.contains(&"cosine_similarity"));
    assert!(identity.kernels.contains(&"equation_of_time"));
    assert!(identity.kernels.contains(&"chunk_text"));
}

#[test]
fn exported_vector_search_kernel_has_real_behavior() {
    let query = vec![1.0, 0.0];
    let documents = vec![vec![0.0, 1.0], vec![1.0, 0.0]];
    let hits = rust_core::vector_search::dense_vector_search_rust(&query, &documents, 2, 0.0);

    assert_eq!(hits, vec![(1, 1.0), (0, 0.0)]);
}

#[test]
fn featureless_solar_kernel_has_real_behavior() {
    let equation_minutes = rust_core::solar::equation_of_time_rust(1);

    assert!((equation_minutes + 2.904).abs() < 0.01);
}

#[test]
fn panics_unwind_in_tests_instead_of_aborting_the_process() {
    let panic_result = std::panic::catch_unwind(|| panic!("test panic"));

    assert!(panic_result.is_err());
}

#[cfg(feature = "server")]
#[test]
fn server_feature_exposes_pure_library_entrypoint() {
    let _entrypoint = rust_core::server::run_rust_axum_server;
}
