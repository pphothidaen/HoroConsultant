/* ===========================================================================
   Computational Metaphysics Engine — Dashboard Frontend Script (app.js)
   =========================================================================== */

function loadPreset(datetime, lng, utc, label) {
  document.getElementById('birth_datetime').value = datetime;
  document.getElementById('longitude').value = lng;
  document.getElementById('utc_offset_hours').value = utc;
  console.log(`Loaded preset: ${label}`);
}

async function resolveLocation() {
  const locInput = document.getElementById('location_search').value.trim();
  if (!locInput) return;
  
  const statusEl = document.getElementById('location-status');
  const spinner = document.getElementById('loc-spinner');
  
  spinner.classList.remove('hidden');
  statusEl.textContent = "กำลังค้นหาพิกัด...";
  statusEl.style.color = "#94a3b8";
  
  try {
    const res = await fetch('/api/v1/location/resolve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ location: locInput })
    });
    
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || "ไม่พบสถานที่ดังกล่าว โปรดลองพิมพ์ชื่อให้ชัดเจนขึ้น");
    }
    
    const data = await res.json();
    document.getElementById('longitude').value = data.longitude.toFixed(4);
    document.getElementById('utc_offset_hours').value = data.utc_offset_hours;
    
    const offsetSign = data.utc_offset_hours >= 0 ? '+' : '';
    statusEl.textContent = `✅ ${data.location} (UTC${offsetSign}${data.utc_offset_hours})`;
    statusEl.style.color = "#10b981";
  } catch (err) {
    statusEl.textContent = `❌ ${err.message}`;
    statusEl.style.color = "#ef4444";
  } finally {
    spinner.classList.add('hidden');
  }
}

