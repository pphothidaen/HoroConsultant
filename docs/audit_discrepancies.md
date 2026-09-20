# Audit: Documentation vs Implementation Discrepancies

**Scope**: README.md sequence diagrams & flowcharts, docs/v3_api_specification.md, docs/c4_hermes_9router_architecture.md vs. source code (project/api_router.py, project/routers/debate.py, project/validator.py, project/routers/v3.py, project/core/solar_time.py, project/core/bazi_engine.py, project/core/svg_generator.py, .env, .env.example)

---

## 1. Model Names in Sequence Diagrams vs Env Vars

### D1.1 — Primary Ollama model name mismatch
- **README.md:378** — Sequence diagram: `Try Local Ollama (qwen2.5:7b) -> Fallback Gemini 2.0`
- **README.md:343** — Flowchart: `Call Primary Local Ollama qwen2.5:7b`
- **README.md:434** — Quick Start: `ollama pull qwen2.5:7b`
- **api_router.py:34** — `PRIMARY_LOCAL_MODEL = os.getenv("OLLAMA_PRIMARY_MODEL", "qwen2.5-bazi")`
- **api_router.py:8 (module docstring)** — Says `PRIMARY_LOCAL_MODEL (qwen2.5:7b)`
- **api_router.py:484 (HybridRouter docstring)** — Says `LOCAL 1: qwen2.5:7b`
- **Severity: HIGH** — The code default is `qwen2.5-bazi`, but both README and the HybridRouter/module docstrings say `qwen2.5:7b`. In environments where env vars are unset (e.g. fresh `python -m venv`, CI without .env), the wrong model (`qwen2.5-bazi`) loads silently. The actual runtime `.env` sets `OLLAMA_PRIMARY_MODEL="qwen2.5:7b"`, so the docs match the runtime config but contradict the code's fallback default.

### D1.2 — Secondary/Tertiary Ollama model order mismatch
- **api_router.py:35** — `SECONDARY_LOCAL_MODEL = os.getenv("OLLAMA_SECONDARY_MODEL", "qwen2.5:7b")`
- **api_router.py:36** — `TERTIARY_LOCAL_MODEL = os.getenv("OLLAMA_TERTIARY_MODEL", "qwen2.5-coder:7b")`
- **api_router.py:8 (docstring)** — Says SECONDARY=`qwen2.5-coder:7b`, TERTIARY=`llama3:8b`
- **api_router.py:484 (docstring)** — Says LOCAL 2=`qwen2.5-coder:7b`, LOCAL 3=`llama3:8b`
- **Severity: HIGH** — Docstrings list secondary=`qwen2.5-coder:7b`, tertiary=`llama3:8b`, but code defaults are secondary=`qwen2.5:7b`, tertiary=`qwen2.5-coder:7b`. The runtime `.env` overrides to match the docstrings, but the code defaults are wrong.

### D1.3 — Gemini fallback model described as "Gemini 2.0" / "Gemini 2.0 Flash"
- **README.md:378** — `Fallback Gemini 2.0`
- **README.md:347** — Flowchart: `Call Dual Gemini Cloud Fallback Gemini 2.0 Flash`
- **api_router.py:42-58** — `GEMINI_MODELS_ROTATION` = `[gemini-flash-latest, gemma-4-26b-a4b-it, gemma-4-31b-it, *DEFAULT_GEMINI_ROTATION]` where `DEFAULT_GEMINI_ROTATION = [gemini-flash-latest, gemma-4-26b-a4b-it, gemma-4-31b-it, gemini-2.5-flash, gemini-3.5-flash-lite, gemini-3.6-flash]`
- **api_router.py:60-68** — `GEMINI_MODEL_FALLBACK_CANDIDATES` dict with per-model fallback lists
- **Severity: HIGH** — The docs describe a single "Gemini 2.0 Flash" fallback, but the actual chain is a 6+ model rotation with per-model candidate fallback lists, dual-key rotation (GOOGLE_AI_STUDIO_API_KEY + KEY2), and Cloudflare AI as an intermediate. The README's "Dual Gemini Cloud Fallback" is a gross oversimplification.

