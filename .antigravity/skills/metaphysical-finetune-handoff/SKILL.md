---
name: metaphysical-finetune-handoff
description: Curate verified, redacted metaphysical consultation datasets for fine-tuning handoff.
---

# Metaphysical Fine-Tune Handoff

Curate and package high-quality, privacy-redacted consultation pairs for model distillation.

## Purpose

Enforce distillation quality gates and redacting PII before exporting consultation logs
into fine-tuning datasets, binding `source_domain=metaphysical-domain-engine`.

## Handoff Requirements

1. **Rejection of Raw/Unverified Chat Logs**:
   - Never export raw user transcripts or unverified LLM interpretations into training sets.
   - Every candidate pair must be grounded in verified deterministic calculations.

2. **Distillation Quality Checklist**:
   - Verification of astronomical calculation grounding against ephemeris engines.
   - Resolution of grayzone paradoxes with recorded human master sign-off.
   - Verification that the item successfully cleared the HITL scope gate.
   - Confirmation of vault sync status.

3. **Privacy & PII Redaction**:
   - Redact all personal identifiers: names, phone numbers, exact birth locations, and coordinates.
   - Generalize sensitive metadata while retaining astronomical timestamp precision.

4. **Signed Dataset Manifest**:
   - Emit a signed training handoff manifest binding dataset SHA-256 digest, sample counts, and master approval signature.

## Handoff Workflow

1. Filter candidate consultation pairs by `pass_gate_check=true` and certified master sign-off.
2. Verify deterministic ephemeris grounding for all astrological claims.
3. Apply rigorous regex and heuristic redaction of PII.
4. Generate signed dataset export manifest.
5. Report status:
   - `[OK]`: Fine-tuning batch verified, redacted, and manifest signed.
   - `[ERROR]`: Raw unverified logs or unredacted PII detected.
   - `[WARNING]`: Incomplete distillation checklist item found.
   - `[INFO]`: Batch export completed.

## Gotchas

- Must bind `source_domain=metaphysical-domain-engine`.
- Pure ASCII logs only: `[OK]`, `[ERROR]`, `[WARNING]`, `[INFO]`.
