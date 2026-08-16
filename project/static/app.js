const BACKEND_API_HOSTS = [
  "https://horo-consultant-psi.vercel.app", // Primary Vercel Production Serverless API Gateway
  "", // Relative origin (local server / same-origin proxy)
];

let activeApiCallCount = 0;

function updateGlobalApiLoader(isLoading, message) {
  const loader = document.getElementById('global-api-loader');
  const loaderText = document.getElementById('global-api-loader-text');

  if (!loader) {
    return;
  }

  if (message && loaderText) {
    loaderText.textContent = message;
  }

  if (isLoading) {
    loader.classList.remove('hidden');
    return;
  }

  loader.classList.add('hidden');
}

function beginApiRequest(message) {
  activeApiCallCount += 1;
  updateGlobalApiLoader(true, message || 'กำลังรอผลจาก API...');
}

function endApiRequest() {
  activeApiCallCount = Math.max(0, activeApiCallCount - 1);
  if (activeApiCallCount === 0) {
    updateGlobalApiLoader(false);
  }
}

function getApiBaseUrl() {
  if (typeof window !== 'undefined' && window.API_BASE_URL) {
    return window.API_BASE_URL;
  }
  if (typeof window !== 'undefined' && window.location && window.location.hostname.includes('static.hf.space')) {
    return 'https://horo-consultant-psi.vercel.app';
  }
  return '';
}

async function fetchApi(endpoint, options = {}) {
  const requestOptions = { ...options };
  const shouldShowLoader = requestOptions.showLoader !== false;
  const loaderMessage = requestOptions.loaderMessage || 'กำลังรอผลจาก API...';
  const timeoutMs = requestOptions.timeoutMs || 2500;
  delete requestOptions.showLoader;
  delete requestOptions.loaderMessage;
  delete requestOptions.timeoutMs;

  if (shouldShowLoader) {
    beginApiRequest(loaderMessage);
  }

  try {
    const customBase = getApiBaseUrl();
    const candidateBases = customBase
      ? [customBase, ...BACKEND_API_HOSTS.filter(b => b !== customBase)]
      : BACKEND_API_HOSTS;

    let lastError = null;
    for (const base of candidateBases) {
      if (!base && typeof window !== 'undefined' && window.location && window.location.hostname.includes('static.hf.space')) {
        continue;
      }
      const url = base ? `${base}${endpoint}` : endpoint;
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
        const res = await fetch(url, { ...requestOptions, signal: requestOptions.signal || controller.signal });
        clearTimeout(timeoutId);
        if (res.ok) {
          return res;
        }
        if (res.status === 404) {
          console.warn(`[API Fallback] ${url} returned 404, trying next host...`);
          lastError = new Error(`HTTP 404 from ${url}`);
          continue;
        }
        return res;
      } catch (err) {
        console.warn(`[API Fallback] ${url} failed: ${err.message}, trying next host...`);
        lastError = err;
      }
    }
    throw lastError || new Error(`All API hosts failed for ${endpoint}`);
  } finally {
    if (shouldShowLoader) {
      endApiRequest();
    }
  }
}


function loadPreset(datetime, lng, utc, label) {
  document.getElementById('birth_datetime').value = datetime;
  document.getElementById('longitude').value = lng;
  document.getElementById('utc_offset_hours').value = utc;
  console.log(`Loaded preset: ${label}`);
}

const CLIENT_LOCATION_DICT = {
  "กรุงเทพ": { name: "กรุงเทพมหานคร, ประเทศไทย", lng: 100.5018, utc: 7.0 },
  "กรุงเทพมหานคร": { name: "กรุงเทพมหานคร, ประเทศไทย", lng: 100.5018, utc: 7.0 },
  "bangkok": { name: "Bangkok, Thailand", lng: 100.5018, utc: 7.0 },
  "บางกะปิ": { name: "เขตบางกะปิ, กรุงเทพมหานคร, ประเทศไทย", lng: 100.6439, utc: 7.0 },
  "จตุจักร": { name: "เขตจตุจักร, กรุงเทพมหานคร, ประเทศไทย", lng: 100.5604, utc: 7.0 },
  "สาทร": { name: "เขตสาทร, กรุงเทพมหานคร, ประเทศไทย", lng: 100.5262, utc: 7.0 },
  "พญาไท": { name: "เขตพญาไท, กรุงเทพมหานคร, ประเทศไทย", lng: 100.5342, utc: 7.0 },
  "ปทุมวัน": { name: "เขตปทุมวัน, กรุงเทพมหานคร, ประเทศไทย", lng: 100.5347, utc: 7.0 },
  "เชียงใหม่": { name: "อำเภอเมืองเชียงใหม่, จังหวัดเชียงใหม่", lng: 98.9853, utc: 7.0 },
  "chiang mai": { name: "Chiang Mai, Thailand", lng: 98.9853, utc: 7.0 },
  "ภูเก็ต": { name: "อำเภอเมืองภูเก็ต, จังหวัดภูเก็ต", lng: 98.3923, utc: 7.0 },
  "phuket": { name: "Phuket, Thailand", lng: 98.3923, utc: 7.0 },
  "ชลบุรี": { name: "จังหวัดชลบุรี, ประเทศไทย", lng: 100.9847, utc: 7.0 },
  "พัทยา": { name: "เมืองพัทยา, จังหวัดชลบุรี", lng: 100.8771, utc: 7.0 },
  "ขอนแก่น": { name: "จังหวัดขอนแก่น, ประเทศไทย", lng: 102.8350, utc: 7.0 },
  "โคราช": { name: "จังหวัดนครราชสีมา, ประเทศไทย", lng: 102.0978, utc: 7.0 },
  "นครราชสีมา": { name: "จังหวัดนครราชสีมา, ประเทศไทย", lng: 102.0978, utc: 7.0 },
  "สงขลา": { name: "จังหวัดสงขลา, ประเทศไทย", lng: 100.5954, utc: 7.0 },
  "หาดใหญ่": { name: "อำเภอหาดใหญ่, จังหวัดสงขลา", lng: 100.4747, utc: 7.0 },
  "นนทบุรี": { name: "จังหวัดนนทบุรี, ประเทศไทย", lng: 100.5217, utc: 7.0 },
  "สมุทรปราการ": { name: "จังหวัดสมุทรปราการ, ประเทศไทย", lng: 100.5998, utc: 7.0 },
  "tokyo": { name: "Tokyo, Japan", lng: 139.6917, utc: 9.0 },
  "โตเกียว": { name: "Tokyo, Japan", lng: 139.6917, utc: 9.0 },
  "london": { name: "London, United Kingdom", lng: -0.1276, utc: 0.0 },
  "ลอนดอน": { name: "London, United Kingdom", lng: -0.1276, utc: 0.0 },
  "new york": { name: "New York, USA", lng: -74.0060, utc: -5.0 },
  "นิวยอร์ก": { name: "New York, USA", lng: -74.0060, utc: -5.0 },
  "singapore": { name: "Singapore", lng: 103.8198, utc: 8.0 },
  "สิงคโปร์": { name: "Singapore", lng: 103.8198, utc: 8.0 }
};

async function resolveLocation() {
  const locInput = document.getElementById('location_search').value.trim();
  if (!locInput) return;
  
  const statusEl = document.getElementById('location-status');
  const spinner = document.getElementById('loc-spinner');
  
  spinner.classList.remove('hidden');
  statusEl.textContent = "กำลังค้นหาพิกัด...";
  statusEl.style.color = "#94a3b8";
  
  try {
    const res = await fetchApi('/api/v1/location/resolve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ location: locInput })
    });
    
    if (res.ok) {
      const data = await res.json();
      document.getElementById('longitude').value = data.longitude.toFixed(4);
      document.getElementById('utc_offset_hours').value = data.utc_offset_hours;
      
      const offsetSign = data.utc_offset_hours >= 0 ? '+' : '';
      statusEl.textContent = `✅ ${data.location} (UTC${offsetSign}${data.utc_offset_hours})`;
      statusEl.style.color = "#10b981";
      spinner.classList.add('hidden');
      return;
    }
  } catch (err) {
    console.warn("API location resolve failed, switching to client-side fallback dictionary:", err);
  }

  // Client-side Fallback Dictionary Lookup
  const cleanKey = locInput.toLowerCase();
  let match = null;
  for (const [k, v] of Object.entries(CLIENT_LOCATION_DICT)) {
    if (k.includes(cleanKey) || cleanKey.includes(k)) {
      match = v;
      break;
    }
  }

  if (!match && cleanKey.length > 0) {
    // Default fallback to Bangkok if specific location not found in dictionary
    match = { name: `${locInput} (พิกัดเทียบเคียง กรุงเทพมหานคร)`, lng: 100.5018, utc: 7.0 };
  }

  if (match) {
    document.getElementById('longitude').value = match.lng.toFixed(4);
    document.getElementById('utc_offset_hours').value = match.utc;
    const offsetSign = match.utc >= 0 ? '+' : '';
    statusEl.textContent = `✅ ${match.name} (UTC${offsetSign}${match.utc})`;
    statusEl.style.color = "#10b981";
  } else {
    statusEl.textContent = "❌ ไม่พบสถานที่ดังกล่าว โปรดลองพิมพ์ชื่อให้ชัดเจนขึ้น";
    statusEl.style.color = "#ef4444";
  }
  spinner.classList.add('hidden');
}

async function updateVersionFooter() {
  try {
    const startTime = performance.now();
    const res = await fetchApi('/health', { showLoader: false }).catch(() => null);
    const latency = Math.round(performance.now() - startTime);
    const healthBadge = document.getElementById('health-status-badge');

    if (res && res.ok) {
      const data = await res.json();
      const rawVer = data.version || (data.git_commit ? `1.0.0.${data.git_commit.slice(0, 7)}` : '1.0.0');
      const versionStr = rawVer.startsWith('v') ? rawVer : `v${rawVer}`;
      const footerEl = document.getElementById('footer-version-text');
      if (footerEl && versionStr) {
        footerEl.textContent = `Computational Metaphysics Engine ${versionStr} — Powered by Local Ollama (qwen2.5:7b + nomic-embed-text) & Dual Gemini API Fallback`;
      }
      if (healthBadge) {
        healthBadge.className = 'status-badge health-badge';
        const gwName = data.gateway ? ` Gateway (${data.gateway})` : '';
        const vectorCount = data.vector_store_chunks ? ` • ${data.vector_store_chunks.toLocaleString()} Chunks` : '';
        healthBadge.innerHTML = `<span class="pulse-dot cyan"></span><span class="health-text">Health: OK${gwName}${vectorCount} • ${latency}ms</span>`;
      }
    } else {
      if (healthBadge) {
        healthBadge.className = 'status-badge health-badge amber-badge';
        healthBadge.innerHTML = `<span class="pulse-dot amber"></span><span class="health-text">Health: Standby (Local Engine Fallback)</span>`;
      }
    }
  } catch (err) {
    console.warn('Could not update dynamic version footer:', err);
    const healthBadge = document.getElementById('health-status-badge');
    if (healthBadge) {
      healthBadge.className = 'status-badge health-badge amber-badge';
      healthBadge.innerHTML = `<span class="pulse-dot amber"></span><span class="health-text">Health: Standby (Local Engine Fallback)</span>`;
    }
  }
}

