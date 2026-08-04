# Computational Metaphysics Engine 🌌

> **BaZi Four Pillars of Destiny** — Deterministic computation engine with True Solar Time, Fine-Tuned LLM interpretation, and Multi-Agent orchestration on Antigravity IDE.

---

## Architecture Overview

```
HoroConsultant/
├── project/
│   ├── core/
│   │   ├── solar_time.py      # True Solar Time (TST = LMT + EoT)
│   │   ├── bazi_engine.py     # Four Pillars + Five Elements scoring
│   │   ├── config.py          # Centralized Secrets & Doppler Config Manager
│   │   └── supabase_db.py     # Supabase REST Client & Dataset Exporter
│   ├── api_router.py          # Hybrid routing: Gemini → Ollama fallback
│   ├── main.py                # FastAPI application
│   └── models/
│       └── Modelfile          # Ollama model definition (Qwen2.5-BaZi)
├── tests/
│   └── test_core.py           # Unit tests (pytest)
├── scripts/
│   ├── extract_dataset_mlx.py       # MLX fine-tuning dataset preparation
│   ├── cloud_train_orchestrator.py  # Production Cloud Training (Kaggle/Lightning AI)
│   ├── kaggle_notebook_manager.py   # Kaggle Notebook CLI Push/Status/Pull Manager
│   ├── add_vault_entry.py           # Add & Sync Vault knowledge entries
│   ├── sync_doppler_secrets.py      # Doppler Secrets Management Auto-Sync
│   └── publish_to_hf.py             # Hugging Face Hub automated upload
├── .antigravity/
│   ├── agents/
│   │   ├── sol-orchestrator.agent   # Gemini 3.6 Flash Master Planner
│   │   └── luna-auditor.agent       # Claude Opus Thinking Auditor
│   └── skills/
│       ├── bazi-calculator.skill
│       └── rag-search.skill
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── requirements.txt
└── project.md                 # API spec & data flow architecture
```

---

## Quick Start

### 1. Clone & Configure

```bash
git clone <your-repo-url>
cd HoroConsultant
cp .env.example .env
# Edit .env — set GOOGLE_AI_STUDIO_API_KEY
```

### 2. Python (Local Dev)

```bash
pip install -r requirements.txt
export PYTHONPATH=$(pwd)

# Run FastAPI server
uvicorn project.main:app --reload --port 8000

# Test the API
curl -s http://localhost:8000/health | python3 -m json.tool
```

### 3. Run Unit Tests

```bash
# Full test suite
python -m pytest tests/ -v --tb=short

# Single module
python -m unittest tests.test_core -v
```

### 4. CLI — BaZi Calculation

```bash
# Calculate Four Pillars (Bangkok)
python -m project.core.bazi_engine \
  --dt "1990-05-15 14:30:00" \
  --longitude 100.493 \
  --utc 7.0

# Probabilistic mode (unknown birth hour)
python -m project.core.bazi_engine \
  --dt "1990-05-15 00:00:00" \
  --longitude 100.493 \
  --utc 7.0 \
  --unknown-hour

# True Solar Time only
python -m project.core.solar_time \
  --dt "2026-08-03 12:00:00" \
  --longitude 100.493 \
  --utc 7.0
```

### 5. Docker Deployment (Ubuntu)

```bash
# Build and start all services
docker compose up --build -d

# Check service health
docker compose ps
docker compose logs app --tail=50

# Stop services
docker compose down

# Load custom Qwen2.5-BaZi GGUF model
# 1. Place your .gguf file at: project/models/qwen2.5-bazi.gguf
# 2. Restart the model-loader service:
docker compose run --rm model-loader
```

---

## Fine-Tuning on macOS (Apple Silicon)

### Prerequisites

```bash
# Install MLX (Apple Silicon only)
pip install mlx mlx-lm datasets transformers
```

### Step 1: Extract Dataset

```bash
python scripts/extract_dataset_mlx.py \
  --source  project/data/raw_texts/ \
  --charts  project/data/sample_charts.json \
  --output  project/data/mlx_finetune/ \
  --val-split 0.10
```

### Step 2: Fine-Tune with MLX LoRA

```bash
mlx_lm.lora \
  --model Qwen/Qwen2.5-7B-Instruct \
  --train \
  --data project/data/mlx_finetune/ \
  --iters 1000 \
  --batch-size 4 \
  --lora-layers 8 \
  --adapter-path project/models/qwen2.5-bazi-adapter
```

### Step 3: Fuse & Convert to GGUF

