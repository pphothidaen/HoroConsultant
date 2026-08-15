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
const AI_ROUTE_BUDGET_MS = Number(process.env.VERCEL_AI_ROUTE_BUDGET_MS || 8000);
const AI_KEY_GUARD_HINTS = ["replace", "your_", "your ", "dummy", "test_", "sample", "placeholder", "changeme", "set_me", "set-me"];
const INTERPRET_MIN_LENGTH = 100;

const CLIENT_LOCATION_FALLBACK = {
  "กรุงเทพ": {
    location: "กรุงเทพมหานคร, ประเทศไทย",
    latitude: 13.7563,
    longitude: 100.5018,
    timezone: "Asia/Bangkok",
    utc_offset_hours: 7.0,
  },
  "กรุงเทพมหานคร": {
    location: "กรุงเทพมหานคร, ประเทศไทย",
    latitude: 13.7563,
    longitude: 100.5018,
    timezone: "Asia/Bangkok",
    utc_offset_hours: 7.0,
  },
  bangkok: {
    location: "Bangkok, Thailand",
    latitude: 13.7563,
    longitude: 100.5018,
    timezone: "Asia/Bangkok",
    utc_offset_hours: 7.0,
  },
  "บางกะปิ": {
    location: "เขตบางกะปิ, กรุงเทพมหานคร, ประเทศไทย",
    latitude: 13.7658,
    longitude: 100.6439,
    timezone: "Asia/Bangkok",
    utc_offset_hours: 7.0,
  },
  "จตุจักร": {
    location: "เขตจตุจักร, กรุงเทพมหานคร, ประเทศไทย",
    latitude: 13.8166,
    longitude: 100.5604,
    timezone: "Asia/Bangkok",
    utc_offset_hours: 7.0,
  },
  สาทร: {
    location: "เขตสาทร, กรุงเทพมหานคร, ประเทศไทย",
    latitude: 13.7208,
    longitude: 100.5262,
    timezone: "Asia/Bangkok",
    utc_offset_hours: 7.0,
  },
  พญาไท: {
    location: "เขตพญาไท, กรุงเทพมหานคร, ประเทศไทย",
    latitude: 13.78,
    longitude: 100.5342,
    timezone: "Asia/Bangkok",
    utc_offset_hours: 7.0,
  },
  ปทุมวัน: {
    location: "เขตปทุมวัน, กรุงเทพมหานคร, ประเทศไทย",
    latitude: 13.7462,
    longitude: 100.5347,
    timezone: "Asia/Bangkok",
    utc_offset_hours: 7.0,
  },
  เชียงใหม่: {
    location: "อำเภอเมืองเชียงใหม่, จังหวัดเชียงใหม่, ประเทศไทย",
    latitude: 18.7883,
    longitude: 98.9853,
    timezone: "Asia/Bangkok",
    utc_offset_hours: 7.0,
  },
  "chiang mai": {
    location: "Chiang Mai, Thailand",
    latitude: 18.7883,
    longitude: 98.9853,
    timezone: "Asia/Bangkok",
    utc_offset_hours: 7.0,
  },
  ภูเก็ต: {
    location: "อำเภอเมืองภูเก็ต, จังหวัดภูเก็ต, ประเทศไทย",
    latitude: 7.8804,
    longitude: 98.3923,
    timezone: "Asia/Bangkok",
    utc_offset_hours: 7.0,
  },
  phuket: {
    location: "Phuket, Thailand",
    latitude: 7.8804,
    longitude: 98.3923,
    timezone: "Asia/Bangkok",
    utc_offset_hours: 7.0,
  },
  ชลบุรี: {
    location: "จังหวัดชลบุรี, ประเทศไทย",
    latitude: 13.3611,
    longitude: 100.9847,
    timezone: "Asia/Bangkok",
    utc_offset_hours: 7.0,
  },
  พัทยา: {
    location: "เมืองพัทยา, จังหวัดชลบุรี, ประเทศไทย",
    latitude: 12.9236,
    longitude: 100.8771,
    timezone: "Asia/Bangkok",
    utc_offset_hours: 7.0,
  },
  ขอนแก่น: {
    location: "จังหวัดขอนแก่น, ประเทศไทย",
    latitude: 16.4322,
    longitude: 102.835,
    timezone: "Asia/Bangkok",
    utc_offset_hours: 7.0,
  },
  โคราช: {
    location: "จังหวัดนครราชสีมา, ประเทศไทย",
    latitude: 14.9799,
    longitude: 102.0978,
    timezone: "Asia/Bangkok",
    utc_offset_hours: 7.0,
  },
  นครราชสีมา: {
    location: "จังหวัดนครราชสีมา, ประเทศไทย",
    latitude: 14.9799,
    longitude: 102.0978,
    timezone: "Asia/Bangkok",
    utc_offset_hours: 7.0,
  },
  สงขลา: {
    location: "จังหวัดสงขลา, ประเทศไทย",
    latitude: 7.1988,
    longitude: 100.5954,
    timezone: "Asia/Bangkok",
    utc_offset_hours: 7.0,
  },
  หาดใหญ่: {
    location: "อำเภอหาดใหญ่, จังหวัดสงขลา, ประเทศไทย",
    latitude: 7.0084,
    longitude: 100.4747,
    timezone: "Asia/Bangkok",
    utc_offset_hours: 7.0,
  },
  นนทบุรี: {
    location: "จังหวัดนนทบุรี, ประเทศไทย",
    latitude: 13.8591,
    longitude: 100.5217,
    timezone: "Asia/Bangkok",
    utc_offset_hours: 7.0,
  },
  สมุทรปราการ: {
    location: "จังหวัดสมุทรปราการ, ประเทศไทย",
    latitude: 13.5991,
    longitude: 100.5998,
    timezone: "Asia/Bangkok",
    utc_offset_hours: 7.0,
  },
  tokyo: {
    location: "Tokyo, Japan",
    latitude: 35.6895,
    longitude: 139.6917,
    timezone: "Asia/Tokyo",
    utc_offset_hours: 9.0,
  },
  โตเกียว: {
    location: "Tokyo, Japan",
    latitude: 35.6895,
    longitude: 139.6917,
    timezone: "Asia/Tokyo",
    utc_offset_hours: 9.0,
  },
  london: {
    location: "London, United Kingdom",
    latitude: 51.5074,
    longitude: -0.1276,
    timezone: "Europe/London",
    utc_offset_hours: 0.0,
  },
  ลอนดอน: {
    location: "London, United Kingdom",
    latitude: 51.5074,
    longitude: -0.1276,
    timezone: "Europe/London",
    utc_offset_hours: 0.0,
  },
  "new york": {
    location: "New York, USA",
    latitude: 40.7128,
    longitude: -74.006,
    timezone: "America/New_York",
    utc_offset_hours: -5.0,
  },
  นิวยอร์ก: {
    location: "New York, USA",
    latitude: 40.7128,
    longitude: -74.006,
    timezone: "America/New_York",
    utc_offset_hours: -5.0,
  },
  singapore: {
    location: "Singapore",
    latitude: 1.3521,
    longitude: 103.8198,
    timezone: "Asia/Singapore",
    utc_offset_hours: 8.0,
  },
  สิงคโปร์: {
    location: "Singapore",
    latitude: 1.3521,
    longitude: 103.8198,
    timezone: "Asia/Singapore",
    utc_offset_hours: 8.0,
  },
};

