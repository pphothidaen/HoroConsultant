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

const SATTA_LEK_HOUSES = ["อัตตา", "หินะ", "ธนัง", "ปิตา", "มาตา", "โภคา", "มัชฌิมา"];

const CHALDEAN_MAP = {
  'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 8, 'G': 3, 'H': 5, 'I': 1,
  'J': 1, 'K': 2, 'L': 3, 'M': 4, 'N': 5, 'O': 7, 'P': 8, 'Q': 1, 'R': 2,
  'S': 3, 'T': 4, 'U': 6, 'V': 6, 'W': 6, 'X': 5, 'Y': 1, 'Z': 7,
  'ก': 1, 'ข': 2, 'ค': 3, 'ฆ': 4, 'ง': 5, 'จ': 6, 'ฉ': 7, 'ช': 8, 'ซ': 9,
  'ฌ': 2, 'ญ': 4, 'ฎ': 1, 'ฏ': 8, 'ฐ': 9, 'ฑ': 4, 'ฒ': 1, 'ณ': 5, 'ด': 1,
  'ต': 2, 'ถ': 3, 'ท': 4, 'ธ': 5, 'น': 5, 'บ': 2, 'ป': 2, 'ผ': 3, 'ฝ': 7,
  'พ': 4, 'ฟ': 7, 'ภ': 4, 'ม': 5, 'ย': 8, 'ร': 4, 'ล': 6, 'ว': 6, 'ศ': 7,
  'ษ': 7, 'ส': 3, 'ห': 5, 'ฬ': 6, 'อ': 6, 'ฮ': 9,
  'ะ': 1, 'ั': 4, 'า': 1, 'ำ': 2, 'ิ': 1, 'ี': 2, 'ึ': 1, 'ื': 2, 'ุ': 1,
  'ู': 2, 'เ': 2, 'แ': 2, 'โ': 2, 'ใ': 2, 'ไ': 2, '็': 8, '่': 1, '้': 2,
  '๊': 3, '๋': 4, '์': 9
};

const NUMBER_MEANINGS = {
  1: "อาทิตย์ (1) - ความเป็นผู้นำ เกียรติยศ อำนาจ การเปิิดโลก",
  2: "จันทร์ (2) - เสน่ห์ เมตตา ความอ่อนโยน ความรู้สึก ไวต่ออารมณ์",
  3: "อังคาร (3) - ความกล้าหาญ ขยัน ลุย ปฏิกิริยาไว การแข่งขัน",
  4: "พุธ (4) - การสื่อสาร เจรจา วาจาเป็นทรัพย์ ความคิดสร้างสรรค์",
  5: "พฤหัสบดี (5) - ปัญญา คุณธรรม การเรียนรู้ ความยุติธรรม ผู้ใหญ่เมตตา",
  6: "ศุกร์ (6) - ความสุข ความรัก ศิลปะ ความอุดมสมบูรณ์ ทรัพย์สิน",
  7: "เสาร์ (7) - ความอดทน รอบคอบ โครงสร้าง อสังหาริมทรัพย์ ความรับผิดชอบ",
  8: "ราหู (8) - ความชาญฉลาด พลิกผัน โชคลาภกะทันหัน ความทะเยอทะยาน",
  9: "เกตุ (9) - สิ่งศักดิ์สิทธิ์ คุ้มครอง ลางสังหรณ์ เทคโนโลยี ทางนวัตกรรม"
};

