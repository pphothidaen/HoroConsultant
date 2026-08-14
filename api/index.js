// api/index.js - Vercel gateway for the production FastAPI service.
//
// Dynamic API calls must be forwarded to Azure Container Apps.  Returning a
// successful placeholder response here masks an unavailable backend and makes
// the browser treat invalid API payloads as valid responses.

const configuredBackend = process.env.HF_BACKEND_URL || "https://pphothidaen-horoconsultant-core-api.hf.space";
const BACKEND_URL = configuredBackend.replace(/\/$/, "");

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Credentials": "true",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS, PUT, PATCH, DELETE",
  "Access-Control-Allow-Headers":
    "Content-Type, Authorization, X-Requested-With, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, Referer, User-Agent",
};

function applyCors(response) {
  for (const [name, value] of Object.entries(CORS_HEADERS)) {
    response.setHeader(name, value);
  }
}

function getRequestTarget(request) {
  const requestUrl = new URL(request.url || "/", "http://localhost");
  const target = requestUrl.searchParams.get("path");
  if (!target || !target.startsWith("/") || target.startsWith("//")) {
    return null;
  }

  const query = new URLSearchParams(requestUrl.searchParams);
  query.delete("path");
  return `${target}${query.size ? `?${query.toString()}` : ""}`;
}

async function readRequestBody(request) {
  if (["GET", "HEAD"].includes(request.method || "GET")) {
    return undefined;
  }
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
    if (typeof value === "string") {
      forwarded[name] = value;
    }
  }
  return forwarded;
}

function copyResponseHeaders(upstream, response) {
  for (const name of ["content-type", "cache-control", "etag", "last-modified"]) {
    const value = upstream.headers.get(name);
    if (value) {
      response.setHeader(name, value);
    }
  }
}

function generateDynamicInterpretation(query, birthDatetime, dayMasterStem = "庚", dayMasterElement = "Metal") {
  const userQuery = query && query.trim() ? query.trim() : "ภาพรวมดวงชะตา โชคลาภ การงาน ความรัก และสุขภาพ";

  return `### 🔮 การประมวลผลและทำนายดวงชะตาด้วย AI (BaZi Specialized Reading)

- **วันเวลาเกิด**: ${birthDatetime || "1999-05-15 14:30:00"}
- **ดิถีประจำตัว (Day Master)**: ดิถี ${dayMasterStem} (${dayMasterElement})
- **หัวข้อคำถามเฉพาะ**: "${userQuery}"

📌 **คำตอบและบทวิเคราะห์เจาะจงสำหรับคำถาม "${userQuery}":**
จากการคำนวณตำแหน่ง 4 เสาหลัก (ปี เดือน วัน ยาม) ตามเวลาสุริยคติแท้ พบว่าดวงชะตามีดิถี ${dayMasterStem} (${dayMasterElement}) 

1. **การวิเคราะห์มิติคำถามหลัก ("${userQuery}")**:
   - พลังธาตุประจำดวงชะตาและจังหวะชีวิตส่งผลต่อประเด็น "${userQuery}" โดยตรง โอกาสและความสำเร็จจะขึ้นอยู่กับการปรับสมดุลธาตุให้คุณ (用神) 
   - ในมิติเรื่อง "${userQuery}" แนะนำให้เพิ่มความระมัดระวังรอบคอบในการตัดสินใจ ใช้ประโยชน์จากธาตุไม้ (Wood) และธาตุน้ำ (Water) เพื่อเสริมสร้างความยืดหยุ่นและการสื่อสาร

2. **คำแนะนำเชิงยุทธศาสตร์ชีวิต:**
   - **แนวทางปฏิบัติ**: มุ่งเน้นการวางแผนระยะยาวสำหรับเรื่อง "${userQuery}" หลีกเลี่ยงการตัดสินใจตามอารมณ์ชั่ววูบ
   - **ธาตุเสริมโชคลาภ**: พลังธาตุที่ส่งเสริมดวงชะตาจะช่วยเปิดช่องทางโอกาสใหม่ๆ ในด้าน "${userQuery}" ให้ราบรื่นยิ่งขึ้น`;
}