function isUsableApiKey(value) {
  if (typeof value !== "string") return false;
  const normalized = value.trim().toLowerCase();
  if (normalized.length < 12) return false;
  return !AI_KEY_GUARD_HINTS.some((hint) => normalized.startsWith(hint) || normalized.includes(hint));
}

function setAiHeaders(response, source, model) {
  response.setHeader("X-AI-Source", source || "backend");
  response.setHeader("X-AI-Model", model || "unknown");
}

function buildFallbackInterpretation(qText, dateStr, stem, elem) {
  const q = (qText || "").toLowerCase();
  if (/ลูก|บุตร|บริวาร|ครรภ์|มีลูก|child|son|daughter/.test(q)) {
    return `### 🔮 การวิเคราะห์ผังดวงจีนด้านบุตรหลาน (BaZi Children Analysis)\n\n- **วันเวลาเกิด**: ${dateStr}\n- **ดิถีประจำตัว**: ดิถี ${stem} (${elem})\n\n📌 บุตรหลานของดิถี ${stem} มีดาวแทน **ธาตุน้ำ (食神/傷官)** ส่งเสริมปัญญา ความคิดสร้างสรรค์ และความเป็นผู้นำในอนาคต\n\n⚠️ *[AI Inference Unavailable — Domain Template Response. Set Cloudflare AI / HF / Gemini / OpenAI keys in Vercel Env Vars for live readings.]*`;
  }
  if (/ความรัก|คู่ครอง|แฟน|แต่งงาน|รัก|love|marriage|spouse/.test(q)) {
    return `### 🔮 การวิเคราะห์ผังดวงจีนด้านความรัก (BaZi Relationship Analysis)\n\n- **วันเวลาเกิด**: ${dateStr}\n- **ดิถีประจำตัว**: ดิถี ${stem} (${elem})\n\n📌 เรือนคู่ครอง (日支) ของดิถี ${stem} ส่งผลให้มีคู่ครองที่มีเหตุผล รับผิดชอบ และเป็นที่พึ่งพาทางจิตใจ\n\n⚠️ *[AI Inference Unavailable — Domain Template Response. Set Cloudflare AI / HF / Gemini / OpenAI keys in Vercel Env Vars for live readings.]*`;
  }
  if (/อาชีพ|การงาน|ทำธุรกิจ|ทำงาน|ลงทุน|career|job|business/.test(q) || (q.includes("งาน") && !q.includes("แต่งงาน"))) {
    return `### 🔮 การวิเคราะห์ผังดวงจีนด้านอาชีพ (BaZi Career Analysis)\n\n- **วันเวลาเกิด**: ${dateStr}\n- **ดิถีประจำตัว**: ดิถี ${stem} (${elem})\n\n📌 ดาวการงาน (正官/七殺) ของดิถี ${stem} โดดเด่นในสายงานบริหาร การวางยุทธศาสตร์ เทคโนโลยี และการเงิน\n\n⚠️ *[AI Inference Unavailable — Domain Template Response. Set Cloudflare AI / HF / Gemini / OpenAI keys in Vercel Env Vars for live readings.]*`;
  }
  if (/การเงิน|เงิน|โชคลาภ|หุ้น|ทรัพย์|รวย|wealth|finance|money/.test(q)) {
    return `### 🔮 การวิเคราะห์ผังดวงจีนด้านการเงิน (BaZi Wealth Analysis)\n\n- **วันเวลาเกิด**: ${dateStr}\n- **ดิถีประจำตัว**: ดิถี ${stem} (${elem})\n\n📌 ดาวโชคลาภ (正財/偏財) ของดิถี ${stem} มีช่องทางรายได้หลากหลาย ควรเน้นลงทุนสินทรัพย์ยั่งยืนและกระจายความเสี่ยง\n\n⚠️ *[AI Inference Unavailable — Domain Template Response. Set Cloudflare AI / HF / Gemini / OpenAI keys in Vercel Env Vars for live readings.]*`;
  }
  return `### 🔮 การวิเคราะห์ผังดวงจีน 4 เสาหลัก (BaZi Comprehensive Reading)\n\n- **วันเวลาเกิด**: ${dateStr}\n- **ดิถีประจำตัว**: ดิถี ${stem} (${elem})\n- **คำถาม**: "${qText}"\n\n📌 ดวงชะตาดิถี ${stem} (${elem}) มีพลังปรับสมดุลชีวิตการงาน การเงิน ความสัมพันธ์ และสุขภาพ ตามสมดุล 5 ธาตุ\n\n⚠️ *[AI Inference Unavailable — Domain Template Response. Set Cloudflare AI / HF / Gemini / OpenAI keys in Vercel Env Vars for live readings.]*`;
}

