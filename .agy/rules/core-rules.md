---
description: Astronomical algorithms, NOAA Spencer 1971, BaZi calculations, and deterministic math integrity.
paths: "project/core/**/*, rust_core/**/*"
---

# Core Astrological & Deterministic Math Governance

## Mathematical Integrity & NOAA Solar Engine
- True Solar Time calculations must adhere strictly to NOAA Spencer 1971 formulas.
- Astronomical ephemeris calculations must be 100% deterministic with zero floating-point drift.
- All core functions must be pure, immutable, and side-effect free.

<important if="modifying_ephemeris">
- Do not alter astronomical constant definitions (e.g. Obliquity of Ecliptic, Solar Declination constants).
- Validate calculations against Swiss Ephemeris golden datasets in `tests/test_solar_time.py`.
- Rust PyO3 bindings must match Python core API signatures precisely.
</important>

<important if="refactoring_core">
- Enforce pure function immutability.
- Do not introduce circular package dependencies between `project.core` and `project.rag`.
</important>
