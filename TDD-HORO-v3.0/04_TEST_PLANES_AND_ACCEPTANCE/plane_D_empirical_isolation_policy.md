# 📋 Plane D — Empirical Isolation Policy
**Horo Architecture v3.0 — Frozen Baseline**  
**Schema Version**: 3.0.0  
**Status**: POLICY DOCUMENT — Normative

---

## 1. Purpose

This document defines the **Observational Data Firewall** that governs how real-world outcome data (empirical observations) may and may not interact with the Horo Engine's deterministic core systems.

The fundamental epistemic principle of Horo v3.0 is:

> **Astronomical Correctness ≠ Tradition-Rule Validity ≠ Interpretive Consistency ≠ Predictive Validity**

Layer D (Empirical Evaluation) exists **outside** the system's formal verification boundary. Observational data CANNOT automatically promote or demote the pass/fail status of Layer A, B, or C tests.

---

## 2. What Is Observational Data (Layer D)

Layer D data is defined as any data that measures real-world outcomes associated with system predictions. Examples:

| Category | Examples |
|---|---|
| User feedback | Rating of interpretation quality (1–5 stars) |
| Outcome tracking | User-reported event outcomes vs. system predictions |
| HITL review decisions | Human reviewer accept/reject of claims in `hitl_approved.jsonl` |
| Statistical correlations | Correlation between BaZi pattern X and life outcome Y across N users |
| A/B test results | Comparison of interpretation quality between Prompt Bundle v3.0 and v3.1 |

---

## 3. The Firewall Rules (Normative)

### Rule D-1: No Automatic Core Engine State Change
**Observational data MUST NOT automatically change the pass/fail status of any Layer A, B, or C test case.**

- A high user rating for a response does NOT prove that the underlying calculation was correct.
- A low user rating does NOT invalidate a classically-grounded claim.
- Correlation between a BaZi pattern and an observed outcome does NOT update rule weights without human review.

**Enforcement**: All Layer A/B/C tests run in isolated environments with no read access to Layer D data stores.

### Rule D-2: Manual Review Required for Feedback Loop
**Any use of observational data to inform system changes MUST pass through a human review gate.**

Permitted pathway:
```
Layer D Observation
  → Statistical Analysis (separate process, read-only)
  → Human Researcher Review
  → Formal Architecture Change Request (ACR)
  → Rule Bundle Update (if approved)
  → Layer B/C regression re-validation
```

Prohibited pathway:
```
Layer D Observation → Automatic rule weight update → Core Engine [FORBIDDEN]
Layer D Observation → Automatic prompt update → L3/L4 Agent [FORBIDDEN without ACR]
```

### Rule D-3: Data Segregation
Layer D data stores are physically separated from Layer A/B/C test fixtures:

| Layer | Storage Location | Access |
|---|---|---|
| A — Golden Vectors | `04_TEST_PLANES_AND_ACCEPTANCE/plane_A_*.json` | Read-only, version-controlled |
| B — Conformance | `04_TEST_PLANES_AND_ACCEPTANCE/plane_B_*.json` | Read-only, version-controlled |
| C — Adversarial | `04_TEST_PLANES_AND_ACCEPTANCE/plane_C_*.json` | Read-only, version-controlled |
| D — Empirical | `project/hitl_approved.jsonl`, `project/hitl_reviews.json`, analytics DB | Separate, append-only |

### Rule D-4: No Predictive Validity Claims
**The system MUST NOT claim that any output has been empirically validated for predictive accuracy.**

The `@Horo_Composer_Node` (L7) is required to include this disclaimer verbatim in every output:

> *"ผลการวิเคราะห์นี้เกิดขึ้นจากการประมวลผลตรรกะตามกฎของสำนักวิชาที่เลือก (Tradition-Rule Validity) และความสอดคล้องของแบบจำลอง (Interpretive Consistency) เท่านั้น ไม่ถือเป็นการรับรองผลสัมฤทธิ์ในอนาคตเชิงประจักษ์ (Predictive Validity is Explicitly Disclaimed)"*

### Rule D-5: Statistical Isolation Window
When running Layer D statistical analyses, the analysis must use a **minimum 90-day holdout window** — outcomes from the last 90 days are excluded from any retrospective analysis to prevent data leakage from recent system changes.

---

## 4. Permitted Layer D Workflows

The following workflows are explicitly permitted under this policy:

### 4.1 HITL Fine-Tuning Data Collection
```
User interaction → Anonymized QA export → hitl_reviews.json
  → Human reviewer approves/rejects → hitl_approved.jsonl
  → Quarterly review by domain expert → Update proposal
  → ACR process
```

### 4.2 Interpretation Quality Monitoring
```
Response generated → User rates quality → Rating stored in analytics DB
  → Weekly aggregate report (anonymized) → Researcher review
  → No automatic action
```

### 4.3 Claim Accuracy Tracking (Experimental)
```
System generates prediction claim → User tracks real outcome → Outcome recorded
  → Statistical analysis (min N=1000 per tradition) → Report to domain expert
  → Only if statistical significance p<0.001 → Consider for ACR
```

---

## 5. Audit and Compliance

All Layer D data access must be logged. The following events trigger a mandatory policy compliance audit:

- Any code change that creates a read dependency between Layer D data and Layer A/B/C test fixtures
- Any automated process that modifies rule weights or prompt templates based on observational data
- Any release that claims "empirically validated" accuracy metrics without attached ACR number

---

## 6. Exception Process

If a domain expert believes Layer D evidence is strong enough to warrant a Core Engine change:

1. File an **Architecture Change Request (ACR)** with supporting statistical evidence
2. Minimum evidence: N≥500 cases, p<0.001, peer review by 2 domain experts
3. If approved: update Layer B conformance cases to reflect the new rule
4. Re-run full Layer A/B/C suite before release
5. Document the change in `docs/RELEASE_NOTES.md`

---

*This policy is part of the Frozen Baseline (Horo Architecture v3.0) and requires an ACR to modify.*