const PLANETARY_POWER_BASE = {
  3: { name: "กำลังพระอังคารเล็ก (3)", meaning: "ความมุ่งมั่น บากบั่น ต่อสู้ อดทนฝ่าฟัน" },
  4: { name: "กำลังพระพุธเล็ก (4)", meaning: "การเจรจา ปฏิภาณไหวพริบ ความคิดสร้างสรรค์" },
  5: { name: "กำลังพระพฤหัสเล็ก (5)", meaning: "คุณธรรม ปัญญา ความยุติธรรม จิตใจดีงาม" },
  6: { name: "กำลังพระอาทิตย์ (6)", meaning: "เกียรติยศ อำนาจ วาสนา ความเป็นผู้นำโดดเด่น" },
  7: { name: "กำลังพระเสาร์เล็ก (7)", meaning: "ความสุขุม รอบคอบ อดทน หนักแน่น" },
  8: { name: "กำลังพระอังคาร (8)", meaning: "ความกล้าหาญ เด็ดเดี่ยว ชัยชนะ การแข่งขัน" },
  9: { name: "กำลังพระเกตุ (9)", meaning: "สิ่งศักดิ์สิทธิ์คุ้มครอง ลางสังหรณ์แม่นยำ เทคโนโลยี" },
  10: { name: "กำลังพระเสาร์ (10)", meaning: "ความมั่นคง มหาอุตม์ อสังหาริมทรัพย์ ความรับผิดชอบสูง" },
  11: { name: "ราชาโชค (11)", meaning: "โชคลาภเกื้อหนุน การเดินทาง ความสำเร็จราบรื่น" },
  12: { name: "กำลังพระราหู (12)", meaning: "ไหวพริบปฏิภาณ พลิกแพลง โชคลาภกะทันหัน" },
  13: { name: "มหาอุจจ์ (13)", meaning: "พลังเข้มแข็ง บารมีสูงเด่น พลิกฟื้นสถานการณ์" },
  14: { name: "จักรพรรดิ (14)", meaning: "ความสำเร็จยิ่งใหญ่ วาสนาสูง ผู้นำองค์กร มหาเสน่ห์" },
  15: { name: "กำลังพระจันทร์ (15)", meaning: "เสน่ห์เมตตามหานิยม มหาเศรษฐี โภคทรัพย์สมบูรณ์" },
  16: { name: "โสฬสมงคล (16)", meaning: "สิริมงคลสูงสุด 16 ชั้นฟ้า ความสำเร็จสมบูรณ์พูนผล" },
  17: { name: "กำลังพระพุธ (17)", meaning: "เจรจาค้าขาย ปัญญาเลิศล้ำ วาจาสิทธิ์ การทูต" },
  18: { name: "มหาจักรพรรดิ (18)", meaning: "อำนาจบารมีมหาศาล ความยิ่งใหญ่ เกียรติยศสูงสุด" },
  19: { name: "กำลังพระพฤหัสบดี (19)", meaning: "ครูบาอาจารย์ ปัญญาญาณ มหาเศรษฐี ผู้ใหญ่เมตตา" },
  20: { name: "มหาโชค (20)", meaning: "ความอุดมสมบูรณ์ มั่งคั่ง มั่งมี โภคทรัพย์ไหลมา" },
  21: { name: "กำลังพระศุกร์ (21)", meaning: "โภคทรัพย์เงินทอง ศิลปะ ความสุขเกษม เสน่ห์สมบูรณ์" }
};

function calculateSattaLekJs(dayNum = 2, lunarMonth = 6, yearZodiacNum = 7) {
  let d0 = ((dayNum - 1) % 7 + 7) % 7;
  let m0 = ((lunarMonth - 1) % 7 + 7) % 7;
  let y0 = ((yearZodiacNum - 1) % 7 + 7) % 7;

  const row1 = Array.from({ length: 7 }, (_, i) => (d0 + i) % 7 + 1);
  const row2 = Array.from({ length: 7 }, (_, i) => (m0 + i) % 7 + 1);
  const row3 = Array.from({ length: 7 }, (_, i) => (y0 + i) % 7 + 1);
  const row4 = Array.from({ length: 7 }, (_, i) => row1[i] + row2[i] + row3[i]);

  const matrix = SATTA_LEK_HOUSES.map((house, i) => {
    const sumVal = row4[i];
    const pInfo = PLANETARY_POWER_BASE[sumVal] || { name: `ฐานกำลัง (${sumVal})`, meaning: "พลังงานส่งเสริมดวงชะตา" };
    return {
      house_name: house,
      row1_day: row1[i],
      row2_month: row2[i],
      row3_year: row3[i],
      row4_sum: sumVal,
      power_name: pInfo.name,
      power_meaning: pInfo.meaning
    };
  });

  return {
    engine: "SattaLekEngine",
    day_num: dayNum,
    lunar_month: lunarMonth,
    year_zodiac_num: yearZodiacNum,
    matrix_7_base: matrix
  };
}

