# rust_core/ — Rust PyO3 High-Performance Math Core

## Purpose
Rust-based high-performance computation engine exposed to Python via PyO3.

## Key Files
- `rust_core/Cargo.toml` — Rust package manifest
- `rust_core/src/` — Rust source code
- `rust_core/tests/` — Rust unit tests
- `rust_core/pyproject.toml` — Maturin build config

## Build
```bash
cd rust_core
cargo build --locked --release --no-default-features --features server
maturin build --locked --release --out wheelhouse
```

## Features
- `server` — Axum-based HTTP server (no PyO3 dependency)
- Default — Python bindings via PyO3

## CI
- `cargo fmt --all -- --check` — Formatting
- `cargo clippy --all-targets -- -D warnings` — Linting
- `cargo test --all-targets` — Tests