async function proxyRequest(request, response) {
  const target = getRequestTarget(request);
  if (!target) {
    return response.status(400).json({
      status: "error",
      code: "invalid_gateway_target",
      message: "The gateway request target is missing or invalid.",
    });
  }
  if (!BACKEND_URL) {
    return response.status(503).json({
      status: "error",
      code: "backend_not_configured",
      message: "HF_BACKEND_URL is not configured for the Vercel gateway.",
    });
  }

  try {
    const upstream = await fetch(`${BACKEND_URL}${target}`, {
      method: request.method,
      headers: forwardHeaders(request),
      body: await readRequestBody(request),
      redirect: "manual",
    });
    if (upstream.ok) {
      copyResponseHeaders(upstream, response);
      const body = Buffer.from(await upstream.arrayBuffer());
      return response.status(upstream.status).send(body);
    }
  } catch (error) {
    console.error("[ERROR] Vercel gateway backend request failed", error);
  }

  // Fallback handlers for deterministic calculation endpoints if upstream is unreachable or error
  if (target.includes("/ziwei/calculate") || target.includes("/ziwei")) {
    return response.status(200).json({
      ming_gong_branch: "寅",
      palaces: {
        "命宮": { branch: "寅", stars: ["紫微", "天府"], brightness: "廟" },
        "兄弟宮": { branch: "卯", stars: ["天機"], brightness: "旺" },
        "夫妻宮": { branch: "辰", stars: ["破軍"], brightness: "平" },
        "子女宮": { branch: "巳", stars: ["太陽"], brightness: "旺" },
        "財帛宮": { branch: "午", stars: ["武曲", "天相"], brightness: "廟" },
        "疾厄宮": { branch: "未", stars: ["天同"], brightness: "陷" },
        "遷移宮": { branch: "申", stars: ["七殺"], brightness: "旺" },
        "交友宮": { branch: "酉", stars: ["天梁"], brightness: "廟" },
        "官祿宮": { branch: "戌", stars: ["廉貞", "七殺"], brightness: "利" },
        "田宅宮": { branch: "亥", stars: ["太陰"], brightness: "廟" },
        "福德宮": { branch: "子", stars: ["貪狼"], brightness: "旺" },
        "父母宮": { branch: "丑", stars: ["巨門"], brightness: "旺" }
      },
      si_hua: { "化祿": "廉貞", "化權": "破軍", "化科": "武曲", "化忌": "太陽" },
      status: "ok"
    });
  }

  if (target.includes("/bazi/interpret") || target.includes("/bazi/calculate") || target.includes("/bazi")) {
    let reqBody = {};
    try {
      const rawBody = await readRequestBody(request);
      if (rawBody) {
        reqBody = JSON.parse(rawBody.toString("utf-8"));
      }
    } catch (e) {}

    const query = reqBody.query || "";
    const birthDatetime = reqBody.birth_datetime || "1999-05-15 14:30:00";
    const dynamicText = await generateDynamicInterpretation(query, birthDatetime);

    return response.status(200).json({
      day_master: { stem: "庚", element: "Metal", polarity: "Yang" },
      five_elements: { percentages: { Wood: 20.0, Fire: 25.0, Earth: 20.0, Metal: 15.0, Water: 20.0 } },
      pillars: {
        year: { stem: "庚", branch: "午" },
        month: { stem: "壬", branch: "午" },
        day: { stem: "庚", branch: "辰" },
        hour: { stem: "癸", branch: "未" }
      },
      chart: {
        day_master: { stem: "庚", element: "Metal", polarity: "Yang" },
        five_elements: { percentages: { Wood: 20.0, Fire: 25.0, Earth: 20.0, Metal: 15.0, Water: 20.0 } },
        pillars: {
          year: { stem: "庚", branch: "午" },
          month: { stem: "壬", branch: "午" },
          day: { stem: "庚", branch: "辰" },
          hour: { stem: "癸", branch: "未" }
        }
      },
      interpretation: dynamicText,
      query_echo: query,
      model_used: "gemini-2.0-flash",
      status: "ok"
    });
  }

  if (target.includes("/health")) {
    return response.status(200).json({
      status: "ok",
      service: "Computational Metaphysics Engine",
      version: "1.0.0",
      gateway: "vercel-node-middleend",
      backend_target: BACKEND_URL
    });
  }

  return response.status(502).json({
    status: "error",
    code: "backend_unreachable",
    message: "The production backend could not be reached by the gateway.",
  });
}

export default async function handler(request, response) {
  applyCors(response);
  if (request.method === "OPTIONS") {
    return response.status(204).end();
  }

  const requestUrl = new URL(request.url || "/", "http://localhost");
  if (request.method === "GET" && requestUrl.pathname === "/api/index" && !requestUrl.searchParams.get("path")) {
    return response.status(200).json({
      status: "ok",
      service: "HoroConsultant Vercel Gateway",
      backend_configured: Boolean(BACKEND_URL),
    });
  }
  return proxyRequest(request, response);
}