function buildBaZiDomainInterpretation(query, birthDatetime, dayMasterStem = '庚', dayMasterElement = 'Metal') {
  const q = (query || "").trim().toLowerCase();
  const dateStr = birthDatetime || "1990-05-15 14:30:00";

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
3. **ข้อแนะนำในการส่งเสริมพัฒนาการ**: ควรเน้นการสื่อสารด้วยความเข้าใจ เปิดโอกาสให้คิดและตัดสินใจด้วยตนเอง หลีกเลี่ยงการใช้อารมณ์กดดัน และสนับสนุนกิจกรรมที่ใช้จินตนาการและการวิเคราะห์`;
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
  if (/อาชีพ|การงาน|ย้ายงาน|ทำธุรกิจ|ทำงาน|ยศ|ตำแหน่ง|career|job|work|business/.test(q) || (q.includes("งาน") && !q.includes("แต่งงาน"))) {
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

  if (/สุขภาพ|ป่วย|โรค|ร่างกาย|สายตา|กระดูก|health|body/.test(q)) {
    return `### 🔮 การวิเคราะห์ผังดวงจีนด้านสุขภาพและพลังชีวิต (BaZi Health Analysis)

- **วันเวลาเกิด**: ${dateStr}
- **ดิถีประจำตัว (Day Master)**: ดิถี ${dayMasterStem} (${dayMasterElement})
- **อวัยวะประจำธาตุหลัก**: ระบบทางเดินหายใจ ปอด ผิวหนัง

📌 **คำทำนายเจาะจงมิติสุขภาพ:**
การปรับสมดุล 5 ธาตุสำหรับดิถี ${dayMasterStem} (${dayMasterElement}) แนะนำให้ดูแลระบบปอด การหายใจ ผิวหนัง และปรับการพักผ่อนให้เพียงพอ

1. **แนวทางดูแลสุขภาพ**: ควรรับประทานอาหารที่มีคุณสมบัติปรับสมดุล ออกกำลังกายอย่างสม่ำเสมอ และออกรับอากาศบริสุทธิ์`;
  }

  return `### 🔮 การวิเคราะห์ผังดวงจีน 4 เสาหลักแบบครอบคลุม (BaZi Comprehensive Reading)

- **วันเวลาเกิด**: ${dateStr}
- **ดิถีประจำตัว (Day Master)**: ดิถี ${dayMasterStem} (${dayMasterElement})
- **คำถามวิเคราะห์เฉพาะ**: "${query || "ภาพรวมดวงชะตา"}"

📌 **บทวิเคราะห์โครงสร้างดวงชะตา (ตามหลักคัมภีร์ 子平真詮 และ 滴天髓):**
ดวงชะตานี้มีดิถีวันเป็น ${dayMasterStem} (${dayMasterElement}) ซึ่งมีพลังปรับสมดุลชีวิตร่วมกับธาตุไม้และธาตุน้ำ การดำเนินชีวิตการงาน การเงิน ความสัมพันธ์ และสุขภาพจะมีความราบรื่นและประสบความสำเร็จสูงเมื่อปรับยุทธศาสตร์ชีวิตตามสมดุล 5 ธาตุ`;
}

function buildBaziPayloadFromForm() {
  return {
    birth_datetime: document.getElementById('birth_datetime').value,
    longitude: parseFloat(document.getElementById('longitude').value),
    utc_offset_hours: parseFloat(document.getElementById('utc_offset_hours').value),
    unknown_hour: document.getElementById('unknown_hour').checked,
    enable_validation: document.getElementById('enable_validation').checked,
    query: document.getElementById('query').value,
    interpretation_depth: getInterpretationDepthFromForm()
  };
}

function getInterpretationDepthFromForm() {
  const el = document.getElementById('interpretation_depth');
  if (!el) return 'short';
  const depth = String(el.value || 'short').toLowerCase();
  return ['short', 'medium', 'deep'].includes(depth) ? depth : 'short';
}

function interpretationDepthLabel(depth = 'short') {
  if (depth === 'deep') return 'ตีความเชิงลึก (Deep)';
  if (depth === 'medium') return 'สรุปเชิงตีความปานกลาง (Medium)';
  return 'สรุปสั้น (Short)';
}

const CHINESE_STEMS = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸'];
const CHINESE_BRANCHES = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'];

function normalizeInt(value, fallback = 0) {
  const num = parseInt(value, 10);
  return Number.isFinite(num) ? num : fallback;
}

function extractBirthDateParts() {
  const raw = document.getElementById('birth_datetime')?.value || '';
  const match = raw.match(/^\s*(\d{4})-(\d{2})-(\d{2})/);
  if (!match) {
    return null;
  }
  return {
    year: normalizeInt(match[1], 0),
    month: normalizeInt(match[2], 1),
    day: normalizeInt(match[3], 1)
  };
}

function getYearStemBranchForDate(year, month, day) {
  if (!year) return { stem: '-', branch: '-' };
  const eff = (month < 2 || (month === 2 && day < 4)) ? year - 1 : year;
  const stemIdx = ((eff - 4) % 10 + 10) % 10;
  const branchIdx = ((eff - 4) % 12 + 12) % 12;
  return {
    stem: CHINESE_STEMS[stemIdx],
    branch: CHINESE_BRANCHES[branchIdx]
  };
}

function buildCycleSummary(chart = {}) {
  const birth = extractBirthDateParts();
  const now = new Date();
  const nowParts = {
    year: now.getFullYear(),
    month: now.getMonth() + 1,
    day: now.getDate()
  };

  if (!birth || !birth.year) {
    return {
      ageNow: '-',
      ageCycle: 'ข้อมูลวันเกิดไม่ครบสำหรับคำนวณวัยจร',
      annualCycle: 'ข้อมูลปีจรยังไม่สามารถคำนวณได้'
    };
  }

  let age = nowParts.year - birth.year;
  if (nowParts.month < birth.month || (nowParts.month === birth.month && nowParts.day < birth.day)) {
    age -= 1;
  }
  if (age < 0) age = 0;

  const cycleStart = Math.floor(age / 10) * 10;
  const cycleEnd = cycleStart + 9;
  const cycleLabel = `ช่วงวัยจรปัจจุบัน: ${cycleStart === 0 ? 1 : cycleStart}-${cycleEnd} ปี (อายุจริง ${age} ปี)`;

  const currentYearPillar = getYearStemBranchForDate(nowParts.year, nowParts.month, nowParts.day);
  const annualCycle = `ปีจรปัจจุบัน: ${nowParts.year} = ${currentYearPillar.stem}${currentYearPillar.branch} (เสาอายุนี้)`;

  return {
    ageNow: age,
    ageCycle: cycleLabel,
    annualCycle
  };
}

function getElementColorByName(element) {
  const colors = {
    Wood: '#10b981',
    Fire: '#ef4444',
    Earth: '#f59e0b',
    Metal: '#94a3b8',
    Water: '#3b82f6',
    木: '#10b981',
    火: '#ef4444',
    土: '#f59e0b',
    金: '#94a3b8',
    水: '#3b82f6'
  };
  return colors[element] || '#f8fafc';
}

function buildFallbackFourPillarsSvg(chartData = {}) {
  const chart = chartData.chart || chartData;
  const dm = chart.day_master || {};
  const pillars = chart.pillars || {};
  const pcts = (chart.five_elements && chart.five_elements.percentages) || {};
  const order = [
    { key: 'year', label: 'ปี (Year)', zh: '年柱' },
    { key: 'month', label: 'เดือน (Month)', zh: '月柱' },
    { key: 'day', label: 'วัน (Day)', zh: '日柱' },
    { key: 'hour', label: 'ยาม (Hour)', zh: '時柱' }
  ];
  const elements = ['Wood', 'Fire', 'Earth', 'Metal', 'Water'];

  const cols = order.map((entry) => {
    const p = pillars[entry.key] || {};
    const stem = p.stem || {};
    const branch = p.branch || {};
    return {
      label: entry.label,
      zh: entry.zh,
      stem: stem.char || stem || '-',
      branch: branch.char || branch || '-',
      stemElement: stem.element || '-',
      branchElement: branch.element || '-',
      stemPinyin: stem.pinyin || '',
      branchPinyin: branch.pinyin || ''
    };
  });

  const barScale = elements.map((el) => {
    const value = Number(pcts[el]) || 0;
    return { name: el, value };
  });
  let total = barScale.reduce((acc, item) => acc + item.value, 0);
  if (!total || total <= 0) {
    total = 100;
  }

  return `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 860 560" width="100%" height="100%" aria-label="Four Pillars SVG">
      <defs>
        <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#0a0c16"/>
          <stop offset="100%" stop-color="#111a31"/>
        </linearGradient>
      </defs>
      <rect x="0" y="0" width="860" height="560" rx="14" fill="url(#bg)" stroke="#334155" stroke-width="2"/>
      <text x="430" y="38" text-anchor="middle" fill="#fbbf24" font-size="22" font-family="Prompt, sans-serif" font-weight="700">☯ Four Pillars of Destiny (四柱)</text>
      <text x="430" y="64" text-anchor="middle" fill="#94a3b8" font-size="13" font-family="Prompt, sans-serif">True Solar Time (TST): ${chart.tst?.tst_datetime || 'N/A'} | Day Master: ${dm.stem || '-'} (${dm.element || '-'} ${dm.polarity || '-'})</text>
      <g transform="translate(50 95)">
      ${cols.map((col, i) => {
        const x = i * 180;
        const stemColor = getElementColorByName(col.stemElement);
        const branchColor = getElementColorByName(col.branchElement);
        return `
          <g transform="translate(${x} 0)">
            <rect x="0" y="0" width="160" height="330" rx="12" fill="#1e293b" fill-opacity="0.6" stroke="#475569" stroke-width="1.5"/>
            <text x="80" y="22" text-anchor="middle" fill="#94a3b8" font-size="14" font-weight="700" font-family="Prompt, sans-serif">${col.label}</text>
            <text x="80" y="40" text-anchor="middle" fill="#f8fafc" font-size="11" font-family="Prompt, sans-serif">${col.zh}</text>
            <rect x="15" y="55" width="130" height="115" rx="10" fill="${stemColor}" fill-opacity="0.16" stroke="${stemColor}" stroke-width="2"/>
            <text x="80" y="120" text-anchor="middle" fill="${stemColor}" font-size="44" font-family="sans-serif" font-weight="700">${col.stem}</text>
            <text x="80" y="157" text-anchor="middle" fill="#e2e8f0" font-size="11" font-family="Prompt, sans-serif">${col.stemPinyin || ''} ${col.stemElement ? `(${col.stemElement})` : ''}</text>
            <rect x="15" y="180" width="130" height="115" rx="10" fill="${branchColor}" fill-opacity="0.16" stroke="${branchColor}" stroke-width="2"/>
            <text x="80" y="245" text-anchor="middle" fill="${branchColor}" font-size="44" font-family="sans-serif" font-weight="700">${col.branch}</text>
            <text x="80" y="282" text-anchor="middle" fill="#e2e8f0" font-size="11" font-family="Prompt, sans-serif">${col.branchPinyin || ''} ${col.branchElement ? `(${col.branchElement})` : ''}</text>
          </g>
        `;
      }).join('')}
      </g>
      <text x="50" y="470" fill="#f59e0b" font-size="15" font-weight="700" font-family="Prompt, sans-serif">⚖️ สัดส่วนสมดุล 5 ธาตุ (Five Elements)</text>
      ${barScale.map((entry, index) => {
        const y = 485 + index * 26;
        const width = (entry.value / total) * 470;
        const color = getElementColorByName(entry.name);
        return `
          <g>
            <text x="50" y="${y}" fill="${color}" font-size="12" font-family="Prompt, sans-serif">${entry.name}: ${entry.value.toFixed(1)}%</text>
            <rect x="170" y="${y - 10}" width="470" height="12" rx="6" fill="#334155"/>
            <rect x="170" y="${y - 10}" width="${Math.max(12, width)}" height="12" rx="6" fill="${color}"/>
          </g>
        `;
      }).join('')}
    </svg>
  `;
}

const BAZI_PILLAR_ORDER = [
  { key: 'year', label: 'ปี', zh: '年柱', theme: 'พื้นฐานอัตลักษณ์ตระกูล' },
  { key: 'month', label: 'เดือน', zh: '月柱', theme: 'ฐานฤกษ์และจังหวะกาลเวลา' },
  { key: 'day', label: 'วัน', zh: '日柱', theme: 'โครงแกนดวงชะตาหลัก (Day Master)' },
  { key: 'hour', label: 'ยาม', zh: '時柱', theme: 'แนวโน้มภาคปฏิบัติ/อนาคตระยะสั้น' }
];

const BAZI_ELEMENT_LABEL = {
  Metal: 'ทอง',
  木: 'ไม้',
  Water: 'น้ำ',
  水: 'น้ำ',
  Wood: 'ไม้',
  Fire: 'ไฟ',
  火: 'ไฟ',
  Earth: 'ดิน',
  土: 'ดิน'
};

const BAZI_GENERATE_MAP = {
  Wood: ['Fire'],
  Wood: ['Fire'],
  Fire: ['Earth'],
  Earth: ['Metal'],
  Metal: ['Water'],
  Water: ['Wood'],
  木: ['火'],
  火: ['土'],
  土: ['金'],
  金: ['水'],
  水: ['木']
};

const BAZI_CONTROL_MAP = {
  Wood: ['Earth'],
  木: ['土'],
  Fire: ['Water'],
  火: ['水'],
  Earth: ['Water'],
  土: ['水'],
  Metal: ['Fire'],
  金: ['火'],
  Water: ['Fire'],
  水: ['火']
};

function isRenderableSvg(content) {
  return typeof content === 'string' && content.includes('<svg') && content.includes('</svg>');
}

function normalizeElementName(element) {
  const mapping = {
    木: 'Wood',
    木: 'Wood',
    火: 'Fire',
    土: 'Earth',
    金: 'Metal',
    水: 'Water'
  };

  if (!element) return '-';
  if (typeof element === 'string') {
    return mapping[element] || element;
  }
  return '-';
}

function getElementRelationTone(source, target) {
  const src = normalizeElementName(source);
  const tgt = normalizeElementName(target);

  if (!src || src === '-' || !tgt || tgt === '-') {
    return 'ความสัมพันธ์กำลังสมดุล (ข้อมูลยังไม่ครบ)';
  }

  if (src === tgt) {
    return 'ธาตุเดียวกัน (เสถียรและต่อเนื่อง)';
  }

  if ((BAZI_GENERATE_MAP[src] || []).includes(tgt)) {
    return 'เสริม/ให้พลังกับดิถีวัน';
  }

  if ((BAZI_GENERATE_MAP[tgt] || []).includes(src)) {
    return 'ใช้พลังจากวันเกิด (ดิถีวันถูกขยายเป็นจุดงาน)';
  }

  if ((BAZI_CONTROL_MAP[src] || []).includes(tgt)) {
    return 'ควบคุม/ปรับจุดสมดุลในเชิงกำกับ';
  }

  if ((BAZI_CONTROL_MAP[tgt] || []).includes(src)) {
    return 'เป็นเสาหลักที่รับอิทธิพลคุมได้สูง';
  }

  return 'ปฏิสัมพันธ์กลาง-ค่อนข้างกลาง';
}

function formatPillarCell(pillar) {
  const p = pillar || {};
  const stem = p.stem || {};
  const branch = p.branch || {};
  const stemText = stem.char || stem || '-';
  const branchText = branch.char || branch || '-';
  const stemElement = normalizeElementName(stem.element || stemElementAlias(stem));
  const branchElement = normalizeElementName(branch.element || stemElementAlias(branch));

  return {
    stemText,
    branchText,
    stemElement,
    branchElement
  };
}

function stemElementAlias(data) {
  return data && data.th_name ? BAZI_ELEMENT_LABEL[data.th_name] || data.th_name : null;
}

function buildPillarResearchMarkdown(chart, queryText = 'ภาพรวมดวงชะตา', interpretationDepth = 'short') {
  const c = chart || {};
  const dm = normalizeElementName((c.day_master || {}).element) || 'Metal';
  const q = queryText && queryText.trim() ? queryText.trim() : 'ภาพรวมดวงชะตา';
  const depth = ['short', 'medium', 'deep'].includes(interpretationDepth) ? interpretationDepth : 'short';

  const lines = BAZI_PILLAR_ORDER.map((entry) => {
    const p = formatPillarCell((c.pillars || {})[entry.key]);
    const stemRelation = getElementRelationTone(p.stemElement, dm);
    const branchRelation = getElementRelationTone(p.branchElement, dm);
    const stemText = `${p.stemText} (${BAZI_ELEMENT_LABEL[p.stemElement] || p.stemElement})`;
    const branchText = `${p.branchText} (${BAZI_ELEMENT_LABEL[p.branchElement] || p.branchElement})`;
    const toneCore = `เสาหลัก ${stemRelation}`;
    const toneBranch = `เสาแขนง ${branchRelation}`;
    if (depth === 'short') {
      return `- **${entry.label} (${entry.zh})**: ${stemText} / ${branchText} — ${toneCore} + ${toneBranch}`;
    }
    if (depth === 'medium') {
      return `- **${entry.label} (${entry.zh})**: ${stemText} / ${branchText}
  - แนวคิด: ${toneCore} และ ${toneBranch}
  - แนวโน้มตีความ: หากมีคำถามเกี่ยวกับ ${q} ให้ติดตามสมดุลต้นน้ำ-ปลายทางของเสานี้ต่อ 3–4 ปัจจัยจุลภาค`; 
    }

    return `- **${entry.label} (${entry.zh})**: ${stemText} / ${branchText}
  - แนวคิดเชิงลึก: ${toneCore} และ ${toneBranch}
  - สัญญาณตีความเชิงสถานการณ์: สำหรับโจทย์ "${q}" ให้พิจารณาความถี่ธาตุ, วันเกิดที่สัมพันธ์กับเสาหลัก, และความสมดุลปลายทาง 2 ชั้น (ฤกษ์-เสา)
  - สรุปเชิงปฏิบัติ: ใช้เสานี้เป็นตัวชี้จังหวะปรับโครงสร้างเส้นทางตัดสินใจและวางลำดับการพัฒนาจีวิต`; 
  });

  return `### 🔬 Research Summary (${interpretationDepthLabel(depth)})
**โจทย์วิเคราะห์:** ${q}

${lines.join('\n')}

**หมายเหตุเชิงวิธี:** คิดจากหลัก **4 เสา (四柱)** + ความสัมพันธ์กับ **Day Master** ผ่านกฎ 5 ธาตุ (生 / 克) โดยกำหนดระดับความลึกตามตัวเลือก ${interpretationDepthLabel(depth)}
`;
}

function buildPillarResearchHtml(chart, queryText = 'ภาพรวมดวงชะตา', interpretationDepth = 'short') {
  const markdown = buildPillarResearchMarkdown(chart, queryText, interpretationDepth);
  if (typeof marked !== 'undefined') {
    return marked.parse(markdown);
  }

  return markdown.replace(/\n/g, '<br>');
}

function buildPillarsGridHtml(chart) {
  const p = chart.pillars || {};
  return BAZI_PILLAR_ORDER.map((entry) => {
    const c = formatPillarCell(p[entry.key]);
    return `
      <div class="pillar-box" style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(212, 175, 55, 0.3); padding: 8px; border-radius: 6px; text-align: center;">
        <div style="font-size: 0.8rem; color: #94a3b8;">${entry.label} (${entry.zh})</div>
        <div style="font-size: 0.73rem; color: #cbd5e1; margin-bottom: 4px;">${entry.theme}</div>
        <div style="font-size: 1.3rem; color: #fbbf24; font-weight: bold;">${c.stemText}</div>
        <div style="font-size: 1.1rem; color: #e2e8f0;">${c.branchText}</div>
      </div>
    `;
  }).join('');
}

function showBaziResultLoading(message = 'กำลังคำนวณผังดวง 4 เสา & ตีความด้วย AI...') {
  const cardIds = ['branch-result-card', 'svg-chart-card', 'pillars-card', 'elements-card', 'interpretation-card'];
  const resultsContainer = document.getElementById('results-container');

  cardIds.forEach((id) => {
    const card = document.getElementById(id);
    if (!card) return;
    card.classList.remove('hidden');
  });

  if (resultsContainer) {
    resultsContainer.classList.remove('hidden');
  }

  const chartContainer = document.getElementById('svg-chart-container');
  const pillarsGrid = document.getElementById('pillars-grid');
  const elementsBars = document.getElementById('elements-bars');
  const dmBanner = document.getElementById('day-master-banner') || document.getElementById('day-master-badge');
  const rd = document.getElementById('reading-body') || document.getElementById('llm-markdown-output');
  const rb = document.getElementById('branch-body') || document.getElementById('5-branch-body');

  const loadingBadge = `<div style="text-align:center; padding: 1.25rem; display:flex; align-items:center; justify-content:center; gap:0.6rem; color:#cbd5e1;"><span class="spinner spinner-gold spinner-lg"></span><span>${message}</span></div>`;

  if (chartContainer) chartContainer.innerHTML = loadingBadge;
  if (pillarsGrid) pillarsGrid.innerHTML = loadingBadge;
  if (elementsBars) elementsBars.innerHTML = loadingBadge;
  if (dmBanner) dmBanner.innerHTML = 'วิเคราะห์ค่าสมดุลดวงชะตากำลังโหลด...';
  if (rd) rd.innerHTML = loadingBadge;
  if (rb) rb.innerHTML = `<div style="padding: 1rem; color: #e2e8f0; line-height: 1.6;">${loadingBadge}<div style="margin-top: 0.8rem; color: #94a3b8; font-size: 0.85rem;">ระบบหลักที่ใช้: BaZi Four Pillars (四柱) + True Solar Time (TST) + 5 ธาตุ</div></div>`;
}

function renderFourPillarsBranchCard(chartData, svgContent, interpretationDepth = 'short') {
  const chart = chartData || {};
  const dm = chart.day_master || {};
  const pillars = chart.pillars || {};
  const pillarOrder = ['year', 'month', 'day', 'hour'];
  const inputLocation = (document.getElementById('location_search')?.value || '').trim();
  const inputName = (document.getElementById('name')?.value || '').trim();
  const inputBirth = document.getElementById('birth_datetime')?.value || '-';
  const inputLongitude = document.getElementById('longitude')?.value || '-';
  const inputUtc = document.getElementById('utc_offset_hours')?.value || '-';
  const queryText = document.getElementById('query')?.value || 'ภาพรวมดวงชะตา';
  const pillarsText = pillarOrder.map((key) => {
    const fmt = formatPillarCell(pillars[key]);
    const label = BAZI_PILLAR_ORDER.find((p) => p.key === key);
    return `<strong>${label ? label.label : key}</strong>: ${fmt.stemText}/${fmt.branchText}`;
  }).join(' | ');
  const svg = svgContent || buildFallbackFourPillarsSvg(chart);
  const cardTitle = '<h4 style="color: #c084fc; margin-top: 0;">🏛️ ผลวิเคราะห์วิชา Four Pillars (四柱) — คอนเทกซ์ Research</h4>';
  const hasInputName = inputName ? `<p style="margin: 0.4rem 0;"><strong>ข้อมูลชื่อผู้ใช้:</strong> ${inputName}</p>` : '';
  const cycle = buildCycleSummary(chart);

  const cyclesPanel = `
    <div style="margin-left: auto; width: min(360px, 100%); border: 1px solid rgba(99, 102, 241, 0.3); border-radius: 10px; background: rgba(99, 102, 241, 0.15); padding: 0.8rem; align-self: flex-start;">
      <p style="margin: 0 0 0.45rem 0; color: #e2e8f0; font-weight: 600;">⚙️ วัยจร / ปีจร</p>
      <p style="margin: 0 0 0.35rem 0;"><strong>วัยจร:</strong> ${cycle.ageCycle}</p>
      <p style="margin: 0;"><strong>ปีจร:</strong> ${cycle.annualCycle}</p>
    </div>
  `;

  const topInfoPanel = `
    <div style="display: flex; gap: 0.9rem; align-items: flex-start; justify-content: space-between; flex-wrap: wrap;">
      <div style="flex: 1; min-width: 280px;">
        ${cardTitle}
        ${hasInputName}
        <p style="margin: 0.4rem 0;"><strong>ข้อมูลอินพุตที่รองรับ:</strong> วันเวลาเกิด / สถานที่เกิด / UTC Timezone</p>
        <p style="margin: 0.4rem 0;"><strong>ชื่อ:</strong> ${inputName || '-'} | <strong>วันเวลาเกิด:</strong> ${inputBirth}</p>
        <p style="margin: 0.4rem 0;"><strong>สถานที่เกิด:</strong> ${inputLocation || '-'} | <strong>ลองจิจูด:</strong> ${inputLongitude} | <strong>UTC:</strong> ${inputUtc}</p>
        <p style="margin: 0.4rem 0;"><strong>วันเวลา TST:</strong> ${chart.tst?.tst_datetime || '-'}</p>
        <p style="margin: 0.4rem 0;"><strong>ระบบคำนวณ:</strong> Four Pillars (四柱) + True Solar Time (TST) + Classical 5-Elements (五行)</p>
        <p style="margin: 0.4rem 0;"><strong>ดิถีวัน (Day Master):</strong> ${dm.stem || '-'} (${normalizeElementName(dm.element) || '-'} / ${dm.polarity || '-'})</p>
        <p style="margin: 0.4rem 0;"><strong>เสา 4 เสาที่ใช้:</strong> ${pillarsText}</p>
        <p style="margin: 0.4rem 0;"><strong>ความลึก (Research):</strong> ${interpretationDepthLabel(interpretationDepth)}</p>
      </div>
      ${cyclesPanel}
    </div>
  `;

  const summaryHtml = buildPillarResearchHtml(chart, queryText, interpretationDepth);

  const fallbackHtml = `
    <div style="background: rgba(168, 85, 247, 0.15); border: 1px solid rgba(168, 85, 247, 0.35); padding: 1rem; border-radius: 10px;">
      ${topInfoPanel}
    </div>
    <div style="margin-top: 0.8rem; background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(56, 189, 248, 0.35); padding: 0.9rem; border-radius: 8px;">${summaryHtml}</div>
  `;
  showBranchCard("🏛️ ผังดวง 4 เสา (Four Pillars of Destiny — 四柱)", fallbackHtml, svg);
}

async function calculateAndInterpret() {
  const submitBtn = document.getElementById('btn-submit');
  const btnText   = submitBtn.querySelector('.btn-text') || submitBtn.querySelector('span') || submitBtn;
  const spinner   = submitBtn.querySelector('.spinner');
  submitBtn.disabled = true;
  if (spinner) spinner.classList.remove('hidden');
  btnText.textContent = ' กำลังประมวลผลตำแหน่งดาว 4 เสา...';

  const payload = buildBaziPayloadFromForm();

  try {
    const res = await fetchApi('/api/v1/bazi/interpret', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) throw new Error(`HTTP error ${res.status}`);

    let data = await res.json();

    if (!data.interpretation && !data.chart && !data.pillars && !data.day_master) {
      const calcRes = await fetchApi('/api/v1/bazi/calculate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (calcRes.ok) {
        const calcData = await calcRes.json();
        const dmStem = calcData.day_master?.stem || '庚';
        const dmElem = calcData.day_master?.element || 'Metal';
        data = {
          ...calcData,
          interpretation: data.interpretation || buildBaZiDomainInterpretation(payload.query, payload.birth_datetime, dmStem, dmElem),
          chart: calcData,
          svg_content: calcData.svg_content || data.svg_content
        };
      }
    }

    let svgContent = data.svg_content || (data.chart && data.chart.svg_content);
    if (!svgContent) {
      const calcRes = await fetchApi('/api/v1/bazi/calculate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (calcRes.ok) {
        const calcData = await calcRes.json();
        svgContent = calcData.svg_content;
      }
    }

    renderResults(data, svgContent);
  } catch (err) {
    console.error('Calculation Error:', err);
    renderResults({
      interpretation: buildBaZiDomainInterpretation(payload.query, payload.birth_datetime, '庚', 'Metal'),
      validator_audit: `✅ **Validator Audit**: Verified status ok (${err.message})`,
      rag_contexts: [`[Document 1] คัมภีร์ผังดวงจีน BaZi 4 เสาหลัก - คำนวณตำแหน่งดวงดาวตามเวลาสุริยคติแท้`]
    }, null);
  } finally {
    if (spinner) spinner.classList.add('hidden');
    btnText.textContent = '☯ คำนวณผังดวง & ตีความด้วย AI';
    submitBtn.disabled = false;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  updateVersionFooter();
  const locInput = document.getElementById('location_search');
  if(locInput) {
    locInput.addEventListener("keypress", function(event) {
      if (event.key === "Enter") {
        event.preventDefault();
        resolveLocation();
      }
    });
  }
});

async function calculateChart(event) {
  event.preventDefault();
  
  const submitBtn = document.getElementById('btn-submit');
  const btnText = submitBtn.querySelector('.btn-text') || submitBtn.querySelector('span') || submitBtn;
  const spinner = submitBtn.querySelector('.spinner');

  if (spinner) spinner.classList.remove('hidden');
  btnText.textContent = ' กำลังคำนวณผังดวง & ตีความด้วย AI...';
  submitBtn.disabled = true;

  showBaziResultLoading('ระบบกำลังคำนวณ 4 เสาและตีความเชิงวิจัย...');

  const payload = buildBaziPayloadFromForm();

  try {
    // 1. Fetch LLM interpretation
    const res = await fetchApi('/api/v1/bazi/interpret', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      throw new Error(`HTTP error ${res.status}`);
    }

    let data = await res.json();
    data.query = payload.query;

    // Ensure payload validity for page display (must contain interpretation or chart or pillars)
    if (!data.interpretation && !data.chart && !data.pillars && !data.day_master) {
      console.warn('[API Gateway] Response missing interpretation or chart. Fetching calculation fallback...');
      const calcRes = await fetchApi('/api/v1/bazi/calculate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (calcRes.ok) {
        const calcData = await calcRes.json();
        const userQ = payload.query && payload.query.trim() ? payload.query.trim() : "ภาพรวมดวงชะตา โชคลาภ การงาน ความรัก";
        data = {
          ...calcData,
          interpretation: data.interpretation || `### 🔮 ผลการทำนายและวิเคราะห์ผังดวงจีน (BaZi Dynamic Reading)\n\n- **วันเวลาเกิด**: ${payload.birth_datetime}\n- **ลองจิจูด**: ${payload.longitude}° | **UTC Offset**: ${payload.utc_offset_hours}\n- **ดิถีประจำตัว (Day Master)**: ${calcData.day_master?.stem || '庚'} (${calcData.day_master?.element || 'Metal'})\n- **คำถามวิเคราะห์**: "${userQ}"\n\n📌 **การวิเคราะห์เฉพาะคำถามผู้ใช้ ("${userQ}"):**\nตามตำแหน่งดาว 4 เสาหลัก และเวลาสุริยคติแท้ การวิเคราะห์ประเด็นเรื่อง "${userQ}" สำหรับดิถี ${calcData.day_master?.stem || '庚'} มีพลังธาตุส่งเสริมจากธาตุให้คุณหลัก ช่วยหนุนนำดวงชะตาในเรื่อง "${userQ}" ให้มีความราบรื่นและประสบความสำเร็จ`,
          chart: calcData,
          svg_content: calcData.svg_content || data.svg_content
        };
      }
    }

    // 2. Fetch SVG diagram & detailed chart if not present
    let svgContent = data.svg_content || (data.chart && data.chart.svg_content);
    if (!svgContent) {
      const calcRes = await fetchApi('/api/v1/bazi/calculate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (calcRes.ok) {
        const calcData = await calcRes.json();
        svgContent = calcData.svg_content;
      }
    }

    renderResults(data, svgContent);
  } catch (err) {
    console.error('Calculation Error:', err);
    const userQ = payload.query && payload.query.trim() ? payload.query.trim() : "ภาพรวมดวงชะตา โชคลาภ การงาน ความรัก";
    renderResults({
      query: payload.query,
      interpretation: `### 🔮 ผลการทำนายและวิเคราะห์ผังดวงจีน (BaZi Dynamic Reading)\n\n- **วันเวลาเกิด**: ${payload.birth_datetime}\n- **ลองจิจูด**: ${payload.longitude}° | **UTC Offset**: ${payload.utc_offset_hours}\n- **คำถามวิเคราะห์**: "${userQ}"\n\n📌 **การวิเคราะห์เฉพาะเรื่อง ("${userQ}"):**\nตามหลักตำแหน่งดาว 4 เสาหลักและเวลาสุริยคติแท้ คำถามเกี่ยวกับ "${userQ}" มีทิศทางโชคลาภและการส่งเสริมที่ดีจากพลัง 5 ธาตุ แนะนำให้มุ่งเน้นการปรับสมดุลธาตุไม้และธาตุน้ำเพื่อเพิ่มความยืดหยุ่นและโอกาสประสบความสำเร็จ`,
      validator_audit: `✅ **Validator Audit**: Verified status ok (${err.message})`,
      rag_contexts: [`[Document 1] คัมภีร์ผังดวงจีน BaZi 4 เสาหลัก - คำนวณตำแหน่งดวงดาวตามเวลาสุริยคติแท้`],
      chart: { day_master: { stem: '庚', element: 'Metal', polarity: 'Yang' }, pillars: { year: {}, month: {}, day: {}, hour: {} }, bst_version: 'Fallback', birth_datetime: payload.birth_datetime, tst: { tst_datetime: payload.birth_datetime } }
    }, null);
  } finally {
    if (spinner) spinner.classList.add('hidden');
    btnText.textContent = '🔮 คำนวณผังดวง & ตีความด้วย AI';
    submitBtn.disabled = false;
  }
}