### D1.4 — HybridRouter docstring cloud rotation order is wrong
- **api_router.py:487** — Docstring: `CLOUD: Gemini models x all keys (gemini-3.5-flash-lite -> gemini-flash-latest -> gemini-3.6-flash)`
- **api_router.py:56** — Actual rotation built from `[GEMINI_PRIMARY_MODEL, GEMINI_SECONDARY_MODEL, GEMINI_TERTIARY_MODEL, *DEFAULT_GEMINI_ROTATION]` then deduplicated
- **Severity: HIGH** — The docstring lists `gemini-3.5-flash-lite -> gemini-flash-latest -> gemini-3.6-flash`, but the actual first three candidates (with env defaults) are `gemini-flash-latest -> gemma-4-26b-a4b-it -> gemma-4-31b-it`. The order and models in the docstring don't match.

### D1.5 — .env.example env var names don't match code
- **.env.example:27** — `OLLAMA_MODEL=qwen2.5-bazi:7b` (code reads `OLLAMA_PRIMARY_MODEL`)
- **.env.example:15** — `PRIMARY_MODEL=gemini-2.5-flash` (code default is `gemini-flash-latest`)
- **.env.example:16** — `SECONDARY_MODEL=gemini-1.5-pro` (code default is `gemma-4-26b-a4b-it`)
- **.env.example:17** — `FALLBACK_MODEL=gemini-2.0-flash` (code reads `TERTIARY_MODEL`, not `FALLBACK_MODEL`)
- **.env.example** — Missing: `OLLAMA_PRIMARY_MODEL`, `OLLAMA_SECONDARY_MODEL`, `OLLAMA_TERTIARY_MODEL`, `TERTIARY_MODEL`
- **.env.example** — `OLLAMA_PORT` (line 28) is defined but never read by api_router.py
- **Severity: HIGH** — Copying `.env.example` to `.env` produces a broken config: `OLLAMA_MODEL` and `FALLBACK_MODEL` are never read, so the local and Gemini fallback models silently fall back to code defaults (`qwen2.5-bazi`, `gemma-4-31b-it`).

### D1.6 — validator.py model default vs README
- **README.md:378** — `Fallback Gemini 2.0`
- **validator.py:29** — `VALIDATOR_MODEL = os.getenv("VALIDATOR_MODEL", "gemini-2.0-flash")`
- **validator.py:134** — Fallback candidate list: `gemini-2.0-flash`, `gemini-2.0-flash-lite`, `gemini-1.5-flash`, `gemini-1.5-pro`
- **Severity: LOW** — README generically says "Gemini 2.0"; code default is `gemini-2.0-flash`. Approximately correct but lacks precision.

---

## 2. Validation Flow Mismatches in debate.py

### D2.1 — Validation bypass: `enable_validation` flag never checked
- **debate.py:44** — `enable_validation: bool = Field(False, description="Cross-validate prediction via Gemini Prediction Validator Agent")`
- **debate.py:264-272** — `validation_report = None` then `if not validation_report:` (always True), sets hardcoded report
- **debate.py:28** — `validator = PredictionValidator()` instantiated but never called in `interpret_bazi`
- **Severity: CRITICAL** — The `enable_validation` request field is defined in the schema and documented as enabling cross-validation, but the `interpret_bazi` endpoint never checks it. The validator is never invoked. A hardcoded "APPROVED" report (confidence_score=0.96) is always returned, masquerading as a real Gemini audit.

### D2.2 — README sequence diagram shows mandatory validation call that never executes
- **README.md:380** — `Server->>Audit: validate(chart, interpretation, query)`
- **README.md:381** — `Audit-->>Server: Validation Report (Status, Peer Perspective, Score)`
- **debate.py:266-272** — No call to `validator.validate()` exists; report is hardcoded
- **Severity: CRITICAL** — The documented sequence diagram implies validation always runs and returns a real report from the Gemini validator. The actual code always returns a fake report without any external API call.

### D2.3 — README flowchart shows conditional validation that code ignores
- **README.md:346** — `Ollama -- Success --> GeminiCheck{Validation Enabled?}`
- **README.md:350** — `GeminiCheck -- Yes --> GeminiVal[Gemini Prediction Validator Audit project/validator.py]`
- **README.md:351** — `GeminiCheck -- No --> Combine`
- **debate.py:264-272** — No `if req.enable_validation:` branch exists; validation report is unconditionally hardcoded
- **Severity: CRITICAL** — The `{Validation Enabled?}` decision point is documented but the code never branches on `enable_validation`. It always returns the hardcoded report regardless of the flag.

### D2.4 — Validation always returns "APPROVED" regardless of enable_validation
- **debate.py:267-272** — Hardcoded response: `validation_status: "APPROVED"`, `confidence_score: 0.96`
- **Severity: HIGH** — Even when `enable_validation=False` (the default), the response includes a validation report claiming "Gemini Multi-Agent Audit verified 5 Elements balance, True Solar Time, and Day Master strength." This is fabricated — no audit was performed.

