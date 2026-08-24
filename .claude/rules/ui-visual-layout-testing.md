---
description: Multi-viewport screenshot capture and visual layout distortion rules.
paths:
  - "project/static/**/*"
  - "public/**/*"
  - "scripts/run_visual_layout_audit.py"
  - "project/tests/test_visual_layout_audit.py"
---

# UI Visual Layout & Multi-Viewport Testing

- **Viewports**: Test across Desktop (1920x1080), Laptop (1366x768), Tablet (768x1024), Mobile iOS (390x844), and Compact (360x740).
- **Overlap & Clipping**: Assert zero bounding box collisions, text truncation, or unhandled horizontal overflow (`scrollWidth > clientWidth`).
- **Automation**: Execute `python3 scripts/run_visual_layout_audit.py` to capture screenshots and generate `visual_layout_report.json`.
- **Ownership**: Owned by `ui_visual_tester` agent using `ui-visual-auditor` skill.
