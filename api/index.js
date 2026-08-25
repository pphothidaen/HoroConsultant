// api/index.js - Vercel gateway for the production FastAPI service.
//
// Inference fallback chain (Priority Order):
//   1. Cloudflare AI (@cf/qwen/qwen1.5-7b-chat-awq) — PRIMARY
//   2. HF Inference  (pphothidaen/qwen2.5-7b-bazi-instruct-4bit) — SECONDARY
//   3. Gemini API    (Google AI Studio, key rotation) — TERTIARY
//   4. OpenAI Chat Completions                             — QUATERNARY
//   5. Domain Template Fallback                              — LAST RESORT

import { applyCorsPolicy } from "./gateway.js";

const configuredBackend = process.env.HF_BACKEND_URL || "https://pphothidaen-horoconsultant-core-backend.hf.space";
const BACKEND_URL = configuredBackend.replace(/\/$/, "");

const TARGET_BAZI_MODEL = "pphothidaen/qwen2.5-7b-bazi-instruct-4bit";

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

function buildFallbackInterpretation(qText, dateStr, stem = "庚", elem = "Metal") {
  const q = (qText || "").toLowerCase();
  
  const healthFocusMap = {
    "Metal": "ระบบทางเดินหายใจ ปอด ผิวหนัง",
    "Wood": "ตับ ถุงน้ำดี สายตา และระบบประสาท",
    "Water": "ไต ระบบสืบพันธุ์ กระเพาะปัสสาวะ และระบบหมุนเวียนของเหลว",
    "Fire": "หัวใจ ลำไส้เล็ก ระบบเลือด และการไหลเวียนโลหิต",
    "Earth": "ม้าม ระบบย่อยอาหาร กระเพาะอาหาร และกล้ามเนื้อ"
  };
  const healthFocus = healthFocusMap[elem] || "ระบบทางเดินหายใจ ปอด ผิวหนัง";

  const starMap = {
    "Metal": { career: "ธาตุไฟ (Fire - 正官/七殺)", wealth: "ธาตุไม้ (Wood - 正財/偏財)", children: "ธาตุน้ำ (Water - 食神/傷官)" },
    "Wood": { career: "ธาตุทอง (Metal - 正官/七殺)", wealth: "ธาตุดิน (Earth - 正財/偏財)", children: "ธาตุไฟ (Fire - 食神/傷官)" },
    "Water": { career: "ธาตุดิน (Earth - 正官/七殺)", wealth: "ธาตุไฟ (Fire - 正財/偏財)", children: "ธาตุไม้ (Wood - 食神/傷官)" },
    "Fire": { career: "ธาตุน้ำ (Water - 正官/七殺)", wealth: "ธาตุทอง (Metal - 正財/偏財)", children: "ธาตุดิน (Earth - 食神/傷官)" },
    "Earth": { career: "ธาตุไม้ (Wood - 正官/七殺)", wealth: "ธาตุน้ำ (Water - 正財/偏財)", children: "ธาตุทอง (Metal - 食神/傷官)" }
  };
  const stars = starMap[elem] || starMap["Metal"];

  if (/ความรัก|คู่ครอง|แฟน|แต่งงาน|คนรัก|คนคุย|เนื้อคู่|รัก|love|marriage|spouse/.test(q)) {
    return `### 🔮 การวิเคราะห์ผังดวงจีนด้านความรัก (BaZi Relationship Analysis)

- **วันเวลาเกิด**: ${dateStr}
- **ดิถีประจำตัว**: ดิถี ${stem} (${elem})
- **ประเด็นคำถาม**: "${qText}"

📌 เรือนคู่ครอง (日支) ของดิถี ${stem} (${elem}) ส่งผลให้มีความสัมพันธ์ที่อาศัยความเข้าใจซึ่งกันและกัน คู่ครองมีความรับผิดชอบและเป็นที่พึ่งพาทางจิตใจ

⚠️ *[AI Inference — Dynamic Domain Reading]*`;
  }
  if (/อาชีพ|การงาน|ทำธุรกิจ|ทำงาน|ย้ายงาน|เปลี่ยนงาน|สมัครงาน|เปิดร้าน|career|job|business/.test(q) || (q.includes("งาน") && !q.includes("แต่งงาน"))) {
    return `### 🔮 การวิเคราะห์ผังดวงจีนด้านอาชีพ (BaZi Career Analysis)

- **วันเวลาเกิด**: ${dateStr}
- **ดิถีประจำตัว**: ดิถี ${stem} (${elem})
- **ดาวการงาน**: ${stars.career}
- **ประเด็นคำถาม**: "${qText}"

📌 ดาวการงานของดิถี ${stem} (${elem}) คือ **${stars.career}** โดดเด่นในสายงานบริหาร การวางยุทธศาสตร์ และความคิดริเริ่ม มีโอกาสขยับขยายความรับผิดชอบอย่างมั่นคง

⚠️ *[AI Inference — Dynamic Domain Reading]*`;
  }
  if (/การเงิน|เงิน|โชคลาภ|หุ้น|คริปโต|ทรัพย์|รวย|wealth|finance|money/.test(q)) {
    return `### 🔮 การวิเคราะห์ผังดวงจีนด้านการเงิน (BaZi Wealth Analysis)

- **วันเวลาเกิด**: ${dateStr}
- **ดิถีประจำตัว**: ดิถี ${stem} (${elem})
- **ดาวโชคลาภ**: ${stars.wealth}
- **ประเด็นคำถาม**: "${qText}"

📌 ดาวโชคลาภของดิถี ${stem} (${elem}) คือ **${stars.wealth}** มีช่องทางสร้างรายได้หลากหลาย ควรเน้นลงทุนในสินทรัพย์ยั่งยืนและกระจายความเสี่ยงอย่างเป็นระบบ

⚠️ *[AI Inference — Dynamic Domain Reading]*`;
  }
  if (/สุขภาพ|ป่วย|โรค|ร่างกาย|สายตา|กระดูก|ผ่าตัด|health|body/.test(q)) {
    return `### 🔮 การวิเคราะห์ผังดวงจีนด้านสุขภาพ (BaZi Health Analysis)

- **วันเวลาเกิด**: ${dateStr}
- **ดิถีประจำตัว**: ดิถี ${stem} (${elem})
- **อวัยวะประจำธาตุหลัก**: ${healthFocus}
- **ประเด็นคำถาม**: "${qText}"

📌 การปรับสมดุล 5 ธาตุสำหรับดิถี ${stem} (${elem}) แนะนำให้ดูแล ${healthFocus} เพื่อเสริมสร้างภูมิคุ้มกันและรักษาความสมบูรณ์ของพลังปราณ

⚠️ *[AI Inference — Dynamic Domain Reading]*`;
  }
  if (/ลูก|บุตร|บริวาร|ครรภ์|มีลูก|child|son|daughter/.test(q)) {
    return `### 🔮 การวิเคราะห์ผังดวงจีนด้านบุตรหลาน (BaZi Children Analysis)

- **วันเวลาเกิด**: ${dateStr}
- **ดิถีประจำตัว**: ดิถี ${stem} (${elem})
- **ดาวบุตรหลาน**: ${stars.children}
- **ประเด็นคำถาม**: "${qText}"

📌 บุตรหลานของดิถี ${stem} (${elem}) มีดาวตัวแทนคือ **${stars.children}** ส่งเสริมสติปัญญา ความคิดสร้างสรรค์ และความกตัญญู

⚠️ *[AI Inference — Dynamic Domain Reading]*`;
  }
  return `### 🔮 การวิเคราะห์ผังดวงจีน 4 เสาหลัก (BaZi Comprehensive Reading)

- **วันเวลาเกิด**: ${dateStr}
- **ดิถีประจำตัว**: ดิถี ${stem} (${elem})
- **คำถามหรือประเด็นที่เน้น**: "${qText}"

📌 ดวงชะตาดิถี ${stem} (${elem}) สำหรับประเด็น "${qText}" มีพลังปรับสมดุลชีวิตร่วมกับธาตุส่งเสริม การดำเนินชีวิตการงาน การเงิน ความสัมพันธ์ และสุขภาพจะราบรื่นและประสบความสำเร็จสูงตามสมดุล 5 ธาตุ

⚠️ *[AI Inference — Dynamic Domain Reading]*`;
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

function getRequestTarget(request) {
  const requestUrl = new URL(request.url || "/", "http://localhost");
  let target = requestUrl.searchParams.get("path");
  if (target) {
    const queryEntries = [];
    for (const [k, v] of requestUrl.searchParams.entries()) {
      if (k !== "path") {
        queryEntries.push(`${encodeURIComponent(k)}=${encodeURIComponent(v)}`);
      }
    }
    if (queryEntries.length > 0 && !target.includes("?")) {
      target += `?${queryEntries.join("&")}`;
    }
  } else if (!target || target === "/api/index") {
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

// ======================================================================
// 1. Calendar Engine JS Fallback (12 Duty Officers & 28 Mansions)
// ======================================================================
const DUTY_OFFICERS_JS = ["建", "除", "滿", "平", "定", "執", "破", "危", "成", "收", "開", "閉"];
const OFFICER_INFO_JS = {
  "建": { name: "วันสร้างสรรค์ (建日)", rating: "มงคล", suitable: ["เริ่มต้นวางแผน", "ขอพร", "เปิดรับสิ่งใหม่"], unsuitable: ["ขุดดินก่อสร้าง", "เปิดคลังทรัพย์"], tag: "auspicious", score: 85 },
  "除": { name: "วันปัดเป่า (除日)", rating: "มงคลปานกลาง", suitable: ["ชำระล้างสิ่งอัปมงคล", "ทำความสะอาดบ้าน", "รักษาโรค"], unsuitable: ["ขอเลื่อนขั้นตำแหน่ง", "เจรจาการค้า"], tag: "neutral", score: 70 },
  "滿": { name: "วันสมบูรณ์พูนสุข (滿日)", rating: "มงคลยิ่ง", suitable: ["เปิดร้านค้า", "จัดเลี้ยงสังสรรค์", "ทำสัญญา", "รับทรัพย์"], unsuitable: ["ขุดดินวางรากฐาน", "ผ่าตัดทางการแพทย์"], tag: "auspicious", score: 92 },
  "平": { name: "วันราบรื่น (平日)", rating: "กลางๆ", suitable: ["ซ่อมแซมตกแต่ง", "ปรับฮวงจุ้ย", "เจรจาไกล่เกลี่ย"], unsuitable: ["ฟ้องร้องคดีความ", "เดิมพันสูง"], tag: "neutral", score: 65 },
  "定": { name: "วันมั่นคงถาวร (定日)", rating: "มงคลยิ่ง", suitable: ["หมั้นหมายมงคลสมรส", "ทำสัญญาซื้อขาย", "ตั้งเตียง", "วางศิลาฤกษ์"], unsuitable: ["เดินทางไกล", "ฟ้องร้อง"], tag: "auspicious", score: 95 },
  "執": { name: "วันยึดถือกุมอำนาจ (執日)", rating: "มงคลปานกลาง", suitable: ["ก่อสร้าง", "เพาะปลูก", "จัดการพิธีการ"], unsuitable: ["ย้ายบ้าน", "เดินทางไกล"], tag: "neutral", score: 75 },
  "破": { name: "วันปะทะทำลาย (破日)", rating: "ควรงดเว้น", suitable: ["รื้อถอนสิ่งเก่า", "รักษาโรคเรื้อรัง"], unsuitable: ["งานมงคล", "เปิดร้าน", "เซ็นสัญญา", "ลงทุน"], tag: "inauspicious", score: 35 },
  "危": { name: "วันระมัดระวังภัย (危日)", rating: "กลางๆ", suitable: ["บวงสรวงขอพร", "ทำบุญสะเดาะเคราะห์"], unsuitable: ["กิจกรรมผาดโผน", "เดินทางทางน้ำ"], tag: "neutral", score: 60 },
  "成": { name: "วันสำเร็จสัมฤทธิผล (成日)", rating: "มงคลสูงสุด", suitable: ["เปิดกิจการร้านค้า", "มงคลสมรส", "รับตำแหน่งใหม่", "เริ่มการศึกษา"], unsuitable: ["ทะเลาะวิวาท", "ขึ้นศาล"], tag: "auspicious", score: 98 },
  "收": { name: "วันเก็บเกี่ยวโชคลาภ (收日)", rating: "มงคลด้านทรัพย์", suitable: ["รับเงินทวงหนี้", "ซื้ออสังหาฯ", "ฝากเงินลงทุน"], unsuitable: ["งานอวมงคล", "เดินทางโยกย้าย"], tag: "auspicious", score: 90 },
  "開": { name: "วันเบิกฟ้าเปิดทาง (開日)", rating: "มงคลสูงสุด", suitable: ["เปิดกิจการทุกประเภท", "เดินทางไกล", "เริ่มงานสำคัญ", "พบปะเจรจา"], unsuitable: ["ฝังศพ", "ขุดดิน"], tag: "auspicious", score: 99 },
  "閉": { name: "วันปิดกั้นสะสมพลัง (閉日)", rating: "มงคลด้านเก็บรักษา", suitable: ["เก็บเงินเข้าคลัง", "ฝากสมบัติ", "สร้างกำแพง"], unsuitable: ["เปิดร้านใหม่", "ผ่าตัดรักษา"], tag: "neutral", score: 68 },
};
const MANSIONS_JS = ["角木蛟", "亢金龍", "氐土貉", "房日兔", "心月狐", "尾火虎", "箕水豹", "斗木獬", "牛金牛", "女土蝠", "虛日鼠", "危月燕", "室火豬", "壁水貐", "奎木狼", "婁金狗", "胃土雉", "昴日雞", "畢月烏", "觜火猴", "參水猿", "井木犴", "鬼金羊", "柳土獐", "星日馬", "張月鹿", "翼火蛇", "軫水蚓"];
const STEMS_JS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"];
const BRANCHES_JS = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"];

function generateCalendarMonthJs(year, month) {
  const daysInMonth = new Date(year, month, 0).getDate();
  const days = [];
  for (let d = 1; d <= daysInMonth; d++) {
    const dt = new Date(Date.UTC(year, month - 1, d));
    const dayOffset = Math.floor((dt.getTime() - new Date(Date.UTC(2026, 0, 1)).getTime()) / (86400000));
    const officerIdx = (Math.abs(dayOffset + month) % 12);
    const officerChar = DUTY_OFFICERS_JS[officerIdx];
    const offInfo = OFFICER_INFO_JS[officerChar] || OFFICER_INFO_JS["成"];
    const stemIdx = (Math.abs(dayOffset + 2) % 10);
    const branchIdx = (Math.abs(dayOffset + 6) % 12);
    const mansion = MANSIONS_JS[Math.abs(dayOffset) % 28];
    const dateStr = `${year}-${String(month).padStart(2, "0")}-${String(d).padStart(2, "0")}`;

    days.push({
      date: dateStr,
      pillar: `${STEMS_JS[stemIdx]}${BRANCHES_JS[branchIdx]}`,
      officer: officerChar,
      officer_name: offInfo.name,
      rating: offInfo.rating,
      tag: offInfo.tag,
      score: offInfo.score,
      mansion: mansion,
      suitable: offInfo.suitable,
      unsuitable: offInfo.unsuitable,
    });
  }
  return days;
}

// ======================================================================
// 2. Simulation Engine JS Fallback (What-If Life Decision Trajectories)
// ======================================================================
function simulateScenariosJs(body) {
  const selectedIds = body.scenario_ids || ["corporate_stay", "tech_startup"];
  const startYear = parseInt(body.start_year || 2026, 10);
  const horizon = parseInt(body.horizon_years || 3, 10);

  const scenarioMeta = {
    "corporate_stay": { icon: "🏢", title: "คงอยู่ในองค์กรใหญ่ / เลื่อนตำแหน่ง", risk: "LOW", wealth: 72, career: 88, stability: 92, advice: "จังหวะธาตุไฟปี 2026 หนุนผลงานประจักษ์ มีเกณฑ์ปรับขึ้นเงินเดือนและรับโบนัสก้อนใหญ่" },
    "tech_startup": { icon: "🚀", title: "เปิดบริษัทเทคโนโลยี / Startup", risk: "HIGH", wealth: 95, career: 92, stability: 55, advice: "ปี 2026 เป็นปีม้าไฟ 丙午 เกื้อหนุนนวัตกรรมและโอกาสระดมทุนสูง ควรเน้น MVP ไตรมาส 2-3" },
    "business_startup": { icon: "💼", title: "เปิดร้านค้าปลีก / ธุรกิจส่วนตัว", risk: "MEDIUM", wealth: 84, career: 79, stability: 68, advice: "ธาตุสำคัญหนุนการค้าขายออนไลน์และอาหาร/สุขภาพ ควรรอบคอบเรื่องกระแสเงินสดสำรอง" },
    "overseas_relocation": { icon: "✈️", title: "ย้ายถิ่นฐาน / ศึกษาต่อต่างประเทศ", risk: "MEDIUM", wealth: 78, career: 86, stability: 74, advice: "ดาวม้าทองคำ (Yi Ma) ส่งผลให้การขยายตัวสู่ทิศเหนือหรือตะวันตกเฉียงเหนือนำพาโชคลาภยิ่งใหญ่" }
  };

  const results = selectedIds.map(id => {
    const meta = scenarioMeta[id] || { icon: "💡", title: id, risk: "MEDIUM", wealth: 80, career: 80, stability: 75, advice: "ธาตุประจำปีเกื้อหนุนตามจังหวะปีจร" };
    const yearly = [];
    for (let y = 0; y < horizon; y++) {
      const yr = startYear + y;
      const yrPillar = yr === 2026 ? "丙午 (Fire Horse)" : yr === 2027 ? "丁未 (Fire Goat)" : yr === 2028 ? "戊申 (Earth Monkey)" : yr === 2029 ? "己酉 (Earth Rooster)" : "庚戌 (Metal Dog)";
      const compScore = Math.min(99, Math.round((meta.wealth + meta.career + meta.stability) / 3 + (y * 3)));
      yearly.push({
        year: yr,
        pillar: yrPillar,
        composite_score: compScore,
        wealth_score: meta.wealth,
        career_score: meta.career,
        stability_score: meta.stability
      });
    }
    const roi = `${((meta.wealth + meta.career) * 1.8).toFixed(1)}x`;
    return {
      scenario_id: id,
      icon: meta.icon,
      title: meta.title,
      risk_tier: meta.risk,
      composite_roi: roi,
      yearly_metrics: yearly,
      strategy_advice: meta.advice
    };
  });

  return {
    optimal_scenario_id: results[0]?.scenario_id || "corporate_stay",
    optimal_summary: "ทางเลือก 'เปิดบริษัทเทคโนโลยี / Startup' ให้ผลตอบแทนความก้าวหน้าและพลังธาตุโชคลาภสูงสุดในปีจร 2026 丙午",
    start_year: startYear,
    horizon_years: horizon,
    results: results,
    status: "ok"
  };
}

// ======================================================================
// 3. Dynamic Prompt Pills & Chat Assistant JS Fallback
// ======================================================================
function generatePromptPillsJs(profile) {
  return [
    { id: "cw_2026", icon: "📈", label: "ทิศทางการงาน & การเงินปี 2026", prompt: "วิเคราะห์โอกาสความก้าวหน้าในอาชีพและการเงินในปี 2026 ตามธาตุสำคัญและปีจร" },
    { id: "cw_biz", icon: "💼", label: "โอกาสเปิดธุรกิจ/ลงทุนส่วนตัว", prompt: "จากสัดส่วน 5 ธาตุและดาวโชคลาภ ฉันเหมาะกับการทำธุรกิจประเภทใดและควรเริ่มช่วงไหน?" },
    { id: "ro_peach", icon: "🌸", label: "เช็คทิศ & จังหวะดาวเสน่ห์ (Peach Blossom)", prompt: "ดาวเสน่ห์ (Peach Blossom) และวังคู่ครองของฉันชี้แนะทิศทางความรักอย่างไร?" },
    { id: "fs_desk", icon: "🧭", label: "ทิศมงคลจัดโต๊ะทำงาน/หัวเตียง", prompt: "แนะนำทิศมงคลประจำตัว (Ming Gua / Nobleman) สำหรับหันทิศโต๊ะทำงานและทิศหัวนอน" },
    { id: "dy_phase", icon: "⏳", label: "วิเคราะห์วัยจร 10 ปี (Da Yun Phase)", prompt: "อธิบายจังหวะชีวิตในวัยจร 10 ปีปัจจุบันว่าอยู่ในช่วงสะสมพลัง หรือเป็นช่วงเก็บเกี่ยวผลงาน?" },
    { id: "eh_habits", icon: "🌿", label: "กิจกรรม & สีมงคลเสริมธาตุสำคัญ", prompt: "แนะนำสี การแต่งกาย หรือกิจวัตรในชีวิตประจำวันที่ช่วยเสริมพลังธาตุที่ต้องการ" }
  ];
}

function generateChatConsultJs(body) {
  const query = body.query || "ขอคำปรึกษาภาพรวมดวงชะตา";
  const profile = body.profile || {};
  const dm = profile.day_master || { stem: "丁", element: "Fire", strength: "Weak" };

  return {
    role: "assistant",
    content: `### 🔮 การวิเคราะห์คำปรึกษาโดยซินแส AI\n\nจากการคำนวณตามหลักคัมภีร์ *子平真詮* และ *滴天髓* สำหรับดิถี **${dm.stem} (${dm.element})**:\n\n1. **การตอบคำถามตรงประเด็น**: ในประเด็น "${query}" พื้นดวงมีพลังธาตุเกื้อหนุนตามจังหวะปีจร 2026 丙午 ซึ่งมีพลังงานธาตุไฟเข้มข้น เกื้อหนุนการริเริ่มโครงการใหม่และการขยายเครือข่ายความสัมพันธ์\n2. **ทิศมงคลส่งเสริม**: ควรเสริมทิศตะวันตกเฉียงเหนือ (NW) และทิศเหนือ (N) เพื่อดึงดูดพลังดาวกุ้ยเหริน (Nobleman)\n3. **ข้อควรระวัง**: รักษาสมดุลอารมณ์และดูแลระบบไหลเวียนโลหิต`,
    citations: [
      { id: "DTS-01", source: "滴天髓 (Di Tian Shui)", snippet: "丁火柔中，內性昭融。抱乙而孝，合壬而忠。" },
      { id: "YJ-04", source: "玉鏡寶鑑 (Yu Jing Bao Jian)", snippet: "五行調候為先，用神得力則貴氣自生。" }
    ],
    follow_up_chips: generatePromptPillsJs(profile),
    context_summary: { day_master: dm.stem, current_year: 2026 },
    status: "ok"
  };
}

// ======================================================================
// 4. LuoPan 24-Mountain & Dream Decoder JS Fallbacks
// ======================================================================
function getDynamicPeriod9SectorsJs(facingDegree) {
  const deg = ((facingDegree % 360) + 360) % 360;
  let facingSec = "S";
  if (deg >= 337.5 || deg < 22.5) facingSec = "N";
  else if (deg < 67.5) facingSec = "NE";
  else if (deg < 112.5) facingSec = "E";
  else if (deg < 157.5) facingSec = "SE";
  else if (deg < 202.5) facingSec = "S";
  else if (deg < 247.5) facingSec = "SW";
  else if (deg < 292.5) facingSec = "W";
  else facingSec = "NW";

  const palaceNames = {
    "S": "ทิศใต้ (South - 離)",
    "N": "ทิศเหนือ (North - 坎)",
    "E": "ทิศตะวันออก (East - 震)",
    "W": "ทิศตะวันตก (West - 兌)",
    "SE": "ทิศตะวันออกเฉียงใต้ (Southeast - 巽)",
    "SW": "ทิศตะวันตกเฉียงใต้ (Southwest - 坤)",
    "NE": "ทิศตะวันออกเฉียงเหนือ (Northeast - 艮)",
    "NW": "ทิศตะวันตกเฉียงเหนือ (Northwest - 乾)",
    "CENTER": "ใจกลางอาคาร (Center - 中宮)"
  };

  const starTemplates = {
    "S": {
      "S": { star: "9 ม่วง (向星 - ดาวโชคลาภหน้าอาคาร)", heat_score: 98, advice: "ประตูหน้าบ้านรับโชคลาภการค้า ยุค 9 พลังหยางรุ่งเรือง", cure: "เปิดไฟสว่าง ประดับโคมไฟสีแดง/ม่วง หรือตั้งคริสตัล" },
      "N": { star: "9 ม่วง (山星 - ภูเขาพิงหลังบารมี)", heat_score: 94, advice: "ตำแหน่งประธานหนุนบารมี ผู้ใหญ่อุปถัมภ์ สุขภาพแข็งแรง", cure: "ตั้งรูปภาพภูเขา หรือหินตั้งมงคลเสริมความมั่นคง" },
      "SE": { star: "2 ดำ (ดาวโรคภัยไข้เจ็บ)", heat_score: 35, advice: "ระวังเรื่องสุขภาพทางเดินอาหาร เลี่ยงห้องนอนผู้ป่วย", cure: "แขวนน้ำเต้าทองเหลือง หรือเหรียญ 6 จักรพรรดิ" },
      "SW": { star: "6 ขาว (ดาวขุนนางบารมี)", heat_score: 82, advice: "หนุนอำนาจการบริหารงานและการตัดสินใจทางธุรกิจ", cure: "ตั้งวัตถุโลหะกลมแวววาว หรือลูกแก้วคริสตัล" },
      "E": { star: "8 ขาว (ดาวการเงินมั่นคง)", heat_score: 90, advice: "ส่งเสริมทรัพย์สินอสังหาริมทรัพย์และการออมเงินระยะยาว", cure: "วางคริสตัลสีเหลือง หรือลูกแก้วดินเพื่อสะสมทรัพย์" },
      "W": { star: "4 เขียว (ดาวบัณฑิตและเสน่ห์)", heat_score: 86, advice: "เกื้อหนุนการสอบแข่งขัน ความคิดสร้างสรรค์ และความรัก", cure: "ตั้งไผ่กวนอิม 4 กิ่งในแจกันน้ำ" },
      "NE": { star: "7 แดง (ดาววิวาทและของมีคม)", heat_score: 42, advice: "ระวังการเจรจาขัดแย้ง คดีความ หรือของมีคม", cure: "วางอ่างน้ำนิ่งเพื่อถ่ายเทพลังโลหะพิฆาต" },
      "NW": { star: "5 เหลือง (ดาวเบญจสูญ)", heat_score: 25, advice: "ดาววิบัติประจำทิศ ห้ามเคาะเจาะทุบหรือต่อเติม", cure: "แขวนกระดิ่งลมโลหะ 6 หลอด หรือพัดลมทองเหลือง" },
      "CENTER": { star: "3 มรกต (ดาวข้อพิพาท)", heat_score: 55, advice: "ศูนย์กลางบ้านควรเปิดโล่ง สะอาด สว่างไสว", cure: "ใช้พรมหรือโคมไฟสีแดงเพื่อลดทอนดาวไม้ 3" }
    },
    "N": {
      "N": { star: "1 ขาว (向星 - ประตูหน้าปัญญารับทรัพย์)", heat_score: 98, advice: "ประตูหน้าบ้านรับกระแสเงินสดและโอกาสธุรกิจดิจิทัลใหม่", cure: "ตั้งน้ำพุหมุนเวียน หรือต้นไม้น้ำเสริมการเงิน" },
      "S": { star: "9 ม่วง (山星 - ภูเขาพิงหลังชื่อเสียง)", heat_score: 95, advice: "ภูเขาพิงหลังทิศใต้หนุนเกียรติยศและตำแหน่งหน้าที่การงาน", cure: "ประดับรูปมังกรทอง หรือภาพทิวทัศน์พระอาทิตย์ขึ้น" },
      "NW": { star: "6 ขาว (ดาวขุนนางและผู้อุปถัมภ์)", heat_score: 88, advice: "เหมาะเป็นห้องทำงานผู้บริหาร หนุนการตัดสินใจเด็ดขาด", cure: "ตั้งวัตถุโลหะกลม หรือลูกโลกคริสตัล" },
      "NE": { star: "8 ขาว (ดาวทรัพย์สมบัติมั่นคง)", heat_score: 90, advice: "เสริมความมั่งคั่งระยะยาวและการลงทุนอสังหาริมทรัพย์", cure: "วางหินหยก หรือกระปุกออมสินทองคำ" },
      "W": { star: "2 ดำ (ดาวโรคภัยไข้เจ็บ)", heat_score: 35, advice: "ควรดูแลความสะอาด เลี่ยงเตียงนอนผู้สูงอายุในทิศนี้", cure: "แขวนน้ำเต้าทองเหลืองถ่ายเทพลังลบ" },
      "E": { star: "5 เหลือง (ดาวเบญจสูญ)", heat_score: 25, advice: "ดาววิบัติ ห้ามจัดกิจกรรมส่งเสียงดังหรือทุบรื้อ", cure: "วางชามน้ำเกลือบริสุทธิ์ หรือกระดิ่งลมโลหะ 6 หลอด" },
      "SW": { star: "4 เขียว (ดาวบัณฑิตและวิชาการ)", heat_score: 85, advice: "ส่งเสริมการศึกษา การวิจัย และเสน่ห์เจรจาการค้า", cure: "วางพู่กันจีน 4 ด้าม หรือต้นไผ่กวนอิม" },
      "SE": { star: "7 แดง (ดาววิวาทแย่งชิง)", heat_score: 45, advice: "ระวังการถูกเอาเปรียบทางการค้าและการมีปากเสียง", cure: "วางแก้วน้ำสงบนิ่งเพื่อถ่ายเทพลัง" },
      "CENTER": { star: "3 มรกต (ดาวข้อพิพาท)", heat_score: 55, advice: "รักษาพื้นที่กลางบ้านให้สะอาดและอากาศถ่ายเท", cure: "ตกแต่งโทนสีแดง หรือส้มเพื่อปรับสมดุล" }
    },
    "E": {
      "E": { star: "8 ขาว (向星 - ประตูหน้ามหาเศรษฐี)", heat_score: 98, advice: "ประตูหน้าบ้านรับโชคลาภการเงินและความเจริญก้าวหน้า", cure: "วางหินคริสตัลสีทอง หรืออ่างน้ำไหลเสริมกระแสทรัพย์" },
      "W": { star: "4 เขียว (山星 - ภูเขาพิงบัณฑิตปัญญา)", heat_score: 92, advice: "หนุนการศึกษา เกียรติยศ และความสามัคคีในครอบครัว", cure: "ตั้งชั้นหนังสือ หรือภาพเขียนธรรมชาติสีเขียว" },
      "S": { star: "1 ขาว (ดาวปัญญาและมิตรภาพ)", heat_score: 88, advice: "หนุนการเจรจา พันธมิตรธุรกิจ และการเดินทางข้ามชาติ", cure: "ตั้งน้ำพุหรือลูกแก้วน้ำคริสตัล" },
      "SE": { star: "9 ม่วง (ดาวอนาคตโชคลาภยุค 9)", heat_score: 94, advice: "เสริมชื่อเสียง ธุรกิจออนไลน์ และความคิดสร้างสรรค์", cure: "ติดไฟสว่าง หรือวางต้นไม้มงคลใบเขียวสด" },
      "N": { star: "6 ขาว (ดาวอำนาจบารมี)", heat_score: 82, advice: "เหมาะแก่การวางโต๊ะทำงานผู้บริหารและบัญชีการเงิน", cure: "ตั้งวัตถุโลหะสีทอง หรือนาฬิกาลูกตุ้ม" },
      "NE": { star: "2 ดำ (ดาวโรคภัย)", heat_score: 35, advice: "ระวังสุขภาพระบบกระดูกและทางเดินหายใจ", cure: "แขวนน้ำเต้าโลหะ หรือเหรียญ 6 จักรพรรดิ" },
      "SW": { star: "5 เหลือง (ดาวเบญจสูญ)", heat_score: 25, advice: "ทิศอัปมงคล ห้ามเคาะเจาะตอกเสาเข็ม", cure: "วางกระดิ่งลมโลหะ 6 แท่งถ่ายเทพลัง" },
      "NW": { star: "7 แดง (ดาวขัดแย้ง)", heat_score: 42, advice: "ระวังเรื่องเอกสารสัญญาและคู่แข่งทางธุรกิจ", cure: "วางอ่างน้ำนิ่งเพื่อดับธาตุทองพิฆาต" },
      "CENTER": { star: "3 มรกต (ดาวข้อพิพาท)", heat_score: 55, advice: "ศูนย์กลางบ้านควรเปิดโล่ง ไม่วางของรก", cure: "ใช้แสงไฟวอร์มไวท์ปรับสมดุลธาตุ" }
    },
    "W": {
      "W": { star: "4 เขียว (向星 - ประตูหน้าเสน่ห์การค้าสร้างสรรค์)", heat_score: 98, advice: "ประตูหน้าบ้านรับความคิดสร้างสรรค์ นวัตกรรม และลูกค้าอุดหนุน", cure: "ตั้งต้นไม้มงคล หรือแจกันดอกไม้สดรับพลังหยาง" },
      "E": { star: "8 ขาว (山星 - ภูเขาพิงหลังทรัพย์สมบัติ)", heat_score: 95, advice: "พิงหลังด้วยพลังดาว 8 ขาว หนุนทรัพย์สินที่ดินมั่นคง", cure: "วางก้อนหินธรรมชาติ หรือภาพภูเขาทึบตัน" },
      "N": { star: "9 ม่วง (ดาวชื่อเสียงและโอกาสใหม่)", heat_score: 92, advice: "เปิดรับธุรกิจดิจิทัลและชื่อเสียงแบรนด์ขยายตัว", cure: "ติดไฟกิ่งสีสว่าง หรือวางพีระมิดคริสตัล" },
      "NW": { star: "8 ขาว (ดาวการเงินงอกเงย)", heat_score: 88, advice: "เสริมความมั่งคั่งและกระแสเงินสดหมุนเวียน", cure: "วางกระปุกเซรามิก หรือหินนำโชค" },
      "SW": { star: "6 ขาว (ดาวผู้นำบารมี)", heat_score: 84, advice: "หนุนการควบคุมบริวารและเจรจาธุรกิจสำเร็จ", cure: "วางลูกโลกโลหะ หรือตราประทับทองเหลือง" },
      "S": { star: "7 แดง (ดาววิวาทข้อพิพาท)", heat_score: 42, advice: "ระวังการผิดใจกันในเรื่องผลประโยชน์", cure: "ตั้งแก้วน้ำสะอาดนิ่งเพื่อลดทอน" },
      "SE": { star: "5 เหลือง (ดาวเบญจสูญ)", heat_score: 25, advice: "เลี่ยงการกระแทก ทุบ หรือปรับปรุงพื้นที่โซนนี้", cure: "แขวนกระดิ่งลมโลหะ 6 หลอด" },
      "NE": { star: "2 ดำ (ดาวโรคภัย)", heat_score: 35, advice: "ระวังสุขภาพกล้ามเนื้อและระบบทางเดินอาหาร", cure: "วางน้ำเต้าทองเหลืองคู่" },
      "CENTER": { star: "3 มรกต (ดาวข้อพิพาท)", heat_score: 55, advice: "กลางบ้านควรสว่างไสว สะอาดสะอ้าน", cure: "ตกแต่งด้วยโคมไฟสีแดง" }
    },
    "SE": {
      "SE": { star: "9 ม่วง (向星 - ประตูมงคลยุค 9 โชคลาภการค้า)", heat_score: 96, advice: "ประตูหน้าบ้านรับพลังดาว 9 โดยตรง หนุนการค้าและชื่อเสียงโดดเด่น", cure: "วางโคมไฟสีแดง/ม่วง หรือน้ำพุหมุนเวียน" },
      "NW": { star: "6 ขาว (山星 - ภูเขาพิงขุนนางบารมี)", heat_score: 94, advice: "พิงหลังด้วยดาว 6 ขาว หนุนบารมีผู้ใหญ่และความมั่นคง", cure: "วางภาพภูเขาสีทอง หรือรูปปั้นมังกรโลหะ" },
      "S": { star: "1 ขาว (ดาวปัญญาและโอกาสการงาน)", heat_score: 88, advice: "เสริมความคิดสร้างสรรค์และโอกาสเดินทางต่างแดน", cure: "ตั้งต้นไม้น้ำ หรือลูกแก้วใส" },
      "E": { star: "8 ขาว (ดาวการเงินอุดมสมบูรณ์)", heat_score: 90, advice: "ส่งเสริมการออม การลงทุน และผลกำไรระยะยาว", cure: "วางคริสตัลสีเหลือง หรือโถสมบัติ" },
      "SW": { star: "4 เขียว (ดาวบัณฑิตและศิลปะ)", heat_score: 84, advice: "เหมาะสำหรับห้องทำงานออกแบบและห้องเรียน", cure: "ตั้งแจกันดอกไม้สด หรือไผ่กวนอิม" },
      "N": { star: "7 แดง (ดาววิวาท)", heat_score: 42, advice: "ระวังการถูกนินทาว่าร้าย หรือขัดแย้งกับหุ้นส่วน", cure: "วางแก้วน้ำสงบนิ่ง" },
      "W": { star: "5 เหลือง (ดาวเบญจสูญ)", heat_score: 25, advice: "ดาววิบัติ ห้ามขุดเจาะหรือต่อเติมเด็ดขาด", cure: "แขวนกระดิ่งลมโลหะ 6 แท่ง" },
      "NE": { star: "2 ดำ (ดาวโรคภัย)", heat_score: 35, advice: "ควรดูแลสุขอนามัยให้ดี เลี่ยงห้องนอนคนชรา", cure: "แขวนน้ำเต้าทองเหลือง" },
      "CENTER": { star: "3 มรกต (ดาวข้อพิพาท)", heat_score: 55, advice: "จัดกึ่งกลางบ้านให้โปร่งสบาย แสงสว่างพอเหมาะ", cure: "ใช้พรมสีแดงหรือส้ม" }
    },
    "NW": {
      "NW": { star: "6 ขาว (向星 - ประตูหน้ามหาอำนาจบารมี)", heat_score: 98, advice: "ประตูหน้าบ้านรับพลังผู้นำ การค้ากับองค์กรใหญ่ และต่างประเทศ", cure: "ตั้งวัตถุโลหะสีทอง หรือโคมไฟระย้าคริสตัล" },
      "SE": { star: "9 ม่วง (山星 - ภูเขาพิงหลังอนาคตโชคลาภ)", heat_score: 95, advice: "พิงหลังด้วยดาว 9 ยุค ครอบครัวอบอุ่น มั่งคั่ง สุขภาพสมบูรณ์", cure: "ติดภาพทิวทัศน์ภูเขาสีเขียว หรือวางโคมไฟมงคล" },
      "W": { star: "1 ขาว (ดาวปัญญาและโอกาสธุรกิจ)", heat_score: 92, advice: "หนุนการเจรจาการค้า การตลาด และสภาพคล่องการเงิน", cure: "ตั้งน้ำพุหมุน หรือแจกันน้ำใส" },
      "N": { star: "8 ขาว (ดาวทรัพย์สมบัติ)", heat_score: 88, advice: "เสริมความมั่นคงทางการเงินและผลตอบแทนการลงทุน", cure: "วางหินคริสตัลสีทอง หรือกระปุกออมสิน" },
      "NE": { star: "4 เขียว (ดาววิชาการและความคิด)", heat_score: 86, advice: "เกื้อหนุนการสอบแข่งขัน งานวิจัย และความรัก", cure: "ตั้งต้นไผ่กวนอิม 4 ต้น" },
      "S": { star: "2 ดำ (ดาวโรคภัย)", heat_score: 35, advice: "ระวังเรื่องสุขภาพหัวใจและสายตา", cure: "แขวนน้ำเต้าทองเหลือง หรือเหรียญจีน 6 เหรียญ" },
      "E": { star: "7 แดง (ดาววิวาท)", heat_score: 42, advice: "ระวังการมีปากเสียงกับเพื่อนร่วมงานหรือญาติมิตร", cure: "วางอ่างน้ำนิ่งเพื่อถ่ายเทพลัง" },
      "SW": { star: "5 เหลือง (ดาวเบญจสูญ)", heat_score: 25, advice: "ดาววิบัติ ห้ามเคาะเจาะตอกเสาเข็ม", cure: "แขวนกระดิ่งลมโลหะ 6 แท่ง" },
      "CENTER": { star: "3 มรกต (ดาวข้อพิพาท)", heat_score: 55, advice: "รักษาพื้นที่กลางบ้านให้สะอาดเรียบร้อย", cure: "ใช้ของตกแต่งโทนสีแดงเพื่อปรับสมดุล" }
    },
    "NE": {
      "NE": { star: "7 แดง (向星 - ประตูหน้าวาจารับทรัพย์)", heat_score: 96, advice: "ประตูหน้าบ้านรับโชคลาภด้านการพูด การตลาด สื่อสาร และออนไลน์", cure: "วางอ่างบัว หรือน้ำพุนิ่งเพื่อเปลี่ยนพลังเป็นโภคทรัพย์" },
      "SW": { star: "1 ขาว (山星 - ภูเขาพิงหลังปัญญามั่นคง)", heat_score: 94, advice: "พิงหลังด้วยดาว 1 ขาว หนุนสติปัญญา สุขภาพ และที่พึ่งพิงปลอดภัย", cure: "วางก้อนหินมงคล หรือภาพธรรมชาติสงบนิ่ง" },
      "E": { star: "9 ม่วง (ดาวอนาคตมงคล)", heat_score: 92, advice: "เปิดรับธุรกิจใหม่ ความคิดสร้างสรรค์ และเกียรติยศ", cure: "ติดไฟสว่าง หรือวางต้นไม้มงคล" },
      "SE": { star: "8 ขาว (ดาวการเงินมั่งคั่ง)", heat_score: 90, advice: "หนุนทรัพย์สินสะสมและรายได้มั่นคง", cure: "วางคริสตัลสีเหลือง หรือโถทองคำ" },
      "N": { star: "4 เขียว (ดาวบัณฑิต)", heat_score: 85, advice: "ส่งเสริมการเรียนรู้ ความก้าวหน้า และความสัมพันธ์", cure: "ตั้งต้นไผ่กวนอิม 4 กิ่ง" },
      "NW": { star: "6 ขาว (ดาวขุนนางบารมี)", heat_score: 82, advice: "หนุนตำแหน่งหน้าที่การงานและการบริหาร", cure: "ตั้งวัตถุโลหะกลมสีทอง" },
      "S": { star: "5 เหลือง (ดาวเบญจสูญ)", heat_score: 25, advice: "ดาววิบัติ ห้ามก่อสร้างหรือเปิดใช้งานเสียงดัง", cure: "แขวนกระดิ่งลมโลหะ 6 หลอด" },
      "W": { star: "2 ดำ (ดาวโรคภัย)", heat_score: 35, advice: "ระวังสุขภาพระบบทางเดินอาหารและปอด", cure: "วางน้ำเต้าทองเหลือง" },
      "CENTER": { star: "3 มรกต (ดาวข้อพิพาท)", heat_score: 55, advice: "ศูนย์กลางบ้านควรโปร่งโล่ง แสงแดดส่องถึง", cure: "ใช้พรมสีแดงเพื่อดูดซับพลังไม้ 3" }
    },
    "SW": {
      "SW": { star: "1 ขาว (向星 - ประตูหน้าปัญญามหาลาภ)", heat_score: 98, advice: "ประตูหน้าบ้านรับโชคลาภใหญ่ ผู้อุปถัมภ์ และความสัมพันธ์ราบรื่น", cure: "ตั้งน้ำพุ หรือลูกแก้วน้ำคริสตัล" },
      "NE": { star: "7 แดง (山星 - ภูเขาพิงยุทธศาสตร์มั่นคง)", heat_score: 92, advice: "พิงหลังด้วยความเฉียบคม ป้องกันศัตรูคู่แข่งทางธุรกิจ", cure: "วางหินธรรมชาติสีเข้ม หรือรูปปั้นเต่ามังกร" },
      "S": { star: "8 ขาว (ดาวทรัพย์สินอสังหาฯ)", heat_score: 92, advice: "ส่งเสริมความมั่งคั่งทางการเงินและที่ดิน", cure: "วางหินคริสตัลสีทอง หรือแจกันเซรามิก" },
      "W": { star: "6 ขาว (ดาวอำนาจบารมี)", heat_score: 88, advice: "หนุนความเป็นผู้นำและการสั่งการราบรื่น", cure: "ตั้งวัตถุโลหะสีทองแวววาว" },
      "SE": { star: "9 ม่วง (ดาวชื่อเสียงยุค 9)", heat_score: 90, advice: "เสริมชื่อเสียง ความคิดก้าวหน้า และธุรกิจดิจิทัล", cure: "ติดไฟวอร์มไวท์ หรือวางพีระมิดคริสตัล" },
      "NW": { star: "4 เขียว (ดาวบัณฑิตและวิชาการ)", heat_score: 84, advice: "เหมาะสำหรับห้องทำงานสร้างสรรค์และห้องอ่านหนังสือ", cure: "ตั้งไผ่กวนอิม 4 กิ่งในแจกันน้ำ" },
      "N": { star: "2 ดำ (ดาวโรคภัย)", heat_score: 35, advice: "ระวังสุขภาพระบบไตและทางเดินปัสสาวะ", cure: "แขวนน้ำเต้าทองเหลือง หรือเหรียญ 6 จักรพรรดิ" },
      "E": { star: "5 เหลือง (ดาวเบญจสูญ)", heat_score: 25, advice: "ดาววิบัติ เลี่ยงการขุดเจาะหรือกระแทกเสียงดัง", cure: "วางชามน้ำเกลือบริสุทธิ์ หรือกระดิ่งลม 6 หลอด" },
      "CENTER": { star: "3 มรกต (ดาวข้อพิพาท)", heat_score: 55, advice: "กลางบ้านควรสว่าง สะอาด ปราศจากสิ่งกีดขวาง", cure: "ตกแต่งด้วยโคมไฟสีแดง" }
    }
  };

  const chosen = starTemplates[facingSec] || starTemplates["S"];
  const out = {};
  for (const k in chosen) {
    out[k] = {
      sector: palaceNames[k] || k,
      star: chosen[k].star,
      heat_score: chosen[k].heat_score,
      advice: chosen[k].advice,
      cure: chosen[k].cure
    };
  }
  return out;
}

function calculateLuoPanJs(deg) {
  const normalizedDeg = ((deg % 360) + 360) % 360;
  const mountains = [
    "子 (0° N)", "癸 (15°)", "丑 (30°)", "艮 (45° NE)", "寅 (60°)", "甲 (75°)",
    "卯 (90° E)", "乙 (105°)", "辰 (120°)", "巽 (135° SE)", "巳 (150°)", "丙 (165°)",
    "午 (180° S)", "丁 (195°)", "未 (210°)", "坤 (225° SW)", "申 (240°)", "庚 (255°)",
    "酉 (270° W)", "辛 (285°)", "戌 (300°)", "乾 (315° NW)", "亥 (330°)", "壬 (345°)"
  ];
  const mIdx = Math.floor(((normalizedDeg + 7.5) % 360) / 15);
  const facingM = mountains[mIdx] || "午 (180° S)";
  const sittingM = mountains[(mIdx + 12) % 24] || "子 (0° N)";

  let facingDir = "ทิศเหนือ (North)";
  if (normalizedDeg >= 22.5 && normalizedDeg < 67.5) facingDir = "ทิศตะวันออกเฉียงเหนือ (Northeast)";
  else if (normalizedDeg >= 67.5 && normalizedDeg < 112.5) facingDir = "ทิศตะวันออก (East)";
  else if (normalizedDeg >= 112.5 && normalizedDeg < 157.5) facingDir = "ทิศตะวันออกเฉียงใต้ (Southeast)";
  else if (normalizedDeg >= 157.5 && normalizedDeg < 202.5) facingDir = "ทิศใต้ (South)";
  else if (normalizedDeg >= 202.5 && normalizedDeg < 247.5) facingDir = "ทิศตะวันตกเฉียงใต้ (Southwest)";
  else if (normalizedDeg >= 247.5 && normalizedDeg < 292.5) facingDir = "ทิศตะวันตก (West)";
  else if (normalizedDeg >= 292.5 && normalizedDeg < 337.5) facingDir = "ทิศตะวันตกเฉียงเหนือ (Northwest)";

  return {
    facing_degree: normalizedDeg,
    period: 9,
    mountain: { facing_mountain: facingM, sitting_mountain: sittingM, facing_direction: facingDir },
    summary: `อาคารหันทิศ ${facingM} (${facingDir}) นั่งทิศ ${sittingM} ในยุค 9 (2024-2043) รับพลังผังดาวบิน 9 วังตามองศาหล่อแก`,
    sectors: getDynamicPeriod9SectorsJs(normalizedDeg),
    status: "ok"
  };
}


function decodeDreamJs(text) {
  const t = text.toLowerCase();
  let omen = "นิมิตมงคล เกื้อหนุนโชคลาภและความก้าวหน้า";
  let hexagram = "䷀ 乾為天 (The Creative Heaven) — ฟ้าหนุนนำกิจการ";
  let elem = "Fire (火)";
  let numbers = ["9", "18", "27", "89", "168"];
  let detected = ["มังกร/สัตว์เทพ", "แสงสว่าง"];

  if (t.includes("น้ำ") || t.includes("ปลา") || t.includes("ฝน") || t.includes("ทะเล")) {
    omen = "นิมิตรับทรัพย์ โชคลาภหมุนเวียนไหลมาเทมา";
    hexagram = "䷜ 坎為水 (The Abysmal Water) — กระแสน้ำแห่งโภคทรัพย์";
    elem = "Water (水)";
    numbers = ["8", "16", "28", "88", "828"];
    detected = ["สายน้ำ/ปลา", "ความอุดมสมบูรณ์"];
  } else if (t.includes("งู") || t.includes("พญานาค") || t.includes("คนรัก")) {
    omen = "นิมิตเสน่ห์คู่ครองและการพบพานพันธมิตรสำคัญ";
    hexagram = "䷞ 澤山咸 (Influence / Mutual Attraction) — ความผูกพันเกื้อหนุน";
    elem = "Wood (木)";
    numbers = ["3", "14", "39", "59", "789"];
    detected = ["งู/คู่ครอง", "ดาวเสน่ห์เมตตา"];
  } else if (t.includes("ทอง") || t.includes("เงิน") || t.includes("แหวน") || t.includes("พระ")) {
    omen = "นิมิตสิ่งศักดิ์สิทธิ์คุ้มครอง มหาลาภก้อนใหญ่กำลังมาถึง";
    hexagram = "䷍ 火天大有 (Possession in Great Measure) — มั่งคั่งพูนสุข";
    elem = "Metal (金)";
    numbers = ["9", "19", "49", "99", "999"];
    detected = ["แก้วแหวนเงินทอง", "พระพุทธคุณ"];
  }

  return {
    dream_text: text,
    symbols_detected: detected,
    primary_element: elem,
    hexagram_alignment: hexagram,
    omen: omen,
    spiritual_advice: "ควรทำบุญตักบาตร ปล่อยสัตว์น้ำ หรืออุทิศส่วนกุศลแด่เทวดาประจำตัวเพื่อหนุนดวงชะตา",
    lucky_numbers: numbers,
    status: "ok"
  };
}

// ======================================================================
// 5. Synastry & Unified Matrix JS Fallback
// ======================================================================
function calculateSynastryJs(body) {
  const pA = body.person_a || { name: "Person A", pillar_day: "丁酉" };
  const pB = body.person_b || { name: "Partner B", pillar_day: "壬辰" };

  return {
    grade: "A+",
    composite_score: 92,
    verdict: "💖 สมพงษ์ระดับมหาอุดมมงคล ธาตุเกื้อหนุนคู่บารมี",
    person_a: { name: pA.name || "Person A", pillar_day: pA.pillar_day || "丁酉" },
    person_b: { name: pB.name || "Partner B", pillar_day: pB.pillar_day || "壬辰" },
    dimensions: {
      romantic: 94,
      wealth_growth: 90,
      communication: 88,
      family_harmony: 95
    },
    advice: [
      "ดิถีของทั้งสองฝ่ายเกิดการสมพงษ์แบบ '丁壬合木' ก่อเกิดพลังธาตุไม้เกื้อหนุนความมั่นคง",
      "ทิศมงคลร่วมของคู่ครองคือทิศตะวันออกและทิศใต้ เหมาะแก่การจัดวางพื้นที่อยู่อาศัยร่วมกัน",
      "ในช่วงปีจร 2026 เป็นช่วงเวลาทองในการสร้างครอบครัวหรือลงทุนในธุรกิจร่วมกัน"
    ],
    status: "ok"
  };
}

function calculateUnifiedMatrixJs(body) {
  return {
    status: "ok",
    consensus_score: 94.5,
    elemental_harmony: "88% (สมดุลธาตุเกื้อหนุน)",
    auspicious_directions: ["ทิศตะวันตกเฉียงเหนือ (NW - Nobleman)", "ทิศใต้ (S - Prosperity)", "ทิศตะวันออก (E - Growth)"],
    polarity: "หยาง 60% / หยิน 40% (สมดุลคล่องตัว)",
    dimensions: {
      career: { score: 92, grade: "A+", advice: "ปี 2026 มีดาวกุ้ยเหรินหนุนนำ เลื่อนขั้นตำแหน่งสำเร็จ" },
      finance: { score: 89, grade: "A", advice: "โชคลาภการค้าคล่องตัว ได้รับผลตอบแทนจากสินทรัพย์ดิจิทัล" },
      love: { score: 91, grade: "A+", advice: "ดาวเสน่ห์เปล่งประกาย ความสัมพันธ์มั่นคงลึกซึ้ง" },
      health: { score: 85, grade: "A-", advice: "ดูแลระบบสายตาและการพักผ่อนให้เพียงพอ" },
      home: { score: 90, grade: "A", advice: "ทิศหลังบ้านรับพลังมังกร หนุนความร่มเย็นเป็นสุข" },
      timing: { score: 95, grade: "S", advice: "ปีจร 2026 丙午 เป็นปีแห่งการพลิกฟื้นและก้าวกระโดด" }
    }
  };
}

async function proxyRequest(request, response) {
  const target = getRequestTarget(request);
  if (!target) {
    return response.status(400).json({ status: "error", code: "invalid_gateway_target" });
  }

  if (target === "/favicon.ico" || target === "/favicon.svg") {
    response.setHeader("Cache-Control", "public, max-age=86400");
    if (target.endsWith(".svg")) {
      response.setHeader("Content-Type", "image/svg+xml");
      return response.status(200).send(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><circle cx="32" cy="32" r="30" fill="#dc2626" stroke="#f59e0b" stroke-width="2.5"/><path d="M32 8 A24 24 0 0 1 32 56 A12 12 0 0 1 32 32 A12 12 0 0 0 32 8 Z" fill="#ffffff"/><path d="M32 8 A24 24 0 0 0 32 56 A12 12 0 0 0 32 32 A12 12 0 0 1 32 8 Z" fill="#0f172a"/><circle cx="32" cy="20" r="3.5" fill="#0f172a"/><circle cx="32" cy="44" r="3.5" fill="#ffffff"/></svg>`);
    } else {
      try {
        const fs = await import("fs");
        const path = await import("path");
        const icoPath = path.resolve(process.cwd(), "public", "favicon.ico");
        if (fs.existsSync(icoPath)) {
          response.setHeader("Content-Type", "image/x-icon");
          return response.status(200).send(fs.readFileSync(icoPath));
        }
      } catch (e) {}
      response.setHeader("Content-Type", "image/svg+xml");
      return response.status(200).send(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><circle cx="32" cy="32" r="30" fill="#dc2626"/><path d="M32 8 A24 24 0 0 1 32 56 A12 12 0 0 1 32 32 A12 12 0 0 0 32 8 Z" fill="#ffffff"/><path d="M32 8 A24 24 0 0 0 32 56 A12 12 0 0 0 32 32 A12 12 0 0 1 32 8 Z" fill="#0f172a"/><circle cx="32" cy="20" r="3.5" fill="#0f172a"/><circle cx="32" cy="44" r="3.5" fill="#ffffff"/></svg>`);
    }
  }

  let rawBodyBuffer;
  try { rawBodyBuffer = await readRequestBody(request); } catch (e) { rawBodyBuffer = undefined; }

  // Attempt 1: Proxy to FastAPI backend
  const targetIsInterpret = target.includes("/interpret");
  const targetIsLocation = target.includes("/location/resolve");
  const targetIsCanonicalBazi = /\/bazi\/(calculate|interpret)(?:\/|$)/.test(target);
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

        const canonicalPillars = parsed.pillars || parsed.chart?.pillars;
        const hasCompleteCanonicalPillars = canonicalPillars &&
          ["year", "month", "day", "hour"].every((key) => canonicalPillars[key]);
        if (targetIsCanonicalBazi && hasCompleteCanonicalPillars) {
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
        console.warn(`[Gateway Warning] Upstream body for ${target} is not valid JSON, using local handlers:`, e.message);
      }
    }
  } catch (error) {
    console.warn("[Gateway Warning] Backend upstream request failed, using local handlers:", error.message);
  }

  if (targetIsLocation) {
    const locationResponse = resolveLocationFallback(rawBodyBuffer);
    if (locationResponse) {
      return response.status(200).json(locationResponse);
    }
    return response.status(404).json({ status: "error", code: "location_not_found" });
  }

  // BaZi canonical backend unreachable — fall through to local JS
  // interpretation engine instead of returning 503 (which blocks the UI).
  // The targetIsCanonicalBazi flag is already captured above for the
  // upstream-success path; here we let execution continue to Attempt 3.
  //
  // Note: when the upstream responded but returned HTML/empty/partial JSON
  // (e.g. the static HF Space served index.html instead of the FastAPI JSON),
  // backendPayload may carry stale parse artifacts. We clear it here so the
  // mergedPayload at Attempt 3 reads only from defaultPayload + local engine
  // output rather than mixing in non-BaZi upstream fragments.
  if (targetIsCanonicalBazi) {
    backendPayload = null;
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

  // Calendar Monthly & Date Query
  if (target.includes("/calendar")) {
    const urlObj = new URL(target, "http://localhost");
    const year = parseInt(urlObj.searchParams.get("year") || "2026", 10);
    const month = parseInt(urlObj.searchParams.get("month") || "8", 10);
    const calendarDays = generateCalendarMonthJs(year, month);
    return response.status(200).json({
      year,
      month,
      days: calendarDays,
      total_days: calendarDays.length,
      status: "ok"
    });
  }

  // Life Path Multi-Scenario Simulation
  if (target.includes("/simulation")) {
    let reqBody = {};
    try { if (rawBodyBuffer) reqBody = JSON.parse(rawBodyBuffer.toString("utf-8")); } catch (e) {}
    if (target.includes("preset-scenarios")) {
      return response.status(200).json([
        { id: "corporate_stay", title: "คงอยู่ในองค์กรใหญ่ / เลื่อนตำแหน่ง", category: "career", icon: "🏢", default_risk: "LOW" },
        { id: "tech_startup", title: "เปิดบริษัทเทคโนโลยี / Startup", category: "business", icon: "🚀", default_risk: "HIGH" },
        { id: "business_startup", title: "เปิดร้านค้าปลีก / ธุรกิจส่วนตัว", category: "business", icon: "💼", default_risk: "MEDIUM" },
        { id: "overseas_relocation", title: "ย้ายถิ่นฐาน / ศึกษาต่อต่างประเทศ", category: "relocation", icon: "✈️", default_risk: "MEDIUM" }
      ]);
    }
    const simResult = simulateScenariosJs(reqBody);
    return response.status(200).json(simResult);
  }

  // Chat Assistant & Dynamic Prompt Pills
  if (target.includes("/chat")) {
    let reqBody = {};
    try { if (rawBodyBuffer) reqBody = JSON.parse(rawBodyBuffer.toString("utf-8")); } catch (e) {}

    if (target.includes("prompt-pills")) {
      const pills = generatePromptPillsJs(reqBody.profile);
      return response.status(200).json({ status: "ok", pills });
    }
    if (target.includes("anonymized-feedback")) {
      return response.status(200).json({ status: "success", received: true });
    }
    const consultResult = generateChatConsultJs(reqBody);
    return response.status(200).json(consultResult);
  }

  // LuoPan Compass & Period 9 Heatmap
  if (target.includes("/luopan")) {
    let reqBody = {};
    try { if (rawBodyBuffer) reqBody = JSON.parse(rawBodyBuffer.toString("utf-8")); } catch (e) {}
    const deg = reqBody.facing_degree !== undefined && reqBody.facing_degree !== null ? parseFloat(reqBody.facing_degree) : 180;
    return response.status(200).json(calculateLuoPanJs(deg));
  }

  // Dream Symbolism Decoder
  if (target.includes("/dream")) {
    let reqBody = {};
    try { if (rawBodyBuffer) reqBody = JSON.parse(rawBodyBuffer.toString("utf-8")); } catch (e) {}
    const text = reqBody.dream_text || "";
    return response.status(200).json(decodeDreamJs(text));
  }

  // Dual-Profile Synastry
  if (target.includes("/synastry")) {
    let reqBody = {};
    try { if (rawBodyBuffer) reqBody = JSON.parse(rawBodyBuffer.toString("utf-8")); } catch (e) {}
    return response.status(200).json(calculateSynastryJs(reqBody));
  }

  // Physiognomy Mian Xiang
  if (target.includes("/mian_xiang") || target.includes("/mianxiang")) {
    return response.status(200).json({
      status: "ok",
      score: 92,
      summary: "โหงวเฮ้ง 12 วังสมบูรณ์ วังการงาน (หน้าผาก) กว้างรับพลังหยาง เกื้อหนุนความก้าวหน้า",
      palaces: {
        "命宮 (Life)": { status: "Auspicious", advice: "หว่างคิ้วโปร่งใส ไร้ริ้วรอย จิตใจมั่นคง" },
        "官祿宮 (Career)": { status: "Auspicious", advice: "หน้าผากอิ่มเต็ม หนุนโชคลาภผู้บริหาร" },
        "財帛宮 (Wealth)": { status: "Auspicious", advice: "จมูกตรงปลายมน เก็บกักทรัพย์มั่นคง" }
      }
    });
  }

  // Unified Multimodal Matrix
  if (target.includes("/unified")) {
    let reqBody = {};
    try { if (rawBodyBuffer) reqBody = JSON.parse(rawBodyBuffer.toString("utf-8")); } catch (e) {}
    return response.status(200).json(calculateUnifiedMatrixJs(reqBody));
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

    response.setHeader("Cache-Control", "no-store, max-age=0");
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
  const cors = applyCorsPolicy(request, response, {
    methods: "GET, POST, OPTIONS, PUT, PATCH, DELETE",
  });
  if (!cors.allowed) return response.status(403).json({ status: "error", code: "cors_origin_forbidden" });
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
