---
name: ui-visual-auditor
description: Audit multi-viewport screenshots for layout distortion, clipping, and overlapping elements.
---

# UI Visual Auditor & Multi-Viewport Layout Inspector Skill

## Overview
This skill provides automated capabilities for multi-viewport web screenshot capture, DOM element collision detection, horizontal overflow validation, and layout distortion analysis across responsive breakpoints.

## Canonical Viewport Matrix

| Viewport Profile | Width x Height | Device Category | Focus Areas |
| :--- | :--- | :--- | :--- |
| `desktop-4k` | 1920 x 1080 | Large Display / Desktop | Grid alignment, wide cards, navbar spacing |
| `laptop-standard` | 1366 x 768 | Standard Laptop | Compact dashboard, modal overlays |
| `tablet-portrait` | 768 x 1024 | iPad / Tablet Portrait | Form field wrapping, collapsible sidebar |
| `mobile-ios` | 390 x 844 | iPhone 14/15 / Modern Mobile | Bottom navigation, button tap targets, claim cards |
| `mobile-compact` | 360 x 740 | Compact Android Mobile | Horizontal overflow, text truncation, badge wraps |

## Core Automated Checks

1. **DOM Overlap & Collision Check**:
   - Compares bounding rectangles (`getBoundingClientRect`) of visible sibling elements.
   - Detects unintentional overlaps where bounding boxes intersect without intentional nesting or z-index layering.
2. **Horizontal Overflow Check**:
   - Asserts `document.documentElement.scrollWidth <= window.innerWidth + 1`.
   - Prevents accidental mobile sideways scrolling.
3. **Clipping & Layout Shift Check**:
   - Checks if elements are clipped by `overflow: hidden` containers unexpectedly.
   - Verifies text nodes are not rendered invisible by container bounds.

## CLI Usage

```bash
# Run full visual layout audit across all viewports
python3 scripts/run_visual_layout_audit.py

# Run audit against specific target URL
python3 scripts/run_visual_layout_audit.py --url http://127.0.0.1:8888 --viewports desktop-4k mobile-ios

# Output pure JSON report
python3 scripts/run_visual_layout_audit.py --json
```

## Output Artifacts
- **Screenshots**: `project/tests/screenshots/visual_audit/{viewport}_{scenario}.png`
- **JSON Report**: `project/tests/artifacts/visual_layout_report.json`
