# Horo v3.0 Production Visual Integrity — Lessons Learned

Date: 2026-08-24  
Target: `🏛️ Horo v3.0 Consensus Engine` on the Hugging Face Production Space  
Release state: Vercel production deployed and verified; Hugging Face Docker republish blocked by repository quota

## Issue Experienced

The exact fourth tab was partly inaccessible on compact mobile widths. Several descendants were clipped even though the document itself reported no horizontal overflow. The v3 content also appeared as a dark-theme island inside the light host application, semantic metric colors failed WCAG AA, and long populated output could be cut off by a fixed accordion expansion height.

The original audit could additionally return process exit code 0 when its report status was `WARNING`, creating a false-green CI risk.

## Definitive Root Cause

1. `@media (prefers-color-scheme: dark)` changed only v3 tokens instead of following the host application's explicit theme state.
2. The tab row did not wrap, intrinsic-width children resisted shrinking, and an ancestor hid overflow. Root-level `scrollWidth` therefore missed child clipping.
3. The open accordion used an arbitrary `max-height: 5000px`, shorter than a ten-claim multilingual result.
4. Green/red semantic text tokens were too light on translucent surfaces, and gradient text/background combinations were treated as ordinary solid-color contrast checks.
5. The generic visual scenario did not deterministically populate and select the exact v3 tab.
6. The visual-audit command did not fail closed on `WARNING`.
7. Broad QA commands could mutate tracked HITL/training fixture files, creating unrelated dirty-state noise.

## Lessons Learned

1. No document overflow does not prove that descendants are visible; compare critical child bounds with both viewport and clipping ancestors.
2. Component themes must follow one explicit application theme source. OS preference must not independently recolor one section.
3. Expanded content panels should be content-driven, not constrained by guessed maximum heights.
4. A visual regression must reproduce the exact user state: populated result, expanded interpretation card, and selected fourth tab.
5. Gradient contrast must be sampled manually or reported as indeterminate; it must never receive an optimistic automated pass.
6. Status meaning needs text/icon support and AA-compliant tokens, not color alone.
7. `WARNING` is a failed release gate, even when it is not a product failure.
8. QA that touches user or HITL stores must use temporary copies and verify tracked fixtures remain clean.
9. Mirrored frontend assets need byte-parity and syntax gates on both copies.
10. Production and backend version labels must be distinguished; a footer overwritten by `/health` can misidentify the UI release.

## QA Follow-up — Telegram Environment Isolation

The post-upgrade full suite exposed three failures unrelated to the v3 UI. The Telegram singleton captured `TELEGRAM_CHAT_ID` at import time, so later environment changes were ignored; the notifier formatting test also inherited real local credentials and attempted network delivery.

The controller now resolves the default chat ID at request time while retaining explicit constructor overrides. The notifier test clears Telegram and Discord credentials before asserting formatting. Focused Telegram/config/security tests pass `16/16`, and the full suite passes `792 passed, 9 skipped`.

## Prevention Protocol

- Activate v3 dark tokens only through `[data-theme="dark"]` or `body.dark-mode`.
- Use a responsive tab grid: two columns at tablet/mobile, one column at compact mobile, with 44 px minimum targets.
- Apply `min-width: 0`, safe wrapping, and bounded widths to claim IDs, node tags, provenance labels, audit metrics, and confidence dimensions.
- Remove the open-state height ceiling while preserving the collapsed `max-height: 0` state.
- Verify PASS and TENSION colors in light and explicit-dark themes against WCAG AA.
- Run the deterministic `v3-consensus` scenario at 2560×1440, 1440×900, 768×1024, 390×844, and 360×800.
- Audit sibling collisions, descendant out-of-bounds, clipping ancestors, tab visibility, and complete vertical content.
- Return exit code 0 only for `overall_status == "PASSED"`; fail for `WARNING` and `FAILED`.
- Keep `public/app.js` and `project/static/app.js` byte-identical and validate both with `node --check` plus the asset-parity test.
- After an authorized deployment, repeat the five-viewport Production capture before claiming full visual `READY_FOR_PROD`; this release has request-path and asset-hash verification, while the managed browser rerun remains an environment follow-up.

## Current Verification Evidence

- Production baseline: selected v3 tab captured at five canonical viewports.
- Production defect counts: descendant out-of-bounds was 2 at 390 px and 33 at 360 px; root horizontal overflow remained false.
- Local final mobile verification: all four tabs visible; tab/content out-of-bounds 0; clipping 0; sibling collisions 0; full content height rendered at 390 px and 360 px.
- Measured local contrast: light PASS metric 7.18:1, explicit-dark TENSION metric 5.29:1, accordion chevron approximately 6.53:1.
- Automated unit gate: visual-audit and mirrored-asset tests 13/13 passed (including app.js and v3 token CSS parity); both JavaScript files passed syntax validation; ecosystem sync passed.
- Limitation: the tracked visual-layout JSON is the pre-final-fix run and remains `WARNING`. A fresh managed-browser run was blocked by local port and Chromium MachPort permissions. A root retry of `python3 -m http.server 8899 --bind 127.0.0.1 --directory project/static` reproduced `PermissionError: Operation not permitted`; Browser URL policy also rejected a local `data:` render and prohibited workaround paths. The old report must therefore not be presented as a green post-fix report.
- Production release evidence: Vercel deployment `dpl_EGC8zXBVCc1oRfGRMU932zaZHkc5` is READY; live visual asset hashes match `public/app.js` and `public/v3_tokens.css`; production path is 3/3 and Vercel curl regression is 100%.
- Remaining operational issue: the Hugging Face repository rejected the Docker upload at its 1 GB storage limit. No remote history was deleted; quota cleanup or a maintained deployment target is required for a future HF republish.
