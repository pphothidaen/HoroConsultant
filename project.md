# Computational Metaphysics Engine — Project Specification

> **Version**: 1.0.0 | **Last Updated**: 2026-08-03  
> **For**: Handoff to any AI agent or developer continuing this project

---

## 1. System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   User / Client                         │
└───────────────────┬─────────────────────────────────────┘
                    │  HTTP / Antigravity IDE
                    ▼
┌─────────────────────────────────────────────────────────┐
│           FastAPI Application  (port 8000)              │
│  ┌──────────────────┐   ┌──────────────────────────┐   │
│  │  BaZi Engine     │   │  Hybrid API Router        │   │
│  │  (Pure Python)   │   │  Gemini → Ollama fallback │   │
│  └──────────────────┘   └──────────────────────────┘   │
└──────────┬───────────────────────┬──────────────────────┘
           │                       │
    ┌──────▼──────┐         ┌──────▼──────────┐
    │ Redis Cache │         │ Ollama Container │
    │ (rate state)│         │ qwen2.5-bazi:7b  │
    └─────────────┘         └─────────────────┘
           │
    ┌──────▼──────────────────────────────────┐
    │        Google AI Studio API              │
    │  Primary:  Gemini 3.6 Flash             │
    │  Secondary: Gemini 1.5 Pro              │
    │  Fallback: Gemini 3.5 Flash             │
    └──────────────────────────────────────────┘
```

---

## 2. Data Flow Architecture

### 2.1 BaZi Calculation Flow

```
Input: birth_datetime, longitude, utc_offset_hours
         │
         ▼
┌─────────────────────────────┐
│  1. True Solar Time (TST)   │
│  TST = LMT + EoT            │
│  LMT = Clock + 4×(λ − Λ)   │
│  EoT = NOAA Spencer formula │
└────────────┬────────────────┘
             │ tst_datetime
             ▼
┌─────────────────────────────┐
│  2. Four Pillars Calculation │
│  Year  : (year − 4) mod 10/12 │
│          (adjusted for Lichun)│
│  Month : Five Tigers Rule    │
│  Day   : Julian Day Number   │
│  Hour  : Five Rats Rule      │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│  3. Hidden Stems (藏干)     │
│  Each branch → 1-3 stems    │
│  with fractional weights    │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│  4. Five Elements Scoring   │
│  Stems: 10 pts each         │
│  Hidden stems: 15×weight    │
│  × Seasonal multiplier      │
└────────────┬────────────────┘
             │
             ▼
Output: Structured JSON (see §3)
```

### 2.2 Probabilistic Mode (Unknown Birth Hour)

When `unknown_hour=true`:
- Hours 0–11 (all 12 double-hour branches) computed independently
- Each scenario assigned equal prior weight = 1/12 ≈ 0.0833
- Returns array of 12 complete charts in `probabilistic_matrix`
- Consuming agent may apply Bayesian updating with additional evidence

### 2.3 AI Interpretation Flow

```
BaZi Chart JSON
      │
      ▼
HybridRouter.generate()
      │
      ├─→ Gemini 3.6 Flash  (primary, 8s timeout)
      │       │ HTTP 429 or timeout
      ├─→ Gemini 1.5 Pro    (secondary)
      │       │ failure
      ├─→ Gemini 3.5 Flash  (fallback)
      │       │ failure
      └─→ Ollama qwen2.5-bazi (local, unlimited timeout)
                │
                ▼
         Natural Language Response
```

### 2.4 Multi-Agent Flow (Antigravity IDE)

```
User Query
    │
    ▼
Sol Orchestrator (Gemini 3.6 Flash)
    │
    ├─→ [Tool] bazi-calculator.skill  → BaZi Engine API
    │
    ├─→ [Tool] rag-search.skill       → Vector Store
    │
    ▼
Draft Response
    │
    ▼
Luna Auditor (Claude Opus + Thinking)
    │
    ├─→ Verify pillar calculations
    ├─→ Cross-check citations
    ├─→ Validate element percentages sum=100%
    │
    ▼
