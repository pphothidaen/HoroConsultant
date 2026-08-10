async function fetchApi(endpoint, options = {}) {
  return fetch(endpoint, options);
}

const BACKEND_WAKE_DELAYS_MS = [1000, 2000, 4000, 8000, 10000];
const BACKEND_WAKE_LIMIT_MS = 60000;
let backendWakePromise = null;

function setBackendStatus(message, state = 'idle') {
  const statusEl = document.getElementById('backend-status');
  if (!statusEl) return;
  statusEl.textContent = message;
  statusEl.dataset.state = state;
}

function setRetryVisible(visible) {
  const retryButton = document.getElementById('backend-retry');
  if (retryButton) retryButton.classList.toggle('hidden', !visible);
}

function sleep(delayMs) {
  return new Promise(resolve => window.setTimeout(resolve, delayMs));
}

function createCorrelationId() {
  if (window.crypto && typeof window.crypto.randomUUID === 'function') {
    return window.crypto.randomUUID();
  }
  return `ui-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

function safeApiDetail(value) {
  if (typeof value !== 'string' || !value.trim()) return 'The API request could not be completed.';
  if (/https?:\/\/|localhost|traceback|exception|stack trace/i.test(value)) {
    return 'The API request could not be completed.';
  }
  return value.trim().slice(0, 240);
}

async function wakeBackend(options = {}) {
  const delays = options.delays || BACKEND_WAKE_DELAYS_MS;
  const deadlineMs = options.deadlineMs || BACKEND_WAKE_LIMIT_MS;
  const now = options.now || Date.now;
  const waitFor = options.waitFor || sleep;
  const correlationId = options.correlationId || createCorrelationId();
  const startedAt = now();
  let delayIndex = 0;
  setRetryVisible(false);
  setBackendStatus('Starting the API. This can take up to one minute.', 'waking');

  while (now() - startedAt < deadlineMs) {
    const remaining = deadlineMs - (now() - startedAt);
    if (remaining <= 0) break;
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), remaining);
    try {
      const response = await fetchApi('/health', {
        cache: 'no-store',
        signal: controller.signal,
        headers: { 'X-Request-ID': correlationId },
      });
      if (response.ok) {
        setBackendStatus('API is ready. AI is processing your request.', 'processing');
        return true;
      }
    } catch (error) {
      if (controller.signal.aborted) break;
      console.warn('[WARNING] API readiness probe failed:', error);
    } finally {
      window.clearTimeout(timeoutId);
    }

    const elapsed = now() - startedAt;
    const remainingAfterProbe = deadlineMs - elapsed;
    if (remainingAfterProbe <= 0) break;
    const delay = Math.min(delays[Math.min(delayIndex, delays.length - 1)], remainingAfterProbe);
    delayIndex += 1;
    setBackendStatus(`Starting the API. Checking again in ${Math.ceil(delay / 1000)} seconds.`, 'waking');
    await waitFor(delay);
  }

  setBackendStatus('The API did not become ready within one minute. Your form is unchanged; try again when it is available.', 'unavailable');
  setRetryVisible(true);
  return false;
}

async function ensureBackendReady(correlationId) {
  if (!backendWakePromise) {
    backendWakePromise = wakeBackend({ correlationId }).finally(() => {
      backendWakePromise = null;
    });
  }
  return backendWakePromise;
}

async function getApiError(response) {
  let message = 'The API request could not be completed.';
  let correlationId = response.headers.get('x-request-id') || '';
  try {
    const data = await response.json();
    message = safeApiDetail(data.detail || data.message);
    correlationId = data.correlation_id || correlationId;
  } catch (error) {
    // Keep the stable public message when an upstream error body is not JSON.
  }
  const apiError = new Error(message);
  apiError.correlationId = correlationId;
  return apiError;
}

async function fetchApiJson(endpoint, options = {}) {
  const response = await fetchApi(endpoint, options);
  if (!response.ok) throw await getApiError(response);
  return response.json();
}


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
    throw await getApiError(res);
  } catch (err) {
    console.warn('[WARNING] Location resolution failed:', err);
    statusEl.textContent = `ไม่สามารถค้นหาพิกัดได้: ${err.message}`;
    statusEl.style.color = "#ef4444";
  } finally {
    spinner.classList.add('hidden');
  }
}

async function updateVersionFooter() {
  try {
    const startTime = performance.now();
    const res = await fetchApi('/health').catch(() => null);
    const latency = Math.round(performance.now() - startTime);
    const healthBadge = document.getElementById('health-status-badge');

    if (res && res.ok) {
      const data = await res.json();
      const rawVer = data.version || (data.git_commit ? `1.0.0.${data.git_commit.slice(0, 7)}` : '1.0.0');
      const versionStr = rawVer.startsWith('v') ? rawVer : `v${rawVer}`;
      const footerEl = document.getElementById('footer-version-text');
      if (footerEl && versionStr) {
        footerEl.textContent = `Computational Metaphysics Engine ${versionStr} — Azure API gateway`;
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
        healthBadge.innerHTML = `<span class="pulse-dot amber"></span><span class="health-text">Health: API unavailable</span>`;
      }
    }
  } catch (err) {
    console.warn('Could not update dynamic version footer:', err);
    const healthBadge = document.getElementById('health-status-badge');
    if (healthBadge) {
      healthBadge.className = 'status-badge health-badge amber-badge';
      healthBadge.innerHTML = `<span class="pulse-dot amber"></span><span class="health-text">Health: API unavailable</span>`;
    }
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
  if (event) event.preventDefault();
  
  const submitBtn = document.getElementById('btn-submit');
  const btnText = submitBtn.querySelector('.btn-text');
  btnText.textContent = 'Starting API...';
  submitBtn.disabled = true;

  const payload = {
    birth_datetime: document.getElementById('birth_datetime').value,
    longitude: parseFloat(document.getElementById('longitude').value),
    utc_offset_hours: parseFloat(document.getElementById('utc_offset_hours').value),
    unknown_hour: document.getElementById('unknown_hour').checked,
    enable_validation: document.getElementById('enable_validation').checked,
    query: document.getElementById('query').value
  };

  const correlationId = createCorrelationId();

  try {
    const ready = await ensureBackendReady(correlationId);
    if (!ready) return;

    btnText.textContent = 'AI is processing your request...';
    setBackendStatus('API is ready. AI is processing your request.', 'processing');
    const res = await fetchApi('/api/v1/bazi/interpret', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Request-ID': correlationId,
      },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      throw await getApiError(res);
    }

    const data = await res.json();
    renderResults(data, data.svg_content || (data.chart && data.chart.svg_content));
    setBackendStatus('API is ready. AI processing completed.', 'complete');
  } catch (err) {
    console.error('[ERROR] Calculation request failed:', err);
    const correlationNote = err.correlationId ? ` Correlation ID: ${err.correlationId}.` : '';
    setBackendStatus(`AI request failed: ${safeApiDetail(err.message)}.${correlationNote} Your form is unchanged.`, 'error');
    setRetryVisible(true);
  } finally {
    btnText.textContent = '🔮 คำนวณผังดวง & ตีความด้วย AI';
    submitBtn.disabled = false;
  }
}

function retryChartCalculation() {
  calculateChart();
}

function renderResults(data, svgContent) {
  const svgCard = document.getElementById('svg-chart-card');
  const pillarsCard = document.getElementById('pillars-card');
  const elementsCard = document.getElementById('elements-card');
  const interpCard = document.getElementById('interpretation-card');

  if (svgCard) svgCard.classList.remove('hidden');
  if (pillarsCard) pillarsCard.classList.remove('hidden');
  if (elementsCard) elementsCard.classList.remove('hidden');
  if (interpCard) interpCard.classList.remove('hidden');

  const mainContainer = document.getElementById('results-container');
  if (mainContainer) mainContainer.classList.remove('hidden');

  // 1. Render SVG Chart
  const chartWrapper = document.getElementById('svg-chart-container') || document.getElementById('bazi-chart-svg');
  if (chartWrapper) {
    if (svgContent) {
      chartWrapper.innerHTML = svgContent;
    } else {
      chartWrapper.innerHTML = '<div style="color: #94a3b8; padding: 2rem;">ไม่สามารถสร้างผังดวง SVG ได้</div>';
    }
  }

  const chart = data.chart || {};
  const dm = chart.day_master || {};

  // 2. Render Pillars Grid
  const pillarsGrid = document.getElementById('pillars-grid');
  if (pillarsGrid && chart.pillars) {
    const p = chart.pillars;
    pillarsGrid.innerHTML = `
      <div class="pillar-box" style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(212, 175, 55, 0.3); padding: 8px; border-radius: 6px; text-align: center;">
        <div style="font-size: 0.8rem; color: #94a3b8;">ยาม (Hour)</div>
        <div style="font-size: 1.3rem; color: #fbbf24; font-weight: bold;">${p.hour?.stem?.char || '-'}</div>
        <div style="font-size: 1.1rem; color: #e2e8f0;">${p.hour?.branch?.char || '-'}</div>
      </div>
      <div class="pillar-box" style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(212, 175, 55, 0.3); padding: 8px; border-radius: 6px; text-align: center;">
        <div style="font-size: 0.8rem; color: #94a3b8;">วัน (Day)</div>
        <div style="font-size: 1.3rem; color: #fbbf24; font-weight: bold;">${p.day?.stem?.char || '-'}</div>
        <div style="font-size: 1.1rem; color: #e2e8f0;">${p.day?.branch?.char || '-'}</div>
      </div>
      <div class="pillar-box" style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(212, 175, 55, 0.3); padding: 8px; border-radius: 6px; text-align: center;">
        <div style="font-size: 0.8rem; color: #94a3b8;">เดือน (Month)</div>
        <div style="font-size: 1.3rem; color: #fbbf24; font-weight: bold;">${p.month?.stem?.char || '-'}</div>
        <div style="font-size: 1.1rem; color: #e2e8f0;">${p.month?.branch?.char || '-'}</div>
      </div>
      <div class="pillar-box" style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(212, 175, 55, 0.3); padding: 8px; border-radius: 6px; text-align: center;">
        <div style="font-size: 0.8rem; color: #94a3b8;">ปี (Year)</div>
        <div style="font-size: 1.3rem; color: #fbbf24; font-weight: bold;">${p.year?.stem?.char || '-'}</div>
        <div style="font-size: 1.1rem; color: #e2e8f0;">${p.year?.branch?.char || '-'}</div>
      </div>
    `;
  }

  // 3. Render Day Master Banner / Badge
  const dmBadge = document.getElementById('day-master-banner') || document.getElementById('day-master-badge');
  if (dmBadge) {
    if (dm.stem && dm.element) {
      dmBadge.innerHTML = `ดิถีวัน (Day Master): <strong>${dm.stem} (${dm.th_name || dm.element})</strong> | ธาตุ: <span style="color: #10b981;">${dm.element}</span>`;
    } else {
      dmBadge.textContent = 'The API response did not include a Day Master.';
    }
  }

  // 4. Render Five Elements Bar Chart
  const elemChart = document.getElementById('elements-bars') || document.getElementById('five-elements-chart');
  if (elemChart) {
    const elements = (chart.five_elements && chart.five_elements.percentages) || chart.five_elements_percent;
    const colors = { Wood: '#10b981', Fire: '#ef4444', Earth: '#f59e0b', Metal: '#94a3b8', Water: '#3b82f6' };

    if (!elements) {
      elemChart.textContent = 'The API response did not include Five Elements data.';
    } else {
    let elemHtml = '<div style="display: flex; gap: 8px; height: 24px; border-radius: 6px; overflow: hidden; margin-top: 8px;">';
    for (const [elem, pct] of Object.entries(elements)) {
      if (pct > 0) {
        elemHtml += `<div style="width: ${pct}%; background: ${colors[elem] || '#64748b'}; text-align: center; color: #fff; font-size: 11px; line-height: 24px;">${elem} ${pct}%</div>`;
      }
    }
    elemHtml += '</div>';
    elemChart.innerHTML = elemHtml;
    }
  }

  // 5. Render AI Interpretation text with Markdown formatting
  const mdContainer = document.getElementById('reading-body') || document.getElementById('llm-markdown-output');
  let rawText = data.interpretation || data.text;
  if (!rawText || !rawText.trim() || rawText === 'ไม่พบผลลัพธ์คำตีความ') {
    rawText = 'The API response did not include an interpretation.';
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
    const val = data.validation_report;
    if (!val) {
      valContainer.textContent = 'The API response did not include a validation report.';
    } else {
    valContainer.innerHTML = `
      <div style="padding: 1rem; background: rgba(168, 85, 247, 0.12); border: 1px solid rgba(168, 85, 247, 0.35); border-radius: 8px; color: #e2e8f0;">
        <h4 style="color: #c084fc; margin-top: 0;">🛡️ ผลการตรวจสอบโดย Gemini Prediction Validator Agent</h4>
        <p><strong>สถานะการตรวจสอบ (Audit Status):</strong> ${val.validation_status || 'Not supplied'} (Confidence Score: <strong>${val.confidence_score ?? 'Not supplied'}</strong>)</p>
        <p><strong>มุมมอง Multi-Agent Audit:</strong> ${val.peer_perspective || 'Not supplied'}</p>
        <p style="margin-bottom: 0;"><strong>ข้อสรุปคำแนะนำการขัดเกลา:</strong> ${val.refined_interpretation || 'Not supplied'}</p>
      </div>
    `;
    }
  }

  // 7. Render RAG Canonical References (RAG 3,132 Chunks)
  const ragContainer = document.getElementById('rag-body');
  if (ragContainer) {
    const refs = data.rag_references || data.canonical_citations || [];

    let ragHtml = `
      <div style="padding: 1rem; background: rgba(14, 165, 233, 0.12); border: 1px solid rgba(14, 165, 233, 0.35); border-radius: 8px; color: #e2e8f0;">
        <h4 style="color: #38bdf8; margin-top: 0;">📚 คัมภีร์อ้างอิงโบราณ (Vector RAG Search Over 3,132 Ingested Chunks)</h4>
        <p style="font-size: 0.85rem; color: #94a3b8;">${refs.length ? 'References returned by the API:' : 'The API response did not include RAG references.'}</p>
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

  // Smooth Scroll to Results
  const targetCard = interpCard || pillarsCard || svgCard;
  if (targetCard) {
    targetCard.scrollIntoView({ behavior: 'smooth' });
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

function showBranchError(title, error) {
  const message = String(error && error.message ? error.message : error)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
  showBranchCard(title, `<div class="branch-error" role="alert">Calculation failed: ${message}. Try again when the API is available.</div>`, null);
}

async function calcZiWei() {
  try {
    const data = await fetchApiJson('/api/v1/ziwei/calculate?year=1990&month=5&day=15&hour=14&gender=male');
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
    showBranchError("🔮 ผังวิชา紫微斗數 (Zi Wei Dou Shu Visualizer)", err);
  }
}

async function calcQiMen() {
  try {
    const data = await fetchApiJson('/api/v1/qimen/calculate?year=2026&month=8&day=7&hour=14');
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
    showBranchError("⚡ ผังวิชา奇門遁甲 (Qi Men Dun Jia Visualizer)", err);
  }
}

async function calcLiuRen() {
  try {
    const data = await fetchApiJson('/api/v1/liuren/calculate?day_stem=甲&day_branch=子&month_general=正月&hour_branch=午');
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
    showBranchError("🌊 ผังวิชา大六壬 (Da Liu Ren Visualizer)", err);
  }
}

async function calcIChing() {
  try {
    const data = await fetchApiJson('/api/v1/iching/calculate?day_stem=甲');
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
    showBranchError("☯ ผังวิชา易經六爻 (I Ching & Liu Yao Visualizer)", err);
  }
}

async function calcXuanKong() {
  try {
    const data = await fetchApiJson('/api/v1/xuankong/calculate?facing_degree=180.0&period=9');
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
    showBranchError("🏯 ผังวิชา玄空風水 (Xuan Kong Visualizer)", err);
  }
}

async function calcZeJi() {
  try {
    const data = await fetchApiJson('/api/v1/zeji/calculate?year_branch=午&month_branch=申&day_branch=寅&user_birth_branch=子');
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
    showBranchError("📅 คำนวณฤกษ์擇吉 (Date Selection Visualizer)", err);
  }
}

async function calcThaiVedic() {
  try {
    const data = await fetchApiJson('/api/v1/thaivedic/calculate?year=1990&month=5&day=15&hour=14&day_of_week=2');
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
    showBranchError("🐘 โหราศาสตร์ไทย & ภารตวิทยา (Thai & Jyotish Visualizer)", err);
  }
}

async function calcWestern() {
  try {
    const data = await fetchApiJson('/api/v1/western/calculate?year=1990&month=5&day=15&hour=14');
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
    showBranchError("🌌 โหราศาสตร์สากล & ยูเรเนียน (Western & Uranian Visualizer)", err);
  }
}

async function calcNumerology() {
  try {
    const data = await fetchApiJson('/api/v1/numerology/calculate?text=0812345678&day_num=2&lunar_month=6&year_zodiac_num=7');
    const score = data.chaldean_score || {};
    const satta = data.satta_lek || {};
    const html = `
      <div style="background: rgba(20, 184, 166, 0.15); border: 1px solid #2dd4bf; padding: 1rem; border-radius: 8px;">
        <h4 style="color: #2dd4bf; margin-top: 0;">🔢 สัตตเลข 7 ฐาน & เลขศาสตร์ Chaldean</h4>
        <p><strong>เลขศาสตร์ Chaldean (Input: ${score.input_text || ''}):</strong> ผลรวม ${score.total_score || ''} → ถอดถอดรากได้ <strong>เลข ${score.reduced_root_digit || ''}</strong></p>
        <p><strong>ความหมายเลข:</strong> ${score.digit_meaning || ''}</p>
        <hr style="border-color: rgba(255,255,255,0.1); margin: 0.8rem 0;">
        <p><strong>ผัง 7 ฐาน 4 แถว (Satta-Lek Matrix):</strong></p>
        <div style="display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px; font-size: 0.8rem; text-align: center;">
          ${(satta.matrix_7_base || []).map(m => `
            <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid #0d9488; padding: 4px; border-radius: 4px;">
              <strong>${m.column_name}</strong><br>${m.digit}
            </div>
          `).join('')}
        </div>
      </div>
    `;
    showBranchCard("🔢 สัตตเลข 7 ฐาน & เลขศาสตร์ Chaldean Visualizer", html, data.svg_content);
  } catch (err) {
    showBranchError("🔢 สัตตเลข 7 ฐาน & เลขศาสตร์ Chaldean Visualizer", err);
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
