# 🌌 Computational Metaphysics Engine — Developer Architecture & Integration Guide

> **Project:** HoroConsultant — High-Precision 10-Domain Computational Metaphysics Engine, True Solar Time Engine, Multi-Agent Gemini & Local Ollama Hybrid Routing, FAISS Classical Vault RAG, Rust Fast Math Acceleration, and HITL Review Studio.

---

> 🚨 **GOVERNANCE MANDATE FOR DEVELOPERS & AI AGENTS (กฎการดูแลรักษาโปรเจกต์):**  
> **หากมีการเปลี่ยนแปลง โครงสร้าง สถาปัตยกรรม API Endpoint หรือฟีเจอร์ใดๆ ในโปรเจกต์นี้ นักพัฒนาและ AI Agents ทุกคน จะต้องทำการอัปเดตเอกสาร [`README.md`](file:///Users/kimlenglim/Project/HoroConsultant/README.md) และคู่มือ [`HOWTO.md`](file:///Users/kimlenglim/Project/HoroConsultant/HOWTO.md) นี้ให้เป็นปัจจุบันเสมอ** เพื่อรักษาความถูกต้อง ความแม่นยำ และความต่อเนื่องของการพัฒนาระบบ

> 📘 **คู่มือการใช้งานระบบสำหรับผู้ใช้และแพลตฟอร์มต่างๆ:**  
> สำหรับวิธีใช้งานเว็บไซต์สำหรับ End-User, การใช้งาน Admin Panel, HITL Review Studio และคู่มือการรันบนแพลตฟอร์มต่างๆ (Docker, Ollama, Kaggle GPU, MCP Server) โปรดอ่านเพิ่มเติมได้ที่ [**`HOWTO.md` (คู่มือการใช้งาน HoroConsultant Manual)**](file:///Users/kimlenglim/Project/HoroConsultant/HOWTO.md)

---

## 🏛️ C4 Software Architecture Levels

### Level 1: System Context Diagram (บริบทระบบภายนอก)

Describes how end-users, expert astrologers, and external AI services interact with the **HoroConsultant Computational Metaphysics Engine**.

```mermaid
graph TD
    User([👤 User / Client App]) -->|HTTP / Web Dashboard| Engine["🌌 HoroConsultant Engine<br/>(FastAPI + Rust Core)"]
    Admin([🔐 Admin / Astrologer]) -->|Admin Panel & HITL Studio| Engine
    MCPClient([🤖 AGY Subagent / thClaws CLI]) -->|JSON-RPC / MCP Protocol| MCPServer["🔌 MCP Server<br/>(project/mcp_server.py)"]
    
    Engine -->|Local Inference| Ollama["🦙 Local Ollama Service<br/>(qwen2.5:7b / llama3:8b)"]
    Engine -->|Cloud Multi-Agent Audit| Gemini["🛡️ Gemini API Fallback<br/>(Gemini 2.0 Flash / Pro)"]
    Engine -->|Knowledge Ingestion| GDrive["☁️ Google Drive Vault<br/>(3,132 Vector Chunks)"]
    Engine -->|Fine-Tune Pipeline| Kaggle["⚡ Kaggle GPU / HF Hub<br/>(Nvidia T4 Accelerator)"]
    
    MCPServer --> Engine

    classDef primary fill:#0f172a,stroke:#38bdf8,stroke-width:2px,color:#e2e8f0;
    classDef external fill:#1e1b4b,stroke:#a855f7,stroke-width:1.5px,color:#e9d5ff;
    class Engine,MCPServer primary;
    class Ollama,Gemini,GDrive,Kaggle external;
```

#### PlantUML Specification (Level 1 System Context):
```plantuml
@startuml C4_Level1_Context
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Context.puml

Person(user, "User / Client", "Interacts with astrology calculator & dashboards.")
Person(admin, "Admin / Astrologer", "Reviews AI outputs, manages knowledge catalog.")
System(horo, "HoroConsultant Engine", "Computational Metaphysics & Multi-Agent Calculation Engine.")

System_Ext(ollama, "Local Ollama LLM", "qwen2.5:7b local inference.")
System_Ext(gemini, "Gemini API", "Gemini 2.0 Multi-Agent Auditor & Fallback.")
System_Ext(gdrive, "Google Drive Vault", "Obsidian classical text storage.")
System_Ext(kaggle, "Kaggle GPU Hub", "Fine-tuning & LoRA training.")

Rel(user, horo, "Uses", "HTTPS / Web Dashboard")
Rel(admin, horo, "Reviews & Manages", "HTTPS / HITL & Admin UI")
Rel(horo, ollama, "Infers Locally", "HTTP API")
Rel(horo, gemini, "Validates & Audits", "HTTPS API")
Rel(horo, gdrive, "Syncs Vault", "GDrive API")
Rel(horo, kaggle, "Triggers Fine-Tune", "Kaggle CLI")
@enduml
```

---

### Level 2: Container Diagram (ตู้คอนเทนเนอร์และโครงสร้างระบบ)

Details the internal runtime containers, database layers, background schedulers, and static assets.

```mermaid
graph TB
    subgraph Frontend["Web Presentation Layer (Vanilla CSS + JS)"]
        UI_Dash["🔮 Main Dashboard<br/>(index.html + app.js)"]
        UI_Admin["🔐 Admin Panel<br/>(admin.html)"]
        UI_HITL["🔬 HITL Review Studio<br/>(hitl.html)"]
    end

    subgraph Backend["FastAPI Application Server (project/main.py)"]
        AstroRouter["🌌 Astrology Router<br/>(/api/v1/*)"]
        AdminRouter["🔐 Admin Router<br/>(/admin/*)"]
        HITLRouter["🔬 HITL Router<br/>(/hitl/*)"]
        MCPModule["🔌 MCP Server Module<br/>(mcp_server.py)"]
    end

    subgraph Accelerator["Fast Math Core Layer"]
        RustCore["⚡ Rust Native Module<br/>(rust_core / fast_math)"]
        FAISSIndex["📚 FAISS RAG Index<br/>(3,132 Vector Chunks)"]
    end

    subgraph DataStore["Persistence & Vault Layer"]
        CatalogDB[("JSON Catalog DB<br/>knowledge_catalog.json")]
        GrayzoneDB[("JSON Grayzone DB<br/>grayzone_answers.json")]
        HITLDB[("JSON HITL Reviews DB<br/>hitl_reviews.json")]
    end

    UI_Dash -->|REST API| AstroRouter
    UI_Admin -->|REST API| AdminRouter
    UI_HITL -->|REST API| HITLRouter

    AstroRouter --> RustCore
    AstroRouter --> FAISSIndex
    AdminRouter --> CatalogDB
    AdminRouter --> GrayzoneDB
    HITLRouter --> HITLDB

    classDef ui fill:#09131d,stroke:#3b82f6,stroke-width:1.5px,color:#93c5fd;
    classDef app fill:#1a0914,stroke:#ec4899,stroke-width:1.5px,color:#fbcfe8;
    classDef fast fill:#041812,stroke:#22c55e,stroke-width:1.5px,color:#86efac;
    class UI_Dash,UI_Admin,UI_HITL ui;
    class AstroRouter,AdminRouter,HITLRouter,MCPModule app;
    class RustCore,FAISSIndex fast;
```

#### PlantUML Specification (Level 2 Containers):
```plantuml
@startuml C4_Level2_Containers
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Container.puml

Container(web_ui, "Web Dashboard", "HTML5/Vanilla CSS/JS", "Main calculation dashboard & SVG visualizer.")
Container(admin_ui, "Admin & HITL UI", "HTML5/Vanilla CSS/JS", "Knowledge management & HITL review studio.")
Container(fastapi_app, "FastAPI App Server", "Python 3.12/FastAPI", "Serves REST APIs, routing, and background tasks.")
Container(rust_math, "Rust Core Engine", "Rust / PyO3", "Accelerates True Solar Time & Ephemeris math.")
ContainerDb(faiss_db, "FAISS Vector Store", "FAISS / Nomic Embed", "Stores 3,132 classical metaphysics vector chunks.")
ContainerDb(json_dbs, "Data Store Vault", "JSON DB Files", "Catalog, grayzone answers, and HITL review dataset.")

Rel(web_ui, fastapi_app, "API Calls", "HTTP / REST")
Rel(admin_ui, fastapi_app, "API Calls", "HTTP / REST")
Rel(fastapi_app, rust_math, "Calls native bindings", "C-ABI / PyO3")
Rel(fastapi_app, faiss_db, "Searches embeddings", "In-Memory Vector Search")
Rel(fastapi_app, json_dbs, "Reads/Writes JSON", "File I/O")
@enduml
```

---

### Level 3: Component Diagram (ส่วนประกอบภายในเซิร์ฟเวอร์)

Detailed structural component view of `astrology_router`, calculation engines, SVG diagram generators, and LLM Routers.

```mermaid
graph LR
    subgraph RoutingComponents["Routing & Orchestration Components"]
        HR["HybridRouter<br/>(project/api_router.py)"]
        PV["PredictionValidator<br/>(project/validator.py)"]
    end

    subgraph DisciplineEngines["10 Metaphysical Calculation Engines (project/core/*)"]
        BaZi["BaZiEngine"]
        ZiWei["ZiWeiEngine"]
        QiMen["QiMenEngine"]
        LiuRen["LiuRenEngine"]
        IChing["IChingEngine"]
        XuanKong["XuanKongEngine"]
        ZeJi["ZeJiEngine"]
        ThaiVedic["ThaiVedicEngine"]
        Western["WesternUranianEngine"]
        Numerology["NumerologyEngine"]
    end

    subgraph VisualizerComponents["SVG Vector Generator (project/core/svg_generator.py)"]
        SVGGen["SVG Diagram Generator<br/>(11 Discipline SVG Renderers)"]
    end

    DisciplineEngines --> SVGGen
    BaZi --> HR
    HR --> PV
```

#### PlantUML Specification (Level 3 Components):
```plantuml
@startuml C4_Level3_Components
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Component.puml

Container_Boundary(api_boundary, "FastAPI Core Services") {
    Component(astro_router, "Astrology Router", "FastAPI APIRouter", "Handles calculation & interpretation endpoints.")
    Component(bazi_comp, "BaZi Engine", "Python Core Module", "Calculates TST, 4 Pillars, and 5 Elements scores.")
    Component(ziwei_comp, "Zi Wei Engine", "Python Core Module", "Calculates 12 Palaces, Stars, and Si Hua mutators.")
    Component(qimen_comp, "Qi Men Engine", "Python Core Module", "Calculates 4-Plate grid (Stars, Doors, Spirits).")
    Component(svg_comp, "SVG Generator", "svg_generator.py", "Generates high-aesthetic SVG vector charts.")
    Component(hybrid_router, "Hybrid Router", "api_router.py", "Executes Ollama -> Gemini fallback chain.")
}

Rel(astro_router, bazi_comp, "Invokes calculation")
Rel(astro_router, ziwei_comp, "Invokes calculation")
Rel(astro_router, qimen_comp, "Invokes calculation")
Rel(bazi_comp, svg_comp, "Requests SVG markup")
Rel(ziwei_comp, svg_comp, "Requests SVG markup")
Rel(astro_router, hybrid_router, "Requests LLM interpretation")
@enduml
```

---

### Level 4: Code & Data Flow Diagrams (การไหลของข้อมูลและอัลกอริทึม)

#### Flowchart 1: Main Chart Calculation & Multi-Agent Audit Data Flow

```mermaid
flowchart TD
    Start([User Inputs DOB, Longitude, UTC Offset & Query]) --> TST[Calculate True Solar Time<br/>TST = LMT + EoT]
    TST --> Pillars[Calculate 4 Pillars:<br/>Year, Month, Day, Hour Pillars]
    Pillars --> Scores[Compute Five Elements Balance Scores<br/>Wood, Fire, Earth, Metal, Water %]
    Scores --> SVG[Generate SVG Vector Chart Markup<br/>project/core/svg_generator.py]
    
    SVG --> CheckLLM{Is LLM Interpretation Requested?}
    CheckLLM -- Yes --> Ollama[Call Primary Local Ollama<br/>qwen2.5:7b]
    CheckLLM -- No --> FastReturn[Return Chart JSON + SVG]
    
    Ollama -- Success --> GeminiCheck{Validation Enabled?}
    Ollama -- Timeout / 429 --> CloudFallback[Call Dual Gemini Cloud Fallback<br/>Gemini 2.0 Flash]
    CloudFallback --> GeminiCheck
    
    GeminiCheck -- Yes --> GeminiVal[Gemini Prediction Validator Audit<br/>project/validator.py]
    GeminiCheck -- No --> Combine[Combine Chart + Reading + SVG]
    
    GeminiVal --> Combine
    Combine --> RenderUI[Render Dashboard UI Cards & SVG Visualizer]
    FastReturn --> RenderUI
    RenderUI --> End([Complete])
```

#### Sequence Diagram 1: BaZi True Solar Time & AI Interpretation Sequence

```mermaid
sequenceDiagram
    autonumber
    actor User as Client UI
    participant Server as FastAPI Server
    participant BaZi as BaZi Engine
    participant SVG as SVG Generator
    participant LLM as Hybrid Router
    participant Audit as Gemini Validator

    User->>Server: POST /api/v1/bazi/interpret (DOB, Longitude, UTC, Query)
    Server->>BaZi: calculate(dt, longitude, utc_offset_hours)
    BaZi->>BaZi: Adjust TST = Local Time + LMT Offset + EoT
    BaZi-->>Server: BaZiChart Object (Pillars, DayMaster, 5 Elements)
    Server->>SVG: generate_bazi_svg(chart)
    SVG-->>Server: SVG Vector String
    Server->>LLM: generate(prompt, system_instruction)
    LLM->>LLM: Try Local Ollama (qwen2.5:7b) -> Fallback Gemini 2.0
    LLM-->>Server: Interpretation Text + Route Metadata
    Server->>Audit: validate(chart, interpretation, query)
    Audit-->>Server: Validation Report (Status, Peer Perspective, Score)
    Server-->>User: HTTP 200 JSON (Chart, Interpretation, SVG, Audit Report)
```

#### Sequence Diagram 2: HITL Review Studio Fine-Tuning Pipeline Loop

```mermaid
sequenceDiagram
    autonumber
    actor Expert as Astrologer Reviewer
    participant HITLUI as HITL Review Studio
    participant Router as HITL Router (/hitl/*)
    participant DB as HITL JSON DB
    participant Dataset as JSONL Dataset File

    Expert->>HITLUI: Select Pending Item from Review Queue
    HITLUI->>Router: GET /hitl/item/{item_id}
    Router->>DB: Load item & confidence heatmap
    DB-->>HITLUI: Return AI Output + Segments Confidence
    Expert->>HITLUI: Edit Answer & Assign Quality Stars (1-5)
    Expert->>HITLUI: Click 'Approve' or 'Edit & Save'
    HITLUI->>Router: POST /hitl/review/{item_id} (decision, final_answer, rating)
    Router->>DB: Save Review Record
    Expert->>HITLUI: Click 'Export JSONL'
    HITLUI->>Router: GET /hitl/export
    Router->>Dataset: Export approved pairs to hitl_approved.jsonl
    Router-->>HITLUI: Downloadable hitl_approved.jsonl
```

---

## ☯️ 10 Metaphysical Disciplines Overview

The system implements 10 canonical computational metaphysics disciplines, each with dedicated math engines and high-aesthetic SVG vector diagram generators:

1. **BaZi (四柱命理):** Four Pillars of Destiny, True Solar Time adjustment, Heavenly Stems, Earthly Branches, Hidden Stems, and Five Elements Percentage Scores.
2. **Zi Wei Dou Shu (紫微斗數):** 12 Palaces (Ming Gong, Shen Gong), 14 Main Stars, and Si Hua Mutators (化祿, 化權, 化科, 化忌).
3. **Qi Men Dun Jia (奇門遁甲):** 4-Plate Grid (Yang/Yin Dun 18 Ju, Nine Stars, Eight Doors, Eight Spirits).
4. **Da Liu Ren (大六壬):** 3 Transmissions (初傳, 中傳, 末傳), 4 Lessons, and 12 Heavenly Generals.
5. **I Ching & Liu Yao (易經六爻):** Primary & Transformed Hexagrams, 6 Lines, 6 Animals, and 5 Relatives setup.
6. **Xuan Kong Flying Stars (玄空風水):** Period 9 9-Grid Flying Stars (Base Star, Sitting Star, Facing Star).
7. **Ze Ji Date Selection (擇吉คำนวณฤกษ์):** 12 Duty Officers (建除十二神), Day Clash analysis, and Activity Suitability matrix.
8. **Thai Suriyayart & Vedic (โหราศาสตร์ไทย & ภารตวิทยา):** Thai Suriyayart 10 Lagna, Maha Thaksa 8 Angels, 27 Vedic Nakshatras & Vimshottari Dasha.
9. **Western Tropical & Uranian (โหราศาสตร์สากล & ยูเรเนียน):** Tropical Planetary Longitudes, 8 Uranian Transneptunian Planets (TNPs), and Midpoint Formulas.
10. **Numerology & Satta-Lek (สัตตเลข 7 ฐาน & เลขศาสตร์):** Satta-Lek 7-Base 4-Row Matrix & Chaldean Numerology Scoring.

---

## ⚡ Quick Start & Development Setup

### 1. Requirements & Prerequisites
- Python 3.12+
- Node.js & npm (optional, for Playwright visual tests)
- Local Ollama (`qwen2.5:7b` installed via `ollama pull qwen2.5:7b`)

### 2. Environment Setup

```bash
git clone https://github.com/pphothidaen/HoroConsultant.git
cd HoroConsultant
cp .env.example .env

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Run FastAPI Application

```bash
# Start dev server on http://localhost:8000
python3 -m uvicorn project.main:app --reload --port 8000
```

Access Interactive UI Dashboards:
- **Main Dashboard:** `http://localhost:8000/`
- **Admin Panel:** `http://localhost:8000/admin` (Authorized Email: `pansakorn@gmail.com`)
- **HITL Review Studio:** `http://localhost:8000/hitl-studio`
- **Interactive Swagger Docs:** `http://localhost:8000/docs`

---

## 🧪 Testing & Quality Assurance

### Run Pytest Test Suite

```bash
# Full test suite (93 unit/integration/button regression tests)
python3 -m pytest project/tests -v

# Run UI Button Regression suite specifically
python3 -m pytest project/tests/test_button_regression.py -v
```

### Run Playwright E2E Visual Screenshot Suite

```bash
# Installs playwright binaries and executes E2E screen captures
python3 -m playwright install
python3 scripts/run_e2e_screenshots.py
```

Captured screenshots are saved in `project/tests/screenshots/`.

---

## 🔌 Model Context Protocol (MCP) Server Integration

The system exposes all metaphysics tools as an **MCP Server** for integration with **AGY Subagents** and **thClaws (Rust Agent Harness)**.

```bash
# Start MCP Server via Stdin/Stdout
python3 project/mcp_server.py
```

### Exposed MCP Tools:
- `bazi_calculate`: Returns structured 4 Pillars JSON & Five Elements percentages.
- `render_bazi_svg`: Generates BaZi SVG chart and saves to `project/static/charts/bazi_chart.svg`.
- `render_zodiac_svg`: Generates 12 Zodiac Wheel SVG and saves to `project/static/charts/zodiac_wheel.svg`.
- `rag_search`: Searches 3,132 FAISS vector chunks from classical classical texts.

---

## 📝 Governance Rule Checklist for Developers

When making changes to this codebase:
- [ ] Maintain deterministic math verification in `project/core/` before calling LLMs.
- [ ] Preserve all ASCII subprocess logging tags (`[OK]`, `[ERROR]`, `[WARNING]`, `[INFO]`).
- [ ] Verify that all 22 UI buttons pass `test_button_regression.py`.
- [ ] **ALWAYS update this `README.md` document to accurately reflect any new architecture, route changes, or newly added metaphysical engines.**
