(function () {
  "use strict";

  const TOPIC_IDS = [
    "personal_overview_strengths",
    "past_pattern_calibration",
    "annual_overview",
    "career_business",
    "finance",
    "love_relationships",
    "health_wellbeing",
    "family_surrounding_people",
    "opportunities_caution_periods",
    "twelve_month_roadmap",
    "top_priorities_cautions",
    "export_sharing_actions",
  ];

  const FEEDBACK_CHOICES = ["ตรง", "ตรงบางส่วน", "ไม่ตรง", "จำไม่ได้"];
  const FEEDBACK_STORAGE_KEY = "horo_lite_past_pattern_feedback";

  const PLACE_DEFAULTS = {
    "bangkok, thailand": { latitude: 13.7563, longitude: 100.5018, timezone: "Asia/Bangkok" },
    bangkok: { latitude: 13.7563, longitude: 100.5018, timezone: "Asia/Bangkok" },
    "กรุงเทพ": { latitude: 13.7563, longitude: 100.5018, timezone: "Asia/Bangkok" },
    "chiang mai, thailand": { latitude: 18.7883, longitude: 98.9853, timezone: "Asia/Bangkok" },
    "chiang mai": { latitude: 18.7883, longitude: 98.9853, timezone: "Asia/Bangkok" },
    "เชียงใหม่": { latitude: 18.7883, longitude: 98.9853, timezone: "Asia/Bangkok" },
    "phuket, thailand": { latitude: 7.8804, longitude: 98.3923, timezone: "Asia/Bangkok" },
    phuket: { latitude: 7.8804, longitude: 98.3923, timezone: "Asia/Bangkok" },
    "ภูเก็ต": { latitude: 7.8804, longitude: 98.3923, timezone: "Asia/Bangkok" },
    "khon kaen, thailand": { latitude: 16.4419, longitude: 102.8350, timezone: "Asia/Bangkok" },
    "khon kaen": { latitude: 16.4419, longitude: 102.8350, timezone: "Asia/Bangkok" },
    "ขอนแก่น": { latitude: 16.4419, longitude: 102.8350, timezone: "Asia/Bangkok" },
    "nakhon ratchasima, thailand": { latitude: 14.9799, longitude: 102.0977, timezone: "Asia/Bangkok" },
    "nakhon ratchasima": { latitude: 14.9799, longitude: 102.0977, timezone: "Asia/Bangkok" },
    "นครราชสีมา": { latitude: 14.9799, longitude: 102.0977, timezone: "Asia/Bangkok" },
    "songkhla, thailand": { latitude: 7.1898, longitude: 100.5951, timezone: "Asia/Bangkok" },
    songkhla: { latitude: 7.1898, longitude: 100.5951, timezone: "Asia/Bangkok" },
    "สงขลา": { latitude: 7.1898, longitude: 100.5951, timezone: "Asia/Bangkok" },
    "chonburi, thailand": { latitude: 13.3611, longitude: 100.9847, timezone: "Asia/Bangkok" },
    chonburi: { latitude: 13.3611, longitude: 100.9847, timezone: "Asia/Bangkok" },
    "ชลบุรี": { latitude: 13.3611, longitude: 100.9847, timezone: "Asia/Bangkok" },
    "udon thani, thailand": { latitude: 17.4138, longitude: 102.7872, timezone: "Asia/Bangkok" },
    "udon thani": { latitude: 17.4138, longitude: 102.7872, timezone: "Asia/Bangkok" },
    "อุดรธานี": { latitude: 17.4138, longitude: 102.7872, timezone: "Asia/Bangkok" },
  };

  const form = document.getElementById("lite-form");
  const statusMessage = document.getElementById("status-message");
  const resultOutput = document.getElementById("result-output");
  const submitButton = document.getElementById("submit-reading");
  const birthTime = document.getElementById("birth_time");
  const unknownHour = document.getElementById("unknown_hour");
  const birthPlace = document.getElementById("birth_place");
  const latitude = document.getElementById("latitude");
  const longitude = document.getElementById("longitude");
  const timezone = document.getElementById("timezone");
  const targetYear = document.getElementById("target_year");
  const resultPanel = document.getElementById("result-panel");
  const resultMeta = document.getElementById("result-meta");
  const hitlAlert = document.getElementById("hitl-alert");
  const topicsContainer = document.getElementById("topics-container");
  const retryButton = document.getElementById("result-retry");
  const technicalBasis = document.getElementById("technical-basis");
  const calculationDrawer = document.getElementById("calculation-drawer");
  const submitLoadingMessage = "กำลังส่งข้อมูลไปยัง Horo Lite unified reading API...";

  const state = {
    lastPayload: null,
    lastResult: null,
    feedbackByPattern: {},
  };

  function findById(id) {
    return document.getElementById(id);
  }

  function setStatus(message, mode = "default") {
    if (!statusMessage) {
      return;
    }
    statusMessage.textContent = message;
    statusMessage.classList.toggle("is-success", mode === "success");
    statusMessage.classList.toggle("is-error", mode === "error");
    statusMessage.classList.toggle("is-warning", mode === "warning");
  }

  function normalizePlace(value) {
    return String(value || "").trim().toLowerCase();
  }

  function applyPlaceDefault() {
    const place = PLACE_DEFAULTS[normalizePlace(birthPlace.value)];
    if (!place) {
      return;
    }
    latitude.value = String(place.latitude);
    longitude.value = String(place.longitude);
    timezone.value = place.timezone;
  }

  function syncUnknownHour() {
    birthTime.disabled = unknownHour.checked;
    birthTime.required = !unknownHour.checked;
    if (unknownHour.checked) {
      birthTime.value = "";
    }
  }

  function optionalText(formData, key) {
    const value = String(formData.get(key) || "").trim();
    return value ? value : null;
  }

  function buildPayload() {
    const formData = new FormData(form);
    const payload = {
      birth_date: String(formData.get("birth_date") || ""),
      birth_time: unknownHour.checked ? null : String(formData.get("birth_time") || ""),
      unknown_hour: unknownHour.checked,
      birth_place: String(formData.get("birth_place") || "").trim(),
      latitude: Number(formData.get("latitude")),
      longitude: Number(formData.get("longitude")),
      timezone: String(formData.get("timezone") || "Asia/Bangkok").trim(),
      gender_at_birth: optionalText(formData, "gender_at_birth"),
      target_year: Number(formData.get("target_year")),
      locale: String(formData.get("locale") || "th-TH"),
      display_name: optionalText(formData, "display_name"),
      primary_focus_question: optionalText(formData, "primary_focus_question"),
      force_human_review: formData.get("force_human_review") === "on",
    };
    const engineMode = optionalText(formData, "engine_mode");
    if (engineMode) {
      payload.engine_mode = engineMode;
    }
    return payload;
  }

  function isEmptyValue(value) {
    return value === undefined || value === null || String(value).trim() === "";
  }

  function formatMonthHeader(month) {
    return `เดือนที่ ${month}`;
  }

  function confidenceClass(confidence) {
    const value = String(confidence || "MEDIUM").toUpperCase();
    if (value === "HIGH") {
      return "is-high";
    }
    if (value === "LOW") {
      return "is-low";
    }
    return "is-medium";
  }

  function clamp(value) {
    const num = Number(value);
    if (!Number.isFinite(num)) {
      return 5;
    }
    return Math.max(1, Math.min(10, Math.round(num)));
  }

  function makeNode(tag, props = {}, text) {
    const node = document.createElement(tag);
    Object.entries(props).forEach(([key, value]) => {
      if (key.startsWith("on") && typeof value === "function") {
        node.addEventListener(key.slice(2), value);
      } else if (key === "className") {
        node.className = value;
      } else if (value !== null && value !== undefined) {
        node.setAttribute(key, String(value));
      }
    });
    if (text !== undefined) {
      node.textContent = String(text);
    }
    return node;
  }

  function renderEvidencePills(values) {
    if (!Array.isArray(values) || !values.length) {
      return null;
    }
    const wrapper = makeNode("div", { className: "evidence-list" });
    values
      .slice(0, 4)
      .forEach((item) => {
        wrapper.appendChild(makeNode("span", { className: "evidence-pill" }, item));
      });
    return wrapper;
  }

  function renderGaugeValue(label, value, range) {
    const wrapper = makeNode("div", { className: "score-cell" });
    wrapper.appendChild(makeNode("div", { className: "score-label" }, label));

    if (Array.isArray(range) && range.length === 2) {
      const [start, end] = [clamp(range[0]), clamp(range[1])];
      const rangeBar = makeNode("div", { className: "score-gauge-range", role: "img", "aria-label": `${label} ช่วงคะแนน ${start} ถึง ${end}` });
      const count = Math.max(10, Math.min(10, Number(end)));
      for (let i = 1; i <= 10; i += 1) {
        const seg = makeNode("span", {});
        if (i >= start && i <= end) {
          seg.className = "active";
        }
        rangeBar.appendChild(seg);
      }
      wrapper.appendChild(rangeBar);
      wrapper.appendChild(makeNode("div", { className: "gauge-value" }, `${start} - ${end}`));
      return wrapper;
    }

    const safeScore = clamp(value);
    const gauge = makeNode("div", { className: "score-gauge", role: "img", "aria-label": `${label} คะแนน ${safeScore} จาก 10` });
    const track = makeNode("div", { className: "score-scale" });
    track.style.width = `${safeScore * 10}%`;

    gauge.appendChild(track);
    gauge.appendChild(makeNode("div", { className: "gauge-value" }, safeScore));
    return gauge;
  }

  function renderMonthlyCards(monthlyScores) {
    const monthlyGrid = makeNode("div", { className: "roadmap-grid" });

    if (!Array.isArray(monthlyScores)) {
      return monthlyGrid;
    }

    monthlyScores.forEach((monthItem) => {
      const monthNo = Number(monthItem.month || 0);
      const card = makeNode("article", { className: "monthly-card" });
      card.appendChild(makeNode("h4", {}, formatMonthHeader(monthNo)));
      const scoreRow = makeNode("div", { className: "score-row" });
      const careerRange = monthItem.career_score_range || monthItem.career_range;
      const financeRange = monthItem.finance_score_range || monthItem.finance_range;
      const loveRange = monthItem.love_score_range || monthItem.love_range;

      scoreRow.appendChild(renderGaugeValue("งาน", monthItem.career_score, careerRange));
      scoreRow.appendChild(renderGaugeValue("เงิน", monthItem.finance_score, financeRange));
      scoreRow.appendChild(renderGaugeValue("ความรัก", monthItem.love_score, loveRange));
      card.appendChild(scoreRow);

      const reasons = Array.isArray(monthItem.reasons)
        ? monthItem.reasons.filter(Boolean)
        : [];
      const reasonText = reasons.slice(0, 2).join(" | ") || "สถิติรายเดือนจากหลักฐานร่วม consensus";
      card.appendChild(makeNode("p", { className: "topic-conf" }, reasonText));
      monthlyGrid.appendChild(card);
    });
    return monthlyGrid;
  }

  function calculateTopAndCaution(monthlyScores) {
    if (!Array.isArray(monthlyScores) || !monthlyScores.length) {
      return { top: [], caution: [] };
    }
    const scored = monthlyScores
      .map((item) => {
        const career = clamp(item.career_score || 0);
        const finance = clamp(item.finance_score || 0);
        const love = clamp(item.love_score || 0);
        const total = career + finance + love;
        return {
          month: Number(item.month),
          total,
          career,
          finance,
          love,
          item,
        };
      })
      .filter((entry) => Number.isFinite(entry.month));

    const top = [...scored]
      .sort((a, b) => b.total - a.total || a.month - b.month)
      .slice(0, 3)
      .map((entry) => `เดือนที่ ${entry.month} : รวม ${entry.total}`);
    const caution = [...scored]
      .sort((a, b) => a.total - b.total || a.month - b.month)
      .slice(0, 3)
      .map((entry) => `เดือนที่ ${entry.month} : รวม ${entry.total}`);
    return { top, caution };
  }

  function getPastPatternThemeLabel(theme) {
    const labels = {
      education: "การศึกษา",
      career_shift: "การเปลี่ยนอาชีพ",
      relocation: "การย้ายถิ่น",
      financial_pressure: "แรงกดดันการเงิน",
      work_role_change: "เปลี่ยนบทบาทงาน",
    };
    return labels[theme] || theme;
  }

  function createPastPatternCard(pattern) {
    const patternId = String(pattern.pattern_id || `pattern-${Math.random()}`);
    const container = makeNode("article", { className: "pattern-item" });
    container.appendChild(makeNode("h4", {}, `${getPastPatternThemeLabel(pattern.theme)} (${pattern.year_range?.[0]}-${pattern.year_range?.[1]})`));
    const years = `ช่วงอายุ ${pattern.age_range?.[0]}-${pattern.age_range?.[1]} ปี`;
    container.appendChild(makeNode("p", { className: "topic-conf" }, years));

    const chips = makeNode("div", { className: "chip-row", role: "group", "aria-label": "เลือกความตรงของประวัติศาสตร์นี้" });
    FEEDBACK_CHOICES.forEach((choice) => {
      const pressed = state.feedbackByPattern[patternId] === choice;
      const button = makeNode(
        "button",
        {
          type: "button",
          className: "chip",
          "aria-pressed": pressed ? "true" : "false",
          "data-pattern-id": patternId,
          "data-choice": choice,
          onClick: (event) => {
            event.preventDefault();
            const target = event.currentTarget;
            const choiceValue = target.getAttribute("data-choice");
            if (!choiceValue) {
              return;
            }
            state.feedbackByPattern[patternId] = choiceValue;
            updatePatternSelection(patternId, chips);
            persistFeedbackIfConsented();
          },
        },
        choice,
      );
      chips.appendChild(button);
    });
    container.appendChild(chips);

    if (state.feedbackByPattern[patternId]) {
      updatePatternSelection(patternId, chips);
    }
    return container;
  }

  function updatePatternSelection(patternId, chipRow) {
    const selected = state.feedbackByPattern[patternId];
    chipRow.querySelectorAll("button").forEach((button) => {
      button.setAttribute("aria-pressed", button.getAttribute("data-choice") === selected ? "true" : "false");
    });
  }

  function persistFeedbackIfConsented() {
    const consent = findById("feedback-consent");
    if (!consent || !consent.checked) {
      return;
    }
    try {
      window.localStorage.setItem(FEEDBACK_STORAGE_KEY, JSON.stringify(state.feedbackByPattern));
    } catch {
      // best-effort only
    }
  }

  function loadFeedbackFromStorage() {
    const consent = findById("feedback-consent");
    if (!consent || !consent.checked) {
      state.feedbackByPattern = {};
      return;
    }
    try {
      const raw = window.localStorage.getItem(FEEDBACK_STORAGE_KEY);
      const parsed = raw ? JSON.parse(raw) : {};
      state.feedbackByPattern = parsed && typeof parsed === "object" ? parsed : {};
    } catch {
      state.feedbackByPattern = {};
    }
  }

  function enforceNoPersistenceWithoutConsent() {
    const consent = findById("feedback-consent");
    if (!consent || consent.checked) {
      return;
    }
    try {
      window.localStorage.removeItem(FEEDBACK_STORAGE_KEY);
    } catch {
      // ignore
    }
  }

  function renderTopic(topic, data, options = {}) {
    const card = makeNode("article", { className: options.className || "topic-card topic-card--half", "aria-labelledby": `topic-${topic.topic_id}` });
    const iconMap = {
      personal_overview_strengths: "🧭",
      past_pattern_calibration: "🧩",
      annual_overview: "📌",
      career_business: "💼",
      finance: "💰",
      love_relationships: "💞",
      health_wellbeing: "🩺",
      family_surrounding_people: "👨‍👩‍👧",
      opportunities_caution_periods: "🧭",
      twelve_month_roadmap: "📅",
      top_priorities_cautions: "🎯",
      export_sharing_actions: "📤",
    };
    const heading = makeNode("h3", { id: `topic-${topic.topic_id}` }, `${iconMap[topic.topic_id] || "🔮"} ${topic.title || topic.topic_id}`);
    card.appendChild(heading);
    card.appendChild(makeNode("p", { className: "topic-copy" }, topic.summary || ""));

    const conf = makeNode("span", { className: `topic-confidence ${confidenceClass(topic.confidence)}` }, `ความมั่นใจ: ${topic.confidence || "MEDIUM"}`);
    card.appendChild(conf);

    const guidance = topic.guidance || "";
    card.appendChild(makeNode("p", { className: "topic-conf" }, guidance));

    const evidence = renderEvidencePills(topic.evidence_refs || []);
    if (evidence) {
      card.appendChild(evidence);
    }

    if (topic.topic_id === "annual_overview") {
      const note = `สถิติความเสี่ยงรายเดือน: ${Math.min(10, Math.max(1, Math.round((topic.summary || "").length / 5)))} /10`;
      card.appendChild(makeNode("p", { className: "topic-conf" }, note));
    }

    if (topic.topic_id === "opportunities_caution_periods") {
      card.appendChild(makeNode("p", { className: "topic-conf" }, "ช่วงมีโอกาสและช่วงควรระวังถูกประมวลผลจากคะแนนรายเดือน 12 เดือน"));
    }

    if (topic.topic_id === "past_pattern_calibration") {
      const patternTitle = makeNode("p", { className: "topic-conf" }, "เลือกประวัติที่ตรงกับชีวิตคุณ — ใช้เพื่อปรับน้ำเสียงถัดไป (ไม่ใช้ปรับคะแนน)" );
      card.appendChild(patternTitle);
      const container = makeNode("div", { className: "pattern-list" });
      (data.past_patterns || []).forEach((pattern) => container.appendChild(createPastPatternCard(pattern)));
      card.appendChild(container);

      const consentRow = makeNode("div", { className: "toggle-row", role: "group", "aria-label": "Consent controls" });
      consentRow.appendChild(makeNode("input", { id: "feedback-consent", type: "checkbox", name: "feedback-consent" }));
      consentRow.appendChild(makeNode("label", { for: "feedback-consent" }, "ยอมรับการเก็บผลตอบรับเพื่อปรับน้ำเสียงเฉพาะหน้าได้"));
      card.appendChild(consentRow);

      const consentInput = consentRow.querySelector("input");
      if (consentInput) {
        consentInput.addEventListener("change", () => {
          if (consentInput.checked) {
            persistFeedbackIfConsented();
          } else {
            enforceNoPersistenceWithoutConsent();
          }
        });
        loadFeedbackFromStorage();
      }
      return card;
    }

    if (topic.topic_id === "twelve_month_roadmap") {
      card.className = `${card.className} topic-card--wide`;
      card.appendChild(renderMonthlyCards(data.monthly_scores || []));
    }

    if (topic.topic_id === "top_priorities_cautions") {
      const priorityGrid = makeNode("div", { className: "priority-grid" });
      const summary = calculateTopAndCaution(data.monthly_scores || []);
      const priorities = makeNode("div", {});
      priorities.appendChild(makeNode("h4", {}, "โฟกัสสูงสุด"));
      if (summary.top.length === 0) {
        priorities.appendChild(makeNode("p", { className: "topic-conf" }, "ข้อมูลยังไม่เพียงพอสำหรับการจัดอันดับ"));
      } else {
        summary.top.forEach((text) => {
          priorities.appendChild(makeNode("p", { className: "topic-conf" }, `✅ ${text}`));
        });
      }
      const cautions = makeNode("div", {});
      cautions.appendChild(makeNode("h4", {}, "สิ่งที่ควรระวัง"));
      if (summary.caution.length === 0) {
        cautions.appendChild(makeNode("p", { className: "topic-conf" }, "ไม่มีข้อมูลเตือนชัดเจน"));
      } else {
        summary.caution.forEach((text) => {
          cautions.appendChild(makeNode("p", { className: "topic-conf" }, `⚠️ ${text}`));
        });
      }
      card.appendChild(priorities);
      card.appendChild(cautions);
      return card;
    }

    if (topic.topic_id === "export_sharing_actions") {
      card.className = `${card.className} topic-card--actions`;
      const controls = makeNode("div", { className: "export-buttons" });
      controls.appendChild(
        makeNode("button", {
          type: "button",
          className: "primary-action",
          id: "export-full",
          onClick: (event) => {
            event.preventDefault();
            if (!window.horoLiteExport) {
              return;
            }
            const includeBirth = Boolean(findById("export-include-birth" )?.checked);
            window.horoLiteExport.exportFullPng(state.lastResult, {
              includeBirthDetails: includeBirth,
            });
          },
        }, "บันทึกภาพแนวตั้งเต็มหน้าจอ"),
      );
      controls.appendChild(
        makeNode("button", {
          type: "button",
          className: "ghost-button",
          id: "export-story",
          onClick: (event) => {
            event.preventDefault();
            if (!window.horoLiteExport) {
              return;
            }
            const includeBirth = Boolean(findById("export-include-birth" )?.checked);
            window.horoLiteExport.exportStoryPng(state.lastResult, {
              includeBirthDetails: includeBirth,
            });
          },
        }, "บันทึก 9:16 Story 1080×1920"),
      );
      controls.appendChild(
        makeNode("button", {
          type: "button",
          id: "copy-summary",
          className: "ghost-button",
          onClick: (event) => {
            event.preventDefault();
            if (!window.horoLiteExport) {
              return;
            }
            const includeBirth = Boolean(findById("export-include-birth" )?.checked);
            window.horoLiteExport.copySocialSummary(state.lastResult, {
              includeBirthDetails: includeBirth,
            });
          },
        }, "คัดลอกข้อความแชร์"),
      );
      controls.appendChild(
        makeNode("button", {
          type: "button",
          id: "print-summary",
          className: "ghost-button",
          onClick: (event) => {
            event.preventDefault();
            if (!window.horoLiteExport) {
              return;
            }
            const includeBirth = Boolean(findById("export-include-birth" )?.checked);
            window.horoLiteExport.printResult(state.lastResult, {
              includeBirthDetails: includeBirth,
            });
          },
        }, "พิมพ์รายงาน"),
      );
      card.appendChild(controls);

      const privacyRow = makeNode("div", { className: "toggle-row" });
      privacyRow.appendChild(makeNode("input", { id: "export-include-birth", type: "checkbox", name: "export-include-birth" }));
      privacyRow.appendChild(makeNode("label", { for: "export-include-birth" }, "แสดงวันเวลาเกิดในรูปภาพ/สรุป (ไม่แนะนำ)") );
      card.appendChild(privacyRow);

      const help = makeNode("p", { className: "topic-conf" }, "สำรอง: ข้อมูลวันเกิดจะปิดซ่อนในโหมดเริ่มต้นเพื่อความเป็นส่วนตัวโดยค่าเริ่มต้น");
      card.appendChild(help);
    }

    return card;
  }

  function renderResultOutputRaw(data) {
    if (!resultOutput) {
      return;
    }
    resultOutput.textContent = JSON.stringify(data, null, 2);
    resultOutput.classList.remove("hidden");
    resultOutput.hidden = false;
  }

  function renderResultMeta(data) {
    if (!resultMeta) {
      return;
    }
    const flags = data.hitl_flags || {};
    const routing = data.hitl_routing || {};
    const metadata = data.consensus_metadata || {};
    const metaLines = [
      `ชื่อแคมเปญ: ${isEmptyValue(data.request_id) ? "-" : data.request_id}`,
      `ปีที่ดู: ${data.target_year}`,
      `คะแนน consensus: ${(metadata.consensus_score ?? "").toString()}`,
      `routing: ${routing.status || "N/A"}`,
      `HITL required: ${Boolean(flags.required_human_review) ? "ใช่" : "ไม่"}`,
    ];
    resultMeta.textContent = metaLines.join(" | ");
    resultMeta.classList.remove("hidden");
    resultMeta.hidden = false;

    if (flags.required_human_review || (metadata.arbitration_status || "").includes("CONFLICT")) {
      hitlAlert.classList.remove("hidden");
      hitlAlert.hidden = false;
      hitlAlert.textContent = `สาขาแสดงผลอยู่โหมดตรวจทาน: ${routing.status || "QUEUED_FOR_HUMAN_REVIEW"}`;
    } else {
      hitlAlert.classList.add("hidden");
      hitlAlert.hidden = true;
      hitlAlert.textContent = "";
    }
  }

  function renderTechnicalBasis(data) {
    if (!technicalBasis) {
      return;
    }
    const lines = {
      schema_version: data.schema_version,
      request_id: data.request_id,
      consensus_metadata: data.consensus_metadata || {},
      hitl_flags: data.hitl_flags || {},
      hitl_routing: data.hitl_routing || {},
      llm_metadata: data.llm_metadata || {},
      topic_count: Array.isArray(data.topics) ? data.topics.length : 0,
      month_count: Array.isArray(data.monthly_scores) ? data.monthly_scores.length : 0,
    };
    technicalBasis.textContent = JSON.stringify(lines, null, 2);
  }

  function attachExportButtonKeyboardSupport() {
    const buttons = topicsContainer.querySelectorAll("button");
    buttons.forEach((button) => {
      if (button.dataset.bound === "1") {
        return;
      }
      button.setAttribute("data-bound", "1");
      button.addEventListener("keydown", (event) => {
        if (event.key !== "Enter" && event.key !== " ") {
          return;
        }
        event.preventDefault();
        button.click();
      });
    });
  }

  function assignLayoutClass(section) {
    if (["twelve_month_roadmap", "past_pattern_calibration", "top_priorities_cautions", "export_sharing_actions"].includes(section.topic_id)) {
      return "topic-card--wide";
    }
    return "topic-card--half";
  }

  function renderTopics(data) {
    if (!topicsContainer) {
      return;
    }
    topicsContainer.innerHTML = "";

    const ordered = Array.isArray(data.topics)
      ? [...data.topics].sort((a, b) => Number(a.order || 0) - Number(b.order || 0))
      : [];

    const mapped = [];
    ordered.forEach((topic) => {
      const className = `topic-card topic-card--half ${assignLayoutClass(topic)}`;
      mapped.push(renderTopic({ ...topic, order: topic.order || 0 }, data, { className }));
    });

    // fill missing topics deterministically from server if incomplete due to fallback
    const seen = new Set(mapped.map((topic) => topic.querySelector("h3")?.textContent || ""));
    for (const topicId of TOPIC_IDS) {
      const found = ordered.find((item) => item.topic_id === topicId);
      if (!found) {
        const fakeTopic = {
          topic_id: topicId,
          title: topicId,
          summary: `${topicId} (fallback topic)`,
          guidance: "ข้อมูลอาจมาจากโหมด fallback ของ API",
          confidence: "MEDIUM",
          evidence_refs: ["fallback"],
        };
        const node = renderTopic(fakeTopic, data, { className: "topic-card topic-card--half" });
        if (!seen.has(fakeTopic.title)) {
          mapped.push(node);
          seen.add(fakeTopic.title);
        }
      }
    }

    mapped.forEach((node) => topicsContainer.appendChild(node));
    attachExportButtonKeyboardSupport();
  }

  function renderUnknownHourNotice(data) {
    if (!data?.hitl_flags?.uncertain_birth_time) {
      return;
    }
    const notice = makeNode("p", { className: "topic-conf", role: "note" }, "⚠️ ไม่ทราบเวลาเกิด → ระบบแสดงเกณฑ์ประเมินแบบคาดเดากว้างและรันเส้นทางตรวจทานคน" );
    resultMeta?.appendChild(notice);
  }

  function renderResult(data) {
    state.lastResult = data;
    window.horoLiteLastPayload = state.lastPayload;
    window.horoLiteLastResult = data;
    renderResultOutputRaw(data);
    renderResultMeta(data);
    renderTechnicalBasis(data);
    renderTopics(data);
    renderUnknownHourNotice(data);

    if (!data.topics || !data.topics.length) {
      setStatus("ผลลัพธ์ว่างจาก API", "warning");
      return;
    }
    setStatus("ได้รับผลลัพธ์จาก API แล้ว", "success");
    if (state.feedbackByPattern && Object.keys(state.feedbackByPattern).length > 0) {
      persistFeedbackIfConsented();
    }
  }

  async function submitReading(event) {
    event.preventDefault();
    applyPlaceDefault();
    if (!form.reportValidity()) {
      setStatus("กรุณาตรวจสอบข้อมูลที่จำเป็นก่อนส่งคำขอ", "error");
      return;
    }

    const payload = buildPayload();
    state.lastPayload = payload;
    submitButton.disabled = true;

    if (retryButton) {
      retryButton.classList.add("hidden");
      retryButton.hidden = true;
    }
    setStatus(submitLoadingMessage, "warning");
    resultOutput?.classList.add("hidden");
    resultOutput.hidden = true;

    const start = performance.now();
    try {
      const response = await fetch("/api/v3/unified-reading", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const elapsed = Math.round(performance.now() - start);
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        const message =
          data.detail || data.message || "ไม่สามารถคำนวณผลลัพธ์ได้";
        throw new Error(Array.isArray(message) ? JSON.stringify(message) : String(message));
      }

      renderResult(data);
      setStatus(`ได้รับผลลัพธ์จาก API ใน ${elapsed}ms`, "success");
      return;
    } catch (error) {
      setStatus(error.message || "เกิดข้อผิดพลาดระหว่างส่งคำขอ", "error");
      if (retryButton) {
        retryButton.classList.remove("hidden");
        retryButton.hidden = false;
      }
    } finally {
      submitButton.disabled = false;
    }
  }

  function retryReading() {
    if (!state.lastPayload || !form) {
      return;
    }
    submitButton.click();
  }

  function initializeDefaults() {
    targetYear.value = String(new Date().getFullYear());
    if (!birthPlace.value) {
      birthPlace.value = "Bangkok, Thailand";
    }
    applyPlaceDefault();
    syncUnknownHour();
    state.lastResult = null;
    window.horoLiteLastPayload = null;
    window.horoLiteLastResult = null;
    state.feedbackByPattern = {};
  }

  function registerEvents() {
    birthPlace.addEventListener("change", applyPlaceDefault);
    birthPlace.addEventListener("blur", applyPlaceDefault);
    unknownHour.addEventListener("change", syncUnknownHour);
    form.addEventListener("submit", submitReading);
    retryButton?.addEventListener("click", retryReading);

    // Accessibility: allow quick reflow if JavaScript fails on button click
    resultPanel?.addEventListener("keydown", (event) => {
      if (event.key !== "Enter" || event.target.tagName !== "BUTTON") {
        return;
      }
      event.preventDefault();
      event.target.click();
    });
  }

  initializeDefaults();
  registerEvents();
})();