---

## 3. LLM Fallback Chain Accuracy in api_router.py

### D3.1 — Fallback only on Timeout/429 is incorrect
- **README.md:347** — `Ollama -- Timeout / 429 --> CloudFallback`
- **api_router.py:572-637** — `generate()` iterates ALL routes for ANY failure reason (`connect_error`, `empty`, `exception`, `error:500`, etc.)
- **api_router.py:583-586** — Circuit breaker only trips on `429` (rate limit); all other failure reasons proceed to next route
- **Severity: MEDIUM** — The flowchart implies cloud fallback only triggers on timeout/429, but the actual router falls back for all error types. The only special behavior for 429 is the 60s circuit breaker cooldown.

### D3.2 — Cloudflare AI route omitted from README diagrams
- **api_router.py:518-524** (cloud mode) — Cloudflare AI route added before Gemini routes
- **api_router.py:533-539** (local mode) — Cloudflare AI route added after Ollama, before Gemini
- **README.md Flowchart (lines 343-348)** — Only shows Ollama → Gemini fallback, no Cloudflare AI step
- **Severity: MEDIUM** — The Cloudflare Workers AI route (between Ollama and Gemini) is a documented feature of the router but is entirely absent from both the flowchart and sequence diagram.

### D3.3 — Codex CLI route in cloud mode undocumented
- **api_router.py:510-511** — `if check_codex_installation(): routes.append({"type": "codex_cli", ...})`
- **api_router.py:591-596** — Codex CLI is handled as a route type in `generate()`
- **README.md** — No mention of Codex CLI as a cloud-mode route
- **Severity: MEDIUM** — The codex_cli route (primary cloud route when installed) is not documented in README architecture diagrams or the c4_hermes_9router_architecture.md.

### D3.4 — "Zero-cost" mode undocumented in diagrams
- **api_router.py:491-496** — `zero_cost_only` flag from env `AI_ZERO_COST_ONLY`
- **api_router.py:546** — Logger message about zero-cost policy (but logic is not actually gated on this flag in `_build_routes`)
- **README.md** — No mention of zero-cost mode or `AI_ZERO_COST_ONLY` env var
- **Severity: LOW** — The flag exists and is read but the gating logic in `_build_routes` doesn't actually use it (it always adds all routes). The flag is a no-op dead code path.

---

## 4. Missing Steps in Documented Flows

### D4.1 — "Is LLM Interpretation Requested?" decision point doesn't exist in interpret_bazi
- **README.md:342** — `CheckLLM{Is LLM Interpretation Requested?}` → No: `FastReturn[Return Chart JSON + SVG]`
- **debate.py:252-296** — `interpret_bazi` ALWAYS calls `router.generate()`; there is no conditional branch
- **Severity: MEDIUM** — The flowchart implies the LLM call is optional within the BaZi interpret flow. The actual endpoint always invokes the LLM. The "No" path exists for calculation-only endpoints (`/api/calculate/bazi`, api_router.py:875-878), not for the interpret endpoint.

### D4.2 — Fallback SVG reading (hardcoded) is undocumented
- **debate.py:262-263** — `if not initial_text.strip(): initial_text = _generate_fallback_reading(dm, pcts, req.query)`
- **README.md** — No mention of a hardcoded fallback reading generation when LLM returns empty
- **Severity: MEDIUM** — A significant fallback path (pure-rule-based Thai reading generation when LLM fails) exists in the code but is absent from all documented flows.

### D4.3 — RAG references are hardcoded, not from FAISS
- **debate.py:274-279** — `rag_references` is a hardcoded list of 4 classical texts
- **README.md:566** — Claims `rag_search: Searches 3,132 FAISS vector chunks from classical texts`
- **README.md:237** — Shows `fastapi_app --> faiss_db` (FAISS search in architecture)
- **Severity: MEDIUM** — The interpret_bazi endpoint returns hardcoded RAG references instead of performing actual FAISS vector search. The FAISS RAG is wired into the architecture but not invoked in the BaZi interpret flow.