```bash
# Fuse LoRA adapter back into base model
mlx_lm.fuse \
  --model Qwen/Qwen2.5-7B-Instruct \
  --adapter-path project/models/qwen2.5-bazi-adapter \
  --save-path project/models/qwen2.5-bazi-fused

# Convert to GGUF for Ollama
cd llama.cpp
python convert_hf_to_gguf.py \
  ../project/models/qwen2.5-bazi-fused \
  --outfile ../project/models/qwen2.5-bazi.gguf \
  --outtype q4_k_m
```

### Step 4: Register with Ollama

```bash
# Create Ollama model from Modelfile
cd project/models
ollama create qwen2.5-bazi -f Modelfile
ollama run qwen2.5-bazi
```

---

## Production Cloud Fine-Tuning (Kaggle / Lightning AI)

For heavy production fine-tuning on Cloud GPUs (NVIDIA T4 / L4):

```bash
# 1. Export Supabase SQL DDL Schema (Run once in Supabase SQL Editor)
python3 -m project.core.supabase_db --show-schema

# 2. Dry-run test on Kaggle / Lightning AI
python3 scripts/cloud_train_orchestrator.py --dry-run

# 3. Execute 4-bit LoRA training and push adapter to Hugging Face Hub
python3 scripts/cloud_train_orchestrator.py --platform KAGGLE_T4 --epochs 3
```

### Direct Kaggle Notebook Management via CLI

Manage, push, and monitor Kaggle fine-tuning notebooks directly from your local terminal:

```bash
# 1. Setup credentials (~/.kaggle/kaggle.json) & project/kaggle_kernel metadata
python3 scripts/kaggle_notebook_manager.py --setup

# 2. Push notebook & start execution on Kaggle GPU
python3 scripts/kaggle_notebook_manager.py --push

# 3. Check live execution status on Kaggle
python3 scripts/kaggle_notebook_manager.py --status

# 4. Pull notebook outputs & logs down locally
python3 scripts/kaggle_notebook_manager.py --pull
```

---

## Adding Knowledge Entries & Syncing to Vault

To easily add new Q&A pairs or documents to Obsidian Vault, FAISS Vector Store, and Supabase DB:

```bash
# Add Q&A knowledge entry (saves to Obsidian Vault + FAISS RAG + Supabase DB)
python3 scripts/add_vault_entry.py \
  -q "คำถามเกี่ยวกับดวงชะตา" \
  -a "คำตอบและบทวิเคราะห์โหราศาสตร์" \
  -s "子平真詮"

# Interactive mode (prompts for Q&A inputs)
python3 scripts/add_vault_entry.py --interactive

# Import a custom Markdown file to Obsidian Vault & FAISS Vector DB
python3 scripts/add_vault_entry.py --file path/to/document.md
```

---

## Multi-Agent Orchestration (Antigravity IDE)

Two agents are pre-configured in `.antigravity/agents/`:

| Agent | Model | Role |
|-------|-------|------|
| `sol-orchestrator` | Gemini 3.6 Flash (Medium) | Master Planner & Tool Caller |
| `luna-auditor` | Claude Opus (Thinking) | Zero-Hallucination Auditor |

Two skills in `.antigravity/skills/`:

| Skill | Purpose |
|-------|---------|
| `bazi-calculator` | Wraps Python BaZi engine |
| `rag-search` | Classical text retrieval |

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/health` | Service health check |
| `POST` | `/api/v1/bazi/calculate` | Deterministic BaZi chart |
| `POST` | `/api/v1/bazi/interpret` | Chart + AI interpretation |
| `GET`  | `/api/v1/eot?date=YYYY-MM-DD` | Equation of Time |

Interactive docs: http://localhost:8000/docs

---

## Hybrid API Routing

```
Request
  │
  ▼
Gemini 3.6 Flash (Primary)
  │ ← 429 or latency > 8s
  ▼
Gemini 1.5 Pro (Secondary)
  │ ← 429 or latency > 8s
  ▼
Gemini 3.5 Flash (Fallback)
  │ ← failure
  ▼
Local Ollama (qwen2.5-bazi:7b)
```

---

## Handoff Notes for Next Developer

See [project.md](./project.md) for:
- Full API specification
- Complete data flow diagrams
- BaZi algorithm reference
- Deployment checklist

Environment variables: see [.env.example](./.env.example)

All core logic is pure Python with no external dependencies — unit tests confirm correctness of solar time and pillar calculations before any LLM is involved.

---

## License

MIT — See LICENSE file.
