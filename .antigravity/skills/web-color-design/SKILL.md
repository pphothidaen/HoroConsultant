---
name: web-color-design
description: Color systems, Five Elements palettes, WCAG contrast, and design tokens for HoroConsultant UI.
---

# 🎨 Web Color Design & Accessible UI Theming Skill

This skill equips the **`ux_ui_designer` agent** with a structured workflow for designing, validating, and delivering production-ready color systems for the **HoroConsultant** web interface.

---

## 🎯 Core Objectives

1. **Color Theory Application**: Apply HSL-based color design with controlled hue, saturation, and luminance for harmonious palettes.
2. **Five Elements Theming**: Map Chinese metaphysical Five Elements to intuitive web colors.
3. **WCAG/APCA Accessibility**: Validate all color pairs against WCAG 2.1 AA and APCA Lc standards.
4. **Design Token Output**: Deliver structured CSS custom properties and Tailwind theme config.
5. **Dark Mode Support**: Produce paired light/dark palettes using CSS `prefers-color-scheme`.

---

## 🌏 Five Elements (Wu Xing) Color Mapping

| Element | Chinese | Primary Color | Hex | HSL | Usage |
|---------|---------|---------------|-----|-----|-------|
| Wood    | 木 (Mù) | Forest Green  | `#2D6A4F` | `hsl(152, 41%, 30%)` | Growth, vitality badges |
| Fire    | 火 (Huǒ) | Vermillion Red | `#C1121F` | `hsl(357, 79%, 42%)` | Energy, passion, warnings |
| Earth   | 土 (Tǔ) | Amber Yellow  | `#D4A017` | `hsl(43, 79%, 46%)` | Stability, center, neutral |
| Metal   | 金 (Jīn) | Silver White  | `#9DA3A8` | `hsl(210, 5%, 66%)` | Clarity, precision, logic |
| Water   | 水 (Shuǐ) | Deep Navy    | `#023E8A` | `hsl(215, 95%, 28%)` | Wisdom, depth, flow |

### Semantic Color Extensions
- **Auspicious (吉)**: `#22C55E` — Green-500, positive outcomes
- **Inauspicious (凶)**: `#EF4444` — Red-500, warnings/risks
- **Neutral (平)**: `#94A3B8` — Slate-400, balanced/unclear

---

## 🔍 WCAG Contrast Validation Workflow

### Step 1 — Identify Color Pairs
For every UI component, list: `background → text`, `button → label`, `badge → icon`.

### Step 2 — Calculate Contrast Ratio
Use the formula: **CR = (L1 + 0.05) / (L2 + 0.05)** where L1 > L2 (relative luminance).

**Minimum Requirements:**
- Normal text (< 18pt): **4.5:1** (AA) / **7:1** (AAA)
- Large text (≥ 18pt bold / ≥ 24pt): **3:1** (AA)
- UI components & focus rings: **3:1** (AA)

### Step 3 — APCA Advanced Check (Lc value)
- Body text: **Lc ≥ 75**
- Headlines: **Lc ≥ 60**
- Placeholder / decorative: **Lc ≥ 30**

### Step 4 — Remediation
If contrast fails:
1. Darken background or lighten text (adjust L in HSL).
2. Never rely on color alone — add icons, patterns, or labels.
3. Test with simulated color-blindness (Deuteranopia, Protanopia, Tritanopia).

---

## 🎨 HoroConsultant Design Token Spec