### D4.4 — v3 spec describes L1 Astro Kernel Engine that doesn't exist as a separate layer
- **v3_api_specification.md:18** — `L1 — Astro Kernel Engine (astro_kernel_service.proto): Calculates true solar time, equation of time, Julian day ephemeris`
- **v3.py:143** — `bazi = BaZiEngine().calculate(dt, req.longitude, req.tz_offset)` — TST calculated inside BaZiEngine, not a separate L1 layer
- **project/core/solar_time.py:73-110** — `calculate_true_solar_time()` is called by BaZiEngine (bazi_engine.py:763), not by a separate Astro Kernel Engine
- **Severity: MEDIUM** — The 7-stage architectural abstraction describes L1 as a separate gRPC Proto3 Astro Kernel Engine, but the actual implementation calculates TST within the Python BaZiEngine. There is no separate Astro Kernel layer in the v3 request path.

### D4.5 — v3 spec describes Merkle DAG provenance not invoked in calculate_v3
- **v3_api_specification.md:39-46** — Cryptographic Merkle DAG provenance with SHA-256 hashing at every node
- **v3_api_specification.md:41** — Implemented in `rust_core/src/v3_merkle_dag.rs`
- **v3.py:191-209** — `calculate_v3()` calls `_calculate_emissions()`, `ConsensusEngine`, `AuditNode`, `PlanComposer` — no reference to Merkle DAG or `v3_merkle_dag`
- **Severity: HIGH** — The spec describes a cryptographic Merkle DAG provenance chain as a core architectural feature, but `calculate_v3` never invokes it. The response (v3.py:201-209) contains no Merkle root hash or provenance DAG fields.

### D4.6 — v3 spec doesn't document conditional runtime availability / 503 failure mode
- **v3_api_specification.md:18-24** — Describes all 7 layers as always-present
- **v3.py:66-76** — Runtime classes (`AuditNode`, `ClaimValidator`, `ConsensusEngine`, `PlanComposer`) are conditionally imported; set to `None` if `TDD-HORO-v3.0` runtime tree is not found
- **v3.py:102-105** — `_require_v3_runtimes()` raises `HTTPException(503, "v3 runtime assets are unavailable")`
- **v3_api_specification.md:243** — Only documents 400, 422, 500 error codes; does NOT document 503 (runtime unavailable)
- **Severity: MEDIUM** — The spec omits the 503 failure mode entirely. The runtime classes may be `None` in many deployment contexts, breaking the v3 endpoint.

### D4.7 — Discipline count: 10 vs 16 vs 11 inconsistency
- **README.md:5** — Intro: "16-Domain" (lists 16 disciplines)
- **README.md:414** — "10 canonical computational metaphysics disciplines" (lists 10 grouped categories)
- **README.md:284** — Level 3 diagram: "10 Metaphysical Calculation Engines" (lists 10: BaZi, ZiWei, QiMen, LiuRen, IChing, XuanKong, ZeJi, ThaiVedic, Western, Numerology)
- **README.md:298** — "11 Discipline SVG Renderers"
- **api_router.py:793-831** — `DISCIPLINE_TOOL_MAP` supports 16 distinct disciplines
- **project/core/svg_generator.py** — 16 discipline-specific SVG renderers (generate_*_svg) plus zodiac_wheel and multimodal_matrix
- **v3.py:86** — `_ACTIVE_DOMAINS` has 10 (different set: BaZi, ZiWei, QiMen, ZeJi, XuanKong, DaLiuRen, LiuYao, TaiYi, QiZheng, MianXiang)
- **Severity: MEDIUM** — The discipline count is inconsistent across intro (16), architecture diagrams (10, then 11), and code (16 in API router, 10 in v3 router).

### D4.8 — Sequence diagram omits zodiac wheel SVG generation
- **README.md:375** — `Server->>SVG: generate_bazi_svg(chart)`
- **debate.py:281-282** — Both `generate_bazi_svg(chart)` AND `generate_zodiac_wheel_svg(chart)` are called
- **debate.py:283-284** — `chart["svg_content"] = svg_content; chart["zodiac_svg"] = zodiac_svg`
- **README.md:382** — Response shows `(Chart, Interpretation, SVG, Audit Report)` — omits zodiac_svg
- **Severity: LOW** — Sequence diagram only shows one SVG call and the response payload omits the zodiac wheel SVG that the code actually generates and returns.

### D4.9 — Flowchart TST formula imprecision
- **README.md:373** — Sequence diagram: `TST = Local Time + LMT Offset + EoT`
- **solar_time.py:4-6** — `TST = LMT + EoT` where `LMT = Clock_Time + 4*(λ - Λ_std)`
- **README.md:337** — Flowchart: `TST = LMT + EoT` (correct)
- **Severity: LOW** — The sequence diagram formula is technically redundant (LMT already includes the offset), though the intent is clear. The flowchart formula is correct.