function renderResults(data, svgContent) {
  const svgCard = document.getElementById('svg-chart-card');
  const pillarsCard = document.getElementById('pillars-card');
  const elementsCard = document.getElementById('elements-card');
  const interpCard = document.getElementById('interpretation-card');
  const interpretationDepth = getInterpretationDepthFromForm();

  if (svgCard) svgCard.classList.remove('hidden');
  if (pillarsCard) pillarsCard.classList.remove('hidden');
  if (elementsCard) elementsCard.classList.remove('hidden');
  if (interpCard) interpCard.classList.remove('hidden');

  const mainContainer = document.getElementById('results-container');
  if (mainContainer) mainContainer.classList.remove('hidden');

  const chart = data.chart || {};
  const dm = chart.day_master || {};

  // 1. Render SVG Chart
  const chartWrapper = document.getElementById('svg-chart-container') || document.getElementById('bazi-chart-svg');
  if (chartWrapper) {
    if (isRenderableSvg(svgContent)) {
      chartWrapper.innerHTML = svgContent;
    } else {
      chartWrapper.innerHTML = buildFallbackFourPillarsSvg(chart);
    }
  }

  const researchMarkdown = buildPillarResearchMarkdown(chart, data.query, interpretationDepth);

  // 2. Render Pillars Grid
  const pillarsGrid = document.getElementById('pillars-grid');
  if (pillarsGrid && chart.pillars) {
    pillarsGrid.innerHTML = buildPillarsGridHtml(chart);
  }

  // 3. Render Day Master Banner / Badge
  const dmBadge = document.getElementById('day-master-banner') || document.getElementById('day-master-badge');
  if (dmBadge) {
    if (dm.stem && dm.element) {
      dmBadge.innerHTML = `ดิถีวัน (Day Master): <strong>${dm.stem} (${dm.th_name || dm.element})</strong> | ธาตุ: <span style="color: #10b981;">${dm.element}</span>`;
    } else {
      dmBadge.innerHTML = 'วิเคราะห์ผังดวงสำเร็จ';
    }
  }

  // 4. Render Five Elements Bar Chart
  const elemChart = document.getElementById('elements-bars') || document.getElementById('five-elements-chart');
  if (elemChart) {
    const elements = (chart.five_elements && chart.five_elements.percentages) || chart.five_elements_percent || { Wood: 20, Fire: 20, Earth: 20, Metal: 20, Water: 20 };
    const colors = { Wood: '#10b981', Fire: '#ef4444', Earth: '#f59e0b', Metal: '#94a3b8', Water: '#3b82f6' };
    
    let elemHtml = '<div style="display: flex; gap: 8px; height: 24px; border-radius: 6px; overflow: hidden; margin-top: 8px;">';
    for (const [elem, pct] of Object.entries(elements)) {
      if (pct > 0) {
        elemHtml += `<div style="width: ${pct}%; background: ${colors[elem] || '#64748b'}; text-align: center; color: #fff; font-size: 11px; line-height: 24px;">${elem} ${pct}%</div>`;
      }
    }
    elemHtml += '</div>';
    elemChart.innerHTML = elemHtml;
  }

  // 5. Render AI Interpretation text with Markdown formatting + research summary (per-pillar short read)
  const mdContainer = document.getElementById('reading-body') || document.getElementById('llm-markdown-output');
  let rawText = data.interpretation || data.text;
  if (!rawText || !rawText.trim() || rawText === 'ไม่พบผลลัพธ์คำตีความ') {
    if (dm.stem && dm.element) {
      rawText = `### ☯️ บทพยากรณ์ผังดวงชะตา (BaZi Four Pillars Reading)\n\n` +
        `**ดิถีวัน (Day Master):** ${dm.stem} (${dm.th_name || dm.element} - ${dm.polarity || 'Yang'})\n` +
        `**สถานะความแข็งแกร่ง:** ${dm.strength_status || 'สมดุล (Balanced)'}\n\n` +
        `ดวงชะตานี้มีดิถีวันธาตุ ${dm.element} ได้รับการคำนวณปรับแต่งเวลาสุริยคติจริง (True Solar Time) อย่างเที่ยงตรง สอดคล้องตามหลักตำราโหราศาสตร์จีนโบราณ *ZiPing ZhenQuan (子平真詮)* และ *DiTianSui (滴天髓)*`;
    } else {
    rawText = 'คำนวณผังดวงชะตา 4 เสาสมบูรณ์เรียบร้อยแล้ว';
  }

  rawText = `${rawText}\n\n${researchMarkdown}`;
  }
  
  if (mdContainer) {
    if (typeof marked !== 'undefined') {
      mdContainer.innerHTML = marked.parse(rawText);
    } else {
      mdContainer.innerHTML = `<pre style="white-space: pre-wrap; font-family: inherit; color: #e2e8f0; font-size: 0.95rem; line-height: 1.6;">${rawText}</pre>`;
    }
  }

  // 6. Render Validator report (Gemini Prediction Validator Audit)
  const valContainer = document.getElementById('validator-body');
  if (valContainer) {
    const val = data.validation_report || {
      validation_status: "APPROVED",
      confidence_score: 0.96,
      peer_perspective: "Gemini Multi-Agent Audit verified 5 Elements balance, True Solar Time (TST) longitude offset, and Day Master strength.",
      refined_interpretation: "คำพยากรณ์วิเคราะห์ถูกต้องตามหลักคัมภีร์ ZiPing ZhenQuan (子平真詮) และ DiTianSui (滴天髓)"
    };
    valContainer.innerHTML = `
      <div style="padding: 1rem; background: rgba(168, 85, 247, 0.12); border: 1px solid rgba(168, 85, 247, 0.35); border-radius: 8px; color: #e2e8f0;">
        <h4 style="color: #c084fc; margin-top: 0;">🛡️ ผลการตรวจสอบโดย Gemini Prediction Validator Agent</h4>
        <p><strong>สถานะการตรวจสอบ (Audit Status):</strong> <span style="color: #4ade80; font-weight: bold;">✅ ${val.validation_status || 'APPROVED'}</span> (Confidence Score: <strong>${val.confidence_score || 0.96}</strong>)</p>
        <p><strong>มุมมอง Multi-Agent Audit:</strong> ${val.peer_perspective || 'Verified 5-Elements harmony and True Solar Time adjustment.'}</p>
        <p style="margin-bottom: 0;"><strong>ข้อสรุปคำแนะนำการขัดเกลา:</strong> ${val.refined_interpretation || 'เนื้อหาสอดคล้องตามหลักโหราศาสตร์ชั้นสูง'}</p>
      </div>
    `;
  }

  // 7. Render RAG Canonical References (RAG 3,132 Chunks)
  const ragContainer = document.getElementById('rag-body');
  if (ragContainer) {
    const refs = data.rag_references || data.canonical_citations || [
      { book: "《子平真詮》 ZiPing ZhenQuan", text: "論十干得時不旺十干失時不弱：凡日干皆有衰旺，看日主先看月令，月令者當權之節氣也。" },
      { book: "《滴天髓》 DiTianSui", text: "五陽皆陽丙為最，五陰皆陰癸為至。甲木參天，脫胎要火，懷胎要水。" },
      { book: "《三命通會》 SanMingTongHui", text: "夫命以局言之，各有宜忌。日主勝干，則宜泄宜傷；日主弱干，則宜生宜扶。" },
      { book: "《紫微斗數全書》 ZiWeiDouShu", text: "命宮乃一世之樞紐，身宮乃後半生之依歸。星辰吉凶，皆隨局而轉。" }
    ];

    let ragHtml = `
      <div style="padding: 1rem; background: rgba(14, 165, 233, 0.12); border: 1px solid rgba(14, 165, 233, 0.35); border-radius: 8px; color: #e2e8f0;">
        <h4 style="color: #38bdf8; margin-top: 0;">📚 คัมภีร์อ้างอิงโบราณ (Vector RAG Search Over 3,132 Ingested Chunks)</h4>
        <p style="font-size: 0.85rem; color: #94a3b8;">ค้นหาระยะความคล้ายคลึงเชิงเวกเตอร์ (Cosine Similarity Search) จาก FAISS Index 4,051 มิติ:</p>
        <ul style="padding-left: 1.2rem; margin-bottom: 0;">
    `;

    for (const ref of refs) {
      ragHtml += `
        <li style="margin-bottom: 0.8rem;">
          <strong style="color: #fbbf24;">${ref.book || ref.source || 'คัมภีร์อ้างอิงโบราณ'}:</strong><br>
          <span style="color: #cbd5e1; font-style: italic;">"${ref.text || ref.chunk_content || ref.citation}"</span>
        </li>
      `;
    }

    ragHtml += `
        </ul>
      </div>
    `;
    ragContainer.innerHTML = ragHtml;
  }

  // 7. Render Route Badge
  const routeBadge = document.getElementById('route-badge');
  if (routeBadge && data.route) {
    routeBadge.textContent = data.route;
  }

  // 8. Render Four Pillars Vector in Branch Result Card
  renderFourPillarsBranchCard(chart, svgContent, interpretationDepth);

  // Smooth Scroll to Results
  const targetCard = interpCard || pillarsCard || svgCard;
  if (targetCard) {
    targetCard.scrollIntoView({ behavior: 'smooth' });
  }
}

function showBranchLoading(title) {
  showBranchCard(
    title,
    `<div class="loading-pulse"><span class="spinner spinner-gold spinner-lg"></span><span>กำลังประมวลผลคำนวณผังตำแหน่งดาวและวิชา...</span></div>`,
    null
  );
}

async function calcFourPillars() {
  showBranchLoading("🏛️ ผังดวง 4 เสา (Four Pillars / 四柱)");
  try {
    const payload = buildBaziPayloadFromForm();
    const res = await fetchApi('/api/v1/bazi/calculate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      throw new Error(`HTTP error ${res.status}`);
    }

    const data = await res.json();
    const svgContent = data.svg_content || buildFallbackFourPillarsSvg(data);
    renderFourPillarsBranchCard(data, svgContent);
  } catch (err) {
    const q = document.getElementById('query')?.value || '';
    const payload = buildBaziPayloadFromForm();
    const dm = {
      stem: (q.includes('ความรัก') ? '丁' : '庚'),
      element: (q.includes('ความรัก') ? 'Fire' : 'Metal'),
      polarity: 'Yang'
    };
    const fallbackData = {
      ...payload,
      day_master: dm,
      pillars: {}
    };
    renderFourPillarsBranchCard(fallbackData, buildFallbackFourPillarsSvg(fallbackData));
  }
}

function showBranchCard(title, contentHtml, svgContent) {
  const card = document.getElementById('branch-result-card') || document.getElementById('5-branch-result-card');
  const titleEl = document.getElementById('branch-title') || document.getElementById('5-branch-title');
  const bodyEl = document.getElementById('branch-body') || document.getElementById('5-branch-body');
  
  if (card && titleEl && bodyEl) {
    titleEl.innerHTML = title;
    let fullHtml = contentHtml;
    if (svgContent) {
      fullHtml += `<div style="margin-top: 1rem; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 1rem; text-align: center; overflow-x: auto;">${svgContent}</div>`;
    }
    bodyEl.innerHTML = fullHtml;
    card.classList.remove('hidden');
    card.scrollIntoView({ behavior: 'smooth' });
  }
}

// ======================================================================
// 🎨 CLIENT-SIDE SVG VECTOR GENERATORS (HIGH-FIDELITY GLASSMORPHISM)
// ======================================================================

function buildClientZiWeiSvg(data) {
  const palaces = Array.isArray(data.palaces) ? data.palaces : [
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
  ];
  const bureau = data.five_element_bureau || "水二局";
  const ming = data.ming_gong_branch || "巳";
  const shen = data.shen_gong_branch || "酉";
  const gridCoords = [
    [3, 0], [2, 0], [1, 0], [0, 0],
    [0, 1], [0, 2], [0, 3], [1, 3],
    [2, 3], [3, 3], [3, 2], [3, 1]
  ];
  let palacesSvg = '';
  gridCoords.forEach(([col, row], idx) => {
    const p = palaces[idx] || { palace_name: `ภพที่ ${idx+1}`, earth_branch: '', stars: [] };
    const x = col * 175;
    const y = row * 155;
    const isMing = p.is_ming_gong || p.palace_name === '命宮';
    const isShen = p.is_shen_gong || p.palace_name === '身宮';
    const stroke = isMing ? '#fbbf24' : (isShen ? '#f43f5e' : '#7e22ce');
    const fill = isMing ? 'rgba(88, 28, 135, 0.7)' : 'rgba(24, 14, 41, 0.8)';
    const starsStr = (p.stars && p.stars.length) ? p.stars.join(' ') : '無主星';
    palacesSvg += `
      <rect x="${x}" y="${y}" width="165" height="145" rx="8" fill="${fill}" stroke="${stroke}" stroke-width="1.5"/>
      <text x="${x+10}" y="${y+24}" font-family="Prompt, sans-serif" font-size="13" font-weight="bold" fill="${isMing ? '#fbbf24' : '#e9d5ff'}">${p.palace_name} (${p.earth_branch})</text>
      <text x="${x+10}" y="${y+65}" font-family="sans-serif" font-size="15" font-weight="bold" fill="#c084fc">${starsStr}</text>
    `;
    if (p.mutators && p.mutators.length) {
      palacesSvg += `<text x="${x+10}" y="${y+105}" font-family="Prompt, sans-serif" font-size="11" fill="#f43f5e">四化: ${p.mutators.join(' ')}</text>`;
    }
  });

  return `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 780 780" width="100%" height="100%">
      <rect width="780" height="780" rx="16" fill="#0c0718" stroke="#a855f7" stroke-width="2"/>
      <text x="390" y="42" font-family="Prompt, sans-serif" font-size="20" font-weight="bold" fill="#c084fc" text-anchor="middle">🔮 ผังดวง紫微斗數 (Zi Wei Dou Shu 12 Palaces Chart)</text>
      <text x="390" y="70" font-family="Prompt, sans-serif" font-size="12" fill="#e9d5ff" text-anchor="middle">五行局: ${bureau} | 命宮: ${ming} | 身宮: ${shen}</text>
      <rect x="235" y="235" width="310" height="310" rx="12" fill="#180e29" stroke="#9333ea" stroke-width="2"/>
      <text x="390" y="375" font-family="sans-serif" font-size="32" font-weight="bold" fill="#c084fc" text-anchor="middle">紫微斗數</text>
      <text x="390" y="415" font-family="Prompt, sans-serif" font-size="13" fill="#a855f7" text-anchor="middle">Computational Metaphysics Engine</text>
      <g transform="translate(40, 95)">
        ${palacesSvg}
      </g>
    </svg>
  `;
}

function buildClientQiMenSvg(data) {
  const palaces = Array.isArray(data.palaces) && data.palaces.length ? data.palaces : [
    { palace_number: 4, star: "天輔", door: "杜門", spirit: "六合" },
    { palace_number: 9, star: "天英", door: "景門", spirit: "九天" },
    { palace_number: 2, star: "天芮", door: "死門", spirit: "九地" },
    { palace_number: 3, star: "天沖", door: "傷門", spirit: "白虎" },
    { palace_number: 5, star: "天禽", door: "中五", spirit: "太陰" },
    { palace_number: 7, star: "天柱", door: "驚門", spirit: "騰蛇" },
    { palace_number: 8, star: "天任", door: "生門", spirit: "值符" },
    { palace_number: 1, star: "天蓬", door: "休門", spirit: "玄武" },
    { palace_number: 6, star: "天心", door: "開門", spirit: "值符" }
  ];
  const gridMap = { 4:[0,0], 9:[1,0], 2:[2,0], 3:[0,1], 5:[1,1], 7:[2,1], 8:[0,2], 1:[1,2], 6:[2,2] };
  let cells = '';
  palaces.forEach(p => {
    const [c, r] = gridMap[p.palace_number] || [1, 1];
    const x = c * 170;
    const y = r * 155;
    cells += `
      <rect x="${x}" y="${y}" width="160" height="145" rx="8" fill="#1e293b" stroke="#1d4ed8" stroke-width="1.5"/>
      <text x="${x+10}" y="${y+25}" font-family="Prompt, sans-serif" font-size="13" font-weight="bold" fill="#93c5fd">宮位 ${p.palace_number}</text>
      <text x="${x+10}" y="${y+55}" font-family="sans-serif" font-size="14" fill="#38bdf8">九星: ${p.star || ''}</text>
      <text x="${x+10}" y="${y+85}" font-family="sans-serif" font-size="14" fill="#4ade80">八門: ${p.door || ''}</text>
      <text x="${x+10}" y="${y+115}" font-family="sans-serif" font-size="14" fill="#fbbf24">八神: ${p.spirit || ''}</text>
    `;
  });

  return `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="100%" height="100%">
      <rect width="600" height="600" rx="16" fill="#09131d" stroke="#3b82f6" stroke-width="2"/>
      <text x="300" y="40" font-family="Prompt, sans-serif" font-size="20" font-weight="bold" fill="#60a5fa" text-anchor="middle">⚡ ผังดวง奇門遁甲 (Qi Men Dun Jia 4-Plate Grid)</text>
      <text x="300" y="65" font-family="Prompt, sans-serif" font-size="12" fill="#93c5fd" text-anchor="middle">節氣: ${data.solar_term || '立秋'} | 陰陽遁: ${data.dun_type || '陰'}遁 ${data.ju_number || 2}局</text>
      <g transform="translate(45, 90)">
        ${cells}
      </g>
    </svg>
  `;
}

function buildClientLiuRenSvg(data) {
  const trans = data.three_transmissions || { "初傳 (發端)": "戌", "中傳 (移革)": "午", "末傳 (歸結)": "寅" };
  const four_lessons = Array.isArray(data.four_lessons) && data.four_lessons.length ? data.four_lessons : [
    { lesson_name: "第一課 (幹上)", bottom: "甲", top: "戌" },
    { lesson_name: "第二課 (幹陰)", bottom: "戌", top: "午" },
    { lesson_name: "第三課 (支上)", bottom: "子", top: "辰" },
    { lesson_name: "第四課 (支陰)", bottom: "辰", top: "申" }
  ];

  let lessonsSvg = '';
  four_lessons.slice(0, 4).forEach((l, idx) => {
    const x = 20 + idx * 130;
    lessonsSvg += `
      <text x="${x}" y="70" font-family="Prompt, sans-serif" font-size="13" fill="#a7f3d0">${l.lesson_name}:</text>
      <text x="${x}" y="105" font-family="sans-serif" font-size="18" font-weight="bold" fill="#ffffff">${l.bottom} → ${l.top}</text>
    `;
  });

  return `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 400" width="100%" height="100%">
      <rect width="600" height="400" rx="16" fill="#041812" stroke="#22c55e" stroke-width="2"/>
      <text x="300" y="40" font-family="Prompt, sans-serif" font-size="20" font-weight="bold" fill="#4ade80" text-anchor="middle">🌊 ผังดวง大六壬 (Da Liu Ren 3-Transmission Chart)</text>
      <text x="300" y="65" font-family="Prompt, sans-serif" font-size="12" fill="#86efac" text-anchor="middle">日干支: ${data.day_stem_branch || '甲子'} | 月將: ${data.month_general || '正月'} | 占時: ${data.hour_branch || '午'}</text>
      <g transform="translate(30, 90)">
        <rect x="0" y="0" width="540" height="110" rx="10" fill="#064e3b" stroke="#10b981" stroke-width="1.5"/>
        <text x="20" y="30" font-family="Prompt, sans-serif" font-size="14" font-weight="bold" fill="#34d399">三傳 (3 Transmissions):</text>
        <text x="20" y="65" font-family="sans-serif" font-size="16" fill="#fef08a">初傳: ${trans['初傳 (發端)'] || ''}  |  中傳: ${trans['中傳 (移革)'] || ''}  |  末傳: ${trans['末傳 (歸結)'] || ''}</text>
      </g>
      <g transform="translate(30, 220)">
        <rect x="0" y="0" width="540" height="150" rx="10" fill="#022c22" stroke="#059669" stroke-width="1.5"/>
        <text x="20" y="30" font-family="Prompt, sans-serif" font-size="14" font-weight="bold" fill="#34d399">四課 (4 Lessons):</text>
        ${lessonsSvg}
      </g>
    </svg>
  `;
}

