# Rule 15: UI Visual Layout & Multi-Viewport Regression Testing

## 1. Core Principles
1. **Multi-Viewport Guarantee**: Every UI component, dashboard, modal, and claim card must render without visual distortion, text clipping, or overlapping bounding boxes across 5 canonical viewports:
   - `desktop-4k` (1920x1080)
   - `laptop-standard` (1366x768)
   - `tablet-portrait` (768x1024)
   - `mobile-ios` (390x844)
   - `mobile-compact` (360x740)
2. **Deterministic Overlap Detection**: Automated Playwright audits must evaluate DOM bounding rects (`getBoundingClientRect`) to detect unintentional sibling element overlaps ($z$-index collisions, negative margin collisions, absolute positioning collisions).
3. **Horizontal Overflow Prevention**: No viewport may trigger unexpected horizontal document scrolling (`scrollWidth > clientWidth + 1`).
4. **Visual Evidence Artifacts**: All screenshot captures must be timestamped and stored in `project/tests/screenshots/visual_audit/` and recorded in `project/tests/artifacts/visual_layout_report.json`.

## 2. Execution Protocol
- Run visual layout suite via `python3 scripts/run_visual_layout_audit.py`.
- Enforce visual validation before releasing major frontend or styling modifications.
- Dedicated agent: `ui_visual_tester` owns visual regression and multi-viewport layout validation.