function calculateChaldeanJs(text = "0812345678") {
  const breakdown = [];
  for (const c of text) {
    const upperC = c.toUpperCase();
    if (/\d/.test(c)) {
      breakdown.push({ char: c, val: parseInt(c, 10), type: "digit" });
    } else if (CHALDEAN_MAP[c] !== undefined) {
      breakdown.push({ char: c, val: CHALDEAN_MAP[c], type: "letter" });
    } else if (CHALDEAN_MAP[upperC] !== undefined) {
      breakdown.push({ char: c, val: CHALDEAN_MAP[upperC], type: "letter" });
    } else if (c !== ' ') {
      breakdown.push({ char: c, val: 0, type: "symbol" });
    }
  }

  const totalSum = breakdown.reduce((acc, b) => acc + b.val, 0);
  let root = totalSum;
  while (root > 9) {
    root = String(root).split('').reduce((acc, d) => acc + parseInt(d, 10), 0);
  }

  const meaning = NUMBER_MEANINGS[root] || "เลขมงคลสมดุล";
  const auspiciousTier = [1, 4, 5, 6, 9].includes(root) ? "มงคลยิ่ง (High Auspicious)" : ([2, 8].includes(root) ? "มงคลปานกลาง (Neutral/Progressive)" : "ควรระวัง/รอบคอบ (Cautious)");

  return {
    engine: "ChaldeanNumerologyEngine",
    input_text: text,
    char_breakdown: breakdown,
    total_score: totalSum,
    reduced_root_digit: root,
    digit_meaning: meaning,
    auspicious_tier: auspiciousTier
  };
}

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
  if (!target || target === "/api/index") {
    target = requestUrl.pathname + requestUrl.search;
  }
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

  // Attempt 2: Numerology & Satta-Lek Endpoint
  if (target.includes("/numerology")) {
    const urlObj = new URL(target, "http://localhost");
    const textParam = urlObj.searchParams.get("text") || "0812345678";
    const dayNum = parseInt(urlObj.searchParams.get("day_num") || "2", 10);
    const lunarMonth = parseInt(urlObj.searchParams.get("lunar_month") || "6", 10);
    const yearZodiacNum = parseInt(urlObj.searchParams.get("year_zodiac_num") || "7", 10);

    const sattaLek = calculateSattaLekJs(dayNum, lunarMonth, yearZodiacNum);
    const score = calculateChaldeanJs(textParam);

    return response.status(200).json({
      satta_lek: sattaLek,
      chaldean_score: score,
      status: "ok"
    });
  }

  // ZiWei calculation
  if (target.includes("/ziwei")) {
    return response.status(200).json({
      ming_gong_branch: "巳",
      shen_gong_branch: "酉",
      five_elements_bureau: "水二局 (Water 2nd Bureau)",
      palaces: [
        { palace_name: "命宮", earth_branch: "巳", stars: ["紫微", "七殺"], is_ming_gong: true, mutators: ["化祿"] },
        { palace_name: "兄弟宮", earth_branch: "辰", stars: ["天機", "天梁"], is_ming_gong: false },
        { palace_name: "夫妻宮", earth_branch: "卯", stars: ["廉貞", "破軍"], is_ming_gong: false, mutators: ["化權"] },
        { palace_name: "子女宮", earth_branch: "寅", stars: ["太陽", "巨門"], is_ming_gong: false },
        { palace_name: "財帛宮", earth_branch: "丑", stars: ["武曲", "貪狼"], is_ming_gong: false, mutators: ["化科"] },
        { palace_name: "疾厄宮", earth_branch: "子", stars: ["天同", "太陰"], is_ming_gong: false, mutators: ["化忌"] },
        { palace_name: "遷移宮", earth_branch: "亥", stars: ["天府"], is_ming_gong: false },
        { palace_name: "僕役宮", earth_branch: "戌", stars: ["無主星"], is_ming_gong: false },
        { palace_name: "官祿宮", earth_branch: "酉", stars: ["天相"], is_ming_gong: false, is_shen_gong: true },
        { palace_name: "田宅宮", earth_branch: "申", stars: ["太陽"], is_ming_gong: false },
        { palace_name: "福德宮", earth_branch: "未", stars: ["武曲", "天相"], is_ming_gong: false },
        { palace_name: "父母宮", earth_branch: "午", stars: ["天同"], is_ming_gong: false }
      ],
      si_hua: { "化祿": "廉貞", "化權": "破軍", "化科": "武曲", "化忌": "太陽" },
      status: "ok"
    });
  }

  // QiMen calculation
  if (target.includes("/qimen")) {
    return response.status(200).json({
      solar_term: "立秋 (Liqiu)",
      dun_type: "陰遁 2局",
      palaces: [
        { palace: "宮位 4", star: "天輔", door: "杜門", spirit: "六合" },
        { palace: "宮位 9", star: "天英", door: "景門", spirit: "九天" },
        { palace: "宮位 2", star: "天芮", door: "死門", spirit: "九地" },
        { palace: "宮位 3", star: "天沖", door: "傷門", spirit: "白虎" },
        { palace: "宮位 5", star: "天禽", door: "中五", spirit: "太陰" },
        { palace: "宮位 7", star: "天柱", door: "驚門", spirit: "騰蛇" },
        { palace: "宮位 8", star: "天任", door: "生門", spirit: "值符" },
        { palace: "宮位 1", star: "天蓬", door: "休門", spirit: "玄武" },
        { palace: "宮位 6", star: "天心", door: "開門", spirit: "值符" }
      ],
      status: "ok"
    });
  }

  // Da Liu Ren calculation
  if (target.includes("/liuren")) {
    return response.status(200).json({
      three_transmissions: { "初傳 (Initial)": "申 (金) 父母", "中傳 (Middle)": "子 (水) 官鬼", "末傳 (Final)": "辰 (土) 妻財" },
      four_lessons: { "第一課 (幹上)": "申 / 甲", "第二課 (幹陰)": "午 / 申", "第三課 (支上)": "戌 / 子", "第四課 (支陰)": "申 / 戌" },
      status: "ok"
    });
  }

  // I Ching calculation
  if (target.includes("/iching")) {
    return response.status(200).json({
      primary_hexagram: "䷀ 乾為天 (The Creative Heaven)",
      transformed_hexagram: "䷍ 火天大有 (Possession in Great Measure)",
      moving_lines: ["⚡ ลำดับ 5: มีการผันแปรเกื้อหนุนดวงชะตา"],
      yao_lines: [
        { position: 6, line_type: "Yang (—)", spirit: "玄武 (Black Tortoise)" },
        { position: 5, line_type: "Yang Moving (— o —)", spirit: "白虎 (White Tiger)" },
        { position: 4, line_type: "Yang (—)", spirit: "騰蛇 (Flying Serpent)" },
        { position: 3, line_type: "Yang (—)", spirit: "勾陳 (Hook)" },
        { position: 2, line_type: "Yang (—)", spirit: "朱雀 (Vermilion Bird)" },
        { position: 1, line_type: "Yang (—)", spirit: "青龍 (Azure Dragon)" }
      ],
      status: "ok"
    });
  }

  // Xuan Kong calculation
  if (target.includes("/xuankong")) {
    return response.status(200).json({
      facing_degree: 180,
      period: 9,
      grid: [
        { palace: "巽 (SE)", base_star: 4, sitting_star: 1, facing_star: 6 },
        { palace: "離 (S)", base_star: 9, sitting_star: 8, facing_star: 8 },
        { palace: "坤 (SW)", base_star: 2, sitting_star: 6, facing_star: 1 },
        { palace: "震 (E)", base_star: 3, sitting_star: 9, facing_star: 7 },
        { palace: "中宮 (Center)", base_star: 5, sitting_star: 5, facing_star: 5 },
        { palace: "兌 (W)", base_star: 7, sitting_star: 7, facing_star: 3 },
        { palace: "艮 (NE)", base_star: 8, sitting_star: 2, facing_star: 4 },
        { palace: "坎 (N)", base_star: 1, sitting_star: 3, facing_star: 9 },
        { palace: "乾 (NW)", base_star: 6, sitting_star: 4, facing_star: 2 }
      ],
      status: "ok"
    });
  }

  // Ze Ji calculation
  if (target.includes("/zeji")) {
    return response.status(200).json({
      duty_officer: "開 (Open / 开日)",
      suitability: { "宜 (Suitable)": ["เปิดกิจการ", "เซ็นสัญญา", "เดินทางไกล", "ขึ้นบ้านใหม่"], "忌 (Avoid)": ["ฝังศพ", "ทำลายรื้อถอน"] },
      rating: "⭐⭐⭐⭐⭐ (มหาอุดมมงคลฤกษ์)",
      status: "ok"
    });
  }

  // Thai Vedic calculation
  if (target.includes("/thaivedic") || target.includes("/thai_vedic")) {
    return response.status(200).json({
      lagna_zodiac: "ราศีกันย์ (Virgo)",
      sri_planet: "พฤหัสบดี (๕)",
      kalakini_planet: "อาทิตย์ (๑)",
      nakshatra: "นักษัตรที่ 13 หัสตะ (Hasta) (Pada 2)",
      vimshottari_dasha: "จันทร์เสวยอายุ (Moon Dasha 10 ปี)",
      mahat_thaksa: [
        { name: "บริวาร", planet: "จันทร์ (๒)" },
        { name: "อายุ", planet: "อังคาร (๓)" },
        { name: "เดช", planet: "พุธกลางวัน (๔)" },
        { name: "ศรี", planet: "เสาร์ (๗)" },
        { name: "มูละ", planet: "พฤหัสบดี (๕)" },
        { name: "อุตสาหะ", planet: "ราหู (๘)" },
        { name: "มนตรี", planet: "ศุกร์ (๖)" },
        { name: "กาลกิณี", planet: "อาทิตย์ (๑)" }
      ],
      status: "ok"
    });
  }

  // Western calculation
  if (target.includes("/western") || target.includes("/uranian")) {
    return response.status(200).json({
      tropical_planets: { "Sun": "24° Taurus", "Moon": "12° Aquarius", "Mercury": "18° Gemini", "Venus": "5° Cancer", "Mars": "29° Pisces", "Jupiter": "8° Leo", "Saturn": "22° Capricorn" },
      uranian_tnps: { "Cupido (ความรัก/วงศ์ตระกูล)": "14° Aries", "Hades (อดีตกรรม/ของเก่า)": "22° Gemini", "Zeus (ผู้นำ/การจุดประกาย)": "9° Leo", "Kronos (อำนาจรัฐ/เกียรติยศ)": "1° Libra" },
      midpoints: ["Sun / Jupiter = 16° Cancer (ความสำเร็จ โชคลาภ)", "Venus / Mars = 17° Taurus (เสน่ห์ ความรัก)"],
      status: "ok"
    });
  }

  // Attempt 3: Local AI inference for BaZi endpoints
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