document.addEventListener("DOMContentLoaded", () => {
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
  const btnText = submitBtn.querySelector('.btn-text');
  const spinner = submitBtn.querySelector('.spinner');

  btnText.textContent = '⚡️ กำลังคำนวณผังดวง & ตีความ...';
  submitBtn.disabled = true;

  const payload = {
    birth_datetime: document.getElementById('birth_datetime').value,
    longitude: parseFloat(document.getElementById('longitude').value),
    utc_offset_hours: parseFloat(document.getElementById('utc_offset_hours').value),
    unknown_hour: document.getElementById('unknown_hour').checked,
    enable_validation: document.getElementById('enable_validation').checked,
    query: document.getElementById('query').value
  };

  try {
    const res = await fetch('/api/v1/bazi/interpret', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      throw new Error(`HTTP error ${res.status}`);
    }

    const data = await res.json();
    renderResults(data);
  } catch (err) {
    alert(`เกิดข้อผิดพลาดในการเรียก API: ${err.message}`);
  } finally {
    btnText.textContent = '☯ คำนวณผังดวง & ตีความด้วย AI';
    submitBtn.disabled = false;
  }
}

function renderResults(data) {
  const chart = data.chart;
  
  // Show Cards
  document.getElementById('pillars-card').classList.remove('hidden');
  document.getElementById('elements-card').classList.remove('hidden');
  document.getElementById('interpretation-card').classList.remove('hidden');

  // Render 4 Pillars
  const pillarsGrid = document.getElementById('pillars-grid');
  const pillars = chart.pillars || {};
  const order = ['year', 'month', 'day', 'hour'];
  const titles = { year: 'เสาปี (Year)', month: 'เสาเดือน (Month)', day: 'เสาวัน (Day)', hour: 'เสายาม (Hour)' };

  pillarsGrid.innerHTML = '';
  order.forEach(key => {
    const p = pillars[key] || {};
    const stem = p.stem || {};
    const branch = p.branch || {};
    
    const col = document.createElement('div');
    col.className = 'pillar-col';
    col.innerHTML = `
      <div class="pillar-title">${titles[key]}</div>
      
      <div class="char-box stem-box">
        <span class="cn-char">${stem.char || '?'}</span>
        <span class="th-name">${stem.pinyin || ''} (${stem.element || ''})</span>
        <div class="element-tag tag-${stem.element}">${stem.polarity || ''} ${stem.element || ''}</div>
      </div>
      
      <div class="char-box branch-box">
        <span class="cn-char">${branch.char || '?'}</span>
        <span class="th-name">${branch.pinyin || ''} (${branch.zodiac || ''})</span>
        <div class="element-tag tag-${branch.element}">${branch.element || ''}</div>
      </div>
    `;
    pillarsGrid.appendChild(col);
  });

  // Day Master Banner
  const dm = chart.day_master || {};
  document.getElementById('day-master-banner').innerHTML = 
    `🌟 Day Master (ธาตุเจ้าตัว): ${dm.stem} (${dm.element} ${dm.polarity} / ${dm.pinyin})`;

  // Render 5 Elements Progress Bars
  const elementsBars = document.getElementById('elements-bars');
  const pcts = (chart.five_elements && chart.five_elements.percentages) || {};
  const elements = ['Wood', 'Fire', 'Earth', 'Metal', 'Water'];
  const thNames = { Wood: 'ไม้ (木)', Fire: 'ไฟ (火)', Earth: 'ดิน (土)', Metal: 'ทอง (金)', Water: 'น้ำ (水)' };

  elementsBars.innerHTML = '';
  elements.forEach(el => {
    const pct = (pcts[el] || 0).toFixed(1);
    const row = document.createElement('div');
    row.className = 'element-row';
    row.innerHTML = `
      <span class="element-name">${thNames[el]}</span>
      <div class="progress-track">
        <div class="progress-fill fill-${el}" style="width: ${pct}%"></div>
      </div>
      <span class="element-pct">${pct}%</span>
    `;
    elementsBars.appendChild(row);
  });

  // Render Interpretation Text
  document.getElementById('reading-body').innerText = data.interpretation || 'ไม่มีข้อมูลตีความ';
  document.getElementById('route-badge').textContent = `Route: ${data.route || 'local'} (${data.latency_ms || 0}ms)`;

  // Render Validator Report
  const valBody = document.getElementById('validator-body');
  if (data.validation_report) {
    const val = data.validation_report;
    valBody.innerHTML = `
      <div class="validator-box">
        <h4>🛡️ Gemini Prediction Validator Report</h4>
        <p><strong>Status:</strong> ${val.validation_status} (Confidence: ${val.confidence_score})</p>
        <p><strong>Peer Perspective:</strong> ${val.peer_perspective || '-'}</p>
        <p><strong>Element Logic Audit:</strong> ${val.element_logic_audit || '-'}</p>
        <div style="margin-top: 0.5rem;">
          <strong>Refined Interpretation:</strong>
          <p style="white-space: pre-line;">${val.refined_interpretation || '-'}</p>
        </div>
      </div>
    `;
  } else {
    valBody.innerHTML = '<p>ไม่ได้เปิดใช้งาน Gemini Validator สำหรับการคำนวณนี้</p>';
  }

  // Render RAG References
  document.getElementById('rag-body').innerHTML = `
    <p>📚 <strong>FAISS RAG Knowledge Base:</strong> 3,132 Vector Chunks Indexed (ZiPing ZhenQuan, DiTianSui, 38 Thai Astrology Books)</p>
    <p>คำตอบนี้ผสมผสานการค้นหาเชิงความหมายจาก FAISS ร่วมกับ Local Model qwen2.5-bazi</p>
  `;
}

function switchTab(tabId) {
  document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(c => c.classList.add('hidden'));

  event.target.classList.add('active');
  document.getElementById(tabId).classList.remove('hidden');
}

/* ---------------------------------------------------------------------------
   5 Metaphysics Branches Helper Handlers & Web UI Visualizer
   --------------------------------------------------------------------------- */
function showBranchCard(title, contentHtml) {
  const card = document.getElementById('branch-result-card');
  const titleEl = document.getElementById('branch-title');
  const bodyEl = document.getElementById('branch-body');
  
  if (card && titleEl && bodyEl) {
    titleEl.innerHTML = title;
    bodyEl.innerHTML = contentHtml;
    card.classList.remove('hidden');
    card.scrollIntoView({ behavior: 'smooth' });
  }
}

async function calcZiWei() {
  const res = await fetch('/api/v1/ziwei/calculate?year=1990&month=5&day=15&hour=14&gender=male');
  const data = await res.json();
  const html = `
    <div style="background: rgba(168, 85, 247, 0.15); border: 1px solid #c084fc; padding: 1rem; border-radius: 8px;">
      <h4 style="color: #c084fc; margin-top: 0;">🔮 紫微斗數 (Zi Wei Dou Shu Chart)</h4>
      <p><strong>命宮支 (Ming Gong):</strong> ${data.ming_gong_branch} | <strong>身宮支 (Shen Gong):</strong> ${data.shen_gong_branch}</p>
      <p><strong>五行局 (Bureau):</strong> ${data.five_element_bureau} | <strong>紫微星位:</strong> ${data.zi_wei_star_branch} | <strong>天府星位:</strong> ${data.tian_fu_star_branch}</p>
      <p><strong>四化 (Si Hua):</strong> 祿:${data.si_hua.化祿 || '-'}, 權:${data.si_hua.化權 || '-'}, 科:${data.si_hua.化科 || '-'}, 忌:${data.si_hua.化忌 || '-'}</p>
      <hr style="border-color: rgba(255,255,255,0.1); margin: 0.8rem 0;">
      <p><strong>ผัง 12 ภพ (12 Palaces):</strong></p>
      <ul style="padding-left: 1.2rem; margin: 0;">
        ${data.palaces.map(p => `<li><strong>${p.palace_name} (${p.earth_branch}):</strong> ${p.stars.join(', ') || '無主星'} ${p.mutators.length ? `[${p.mutators.join(', ')}]` : ''}</li>`).join('')}
      </ul>
    </div>
  `;
  showBranchCard("🔮 ผังวิชา紫微斗數 (Zi Wei Dou Shu Visualizer)", html);
}

async function calcQiMen() {
  const res = await fetch('/api/v1/qimen/calculate?year=2026&month=8&day=7&hour=14');
  const data = await res.json();
  const html = `
    <div style="background: rgba(59, 130, 246, 0.15); border: 1px solid #60a5fa; padding: 1rem; border-radius: 8px;">
      <h4 style="color: #60a5fa; margin-top: 0;">⚡ 奇門遁甲 (Qi Men Dun Jia 4-Plate Grid)</h4>
      <p><strong>節氣 (Solar Term):</strong> ${data.solar_term} | <strong>陰陽遁:</strong> ${data.dun_type}遁 ${data.ju_number}局</p>
      <hr style="border-color: rgba(255,255,255,0.1); margin: 0.8rem 0;">
      <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px;">
        ${data.palaces.map(p => `
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
  showBranchCard("⚡ ผังวิชา奇門遁甲 (Qi Men Dun Jia Visualizer)", html);
}

async function calcLiuRen() {
  const res = await fetch('/api/v1/liuren/calculate?day_stem=甲&day_branch=子&month_general=正月&hour_branch=午');
  const data = await res.json();
  const html = `
    <div style="background: rgba(34, 197, 94, 0.15); border: 1px solid #4ade80; padding: 1rem; border-radius: 8px;">
      <h4 style="color: #4ade80; margin-top: 0;">🌊 大六壬 (Da Liu Ren 3-Transmission & 4-Lesson)</h4>
      <p><strong>日干支:</strong> ${data.day_stem_branch} | <strong>月將:</strong> ${data.month_general} | <strong>占時:</strong> ${data.hour_branch}</p>
      <p><strong>三傳 (3 Transmissions):</strong> 初傳: ${data.three_transmissions['初傳 (發端)']}, 中傳: ${data.three_transmissions['中傳 (移革)']}, 末傳: ${data.three_transmissions['末傳 (歸結)']}</p>
      <hr style="border-color: rgba(255,255,255,0.1); margin: 0.8rem 0;">
      <p><strong>四課 (4 Lessons):</strong></p>
      <ul>
        ${data.four_lessons.map(l => `<li><strong>${l.lesson_name}:</strong> ${l.bottom} → ${l.top}</li>`).join('')}
      </ul>
    </div>
  `;
  showBranchCard("🌊 ผังวิชา大六壬 (Da Liu Ren Visualizer)", html);
}

async function calcIChing() {
  const res = await fetch('/api/v1/iching/calculate?day_stem=甲');
  const data = await res.json();
  const html = `
    <div style="background: rgba(245, 158, 11, 0.15); border: 1px solid #fbbf24; padding: 1rem; border-radius: 8px;">
      <h4 style="color: #fbbf24; margin-top: 0;">☯ 易經六爻 (I Ching & Liu Yao Divination)</h4>
      <p><strong>本卦 (Primary):</strong> ${data.primary_hexagram.name} (${data.primary_hexagram.nature}) | Binary: ${data.primary_hexagram.binary}</p>
      <p><strong>變卦 (Transformed):</strong> ${data.transformed_hexagram.name} | Binary: ${data.transformed_hexagram.binary}</p>
      <hr style="border-color: rgba(255,255,255,0.1); margin: 0.8rem 0;">
      <p><strong>六爻 (6 Lines Detail):</strong></p>
      <ul>
        ${data.six_lines.map(l => `<li><strong>爻 ${l.line_number}:</strong> ${l.line_type} (${l.line_value}) - ${l.relative} [六神: ${l.animal}] ${l.is_moving ? '⚡ 動爻' : ''}</li>`).join('')}
      </ul>
    </div>
  `;
  showBranchCard("☯ ผังวิชา易經六爻 (I Ching & Liu Yao Visualizer)", html);
}

async function calcXuanKong() {
  const res = await fetch('/api/v1/xuankong/calculate?facing_degree=180.0&period=9');
  const data = await res.json();
  const html = `
    <div style="background: rgba(236, 72, 153, 0.15); border: 1px solid #f472b6; padding: 1rem; border-radius: 8px;">
      <h4 style="color: #f472b6; margin-top: 0;">🏯 玄空風水 (Xuan Kong Flying Stars 9-Grid)</h4>
      <p><strong>九運:</strong> 第 ${data.period} 運 (2024-2043) | <strong>向首:</strong> ${data.facing_mountain} | <strong>坐山:</strong> ${data.sitting_mountain}</p>
      <hr style="border-color: rgba(255,255,255,0.1); margin: 0.8rem 0;">
      <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px;">
        ${data.grid_palaces.map(p => `
          <div style="background: rgba(24, 9, 20, 0.8); border: 1px solid #be185d; padding: 6px; border-radius: 6px; font-size: 0.85rem; text-align: center;">
            <strong>${p.direction} (${p.palace_name})</strong><br>
            <span style="color: #38bdf8;">山:${p.sitting_star}</span> | <span style="color: #f43f5e;">向:${p.facing_star}</span><br>
            <span style="color: #fbbf24; font-weight: bold;">運:${p.base_star}</span>
          </div>
        `).join('')}
      </div>
    </div>
  `;
  showBranchCard("🏯 ผังวิชา玄空風水 (Xuan Kong Visualizer)", html);
}

async function calcZeJi() {
  const res = await fetch('/api/v1/zeji/calculate?year_branch=午&month_branch=申&day_branch=寅&user_birth_branch=子');
  const data = await res.json();
  const html = `
    <div style="background: rgba(14, 165, 233, 0.15); border: 1px solid #38bdf8; padding: 1rem; border-radius: 8px;">
      <h4 style="color: #38bdf8; margin-top: 0;">📅 擇吉คำนวณฤกษ์ (Date Selection)</h4>
      <p><strong>建除十二神:</strong> ${data.duty_officer} | <strong>ระดับความมงคล:</strong> ${data.rating_stars} ⭐ (${data.overall_status})</p>
      <p><strong>คำอธิบาย:</strong> ${data.duty_description}</p>
      <hr style="border-color: rgba(255,255,255,0.1); margin: 0.8rem 0;">
      <p><strong>ความเหมาะสมประจำกิจกรรม:</strong></p>
      <ul>
        ${Object.entries(data.activities_suitability).map(([act, res]) => `<li><strong>${act}:</strong> ${res === '宜' ? '✅ 宜 (เหมาะสม)' : (res === '忌' ? '❌ 忌 (ควรหลีกเลี่ยง)' : '⚖️ 平 (ปานกลาง)')}</li>`).join('')}
      </ul>
    </div>
  `;
  showBranchCard("📅 คำนวณฤกษ์擇吉 (Date Selection Visualizer)", html);
}
