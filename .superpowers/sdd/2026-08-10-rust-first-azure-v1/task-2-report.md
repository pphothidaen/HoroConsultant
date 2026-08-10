# Task 2 Report: Rust Toolchain, Packaging, and Runtime Identity

## Status

DONE_WITH_CONCERNS

The Rust extension now has one deterministic installed-package path,
`rust_core._native`. Production import fails when that native module is absent;
Python fallback is available only when `HORO_ALLOW_PYTHON_FALLBACK=1`.
`runtime_backend()` returns native availability, crate version, and active kernel
names without environment values or secrets.

## RED evidence

### Python import and fallback contracts

Command:

```text
python3 -m pytest project/tests/test_rust_extensions.py \
  -k 'import_order or source_tree_native or missing_native or explicit_fallback' -q
```

Initial result:

```text
F.FF
3 failed, 1 passed, 13 deselected

AttributeError: module 'project.core.fast_math' has no attribute 'runtime_backend'
AssertionError: assert 0 != 0
AttributeError: module 'rust_core' has no attribute 'runtime_backend'
```

The source-artifact discovery test was then tightened to observe real
`os.scandir` audit events caused by recursive discovery. Its RED result was:

```text
FAILED test_source_tree_native_artifact_is_not_discovered
Left contains 12 more items ...
1 failed, 16 deselected
```

This proves the old initializer traversed unrelated source directories while
searching for host shared libraries.

### Rust test/link safety contract

Command against the original always-on PyO3 extension feature:

```text
PATH=/Users/kimlenglim/.agy-account-1/.rustup/toolchains/stable-aarch64-apple-darwin/bin:$PATH \
PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 \
cargo test --manifest-path rust_core/Cargo.toml --test test_runtime_contract
```

Initial result:

```text
error: linking with `cc` failed
Undefined symbols for architecture arm64: _PyBool_Type, _PyBytes_AsString, ...
error: could not compile `rust_core` (lib) due to 1 previous error
```

The always-enabled `pyo3/extension-module` feature prevented normal Rust test
linking on macOS. The new test target also introduced runtime identity and real
vector-search behavior assertions that were absent from the prior Rust suite.

## Implementation

- Added `rust_core/pyproject.toml` for a mixed maturin project with
  `python-source = ".."` and `module-name = "rust_core._native"`.
- Added an abi3 Python 3.10+ wheel boundary and separated `python`,
  `python-extension`, and `server` Cargo features.
- Made the no-default library compile without PyO3 or server dependencies.
- Changed release panic behavior from `abort` to `unwind`; added a
  `catch_unwind` test for test-process safety.
- Renamed the PyO3 initializer to `_native`, exported crate version and the
  active kernel list, and added Rust runtime identity.
- Replaced recursive `sys.path` shared-library scanning with the single
  package-relative import `rust_core._native`.
- Removed `fast_math.py` path mutation and silent production fallback.
- Preserved the public `rust_core` API by re-exporting native public symbols.
- Deleted the three tracked macOS host binaries:
  `rust_core.cpython-311-darwin.so`, `rust_core.cpython-314-darwin.so`, and
  `rust_core.so`.

## GREEN evidence

### Source-tree fallback contracts

```text
HORO_ALLOW_PYTHON_FALLBACK=1 \
python3 -m pytest project/tests/test_rust_extensions.py -q

13 passed, 4 skipped in 0.66s
```

The four skips are native-only SVG, audit, security, and observability tests;
they execute in the installed-wheel run below.

### Pure core and Rust behavior

```text
PATH=/Users/kimlenglim/.agy-account-1/.rustup/toolchains/stable-aarch64-apple-darwin/bin:$PATH \
cargo check --manifest-path rust_core/Cargo.toml --lib --no-default-features

Finished `dev` profile ...
```

```text
PATH=/Users/kimlenglim/.agy-account-1/.rustup/toolchains/stable-aarch64-apple-darwin/bin:$PATH \
cargo test --manifest-path rust_core/Cargo.toml --no-default-features \
  --features python --test test_runtime_contract --test test_vector_search

test result: ok. 3 passed; 0 failed
test result: ok. 2 passed; 0 failed
```

