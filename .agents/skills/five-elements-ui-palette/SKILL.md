---
name: five-elements-ui-palette
description: Map Wu Xing five-element semantic color palettes and cultural harmony constraints.
---

# Five Elements UI Palette

Design and maintain Chinese metaphysical Wu Xing five-element color palettes for HoroConsultant.

## Purpose

Map the Five Elements (Wood, Fire, Earth, Metal, Water) into canonical UI color tokens
while respecting metaphysical harmony relationships and rejecting arbitrary hex codes.

## Five Elements Semantic Mapping

- **Wood (木 - Mu)**:
  - Canonical: Forest green tones (`#2D6A4F`, `hsl(152, 41%, 30%)`).
  - Primary, secondary, and container backgrounds for vitality, growth, and birth aspects.
- **Fire (火 - Huo)**:
  - Canonical: Vermillion red tones (`#C1121F`, `hsl(357, 79%, 42%)`).
  - Highlights, energy indicators, and active alert elements.
- **Earth (土 - Tu)**:
  - Canonical: Amber gold/ochre tones (`#D4A017`, `hsl(43, 79%, 46%)`).
  - Stability, center containers, grounding components.
- **Metal (金 - Jin)**:
  - Canonical: Silver slate/white tones (`#9DA3A8`, `hsl(210, 5%, 66%)`).
  - Precision markers, borders, logic structures.
- **Water (水 - Shui)**:
  - Canonical: Deep navy/azure tones (`#023E8A`, `hsl(215, 95%, 28%)`).
  - Wisdom badges, deep surface backdrops, fluid accents.

## Harmony Constraints

1. **Generation (Sheng) Relationships**:
   - Wood generates Fire, Fire generates Earth, Earth generates Metal, Metal generates Water, Water generates Wood.
   - Complementary elements should be paired harmoniously without perceptual jarring.

2. **Overcoming (Ke) Relationships**:
   - Wood overcomes Earth, Earth overcomes Water, Water overcomes Fire, Fire overcomes Metal, Metal overcomes Wood.
   - Antagonistic color combinations must use neutral dividers and clear lightness contrast.

3. **No Hardcoded Raw Hex**:
   - Reject arbitrary inline hex colors like `#ff00ff` in component markup.
   - All styling must reference semantic element tokens.

## ASCII Status Reporting

- `[OK]`: Elemental palette and token mapping conforms to cultural and semantic specs.
- `[ERROR]`: Raw hex code or incompatible element clash detected.
- `[WARNING]`: Suboptimal element contrast detected.
- `[INFO]`: Element tokens mapped.
