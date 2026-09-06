---
name: web-color-design
description: Compatibility router for Five Elements palette, WCAG audit, and UI color tokens.
owner: ux_ui_designer
sunset: Sunset upon full migration to focused UI color skills in v2.0.0; no focused-profile activation.
---

# Web Color Design Compatibility Router

Workflow-free compatibility router delegating to focused color design and accessibility skills.

## Governance and Metadata

- **Owner**: `ux_ui_designer`
- **Sunset Condition**: Retained strictly for backwards-compatible routing; scheduled for sunset in v2.0.0 after full migration to focused UI color skills.
- **Activation Restriction**: No focused-profile activation permitted; this is a workflow-free router.

## Routing Targets

Inquiries and tasks mapped to this router are forwarded to the appropriate focused skill:

1. **`five-elements-ui-palette`**:
   - Manages Chinese metaphysical Wu Xing color palettes (Wood, Fire, Earth, Metal, Water).
   - Enforces cultural harmony relationships and generation/overcoming constraints.
   - Rejects arbitrary raw hex values in favor of semantic element tokens.

2. **`wcag-apca-color-audit`**:
   - Executes fail-closed contrast audits across light and dark theme modes.
   - Validates compliance against WCAG 2.1 AA (4.5:1 / 3.0:1) and APCA lightness criteria.

3. **`ui-color-token-handoff`**:
   - Packages verified color palettes into CSS custom properties and Tailwind configuration.
   - Preserves theme switching support without inline component overrides.

## Reporting Protocol

- All status reports from routed tasks must use pure ASCII logs only:
  - `[OK]`: Sub-task routed and verified.
  - `[ERROR]`: Routing failure or target contract breach.
  - `[WARNING]`: Compatibility router invoked instead of direct focused skill.
  - `[INFO]`: Delegation target identified.
