# Gemini Web Bridge MCP Toggle — Authoritative Specification

> **สถานะเอกสาร:** เอกสารฉบับนี้เป็น **Authoritative Spec** สำหรับฟีเจอร์ "Gemini Web Bridge MCP Toggle" และสามารถใช้เป็น **standalone handoff** ให้ workstream อื่นได้โดยไม่ต้องอ้างอิง ticket ต้นทาง
> Ticket อ้างอิง: `TICKET-GEMINI-BRIDGE-20260921-A2-DOCS-ENV` (branch `feat/render-primary-backend`)
> โค้ดฝั่ง client: `project/core/gemini_bridge_client.py` (`is_gemini_bridge_enabled()`, `call_bridge_tool()`)

---

## 1. Overview & Goals

HoroConsultant เพิ่มช่องทางใหม่ในการตอบคำถามที่ปรึกษา โดย **route คำถามไปยัง "Gemini Web Bridge" MCP server แบบ remote** (Cloudflare Worker) แทนการใช้โมเดล BaZi ที่ fine-tune ไว้ในเครื่อง

**เป้าหมายหลัก:**

1. **Quality uplift** — ใช้ Gemini web session ที่ผูกกับ NotebookLM notebook (project knowledge) ตอบคำถามที่ปรึกษาโดยอิงความรู้ชุดโครงการโดยตรง
2. **Zero-secret-in-repo** — token ทั้งหมดจัดการผ่าน Doppler ห้าม commit ลง repository เด็ดขาด
3. **Fail-closed / byte-identical legacy** — เมื่อ toggle ปิด หรือ bridge ล้มเหลว (HTTP 503/422/429/401, timeout, circuit open) ระบบต้อง fallback กลับสู่ HybridRouter chain เดิมและ chat template path โดยพฤติกรรมเหมือนกับก่อนมีฟีเจอร์นี้ทุกไบต์
4. **Runtime toggle** — เปิด/ปิดด้วยการ flip environment variable โดยไม่ต้อง restart service (อ่านค่าแบบ dynamic ทุกครั้งที่เรียกใช้)

---

## 2. Architecture

```
+---------------------------+
| HoroConsultant Backend    |
|  HybridRouter / chat eng. |
+------------+--------------+
             | 1. is_gemini_bridge_enabled()? (toggle ON)
             | 2. call_bridge_tool(query, birth_context, ...)
             v
+---------------------------+
| MCP Client (Python)       |
| project/core/             |
| gemini_bridge_client.py   |
+------------+--------------+
             | JSON-RPC 2.0 over HTTPS
             | POST {GEMINI_WEB_BRIDGE_URL}/mcp
             | Authorization: Bearer <token>
             v
+---------------------------+
| Cloudflare Worker         |
| gemini-web-bridge         |
|  + Durable Object (queue) |
+------------+--------------+
             | WSS (WebSocket)
             v
+---------------------------+
| Chrome Extension (local)  |
| Gemini web session        |
|  (user's browser)         |
+------------+--------------+
             | scope: notebook:b55f1ee0-384e-4bdf-ab1b-e2ee3b0063a0
             v
+---------------------------+
| NotebookLM Notebook       |
| (project knowledge)       |
+---------------------------+

PDF path (response_format="pdf"):
  Worker -> GET /artifacts/{unguessable-key}  (no Bearer, TTL 3600s)
```

**องค์ประกอบหลัก:**

- **HybridRouter / chat engine** ใน HoroConsultant backend: จุดตัดสินใจ route — ถ้า toggle เปิดจะลอง `gemini_mcp` route เป็นลำดับแรก
- **MCP Client** (`project/core/gemini_bridge_client.py`): client บาง ๆ ที่คุย JSON-RPC 2.0 กับ Worker พร้อม circuit breaker ในตัว
- **Cloudflare Worker + Durable Object**: ประสานงานคิวงานและส่งต่อผ่าน WebSocket (WSS) ไปยัง Chrome extension ที่รัน Gemini web session อยู่ในเบราว์เซอร์ของผู้ดูแล
- **NotebookLM scope**: คำตอบทั้งหมดอิง notebook `notebook:b55f1ee0-384e-4bdf-ab1b-e2ee3b0063a0` ซึ่งเก็บ project knowledge ของ HoroConsultant

---

## 3. Environment Variables

ค่าเริ่มต้นทั้งหมดฝังอยู่ในโค้ดแล้ว ไฟล์ `.env.example` เก็บ placeholder ไว้ให้ dev ใช้ local — **ห้ามใส่ token จริงในไฟล์ใด ๆ ที่ track ด้วย git**

