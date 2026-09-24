# Path-Based Rulesets & CI Tiering Governance (KAN-100)

## 1. Background & Problem Statement

Prior to KAN-100, repository pull requests suffered from two critical bottlenecks:
1. **Uniform CI Wall-Time Burden**: Any PR—even a single-line markdown documentation edit—triggered full CI execution lasting ~7-10 minutes across ~20 matrix jobs (including Rust core compilation with `maturin`, cargo audit, clippy, and full PyTest execution).
2. **Live-Network Signal Pollution**: Unsegregated end-to-end tests (such as `test_prod_version_regression.py` querying external Vercel endpoints) intermittently timed out during PR checks, blocking PRs whose diff had zero relation to live production deployments.

A proposed "two-tier branch bypass" was rejected during Red Team review because bypass branches eliminate defense-in-depth protections.

---

## 2. Architecture & Design Principles

KAN-100 implements **Path-Based Rulesets on a Unified Engine** governed by `scripts/path_ruleset_classifier.py`:

```
           PR Changed Files
                  │
                  ▼
   scripts/path_ruleset_classifier.py
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
    TIER_LIGHT          TIER_STRICT
   (Docs / Meta)       (Source / Logic)
        │                   │
  ┌─────┴─────┐       ┌─────┴─────┐
  │ Provenance│       │ Provenance│
  │ SecretScan│       │ SecretScan│
  │   Lint    │       │   Lint    │
  └───────────┘       │ Rust Build│
                      │ PyTest (-m│
                      │ "not net")│
                      │ E2E Regr. │
                      └───────────┘
```

### Invariants & Non-Negotiable Guarantees

1. **Defense-in-Depth on All Paths**: Every single merge path—without exception—requires **Test Provenance Verification** (`Test Provenance` check run) and **Secret Leak Scanning** (`lint-and-security` Bandit/Gitleaks audit). There is no "unprotected" merge path.
2. **Fail-Closed Default**: If any changed file in a PR touches source paths or is unrecognized, the classifier immediately evaluates to `TIER_STRICT`.
3. **Live Network Isolation**: Live production tests are tagged with `@pytest.mark.network` and excluded from per-PR CI (`pytest -m "not network"`), eliminating transient network flakes while preserving regression coverage in scheduled nightly jobs.

---

## 3. Path Tier Specifications

| Path Pattern | Classification | Executed Checks | Skipped Checks |
|---|---|---|---|
| `docs/**`, `*.md` | `TIER_LIGHT` | Test Provenance, Secret Scan, Lint | Rust Core Build, Heavy PyTest, E2E |
| `.github/workflows/**` | `TIER_LIGHT` | Test Provenance, Secret Scan, Lint, Workflow Validation | Rust Core Build, Heavy PyTest |
| `governance/**` | `TIER_LIGHT` | Test Provenance, Secret Scan, Governance Drift | Rust Core Build, Heavy PyTest |
| `project/**` | `TIER_STRICT` | All Gates (Provenance, Secrets, Lint, Rust, PyTest, E2E) | None |
| `rust_core/**` | `TIER_STRICT` | All Gates (Rust PyO3 Audit, Clippy, PyTest, Provenance) | None |
| `api/**` | `TIER_STRICT` | All Gates (API Contract, OpenAPI Snapshot, Route Sync) | None |
| `scripts/**`, `tests/**`| `TIER_STRICT` | All Gates | None |
| Unrecognized / Mixed | `TIER_STRICT` | All Gates (Fail-Closed) | None |

---

## 4. Operational Runbook

### Checking a PR's Tier Locally
```bash
# Check diff against main
python3 scripts/path_ruleset_classifier.py --base origin/main --head HEAD

# Check JSON details
python3 scripts/path_ruleset_classifier.py --files docs/INDEX.md README.md --json
```

### Adding New Light Paths
Any addition to `LIGHT_PREFIXES` or `LIGHT_EXACT_FILES` must be submitted via PR with test provenance in `tests/test_path_based_rulesets.py`.
