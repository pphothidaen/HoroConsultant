# rust_core/ — Claude Code & AGY Contract

## Build Commands
```bash
cd rust_core
cargo build --locked --release --no-default-features --features server
maturin build --locked --release --out wheelhouse
cargo test --all-targets
```

## CI Checks
- `cargo fmt --all -- --check`
- `cargo clippy --all-targets -- -D warnings`
