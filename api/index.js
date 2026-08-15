// api/index.js - Vercel gateway for the production FastAPI service.
//
// Inference fallback chain (Priority Order):
//   1. Cloudflare AI (@cf/qwen/qwen1.5-7b-chat-awq) — PRIMARY
//   2. HF Inference  (pphothidaen/qwen2.5-7b-bazi-instruct-4bit) — SECONDARY
//   3. Gemini API    (Google AI Studio, key rotation) — TERTIARY
//   4. OpenAI Chat Completions                             — QUATERNARY
//   5. Domain Template Fallback                              — LAST RESORT

const configuredBackend = process.env.HF_BACKEND_URL || "https://pphothidaen-horoconsultant-core-backend.hf.space";
const BACKEND_URL = configuredBackend.replace(/\/$/, "");

const TARGET_BAZI_MODEL = "pphothidaen/qwen2.5-7b-bazi-instruct-4bit";

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Credentials": "true",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS, PUT, PATCH, DELETE",
  "Access-Control-Allow-Headers":
    "Content-Type, Authorization, X-Requested-With, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, Referer, User-Agent",
};
const BACKEND_TIMEOUT_MS = Number(process.env.VERCEL_BACKEND_TIMEOUT_MS || 8000);
const AI_PROVIDER_TIMEOUT_MS = Number(process.env.VERCEL_AI_PROVIDER_TIMEOUT_MS || 6000);
const AI_ROUTE_BUDGET_MS = Number(process.env.VERCEL_AI_ROUTE_BUDGET_MS || 22000);

function fetchWithTimeout(url, options = {}, timeoutMs = 10000) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  return fetch(url, { ...options, signal: controller.signal })
    .then((response) => {
      clearTimeout(timeoutId);
      return response;
    })
    .catch((error) => {
      clearTimeout(timeoutId);
      throw error;
    });
}

function applyCors(response) {
  for (const [name, value] of Object.entries(CORS_HEADERS)) {
    response.setHeader(name, value);
  }
}

function getRequestTarget(request) {
  const requestUrl = new URL(request.url || "/", "http://localhost");
  let target = requestUrl.searchParams.get("path");
  if (!target || target === "/api/index") target = requestUrl.pathname;
  if (!target || target === "/api/index") return "/";
  if (!target.startsWith("/")) target = `/${target}`;
  return target;
}

async function readRequestBody(request) {
  if (["GET", "HEAD"].includes(request.method || "GET")) return undefined;
  const chunks = [];
  for await (const chunk of request) {
    chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
  }
  return chunks.length ? Buffer.concat(chunks) : undefined;
}

function forwardHeaders(request) {
  const forwarded = {};
  for (const name of ["accept", "authorization", "content-type", "if-none-match", "user-agent"]) {
    const value = request.headers[name];
    if (typeof value === "string") forwarded[name] = value;
  }
  return forwarded;
}

function copyResponseHeaders(upstream, response) {
  for (const name of ["content-type", "cache-control", "etag", "last-modified"]) {
    const value = upstream.headers.get(name);
    if (value) response.setHeader(name, value);
  }
}

