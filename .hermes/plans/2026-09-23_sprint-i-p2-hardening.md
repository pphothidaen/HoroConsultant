# Plan: Sprint I P2 — Hardening (KAN-102/103/104)

## Goal
Harden the Hermes Agent system through skill audit, budget enforcement, and session handoff improvements.

---

## KAN-102: Skill Audit

### Tasks
- [x] Categorize 151 skills by trigger frequency
- [x] Archive 23 unused/niche skills to `.hermes/skills/.archive/`
- [x] Verify all linked files exist across all skills
- [x] Fix all skill descriptions ≤60 chars

### Trigger Frequency Categories

**HIGH** (core, used every session):
- hermes-agent, session-librarian, session-handoff, plan, orchestration
- github (all sub-skills), jira-board-operations, jira-goals-sync
- code-review, codebase-inspection, systematic-debugging, test-driven-development
- gateway-route-sync-contract, quality-gate-enforcement, task-decomposition-delegation

**MEDIUM** (specialized, used weekly):
- ai-agent-integration/*, autonomous-ai-agents/*
- creative/excalidaw, creative/ascii-art, creative/humanizer, creative/songwriting-and-ai-music
- devops/cloudflare-deployment, devops/jira-github-operations, devops/doppler-secret-management
- media/*, productivity/*
- research/arxiv, research/blogwatcher, research/rss-feeds, research/grounded-citations
- social-media/reddit-reading, social-media/xurl
- web/blocked-page-recovery
- workflow/*

**LOW** (archived — niche/one-off):
- mlops/* (most), creative/* (most), serving/*, local-llm-macos
- llama-cpp, evaluating-llms-harness, weights-and-biases, manim-video, p5js, pretext
- comfyui, baoyu-infographic, ascii-video, design-md, sketch, popular-web-designs
- node-server-testability, gemini-mcp-safety-retry, github-actions-webhook-integration
- personal-branding-hr-tech, touchdesigner-mcp, ovms-arc-optimization

### Results
- Active skills: 125
- Archived skills: 23
- Total: 148 (3 new added during audit)

---

## KAN-103: Budget Enforcement

### Tasks
- [x] Create `budget-enforcement` skill
- [x] Implement `track_spend.py` — record model call costs to JSONL ledger
- [x] Implement `check_budget.py` — return remaining budget + alert level
- [x] Implement `week_report.py` — generate weekly cost summary
- [x] Configure $10 weekly / $40 monthly limits with 50/80/100% alerts
- [x] Support free-tier model bypass at 100% cap

### Files Created
- `.hermes/skills/budget-enforcement/SKILL.md`
- `.hermes/skills/budget-enforcement/scripts/track_spend.py`
- `.hermes/skills/budget-enforcement/scripts/check_budget.py`
- `.hermes/skills/budget-enforcement/scripts/week_report.py`

### Alert Thresholds
| Level | Weekly | Monthly | Action |
|-------|--------|---------|--------|
| WARNING | $5 (50%) | $20 (50%) | Suggest free models |
| CRITICAL | $8 (80%) | $32 (80%) | Prefer free models |
| HARD_CAP | $10 (100%) | $40 (100%) | Block non-free calls |

---

## KAN-104: Session Handoff Skill

### Tasks
- [x] Enhance session-handoff skill with templates and scripts
- [x] Create session summary template (`templates/session_summary.md`)
- [x] Create continuation prompt template (`templates/continuation_prompt.md`)
- [x] Create handoff extraction script (`scripts/extract_handoff.py`)
- [x] Context preservation across compression boundaries
- [x] Continuation prompt for seamless resume

### Files Created
- `.hermes/skills/workflow/session-handoff/templates/session_summary.md`
- `.hermes/skills/workflow/session-handoff/templates/continuation_prompt.md`
- `.hermes/skills/workflow/session-handoff/scripts/extract_handoff.py`

---

## Verification

- [x] All active skill descriptions ≤60 chars
- [x] Budget enforcement scripts execute correctly
- [x] Session handoff extract script runs on existing sessions
- [x] 23 unused skills archived to `.hermes/skills/.archive/`
- [x] Zero missing linked files across all skills

## Commit

Single commit with `[KAN-102] [KAN-103] [KAN-104]` prefix.
