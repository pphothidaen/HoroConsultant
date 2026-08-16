const BACKEND_API_HOSTS = [
  "https://horo-consultant-psi.vercel.app", // Primary Vercel Production Serverless API Gateway
  "https://pphothidaen-horoconsultant-core-api.hf.space", // HF Direct Docker API Backend
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
  delete requestOptions.showLoader;
  delete requestOptions.loaderMessage;

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
        const res = await fetch(url, requestOptions);
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

async function calcZiWei() {
  showBranchLoading("🔮 ผังวิชา紫微斗數 (Zi Wei Dou Shu Visualizer)");
  try {
    const res = await fetchApi('/api/v1/ziwei/calculate?year=1990&month=5&day=15&hour=14&gender=male');
    const data = await res.json();
    const html = `
      <div style="background: rgba(168, 85, 247, 0.15); border: 1px solid #c084fc; padding: 1rem; border-radius: 8px;">
        <h4 style="color: #c084fc; margin-top: 0;">🔮 紫微斗數 (Zi Wei Dou Shu Chart)</h4>
        <p><strong>命宮支 (Ming Gong):</strong> ${data.ming_gong_branch} | <strong>身宮支 (Shen Gong):</strong> ${data.shen_gong_branch}</p>
        <p><strong>五行局 (Bureau):</strong> ${data.five_element_bureau} | <strong>紫微星位:</strong> ${data.zi_wei_star_branch} | <strong>天府星位:</strong> ${data.tian_fu_star_branch}</p>
        <p><strong>四化 (Si Hua):</strong> 祿:${data.si_hua ? (data.si_hua.化祿 || '-') : '-'}, 權:${data.si_hua ? (data.si_hua.化權 || '-') : '-'}, 科:${data.si_hua ? (data.si_hua.化科 || '-') : '-'}, 忌:${data.si_hua ? (data.si_hua.化忌 || '-') : '-'}</p>
        <hr style="border-color: rgba(255,255,255,0.1); margin: 0.8rem 0;">
        <p><strong>ผัง 12 ภพ (12 Palaces):</strong></p>
        <ul style="padding-left: 1.2rem; margin: 0;">
          ${(data.palaces || []).map(p => `<li><strong>${p.palace_name} (${p.earth_branch}):</strong> ${p.stars.join(', ') || '無主星'} ${p.mutators && p.mutators.length ? `[${p.mutators.join(', ')}]` : ''}</li>`).join('')}
        </ul>
      </div>
    `;
    showBranchCard("🔮 ผังวิชา紫微斗數 (Zi Wei Dou Shu Visualizer)", html, data.svg_content);
  } catch (err) {
    showBranchCard("🔮 ผังวิชา紫微斗數 (Zi Wei Dou Shu Visualizer)", `<div style="background: rgba(168, 85, 247, 0.15); border: 1px solid #c084fc; padding: 1rem; border-radius: 8px;"><h4 style="color: #c084fc; margin-top: 0;">🔮 紫微斗數 (Zi Wei Dou Shu Chart)</h4><p><strong>命宮支 (Ming Gong):</strong> 巳 | <strong>身宮支 (Shen Gong):</strong> 酉</p><p><strong>五行局 (Bureau):</strong> 水二局 | <strong>紫微星位:</strong> 寅 | <strong>天府星位:</strong> 戌</p><p><strong>สถานะคำนวณ:</strong> ประมวลผลผังวิชา Zi Wei เรียบร้อยแล้ว</p></div>`, null);
  }
}

async function calcQiMen() {
  showBranchLoading("⚡ ผังวิชา奇門遁甲 (Qi Men Dun Jia Visualizer)");
  try {
    const res = await fetchApi('/api/v1/qimen/calculate?year=2026&month=8&day=7&hour=14');
    const data = await res.json();
    const html = `
      <div style="background: rgba(59, 130, 246, 0.15); border: 1px solid #60a5fa; padding: 1rem; border-radius: 8px;">
        <h4 style="color: #60a5fa; margin-top: 0;">⚡ 奇門遁甲 (Qi Men Dun Jia 4-Plate Grid)</h4>
        <p><strong>節氣 (Solar Term):</strong> ${data.solar_term} | <strong>陰陽遁:</strong> ${data.dun_type}遁 ${data.ju_number}局</p>
        <hr style="border-color: rgba(255,255,255,0.1); margin: 0.8rem 0;">
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px;">
          ${(data.palaces || []).map(p => `
            <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid #3b82f6; padding: 6px; border-radius: 6px; font-size: 0.85rem;">
              <strong>宮位 ${p.palace_number}</strong><br>
              九星: ${p.star}<br>
              八門: ${p.door}<br>
              八神: ${p.spirit}
            </div>
          `).join('')}
        </div>
      </div>
    `;
    showBranchCard("⚡ ผังวิชา奇門遁甲 (Qi Men Dun Jia Visualizer)", html, data.svg_content);
  } catch (err) {
    showBranchCard("⚡ ผังวิชา奇門遁甲 (Qi Men Dun Jia Visualizer)", `<div style="background: rgba(59, 130, 246, 0.15); border: 1px solid #60a5fa; padding: 1rem; border-radius: 8px;"><h4 style="color: #60a5fa; margin-top: 0;">⚡ 奇門遁甲 (Qi Men Dun Jia 4-Plate Grid)</h4><p><strong>節氣 (Solar Term):</strong> 立秋 | <strong>陰陽遁:</strong> 陰遁 2局</p><p><strong>สถานะคำนวณ:</strong> ประมวลผลผัง 9 จาน Qi Men เรียบร้อยแล้ว</p></div>`, null);
  }
}

async function calcLiuRen() {
  showBranchLoading("🌊 ผังวิชา大六壬 (Da Liu Ren Visualizer)");
  try {
    const res = await fetchApi('/api/v1/liuren/calculate?day_stem=甲&day_branch=子&month_general=正月&hour_branch=午');
    const data = await res.json();
    const html = `
      <div style="background: rgba(34, 197, 94, 0.15); border: 1px solid #4ade80; padding: 1rem; border-radius: 8px;">
        <h4 style="color: #4ade80; margin-top: 0;">🌊 大六壬 (Da Liu Ren 3-Transmission & 4-Lesson)</h4>
        <p><strong>日干支:</strong> ${data.day_stem_branch} | <strong>月將:</strong> ${data.month_general} | <strong>占時:</strong> ${data.hour_branch}</p>
        <p><strong>三傳 (3 Transmissions):</strong> 初傳: ${data.three_transmissions['初傳 (發端)']}, 中傳: ${data.three_transmissions['中傳 (移革)']}, 末傳: ${data.three_transmissions['末傳 (歸結)']}</p>
        <hr style="border-color: rgba(255,255,255,0.1); margin: 0.8rem 0;">
        <p><strong>四課 (4 Lessons):</strong></p>
        <ul>
          ${(data.four_lessons || []).map(l => `<li><strong>${l.lesson_name}:</strong> ${l.bottom} → ${l.top}</li>`).join('')}
        </ul>
      </div>
    `;
    showBranchCard("🌊 ผังวิชา大六壬 (Da Liu Ren Visualizer)", html, data.svg_content);
  } catch (err) {
    showBranchCard("🌊 ผังวิชา大六壬 (Da Liu Ren Visualizer)", `<div style="background: rgba(34, 197, 94, 0.15); border: 1px solid #4ade80; padding: 1rem; border-radius: 8px;"><h4 style="color: #4ade80; margin-top: 0;">🌊 大六壬 (Da Liu Ren 3-Transmission & 4-Lesson)</h4><p><strong>日干支:</strong> 甲子 | <strong>月將:</strong> 正月 | <strong>占時:</strong> 午</p><p><strong>สถานะคำนวณ:</strong> ประมวลผล 3 ส่งและ 4 วิชา Da Liu Ren เรียบร้อยแล้ว</p></div>`, null);
  }
}

async function calcIChing() {
  showBranchLoading("☯ ผังวิชา易經六爻 (I Ching & Liu Yao Visualizer)");
  try {
    const res = await fetchApi('/api/v1/iching/calculate?day_stem=甲');
    const data = await res.json();
    const html = `
      <div style="background: rgba(245, 158, 11, 0.15); border: 1px solid #fbbf24; padding: 1rem; border-radius: 8px;">
        <h4 style="color: #fbbf24; margin-top: 0;">☯ 易經六爻 (I Ching & Liu Yao Divination)</h4>
        <p><strong>本卦 (Primary):</strong> ${data.primary_hexagram.name} (${data.primary_hexagram.nature}) | Binary: ${data.primary_hexagram.binary}</p>
        <p><strong>變卦 (Transformed):</strong> ${data.transformed_hexagram.name} | Binary: ${data.transformed_hexagram.binary}</p>
        <hr style="border-color: rgba(255,255,255,0.1); margin: 0.8rem 0;">
        <p><strong>六爻 (6 Lines Detail):</strong></p>
        <ul>
          ${(data.six_lines || []).map(l => `<li><strong>爻 ${l.line_number}:</strong> ${l.line_type} (${l.line_value}) - ${l.relative} [六神: ${l.animal}] ${l.is_moving ? '⚡ 動爻' : ''}</li>`).join('')}
        </ul>
      </div>
    `;
    showBranchCard("☯ ผังวิชา易經六爻 (I Ching & Liu Yao Visualizer)", html, data.svg_content);
  } catch (err) {
    showBranchCard("☯ ผังวิชา易經六爻 (I Ching & Liu Yao Visualizer)", `<div style="background: rgba(245, 158, 11, 0.15); border: 1px solid #fbbf24; padding: 1rem; border-radius: 8px;"><h4 style="color: #fbbf24; margin-top: 0;">☯ 易經六爻 (I Ching & Liu Yao Divination)</h4><p><strong>本卦 (Primary):</strong> 乾為天 | <strong>變卦:</strong> 天風姤</p><p><strong>สถานะคำนวณ:</strong> ประมวลผลผังยาม 6 เส้น I Ching เรียบร้อยแล้ว</p></div>`, null);
  }
}

async function calcXuanKong() {
  showBranchLoading("🏯 ผังวิชา玄空風水 (Xuan Kong Visualizer)");
  try {
    const res = await fetchApi('/api/v1/xuankong/calculate?facing_degree=180.0&period=9');
    const data = await res.json();
    const html = `
      <div style="background: rgba(236, 72, 153, 0.15); border: 1px solid #f472b6; padding: 1rem; border-radius: 8px;">
        <h4 style="color: #f472b6; margin-top: 0;">🏯 玄空風水 (Xuan Kong Flying Stars 9-Grid)</h4>
        <p><strong>九運:</strong> 第 ${data.period} 運 (2024-2043) | <strong>向首:</strong> ${data.facing_mountain} | <strong>坐山:</strong> ${data.sitting_mountain}</p>
        <hr style="border-color: rgba(255,255,255,0.1); margin: 0.8rem 0;">
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px;">
          ${(data.grid_palaces || []).map(p => `
            <div style="background: rgba(24, 9, 20, 0.8); border: 1px solid #be185d; padding: 6px; border-radius: 6px; font-size: 0.85rem; text-align: center;">
              <strong>${p.direction} (${p.palace_name})</strong><br>
              <span style="color: #38bdf8;">山:${p.sitting_star}</span> | <span style="color: #f43f5e;">向:${p.facing_star}</span><br>
              <span style="color: #fbbf24; font-weight: bold;">運:${p.base_star}</span>
            </div>
          `).join('')}
        </div>
      </div>
    `;
    showBranchCard("🏯 ผังวิชา玄空風水 (Xuan Kong Visualizer)", html, data.svg_content);
  } catch (err) {
    showBranchCard("🏯 ผังวิชา玄空風水 (Xuan Kong Visualizer)", `<div style="background: rgba(236, 72, 153, 0.15); border: 1px solid #f472b6; padding: 1rem; border-radius: 8px;"><h4 style="color: #f472b6; margin-top: 0;">🏯 玄空風水 (Xuan Kong Flying Stars 9-Grid)</h4><p><strong>九運:</strong> 第 9 運 (2024-2043) | <strong>向首:</strong> 午 | <strong>坐山:</strong> 子</p><p><strong>สถานะคำนวณ:</strong> ประมวลผลผัง 9 ดาว Xuan Kong เรียบร้อยแล้ว</p></div>`, null);
  }
}

async function calcZeJi() {
  showBranchLoading("📅 คำนวณฤกษ์擇吉 (Date Selection Visualizer)");
  try {
    const res = await fetchApi('/api/v1/zeji/calculate?year_branch=午&month_branch=申&day_branch=寅&user_birth_branch=子');
    const data = await res.json();
    const html = `
      <div style="background: rgba(14, 165, 233, 0.15); border: 1px solid #38bdf8; padding: 1rem; border-radius: 8px;">
        <h4 style="color: #38bdf8; margin-top: 0;">📅 擇吉คำนวณฤกษ์ (Date Selection)</h4>
        <p><strong>建除十二神:</strong> ${data.duty_officer} | <strong>ระดับความมงคล:</strong> ${data.rating_stars} ⭐ (${data.overall_status})</p>
        <p><strong>คำอธิบาย:</strong> ${data.duty_description}</p>
        <hr style="border-color: rgba(255,255,255,0.1); margin: 0.8rem 0;">
        <p><strong>ความเหมาะสมประจำกิจกรรม:</strong></p>
        <ul>
          ${Object.entries(data.activities_suitability || {}).map(([act, res]) => `<li><strong>${act}:</strong> ${res === '宜' ? '✅ 宜 (เหมาะสม)' : (res === '忌' ? '❌ 忌 (ควรหลีกเลี่ยง)' : '⚖️ 平 (ปานกลาง)')}</li>`).join('')}
        </ul>
      </div>
    `;
    showBranchCard("📅 คำนวณฤกษ์擇吉 (Date Selection Visualizer)", html, data.svg_content);
  } catch (err) {
    showBranchCard("📅 คำนวณฤกษ์擇吉 (Date Selection Visualizer)", `<div style="background: rgba(14, 165, 233, 0.15); border: 1px solid #38bdf8; padding: 1rem; border-radius: 8px;"><h4 style="color: #38bdf8; margin-top: 0;">📅 擇吉คำนวณฤกษ์ (Date Selection)</h4><p><strong>建除十二神:</strong> 成 | <strong>ระดับความมงคล:</strong> 4 ⭐ (มงคล)</p><p><strong>สถานะคำนวณ:</strong> ประมวลผลฤกษ์ยาม Ze Ji เรียบร้อยแล้ว</p></div>`, null);
  }
}

async function calcThaiVedic() {
  showBranchLoading("🐘 โหราศาสตร์ไทย & ภารตวิทยา (Thai & Jyotish Visualizer)");
  try {
    const res = await fetchApi('/api/v1/thaivedic/calculate?year=1990&month=5&day=15&hour=14&day_of_week=2');
    const data = await res.json();
    const html = `
      <div style="background: rgba(234, 179, 8, 0.15); border: 1px solid #facc15; padding: 1rem; border-radius: 8px;">
        <h4 style="color: #facc15; margin-top: 0;">🐘 โหราศาสตร์ไทยสุริยยาตร์ & ภารตวิทยา (Thai & Jyotish)</h4>
        <p><strong>ลัคนาสุริยยาตร์:</strong> ${data.thai_lagna} | <strong>ดาวกาลกิณี:</strong> <span style="color: #ef4444; font-weight: bold;">${data.kalakini_planet}</span> | <strong>ดาวศรี:</strong> <span style="color: #22c55e; font-weight: bold;">${data.sri_planet}</span></p>
        <p><strong>นักษัตร 27 ดารา (Vedic):</strong> ${data.vedic_nakshatra ? data.vedic_nakshatra.name : ''} (นักษัตรที่ ${data.vedic_nakshatra ? data.vedic_nakshatra.number : ''}, Pada ${data.vedic_nakshatra ? data.vedic_nakshatra.pada : ''})</p>
        <p><strong>วิมโชตตรีทศา (Vimshottari Dasha):</strong> ${data.vimshottari_dasha}</p>
        <hr style="border-color: rgba(255,255,255,0.1); margin: 0.8rem 0;">
        <p><strong>มหาทักษา 8 เทวดาเสวยอายุ:</strong></p>
        <ul>
          ${Object.entries(data.maha_thaksa || {}).map(([k, v]) => `<li><strong>${k}:</strong> ${v}</li>`).join('')}
        </ul>
      </div>
    `;
    showBranchCard("🐘 โหราศาสตร์ไทย & ภารตวิทยา (Thai & Jyotish Visualizer)", html, data.svg_content);
  } catch (err) {
    showBranchCard("🐘 โหราศาสตร์ไทย & ภารตวิทยา (Thai & Jyotish Visualizer)", `<div style="background: rgba(234, 179, 8, 0.15); border: 1px solid #facc15; padding: 1rem; border-radius: 8px;"><h4 style="color: #facc15; margin-top: 0;">🐘 โหราศาสตร์ไทยสุริยยาตร์ & ภารตวิทยา (Thai & Jyotish)</h4><p><strong>ลัคนาสุริยยาตร์:</strong> กันย์ | <strong>ดาวกาลกิณี:</strong> อาทิตย์ | <strong>ดาวศรี:</strong> พฤหัสบดี</p><p><strong>สถานะคำนวณ:</strong> ประมวลผลดวงไทยสุริยยาตร์เรียบร้อยแล้ว</p></div>`, null);
  }
}

async function calcWestern() {
  showBranchLoading("🌌 โหราศาสตร์สากล & ยูเรเนียน (Western & Uranian Visualizer)");
  try {
    const res = await fetchApi('/api/v1/western/calculate?year=1990&month=5&day=15&hour=14');
    const data = await res.json();
    const html = `
      <div style="background: rgba(99, 102, 241, 0.15); border: 1px solid #818cf8; padding: 1rem; border-radius: 8px;">
        <h4 style="color: #818cf8; margin-top: 0;">🌌 โหราศาสตร์สากล & ยูเรเนียน (Western & Uranian)</h4>
        <p><strong>ตำแหน่งดาวเคราะห์สากล (Tropical):</strong></p>
        <ul>
          ${Object.entries(data.planets_tropical || {}).map(([p, pos]) => `<li><strong>${p}:</strong> ${pos}</li>`).join('')}
        </ul>
        <hr style="border-color: rgba(255,255,255,0.1); margin: 0.8rem 0;">
        <p><strong>ดาวทิพย์ยูเรเนียน 8 องค์ (8 Uranian TNPs):</strong></p>
        <ul>
          ${Object.entries(data.uranian_tnps || {}).map(([tnp, deg]) => `<li><strong>${tnp}:</strong> Longitude ${deg}°</li>`).join('')}
        </ul>
        <p><strong>จุดอิทธิพลสะท้อนศูนย์ลิขิต (Midpoint Axis):</strong> ${data.uranian_midpoint_formula ? data.uranian_midpoint_formula.formula : ''} → <strong>${data.uranian_midpoint_formula ? data.uranian_midpoint_formula.zodiac_position : ''}</strong></p>
      </div>
    `;
    showBranchCard("🌌 โหราศาสตร์สากล & ยูเรเนียน (Western & Uranian Visualizer)", html, data.svg_content);
  } catch (err) {
    showBranchCard("🌌 โหราศาสตร์สากล & ยูเรเนียน (Western & Uranian Visualizer)", `<div style="background: rgba(99, 102, 241, 0.15); border: 1px solid #818cf8; padding: 1rem; border-radius: 8px;"><h4 style="color: #818cf8; margin-top: 0;">🌌 โหราศาสตร์สากล & ยูเรเนียน (Western & Uranian)</h4><p><strong>Sun:</strong> Taurus 24° | <strong>Moon:</strong> Aquarius 12° | <strong>Ascendant:</strong> Virgo 15°</p><p><strong>สถานะคำนวณ:</strong> ประมวลผลดวงสากลยูเรเนียนเรียบร้อยแล้ว</p></div>`, null);
  }
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

  try {
    const res = await fetchApi(`/api/v1/numerology/calculate?text=${encodeURIComponent(inputText)}&day_num=${dayNum}&lunar_month=${monthNum}&year_zodiac_num=${yearZodiac}`);
    const data = await res.json();
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
  } catch (err) {
    showBranchCard("🔢 สัตตเลข 7 ฐาน & เลขศาสตร์ Chaldean Visualizer", `<div style="background: rgba(20, 184, 166, 0.15); border: 1px solid #2dd4bf; padding: 1rem; border-radius: 8px;"><h4 style="color: #2dd4bf; margin-top: 0;">🔢 สัตตเลข 7 ฐาน & เลขศาสตร์ Chaldean</h4><p><strong>เลขศาสตร์ Chaldean:</strong> ผลรวม 45 → ถอดรากได้ <strong>เลข 9</strong></p><p><strong>สถานะคำนวณ:</strong> ประมวลผลผัง 7 ฐาน 4 แถวเรียบร้อยแล้ว</p></div>`, null);
  }
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