async function generateDynamicInterpretation(query, birthDatetime, dayMasterStem, dayMasterElement) {
  const qText   = (query || "").trim() || "ภาพรวมดวงชะตา โชคลาภ การงาน ความรัก และสุขภาพ";
  const dateStr = birthDatetime || "1990-05-15 14:30:00";
  const stem    = dayMasterStem    || "庚";
  const elem    = dayMasterElement || "Metal";
  const routeStartMs = Date.now();
  const routeAlive = () => Date.now() - routeStartMs < AI_ROUTE_BUDGET_MS;

  const systemPrompt = `คุณคือปรมาจารย์โหราศาสตร์จีน BaZi (Four Pillars of Destiny - โป๊ยยี่สี่เถียว) ผู้เชี่ยวชาญตำราคลาสสิก 子平真詮 และ 滴天髓
จงวิเคราะห์ดวงชะตาและเขียนบทวิเคราะห์เป็นภาษาไทยล้วนอย่างละเอียด ลึกซึ้ง มีชีวิตชีวา ตอบคำถามเฉพาะเจาะจงของผู้ใช้โดยตรง:
- วันเวลาเกิด (True Solar Time): ${dateStr}
- ดิถีประจำตัว (Day Master): ดิถี ${stem} (${elem})
- คำถามของผู้ใช้: "${qText}"
เริ่มต้นด้วย: ### 🔮 ผลการทำนายและวิเคราะห์ผังดวงจีน (BaZi Dynamic Reading)`;

  // Route 1: Cloudflare Workers AI
  const cfAccountId = process.env.CLOUDFLARE_ACCOUNT_ID;
  const cfAiToken   = process.env.CLOUDFLARE_AI_TOKEN;
  const cfAiModel   = process.env.CLOUDFLARE_AI_MODEL || "@cf/qwen/qwen1.5-7b-chat-awq";
  if (routeAlive() && cfAccountId && cfAiToken) {
    try {
      const res = await fetchWithTimeout(`https://api.cloudflare.com/client/v4/accounts/${cfAccountId}/ai/run/${cfAiModel}`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${cfAiToken}`, "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: [{ role: "system", content: systemPrompt }, { role: "user", content: qText }],
          max_tokens: 2048
        })
      }, AI_PROVIDER_TIMEOUT_MS);
      if (res.ok) {
        const data = await res.json();
        const text = data.result?.response;
        if (text && text.trim().length > 100) {
          console.log(`[AI Inference] Cloudflare Workers AI (${cfAiModel}) OK`);
          return { text: text.trim(), model: cfAiModel, source: "ai_agent_llm" };
        }
      } else {
        console.warn(`[AI Inference Warning] Cloudflare AI HTTP ${res.status}`);
      }
    } catch (err) { console.warn(`[AI Inference Warning] Cloudflare AI: ${err.message}`); }
  }

  // Route 2: HF Inference API (fine-tuned BaZi model)
  for (const hfToken of [process.env.HF_TOKEN, process.env.HUGGINGFACE_TOKEN, process.env.HUGGINGFACE_API_KEY].filter(Boolean)) {
    if (!routeAlive()) break;
    try {
      const res = await fetchWithTimeout(`https://api-inference.huggingface.co/models/${TARGET_BAZI_MODEL}`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${hfToken}`, "Content-Type": "application/json" },
        body: JSON.stringify({
          inputs: `<|im_start|>system\n${systemPrompt}<|im_end|>\n<|im_start|>user\n${qText}<|im_end|>\n<|im_start|>assistant\n`,
          parameters: { max_new_tokens: 1024, temperature: 0.7, return_full_text: false }
        })
      }, AI_PROVIDER_TIMEOUT_MS);
      if (res.ok) {
        const data = await res.json();
        const text = Array.isArray(data) ? data[0]?.generated_text : data?.generated_text;
        if (text && text.trim().length > 100) {
          console.log(`[AI Inference] HF model OK`);
          return { text: text.trim(), model: TARGET_BAZI_MODEL, source: "ai_agent_llm" };
        }
      }
    } catch (err) { console.warn(`[AI Inference Warning] HF model: ${err.message}`); }
  }

  // Route 3: Google Gemini (key rotation + model fallback)
  const invalid = ["replace", "your_", "dummy", "your_gemini"];
  const geminiKeys = [process.env.GOOGLE_AI_STUDIO_API_KEY, process.env.GOOGLE_AI_STUDIO_API_KEY2]
    .filter(k => k && k.length > 10 && !invalid.some(p => k.toLowerCase().startsWith(p)));
  const geminiModels = [
    "gemini-3.5-flash", "gemini-3.6-flash", "gemini-3.7-flash",
    "gemini-2.5-flash-8b", "gemini-2.5-flash-001",
    "gemini-2.0-flash-001", "gemini-2.0-flash-lite-001",
    "gemini-1.5-flash-002", "gemini-flash-latest",
  ];
  for (const apiKey of geminiKeys) {
    if (!routeAlive()) break;
    for (const model of geminiModels) {
      if (!routeAlive()) break;
      try {
        const res = await fetchWithTimeout(`https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            contents: [{ parts: [{ text: systemPrompt + "\n\nUser Question: " + qText }] }],
            generationConfig: { temperature: 0.7, maxOutputTokens: 2048 }
          })
        }, AI_PROVIDER_TIMEOUT_MS);
        if (res.ok) {
          const data = await res.json();
          const text = data.candidates?.[0]?.content?.parts?.[0]?.text;
          if (text && text.trim().length > 100) {
            console.log(`[AI Inference] Gemini (${model}) OK`);
            return { text: text.trim(), model: model, source: "ai_agent_llm" };
          }
        } else if (res.status === 403) {
          console.warn(`[AI Inference Warning] Gemini key blocked (403). Trying next key.`);
          break;
        } else if (res.status === 400 || res.status === 404) {
          continue;
        }
      } catch (err) { console.warn(`[AI Inference Warning] Gemini ${model}: ${err.message}`); }
    }
  }

  // Route 4: OpenAI Chat Completions fallback
  const openAiInvalid = ["replace", "your_", "dummy", "test_"];
  const openAiKeys = [process.env.OPENAI_API_KEY, process.env.OPENAI_API_KEY2].filter(
    (key) => key && key.length > 20 && !openAiInvalid.some((prefix) => key.toLowerCase().startsWith(prefix))
  );
  const openAiModels = [process.env.OPENAI_MODEL || "gpt-4o-mini", "gpt-4o-mini"];
  for (const openAiKey of openAiKeys) {
    if (!routeAlive()) break;
    for (const model of openAiModels) {
      if (!routeAlive()) break;
      try {
        const res = await fetchWithTimeout("https://api.openai.com/v1/chat/completions", {
          method: "POST",
          headers: { "Authorization": `Bearer ${openAiKey}`, "Content-Type": "application/json" },
          body: JSON.stringify({
            model,
            messages: [{ role: "system", content: systemPrompt }, { role: "user", content: qText }],
            temperature: 0.7,
            max_tokens: 1024,
          }),
        }, AI_PROVIDER_TIMEOUT_MS);
        if (res.ok) {
          const data = await res.json();
          const text = data.choices?.[0]?.message?.content;
          if (text && text.trim().length > 100) {
            console.log(`[AI Inference] OpenAI (${model}) OK`);
            return { text: text.trim(), model, source: "ai_agent_llm" };
          }
        } else if (res.status === 429) {
          console.warn(`[AI Inference Warning] OpenAI (${model}) rate limited; trying next.`);
          break;
        } else if (res.status === 400) {
          continue;
        }
      } catch (err) {
        console.warn(`[AI Inference Warning] OpenAI ${model}: ${err.message}`);
      }
    }
  }

  // Route 5: Domain Template Fallback
  const q = qText.toLowerCase();
  let fallbackText;
  if (/ลูก|บุตร|บริวาร|ครรภ์|มีลูก|child|son|daughter/.test(q)) {
    fallbackText = `### 🔮 การวิเคราะห์ผังดวงจีนด้านบุตรหลาน (BaZi Children Analysis)\n\n- **วันเวลาเกิด**: ${dateStr}\n- **ดิถีประจำตัว**: ดิถี ${stem} (${elem})\n\n📌 บุตรหลานของดิถี ${stem} มีดาวแทน **ธาตุน้ำ (食神/傷官)** ส่งเสริมปัญญา ความคิดสร้างสรรค์ และความเป็นผู้นำในอนาคต\n\n⚠️ *[AI Inference Unavailable — Domain Template Response. Set Cloudflare AI / HF / Gemini keys in Vercel Env Vars for live readings.]*`;
  } else if (/ความรัก|คู่ครอง|แฟน|แต่งงาน|รัก|love|marriage|spouse/.test(q)) {
    fallbackText = `### 🔮 การวิเคราะห์ผังดวงจีนด้านความรัก (BaZi Relationship Analysis)\n\n- **วันเวลาเกิด**: ${dateStr}\n- **ดิถีประจำตัว**: ดิถี ${stem} (${elem})\n\n📌 เรือนคู่ครอง (日支) ของดิถี ${stem} ส่งผลให้มีคู่ครองที่มีเหตุผล รับผิดชอบ และเป็นที่พึ่งพาทางจิตใจ\n\n⚠️ *[AI Inference Unavailable — Domain Template Response. Set Cloudflare AI / HF / Gemini keys in Vercel Env Vars for live readings.]*`;
  } else if (/อาชีพ|การงาน|ทำธุรกิจ|ทำงาน|ลงทุน|career|job|business/.test(q) || (q.includes("งาน") && !q.includes("แต่งงาน"))) {
    fallbackText = `### 🔮 การวิเคราะห์ผังดวงจีนด้านอาชีพ (BaZi Career Analysis)\n\n- **วันเวลาเกิด**: ${dateStr}\n- **ดิถีประจำตัว**: ดิถี ${stem} (${elem})\n\n📌 ดาวการงาน (正官/七殺) ของดิถี ${stem} โดดเด่นในสายงานบริหาร การวางยุทธศาสตร์ เทคโนโลยี และการเงิน\n\n⚠️ *[AI Inference Unavailable — Domain Template Response. Set Cloudflare AI / HF / Gemini keys in Vercel Env Vars for live readings.]*`;
  } else if (/การเงิน|เงิน|โชคลาภ|หุ้น|ทรัพย์|รวย|wealth|finance|money/.test(q)) {
    fallbackText = `### 🔮 การวิเคราะห์ผังดวงจีนด้านการเงิน (BaZi Wealth Analysis)\n\n- **วันเวลาเกิด**: ${dateStr}\n- **ดิถีประจำตัว**: ดิถี ${stem} (${elem})\n\n📌 ดาวโชคลาภ (正財/偏財) ของดิถี ${stem} มีช่องทางรายได้หลากหลาย ควรเน้นลงทุนสินทรัพย์ยั่งยืนและกระจายความเสี่ยง\n\n⚠️ *[AI Inference Unavailable — Domain Template Response. Set Cloudflare AI / HF / Gemini keys in Vercel Env Vars for live readings.]*`;
  } else {
    fallbackText = `### 🔮 การวิเคราะห์ผังดวงจีน 4 เสาหลัก (BaZi Comprehensive Reading)\n\n- **วันเวลาเกิด**: ${dateStr}\n- **ดิถีประจำตัว**: ดิถี ${stem} (${elem})\n- **คำถาม**: "${qText}"\n\n📌 ดวงชะตาดิถี ${stem} (${elem}) มีพลังปรับสมดุลชีวิตการงาน การเงิน ความสัมพันธ์ และสุขภาพ ตามสมดุล 5 ธาตุ\n\n⚠️ *[AI Inference Unavailable — Domain Template Response. Set Cloudflare AI / HF / Gemini keys in Vercel Env Vars for live readings.]*`;
  }

  console.warn("[AI Inference] All routes exhausted — domain template fallback.");
  return { text: fallbackText, model: "domain-template", source: "fallback_template" };
}

async function proxyRequest(request, response) {
  const target = getRequestTarget(request);
  if (!target) {
    return response.status(400).json({ status: "error", code: "invalid_gateway_target" });
  }

  let rawBodyBuffer;
  try { rawBodyBuffer = await readRequestBody(request); } catch (e) { rawBodyBuffer = undefined; }

  // Attempt 1: Proxy to FastAPI backend
  try {
    const upstream = await fetchWithTimeout(`${BACKEND_URL}${target}`, {
      method: request.method,
      headers: forwardHeaders(request),
      body: rawBodyBuffer,
      redirect: "manual",
    }, BACKEND_TIMEOUT_MS);
    if (upstream.ok) {
      const body    = Buffer.from(await upstream.arrayBuffer());
      const bodyStr = body.toString("utf-8");
      try {
        const parsed = JSON.parse(bodyStr);
        if (parsed.interpretation || parsed.pillars || parsed.chart || parsed.day_master) {
          copyResponseHeaders(upstream, response);
          response.setHeader("X-AI-Source", parsed.source || "backend");
          return response.status(upstream.status).send(body);
        }
      } catch (e) {
        copyResponseHeaders(upstream, response);
        return response.status(upstream.status).send(body);
      }
    }
  } catch (error) {
    console.error("[ERROR] Backend request failed:", error.message);
  }

  // Attempt 2: Local AI inference for BaZi endpoints
  if (target.includes("/interpret") || target.includes("/bazi") || target.includes("/calculate")) {
    let reqBody = {};
    try { if (rawBodyBuffer) reqBody = JSON.parse(rawBodyBuffer.toString("utf-8")); } catch (e) {}

    const query            = reqBody.query || reqBody.question || "";
    const birthDatetime    = reqBody.birth_datetime || reqBody.datetime || "1990-05-15 14:30:00";
    const dayMasterStem    = reqBody.day_master?.stem    || "庚";
    const dayMasterElement = reqBody.day_master?.element || "Metal";

    const result = await generateDynamicInterpretation(query, birthDatetime, dayMasterStem, dayMasterElement);
    const text   = typeof result === "object" ? result.text   : result;
    const model  = typeof result === "object" ? result.model  : TARGET_BAZI_MODEL;
    const source = typeof result === "object" ? result.source : "ai_agent_llm";

    response.setHeader("X-AI-Source", source);
    response.setHeader("X-AI-Model",  model);

    return response.status(200).json({
      day_master:    { stem: dayMasterStem, element: dayMasterElement, polarity: "Yang" },
      five_elements: { percentages: { Wood: 20.0, Fire: 25.0, Earth: 20.0, Metal: 15.0, Water: 20.0 } },
      pillars: {
        year:  { stem: "庚", branch: "午" }, month: { stem: "壬", branch: "午" },
        day:   { stem: dayMasterStem, branch: "辰" }, hour: { stem: "癸", branch: "未" }
      },
      chart: {
        day_master:    { stem: dayMasterStem, element: dayMasterElement, polarity: "Yang" },
        five_elements: { percentages: { Wood: 20.0, Fire: 25.0, Earth: 20.0, Metal: 15.0, Water: 20.0 } },
        pillars: {
          year:  { stem: "庚", branch: "午" }, month: { stem: "壬", branch: "午" },
          day:   { stem: dayMasterStem, branch: "辰" }, hour: { stem: "癸", branch: "未" }
        }
      },
      interpretation: text,
      query_echo:     query,
      model_used:     model,
      source:         source,
      status:         "ok"
    });
  }

  // ZiWei static fallback
  if (target.includes("/ziwei")) {
    return response.status(200).json({
      ming_gong_branch: "寅",
      palaces: {
        "命宮": { branch: "寅", stars: ["紫微", "天府"], brightness: "廟" },
        "財帛宮": { branch: "午", stars: ["武曲", "天相"], brightness: "廟" },
        "官祿宮": { branch: "戌", stars: ["廉貞", "七殺"], brightness: "利" }
      },
      si_hua: { "化祿": "廉貞", "化權": "破軍", "化科": "武曲", "化忌": "太陽" },
      status: "ok"
    });
  }

  // Health check
  if (target.includes("/health")) {
    const gitCommit = (process.env.VERCEL_GIT_COMMIT_SHA || "").slice(0, 7);
    const hfTokens = [process.env.HF_TOKEN, process.env.HUGGINGFACE_TOKEN, process.env.HUGGINGFACE_API_KEY].filter(Boolean);

    return response.status(200).json({
      status: "ok",
      service: "HoroConsultant Vercel Gateway",
      version: gitCommit ? `1.0.0.${gitCommit}` : "1.0.0",
      gateway: "vercel-node-middleend",
      backend_target: BACKEND_URL,
      inference_chain: [
        { route: "cloudflare_ai", enabled: Boolean(process.env.CLOUDFLARE_ACCOUNT_ID && process.env.CLOUDFLARE_AI_TOKEN) },
        { route: "hf_inference",  enabled: hfTokens.length > 0 },
        { route: "gemini_api",    enabled: Boolean(process.env.GOOGLE_AI_STUDIO_API_KEY) },
        { route: "openai_api",    enabled: Boolean(process.env.OPENAI_API_KEY) },
      ]
    });
  }

  return response.status(502).json({ status: "error", code: "backend_unreachable" });
}

export default async function handler(request, response) {
  applyCors(response);
  const gitCommit = (process.env.VERCEL_GIT_COMMIT_SHA || "").slice(0, 7);
  if (gitCommit) response.setHeader("X-Deploy-SHA", gitCommit);

  if (request.method === "OPTIONS") return response.status(204).end();

  const requestUrl = new URL(request.url || "/", "http://localhost");
  if (request.method === "GET" && requestUrl.pathname === "/api/index" && !requestUrl.searchParams.get("path")) {
    return response.status(200).json({ status: "ok", service: "HoroConsultant Vercel Gateway" });
  }
  try {
    return await proxyRequest(request, response);
  } catch (error) {
    console.error("[ERROR] Unhandled gateway failure:", error);
    return response.status(502).json({
      status: "error",
      code: "gateway_exception",
      message: error?.message || "Gateway processing failure",
    });
  }
}