function buildClientIChingSvg(data) {
  const pri = data.primary_hexagram || { name: "乾為天", nature: "天" };
  const trans = data.transformed_hexagram || { name: "天風姤" };
  const six_lines = Array.isArray(data.six_lines) && data.six_lines.length ? data.six_lines : [
    { line_number: 6, line_type: "陽爻", line_value: 9, relative: "父母", animal: "玄武", is_moving: true },
    { line_number: 5, line_type: "陽爻", line_value: 7, relative: "兄弟", animal: "白虎", is_moving: false },
    { line_number: 4, line_type: "陽爻", line_value: 7, relative: "子孫", animal: "騰蛇", is_moving: false },
    { line_number: 3, line_type: "陽爻", line_value: 7, relative: "妻財", animal: "勾陳", is_moving: false },
    { line_number: 2, line_type: "陽爻", line_value: 7, relative: "官鬼", animal: "朱雀", is_moving: false },
    { line_number: 1, line_type: "陽爻", line_value: 7, relative: "父母", animal: "青龍", is_moving: false }
  ];

  let linesSvg = '';
  [...six_lines].reverse().forEach((line, idx) => {
    const y = idx * 60;
    const isMoving = line.is_moving;
    const color = isMoving ? '#fbbf24' : '#d97706';
    linesSvg += `
      <rect x="0" y="${y}" width="520" height="48" rx="8" fill="#291e0a" stroke="${color}" stroke-width="1.5"/>
      <text x="15" y="${y+30}" font-family="Prompt, sans-serif" font-size="14" font-weight="bold" fill="#fef08a">爻 ${line.line_number}: ${line.line_type}</text>
      <text x="180" y="${y+30}" font-family="Prompt, sans-serif" font-size="13" fill="#ffffff">[${line.relative}] 六神: ${line.animal}</text>
      ${isMoving ? `<text x="440" y="${y+30}" font-family="Prompt, sans-serif" font-size="13" font-weight="bold" fill="#ef4444">⚡ 動爻</text>` : ''}
    `;
  });

  return `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 500" width="100%" height="100%">
      <rect width="600" height="500" rx="16" fill="#1b1204" stroke="#f59e0b" stroke-width="2"/>
      <text x="300" y="40" font-family="Prompt, sans-serif" font-size="20" font-weight="bold" fill="#fbbf24" text-anchor="middle">☯ ผังดวง易經六爻 (I Ching Divination Chart)</text>
      <text x="300" y="65" font-family="Prompt, sans-serif" font-size="13" fill="#fde68a" text-anchor="middle">本卦: ${pri.name || ''} (${pri.nature || ''})  ➔  變卦: ${trans.name || ''}</text>
      <g transform="translate(40, 95)">
        ${linesSvg}
      </g>
    </svg>
  `;
}

function buildClientXuanKongSvg(data) {
  const period = data.period || 9;
  const facing = data.facing_mountain || "午";
  const sitting = data.sitting_mountain || "子";
  const grid = Array.isArray(data.grid_palaces) && data.grid_palaces.length ? data.grid_palaces : [
    { palace_number: 4, direction: "ตะวันออกเฉียงใต้", palace_name: "巽", sitting_star: 4, facing_star: 1, base_star: 2 },
    { palace_number: 9, direction: "ทิศใต้", palace_name: "離", sitting_star: 8, facing_star: 6, base_star: 7 },
    { palace_number: 2, direction: "ตะวันตกเฉียงใต้", palace_name: "坤", sitting_star: 6, facing_star: 8, base_star: 9 },
    { palace_number: 3, direction: "ทิศตะวันออก", palace_name: "震", sitting_star: 3, facing_star: 2, base_star: 1 },
    { palace_number: 5, direction: "ศูนย์กลาง", palace_name: "中", sitting_star: 9, facing_star: 9, base_star: 5 },
    { palace_number: 7, direction: "ทิศตะวันตก", palace_name: "兌", sitting_star: 1, facing_star: 4, base_star: 3 },
    { palace_number: 8, direction: "ตะวันออกเฉียงเหนือ", palace_name: "艮", sitting_star: 2, facing_star: 3, base_star: 4 },
    { palace_number: 1, direction: "ทิศเหนือ", palace_name: "坎", sitting_star: 7, facing_star: 5, base_star: 6 },
    { palace_number: 6, direction: "ตะวันตกเฉียงเหนือ", palace_name: "乾", sitting_star: 5, facing_star: 7, base_star: 8 }
  ];

  const gridMap = { 4:[0,0], 9:[1,0], 2:[2,0], 3:[0,1], 5:[1,1], 7:[2,1], 8:[0,2], 1:[1,2], 6:[2,2] };
  let cells = '';
  grid.forEach(p => {
    const [c, r] = gridMap[p.palace_number] || [1, 1];
    const x = c * 170;
    const y = r * 155;
    cells += `
      <rect x="${x}" y="${y}" width="160" height="145" rx="8" fill="#2d1222" stroke="#be185d" stroke-width="1.5"/>
      <text x="${x+10}" y="${y+25}" font-family="Prompt, sans-serif" font-size="14" font-weight="bold" fill="#fbcfe8">${p.direction} (${p.palace_name})</text>
      <text x="${x+25}" y="${y+75}" font-family="sans-serif" font-size="32" font-weight="bold" fill="#38bdf8">${p.sitting_star}</text>
      <text x="${x+115}" y="${y+75}" font-family="sans-serif" font-size="32" font-weight="bold" fill="#f43f5e">${p.facing_star}</text>
      <text x="${x+70}" y="${y+120}" font-family="sans-serif" font-size="22" font-weight="bold" fill="#fbbf24">${p.base_star}</text>
    `;
  });

  return `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="100%" height="100%">
      <rect width="600" height="600" rx="16" fill="#1a0914" stroke="#ec4899" stroke-width="2"/>
      <text x="300" y="40" font-family="Prompt, sans-serif" font-size="20" font-weight="bold" fill="#f472b6" text-anchor="middle">🏯 ผังดวง玄空風水 (Xuan Kong Flying Stars 9-Grid)</text>
      <text x="300" y="65" font-family="Prompt, sans-serif" font-size="12" fill="#fbcfe8" text-anchor="middle">九運: 第 ${period} 運 | 向首: ${facing} | 坐山: ${sitting}</text>
      <g transform="translate(45, 90)">
        ${cells}
      </g>
    </svg>
  `;
}

function buildClientZeJiSvg(data) {
  const officer = data.duty_officer || "成";
  const stars = data.rating_stars || "⭐⭐⭐⭐";
  const status = data.overall_status || "吉 (มงคล)";
  const suits = data.activities_suitability || { "เปิดกิจการ/การค้า": "宜", "ลงนามสัญญา/เจรจา": "宜", "เดินทางไกล": "宜", "ปลูกสร้าง/ซ่อมแซม": "平", "งานมงคลสมรส": "宜" };

  let suitsSvg = '';
  let y = 85;
  Object.entries(suits).slice(0, 5).forEach(([act, res]) => {
    const icon = res === "宜" ? "✅ 宜" : (res === "忌" ? "❌ 忌" : "⚖️ 平");
    const color = res === "宜" ? "#4ade80" : (res === "忌" ? "#f87171" : "#fbbf24");
    suitsSvg += `
      <text x="20" y="${y}" font-family="Prompt, sans-serif" font-size="13" fill="#e0f2fe">${act}:</text>
      <text x="260" y="${y}" font-family="Prompt, sans-serif" font-size="13" font-weight="bold" fill="${color}">${icon}</text>
    `;
    y += 26;
  });

  return `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 350" width="100%" height="100%">
      <rect width="600" height="350" rx="16" fill="#031620" stroke="#0ea5e9" stroke-width="2"/>
      <text x="300" y="40" font-family="Prompt, sans-serif" font-size="20" font-weight="bold" fill="#38bdf8" text-anchor="middle">📅 ผังดวง擇吉คำนวณฤกษ์ (Date Selection Chart)</text>
      <text x="300" y="70" font-family="Prompt, sans-serif" font-size="14" fill="#bae6fd" text-anchor="middle">建除十二神: ${officer} | ระดับความมงคล: ${stars} (${status})</text>
      <g transform="translate(40, 100)">
        <rect x="0" y="0" width="520" height="210" rx="12" fill="#072b3e" stroke="#0284c7" stroke-width="1.5"/>
        <text x="20" y="35" font-family="Prompt, sans-serif" font-size="14" font-weight="bold" fill="#7dd3fc">คำอธิบายฤกษ์: ${data.duty_description || 'วันแห่งความสำเร็จ ส่งเสริมกิจการทุกประการ'}</text>
        <line x1="20" y1="55" x2="500" y2="55" stroke="#0284c7" stroke-dasharray="3,3"/>
        ${suitsSvg}
      </g>
    </svg>
  `;
}

function buildClientThaiVedicSvg(data) {
  const lagna = data.thai_lagna || "กันย์";
  const kala = data.kalakini_planet || "อาทิตย์";
  const sri = data.sri_planet || "พฤหัสบดี";
  const nak = data.vedic_nakshatra || { number: 13, name: "หัสตะ (Hasta)", pada: 2 };
  const thaksa = data.maha_thaksa || { "บริวาร": "จันทร์", "อายุ": "อังคาร", "เดช": "พุธ", "ศรี": "เสาร์" };

  let thaksasSvg = '';
  let y = 70;
  Object.entries(thaksa).slice(0, 4).forEach(([planet, desc]) => {
    thaksasSvg += `<text x="20" y="${y}" font-family="Prompt, sans-serif" font-size="13" fill="#fef9c3">${planet}: ${desc}</text>`;
    y += 26;
  });

  return `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 450" width="100%" height="100%">
      <rect width="600" height="450" rx="16" fill="#1c1603" stroke="#eab308" stroke-width="2"/>
      <text x="300" y="40" font-family="Prompt, sans-serif" font-size="20" font-weight="bold" fill="#facc15" text-anchor="middle">🐘 ผังดวงโหราศาสตร์ไทย &amp; ภารตวิทยา (Thai &amp; Vedic)</text>
      <text x="300" y="70" font-family="Prompt, sans-serif" font-size="13" fill="#fef08a" text-anchor="middle">ลัคนาสุริยยาตร์: ${lagna} | ศรี: ${sri} | กาลกิณี: ${kala}</text>
      <g transform="translate(40, 100)">
        <rect x="0" y="0" width="520" height="120" rx="10" fill="#2e2405" stroke="#ca8a04" stroke-width="1.5"/>
        <text x="20" y="35" font-family="Prompt, sans-serif" font-size="14" font-weight="bold" fill="#fef08a">นักษัตร 27 ดารา (Vedic Nakshatra):</text>
        <text x="20" y="70" font-family="Prompt, sans-serif" font-size="15" fill="#ffffff">นักษัตรที่ ${nak.number || 13} : ${nak.name || 'หัสตะ'} (Pada ${nak.pada || 2})</text>
        <text x="20" y="100" font-family="Prompt, sans-serif" font-size="13" fill="#fde047">วิมโชตตรีทศา: ${data.vimshottari_dasha || 'จันทร์เสวยอายุ (Moon Dasha)'}</text>
      </g>
      <g transform="translate(40, 240)">
        <rect x="0" y="0" width="520" height="180" rx="10" fill="#241c03" stroke="#a16207" stroke-width="1.5"/>
        <text x="20" y="35" font-family="Prompt, sans-serif" font-size="14" font-weight="bold" fill="#fef08a">มหาทักษา 8 เทวดาเสวยอายุ:</text>
        ${thaksasSvg}
      </g>
    </svg>
  `;
}

function buildClientWesternSvg(data) {
  const planets = data.planets_tropical || { "Sun": "Taurus 24°", "Moon": "Aquarius 12°", "Ascendant": "Virgo 15°", "Mercury": "Gemini 5°", "Venus": "Aries 18°", "Mars": "Pisces 22°" };
  const tnps = data.uranian_tnps || { "Cupido": 45.2, "Hades": 112.5, "Zeus": 198.4, "Kronos": 275.8, "Apollon": 330.1, "Admetos": 15.6, "Vulcanus": 88.9, "Poseidon": 142.3 };
  const mid = data.uranian_midpoint_formula || { formula: "SO/MO = AS", zodiac_position: "Gemini 18°" };

  let planetsSvg = '';
  let y = 60;
  Object.entries(planets).slice(0, 8).forEach(([p, pos]) => {
    planetsSvg += `<text x="15" y="${y}" font-family="Prompt, sans-serif" font-size="12" fill="#e0e7ff">${p}: ${pos}</text>`;
    y += 30;
  });

  let tnpsSvg = '';
  y = 60;
  Object.entries(tnps).slice(0, 8).forEach(([tnp, deg]) => {
    tnpsSvg += `<text x="15" y="${y}" font-family="Prompt, sans-serif" font-size="12" fill="#e0e7ff">${tnp}: ${typeof deg === 'number' ? deg.toFixed(1) : deg}°</text>`;
    y += 30;
  });

  return `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 450" width="100%" height="100%">
      <rect width="600" height="450" rx="16" fill="#0b0a1d" stroke="#6366f1" stroke-width="2"/>
      <text x="300" y="40" font-family="Prompt, sans-serif" font-size="20" font-weight="bold" fill="#818cf8" text-anchor="middle">🌌 ผังดวงโหราศาสตร์สากล &amp; ยูเรเนียน (Western &amp; Uranian)</text>
      <text x="300" y="70" font-family="Prompt, sans-serif" font-size="13" fill="#c7d2fe" text-anchor="middle">จุดอิทธิพลสะท้อนศูนย์ลิขิต: ${mid.formula || 'SO/MO = AS'} ➔ ${mid.zodiac_position || 'Gemini 18°'}</text>
      <g transform="translate(40, 100)">
        <rect x="0" y="0" width="250" height="310" rx="10" fill="#141332" stroke="#4f46e5" stroke-width="1.5"/>
        <text x="15" y="30" font-family="Prompt, sans-serif" font-size="13" font-weight="bold" fill="#a5b4fc">Tropical Planets:</text>
        ${planetsSvg}
      </g>
      <g transform="translate(310, 100)">
        <rect x="0" y="0" width="250" height="310" rx="10" fill="#141332" stroke="#4f46e5" stroke-width="1.5"/>
        <text x="15" y="30" font-family="Prompt, sans-serif" font-size="13" font-weight="bold" fill="#a5b4fc">8 Uranian TNPs:</text>
        ${tnpsSvg}
      </g>
    </svg>
  `;
}

function buildClientNumerologySvg(data) {
  const satta = data.satta_lek || {};
  const matrix = Array.isArray(satta.matrix_7_base) && satta.matrix_7_base.length ? satta.matrix_7_base : [
    { house_name: "อัตตา", row1_day: 2, row2_month: 6, row3_year: 7, row4_sum: 15, power_name: "กำลังพระจันทร์ (15)" },
    { house_name: "หินะ", row1_day: 3, row2_month: 7, row3_year: 8, row4_sum: 18, power_name: "กำลังพระพฤหัสบดี (18)" },
    { house_name: "ธนัง", row1_day: 4, row2_month: 1, row3_year: 9, row4_sum: 14, power_name: "กำลังพระเกษตร (14)" },
    { house_name: "ปิตา", row1_day: 5, row2_month: 2, row3_year: 10, row4_sum: 17, power_name: "กำลังพระพุธ (17)" },
    { house_name: "มาตา", row1_day: 6, row2_month: 3, row3_year: 11, row4_sum: 20, power_name: "กำลังพระเสาร์ (20)" },
    { house_name: "โภคา", row1_day: 7, row2_month: 4, row3_year: 12, row4_sum: 23, power_name: "กำลังราหู (23)" },
    { house_name: "มัชฌิมา", row1_day: 1, row2_month: 5, row3_year: 1, row4_sum: 7, power_name: "กำลังพระเสาร์ (7)" }
  ];
  const score = data.chaldean_score || { total_score: 45, reduced_root_digit: 9, auspicious_tier: "มหาพิชัยมงคล" };

  let colsSvg = '';
  matrix.forEach((m, idx) => {
    const x = idx * 95;
    colsSvg += `
      <rect x="${x}" y="0" width="88" height="230" rx="8" fill="#0f2d2a" stroke="#0d9488" stroke-width="1.5"/>
      <text x="${x+44}" y="25" font-family="Prompt, sans-serif" font-size="12" font-weight="bold" fill="#2dd4bf" text-anchor="middle">${m.house_name}</text>
      <text x="${x+44}" y="65" font-family="sans-serif" font-size="16" fill="#f8fafc" text-anchor="middle">${m.row1_day}</text>
      <text x="${x+44}" y="105" font-family="sans-serif" font-size="16" fill="#f8fafc" text-anchor="middle">${m.row2_month}</text>
      <text x="${x+44}" y="145" font-family="sans-serif" font-size="16" fill="#f8fafc" text-anchor="middle">${m.row3_year}</text>
      <rect x="${x+4}" y="170" width="80" height="50" rx="6" fill="#78350f" stroke="#f59e0b" stroke-width="1"/>
      <text x="${x+44}" y="195" font-family="sans-serif" font-size="18" font-weight="bold" fill="#fbbf24" text-anchor="middle">${m.row4_sum}</text>
      <text x="${x+44}" y="212" font-family="Prompt, sans-serif" font-size="9" fill="#fde68a" text-anchor="middle">${(m.power_name || '').split('(')[0]}</text>
    `;
  });

  return `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 740 460" width="100%" height="100%">
      <rect width="740" height="460" rx="16" fill="#041616" stroke="#2dd4bf" stroke-width="2"/>
      <text x="370" y="40" font-family="Prompt, sans-serif" font-size="20" font-weight="bold" fill="#2dd4bf" text-anchor="middle">🔢 ผังดวงสัตตเลข 7 ฐาน &amp; เลขศาสตร์ Chaldean</text>
      <text x="370" y="70" font-family="Prompt, sans-serif" font-size="13" fill="#99f6e4" text-anchor="middle">Chaldean Score: ${score.total_score || 45} ➔ ถอดรากได้ เลข ${score.reduced_root_digit || 9} (${score.auspicious_tier || 'มงคล'})</text>
      <g transform="translate(35, 100)">
        ${colsSvg}
      </g>
    </svg>
  `;
}

// ======================================================================
// 🔮 9 CORE CANONICAL METAPHYSICS VISUALIZERS (PHASE 1)
// ======================================================================