Audit Report { passed: true, confidence: 0.95, ... }
    │
    ▼
Final Response → User
```

---

## 3. API Specification

### 3.1 POST /api/v1/bazi/calculate

**Request**
```json
{
  "birth_datetime":   "1990-05-15 14:30:00",
  "longitude":        100.4930,
  "utc_offset_hours": 7.0,
  "unknown_hour":     false
}
```

**Response (is_probabilistic: false)**
```json
{
  "engine_version": "1.0.0",
  "solar_time_info": {
    "input_datetime":            "1990-05-15 14:30:00",
    "longitude":                 100.493,
    "utc_offset_hours":          7.0,
    "standard_meridian":         105.0,
    "longitude_offset_minutes":  -18.028,
    "eot_minutes":               3.612,
    "lmt_datetime":              "1990-05-15 14:11:58",
    "tst_datetime":              "1990-05-15 14:15:35",
    "tst_hour":                  14,
    "tst_minute":                15,
    "tst_second":                35
  },
  "day_master": {
    "stem":     "壬",
    "element":  "Water",
    "polarity": "Yang",
    "pinyin":   "Rén"
  },
  "pillars": {
    "year":  { "label": "Year",  "stem": {...}, "branch": {...}, "hidden_stems": [...] },
    "month": { "label": "Month", "stem": {...}, "branch": {...}, "hidden_stems": [...] },
    "day":   { "label": "Day",   "stem": {...}, "branch": {...}, "hidden_stems": [...] },
    "hour":  { "label": "Hour",  "stem": {...}, "branch": {...}, "hidden_stems": [...] }
  },
  "five_elements": {
    "scores":           { "Wood": 18.0, "Fire": 12.0, "Earth": 24.5, "Metal": 9.0, "Water": 21.0 },
    "percentages":      { "Wood": 21.4, "Fire": 14.3, "Earth": 29.2, "Metal": 10.7, "Water": 25.0 },
    "dominant_element": "Earth",
    "weakest_element":  "Metal",
    "total_raw":        84.5
  },
  "is_probabilistic": false
}
```

**Response (is_probabilistic: true)**
```json
{
  "engine_version":   "1.0.0",
  "solar_time_info":  { ... },
  "day_master":       { ... },
  "pillars": { "year": {...}, "month": {...}, "day": {...}, "hour": null },
  "is_probabilistic": true,
  "probabilistic_matrix": [
    {
      "hour_branch":         "子",
      "hour_branch_pinyin":  "Zǐ",
      "animal":              "Rat",
      "hour_window":         "23:00–01:00",
      "probability_weight":  0.083333,
      "hour_pillar":         { ... },
      "five_elements":       { ... }
    },
    ...  // 12 scenarios total
  ]
}
```

---

### 3.2 POST /api/v1/bazi/interpret

Extends calculate with `query` field. Returns `chart` + `interpretation` text + routing metadata.

### 3.3 GET /api/v1/eot?date=YYYY-MM-DD

Returns `{ "date": "...", "eot_minutes": 3.61 }`

---

## 4. BaZi Algorithm Reference

### 4.1 Equation of Time (NOAA Spencer)
```
γ = (2π / DaysInYear) × (DOY − 1 + Hour/24)
EoT = 229.18 × (0.000075
                + 0.001868 cos(γ)
                − 0.032077 sin(γ)
                − 0.014615 cos(2γ)
                − 0.040849 sin(2γ))   [minutes]