let lastTelegramAlertTime = 0;
const TELEGRAM_ALERT_COOLDOWN_MS = 300000; // 5 minutes

async function maybeSendTelegramAlert(reason) {
  const token = process.env.TELEGRAM_BOT_TOKEN;
  const chatId = process.env.TELEGRAM_CHAT_ID;
  if (!token || !chatId) return;

  const now = Date.now();
  if (now - lastTelegramAlertTime < TELEGRAM_ALERT_COOLDOWN_MS) return;
  lastTelegramAlertTime = now;

  try {
    const text = `🚨 *[HoroConsultant AI Gateway Alert]*\n\n⚠️ *Inference Fallback Triggered*\n• *Reason:* ${reason}\n• *Action:* Active fallback to Domain Template\n• *Time:* ${new Date().toISOString()}`;
    await fetchWithTimeout(`https://api.telegram.org/bot${token}/sendMessage`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ chat_id: chatId, text, parse_mode: "Markdown" }),
    }, 3000).catch(() => {});
  } catch (err) {
    // Non-blocking
  }
}

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

function normalizeLocationQuery(value) {
  if (typeof value !== "string") return "";
  return value.trim().toLowerCase();
}

function isUsableLocationResult(payload) {
  return (
    payload &&
    typeof payload === "object" &&
    typeof payload.location === "string" &&
    Number.isFinite(Number(payload.latitude)) &&
    Number.isFinite(Number(payload.longitude)) &&
    Number.isFinite(Number(payload.utc_offset_hours))
  );
}