### Server feature check

```text
PATH=/Users/kimlenglim/.agy-account-1/.rustup/toolchains/stable-aarch64-apple-darwin/bin:$PATH \
cargo check --manifest-path rust_core/Cargo.toml --no-default-features \
  --features server --bin horo_server

Finished `dev` profile ...
```

### Clean wheel build and isolated installation

Build command:

```text
PATH=/Users/kimlenglim/.agy-account-1/.rustup/toolchains/stable-aarch64-apple-darwin/bin:$PATH \
maturin build --manifest-path rust_core/Cargo.toml --release --out "$wheel_tmp/wheels"
```

Result:

```text
Building a mixed python/rust project
Found CPython 3.14
Found pyo3 bindings with abi3-py3.10 support
Built wheel .../rust_core-0.1.0-cp310-abi3-macosx_11_0_arm64.whl
```

The wheel was installed with `pip --no-deps` into a newly created temporary
virtual environment. Native smoke assertions passed for package origin,
version, kernel identity, cosine similarity, and equation of time. The loaded
origin was:

```text
.../venv/lib/python3.14/site-packages/rust_core/_native.abi3.so
```

Automated installed-wheel import-order contract:

```text
HORO_PROJECT_ROOT=<worktree> <venv>/bin/python \
  rust_core/tests/test_installed_wheel.py -v

Ran 1 test in 0.863s
OK
```

Focused Python tests against the installed wheel, from `/tmp` with importlib
test mode:

```text
17 passed in 1.32s
```

## Files

- `rust_core/Cargo.toml`
- `rust_core/pyproject.toml`
- `rust_core/src/lib.rs`
- `rust_core/__init__.py`
- `project/core/fast_math.py`
- `project/tests/test_rust_extensions.py`
- `rust_core/tests/test_runtime_contract.rs`
- `rust_core/tests/test_installed_wheel.py`
- Deleted tracked `rust_core/*.so`

## Commit

Commit message: `build: make Rust packaging deterministic`

Commit hash: populated after commit in the task handoff.

## Concerns

- The existing engine source modules place PyO3 imports and `#[pyfunction]`
  attributes directly beside pure Rust kernels. The no-default library is now
  PyO3-free, and server dependencies are excluded from the Python wheel, but
  the current `server` feature must compose `python` to compile those engine
  modules. Making the standalone server fully PyO3-free requires separating
  bindings from algorithms across the engine modules, which was outside this
  task's assigned file ownership.
- PyO3 remains at 0.21 and uses `abi3-py310`; the wheel was successfully loaded
  by CPython 3.14, but a future PyO3 upgrade should be handled as a separate,
  compatibility-tested dependency change.

## Fix Round 1

### Reviewer findings addressed

1. The computational modules and their non-Python dependencies now compile
   without features. Every PyO3 import and wrapper is gated by `python`, while
   pure Rust kernels remain available without it.
2. The `server` feature now enables only Tokio, Axum, and Reqwest. It does not
   enable `python` or include PyO3 in its dependency graph.
3. `fast_math` now routes every accelerated call through one strict kernel
   resolver. A loaded native module missing a requested kernel raises in
   production and may fall back only with `HORO_ALLOW_PYTHON_FALLBACK=1`.
4. The standard wheel uses the composite `python-extension` plus `server`
   feature set and preserves `start_rust_axum_server` in both the public module
   and reported active kernel list.
5. CI pins maturin 1.14.1, tests the featureless core, tests the PyO3-free
   server target, audits the server dependency tree, builds and installs the
   wheel, and runs its installed-wheel contract.
6. A pure `equation_of_time_rust` function and literal behavior assertion were
   added so the no-feature core exposes and tests real solar math in addition
   to vector search.

### Round 1 RED evidence

Partial-native production behavior:

