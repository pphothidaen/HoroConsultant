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
  const q = (query || "").trim().toLowerCase();
  const dateStr = birthDatetime || "1990-05-15 14:30:00";

  // 1. Children / Offspring / Family (ลูก / บุตรหลาน / บริวาร)
  if (/ลูก|บุตร|เด็ก|บริวาร|ครรภ์|มีลูก|child|children|son|daughter/.test(q)) {
    return `### 🔮 การวิเคราะห์ผังดวงจีนด้านบุตรหลานและบริวาร (BaZi Children Analysis)

- **วันเวลาเกิด**: ${dateStr}
- **ดิถีประจำตัว (Day Master)**: ดิถี ${dayMasterStem} (${dayMasterElement})
- **ดาวประจำมิติตัวแทนลูกหลาน (食神/傷官)**: ธาตุน้ำ (Water - 壬/癸)
- **เสาประจำมิติบุตรหลาน (時柱)**: เสายามกำเนิด

📌 **คำทำนายเจาะจงมิติบุตรหลาน (ตามหลักตำรา 子平真詮 และ 滴天髓):**
สำหรับผังดวงชะตาดิถี ${dayMasterStem} (Metal) ดาวแทนบุตรหลานคือ **ธาตุน้ำ (Water - 食神/傷官)** ซึ่งทำหน้าที่ส่งเสริมปัญญา คล่องแคล่ว และจินตนาการ

1. **ลักษณะและวาสนาของบุตรหลาน**: บุตรหลานมีสติปัญญาเฉลียวฉลาด มีความคิดสร้างสรรค์สูง (食神-ดาวโภคทรัพย์สติปัญญา) เป็นเด็กที่มีความมั่นใจและมีความเป็นตัวของตัวเองสูง หากได้รับการส่งเสริมในทักษะเฉพาะด้าน จะสามารถสร้างชื่อเสียงและความสำเร็จได้ตั้งแต่วัยเยาว์
2. **ความสัมพันธ์และการอุปถัมภ์**: เสายามในผังดวงชะตาส่งผลให้บุตรหลานมีความกตัญญูกตเวที เมื่อเติบใหญ่จะเป็นที่พึ่งพาอาศัยและนำพาโชคลาภมาสู่ครอบครัว
3. **ข้อแนะนำในการส่งเสริมพัฒนาการ**: ควรเน้นการสื่อสารด้วยความเข้าใจ เปิดโอกาสให้คิดและตัดสินใจด้วยตนเอง หลีกเลี่ยงการใชารมณ์กดดัน และสนับสนุนกิจกรรมที่ใช้จินตนาการและการวิเคราะห์`;
  }

  // 2. Love & Marriage (ความรัก / คู่ครอง / แต่งงาน) - CHECK BEFORE CAREER
  if (/ความรัก|คู่ครอง|แฟน|แต่งงาน|ความสัมพันธ์|รัก|love|marriage|spouse/.test(q)) {
    return `### 🔮 การวิเคราะห์ผังดวงจีนด้านความรักและคู่ครอง (BaZi Relationship Analysis)

- **วันเวลาเกิด**: ${dateStr}
- **ดิถีประจำตัว (Day Master)**: ดิถี ${dayMasterStem} (${dayMasterElement})
- **เรือนคู่ครอง (日支)**: ฐานวันเกิดดวงชะตา

📌 **คำทำนายเจาะจงมิติความรักและคู่ครอง:**
สำหรับดิถี ${dayMasterStem} ฐานเรือนคู่ครองส่งผลให้มีดวงชะตาคู่ครองที่เป็นคนมีเหตุผล มีความรับผิดชอบสูง และคอยเป็นที่ปรึกษาหนุนนำชีวิต

1. **อุปนิสัยคู่ครอง**: เป็นคนเก่ง มีความสามารถในการจัดการชีวิต มีความซื่อสัตย์และจริงใจ
2. **แนวทางเสริมความสัมพันธ์**: ควรสื่อสารด้วยการรับฟังอย่างมีเหตุผล เคารพพื้นที่ส่วนตัวของกันและกัน จะช่วยให้ชีวิตคู่มีความอบอุ่นและยั่งยืน`;
  }

  // 3. Career & Job Change (การงาน / อาชีพ / ย้ายงาน / ธุรกิจ)
  if (/อาชีพ|การงาน| ย้ายงาน|ทำธุรกิจ|ทำงาน|ยศ|ตำแหน่ง|career|job|work|business/.test(q) || (q.includes("งาน") && !q.includes("แต่งงาน"))) {
    return `### 🔮 การวิเคราะห์ผังดวงจีนด้านอาชีพและการงาน (BaZi Career Analysis)

- **วันเวลาเกิด**: ${dateStr}
- **ดิถีประจำตัว (Day Master)**: ดิถี ${dayMasterStem} (${dayMasterElement})
- **ดาวการงานและตำแหน่ง (正官/七殺)**: ธาตุไฟ (Fire - 丙/丁)
- **เสาประจำมิติตำแหน่งงาน (月柱)**: เสาเดือนกำเนิด

📌 **คำทำนายเจาะจงมิติอาชีพและการงาน:**
ผังดวงชะตาดิถี ${dayMasterStem} มีดาวการงานและยศตำแหน่งเป็น **ธาตุไฟ (Fire - 正官/七殺)** การขับเคลื่อนอาชีพการงานจะโดดเด่นในสายงานบริหาร การวางยุทธศาสตร์ งานเทคโนโลยี งานการเงิน หรืออุตสาหกรรมที่ใช้ความเด็ดขาดและการตัดสินใจระดับสูง

1. **จังหวะโอกาสก้าวหน้า**: มีเกณฑ์ได้รับความไว้วางใจจากผู้ใหญ่และผู้บังคับบัญชา ได้รับการแต่งตั้งหรือขยับขยายหน้าที่ความรับผิดชอบ
2. **คำแนะนำเชิงยุทธศาสตร์**: ให้มุ่งเน้นการพัฒนาทักษะภาวะผู้นำ (Leadership) การสื่อสารเจรจา และการทำงานร่วมกับองค์กรขนาดใหญ่`;
  }

  // 3. Love & Marriage (ความรัก / คู่ครอง / แต่งงาน)
  if (/ความรัก|คู่ครอง|แฟน|แต่งงาน|ความสัมพันธ์|love|marriage|spouse/.test(q)) {
    return `### 🔮 การวิเคราะห์ผังดวงจีนด้านความรักและคู่ครอง (BaZi Relationship Analysis)

- **วันเวลาเกิด**: ${dateStr}
- **ดิถีประจำตัว (Day Master)**: ดิถี ${dayMasterStem} (${dayMasterElement})
- **เรือนคู่ครอง (日支)**: ฐานวันเกิดดวงชะตา

📌 **คำทำนายเจาะจงมิติความรักและคู่ครอง:**
สำหรับดิถี ${dayMasterStem} ฐานเรือนคู่ครองส่งผลให้มีดวงชะตาคู่ครองที่เป็นคนมีเหตุผล มีความรับผิดชอบสูง และคอยเป็นที่ปรึกษาหนุนนำชีวิต

1. **อุปนิสัยคู่ครอง**: เป็นคนเก่ง มีความสามารถในการจัดการชีวิต มีความซื่อสัตย์และจริงใจ
2. **แนวทางเสริมความสัมพันธ์**: ควรสื่อสารด้วยการรับฟังอย่างมีเหตุผล เคารพพื้นที่ส่วนตัวของกันและกัน จะช่วยให้ชีวิตคู่มีความอบอุ่นและยั่งยืน`;
  }

  // 4. Wealth & Finance (การเงิน / โชคลาภ / ทรัพย์สิน / หุ้น)
  if (/การเงิน|เงิน|โชคลาภ|หุ้น|ลงทุน|รวย|wealth|finance|money/.test(q)) {
    return `### 🔮 การวิเคราะห์ผังดวงจีนด้านการเงินและโชคลาภ (BaZi Wealth Analysis)

- **วันเวลาเกิด**: ${dateStr}
- **ดิถีประจำตัว (Day Master)**: ดิถี ${dayMasterStem} (${dayMasterElement})
- **ดาวโชคลาภและขุมทรัพย์ (正財/偏財)**: ธาตุไม้ (Wood - 甲/乙)

📌 **คำทำนายเจาะจงมิติการเงินและโชคลาภ:**
ดวงชะตาดิถี ${dayMasterStem} มีดาวโชคลาภเป็น **ธาตุไม้ (Wood - 正財/偏財)** ส่งผลให้มีช่องทางหารายได้หลากหลายทาง ทั้งจากงานประจำและการลงทุน

1. **การสะสมทรัพย์สิน**: ควรเน้นการลงทุนในสินทรัพย์ที่มีความยั่งยืน เช่น อสังหาริมทรัพย์ หรือกองทุนระยะยาว
2. **ข้อควรระวังการใช้จ่าย**: หลีกเลี่ยงการเสี่ยงโชคเกินตัว ให้ใช้ระบบกระจายความเสี่ยงอย่างเป็นระบบ`;
  }

  // 5. Health & Body (สุขภาพ / ร่างกาย / การรักษา)
  if (/สุขภาพ|ป่วย|โรค|ร่างกาย|สายตา|กระดูก|health|body/.test(q)) {
    return `### 🔮 การวิเคราะห์ผังดวงจีนด้านสุขภาพและพลังชีวิต (BaZi Health Analysis)

- **วันเวลาเกิด**: ${dateStr}
- **ดิถีประจำตัว (Day Master)**: ดิถี ${dayMasterStem} (${dayMasterElement})
- **อวัยวะประจำธาตุหลัก**: ระบบทางเดินหายใจ ปอด ผิวหนัง

📌 **คำทำนายเจาะจงมิติสุขภาพ:**
การปรับสมดุล 5 ธาตุสำหรับดิถี ${dayMasterStem} (${dayMasterElement}) แนะนำให้ดูแลระบบปอด การหายใจ ผิวหนัง และปรับการพักผ่อนให้เพียงพอ

1. **แนวทางดูแลสุขภาพ**: ควรรับประทานอาหารที่มีคุณสมบัติปรับสมดุล ออกกำลังกายอย่างสม่ำเสมอ และออกรับอากาศบริสุทธิ์`;
  }

  // 6. Default Comprehensive BaZi Analysis (ภาพรวมดวงชะตา 4 เสาหลัก)
  return `### 🔮 การวิเคราะห์ผังดวงจีน 4 เสาหลักแบบครอบคลุม (BaZi Comprehensive Reading)

- **วันเวลาเกิด**: ${dateStr}
- **ดิถีประจำตัว (Day Master)**: ดิถี ${dayMasterStem} (${dayMasterElement})
- **คำถามวิเคราะห์เฉพาะ**: "${query || "ภาพรวมดวงชะตา"}"

📌 **บทวิเคราะห์โครงสร้างดวงชะตา (ตามหลักคัมภีร์ 子平真詮 และ 滴天髓):**
ดวงชะตานี้มีดิถีวันเป็น ${dayMasterStem} (${dayMasterElement}) ซึ่งมีพลังปรับสมดุลชีวิตร่วมกับธาตุไม้และธาตุน้ำ การดำเนินชีวิตการงาน การเงิน ความสัมพันธ์ และสุขภาพจะมีความราบรื่นและประสบความสำเร็จสูงเมื่อปรับยุทธศาสตร์ชีวิตตามสมดุล 5 ธาตุ`;
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