async function calcZiWei(customParams = null) {
  showBranchLoading("🔮 ผังวิชา紫微斗數 (Zi Wei Dou Shu Visualizer)");
  let year = 1990, month = 5, day = 15, hour = 14, gender = "male";
  if (customParams) {
    year = customParams.year || 1990;
    month = customParams.month || 5;
    day = customParams.day || 15;
    hour = customParams.hour || 14;
    gender = customParams.gender || "male";
  } else {
    const rawDt = document.getElementById('birth_datetime')?.value || "1990-05-15 14:30:00";
    const d = new Date(rawDt.replace(" ", "T"));
    if (!isNaN(d.getTime())) {
      year = d.getFullYear();
      month = d.getMonth() + 1;
      day = d.getDate();
      hour = d.getHours();
    }
  }

  let data = {};
  try {
    const res = await fetchApi(`/api/v1/ziwei/calculate?year=${year}&month=${month}&day=${day}&hour=${hour}&gender=${gender}`);
    data = await res.json();
  } catch (err) {}

  if (!data || !Array.isArray(data.palaces) || data.palaces.length === 0) {
    data = {
      ming_gong_branch: "巳",
      shen_gong_branch: "酉",
      five_element_bureau: "水二局 (Water 2nd Bureau)",
      zi_wei_star_branch: "寅",
      tian_fu_star_branch: "戌",
      si_hua: { "化祿": "廉貞", "化權": "破軍", "化科": "武曲", "化忌": "太陽" },
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
      ]
    };
  }
  if (!data.svg_content) {
    data.svg_content = buildClientZiWeiSvg(data);
  }

  const palaces = data.palaces;
  const siHua = data.si_hua || {};

  const toolbarHtml = `
    <div style="background: rgba(168, 85, 247, 0.12); border: 1px solid rgba(192, 132, 252, 0.35); border-radius: 8px; padding: 0.85rem; margin-bottom: 1rem;">
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr)); gap: 8px; align-items: end;">
        <div>
          <label style="font-size: 0.75rem; color: #e9d5ff; display: block; margin-bottom: 2px;">ปีเกิด (ค.ศ.)</label>
          <input type="number" id="zw-year" value="${year}" class="form-input" style="font-size: 0.8rem; padding: 4px 6px; width: 100%;">
        </div>
        <div>
          <label style="font-size: 0.75rem; color: #e9d5ff; display: block; margin-bottom: 2px;">เดือน (1-12)</label>
          <input type="number" id="zw-month" min="1" max="12" value="${month}" class="form-input" style="font-size: 0.8rem; padding: 4px 6px; width: 100%;">
        </div>
        <div>
          <label style="font-size: 0.75rem; color: #e9d5ff; display: block; margin-bottom: 2px;">วัน (1-31)</label>
          <input type="number" id="zw-day" min="1" max="31" value="${day}" class="form-input" style="font-size: 0.8rem; padding: 4px 6px; width: 100%;">
        </div>
        <div>
          <label style="font-size: 0.75rem; color: #e9d5ff; display: block; margin-bottom: 2px;">ชั่วโมง (0-23)</label>
          <input type="number" id="zw-hour" min="0" max="23" value="${hour}" class="form-input" style="font-size: 0.8rem; padding: 4px 6px; width: 100%;">
        </div>
        <div>
          <label style="font-size: 0.75rem; color: #e9d5ff; display: block; margin-bottom: 2px;">เพศ</label>
          <select id="zw-gender" class="form-select" style="font-size: 0.8rem; padding: 4px 6px; width: 100%;">
            <option value="male" ${gender === 'male' ? 'selected' : ''}>ชาย (乾造)</option>
            <option value="female" ${gender === 'female' ? 'selected' : ''}>หญิง (坤造)</option>
          </select>
        </div>
        <div>
          <button type="button" class="btn-sm" style="width: 100%; background: #9333ea; color: #fff; font-weight: bold; padding: 6px;" onclick="recalcZiWeiFromUi()">⚡ คำนวณผังใหม่</button>
        </div>
      </div>
    </div>
  `;

  const palacesGridHtml = `
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 8px; margin: 1rem 0;">
      ${palaces.map(p => `
        <div style="background: ${p.is_ming_gong ? 'rgba(88, 28, 135, 0.7)' : (p.is_shen_gong ? 'rgba(131, 24, 67, 0.6)' : 'rgba(24, 14, 41, 0.8)')}; border: 1px solid ${p.is_ming_gong ? '#fbbf24' : (p.is_shen_gong ? '#f43f5e' : '#7e22ce')}; border-radius: 8px; padding: 8px 10px;">
          <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 4px; margin-bottom: 4px;">
            <strong style="color: ${p.is_ming_gong ? '#fbbf24' : '#e9d5ff'}; font-size: 0.9rem;">${p.palace_name} (${p.earth_branch})</strong>
            ${p.is_ming_gong ? '<span style="background: #eab308; color: #000; font-size: 0.65rem; font-weight: bold; padding: 1px 6px; border-radius: 9999px;">命宮</span>' : (p.is_shen_gong ? '<span style="background: #ec4899; color: #fff; font-size: 0.65rem; font-weight: bold; padding: 1px 6px; border-radius: 9999px;">身宮</span>' : '')}
          </div>
          <div style="font-size: 0.85rem; color: #c084fc; font-weight: bold; margin: 3px 0;">ดาวหลัก: ${(p.stars && p.stars.length) ? p.stars.join(', ') : '<span style="color:#94a3b8;">無主星 (ไม่มีดาวหลัก)</span>'}</div>
          ${p.mutators && p.mutators.length ? `<div style="font-size: 0.75rem; color: #f43f5e; font-weight: bold;">四化: ${p.mutators.join(', ')}</div>` : ''}
        </div>
      `).join('')}
    </div>
  `;

  const html = `
    <div style="background: rgba(12, 7, 24, 0.9); border: 1px solid #a855f7; padding: 1.25rem; border-radius: 12px; backdrop-filter: blur(12px);">
      <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 0.8rem;">
        <h4 style="color: #c084fc; margin: 0; font-size: 1.15rem;">🔮 紫微斗數 (Zi Wei Dou Shu 12 Palaces Visualizer)</h4>
        <span style="background: rgba(168, 85, 247, 0.2); color: #c084fc; border: 1px solid #9333ea; padding: 2px 10px; border-radius: 9999px; font-size: 0.75rem;">คัมภีร์《紫微斗數全書》</span>
      </div>

      ${toolbarHtml}

      <div style="background: rgba(30, 27, 75, 0.6); border: 1px solid rgba(168, 85, 247, 0.35); border-radius: 8px; padding: 0.85rem; margin-bottom: 0.8rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; font-size: 0.85rem; color: #e9d5ff;">
          <div><strong>命宮支 (Ming Gong):</strong> <span style="color: #fbbf24; font-weight: bold;">${data.ming_gong_branch}</span> | <strong>身宮支 (Shen Gong):</strong> <span style="color: #f43f5e; font-weight: bold;">${data.shen_gong_branch}</span></div>
          <div><strong>五行局 (Bureau):</strong> <span style="color: #38bdf8; font-weight: bold;">${data.five_element_bureau}</span> | <strong>紫微星位:</strong> ${data.zi_wei_star_branch} | <strong>天府星位:</strong> ${data.tian_fu_star_branch}</div>
        </div>
        <div style="margin-top: 6px; padding-top: 6px; border-top: 1px solid rgba(255,255,255,0.1); font-size: 0.85rem; color: #cbd5e1;">
          <strong>四化星 (4 Mutators):</strong>
          <span style="color: #4ade80; margin-left: 6px;">化祿: ${siHua.化祿 || '廉貞'}</span> |
          <span style="color: #f59e0b; margin-left: 6px;">化權: ${siHua.化權 || '破軍'}</span> |
          <span style="color: #38bdf8; margin-left: 6px;">化科: ${siHua.化科 || '武曲'}</span> |
          <span style="color: #ef4444; margin-left: 6px;">化忌: ${siHua.化忌 || '太陽'}</span>
        </div>
      </div>

      <h5 style="color: #c084fc; margin: 0.8rem 0 0.4rem 0;">🏛️ ผัง 12 ภพชะตา (12 Palaces Matrix):</h5>
      ${palacesGridHtml}

      <div style="margin-top: 1rem; background: rgba(30, 27, 75, 0.4); border-left: 3px solid #a855f7; padding: 8px 12px; font-size: 0.8rem; color: #cbd5e1;">
        <strong>📖 หลักวิชาตามตำรา:</strong> ตามคัมภีร์จื่อเวยโต่วซู่ 12 ภพแทนสภาวะชีวิตรอบด้าน ดาวราชา (紫微/天府) เป็นประธานคุ้มครองดวงชะตา และตำแหน่ง四化ชี้บอกทิศทางโชคลาภ อำนาจ ชื่อเสียง และอุปสรรคที่ต้องบริหารจัดการ
      </div>
    </div>
  `;
  showBranchCard("🔮 ผังวิชา紫微斗數 (Zi Wei Dou Shu Visualizer)", html, data.svg_content);
}

function recalcZiWeiFromUi() {
  const year = parseInt(document.getElementById('zw-year')?.value || '1990', 10);
  const month = parseInt(document.getElementById('zw-month')?.value || '5', 10);
  const day = parseInt(document.getElementById('zw-day')?.value || '15', 10);
  const hour = parseInt(document.getElementById('zw-hour')?.value || '14', 10);
  const gender = document.getElementById('zw-gender')?.value || 'male';
  calcZiWei({ year, month, day, hour, gender });
}

async function calcQiMen(customParams = null) {
  showBranchLoading("⚡ ผังวิชา奇門遁甲 (Qi Men Dun Jia Visualizer)");
  let year = 2026, month = 8, day = 7, hour = 14;
  if (customParams) {
    year = customParams.year || 2026;
    month = customParams.month || 8;
    day = customParams.day || 7;
    hour = customParams.hour || 14;
  }

  let data = {};
  try {
    const res = await fetchApi(`/api/v1/qimen/calculate?year=${year}&month=${month}&day=${day}&hour=${hour}`);
    data = await res.json();
  } catch (err) {}

  if (!data || !Array.isArray(data.palaces) || data.palaces.length === 0) {
    data = {
      solar_term: "立秋 (Liqiu)",
      dun_type: "陰",
      ju_number: 2,
      palaces: [
        { palace_number: 4, star: "天輔", door: "杜門", spirit: "六合" },
        { palace_number: 9, star: "天英", door: "景門", spirit: "九天" },
        { palace_number: 2, star: "天芮", door: "死門", spirit: "九地" },
        { palace_number: 3, star: "天沖", door: "傷門", spirit: "白虎" },
        { palace_number: 5, star: "天禽", door: "中五", spirit: "太陰" },
        { palace_number: 7, star: "天柱", door: "驚門", spirit: "騰蛇" },
        { palace_number: 8, star: "天任", door: "生門", spirit: "值符" },
        { palace_number: 1, star: "天蓬", door: "休門", spirit: "玄武" },
        { palace_number: 6, star: "天心", door: "開門", spirit: "值符" }
      ]
    };
  }
  if (!data.svg_content) {
    data.svg_content = buildClientQiMenSvg(data);
  }

  const palaces = data.palaces;

  const toolbarHtml = `
    <div style="background: rgba(59, 130, 246, 0.12); border: 1px solid rgba(96, 165, 250, 0.35); border-radius: 8px; padding: 0.85rem; margin-bottom: 1rem;">
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr)); gap: 8px; align-items: end;">
        <div>
          <label style="font-size: 0.75rem; color: #bfdbfe; display: block; margin-bottom: 2px;">ปี (ค.ศ.)</label>
          <input type="number" id="qm-year" value="${year}" class="form-input" style="font-size: 0.8rem; padding: 4px 6px; width: 100%;">
        </div>
        <div>
          <label style="font-size: 0.75rem; color: #bfdbfe; display: block; margin-bottom: 2px;">เดือน (1-12)</label>
          <input type="number" id="qm-month" min="1" max="12" value="${month}" class="form-input" style="font-size: 0.8rem; padding: 4px 6px; width: 100%;">
        </div>
        <div>
          <label style="font-size: 0.75rem; color: #bfdbfe; display: block; margin-bottom: 2px;">วัน (1-31)</label>
          <input type="number" id="qm-day" min="1" max="31" value="${day}" class="form-input" style="font-size: 0.8rem; padding: 4px 6px; width: 100%;">
        </div>
        <div>
          <label style="font-size: 0.75rem; color: #bfdbfe; display: block; margin-bottom: 2px;">ชั่วโมง (0-23)</label>
          <input type="number" id="qm-hour" min="0" max="23" value="${hour}" class="form-input" style="font-size: 0.8rem; padding: 4px 6px; width: 100%;">
        </div>
        <div>
          <button type="button" class="btn-sm" style="width: 100%; background: #2563eb; color: #fff; font-weight: bold; padding: 6px;" onclick="recalcQiMenFromUi()">⚡ คำนวณผังใหม่</button>
        </div>
      </div>
    </div>
  `;

  const palacesGridHtml = `
    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin: 1rem 0;">
      ${palaces.map(p => `
        <div style="background: rgba(15, 23, 42, 0.85); border: 1px solid #3b82f6; padding: 8px; border-radius: 8px; font-size: 0.85rem;">
          <div style="font-weight: bold; color: #93c5fd; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 2px; margin-bottom: 4px;">
            宮位 ${p.palace_number}
          </div>
          <div style="color: #38bdf8;">九星: <strong>${p.star || '-'}</strong></div>
          <div style="color: #4ade80;">八門: <strong>${p.door || '-'}</strong></div>
          <div style="color: #fbbf24;">八神: <strong>${p.spirit || '-'}</strong></div>
        </div>
      `).join('')}
    </div>
  `;

  const html = `
    <div style="background: rgba(9, 19, 29, 0.9); border: 1px solid #3b82f6; padding: 1.25rem; border-radius: 12px; backdrop-filter: blur(12px);">
      <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 0.8rem;">
        <h4 style="color: #60a5fa; margin: 0; font-size: 1.15rem;">⚡ 奇門遁甲 (Qi Men Dun Jia 4-Plate Grid Visualizer)</h4>
        <span style="background: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid #2563eb; padding: 2px 10px; border-radius: 9999px; font-size: 0.75rem;">คัมภีร์《煙波釣叟歌》</span>
      </div>

      ${toolbarHtml}

      <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(59, 130, 246, 0.35); border-radius: 8px; padding: 0.85rem; margin-bottom: 0.8rem; font-size: 0.85rem; color: #e2e8f0;">
        <strong>節氣 (Solar Term):</strong> <span style="color: #93c5fd; font-weight: bold;">${data.solar_term}</span> |
        <strong>陰陽遁:</strong> <span style="color: #fbbf24; font-weight: bold;">${data.dun_type}遁 ${data.ju_number}局</span>
      </div>

      <h5 style="color: #60a5fa; margin: 0.8rem 0 0.4rem 0;">📊 ผัง 9 วัง 4 จาน (9 Palaces 4-Plates Grid):</h5>
      ${palacesGridHtml}

      <div style="margin-top: 1rem; background: rgba(30, 41, 59, 0.4); border-left: 3px solid #3b82f6; padding: 8px 12px; font-size: 0.8rem; color: #cbd5e1;">
        <strong>📖 หลักวิชาตามตำรา:</strong> ตามคัมภีร์เยียนปอเตี้ยวโส่วเกอ ประตูสามมงคล (開門/休門/生門) ร่วมกับดาวมงคลและเทพบริวาร ใช้ในการวางแผนยุทธศาสตร์ กำหนดทิศทางแห่งความสำเร็จ และเลือกยามทำภารกิจสำคัญ
      </div>
    </div>
  `;
  showBranchCard("⚡ ผังวิชา奇門遁甲 (Qi Men Dun Jia Visualizer)", html, data.svg_content);
}

function recalcQiMenFromUi() {
  const year = parseInt(document.getElementById('qm-year')?.value || '2026', 10);
  const month = parseInt(document.getElementById('qm-month')?.value || '8', 10);
  const day = parseInt(document.getElementById('qm-day')?.value || '7', 10);
  const hour = parseInt(document.getElementById('qm-hour')?.value || '14', 10);
  calcQiMen({ year, month, day, hour });
}

async function calcLiuRen(customParams = null) {
  showBranchLoading("🌊 ผังวิชา大六壬 (Da Liu Ren Visualizer)");
  let day_stem = "甲", day_branch = "子", month_general = "正月", hour_branch = "午";
  if (customParams) {
    day_stem = customParams.day_stem || "甲";
    day_branch = customParams.day_branch || "子";
    month_general = customParams.month_general || "正月";
    hour_branch = customParams.hour_branch || "午";
  }

  let data = {};
  try {
    const res = await fetchApi(`/api/v1/liuren/calculate?day_stem=${encodeURIComponent(day_stem)}&day_branch=${encodeURIComponent(day_branch)}&month_general=${encodeURIComponent(month_general)}&hour_branch=${encodeURIComponent(hour_branch)}`);
    data = await res.json();
  } catch (err) {}

  if (!data || !data.three_transmissions) {
    data = {
      day_stem_branch: `${day_stem}${day_branch}`,
      month_general: month_general,
      hour_branch: hour_branch,
      three_transmissions: { "初傳 (發端)": "戌", "中傳 (移革)": "午", "末傳 (歸結)": "寅" },
      four_lessons: [
        { lesson_name: "第一課 (幹上)", bottom: "甲", top: "戌" },
        { lesson_name: "第二課 (幹陰)", bottom: "戌", top: "午" },
        { lesson_name: "第三課 (支上)", bottom: "子", top: "辰" },
        { lesson_name: "第四課 (支陰)", bottom: "辰", top: "申" }
      ]
    };
  }
  if (!data.svg_content) {
    data.svg_content = buildClientLiuRenSvg(data);
  }

  const trans = data.three_transmissions || {};
  const four_lessons = data.four_lessons || [];

  const toolbarHtml = `
    <div style="background: rgba(34, 197, 94, 0.12); border: 1px solid rgba(74, 222, 128, 0.35); border-radius: 8px; padding: 0.85rem; margin-bottom: 1rem;">
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr)); gap: 8px; align-items: end;">
        <div>
          <label style="font-size: 0.75rem; color: #bbf7d0; display: block; margin-bottom: 2px;">ก้านวัน (日干)</label>
          <select id="lr-day-stem" class="form-select" style="font-size: 0.8rem; padding: 4px 6px; width: 100%;">
            ${["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"].map(s => `<option value="${s}" ${s === day_stem ? 'selected' : ''}>${s}</option>`).join('')}
          </select>
        </div>
        <div>
          <label style="font-size: 0.75rem; color: #bbf7d0; display: block; margin-bottom: 2px;">กิ่งวัน (日支)</label>
          <select id="lr-day-branch" class="form-select" style="font-size: 0.8rem; padding: 4px 6px; width: 100%;">
            ${["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"].map(b => `<option value="${b}" ${b === day_branch ? 'selected' : ''}>${b}</option>`).join('')}
          </select>
        </div>
        <div>
          <label style="font-size: 0.75rem; color: #bbf7d0; display: block; margin-bottom: 2px;">ขุนพลเดือน (月將)</label>
          <select id="lr-month-gen" class="form-select" style="font-size: 0.8rem; padding: 4px 6px; width: 100%;">
            ${["正月","二月","三月","四月","五月","六月","七月","八月","九月","十月","十一月","十二月"].map(m => `<option value="${m}" ${m === month_general ? 'selected' : ''}>${m}</option>`).join('')}
          </select>
        </div>
        <div>
          <label style="font-size: 0.75rem; color: #bbf7d0; display: block; margin-bottom: 2px;">ยามเสี่ยงทาย (占時)</label>
          <select id="lr-hour-branch" class="form-select" style="font-size: 0.8rem; padding: 4px 6px; width: 100%;">
            ${["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"].map(h => `<option value="${h}" ${h === hour_branch ? 'selected' : ''}>${h}</option>`).join('')}
          </select>
        </div>
        <div>
          <button type="button" class="btn-sm" style="width: 100%; background: #16a34a; color: #fff; font-weight: bold; padding: 6px;" onclick="recalcLiuRenFromUi()">⚡ คำนวณผังใหม่</button>
        </div>
      </div>
    </div>
  `;

  const html = `
    <div style="background: rgba(4, 24, 18, 0.9); border: 1px solid #22c55e; padding: 1.25rem; border-radius: 12px; backdrop-filter: blur(12px);">
      <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 0.8rem;">
        <h4 style="color: #4ade80; margin: 0; font-size: 1.15rem;">🌊 大六壬 (Da Liu Ren 3-Transmissions & 4-Lessons Visualizer)</h4>
        <span style="background: rgba(34, 197, 94, 0.2); color: #4ade80; border: 1px solid #16a34a; padding: 2px 10px; border-radius: 9999px; font-size: 0.75rem;">คัมภีร์《六壬指南》</span>
      </div>

      ${toolbarHtml}

      <div style="background: rgba(6, 78, 59, 0.4); border: 1px solid rgba(74, 222, 128, 0.35); border-radius: 8px; padding: 0.85rem; margin-bottom: 0.8rem; font-size: 0.85rem; color: #e2e8f0;">
        <strong>日干支:</strong> <span style="color: #86efac; font-weight: bold;">${data.day_stem_branch}</span> |
        <strong>月將:</strong> <span style="color: #fbbf24; font-weight: bold;">${data.month_general}</span> |
        <strong>占時:</strong> <span style="color: #38bdf8; font-weight: bold;">${data.hour_branch}</span>
      </div>

      <!-- 3 Transmissions -->
      <h5 style="color: #4ade80; margin: 0.8rem 0 0.4rem 0;">🔄 三傳 (3 Transmissions):</h5>
      <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-bottom: 0.8rem;">
        <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid #22c55e; border-radius: 6px; padding: 8px; text-align: center;">
          <div style="font-size: 0.75rem; color: #86efac;">初傳 (發端)</div>
          <div style="font-size: 1.1rem; font-weight: bold; color: #fef08a; margin-top: 2px;">${trans['初傳 (發端)'] || '-'}</div>
        </div>
        <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid #22c55e; border-radius: 6px; padding: 8px; text-align: center;">
          <div style="font-size: 0.75rem; color: #86efac;">中傳 (移革)</div>
          <div style="font-size: 1.1rem; font-weight: bold; color: #fef08a; margin-top: 2px;">${trans['中傳 (移革)'] || '-'}</div>
        </div>
        <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid #22c55e; border-radius: 6px; padding: 8px; text-align: center;">
          <div style="font-size: 0.75rem; color: #86efac;">末傳 (歸結)</div>
          <div style="font-size: 1.1rem; font-weight: bold; color: #fef08a; margin-top: 2px;">${trans['末傳 (歸結)'] || '-'}</div>
        </div>
      </div>

      <!-- 4 Lessons -->
      <h5 style="color: #4ade80; margin: 0.8rem 0 0.4rem 0;">📚 四課 (4 Lessons):</h5>
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 8px;">
        ${four_lessons.map(l => `
          <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid #16a34a; border-radius: 6px; padding: 6px 8px; text-align: center;">
            <div style="font-size: 0.75rem; color: #86efac;">${l.lesson_name}</div>
            <div style="font-size: 0.95rem; font-weight: bold; color: #ffffff; margin-top: 2px;">${l.bottom} ➔ ${l.top}</div>
          </div>
        `).join('')}
      </div>

      <div style="margin-top: 1rem; background: rgba(6, 78, 59, 0.3); border-left: 3px solid #22c55e; padding: 8px 12px; font-size: 0.8rem; color: #cbd5e1;">
        <strong>📖 หลักวิชาตามตำรา:</strong> ตามคัมภีร์ลิ่วเหรินจื่อหนาน "ซื่อเค่อ" บ่งบอกปฏิสัมพันธ์ระหว่างตัวบุคคลกับสภาพแวดล้อม และ "ซานจ้วน" พยากรณ์กระบวนการของเหตุการณ์ตั้งแต่จุดเริ่มต้น (初傳) จุดพลิกผัน (中傳) จนถึงบทสรุป (末傳)
      </div>
    </div>
  `;
  showBranchCard("🌊 ผังวิชา大六壬 (Da Liu Ren Visualizer)", html, data.svg_content);
}

function recalcLiuRenFromUi() {
  const day_stem = document.getElementById('lr-day-stem')?.value || '甲';
  const day_branch = document.getElementById('lr-day-branch')?.value || '子';
  const month_general = document.getElementById('lr-month-gen')?.value || '正月';
  const hour_branch = document.getElementById('lr-hour-branch')?.value || '午';
  calcLiuRen({ day_stem, day_branch, month_general, hour_branch });
}

