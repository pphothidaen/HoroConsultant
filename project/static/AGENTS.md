# project/static - Scoped Agent Instructions

## Scope & Precedence
- Governs frontend assets, styles, markup, and visual presentation in `project/static/`.
- Root Universal Safeguards Precedence: Root `AGENTS.md`, `.agents/rules/`, and repository safety mandates strictly supersede this document.
- Asset Integrity: Keep asset bundles lean, tree-shaken, and optimized for low-latency static hosting.

## Five Elements CSS Design Tokens
- Use centralized CSS custom properties in `v3_tokens.css` and `css/tokens.css` for Five Elements colors.
- Wood (Mu), Fire (Huo), Earth (Tu), Metal (Jin), and Water (Shui) palettes must strictly adhere to design tokens.
- Do not introduce inline color overrides, hardcoded hex values, or untokenized styles in templates.
- Ensure consistent theme variable propagation across all UI components and astrological charts.
- Verify semantic color roles (primary, secondary, warning, surface) remain aligned with token definitions.

## WCAG 2.1 AA Accessibility & Contrast
- Maintain minimum 4.5:1 contrast ratio for normal text and 3:1 for large text across all element themes.
- Support both dark mode and light mode palettes without contrast degradation.
- Provide accessible ARIA labels, semantic HTML elements, and clear keyboard focus states.
- Ensure all interactive controls and charts are fully operable via keyboard navigation.
- Validate color accessibility with automated contrast auditing tools before release.

## Canonical 5-Viewport Integrity
- Every UI layout must pass automated visual and layout checks across all 5 canonical viewports:
  1. Mobile Small (360x640)
  2. Mobile Large (414x896)
  3. Tablet Portrait (768x1024)
  4. Laptop / Desktop (1366x768)
  5. Ultrawide Desktop (1920x1080)
- Prevent horizontal scrollbars, clipped text, card overflows, or visual overlapping across all viewports.
- Keep layout breakpoints synchronized with media query constants across all CSS stylesheets.