```

### 4.2 Year Pillar
- Effective year = calendar year − 1 if date is before Lichun (≈ Feb 4)
- Stem index  = (eff_year − 4) mod 10
- Branch index = (eff_year − 4) mod 12

### 4.3 Month Pillar (Five Tigers Rule 五虎遁)
| Year Stem Group | 寅 Month Base Stem |
|-----------------|-------------------|
| 甲 / 己 (0,5)   | 丙 (idx 2)        |
| 乙 / 庚 (1,6)   | 戊 (idx 4)        |
| 丙 / 辛 (2,7)   | 庚 (idx 6)        |
| 丁 / 壬 (3,8)   | 壬 (idx 8)        |
| 戊 / 癸 (4,9)   | 甲 (idx 0)        |

### 4.4 Day Pillar (Julian Day)
```
stem_idx   = (JDN + 9) mod 10
branch_idx = (JDN + 1) mod 12
```

### 4.5 Hour Pillar (Five Rats Rule 五鼠遁)
| Day Stem Group | 子 Hour Base Stem |
|----------------|------------------|
| 甲 / 己 (0,5)  | 甲 (idx 0)       |
| 乙 / 庚 (1,6)  | 丙 (idx 2)       |
| 丙 / 辛 (2,7)  | 戊 (idx 4)       |
| 丁 / 壬 (3,8)  | 庚 (idx 6)       |
| 戊 / 癸 (4,9)  | 壬 (idx 8)       |

### 4.6 Five Elements Scoring
```
Raw score per element E =
  Σ (stem contributes 10 pts if elem(stem) = E)
  + Σ (15 × weight for each hidden stem with elem = E)

Final score[E] = Raw[E] × seasonal_multiplier[season][E]
Percentage[E]  = Final[E] / Σ Final × 100%
```

---

## 5. MLX Fine-Tuning Checklist

- [ ] Place raw classical texts in `project/data/raw_texts/*.txt`
- [ ] Run `python scripts/extract_dataset_mlx.py`
- [ ] Verify `project/data/mlx_finetune/train.jsonl` (≥ 100 entries)
- [ ] Install `mlx mlx-lm` on Apple Silicon macOS
- [ ] Run LoRA fine-tuning (see README §Fine-Tuning)
- [ ] Fuse adapter and convert to GGUF
- [ ] Place GGUF at `project/models/qwen2.5-bazi.gguf`
- [ ] Test: `ollama create qwen2.5-bazi -f project/models/Modelfile`

---

## 6. Docker Deployment Checklist

- [ ] `cp .env.example .env` and fill all vars
- [ ] `docker compose up --build -d`
- [ ] Verify health: `curl http://localhost:8000/health`
- [ ] Check Ollama: `curl http://localhost:11434/api/tags`
- [ ] Run tests: `docker compose exec app python -m pytest tests/ -v`
- [ ] Load custom model via model-loader service if GGUF available

---

## 7. Handoff Checkpoint

This project is structured for seamless AI-to-AI handoff:

| Component | Status | Notes |
|-----------|--------|-------|
| `solar_time.py` | ✅ Complete | NOAA EoT, dataclass output, CLI |
| `bazi_engine.py` | ✅ Complete | 4 pillars, hidden stems, element scores, probabilistic |
| `api_router.py` | ✅ Complete | 4-level fallback chain |
| `main.py` | ✅ Complete | FastAPI 3 endpoints |
| `tests/test_core.py` | ✅ Complete | 14 test cases |
| `Dockerfile` | ✅ Complete | Multi-stage Ubuntu build |
| `docker-compose.yml` | ✅ Complete | App + Ollama + Redis |
| `Modelfile` | ✅ Complete | Qwen2.5-BaZi ChatML format |
| `extract_dataset_mlx.py` | ✅ Complete | Chart synthesis + JSONL output |
| `.antigravity/agents/` | ✅ Complete | Sol + Luna agents |
| `.antigravity/skills/` | ✅ Complete | bazi-calculator + rag-search |
| `README.md` | ✅ Complete | Full usage guide |
| `project.md` | ✅ Complete | This document |

**Remaining tasks for next agent/developer:**
1. Add real classical text files to `project/data/raw_texts/`
2. Curate and annotate `project/data/sample_charts.json` with verified charts
3. Implement vector store backend for `rag-search` skill
4. Run MLX fine-tuning with curated dataset
5. Configure Google AI Studio API key in `.env`
6. Set up CI/CD pipeline (GitHub Actions recommended)