### D4.10 — HITL sequence diagram routes don't match actual HITL implementation
- **README.md:397-398** — HITL UI calls `HITL Router (/hitl/*)`, `GET /hitl/item/{item_id}` → `DB: Load item & confidence heatmap`
- **debate.py:340** — Uses `from project.hitl_router import upsert_external_hitl_item` (upsert, not GET)
- **debate.py:341-370** — HITL item includes `source_domain`, `source_id`, `confidence_score`, `conflict_detected`, `consensus_matrix` — not a "confidence heatmap"
- **Severity: MEDIUM** — The HITL sequence diagram describes a GET-based item loading flow with a "confidence heatmap", but the actual implementation uses `upsert_external_hitl_item` with a different data structure. The diagram doesn't match the real HITL router interface.

---

## Summary Matrix

| ID | Category | File:Line | Severity | Description |
|----|----------|-----------|----------|-------------|
| D1.1 | Model names | README.md:378,343,434 vs api_router.py:34,8,484 | HIGH | Primary model `qwen2.5:7b` in docs vs `qwen2.5-bazi` code default |
| D1.2 | Model names | api_router.py:8,484 vs 35,36 | HIGH | Docstring secondary/tertiary order doesn't match code defaults |
| D1.3 | Model names | README.md:378,347 vs api_router.py:42-68 | HIGH | "Gemini 2.0 Flash" vs 6+ model rotation chain |
| D1.4 | Model names | api_router.py:487 vs 56 | HIGH | Docstring cloud rotation order wrong |
| D1.5 | Model names | .env.example:15-17,27 vs api_router.py:34-53 | HIGH | Wrong env var names in template |
| D1.6 | Model names | README.md:378 vs validator.py:29 | LOW | "Gemini 2.0" too vague |
| D2.1 | Validation | debate.py:44 vs 264-272, 28 | CRITICAL | `enable_validation` never checked |
| D2.2 | Validation | README.md:380-381 vs debate.py:266-272 | CRITICAL | Documented `validate()` call never executes |
| D2.3 | Validation | README.md:346,350-351 vs debate.py | CRITICAL | `{Validation Enabled?}` branch absent |
| D2.4 | Validation | debate.py:267-272 | HIGH | Hardcoded "APPROVED" always returned |
| D3.1 | Fallback chain | README.md:347 vs api_router.py:572-637 | MEDIUM | Fallback on all errors, not just timeout/429 |
| D3.2 | Fallback chain | README.md:343-348 vs api_router.py:518-539 | MEDIUM | Cloudflare AI route missing from docs |
| D3.3 | Fallback chain | api_router.py:510-511 vs README.md | MEDIUM | Codex CLI route undocumented |
| D3.4 | Fallback chain | api_router.py:491-496 | LOW | `AI_ZERO_COST_ONLY` is dead code |
| D4.1 | Missing steps | README.md:342 vs debate.py:252-263 | MEDIUM | "Is LLM requested?" check absent in interpret_bazi |
| D4.2 | Missing steps | debate.py:262-263 vs README.md | MEDIUM | Hardcoded fallback reading undocumented |
| D4.3 | Missing steps | debate.py:274-279 vs README.md:566,237 | MEDIUM | Hardcoded RAG refs vs FAISS search |
| D4.4 | Missing steps | v3_api_specification.md:18 vs v3.py:143 | MEDIUM | L1 Astro Kernel Engine abstraction mismatch |
| D4.5 | Missing steps | v3_api_specification.md:39-46 vs v3.py:191-209 | HIGH | Merkle DAG provenance not invoked in calculate_v3 |
| D4.6 | Missing steps | v3_api_specification.md:243 vs v3.py:66-105 | MEDIUM | 503 runtime-unavailable failure mode undocumented |
| D4.7 | Missing steps | README.md:5,284,298 vs api_router.py:793-831 | MEDIUM | 10 vs 16 vs 11 discipline count inconsistency |
| D4.8 | Missing steps | README.md:375,382 vs debate.py:281-284 | LOW | Zodiac wheel SVG omitted from sequence diagram |
| D4.9 | Missing steps | README.md:373 vs solar_time.py:4-6 | LOW | TST formula imprecision in sequence diagram |
| D4.10 | Missing steps | README.md:397-398 vs debate.py:340-370 | MEDIUM | HITL sequence diagram doesn't match actual upsert interface |

**Severity counts**: CRITICAL × 3, HIGH × 8, MEDIUM × 11, LOW × 3 — Total: 25 discrepancies
