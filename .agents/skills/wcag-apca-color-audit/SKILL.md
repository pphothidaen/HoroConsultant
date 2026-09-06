---
name: wcag-apca-color-audit
description: Audit UI color contrast compliance against WCAG 2.1 AA and APCA lightness standards.
---

# WCAG & APCA Color Audit

Perform rigorous, fail-closed accessibility contrast audits on all HoroConsultant UI components.

## Purpose

Validate color combinations across themes to ensure full readability and conformance
with WCAG 2.1 AA and APCA lightness contrast standards.

## Audit Standards & Thresholds

1. **WCAG 2.1 AA Requirements**:
   - **Normal Body Copy (< 18pt)**: Minimum contrast ratio of **4.5:1**.
   - **Large Text (>= 18pt bold or >= 24pt)**: Minimum contrast ratio of **3.0:1**.
   - **UI Components & Icons**: Minimum contrast ratio of **3.0:1**.

2. **APCA Lightness Contrast (Lc)**:
   - Body Copy: Lc >= 75.
   - Headline / Subhead: Lc >= 60.
   - Non-text / Decorative: Lc >= 30.

3. **Dual Theme Evaluation**:
   - Every component pair must be audited in both Light Theme and Dark Theme.
   - Unverified color pairs (such as `#888888` on `#ffffff`) fail closed and are rejected.

## Audit Procedure

1. Extract foreground and background color definitions for buttons, cards, badges, and text.
2. Compute relative luminance and contrast ratio:
   $$CR = \frac{L_1 + 0.05}{L_2 + 0.05}$$
3. Perform APCA lightness contrast calculation.
4. Output structured, machine-readable audit results:
   - `[OK]`: Contrast ratio >= 4.5:1 (AA compliant) and APCA compliant.
   - `[ERROR]`: Insufficient contrast detected; tokens must be adjusted.
   - `[WARNING]`: Contrast meets AA minimum but fails AAA recommendation.
   - `[INFO]`: Color pair evaluated across light and dark themes.

## Gotchas

- Never approve a visual design without computing exact contrast ratios.
- Pure ASCII logs only: `[OK]`, `[ERROR]`, `[WARNING]`, `[INFO]`.
