---
name: metaphysical-request-router
description: Route metaphysical inquiries to deterministic calculation engines and tools.
---

# Metaphysical Request Router

Route astrological and metaphysical consultation requests to deterministic calculation engines.

## Purpose

Prevent LLM hallucination of astronomical and calendar calculations by strictly routing
inquiries to verified deterministic calculation tools with `source_domain=metaphysical-domain-engine`.

## Routing Architecture

1. **Deterministic Separation**:
   - The LLM must NEVER compute solar terms, stem-branch combinations, planetary longitudes, or chart houses directly.
   - All astrological data must be grounded in verified ephemeris tools (`project/core/bazi.py`, `project/core/suriyayart.py`, etc.).
   - Synthesis and interpretation must strictly consume deterministic tool outputs.

2. **Multi-Tradition Decomposition**:
   - For multi-tradition requests (e.g. BaZi + Western Astrology or Zi Wei Dou Shu + Thai Suriyayart), decompose the inquiry into distinct single-domain calculation tasks.
   - Validate birth coordinates, timezones, and timestamps before dispatching calculations.
   - Combine outputs using the consensus matrix without cross-domain pollution.

3. **HITL Escalation Binding**:
   - If ambiguity, boundary hour, severe stem-branch conflict, or low consensus (< 0.75) is detected, bind a validated HITL audit and owner sign-off before downstream handoff.

## Execution Checklist

1. Parse user birth data (date, time, longitude, latitude, gender).
2. Route calculation to domain engine:
   - BaZi: `project/core/bazi.py`
   - Thai/Vedic: `project/core/suriyayart.py`
   - Classical texts: `project/core/rag_search.py`
3. Verify output integrity.
4. Report status:
   - `[OK]`: Request routed to deterministic engine and validated.
   - `[ERROR]`: Attempted LLM computation without deterministic grounding.
   - `[WARNING]`: Multi-tradition conflict requires arbitration.
   - `[INFO]`: Routing domain identified.

## Gotchas

- Must bind `source_domain=metaphysical-domain-engine`.
- Pure ASCII logs only: `[OK]`, `[ERROR]`, `[WARNING]`, `[INFO]`.