| Variable | ค่าเริ่มต้น (ในโค้ด) | คำอธิบาย |
| :--- | :--- | :--- |
| `GEMINI_WEB_BRIDGE_ENABLED` | `"false"` | Toggle เปิด/ปิด route นี้ — `"true"`/`"false"` เท่านั้น ตั้ง `"true"` ใน Doppler `prd` เพื่อเปิดใช้งาน |
| `GEMINI_WEB_BRIDGE_URL` | `https://gemini-web-bridge.pansakorn-pho.workers.dev` | Base URL ของ Cloudflare Worker (ไม่มี trailing slash) |
| `GEMINI_WEB_BRIDGE_TOKEN` | (ไม่มี default — ต้อง provision) | Bearer token = ค่า `CLIENT_API_TOKEN` ของ bridge ฝั่ง gemini-web-bridge ดึงผ่าน Doppler ห้าม commit |
| `GEMINI_WEB_BRIDGE_SCOPE` | `notebook:b55f1ee0-384e-4bdf-ab1b-e2ee3b0063a0` | NotebookLM notebook scope ของ project knowledge |
| `GEMINI_WEB_BRIDGE_TOOL` | `horo_consult` | ชื่อ MCP tool ที่ bridge เปิดให้เรียก |
| `GEMINI_WEB_BRIDGE_TIMEOUT_S` | `90` | Timeout ต่อครั้ง (วินาที) — คำตอบจาก Gemini web session อาจช้า |

---

## 4. MCP Protocol

### 4.1 Request (โหมด text)

```
POST https://gemini-web-bridge.pansakorn-pho.workers.dev/mcp
Authorization: Bearer <GEMINI_WEB_BRIDGE_TOKEN>
Content-Type: application/json
Accept: application/json, text/event-stream
```

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "horo_consult",
    "arguments": {
      "query": "ดูดวงความรักปี 2569 ให้หน่อย",
      "birth_context": {
        "birth_datetime": "1990-05-14T08:30:00",
        "longitude": 100.5018,
        "utc_offset_hours": 7,
        "day_master": "甲 Yang Wood",
        "five_elements": {"wood": 3, "fire": 1, "earth": 2, "metal": 1, "water": 1},
        "favorable_elements": ["fire", "earth"]
      },
      "response_format": "text",
      "scope": "notebook:b55f1ee0-384e-4bdf-ab1b-e2ee3b0063a0"
    }
  }
}
```

หมายเหตุ: `birth_context` ทั้งหมดเป็น optional — ส่ง `{}` ได้หากไม่มีข้อมูลดวงกำเนิด

### 4.2 Response (โหมด text)

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "...full consultation answer..."
      }
    ]
  }
}
```

คำตอบฉบับเต็มอยู่ที่ `result.content[0].text`

### 4.3 Request / Response (โหมด pdf)

เมื่อ `response_format="pdf"` โครง request เหมือนกัน แต่เปลี่ยนค่า:

```json
{ "response_format": "pdf" }
```

Response จะมี `structuredContent.pdf_url` เพิ่มเติม:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      { "type": "text", "text": "...full consultation answer..." }
    ],
    "structuredContent": {
      "pdf_url": "https://gemini-web-bridge.pansakorn-pho.workers.dev/artifacts/<unguessable-key>"
    }
  }
}
```

### 4.4 PDF Artifact Flow, TTL และความปลอดภัย

1. Client เรียก `tools/call` ด้วย `response_format="pdf"`
2. Worker สร้าง artifact และคืน `structuredContent.pdf_url` ในรูป `GET /artifacts/{unguessable-key}`
3. ดาวน์โหลด PDF ด้วย plain `GET` — **ไม่ต้องแนบ Bearer token**
4. **TTL: artifact หมดอายุหลัง 3600 วินาที (1 ชั่วโมง)**

**Security note (สำคัญ):** เนื่องจาก endpoint ดาวน์โหลดไม่ต้องใช้ Bearer token — **unguessable key ตัวมันเองคือ credential** ระบบจึงต้อง:

- ไม่ log `pdf_url` เต็ม ๆ ลง persistent log ที่เข้าถึงได้กว้าง
- ไม่ฝัง `pdf_url` ลง cache สาธารณะหรือส่งต่อให้ third party
- ถือว่า URL หมดอายุ/ใช้ไม่ได้หลัง 1 ชั่วโมง และ client ต้องไม่ assume ว่าดาวน์โหลดซ้ำได้

### 4.5 Fail-fast HTTP Status

| HTTP | สาเหตุ |
| :--- | :--- |
| `503` | Chrome extension ออฟไลน์ (bridge ไม่มี session ให้ยิงงาน) |
| `422` | โมเดล/session ยังไม่ผ่านการ verify |
| `429` | คิวของ Durable Object เต็ม |

---

## 5. Tool Schema: `horo_consult`

| Field | Type | Required | Default | คำอธิบาย |
| :--- | :--- | :--- | :--- | :--- |
| `query` | string | **yes** | — | คำถามที่ปรึกษา (ภาษาไทยหรืออังกฤษ) |
| `birth_context` | object | no | `{}` | บริบทดวงกำเนิด — ทุก sub-field เป็น optional |
| `birth_context.birth_datetime` | string | no | — | วันเกิด+เวลา เช่น `"1990-05-14T08:30:00"` |
| `birth_context.longitude` | number | no | — | ลองจิจูดสถานที่เกิด (true solar time) |
| `birth_context.utc_offset_hours` | number | no | — | UTC offset ของสถานที่เกิด เช่น `7` |
| `birth_context.day_master` | string | no | — | Day Master เช่น `"甲 Yang Wood"` |
| `birth_context.five_elements` | object | no | — | นับห้าธาตุ เช่น `{"wood":3,"fire":1,"earth":2,"metal":1,"water":1}` |
| `birth_context.favorable_elements` | array | no | — | ธาตุที่เอื้อ เช่น `["fire","earth"]` |
| `response_format` | enum | no | `"text"` | `"text"` หรือ `"pdf"` |
| `scope` | string | no | `notebook:b55f1ee0-384e-4bdf-ab1b-e2ee3b0063a0` | NotebookLM notebook scope |

---

## 6. Toggle Semantics & Failover Chain

Python client API (`project/core/gemini_bridge_client.py`):

```python
is_gemini_bridge_enabled() -> bool