function resolveLocationFallback(rawBodyBuffer) {
  if (!rawBodyBuffer) return null;
  let reqBody = {};
  try {
    reqBody = JSON.parse(rawBodyBuffer.toString("utf-8"));
  } catch (e) {
    return null;
  }

  const query = normalizeLocationQuery(reqBody.location);
  if (!query) return null;

  let fallback = null;
  for (const [key, value] of Object.entries(CLIENT_LOCATION_FALLBACK)) {
    if (key.includes(query) || query.includes(key)) {
      fallback = value;
      break;
    }
  }

  if (!fallback) {
    return {
      location: `${reqBody.location} (Defaulting to Bangkok Coordinates)`,
      latitude: 13.7563,
      longitude: 100.5018,
      timezone: "Asia/Bangkok",
      utc_offset_hours: 7.0,
    };
  }

  return { ...fallback };
}

async function generateDynamicInterpretation(query, birthDatetime, dayMasterStem, dayMasterElement) {
  const qText   = (query || "").trim() || "ภาพรวมดวงชะตา โชคลาภ การงาน ความรัก และสุขภาพ";
  const dateStr = birthDatetime || "1990-05-15 14:30:00";
  const stem    = dayMasterStem    || "庚";
  const elem    = dayMasterElement || "Metal";
  const routeStartMs = Date.now();
  const routeAlive = () => Date.now() - routeStartMs < AI_ROUTE_BUDGET_MS;
  const cfAccountId = process.env.CLOUDFLARE_ACCOUNT_ID;
  const cfAiToken   = process.env.CLOUDFLARE_AI_TOKEN;
  const hfTokens = [process.env.HF_TOKEN, process.env.HUGGINGFACE_TOKEN, process.env.HUGGINGFACE_API_KEY].filter(isUsableApiKey);
  const geminiKeys = [process.env.GOOGLE_AI_STUDIO_API_KEY, process.env.GOOGLE_AI_STUDIO_API_KEY2]
    .filter(isUsableApiKey);
  const openAiKeys = [process.env.OPENAI_API_KEY, process.env.OPENAI_API_KEY2].filter(isUsableApiKey);
  const hasUsableProvider =
    hfTokens.length > 0 ||
    geminiKeys.length > 0 ||
    (isUsableApiKey(cfAccountId) && isUsableApiKey(cfAiToken)) ||
    openAiKeys.length > 0;

  if (!hasUsableProvider) {
    maybeSendTelegramAlert("No usable AI provider keys configured in environment");
    return { text: buildFallbackInterpretation(qText, dateStr, stem, elem), model: "domain-template", source: "fallback_template" };
  }

  const systemPrompt = `คุณคือปรมาจารย์โหราศาสตร์จีน BaZi (Four Pillars of Destiny - โป๊ยยี่สี่เถียว) ผู้เชี่ยวชาญตำราคลาสสิก 子平真詮 และ 滴天髓
จงวิเคราะห์ดวงชะตาและเขียนบทวิเคราะห์เป็นภาษาไทยล้วนอย่างละเอียด ลึกซึ้ง มีชีวิตชีวา ตอบคำถามเฉพาะเจาะจงของผู้ใช้โดยตรง:
- วันเวลาเกิด (True Solar Time): ${dateStr}
- ดิถีประจำตัว (Day Master): ดิถี ${stem} (${elem})
- คำถามของผู้ใช้: "${qText}"
เริ่มต้นด้วย: ### 🔮 ผลการทำนายและวิเคราะห์ผังดวงจีน (BaZi Dynamic Reading)`;

  // Route 1: HF Inference API (fine-tuned BaZi model) — PRIMARY
  for (const hfToken of hfTokens) {
    if (!routeAlive()) break;
    try {
      const res = await fetchWithTimeout(`https://api-inference.huggingface.co/models/${TARGET_BAZI_MODEL}`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${hfToken}`, "Content-Type": "application/json" },
        body: JSON.stringify({
          inputs: `<|im_start|>system\n${systemPrompt}<|im_end|>\n<|im_start|>user\n${qText}<|im_end|>\n<|im_start|>assistant\n`,
          parameters: { max_new_tokens: 1024, temperature: 0.7, return_full_text: false }
        })
      }, 4000);
      if (res.ok) {
        const data = await res.json();
        const text = Array.isArray(data) ? data[0]?.generated_text : data?.generated_text;
        if (text && text.trim().length > 100) {
          console.log(`[AI Inference] HF model OK`);
          return { text: text.trim(), model: TARGET_BAZI_MODEL, source: "ai_agent_llm" };
        }
      } else {
        console.warn(`[AI Inference Warning] HF model HTTP ${res.status}`);
      }
    } catch (err) { console.warn(`[AI Inference Warning] HF model: ${err.message}`); }
  }

  // Route 2: Google Gemini (key rotation + live model fallback) — SECONDARY
  const geminiModels = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash",
    "gemini-2.5-pro",
    "gemini-1.5-pro",
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
          maybeSendTelegramAlert("Gemini API Key returned 403 Forbidden (Blocked)");
          break;
        } else if (res.status === 400 || res.status === 404) {
          continue;
        }
      } catch (err) { console.warn(`[AI Inference Warning] Gemini ${model}: ${err.message}`); }
    }
  }

  // Route 3: Cloudflare Workers AI (with model candidate fallback) — TERTIARY
  const cfAiModels = [
    process.env.CLOUDFLARE_AI_MODEL,
    "@cf/meta/llama-3.1-8b-instruct",
    "@cf/meta/llama-3.2-3b-instruct",
    "@cf/qwen/qwen1.5-7b-chat-awq",
  ].filter(Boolean);

  if (routeAlive() && isUsableApiKey(cfAccountId) && isUsableApiKey(cfAiToken)) {
    for (const cfAiModel of cfAiModels) {
      if (!routeAlive()) break;
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
          console.warn(`[AI Inference Warning] Cloudflare AI (${cfAiModel}) HTTP ${res.status}`);
          if (res.status === 410 || res.status === 404) {
            continue; // Try next model candidate
          } else {
            break; // Auth error or account limit, move to next provider
          }
        }
      } catch (err) {
        console.warn(`[AI Inference Warning] Cloudflare AI (${cfAiModel}): ${err.message}`);
      }
    }
  }

  // Route 4: OpenAI Chat Completions fallback
  const openAiBaseUrl = (process.env.OPENAI_BASE_URL || process.env.CODEX_PRO_BASE_URL || "https://api.openai.com/v1").replace(/\/$/, "");
  const openAiModels = [process.env.OPENAI_MODEL || "gpt-4o-mini", "gpt-4o-mini", "gpt-4o"].filter((v, i, a) => a.indexOf(v) === i);
  for (const openAiKey of openAiKeys) {
    if (!routeAlive()) break;
    for (const model of openAiModels) {
      if (!routeAlive()) break;
      try {
        const res = await fetchWithTimeout(`${openAiBaseUrl}/chat/completions`, {
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
  console.warn("[AI Inference] All routes exhausted — domain template fallback.");
  return { text: buildFallbackInterpretation(qText, dateStr, stem, elem), model: "domain-template", source: "fallback_template" };
}

async function proxyRequest(request, response) {
  const target = getRequestTarget(request);
  if (!target) {
    return response.status(400).json({ status: "error", code: "invalid_gateway_target" });
  }

  let rawBodyBuffer;
  try { rawBodyBuffer = await readRequestBody(request); } catch (e) { rawBodyBuffer = undefined; }

  // Attempt 1: Proxy to FastAPI backend
  const targetIsInterpret = target.includes("/interpret");
  const targetIsLocation = target.includes("/location/resolve");
  let backendPayload = null;

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
        if (targetIsLocation && isUsableLocationResult(parsed)) {
          copyResponseHeaders(upstream, response);
          return response.status(upstream.status).send(body);
        }

        if (targetIsInterpret) {
          const interpretation = (parsed.interpretation || "").toString().trim();
          if (interpretation.length >= INTERPRET_MIN_LENGTH) {
            copyResponseHeaders(upstream, response);
            setAiHeaders(response, parsed.source || parsed.model || parsed.model_used || parsed.route, parsed.model || parsed.model_used || "unknown");
            return response.status(upstream.status).send(body);
          }
          backendPayload = parsed;
          if (Array.isArray(parsed) && parsed.length === 0) {
            backendPayload = null;
          }
        } else if (parsed.interpretation || parsed.pillars || parsed.chart || parsed.day_master) {
          copyResponseHeaders(upstream, response);
          setAiHeaders(response, parsed.source || parsed.model || parsed.model_used || parsed.route, parsed.model || parsed.model_used || "unknown");
          return response.status(upstream.status).send(body);
        }
      } catch (e) {
        if (targetIsLocation) {
          // ignore malformed/HTML responses for location and rely on local fallback
        } else {
          copyResponseHeaders(upstream, response);
          setAiHeaders(response, "backend", "unknown");
          return response.status(upstream.status).send(body);
        }
      }
    }
  } catch (error) {
    console.error("[ERROR] Backend request failed:", error.message);
  }

  if (targetIsLocation) {
    const locationResponse = resolveLocationFallback(rawBodyBuffer);
    if (locationResponse) {
      return response.status(200).json(locationResponse);
    }
    return response.status(404).json({ status: "error", code: "location_not_found" });
  }

  // Attempt 2: Local AI inference for BaZi endpoints
  if (target.includes("/interpret") || target.includes("/bazi") || target.includes("/calculate")) {
    let reqBody = {};
    try { if (rawBodyBuffer) reqBody = JSON.parse(rawBodyBuffer.toString("utf-8")); } catch (e) {}

    const query            = reqBody.query || reqBody.question || "";
    const birthDatetime    = reqBody.birth_datetime || reqBody.datetime || "1990-05-15 14:30:00";
    const dayMasterStem    = reqBody.day_master?.stem    || "庚";
    const dayMasterElement = reqBody.day_master?.element || "Metal";

    const localAiBudgetMs = Number(process.env.VERCEL_LOCAL_AI_BUDGET_MS || 8000);
    const result = await Promise.race([
      generateDynamicInterpretation(query, birthDatetime, dayMasterStem, dayMasterElement),
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error("Local AI budget exceeded")), localAiBudgetMs)
      ),
    ]).catch(() => ({
      text: buildFallbackInterpretation(query, birthDatetime, dayMasterStem, dayMasterElement),
      model: "domain-template",
      source: "fallback_timeout",
    }));
    const text   = typeof result === "object" ? result.text   : result;
    const model  = typeof result === "object" ? result.model  : TARGET_BAZI_MODEL;
    const source = typeof result === "object" ? result.source : "ai_agent_llm";

    setAiHeaders(response, source, model);

    const defaultPayload = {
      day_master: { stem: dayMasterStem, element: dayMasterElement, polarity: "Yang" },
      five_elements: { percentages: { Wood: 20.0, Fire: 25.0, Earth: 20.0, Metal: 15.0, Water: 20.0 } },
      pillars: {
        year:  { stem: "庚", branch: "午" }, month: { stem: "壬", branch: "午" },
        day:   { stem: dayMasterStem, branch: "辰" }, hour: { stem: "癸", branch: "未" },
      },
      chart: {
        day_master: { stem: dayMasterStem, element: dayMasterElement, polarity: "Yang" },
        five_elements: { percentages: { Wood: 20.0, Fire: 25.0, Earth: 20.0, Metal: 15.0, Water: 20.0 } },
        pillars: {
          year:  { stem: "庚", branch: "午" }, month: { stem: "壬", branch: "午" },
          day:   { stem: dayMasterStem, branch: "辰" }, hour: { stem: "癸", branch: "未" },
        },
      },
      interpretation: text,
      query_echo: query,
      model_used: model,
      source: source,
      status: "ok",
    };

    const mergedPayload = {
      ...defaultPayload,
      ...(typeof backendPayload === "object" && backendPayload !== null ? backendPayload : {}),
      interpretation: text,
      query_echo: backendPayload && typeof backendPayload.query_echo === "string" ? backendPayload.query_echo : query,
      model_used: backendPayload?.model_used || model,
      source: source,
      status: backendPayload?.status || "ok",
      day_master: backendPayload?.day_master || defaultPayload.day_master,
      five_elements: backendPayload?.five_elements || defaultPayload.five_elements,
      pillars: backendPayload?.pillars || defaultPayload.pillars,
      chart: backendPayload?.chart || defaultPayload.chart,
    };

    return response.status(200).json(mergedPayload);
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
    const hfTokens = [process.env.HF_TOKEN, process.env.HUGGINGFACE_TOKEN, process.env.HUGGINGFACE_API_KEY].filter(isUsableApiKey);
    const geminiKeys = [process.env.GOOGLE_AI_STUDIO_API_KEY, process.env.GOOGLE_AI_STUDIO_API_KEY2].filter(isUsableApiKey);
    const openAiKeys = [process.env.OPENAI_API_KEY, process.env.OPENAI_API_KEY2].filter(isUsableApiKey);

    return response.status(200).json({
      status: "ok",
      service: "HoroConsultant Vercel Gateway",
      version: gitCommit ? `1.0.0.${gitCommit}` : "1.0.0",
      gateway: "vercel-node-middleend",
      backend_target: BACKEND_URL,
      inference_chain: [
        { route: "hf_inference",  enabled: hfTokens.length > 0 },
        { route: "gemini_api",    enabled: geminiKeys.length > 0 },
        { route: "cloudflare_ai", enabled: Boolean(isUsableApiKey(process.env.CLOUDFLARE_ACCOUNT_ID) && isUsableApiKey(process.env.CLOUDFLARE_AI_TOKEN)) },
        { route: "openai_api",    enabled: openAiKeys.length > 0 },
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