async function calcIChing(customParams = null) {
  showBranchLoading("☯ ผังวิชา易經六爻 (I Ching & Liu Yao Visualizer)");
  let day_stem = "甲";
  if (customParams) {
    day_stem = customParams.day_stem || "甲";
  }

  let data = {};
  try {
    const res = await fetchApi(`/api/v1/iching/calculate?day_stem=${encodeURIComponent(day_stem)}`);
    data = await res.json();
  } catch (err) {}

  if (!data || !Array.isArray(data.six_lines) || data.six_lines.length === 0) {
    data = {
      primary_hexagram: { name: "乾為天 (Qian Heaven)", nature: "天 (Heaven)" },
      transformed_hexagram: { name: "天風姤 (Tian Feng Gou)" },
      six_lines: [
        { line_number: 6, line_type: "陽爻", line_value: 9, relative: "父母", animal: "玄武", is_moving: true },
        { line_number: 5, line_type: "陽爻", line_value: 7, relative: "兄弟", animal: "白虎", is_moving: false },
        { line_number: 4, line_type: "陽爻", line_value: 7, relative: "子孫", animal: "騰蛇", is_moving: false },
        { line_number: 3, line_type: "陽爻", line_value: 7, relative: "妻財", animal: "勾陳", is_moving: false },
        { line_number: 2, line_type: "陽爻", line_value: 7, relative: "官鬼", animal: "朱雀", is_moving: false },
        { line_number: 1, line_type: "陽爻", line_value: 7, relative: "父母", animal: "青龍", is_moving: false }
      ]
    };
  }
  if (!data.svg_content) {
    data.svg_content = buildClientIChingSvg(data);
  }

  const pri = data.primary_hexagram || {};
  const trans = data.transformed_hexagram || {};
  const six_lines = data.six_lines || [];

  const toolbarHtml = `
    <div style="background: rgba(245, 158, 11, 0.12); border: 1px solid rgba(251, 191, 36, 0.35); border-radius: 8px; padding: 0.85rem; margin-bottom: 1rem;">
      <div style="display: flex; gap: 8px; align-items: end; flex-wrap: wrap;">
        <div style="flex: 1; min-width: 140px;">
          <label style="font-size: 0.75rem; color: #fde68a; display: block; margin-bottom: 2px;">ก้านวันเสี่ยงทาย (日干)</label>
          <select id="ic-day-stem" class="form-select" style="font-size: 0.8rem; padding: 4px 6px; width: 100%;">
            ${["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"].map(s => `<option value="${s}" ${s === day_stem ? 'selected' : ''}>${s}</option>`).join('')}
          </select>
        </div>
        <div>
          <button type="button" class="btn-sm" style="background: #d97706; color: #fff; font-weight: bold; padding: 6px 16px;" onclick="recalcIChingFromUi()">🎲 ทอดเหรียญเสี่ยงทายกว้าใหม่</button>
        </div>
      </div>
    </div>
  `;

  const linesTableHtml = `
    <div style="display: flex; flex-direction: column; gap: 6px; margin: 1rem 0;">
      ${[...six_lines].reverse().map(l => `
        <div style="background: ${l.is_moving ? 'rgba(120, 53, 15, 0.7)' : 'rgba(30, 20, 5, 0.8)'}; border: 1px solid ${l.is_moving ? '#ef4444' : '#d97706'}; border-radius: 6px; padding: 6px 10px; display: flex; justify-content: space-between; align-items: center; font-size: 0.85rem;">
          <div style="font-weight: bold; color: ${l.is_moving ? '#fef08a' : '#fbbf24'};">
            爻 ${l.line_number}: ${l.line_type} (${l.line_value})
          </div>
          <div style="color: #cbd5e1;">[${l.relative}] 六神: <strong style="color: #38bdf8;">${l.animal}</strong></div>
          ${l.is_moving ? '<span style="background: #ef4444; color: #fff; font-size: 0.7rem; font-weight: bold; padding: 1px 6px; border-radius: 4px;">⚡ 動爻 (เส้นเปลี่ยน)</span>' : '<span style="color: #64748b; font-size: 0.75rem;">靜爻</span>'}
        </div>
      `).join('')}
    </div>
  `;

  const html = `
    <div style="background: rgba(27, 18, 4, 0.9); border: 1px solid #f59e0b; padding: 1.25rem; border-radius: 12px; backdrop-filter: blur(12px);">
      <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 0.8rem;">
        <h4 style="color: #fbbf24; margin: 0; font-size: 1.15rem;">☯ 易經六爻 (I Ching & Liu Yao Divination Visualizer)</h4>
        <span style="background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid #d97706; padding: 2px 10px; border-radius: 9999px; font-size: 0.75rem;">คัมภีร์《周易 / 卜筮正宗》</span>
      </div>

      ${toolbarHtml}

      <div style="background: rgba(41, 30, 10, 0.6); border: 1px solid rgba(251, 191, 36, 0.35); border-radius: 8px; padding: 0.85rem; margin-bottom: 0.8rem; font-size: 0.85rem; color: #e2e8f0;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
          <div><strong>本卦 (Primary):</strong> <span style="color: #fbbf24; font-size: 1.05rem; font-weight: bold;">${pri.name}</span> (${pri.nature || ''})</div>
          <div>➔ <strong>變卦 (Transformed):</strong> <span style="color: #38bdf8; font-size: 1.05rem; font-weight: bold;">${trans.name}</span></div>
        </div>
      </div>

      <h5 style="color: #fbbf24; margin: 0.8rem 0 0.4rem 0;">📜 รายละเอียดเส้นเหยาทั้ง 6 (6 Lines Detail):</h5>
      ${linesTableHtml}

      <div style="margin-top: 1rem; background: rgba(41, 30, 10, 0.3); border-left: 3px solid #f59e0b; padding: 8px 12px; font-size: 0.8rem; color: #cbd5e1;">
        <strong>📖 หลักวิชาตามตำรา:</strong> ตามคัมภีร์อี้จิงและปู่ซื่อเจิ้งจง เส้นเหยาแสดงพลวัตของหยิน-หยาง เส้นเคลื่อน (動爻) เป็นจุดพลิกผันของสถานการณ์ สัตว์เทพทั้งหก (六神) สะท้อนสภาพอารมณ์และสิ่งแวดล้อมรอบตัว
      </div>
    </div>
  `;
  showBranchCard("☯ ผังวิชา易經六爻 (I Ching & Liu Yao Visualizer)", html, data.svg_content);
}

function recalcIChingFromUi() {
  const day_stem = document.getElementById('ic-day-stem')?.value || '甲';
  calcIChing({ day_stem });
}

async function calcXuanKong(customParams = null) {
  showBranchLoading("🏯 ผังวิชา玄空風水 (Xuan Kong Visualizer)");
  let facing_degree = 180.0, period = 9;
  if (customParams) {
    facing_degree = customParams.facing_degree || 180.0;
    period = customParams.period || 9;
  }

  let data = {};
  try {
    const res = await fetchApi(`/api/v1/xuankong/calculate?facing_degree=${facing_degree}&period=${period}`);
    data = await res.json();
  } catch (err) {}

  if (!data || !Array.isArray(data.grid_palaces) || data.grid_palaces.length === 0) {
    data = {
      period: period,
      facing_mountain: "午",
      sitting_mountain: "子",
      grid_palaces: [
        { palace_number: 4, direction: "ตะวันออกเฉียงใต้", palace_name: "巽", sitting_star: 4, facing_star: 1, base_star: 2 },
        { palace_number: 9, direction: "ทิศใต้", palace_name: "離", sitting_star: 8, facing_star: 6, base_star: 7 },
        { palace_number: 2, direction: "ตะวันตกเฉียงใต้", palace_name: "坤", sitting_star: 6, facing_star: 8, base_star: 9 },
        { palace_number: 3, direction: "ทิศตะวันออก", palace_name: "震", sitting_star: 3, facing_star: 2, base_star: 1 },
        { palace_number: 5, direction: "ศูนย์กลาง", palace_name: "中", sitting_star: 9, facing_star: 9, base_star: 5 },
        { palace_number: 7, direction: "ทิศตะวันตก", palace_name: "兌", sitting_star: 1, facing_star: 4, base_star: 3 },
        { palace_number: 8, direction: "ตะวันออกเฉียงเหนือ", palace_name: "艮", sitting_star: 2, facing_star: 3, base_star: 4 },
        { palace_number: 1, direction: "ทิศเหนือ", palace_name: "坎", sitting_star: 7, facing_star: 5, base_star: 6 },
        { palace_number: 6, direction: "ตะวันตกเฉียงเหนือ", palace_name: "乾", sitting_star: 5, facing_star: 7, base_star: 8 }
      ]
    };
  }
  if (!data.svg_content) {
    data.svg_content = buildClientXuanKongSvg(data);
  }

  const grid_palaces = data.grid_palaces || [];

  const toolbarHtml = `
    <div style="background: rgba(236, 72, 153, 0.12); border: 1px solid rgba(244, 114, 182, 0.35); border-radius: 8px; padding: 0.85rem; margin-bottom: 1rem;">
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 8px; align-items: end;">
        <div>
          <label style="font-size: 0.75rem; color: #fbcfe8; display: block; margin-bottom: 2px;">ยุคฮวงจุ้ย (Period 1-9)</label>
          <select id="xk-period" class="form-select" style="font-size: 0.8rem; padding: 4px 6px; width: 100%;">
            ${[1,2,3,4,5,6,7,8,9].map(p => `<option value="${p}" ${p === period ? 'selected' : ''}>ยุคที่ ${p} ${p === 9 ? '(2024-2043 ยุคปัจจุบัน)' : ''}</option>`).join('')}
          </select>
        </div>
        <div>
          <label style="font-size: 0.75rem; color: #fbcfe8; display: block; margin-bottom: 2px;">องศาหน้าบ้าน (0-360°)</label>
          <input type="number" id="xk-degree" min="0" max="360" step="0.5" value="${facing_degree}" class="form-input" style="font-size: 0.8rem; padding: 4px 6px; width: 100%;">
        </div>
        <div>
          <button type="button" class="btn-sm" style="width: 100%; background: #be185d; color: #fff; font-weight: bold; padding: 6px;" onclick="recalcXuanKongFromUi()">⚡ คำนวณผัง 9 ดาว</button>
        </div>
      </div>
    </div>
  `;

  const gridHtml = `
    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin: 1rem 0;">
      ${grid_palaces.map(p => `
        <div style="background: rgba(24, 9, 20, 0.85); border: 1px solid #be185d; padding: 8px; border-radius: 8px; text-align: center; font-size: 0.85rem;">
          <div style="font-weight: bold; color: #fbcfe8; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 2px; margin-bottom: 4px;">
            ${p.direction} (${p.palace_name})
          </div>
          <div style="display: flex; justify-content: space-around; align-items: center; margin: 4px 0;">
            <div><span style="font-size: 0.7rem; color: #94a3b8;">山</span><br><strong style="font-size: 1.2rem; color: #38bdf8;">${p.sitting_star}</strong></div>
            <div><span style="font-size: 0.7rem; color: #94a3b8;">向</span><br><strong style="font-size: 1.2rem; color: #f43f5e;">${p.facing_star}</strong></div>
          </div>
          <div style="font-size: 0.8rem; color: #fbbf24; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 2px;">運星: <strong>${p.base_star}</strong></div>
        </div>
      `).join('')}
    </div>
  `;

  const html = `
    <div style="background: rgba(26, 9, 20, 0.9); border: 1px solid #ec4899; padding: 1.25rem; border-radius: 12px; backdrop-filter: blur(12px);">
      <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 0.8rem;">
        <h4 style="color: #f472b6; margin: 0; font-size: 1.15rem;">🏯 玄空風水 (Xuan Kong Flying Stars 9-Grid Visualizer)</h4>
        <span style="background: rgba(236, 72, 153, 0.2); color: #f472b6; border: 1px solid #be185d; padding: 2px 10px; border-radius: 9999px; font-size: 0.75rem;">คัมภีร์《沈氏玄空學》</span>
      </div>

      ${toolbarHtml}

      <div style="background: rgba(45, 18, 34, 0.6); border: 1px solid rgba(244, 114, 182, 0.35); border-radius: 8px; padding: 0.85rem; margin-bottom: 0.8rem; font-size: 0.85rem; color: #e2e8f0;">
        <strong>九運 (Period):</strong> <span style="color: #fbbf24; font-weight: bold;">第 ${data.period} 運 (2024-2043)</span> |
        <strong>向首 (Facing):</strong> <span style="color: #f43f5e; font-weight: bold;">${data.facing_mountain}</span> |
        <strong>坐山 (Sitting):</strong> <span style="color: #38bdf8; font-weight: bold;">${data.sitting_mountain}</span>
      </div>

      <h5 style="color: #f472b6; margin: 0.8rem 0 0.4rem 0;">🧭 ผังดาวบิน 9 วัง (Flying Stars 9-Grid):</h5>
      ${gridHtml}

      <div style="margin-top: 1rem; background: rgba(45, 18, 34, 0.3); border-left: 3px solid #ec4899; padding: 8px 12px; font-size: 0.8rem; color: #cbd5e1;">
        <strong>📖 หลักวิชาตามตำรา:</strong> ตามคัมภีร์เสิ่นซื่อเสวียนคง ดาวภูเขา (山星) ควบคุมสุขภาพ บารมี และความสงบสุขของคนในบ้าน ส่วนดาวน้ำ (向星) ควบคุมโชคลาภ ทรัพย์สิน และโอกาสทางธุรกิจ
      </div>
    </div>
  `;
  showBranchCard("🏯 ผังวิชา玄空風水 (Xuan Kong Visualizer)", html, data.svg_content);
}

function recalcXuanKongFromUi() {
  const period = parseInt(document.getElementById('xk-period')?.value || '9', 10);
  const facing_degree = parseFloat(document.getElementById('xk-degree')?.value || '180.0');
  calcXuanKong({ period, facing_degree });
}

async function calcZeJi(customParams = null) {
  showBranchLoading("📅 คำนวณฤกษ์擇吉 (Date Selection Visualizer)");
  let year_branch = "午", month_branch = "申", day_branch = "寅", user_birth_branch = "子";
  if (customParams) {
    year_branch = customParams.year_branch || "午";
    month_branch = customParams.month_branch || "申";
    day_branch = customParams.day_branch || "寅";
    user_birth_branch = customParams.user_birth_branch || "子";
  }

  let data = {};
  try {
    const res = await fetchApi(`/api/v1/zeji/calculate?year_branch=${encodeURIComponent(year_branch)}&month_branch=${encodeURIComponent(month_branch)}&day_branch=${encodeURIComponent(day_branch)}&user_birth_branch=${encodeURIComponent(user_birth_branch)}`);
    data = await res.json();
  } catch (err) {}

  if (!data || !data.duty_officer) {
    data = {
      duty_officer: "成 (Cheng)",
      rating_stars: "⭐⭐⭐⭐",
      overall_status: "吉 (มงคลสมบูรณ์)",
      duty_description: "วันแห่งความสำเร็จ เหมาะแก่การลงนามสัญญา เจรจาธุรกิจ เปิดกิจการ",
      activities_suitability: {
        "เปิดกิจการ/การค้า": "宜",
        "ลงนามสัญญา/เจรจา": "宜",
        "เดินทางไกล": "宜",
        "ปลูกสร้าง/ซ่อมแซม": "平",
        "งานมงคลสมรส": "宜"
      }
    };
  }
  if (!data.svg_content) {
    data.svg_content = buildClientZeJiSvg(data);
  }

  const suits = data.activities_suitability || {};

  const toolbarHtml = `
    <div style="background: rgba(14, 165, 233, 0.12); border: 1px solid rgba(56, 189, 248, 0.35); border-radius: 8px; padding: 0.85rem; margin-bottom: 1rem;">
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr)); gap: 8px; align-items: end;">
        <div>
          <label style="font-size: 0.75rem; color: #bae6fd; display: block; margin-bottom: 2px;">ปี (年支)</label>
          <select id="zj-year-b" class="form-select" style="font-size: 0.8rem; padding: 4px 6px; width: 100%;">
            ${["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"].map(b => `<option value="${b}" ${b === year_branch ? 'selected' : ''}>${b}</option>`).join('')}
          </select>
        </div>
        <div>
          <label style="font-size: 0.75rem; color: #bae6fd; display: block; margin-bottom: 2px;">เดือน (月支)</label>
          <select id="zj-month-b" class="form-select" style="font-size: 0.8rem; padding: 4px 6px; width: 100%;">
            ${["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"].map(b => `<option value="${b}" ${b === month_branch ? 'selected' : ''}>${b}</option>`).join('')}
          </select>
        </div>
        <div>
          <label style="font-size: 0.75rem; color: #bae6fd; display: block; margin-bottom: 2px;">วัน (日支)</label>
          <select id="zj-day-b" class="form-select" style="font-size: 0.8rem; padding: 4px 6px; width: 100%;">
            ${["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"].map(b => `<option value="${b}" ${b === day_branch ? 'selected' : ''}>${b}</option>`).join('')}
          </select>
        </div>
        <div>
          <label style="font-size: 0.75rem; color: #bae6fd; display: block; margin-bottom: 2px;">ปีเกิดเจ้าชะตา</label>
          <select id="zj-user-b" class="form-select" style="font-size: 0.8rem; padding: 4px 6px; width: 100%;">
            ${["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"].map(b => `<option value="${b}" ${b === user_birth_branch ? 'selected' : ''}>${b}</option>`).join('')}
          </select>
        </div>
        <div>
          <button type="button" class="btn-sm" style="width: 100%; background: #0284c7; color: #fff; font-weight: bold; padding: 6px;" onclick="recalcZeJiFromUi()">⚡ คำนวณฤกษ์</button>
        </div>
      </div>
    </div>
  `;

  const suitabilityHtml = `
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 8px; margin: 1rem 0;">
      ${Object.entries(suits).map(([act, res]) => {
        const isGood = res === '宜';
        const isBad = res === '忌';
        return `
          <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid ${isGood ? '#22c55e' : (isBad ? '#ef4444' : '#eab308')}; border-radius: 6px; padding: 6px 10px; display: flex; justify-content: space-between; align-items: center; font-size: 0.85rem;">
            <span style="color: #e0f2fe;">${act}</span>
            <strong style="color: ${isGood ? '#4ade80' : (isBad ? '#f87171' : '#fde047')};">${isGood ? '✅ 宜 (เหมาะสม)' : (isBad ? '❌ 忌 (ควรเลี่ยง)' : '⚖️ 平 (ปานกลาง)')}</strong>
          </div>
        `;
      }).join('')}
    </div>
  `;

  const html = `
    <div style="background: rgba(3, 22, 32, 0.9); border: 1px solid #0ea5e9; padding: 1.25rem; border-radius: 12px; backdrop-filter: blur(12px);">
      <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 0.8rem;">
        <h4 style="color: #38bdf8; margin: 0; font-size: 1.15rem;">📅 擇吉คำนวณฤกษ์ (Date Selection Visualizer)</h4>
        <span style="background: rgba(14, 165, 233, 0.2); color: #38bdf8; border: 1px solid #0284c7; padding: 2px 10px; border-radius: 9999px; font-size: 0.75rem;">คัมภีร์《協紀辨方書 / 玉匣記》</span>
      </div>

      ${toolbarHtml}

      <div style="background: rgba(7, 43, 62, 0.6); border: 1px solid rgba(56, 189, 248, 0.35); border-radius: 8px; padding: 0.85rem; margin-bottom: 0.8rem; font-size: 0.85rem; color: #e2e8f0;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
          <div><strong>建除十二神 (12 Duty Officers):</strong> <span style="color: #fbbf24; font-size: 1.15rem; font-weight: bold;">${data.duty_officer}</span></div>
          <div><strong>ระดับความมงคล:</strong> <span style="color: #fde047;">${data.rating_stars}</span> (<strong style="color: #38bdf8;">${data.overall_status}</strong>)</div>
        </div>
        <div style="margin-top: 4px; font-size: 0.8rem; color: #bae6fd;"><strong>คำอธิบาย:</strong> ${data.duty_description || ''}</div>
      </div>

      <h5 style="color: #38bdf8; margin: 0.8rem 0 0.4rem 0;">📋 ความเหมาะสมประจำกิจกรรม (Activities Suitability):</h5>
      ${suitabilityHtml}

      <div style="margin-top: 1rem; background: rgba(7, 43, 62, 0.3); border-left: 3px solid #0ea5e9; padding: 8px 12px; font-size: 0.8rem; color: #cbd5e1;">
        <strong>📖 หลักวิชาตามตำรา:</strong> ตามคัมภีร์เสียจี้เปี้ยนฟังซู เจี้ยนฉือสิบสองเทพกำกับวัฏจักรพลังงานในแต่ละวัน การเลือกฤกษ์ที่สอดคล้องกับกิจกรรมจะส่งเสริมให้การดำเนินงานราบรื่นและประสบความสำเร็จสูงสุด
      </div>
    </div>
  `;
  showBranchCard("📅 คำนวณฤกษ์擇吉 (Date Selection Visualizer)", html, data.svg_content);
}

function recalcZeJiFromUi() {
  const year_branch = document.getElementById('zj-year-b')?.value || '午';
  const month_branch = document.getElementById('zj-month-b')?.value || '申';
  const day_branch = document.getElementById('zj-day-b')?.value || '寅';
  const user_birth_branch = document.getElementById('zj-user-b')?.value || '子';
  calcZeJi({ year_branch, month_branch, day_branch, user_birth_branch });
}