call_bridge_tool(
    query, *,
    tool=None,                # default: GEMINI_WEB_BRIDGE_TOOL
    birth_context=None,       # default: {}
    response_format="text",   # "text" | "pdf"
    scope=None,               # default: GEMINI_WEB_BRIDGE_SCOPE
    timeout_s=None,           # default: GEMINI_WEB_BRIDGE_TIMEOUT_S
) -> ({"text", "pdf_url"} | None, reason)
```

`reason` ที่เป็นไปได้: `disabled`, `no_config`, `circuit_open`, `http_503`, `http_422`, `http_401`, `http_429`, `timeout`, `empty_response`, `error:<detail>`

### 6.1 Toggle OFF (default)

```
question -> HybridRouter legacy chain -> Ollama qwen2.5:7b
                                       -> Gemini API
                                       -> Cloudflare AI
         -> chat template path (fail-closed)
```

พฤติกรรม **byte-identical legacy** — ไม่มีโค้ด bridge ถูกเรียกเลย

### 6.2 Toggle ON

```
question -> HybridRouter
              | 1. gemini_mcp route (call_bridge_tool)
              |    success  -> คืนคำตอบจาก bridge (จบ)
              |    failure  -> fall through
              v
            2. Ollama qwen2.5:7b
              | failure
              v
            3. Gemini API
              | failure
              v
            4. Cloudflare AI
              | failure
              v
            5. chat template path (fail-closed)
```

หลักการ: bridge เป็นเพียง "route แรกสุด" ไม่ใช่ single point of failure — ทุก failure reason ต้อง fall through ไป chain เดิมเสมอ

---

## 7. Circuit Breaker

- Client ฝัง **circuit breaker พร้อม cooldown 60 วินาที**
- เมื่อ bridge ล้มเหลวตามเกณฑ์ (503/422/429/timeout ฯลฯ) circuit จะ **เปิด** และ reject การเรียกครั้งถัดไปทันทีด้วย reason `circuit_open` — ไม่รอ HTTP timeout ทิ้ง
- หลัง 60 วินาที circuit จะปิดให้ลองใหม่ (half-open probe โดยปริยายผ่าน call ปกติ)
- ทุก failure ต้อง fall through ไป legacy chain ตาม section 6.2 — circuit breaker มีไว้ลด latency ไม่ใช่บล็อกคำตอบ

---

## 8. Secrets Management (Doppler)

```
Doppler project: horo-consultant
  configs: prd, dev
  secret:  GEMINI_WEB_BRIDGE_ENABLED / _URL / _TOKEN / _SCOPE / _TOOL / _TIMEOUT_S

Token source:
  gemini-web-bridge Doppler project -> CLIENT_API_TOKEN
  (คัดลอกค่านี้ไปเป็น GEMINI_WEB_BRIDGE_TOKEN ฝั่ง horo-consultant)