```text
python3 -m pytest project/tests/test_rust_extensions.py -k partial_native -q

FAILED test_partial_native_module_fails_without_explicit_fallback
assert 0 != 0
stdout="('เมถุน', 2)"
1 failed, 17 deselected
```

Installed standard-wheel server entrypoint:

```text
HORO_PROJECT_ROOT=<worktree> <old-venv>/bin/python \
  rust_core/tests/test_installed_wheel.py -v

FAIL: test_standard_wheel_exports_axum_server_entrypoint
AssertionError: False is not true
```

CI and reproducible maturin configuration:

```text
python3 -m pytest project/tests/test_cicd_workflow.py \
  -k 'rust_ci or maturin' -q

2 failed, 2 deselected
```

Featureless core test target:

```text
cargo test --manifest-path rust_core/Cargo.toml --no-default-features \
  --test test_runtime_contract

error: target `test_runtime_contract` ... requires the features: `python`
```

Server dependency audit:

```text
cargo tree --manifest-path rust_core/Cargo.toml --no-default-features \
  --features server -e normal | rg pyo3

├── pyo3 v0.21.2
│   ├── pyo3-ffi v0.21.2
│   └── pyo3-macros v0.21.2
```

Pure solar kernel assertion:

```text
cargo test --manifest-path rust_core/Cargo.toml --no-default-features \
  --test test_runtime_contract featureless_solar_kernel_has_real_behavior

error[E0425]: cannot find function `equation_of_time_rust` in module
`rust_core::solar`
```

### Round 1 GREEN evidence

Featureless core behavior:

```text
cargo test --manifest-path rust_core/Cargo.toml --no-default-features \
  --test test_runtime_contract --test test_vector_search

test result: ok. 4 passed; 0 failed
test result: ok. 2 passed; 0 failed
```

PyO3-free server boundary:

```text
cargo test --manifest-path rust_core/Cargo.toml --no-default-features \
  --features server --bin horo_server

test result: ok. 0 passed; 0 failed

cargo tree --manifest-path rust_core/Cargo.toml --no-default-features \
  --features server -e normal | rg pyo3

[no matches]
```

All-feature composite check:

```text
cargo check --manifest-path rust_core/Cargo.toml --all-features

Finished `dev` profile ...
```

Python source and CI contracts:

```text
HORO_ALLOW_PYTHON_FALLBACK=1 python3 -m pytest \
  project/tests/test_rust_extensions.py project/tests/test_cicd_workflow.py -q

18 passed, 4 skipped
```

The skips are native-only tests and run against the installed wheel below.

Pinned composite wheel build and clean installation:

```text
maturin build --manifest-path rust_core/Cargo.toml --release --out "$fix_tmp/wheels"

Using build options features, bindings from pyproject.toml
Built wheel .../rust_core-0.1.0-cp310-abi3-macosx_11_0_arm64.whl
```

```text
HORO_PROJECT_ROOT=<worktree> <new-venv>/bin/python \
  rust_core/tests/test_installed_wheel.py -v

Ran 2 tests in 1.206s
OK
```

The two tests verify deterministic import order, package-local native origin,
native runtime identity, and the Axum server entrypoint symbol/identity.

Focused Python extension tests against that installed wheel:

```text
18 passed in 1.15s
```

### Round 1 files

- `.github/workflows/ci.yml`
- `project/core/fast_math.py`
- `project/tests/test_cicd_workflow.py`
- `project/tests/test_rust_extensions.py`
- `rust_core/Cargo.toml`
- `rust_core/pyproject.toml`
- `rust_core/src/*.rs` binding/core boundary cfg changes
- `rust_core/tests/test_installed_wheel.py`
- `rust_core/tests/test_runtime_contract.rs`

### Round 1 commit

Commit message: `fix: separate Rust core from PyO3 bindings`

### Round 1 concerns

No blocking concern remains from the Critical or Important findings. PyO3 0.21
continues to use the tested `abi3-py310` compatibility boundary; upgrading PyO3
remains a separate dependency migration.