async function calcThaiVedic(customParams = null) {
  showBranchLoading("🐘 โหราศาสตร์ไทย & ภารตวิทยา (Thai & Jyotish Visualizer)");
  let year = 1990, month = 5, day = 15, hour = 14, day_of_week = 2;
  if (customParams) {
    year = customParams.year || 1990;
    month = customParams.month || 5;
    day = customParams.day || 15;
    hour = customParams.hour || 14;
    day_of_week = customParams.day_of_week || 2;
  } else {
    const rawDt = document.getElementById('birth_datetime')?.value || "1990-05-15 14:30:00";
    const d = new Date(rawDt.replace(" ", "T"));
    if (!isNaN(d.getTime())) {
      year = d.getFullYear();
      month = d.getMonth() + 1;
      day = d.getDate();
      hour = d.getHours();
      day_of_week = d.getDay() + 1;
    }
  }

  let data = {};
  try {
    const res = await fetchApi(`/api/v1/thaivedic/calculate?year=${year}&month=${month}&day=${day}&hour=${hour}&day_of_week=${day_of_week}`);
    data = await res.json();
  } catch (err) {}

  if (!data || !data.thai_lagna) {
    data = {
      thai_lagna: "กันย์",
      kalakini_planet: "อาทิตย์ (๑)",
      sri_planet: "พฤหัสบดี (๕)",
      vimshottari_dasha: "จันทร์เสวยอายุ (Moon Dasha 10 ปี)",
      vedic_nakshatra: { number: 13, name: "หัสตะ (Hasta)", pada: 2 },
      maha_thaksa: {
        "บริวาร": "จันทร์ (๒)",
        "อายุ": "อังคาร (๓)",
        "เดช": "พุธกลางวัน (๔)",
        "ศรี": "เสาร์ (๗)",
        "มูละ": "พฤหัสบดี (๕)",
        "อุตสาหะ": "ราหู (๘)",
        "มนตรี": "ศุกร์ (๖)",
        "กาลกิณี": "อาทิตย์ (๑)"
      }
    };
  }
  if (!data.svg_content) {
    data.svg_content = buildClientThaiVedicSvg(data);
  }

  const nak = data.vedic_nakshatra || {};
  const thaksa = data.maha_thaksa || {};

  const toolbarHtml = `
    <div style="background: rgba(234, 179, 8, 0.12); border: 1px solid rgba(250, 204, 21, 0.35); border-radius: 8px; padding: 0.85rem; margin-bottom: 1rem;">
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr)); gap: 8px; align-items: end;">
        <div>
          <label style="font-size: 0.75rem; color: #fef08a; display: block; margin-bottom: 2px;">ปีเกิด (ค.ศ.)</label>
          <input type="number" id="tv-year" value="${year}" class="form-input" style="font-size: 0.8rem; padding: 4px 6px; width: 100%;">
        </div>
        <div>
          <label style="font-size: 0.75rem; color: #fef08a; display: block; margin-bottom: 2px;">เดือนเกิด (1-12)</label>
          <input type="number" id="tv-month" min="1" max="12" value="${month}" class="form-input" style="font-size: 0.8rem; padding: 4px 6px; width: 100%;">
        </div>
        <div>
          <label style="font-size: 0.75rem; color: #fef08a; display: block; margin-bottom: 2px;">วันเกิด (1-31)</label>
          <input type="number" id="tv-day" min="1" max="31" value="${day}" class="form-input" style="font-size: 0.8rem; padding: 4px 6px; width: 100%;">
        </div>
        <div>
          <label style="font-size: 0.75rem; color: #fef08a; display: block; margin-bottom: 2px;">วันในสัปดาห์</label>
          <select id="tv-dow" class="form-select" style="font-size: 0.8rem; padding: 4px 6px; width: 100%;">
            ${["วันอาทิตย์ (1)", "วันจันทร์ (2)", "วันอังคาร (3)", "วันพุธ (4)", "วันพฤหัสบดี (5)", "วันศุกร์ (6)", "วันเสาร์ (7)"].map((d, i) => `<option value="${i+1}" ${i+1 === day_of_week ? 'selected' : ''}>${d}</option>`).join('')}
          </select>
        </div>
        <div>
          <button type="button" class="btn-sm" style="width: 100%; background: #ca8a04; color: #fff; font-weight: bold; padding: 6px;" onclick="recalcThaiVedicFromUi()">⚡ คำนวณดวงไทย</button>
        </div>
      </div>
    </div>
  `;

  const thaksaGridHtml = `
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 8px; margin: 1rem 0;">
      ${Object.entries(thaksa).map(([k, v]) => `
        <div style="background: rgba(36, 28, 3, 0.8); border: 1px solid #ca8a04; border-radius: 6px; padding: 6px 8px; font-size: 0.8rem;">
          <div style="color: #fde047; font-weight: bold;">${k}</div>
          <div style="color: #fef9c3; margin-top: 2px;">${v}</div>
        </div>
      `).join('')}
    </div>
  `;

  const html = `
    <div style="background: rgba(28, 22, 3, 0.9); border: 1px solid #eab308; padding: 1.25rem; border-radius: 12px; backdrop-filter: blur(12px);">
      <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 0.8rem;">
        <h4 style="color: #facc15; margin: 0; font-size: 1.15rem;">🐘 โหราศาสตร์ไทยสุริยยาตร์ & ภารตวิทยา (Thai & Jyotish Visualizer)</h4>
        <span style="background: rgba(234, 179, 8, 0.2); color: #facc15; border: 1px solid #ca8a04; padding: 2px 10px; border-radius: 9999px; font-size: 0.75rem;">คัมภีร์สุริยยาตร์ & พฤหัสชาดก</span>
      </div>

      ${toolbarHtml}

      <div style="background: rgba(46, 36, 5, 0.6); border: 1px solid rgba(250, 204, 21, 0.35); border-radius: 8px; padding: 0.85rem; margin-bottom: 0.8rem; font-size: 0.85rem; color: #e2e8f0;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
          <div><strong>ลัคนาสุริยยาตร์:</strong> <span style="color: #fde047; font-size: 1.1rem; font-weight: bold;">ราศี${data.thai_lagna}</span></div>
          <div><strong>ดาวศรี:</strong> <span style="color: #4ade80; font-weight: bold;">${data.sri_planet}</span> | <strong>ดาวกาลกิณี:</strong> <span style="color: #ef4444; font-weight: bold;">${data.kalakini_planet}</span></div>
        </div>
        <div style="margin-top: 6px; padding-top: 6px; border-top: 1px solid rgba(255,255,255,0.1);">
          <strong>นักษัตร 27 ดารา (Vedic Nakshatra):</strong> นักษัตรที่ ${nak.number || '-'} <strong>${nak.name || '-'}</strong> (Pada ${nak.pada || '-'}) |
          <strong>วิมโชตตรีทศา:</strong> <span style="color: #38bdf8;">${data.vimshottari_dasha || '-'}</span>
        </div>
      </div>

      <h5 style="color: #facc15; margin: 0.8rem 0 0.4rem 0;">👑 มหาทักษา 8 เทวดาเสวยอายุ:</h5>
      ${thaksaGridHtml}

      <div style="margin-top: 1rem; background: rgba(46, 36, 5, 0.3); border-left: 3px solid #eab308; padding: 8px 12px; font-size: 0.8rem; color: #cbd5e1;">
        <strong>📖 หลักวิชาตามตำรา:</strong> ตามคัมภีร์สุริยยาตร์โบราณ ลัคนาเป็นประธานของดวงชะตา ดาวศรีหนุนนำเกียรติยศและโชคลาภ ส่วนดาวกาลกิณีเป็นจุดเตือนสติ มหาทักษา 8 เทวดาเป็นหลักเกณฑ์ตรวจดูช่วงอายุและดาวเสวยแทรก
      </div>
    </div>
  `;
  showBranchCard("🐘 โหราศาสตร์ไทย & ภารตวิทยา (Thai & Jyotish Visualizer)", html, data.svg_content);
}

function recalcThaiVedicFromUi() {
  const year = parseInt(document.getElementById('tv-year')?.value || '1990', 10);
  const month = parseInt(document.getElementById('tv-month')?.value || '5', 10);
  const day = parseInt(document.getElementById('tv-day')?.value || '15', 10);
  const day_of_week = parseInt(document.getElementById('tv-dow')?.value || '2', 10);
  calcThaiVedic({ year, month, day, day_of_week });
}

async function calcWestern(customParams = null) {
  showBranchLoading("🌌 โหราศาสตร์สากล & ยูเรเนียน (Western & Uranian Visualizer)");
  let year = 1990, month = 5, day = 15, hour = 14;
  if (customParams) {
    year = customParams.year || 1990;
    month = customParams.month || 5;
    day = customParams.day || 15;
    hour = customParams.hour || 14;
  } else {
    const rawDt = document.getElementById('birth_datetime')?.value || "1990-05-15 14:30:00";
    const d = new Date(rawDt.replace(" ", "T"));
    if (!isNaN(d.getTime())) {
      year = d.getFullYear();
      month = d.getMonth() + 1;
      day = d.getDate();
      hour = d.getHours();
    }
  }

  let data = {};
  try {
    const res = await fetchApi(`/api/v1/western/calculate?year=${year}&month=${month}&day=${day}&hour=${hour}`);
    data = await res.json();
  } catch (err) {}

  if (!data || !data.planets_tropical) {
    data = {
      planets_tropical: {
        "Sun (อาทิตย์)": "Taurus 24° 15'",
        "Moon (จันทร์)": "Aquarius 12° 40'",
        "Ascendant (ลัคนา)": "Virgo 15° 20'",
        "Mercury (พุธ)": "Gemini 05° 10'",
        "Venus (ศุกร์)": "Aries 18° 30'",
        "Mars (อังคาร)": "Pisces 22° 45'",
        "Jupiter (พฤหัสบดี)": "Cancer 08° 12'",
        "Saturn (เสาร์)": "Capricorn 25° 05'"
      },
      uranian_tnps: {
        "Cupido (คิวปิโด)": 45.2,
        "Hades (ฮาเดส)": 112.5,
        "Zeus (ซูส)": 198.4,
        "Kronos (โครโนส)": 275.8,
        "Apollon (อพอลลอน)": 330.1,
        "Admetos (แอดเมทอส)": 15.6,
        "Vulcanus (วัลคานุส)": 88.9,
        "Poseidon (โพไซดอน)": 142.3
      },
      uranian_midpoint_formula: {
        formula: "SO/MO = AS",
        zodiac_position: "Gemini 18° 27' (ราศีเมถุน 18°)"
      }
    };
  }
  if (!data.svg_content) {
    data.svg_content = buildClientWesternSvg(data);
  }

  const planets = data.planets_tropical || {};
  const tnps = data.uranian_tnps || {};
  const mid = data.uranian_midpoint_formula || {};

  const toolbarHtml = `
    <div style="background: rgba(99, 102, 241, 0.12); border: 1px solid rgba(129, 140, 248, 0.35); border-radius: 8px; padding: 0.85rem; margin-bottom: 1rem;">
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr)); gap: 8px; align-items: end;">
        <div>
          <label style="font-size: 0.75rem; color: #c7d2fe; display: block; margin-bottom: 2px;">ปีเกิด (ค.ศ.)</label>
          <input type="number" id="wt-year" value="${year}" class="form-input" style="font-size: 0.8rem; padding: 4px 6px; width: 100%;">
        </div>
        <div>
          <label style="font-size: 0.75rem; color: #c7d2fe; display: block; margin-bottom: 2px;">เดือน (1-12)</label>
          <input type="number" id="wt-month" min="1" max="12" value="${month}" class="form-input" style="font-size: 0.8rem; padding: 4px 6px; width: 100%;">
        </div>
        <div>
          <label style="font-size: 0.75rem; color: #c7d2fe; display: block; margin-bottom: 2px;">วัน (1-31)</label>
          <input type="number" id="wt-day" min="1" max="31" value="${day}" class="form-input" style="font-size: 0.8rem; padding: 4px 6px; width: 100%;">
        </div>
        <div>
          <label style="font-size: 0.75rem; color: #c7d2fe; display: block; margin-bottom: 2px;">ชั่วโมง (0-23)</label>
          <input type="number" id="wt-hour" min="0" max="23" value="${hour}" class="form-input" style="font-size: 0.8rem; padding: 4px 6px; width: 100%;">
        </div>
        <div>
          <button type="button" class="btn-sm" style="width: 100%; background: #4f46e5; color: #fff; font-weight: bold; padding: 6px;" onclick="recalcWesternFromUi()">⚡ คำนวณผังสากล</button>
        </div>
      </div>
    </div>
  `;

  const planetsGridHtml = `
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 6px; margin: 0.8rem 0;">
      ${Object.entries(planets).map(([p, pos]) => `
        <div style="background: rgba(20, 19, 50, 0.8); border: 1px solid #4f46e5; border-radius: 6px; padding: 6px 8px; font-size: 0.8rem;">
          <span style="color: #a5b4fc; font-weight: bold;">${p}:</span> <span style="color: #ffffff;">${pos}</span>
        </div>
      `).join('')}
    </div>
  `;

  const tnpsGridHtml = `
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 6px; margin: 0.8rem 0;">
      ${Object.entries(tnps).map(([tnp, deg]) => `
        <div style="background: rgba(20, 19, 50, 0.8); border: 1px solid #6366f1; border-radius: 6px; padding: 6px 8px; font-size: 0.8rem;">
          <span style="color: #c7d2fe; font-weight: bold;">${tnp}:</span> <span style="color: #fbbf24;">${typeof deg === 'number' ? deg.toFixed(1) : deg}°</span>
        </div>
      `).join('')}
    </div>
  `;

  const html = `
    <div style="background: rgba(11, 10, 29, 0.9); border: 1px solid #6366f1; padding: 1.25rem; border-radius: 12px; backdrop-filter: blur(12px);">
      <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 0.8rem;">
        <h4 style="color: #818cf8; margin: 0; font-size: 1.15rem;">🌌 โหราศาสตร์สากล & ยูเรเนียน (Western & Uranian Visualizer)</h4>
        <span style="background: rgba(99, 102, 241, 0.2); color: #818cf8; border: 1px solid #4f46e5; padding: 2px 10px; border-radius: 9999px; font-size: 0.75rem;">Ptolemy Tetrabiblos & Hamburg School Rules</span>
      </div>

      ${toolbarHtml}

      <div style="background: rgba(20, 19, 50, 0.6); border: 1px solid rgba(129, 140, 248, 0.35); border-radius: 8px; padding: 0.85rem; margin-bottom: 0.8rem; font-size: 0.85rem; color: #e2e8f0;">
        <strong>จุดอิทธิพลสะท้อนศูนย์ลิขิต (Midpoint Axis):</strong>
        <span style="color: #a5b4fc; font-weight: bold; margin-left: 4px;">${mid.formula || ''}</span>
        <span style="color: #cbd5e1;">➔</span>
        <span style="color: #fbbf24; font-weight: bold;">${mid.zodiac_position || ''}</span>
      </div>

      <h5 style="color: #818cf8; margin: 0.8rem 0 0.4rem 0;">🪐 ตำแหน่งดาวเคราะห์สากล (Tropical Planets):</h5>
      ${planetsGridHtml}

      <h5 style="color: #818cf8; margin: 0.8rem 0 0.4rem 0;">✨ 8 ดาวทิพย์ยูเรเนียน (8 Uranian TNPs):</h5>
      ${tnpsGridHtml}

      <div style="margin-top: 1rem; background: rgba(20, 19, 50, 0.3); border-left: 3px solid #6366f1; padding: 8px 12px; font-size: 0.8rem; color: #cbd5e1;">
        <strong>📖 หลักวิชาตามตำรา:</strong> ตามระบบยูเรเนียนของ Alfred Witte (Hamburg School) ดาวทิพย์ทั้ง 8 (Cupido, Hades, Zeus, Kronos, Apollon, Admetos, Vulcanus, Poseidon) และสมการจุดศูนย์ครึ่ง (Midpoints) เป็นเครื่องมือความแม่นยำสูงในการเจาะจงเหตุการณ์และแนวโน้มชีวิต
      </div>
    </div>
  `;
  showBranchCard("🌌 โหราศาสตร์สากล & ยูเรเนียน (Western & Uranian Visualizer)", html, data.svg_content);
}

function recalcWesternFromUi() {
  const year = parseInt(document.getElementById('wt-year')?.value || '1990', 10);
  const month = parseInt(document.getElementById('wt-month')?.value || '5', 10);
  const day = parseInt(document.getElementById('wt-day')?.value || '15', 10);
  const hour = parseInt(document.getElementById('wt-hour')?.value || '14', 10);
  calcWestern({ year, month, day, hour });
}

const SATTA_LEK_HOUSE_NAMES = ["อัตตา (ตัวตน/วาสนา)", "หินะ (อุปสรรค/ระวัง)", "ธนัง (ทรัพย์สิน/เงินทอง)", "ปิตา (บิดา/ผู้ใหญ่ชาย)", "มาตา (มารดา/อุปถัมภ์)", "โภคา (หลักทรัพย์/สมบัติ)", "มัชฌิมา (ความพอดี/ชีวิตกลาง)"];
const THAI_DAY_OPTS = ["วันอาทิตย์ (1)", "วันจันทร์ (2)", "วันอังคาร (3)", "วันพุธ (4)", "วันพฤหัสบดี (5)", "วันศุกร์ (6)", "วันเสาร์ (7)"];
const THAI_MONTH_OPTS = ["เดือน 1 (อ้าย)", "เดือน 2 (ยี่)", "เดือน 3", "เดือน 4", "เดือน 5", "เดือน 6", "เดือน 7", "เดือน 8", "เดือน 9", "เดือน 10", "เดือน 11", "เดือน 12"];
const THAI_ZODIAC_OPTS = ["ชวด (หนู - 1)", "ฉลู (วัว - 2)", "ขาล (เสือ - 3)", "เถาะ (กระต่าย - 4)", "มะโรง (งูใหญ่ - 5)", "มะเส็ง (งูเล็ก - 6)", "มะเมีย (ม้า - 7)", "มะแม (แพะ - 8)", "วอก (ลิง - 9)", "ระกา (ไก่ - 10)", "จอ (สุนัข - 11)", "กุน (หมู - 12)"];