```

1. ดึงค่า `CLIENT_API_TOKEN` จาก Doppler project ของ **gemini-web-bridge**
2. ตั้งเป็น `GEMINI_WEB_BRIDGE_TOKEN` ใน Doppler project **`horo-consultant`** (config `prd` และ `dev` ตามสภาพแวดล้อม)
3. ตั้ง `GEMINI_WEB_BRIDGE_ENABLED=true` ใน config `prd` เพื่อเปิด route
4. Sync ค่าไปยัง Render ด้วย `scripts/sync-render-secrets.sh`
5. **ห้าม** commit token จริงลง `.env`, `.env.example`, docs, tests หรือไฟล์ใด ๆ ใน repo

---

## 9. Runtime Toggle

- Toggle อ่านจาก `GEMINI_WEB_BRIDGE_ENABLED` **แบบ dynamic ทุกครั้งที่เรียก** (`is_gemini_bridge_enabled()`) — **flip env แล้วมีผลทันที ไม่ต้อง restart** service
- ขั้นตอนเปิดใช้งาน production: Doppler `prd` ตั้ง `GEMINI_WEB_BRIDGE_ENABLED=true` -> `scripts/sync-render-secrets.sh` -> Render จะได้ env ใหม่ใน deploy/rotation ถัดไปของ Doppler sync
- ขั้นตอนปิด (เช่นเกิด incident): ตั้ง `false` แล้ว sync ซ้ำ — ระบบกลับสู่ legacy chain ทันทีโดยไม่มี side effect ค้างรอบ

---

## 10. Troubleshooting

| Reason / Status | สาเหตุ | การแก้ไข |
| :--- | :--- | :--- |
| `http_503` (HTTP 503) | Chrome extension ออฟไลน์ — ไม่มี Gemini web session ต่อ WSS อยู่ | เปิดเบราว์เซอร์และ Chrome extension ของ bridge ให้ reconnect; ตรวจสถานะ Worker/Durable Object |
| `http_422` (HTTP 422) | โมเดล/session ยังไม่ผ่านการ verify ฝั่ง bridge | ตรวจ Gemini web session ใน extension (ยอมรับเงื่อนไข/verify model) แล้วลองใหม่ |
| `http_429` (HTTP 429) | คิวของ Durable Object เต็ม | รอแล้วลองใหม่ (circuit breaker จะคุมจังหวะ); พิจารณาเพิ่ม capacity/concurrency ฝั่ง Worker |
| `http_401` (HTTP 401) | Bearer token ผิดหรือไม่ได้ตั้ง | ตรวจว่า `GEMINI_WEB_BRIDGE_TOKEN` ตรงกับ `CLIENT_API_TOKEN` ของ bridge ใน Doppler และ sync ถึง Render แล้ว |
| `timeout` | Gemini web session ตอบเกิน `GEMINI_WEB_BRIDGE_TIMEOUT_S` | เพิ่ม timeout (เช่น 120) หรือปล่อยให้ fall through ไป legacy chain; ตรวจว่า extension/เบราว์เซอร์ไม่ค้าง |
| `circuit_open` | Circuit breaker เปิดอยู่จาก failure ก่อนหน้า | รอครบ cooldown 60 วินาที — ระหว่างนั้นคำถามจะใช้ legacy chain ทันที |
| `empty_response` | Bridge ตอบกลับแต่ `content[0].text` ว่าง | ตรวจ notebook scope ว่ายังผูกกับ NotebookLM notebook ที่ถูกต้อง; ดู log ฝั่ง Worker |
| `no_config` | URL หรือ token ไม่ครบ | ตั้ง `GEMINI_WEB_BRIDGE_URL` + `GEMINI_WEB_BRIDGE_TOKEN` ให้ครบก่อนเปิด toggle |
| `disabled` | Toggle ปิดอยู่ (default) | ตั้ง `GEMINI_WEB_BRIDGE_ENABLED=true` หากต้องการใช้ route นี้ |
| `error:<detail>` | ข้อผิดพลาดอื่น ๆ จาก client/transport | อ่าน `<detail>` ใน log และไล่ตามข้อความ (เช่น DNS, TLS, JSON parse) |

---

## 11. Acceptance Checklist (สำหรับ workstream ที่รับ handoff)

- [ ] `.env.example` มีครบทั้ง 6 ตัวแปร `GEMINI_WEB_BRIDGE_*` โดยเป็น placeholder เท่านั้น
- [ ] Toggle ปิด: พฤติกรรมระบบ byte-identical กับก่อนมีฟีเจอร์
- [ ] Toggle เปิด + bridge สำเร็จ: ได้คำตอบจาก `content[0].text`
- [ ] Toggle เปิด + bridge ล้มเหลวทุก reason: fall through ไป Ollama -> Gemini API -> Cloudflare AI -> chat template สำเร็จทุกกรณี
- [ ] Circuit breaker เปิดหลัง failure และคืน reason `circuit_open` ภายใน cooldown 60 วินาที
- [ ] `response_format="pdf"` ได้ `structuredContent.pdf_url` และดาวน์โหลดได้ภายใน 3600 วินาที
- [ ] ไม่มี token จริงปรากฏในไฟล์ที่ track ด้วย git
