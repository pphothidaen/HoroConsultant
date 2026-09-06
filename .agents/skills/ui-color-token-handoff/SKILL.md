---
name: ui-color-token-handoff
description: Export structured CSS custom properties and semantic design tokens for UI handoff.
---

# UI Color Token Handoff

Package and hand off accessible, tokenized design systems from UI design to frontend development.

## Purpose

Enforce tokenized CSS custom property architectures and reject hardcoded color literals
in stylesheets and components.

## Token Architecture

All colors must be exposed as CSS custom properties with clear semantic aliases:

1. **Surface & Background Tokens**:
   - `--surface-bg`: Root viewport background.
   - `--surface-card`: Component container and card background.
   - `--surface-border`: Subdued borders and dividing rules.

2. **Typography & Foreground Tokens**:
   - `--text-primary`: Primary body copy and headings.
   - `--text-secondary`: Supporting text, captions, and secondary labels.
   - `--text-muted`: Placeholder and disabled states.

3. **Domain Semantic Tokens**:
   - Five elements tokens: `--element-wood`, `--element-fire`, `--element-earth`, `--element-metal`, `--element-water`.
   - Divination state tokens: `--color-auspicious`, `--color-inauspicious`, `--color-neutral`.

4. **Theme Switch Support**:
   - Dual configuration via `@media (prefers-color-scheme: light)` and explicit data attributes.
   - Switching themes must require zero inline overrides in component markup.

## Handoff Verification Steps

1. Inspect frontend CSS/Tailwind files for forbidden hardcoded RGB/HEX literals.
2. Confirm structured CSS variable declarations under `:root`.
3. Validate atomic dark and light theme variant consistency.
4. Report status:
   - `[OK]`: Design tokens verified and exported cleanly.
   - `[ERROR]`: Hardcoded RGB/HEX literal detected in styling files.
   - `[WARNING]`: Unaliased token used directly.
   - `[INFO]`: Token bundle generated.

## Gotchas

- Never allow hardcoded color values in component CSS or inline styles.
- Pure ASCII logs only: `[OK]`, `[ERROR]`, `[WARNING]`, `[INFO]`.