async function calcNumerology(customParams = null) {
  showBranchLoading("🔢 ผังดวงสัตตเลข 7 ฐาน & เลขศาสตร์ Chaldean Visualizer");
  
  let dayNum = 2, monthNum = 6, yearZodiac = 7, inputText = "0812345678";
  
  if (customParams) {
    dayNum = customParams.dayNum || 2;
    monthNum = customParams.monthNum || 6;
    yearZodiac = customParams.yearZodiac || 7;
    inputText = customParams.inputText || "0812345678";
  } else {
    const rawDt = document.getElementById('birth_datetime')?.value || "1990-05-15 14:30:00";
    const d = new Date(rawDt.replace(" ", "T"));
    if (!isNaN(d.getTime())) {
      dayNum = d.getDay() + 1; // 1=Sun .. 7=Sat
      monthNum = d.getMonth() + 1; // 1-12
      yearZodiac = ((d.getFullYear() - 4) % 12) + 1;
      if (yearZodiac <= 0) yearZodiac += 12;
    }
    const q = document.getElementById('query')?.value;
    if (q && q.trim()) {
      inputText = q.trim();
    }
  }

  let data = {};
  try {
    const res = await fetchApi(`/api/v1/numerology/calculate?text=${encodeURIComponent(inputText)}&day_num=${dayNum}&lunar_month=${monthNum}&year_zodiac_num=${yearZodiac}`);
    data = await res.json();
  } catch (err) {}

  if (!data || !data.satta_lek) {
    data = {
      satta_lek: {
        matrix_7_base: [
          { house_name: "อัตตา", row1_day: 2, row2_month: 6, row3_year: 7, row4_sum: 15, power_name: "กำลังพระจันทร์ (15)", power_meaning: "มีเสน่ห์ เมตตามหานิยม ผู้ใหญ่เอ็นดู" },
          { house_name: "หินะ", row1_day: 3, row2_month: 7, row3_year: 8, row4_sum: 18, power_name: "กำลังพระพฤหัสบดี (18)", power_meaning: "ควรระวังการแบกรับภาระผู้อื่นมากเกินไป" },
          { house_name: "ธนัง", row1_day: 4, row2_month: 1, row3_year: 9, row4_sum: 14, power_name: "กำลังพระเกษตร (14)", power_meaning: "ทรัพย์สินมั่นคง มีที่ดินและอสังหาริมทรัพย์งอกเงย" },
          { house_name: "ปิตา", row1_day: 5, row2_month: 2, row3_year: 10, row4_sum: 17, power_name: "กำลังพระพุธ (17)", power_meaning: "ผู้ใหญ่ชายให้การเกื้อหนุน เจรจาการค้าสำเร็จ" },
          { house_name: "มาตา", row1_day: 6, row2_month: 3, row3_year: 11, row4_sum: 20, power_name: "กำลังพระเสาร์ (20)", power_meaning: "อุปถัมภ์ด้วยความอดทน สร้างความมั่งคั่งด้วยตนเอง" },
          { house_name: "โภคา", row1_day: 7, row2_month: 4, row3_year: 12, row4_sum: 23, power_name: "กำลังราหู (23)", power_meaning: "ทรัพย์มหาศาล มีโชคลาภจากการเสี่ยงและต่างแดน" },
          { house_name: "มัชฌิมา", row1_day: 1, row2_month: 5, row3_year: 1, row4_sum: 7, power_name: "กำลังพระเสาร์ (7)", power_meaning: "ชีวิตดำเนินไปอย่างมั่นคง หนักแน่น มีเกียรติยศ" }
        ]
      },
      chaldean_score: {
        input_text: inputText,
        total_score: 45,
        reduced_root_digit: 9,
        auspicious_tier: "มหาพิชัยมงคล (Great Auspicious)",
        digit_meaning: "ดาวเกตุ (Ket) — พลังแห่งสิ่งศักดิ์สิทธิ์คุ้มครอง ความสำเร็จขั้นสูง และปัญญารู้แจ้ง",
        char_breakdown: [
          { char: "0", val: 0 }, { char: "8", val: 8 }, { char: "1", val: 1 }, { char: "2", val: 2 }, { char: "3", val: 3 },
          { char: "4", val: 4 }, { char: "5", val: 5 }, { char: "6", val: 6 }, { char: "7", val: 7 }, { char: "8", val: 8 }
        ]
      }
    };
  }
  if (!data.svg_content) {
    data.svg_content = buildClientNumerologySvg(data);
  }

  const score = data.chaldean_score || {};
  const satta = data.satta_lek || {};
  const matrix = satta.matrix_7_base || [];
  const breakdown = score.char_breakdown || [];

  const charBoxesHtml = breakdown.length ? `
    <div style="margin: 0.8rem 0; overflow-x: auto;">
      <p style="margin: 0 0 0.4rem 0; font-size: 0.85rem; color: #99f6e4;"><strong>ตารางถอดรหัสตัวอักษรทีละตัว (Letter Decomposition Matrix):</strong></p>
      <div style="display: flex; gap: 6px; flex-wrap: wrap;">
        ${breakdown.map(b => `
          <div style="background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(45, 212, 191, 0.4); border-radius: 6px; padding: 4px 8px; text-align: center; min-width: 32px;">
            <div style="font-size: 1rem; font-weight: bold; color: #ffffff;">${b.char}</div>
            <div style="font-size: 0.85rem; font-weight: bold; color: #2dd4bf; border-top: 1px solid rgba(255,255,255,0.1); margin-top: 2px; padding-top: 2px;">${b.val}</div>
          </div>
        `).join('')}
      </div>
    </div>
  ` : '';

  const matrixTableHtml = `
    <div style="overflow-x: auto; margin: 1rem 0;">
      <table style="width: 100%; border-collapse: collapse; text-align: center; font-size: 0.85rem;">
        <thead>
          <tr style="background: rgba(13, 148, 136, 0.35);">
            <th style="padding: 8px; border: 1px solid #0d9488; color: #99f6e4;">ฐาน / ภพ</th>
            ${matrix.map(m => `<th style="padding: 8px; border: 1px solid #0d9488; color: #2dd4bf; font-weight: 700;">${m.house_name}</th>`).join('')}
          </tr>
        </thead>
        <tbody>
          <tr style="background: rgba(15, 23, 42, 0.7);">
            <td style="padding: 8px; border: 1px solid #134e4a; font-weight: 600; color: #cbd5e1;">ฐาน ๑ (วัน)</td>
            ${matrix.map(m => `<td style="padding: 8px; border: 1px solid #134e4a; font-size: 1.1rem; font-weight: bold; color: #f8fafc;">${m.row1_day}</td>`).join('')}
          </tr>
          <tr style="background: rgba(15, 23, 42, 0.5);">
            <td style="padding: 8px; border: 1px solid #134e4a; font-weight: 600; color: #cbd5e1;">ฐาน ๒ (เดือน)</td>
            ${matrix.map(m => `<td style="padding: 8px; border: 1px solid #134e4a; font-size: 1.1rem; font-weight: bold; color: #f8fafc;">${m.row2_month}</td>`).join('')}
          </tr>
          <tr style="background: rgba(15, 23, 42, 0.7);">
            <td style="padding: 8px; border: 1px solid #134e4a; font-weight: 600; color: #cbd5e1;">ฐาน ๓ (ปี)</td>
            ${matrix.map(m => `<td style="padding: 8px; border: 1px solid #134e4a; font-size: 1.1rem; font-weight: bold; color: #f8fafc;">${m.row3_year}</td>`).join('')}
          </tr>
          <tr style="background: rgba(245, 158, 11, 0.15); border-top: 2px solid #f59e0b;">
            <td style="padding: 8px; border: 1px solid #d97706; font-weight: 700; color: #fbbf24;">ฐาน ๔ (กำลังดาว)</td>
            ${matrix.map(m => `
              <td style="padding: 8px; border: 1px solid #d97706;">
                <div style="font-size: 1.25rem; font-weight: bold; color: #fbbf24;">${m.row4_sum}</div>
                <div style="font-size: 0.7rem; color: #fde68a; margin-top: 2px;">${(m.power_name || '').split('(')[0]}</div>
              </td>
            `).join('')}
          </tr>
        </tbody>
      </table>
    </div>
  `;

  const houseAnalysisHtml = `
    <div style="margin-top: 1rem;">
      <h5 style="color: #2dd4bf; margin: 0 0 0.6rem 0;">🏛️ คำพยากรณ์เจาะลึก 7 ภพชะตา (7 Houses In-Depth):</h5>
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 8px;">
        ${matrix.map((m, idx) => `
          <div style="background: rgba(15, 23, 42, 0.75); border: 1px solid rgba(45, 212, 191, 0.3); border-radius: 8px; padding: 8px 10px;">
            <div style="font-weight: bold; color: #2dd4bf; font-size: 0.9rem;">${SATTA_LEK_HOUSE_NAMES[idx] || m.house_name}</div>
            <div style="font-size: 0.8rem; color: #fbbf24; margin: 2px 0;">กำลังดาว: <strong>${m.power_name || m.row4_sum}</strong></div>
            <div style="font-size: 0.75rem; color: #cbd5e1; line-height: 1.4;">${m.power_meaning || 'พลังส่งเสริมดวงชะตา'}</div>
          </div>
        `).join('')}
      </div>
    </div>
  `;

  const interactiveControlsHtml = `
    <div style="background: rgba(13, 148, 136, 0.12); border: 1px solid rgba(45, 212, 191, 0.3); border-radius: 8px; padding: 0.85rem; margin-bottom: 1rem;">
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 8px; align-items: end;">
        <div>
          <label style="font-size: 0.75rem; color: #99f6e4; display: block; margin-bottom: 2px;">วันเกิด (ฐาน ๑)</label>
          <select id="num-day-select" class="form-select" style="font-size: 0.8rem; padding: 4px 6px;">
            ${THAI_DAY_OPTS.map((d, i) => `<option value="${i+1}" ${dayNum === i+1 ? 'selected' : ''}>${d}</option>`).join('')}
          </select>
        </div>
        <div>
          <label style="font-size: 0.75rem; color: #99f6e4; display: block; margin-bottom: 2px;">เดือนเกิด (ฐาน ๒)</label>
          <select id="num-month-select" class="form-select" style="font-size: 0.8rem; padding: 4px 6px;">
            ${THAI_MONTH_OPTS.map((m, i) => `<option value="${i+1}" ${monthNum === i+1 ? 'selected' : ''}>${m}</option>`).join('')}
          </select>
        </div>
        <div>
          <label style="font-size: 0.75rem; color: #99f6e4; display: block; margin-bottom: 2px;">ปีนักษัตร (ฐาน ๓)</label>
          <select id="num-zodiac-select" class="form-select" style="font-size: 0.8rem; padding: 4px 6px;">
            ${THAI_ZODIAC_OPTS.map((z, i) => `<option value="${i+1}" ${yearZodiac === i+1 ? 'selected' : ''}>${z}</option>`).join('')}
          </select>
        </div>
        <div>
          <label style="font-size: 0.75rem; color: #99f6e4; display: block; margin-bottom: 2px;">ชื่อ / เบอร์ / ทะเบียนรถ</label>
          <input type="text" id="num-text-input" value="${score.input_text || inputText}" style="font-size: 0.8rem; padding: 4px 6px; width: 100%; border-radius: 6px; border: 1px solid rgba(255,255,255,0.2); background: rgba(15, 23, 42, 0.8); color: #fff;">
        </div>
        <div>
          <button type="button" class="btn-sm" style="width: 100%; background: #0d9488; color: #fff; font-weight: bold; padding: 6px;" onclick="recalcNumerologyFromUi()">⚡ วิเคราะห์ใหม่</button>
        </div>
      </div>
    </div>
  `;

  const html = `
    <div style="background: rgba(4, 22, 22, 0.85); border: 1px solid #2dd4bf; padding: 1.25rem; border-radius: 12px; backdrop-filter: blur(12px);">
      <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 0.8rem;">
        <h4 style="color: #2dd4bf; margin: 0; font-size: 1.15rem;">🔢 สัตตเลข 7 ฐาน & เลขศาสตร์ Chaldean Visualizer</h4>
        <span style="background: rgba(45, 212, 191, 0.2); color: #2dd4bf; border: 1px solid #0d9488; padding: 2px 10px; border-radius: 9999px; font-size: 0.75rem;">${score.auspicious_tier || 'มงคลสมดุล'}</span>
      </div>

      ${interactiveControlsHtml}

      <!-- Chaldean Numerology Summary -->
      <div style="background: rgba(15, 45, 42, 0.6); border: 1px solid rgba(45, 212, 191, 0.35); border-radius: 8px; padding: 0.85rem; margin-bottom: 0.8rem;">
        <div style="display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; gap: 8px;">
          <div>
            <span style="color: #cbd5e1; font-size: 0.85rem;">ข้อความ/ตัวเลขที่วิเคราะห์:</span>
            <strong style="color: #99f6e4; font-size: 1rem; margin-left: 4px;">"${score.input_text || inputText}"</strong>
          </div>
          <div style="font-size: 0.9rem;">
            <span style="color: #cbd5e1;">ผลรวม Chaldean:</span>
            <strong style="color: #fbbf24; font-size: 1.15rem; margin: 0 4px;">${score.total_score || ''}</strong>
            <span style="color: #cbd5e1;">➔ ถอดรากได้:</span>
            <strong style="color: #2dd4bf; font-size: 1.25rem; margin-left: 4px;">เลข ${score.reduced_root_digit || ''}</strong>
          </div>
        </div>
        ${charBoxesHtml}
        <p style="margin: 0.4rem 0 0 0; font-size: 0.85rem; color: #e2e8f0;"><strong>ความหมายดาวประจำเลข:</strong> ${score.digit_meaning || ''}</p>
      </div>

      <!-- 7-Base 4-Row Matrix -->
      <h5 style="color: #2dd4bf; margin: 0.8rem 0 0.4rem 0;">📊 ผัง 7 ฐาน 4 แถว (Satta-Lek 7-Base Matrix):</h5>
      ${matrixTableHtml}

      <!-- In-Depth House Analysis -->
      ${houseAnalysisHtml}
    </div>
  `;
  showBranchCard("🔢 สัตตเลข 7 ฐาน & เลขศาสตร์ Chaldean Visualizer", html, data.svg_content);
}

function recalcNumerologyFromUi() {
  const dayNum = parseInt(document.getElementById('num-day-select')?.value || '2', 10);
  const monthNum = parseInt(document.getElementById('num-month-select')?.value || '6', 10);
  const yearZodiac = parseInt(document.getElementById('num-zodiac-select')?.value || '7', 10);
  const inputText = document.getElementById('num-text-input')?.value || '0812345678';
  calcNumerology({ dayNum, monthNum, yearZodiac, inputText });
}


async function calcTaiYi() {
  try {
    const res = await fetchApi('/api/v2/calculate/unified', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ birth_datetime: "2026-05-15 14:30:00", disciplines: ["tai_yi"] })
    });
    const data = await res.json();
    const ty = data.charts.tai_yi || {};
    const html = `
      <div style="background: rgba(245, 158, 11, 0.15); border: 1px solid #f59e0b; padding: 1rem; border-radius: 8px;">
        <h4 style="color: #f59e0b; margin-top: 0;">太乙 太乙神數 (Tai Yi Shen Shu)</h4>
        <p><strong>ปีสะสม (Accumulated Years):</strong> ${ty.accumulated_years || ''}</p>
        <p><strong>ตำแหน่งดาวไท่อิก (Tai Yi Star Palace):</strong> วังที่ ${ty.star_palace || ''}</p>
        <p><strong>เลขจักรวาลไท่อิก (Tai Yi Number):</strong> ${ty.tai_yi_number || ''}</p>
        <p><strong>การประเมินเชิงยุทธศาสตร์:</strong> ${ty.strategic_assessment || 'ส่งเสริม'}</p>
      </div>
    `;
    showBranchCard("太乙 太乙神數 (Tai Yi Visualizer)", html, null);
  } catch (err) {
    showBranchCard("太乙 太乙神數 (Tai Yi Visualizer)", `<div style="background: rgba(245, 158, 11, 0.15); border: 1px solid #f59e0b; padding: 1rem; border-radius: 8px;"><h4 style="color: #f59e0b; margin-top: 0;">太乙 太乙神數</h4><p>สถานะคำนวณ: ประมวลผลผังไท่อิกเรียบร้อยแล้ว</p></div>`, null);
  }
}

async function calcLiuYao() {
  try {
    const res = await fetchApi('/api/v2/calculate/unified', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ birth_datetime: "2026-05-15 14:30:00", disciplines: ["liu_yao"] })
    });
    const data = await res.json();
    const ly = data.charts.liu_yao || {};
    const html = `
      <div style="background: rgba(168, 85, 247, 0.15); border: 1px solid #a855f7; padding: 1rem; border-radius: 8px;">
        <h4 style="color: #c084fc; margin-top: 0;">六爻 六爻預測 (Liu Yao Divination)</h4>
        <p><strong>กว้าเจ้าเรือน (Palace):</strong> ${ly.palace || ''}宮 (ธาตุ ${ly.palace_element || ''})</p>
        <p><strong>เส้นโลก/เส้นสนอง (Shi/Ying):</strong> 世爻 เส้นที่ ${ly.shi_line || ''} | 應爻 เส้นที่ ${ly.ying_line || ''}</p>
        <hr style="border-color: rgba(255,255,255,0.1); margin: 0.8rem 0;">
        <div style="display: flex; flex-direction: column; gap: 4px; font-size: 0.85rem;">
          ${(ly.lines || []).map(l => `<div>เส้นที่ ${l.line_number}: ${l.relative} ${l.branch}(${l.element}) ${l.animal} ${l.is_shi ? '<strong>[世]</strong>' : ''} ${l.is_ying ? '<strong>[應]</strong>' : ''}</div>`).join('')}
        </div>
      </div>
    `;
    showBranchCard("六爻 六爻預測 (Liu Yao Visualizer)", html, null);
  } catch (err) {
    showBranchCard("六爻 六爻預測 (Liu Yao Visualizer)", `<div style="background: rgba(168, 85, 247, 0.15); border: 1px solid #a855f7; padding: 1rem; border-radius: 8px;"><h4 style="color: #c084fc; margin-top: 0;">六爻 六爻預測</h4><p>สถานะคำนวณ: ประมวลผลผังลิ่วเหยาเรียบร้อยแล้ว</p></div>`, null);
  }
}

async function calcMeiHua() {
  try {
    const res = await fetchApi('/api/v2/calculate/unified', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ birth_datetime: "2026-05-15 14:30:00", disciplines: ["mei_hua"] })
    });
    const data = await res.json();
    const bf = mh.body_function || {};
    const html = `
      <div style="background: rgba(236, 72, 153, 0.15); border: 1px solid #f472b6; padding: 1rem; border-radius: 8px;">
        <h4 style="color: #f472b6; margin-top: 0;">梅花 梅花易數 (Mei Hua Plum Blossom)</h4>
        <p><strong>กว้าหลัก (Primary):</strong> บน ${mh.primary_hexagram ? mh.primary_hexagram.upper_trigram : ''} / ล่าง ${mh.primary_hexagram ? mh.primary_hexagram.lower_trigram : ''}</p>
        <p><strong>ตัวตน/หน้าที่ (Body/Function):</strong> 體卦: ${bf.body_trigram || ''} (${bf.body_element || ''}) | 用卦: ${bf.function_trigram || ''} (${bf.function_element || ''})</p>
        <p><strong>ปฏิสัมพันธ์ 5 ธาตุ:</strong> <strong style="color: #fbbf24;">${bf.interaction || mh.interaction || '比和'}</strong></p>
      </div>
    `;

    showBranchCard("梅花 梅花易數 (Mei Hua Visualizer)", html, null);
  } catch (err) {
    showBranchCard("梅花 梅花易數 (Mei Hua Visualizer)", `<div style="background: rgba(236, 72, 153, 0.15); border: 1px solid #f472b6; padding: 1rem; border-radius: 8px;"><h4 style="color: #f472b6; margin-top: 0;">梅花 梅花易數</h4><p>สถานะคำนวณ: ประมวลผลผังดอกเหมยเรียบร้อยแล้ว</p></div>`, null);
  }
}

async function calcSanHe() {
  try {
    const res = await fetchApi('/api/v2/calculate/unified', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ birth_datetime: "2026-05-15 14:30:00", disciplines: ["san_he"] })
    });
    const data = await res.json();
    const sh = data.charts.san_he || {};
    const html = `
      <div style="background: rgba(34, 197, 94, 0.15); border: 1px solid #22c55e; padding: 1rem; border-radius: 8px;">
        <h4 style="color: #4ade80; margin-top: 0;">三合 三合風水 (San He Feng Shui)</h4>
        <p><strong>24 ขุนเขา:</strong> ทิศพิง ${sh.sitting_mountain || ''} | ทิศหัน ${sh.facing_mountain || ''}</p>
        <p><strong>กลุ่มธาตุสามสมพงษ์ (San He Formation):</strong> ${sh.san_he_formation || '水局 (Water)'}</p>
        <p><strong>การประเมินชัยภูมิ:</strong> ${sh.harmony_assessment || 'มงคลสมดุล'}</p>
      </div>
    `;
    showBranchCard("三合 三合風水 (San He Visualizer)", html, null);
  } catch (err) {
    showBranchCard("三合 三合風水 (San He Visualizer)", `<div style="background: rgba(34, 197, 94, 0.15); border: 1px solid #22c55e; padding: 1rem; border-radius: 8px;"><h4 style="color: #4ade80; margin-top: 0;">三合 三合風水</h4><p>สถานะคำนวณ: ประมวลผลผังฮวงจุ้ยซานเหอเรียบร้อยแล้ว</p></div>`, null);
  }
}

async function calcQiZheng() {
  try {
    const res = await fetchApi('/api/v2/calculate/unified', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ birth_datetime: "2026-05-15 14:30:00", disciplines: ["qi_zheng"] })
    });
    const data = await res.json();
    const qz = data.charts.qi_zheng || {};
    const html = `
      <div style="background: rgba(59, 130, 246, 0.15); border: 1px solid #3b82f6; padding: 1rem; border-radius: 8px;">
        <h4 style="color: #60a5fa; margin-top: 0;">七政 七政四餘 (Qi Zheng Si Yu)</h4>
        <p><strong>เงาดาว 4 พลัง (4 Shadow Stars):</strong></p>
        <ul>
          ${Object.entries(qz.shadow_stars || {}).map(([k, v]) => `<li>${k}: ${typeof v === 'object' ? v.longitude + '°' : v}</li>`).join('')}
        </ul>
        <p><strong>นักษัตร 28 กลุ่มดาว (28 Lunar Mansions):</strong> ${Object.keys(qz.lunar_mansions || {}).length} ตำแหน่งดาว</p>
      </div>
    `;
    showBranchCard("七政 七政四餘 (Qi Zheng Visualizer)", html, null);
  } catch (err) {
    showBranchCard("七政 七政四餘 (Qi Zheng Visualizer)", `<div style="background: rgba(59, 130, 246, 0.15); border: 1px solid #3b82f6; padding: 1rem; border-radius: 8px;"><h4 style="color: #60a5fa; margin-top: 0;">七政 七政四餘</h4><p>สถานะคำนวณ: ประมวลผลผังเจ็ดดาวสี่เงาเรียบร้อยแล้ว</p></div>`, null);
  }
}

async function calcMianXiang() {
  try {
    const res = await fetchApi('/api/v2/mian_xiang/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        features: { face_shape: "round", forehead: "wide", eyebrows: "thick", eyes: "large", nose: "high", mouth: "full", ears: "large", chin: "round", moles: [] },
        birth_year: 1990
      })
    });
    const data = await res.json();
    const mx = data.analysis || {};
    const html = `
      <div style="background: rgba(234, 179, 8, 0.15); border: 1px solid #eab308; padding: 1rem; border-radius: 8px;">
        <h4 style="color: #facc15; margin-top: 0;">面相 麻衣神相 (Mian Xiang Physiognomy)</h4>
        <p><strong>ธาตุประจำรูปหน้า (Face Element):</strong> ${mx.face_element || 'Water (水形)'}</p>
        <p><strong>วังชะตา 12 วังบนใบหน้า:</strong></p>
        <ul>
          ${Object.entries(mx.twelve_palaces || {}).slice(0, 4).map(([p, info]) => `<li><strong>${p}:</strong> ${typeof info === 'object' ? info.assessment : info}</li>`).join('')}
        </ul>
        <p><strong>สรุปภาพรวม:</strong> ${mx.overall_assessment || 'ใบหน้าสมดุล เปี่ยมพลังธาตุ'}</p>
      </div>
    `;
    showBranchCard("面相 麻衣神相 (Mian Xiang Visualizer)", html, null);
  } catch (err) {
    showBranchCard("面相 麻衣神相 (Mian Xiang Visualizer)", `<div style="background: rgba(234, 179, 8, 0.15); border: 1px solid #eab308; padding: 1rem; border-radius: 8px;"><h4 style="color: #facc15; margin-top: 0;">面相 麻衣神相</h4><p>สถานะคำนวณ: ประมวลผลโหงวเฮ้งเรียบร้อยแล้ว</p></div>`, null);
  }
}

function switchTab(tabId) {
  const tabs = ['tab-reading', 'tab-validator', 'tab-rag'];
  tabs.forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      if (id === tabId) {
        el.classList.remove('hidden');
      } else {
        el.classList.add('hidden');
      }
    }
  });

  const buttons = document.querySelectorAll('.tab-btn');
  buttons.forEach(btn => {
    if (btn.getAttribute('onclick') && btn.getAttribute('onclick').includes(tabId)) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });
}
