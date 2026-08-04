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