### CSS Custom Properties (`:root`)
```css
:root {
  /* === Brand Colors === */
  --color-primary: hsl(215, 95%, 28%);        /* Water Blue */
  --color-primary-light: hsl(215, 80%, 55%);
  --color-secondary: hsl(43, 79%, 46%);       /* Earth Gold */
  --color-accent: hsl(357, 79%, 42%);         /* Fire Red */

  /* === Five Elements === */
  --element-wood: hsl(152, 41%, 30%);
  --element-fire: hsl(357, 79%, 42%);
  --element-earth: hsl(43, 79%, 46%);
  --element-metal: hsl(210, 5%, 66%);
  --element-water: hsl(215, 95%, 28%);

  /* === Semantic === */
  --color-auspicious: hsl(142, 71%, 45%);
  --color-inauspicious: hsl(0, 84%, 60%);
  --color-neutral: hsl(215, 16%, 57%);

  /* === Surface === */
  --surface-bg: hsl(222, 47%, 11%);           /* Dark navy bg */
  --surface-card: hsl(222, 35%, 17%);
  --surface-border: hsl(215, 20%, 30%);

  /* === Typography === */
  --text-primary: hsl(210, 40%, 96%);
  --text-secondary: hsl(215, 20%, 65%);
  --text-muted: hsl(215, 15%, 45%);
}

@media (prefers-color-scheme: light) {
  :root {
    --surface-bg: hsl(0, 0%, 98%);
    --surface-card: hsl(0, 0%, 100%);
    --surface-border: hsl(215, 20%, 85%);
    --text-primary: hsl(222, 47%, 11%);
    --text-secondary: hsl(215, 20%, 35%);
    --text-muted: hsl(215, 15%, 55%);
  }
}
```

### Tailwind `theme.extend` Patch
```js
// tailwind.config.js — theme.extend
colors: {
  element: {
    wood:   '#2D6A4F',
    fire:   '#C1121F',
    earth:  '#D4A017',
    metal:  '#9DA3A8',
    water:  '#023E8A',
  },
  horo: {
    auspicious:   '#22C55E',
    inauspicious: '#EF4444',
    neutral:      '#94A3B8',
  }
}
```

---

## 🌑 Dark Mode Design Guidelines

1. **Background Luminance**: Keep dark bg at L 8–15% HSL. Never pure black (`#000`).
2. **Text on Dark**: Use `hsl(210, 40%, 96%)` (near-white) at ≥ 4.5:1 contrast.
3. **Saturate Carefully**: Reduce saturation of bright colors by ~20% in dark mode to prevent eye strain.
4. **Element Colors in Dark Mode**: Add `filter: brightness(1.3)` for Wood/Water on dark backgrounds.
5. **Focus Rings**: Use `outline: 2px solid var(--color-primary-light)` with `outline-offset: 2px`.

---

## 📐 UI Component Color Recipes

### Metaphysics Result Card
```css
.result-card {
  background: var(--surface-card);
  border: 1px solid var(--surface-border);
  border-left: 4px solid var(--element-water);  /* domain accent */
}
```

### Auspicious/Inauspicious Badge
```css
.badge-ji  { background: hsl(142, 71%, 20%); color: hsl(142, 71%, 85%); }
.badge-xiong { background: hsl(0, 84%, 20%); color: hsl(0, 84%, 90%); }
```

### Five Elements Pill
```css
[data-element="wood"]  { background: hsl(152, 41%, 15%); color: hsl(152, 41%, 75%); }
[data-element="fire"]  { background: hsl(357, 79%, 18%); color: hsl(357, 79%, 85%); }
[data-element="earth"] { background: hsl(43, 79%, 18%);  color: hsl(43, 79%, 85%);  }
[data-element="metal"] { background: hsl(210, 5%, 25%);  color: hsl(210, 5%, 85%);  }
[data-element="water"] { background: hsl(215, 95%, 12%); color: hsl(215, 95%, 80%); }
```

---

## 📋 Design Handoff Checklist

Before handing off to `developer` agent:
- [ ] All color tokens defined in CSS custom properties
- [ ] Tailwind config patch produced
- [ ] WCAG contrast ratios verified (list each pair + ratio)
- [ ] Dark mode variants confirmed
- [ ] Color-blind simulation test noted (Deuteranopia / Protanopia)
- [ ] Component CSS snippets provided
- [ ] No color-only information (icons/labels added where needed)

---

## 🔗 References
- WCAG 2.1: https://www.w3.org/TR/WCAG21/
- APCA: https://www.w3.org/WAI/WCAG3/Explainers/APCA/
- HoroConsultant Five Elements Engine: `.agents/skills/bazi-calculator/SKILL.md`
