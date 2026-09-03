# project/core - Scoped Agent Instructions

## Scope & Precedence
- Governs core metaphysical engines, astronomical calculations, and AI routing in `project/core/`.
- Root Universal Safeguards Precedence: Root `AGENTS.md`, `.agents/rules/`, and repository safety mandates strictly supersede this document.
- Package Boundaries: Do not introduce circular dependencies between `project.core` and `project.routers`.
- Immutability: Maintain functional purity across all calculation modules.

## BaZi Math & Astronomical Integrity
- Adhere strictly to NOAA Spencer 1971 formulas for Equation of Time (EoT) and Solar Declination.
- True Solar Time calculations must be 100% deterministic with zero floating-point drift.
- Validate solar terms (Jie Qi), four pillars, and celestial coordinates against Swiss Ephemeris golden baselines.
- Core calculation functions must be pure, immutable, and side-effect free; never mutate input date/time objects.
- Preserve astronomical constants without arbitrary alterations or imprecise rounding.
- Ensure Day Master strength, Hidden Stems, and Ten Gods calculations match classical formulas.

## Ancient Canonical Texts & Citations
- Base metaphysical interpretations on classical texts: San Ming Tong Hui, Di Tian Sui, Zi Ping Zhen Quan, and Qimen classics.
- Always provide provenance citations and bilingual terms (Chinese characters and Romanized pinyin).
- Maintain rigorous separation between classical textual evidence and modern synthesis.
- Prevent anachronistic commentary or unsubstantiated astrological assertions.
- Verify interpretations against verified domain references in `project/core/references/`.

## HITL Routing & Safety
- Ambiguous chart configurations, boundary birth hours, or severe conflicting readings must route to Human-In-The-Loop (`NEEDS_HITL`).
- Never hallucinate astrological pillars or force artificial certainty on ambiguous inputs.
- Enforce provider-agnostic zero-cost router failover when invoking LLM reasoning layers.
- Maintain comprehensive ASCII observability logging for all calculations and routing steps.
- Provide clear diagnostic logs explaining why a chart requires human expert verification.
- Guard user privacy by omitting PII from telemetry logs and analytical traces.
