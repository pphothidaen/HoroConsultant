# rust_core - Scoped Agent Instructions

## Scope & Precedence
- Governs native Rust extensions in `rust_core/` (PyO3 bindings, Rayon parallel concurrency, mathematical kernels).
- Root Universal Safeguards Precedence: Root `AGENTS.md`, `.agents/rules/`, and repository safety mandates strictly supersede this document.
- Cargo Dependencies: Ensure `Cargo.lock` is deterministically managed without unvetted crates.

## PyO3 FFI Boundary Safety
- Enforce strict memory and thread safety across the Python-Rust FFI boundary.
- Zero-panic contract: handle all errors via Rust `Result<T, PyErr>` and never invoke `panic!`, `unwrap()`, or `expect()` across FFI.
- Keep PyO3 exported functions, classes, and parameter types in exact alignment with `project/core`.
- Maintain ABI compatibility with the `abi3-py310` stable extension interface.
- Keep memory ownership unambiguous when converting between Rust data types and Python objects.
- Never leak raw pointers across language boundaries; enforce idiomatic RAII lifetimes.
- Propagate descriptive Python exceptions (`PyValueError`, `PyRuntimeError`) for invalid inputs.

## Rayon Multithreading & Concurrency
- Accelerate heavy calculations (ephemeris batches, matrix transformations) using `rayon::prelude::*`.
- Ensure all closure captures and shared state conform to `Send + Sync`.
- Release the Python GIL using `Python::allow_threads` during compute-intensive multithreaded iterations.
- Balance iterator batch sizing to avoid thread contention or thread pool starvation.
- Ensure parallel loops remain pure, deterministic, and free of side effects.
- Respect host CPU constraints and configure thread pools gracefully for CI environments.

## Testing & Quality Gates
- Always execute `cargo test` in `rust_core/` before code review handoff or release verification.
- Verify both native unit tests and Python bindings integration in `tests/test_fast_math.py`.
- Maintain 100% deterministic mathematical calculations matching Swiss Ephemeris golden standards.
- Run `cargo clippy --all-targets` to prevent common Rust pitfalls, unhandled errors, or unintended leaks.
- Validate release builds with `maturin develop --release` when testing end-to-end performance.
