# Session Goal: KAN-306 Phase 2 - AI-Assisted Code Review & Quality Gates

## ภาษาไทย / English
**เป้าหมาย**: เริ่ม Phase 2 ของ AI-SDLC Transformation — AI Code Review และ Quality Gates  
**Goal**: Begin Phase 2 of AI-SDLC Transformation — AI Code Review & Quality Gates

---

## Jira Context
- **Epic**: KAN-289 "AI-SDLC Transformation"
- **Phase 0**: KAN-290 (14 mitigations) ✅ DONE
- **Phase 1**: KAN-305 "AI Code/Test Generation in CI" ✅ DONE (PR #276 merged)
- **Phase 2**: KAN-306 — **NEXT TARGET**

---

## Phase 2 Scope (Standard AI-SDLC Roadmap)

### 2A: AI Code Review Agent
- เพิ่ม `ai-code-review` job ใน CI (รันหลัง `ai-code-generation`)
- ใช้ `gemini-web-bridge` / `aipass-web-bridge` สำหรับ review
- โพสต์ผล review เป็น PR comments

### 2B: Quality Gate Integration
- กำหนดเกณฑ์คุณภาพ (security, complexity, coverage, best practices)
- Gate: AI review ต้องผ่าน หรือ human override โดยเจตนา
- ติดตาม metrics ของ review

### 2C: Automated Fix Suggestions
- AI แนะนำการแก้ไขสำหรับ pattern ที่พบบ่อย
- Auto-fix สำหรับเรื่องเล็กน้อย (formatting, imports)
- Human approval สำหรับการเปลี่ยนแปลงที่สำคัญ

---

## Acceptance Criteria (ยืนยันจาก Jira เมื่อมีโอกาส)
- [ ] AI review PRs สำหรับ security, style, correctness
- [ ] Quality gates บังคับใน CI pipeline
- [ ] Automated fix suggestions สำหรับ issues ที่พบบ่อย
- [ ] Human override mechanism documented
- [ ] Test provenance maintained (test_provenance_guard.py passes)

---

## TDD Implementation Plan

### Step 1: Failing Tests First
```bash
# สร้าง test สำหรับ AI review agent
tests/test_ai_code_review.py
```

### Step 2: AI Review Agent
```python
# scripts/ai_code_review.py
# - เรียก gemini-web-bridge / aipass-web-bridge
# - parse review results
# - output structured report
```

### Step 3: CI Integration
```yaml
# .github/workflows/ci.yml
# เพิ่ม ai-code-review job
needs: [ai-code-generation, ai-review-enforcement]
```

### Step 4: Quality Gates
```python
# scripts/quality_gate.py
# - evaluate review results against thresholds
# - exit code 0 = pass, 1 = fail (block merge)
```

---

## Ready to Start Checklist
- [ ] Query Jira for exact KAN-306 details (if connector available)
- [ ] Create `.hermes/plans/kan-306-plan.md` with detailed tasks
- [ ] Write failing tests (`tests/test_ai_code_review.py`)
- [ ] Implement `scripts/ai_code_review.py`
- [ ] Add CI job `ai-code-review`
- [ ] Add quality gate script
- [ ] Create test provenance manifest
- [ ] Run full CI verification

---

## Session Start Command
```bash
# เริ่ม session ใหม่ด้วย:
cd /Users/kimlenglim/Project/HoroConsultant
git checkout -b feature/KAN-306-ai-code-review
# เริ่ม TDD: เขียน test ก่อน
```

---

## Notes for Next Session
1. **Phase 1 foundation solid**: PR template, AI detection, human review enforcement all working
2. **Bridges available**: gemini-web-bridge (port 8765), aipass-web-bridge (port 8766) — verified in CI
3. **Test provenance working**: Keyless cosign + test_provenance_guard.py passing
4. **Quality baseline**: All 6 required CI checks passing on main