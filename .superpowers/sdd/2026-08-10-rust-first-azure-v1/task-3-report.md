# Task 3 Report: BaZi and True Solar Time Parity

## Status

QUALIFIED_NOT_PROMOTED

The pure Rust BaZi and true-solar-time kernels now reproduce the canonical
Python chart schema and deterministic behavior. Both ROI thresholds passed.
No gateway, runtime-routing, Python-oracle, deployment, CI, or documentation
source was changed; routing promotion remains a later task.

## RED evidence

### Full chart and true-solar-time API

The first literal Rust fixtures were written before production changes.

```text
cargo test --manifest-path rust_core/Cargo.toml --no-default-features \
  --test test_bazi_parity

error[E0432]: unresolved imports `rust_core::bazi::calculate_bazi`,
`rust_core::bazi::BaziInput`
error[E0432]: unresolved import
`rust_core::solar::calculate_true_solar_time`
```

This proved the fixed-stem placeholder and integer-day EoT kernel could not
satisfy the complete response contract.

### Unknown-hour matrix

The initially uncovered implementation was backed out, then a literal
12-scenario test was added and observed failing:

```text
test unknown_hour_matches_literal_python_scenario_matrix ... FAILED
valid unknown-hour chart:
BaziError("unknown-hour scenario calculation is not implemented")
```

### Randomized cross-language rounding drift

The first explicit parity run found a real Python/Rust difference:

```text
test ten_thousand_cases_match_python_oracle ... FAILED
float mismatch at $[52].five_elements.percentages.Metal:
28.13 != 28.12
```

Python uses ties-to-even rounding. Rust's default half-away rounding was
replaced with ties-to-even rounding for serialized solar and element values.

### Feature-gated wrapper check

The first `--features python` check caught the f64 schema/f32 legacy-wrapper
boundary:

```text
error[E0308]: expected `HashMap<String, f32>`, found `HashMap<String, f64>`
```

The explicit compatibility conversion is feature-gated; the pure kernels
remain free of PyO3 under `--no-default-features`.

## Implementation

- Added validated `BaziInput`, complete serializable response types, and
  `calculate_bazi` without enabling a production route.
- Ported Li Chun year selection, solar-month boundaries, Five Tigers, Julian
  day pillars, double-hour boundaries, Five Rats, and TST date rollover.
- Ported all hidden stems, their weights, branch season selection, seasonal
  multipliers, scores, percentages, dominant/weakest selection, and the
  12-scenario unknown-hour matrix.
- Ported fractional-year NOAA Spencer EoT, leap-year length, standard meridian,
  longitude correction, Local Mean Time, and True Solar Time.
- Replaced the fixed four-pillar compatibility output with real pillar math.
- Added literal Bangkok, Singapore, Li Chun, leap-day, timezone-extreme, and
  cross-midnight fixtures in Rust and Python tests.
- Added an explicit deterministic 10,000-case full-schema oracle runner with
  seed `3122737190` and a normal deterministic 100,000-input invalid/fuzz test.
- Kept all PyO3 imports/functions behind `cfg(feature = "python")`.

## GREEN evidence

### Focused Rust suite and invalid/fuzz gate

```text
cargo test --manifest-path rust_core/Cargo.toml --no-default-features \
  --test test_bazi_parity

7 passed; 0 failed; 2 ignored; finished in 0.04s
```

The normal suite includes all 100,000 invalid/fuzz inputs under
`catch_unwind`; no input panicked, aborted, or returned success.

### Explicit 10,000-case parity gate

```text
cargo test --manifest-path rust_core/Cargo.toml --no-default-features \
  --test test_bazi_parity ten_thousand_cases_match_python_oracle -- \
  --ignored --exact --nocapture

test ten_thousand_cases_match_python_oracle ... ok
1 passed; 0 failed; finished in 1.86s
```

Every complete response was recursively compared after removing only the
nondeterministic calculation timestamp. Categorical/integer/schema values were
exact; floats used the required `1e-6` tolerance. The oracle process forcibly
sets `project.core.fast_math.RUST_AVAILABLE = False`, so an installed native
wheel cannot make this comparison circular.

### Python oracle fixtures

```text
HORO_ALLOW_PYTHON_FALLBACK=1 \
python3 -m pytest project/tests/test_bazi_calculator.py -q

37 passed in 0.80s
```

### Feature boundaries

```text
cargo check --manifest-path rust_core/Cargo.toml --lib --no-default-features
Finished `dev` profile

PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 \
cargo check --manifest-path rust_core/Cargo.toml --lib \
  --no-default-features --features python
Finished `dev` profile
```

## Complete request-work benchmark

The ignored release benchmark feeds the identical 2,000 serialized requests to
both implementations and measures request JSON decode, complete engine
calculation, and response JSON encode. It does not measure an isolated FFI call
or network transport. The test fails instead of qualifying the engine if either
threshold is missed.

```text
cargo test --release --manifest-path rust_core/Cargo.toml \
  --no-default-features --test test_bazi_parity \
  benchmark_complete_calculation_reports_roi_gates -- \
  --ignored --exact --nocapture

[INFO] BAZI_ROI decision=QUALIFIED
rust_p95_ns=4625 python_p95_ns=52250 p95_improvement=91.15%
rust_cpu_per_request_ns=5313 python_cpu_per_request_ns=48252
cpu_reduction=88.99%
```

Required gates:

- p95 improvement at least 20%: PASS (91.15%).
- CPU/request reduction at least 30%: PASS (88.99%).

Decision: QUALIFIED. Task 3 changes no routing, so production promotion is
deferred to the gateway/routing task and is not implied by this result.

## Concerns

- The canonical known-hour Python response currently includes a zero-valued
  legacy `element_scores` object in addition to `five_elements`; Rust preserves
  that schema for parity.
- A crate-wide strict Clippy run still reports the pre-existing
  `clippy::let_and_return` finding in `rust_core/src/swisseph.rs`, outside Task 3
  ownership. The focused Task 3 Clippy run passes when that known baseline lint
  is allowed.

## Review resolution

Read-only review found no critical kernel defects. Its two important harness
findings were resolved before handoff:

- The Python oracle now forcibly disables native dispatch even when a wheel is
  installed.
- Both benchmark sides now receive the identical serialized corpus, and a
  missed p95 or CPU/request threshold fails the qualification test.
