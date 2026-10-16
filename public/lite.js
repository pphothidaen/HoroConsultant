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
  const drawerMetaMirror = document.getElementById("drawer-meta-mirror");
  const drawerBaziMirror = document.getElementById("drawer-bazi-mirror");
  const genderAtBirth = document.getElementById("gender_at_birth");
  const genderPillsContainer = document.getElementById("gender-pills");
  const plainSummarySection = document.getElementById("plain-summary-section");
  const plainSummaryContainer = document.getElementById("plain-summary-container");
  const btnViewFateBook = document.getElementById("btn-view-fate-book");
  const fateBookModal = document.getElementById("fate-book-modal");
  const modalPromptContent = document.getElementById("modal-prompt-content");
  const btnCloseModal = document.getElementById("btn-close-modal");
  const btnCloseModalFooter = document.getElementById("btn-close-modal-footer");
  const btnCopyModalPrompt = document.getElementById("btn-copy-modal-prompt");
  const copyToastMessage = document.getElementById("copy-toast-message");
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
            updateExplanationEmphasis();
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
    const card = chipRow.closest(".pattern-item");
    if (card) {
      let emphasisBadge = card.querySelector(".pattern-feedback-emphasis");
      if (selected) {
        if (!emphasisBadge) {
          emphasisBadge = makeNode("div", { className: "pattern-feedback-emphasis" });
          card.appendChild(emphasisBadge);
        }
        emphasisBadge.textContent = `น้ำเสียง: ปรับตามผลตอบรับ (${selected})`;
      } else if (emphasisBadge) {
        emphasisBadge.remove();
      }
    }
  }

  function updateExplanationEmphasis() {
    const feedbackEntries = Object.entries(state.feedbackByPattern || {});
    const indicator = findById("feedback-emphasis-indicator");
    if (!indicator) {
      return;
    }
    if (feedbackEntries.length === 0) {
      indicator.textContent = "";
      indicator.className = "pattern-feedback-emphasis-hidden";
      return;
    }
    indicator.className = "pattern-feedback-emphasis";
    const matched = feedbackEntries.filter(([, v]) => v === "ตรงมาก" || v === "ค่อนข้างตรง").length;
    const diff = feedbackEntries.filter(([, v]) => v === "ไม่ตรง").length;
    let note = "💡 การปรับน้ำเสียงคำอธิบาย: ";
    if (matched > diff) {
      note += `เน้นคำอธิบายเชิงยืนยันตามประสบการณ์จริง (${matched} ช่วงตรงกัน)`;
    } else if (diff > 0) {
      note += `เน้นคำเตือนเชิงป้องกันและทางเลือกสำรอง (${diff} ช่วงไม่ตรง)`;
    } else {
      note += "เน้นสังเกตการณ์จังหวะชีวิตปัจจุบันเป็นหลัก";
    }
    indicator.textContent = note;
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
    if (!consent || consent.checked) return;
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

    const conf = makeNode("span", { className: `topic-confidence ${confidenceClass(topic.confidence)} hidden`, "aria-hidden": "true" }, `ความมั่นใจ: ${topic.confidence || "MEDIUM"}`);
    card.appendChild(conf);

    const guidance = topic.guidance || "";
    card.appendChild(makeNode("p", { className: "topic-conf" }, guidance));

    // Evidence pills hidden from end users (technical reference data)
    const evidence = renderEvidencePills(topic.evidence_refs || []);
    if (evidence) {
      evidence.classList.add("hidden");
      evidence.setAttribute("aria-hidden", "true");
      card.appendChild(evidence);
    }

    if (topic.topic_id === "annual_overview") {
      const note = `สถิติความเสี่ยงรายเดือน: ${Math.min(10, Math.max(1, Math.round((topic.summary || "").length / 5)))} /10`;
      card.appendChild(makeNode("p", { className: "topic-conf hidden", "aria-hidden": "true" }, note));
    }

    if (topic.topic_id === "opportunities_caution_periods") {
      card.appendChild(makeNode("p", { className: "topic-conf hidden", "aria-hidden": "true" }, "ช่วงมีโอกาสและช่วงควรระวังถูกประมวลผลจากคะแนนรายเดือน 12 เดือน"));
    }

    if (topic.topic_id === "past_pattern_calibration") {
      const patternTitle = makeNode("p", { className: "topic-conf" }, "เลือกประวัติที่ตรงกับชีวิตคุณ — ใช้เพื่อปรับน้ำเสียงถัดไป (ไม่ใช้ปรับคะแนน)" );
      card.appendChild(patternTitle);
      const container = makeNode("div", { className: "pattern-list" });
      (data.past_patterns || []).forEach((pattern) => container.appendChild(createPastPatternCard(pattern)));
      card.appendChild(container);

      const emphasisIndicator = makeNode("div", {
        id: "feedback-emphasis-indicator",
        className: "pattern-feedback-emphasis",
        role: "status",
        "aria-live": "polite",
      });
      card.appendChild(emphasisIndicator);

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
            updateExplanationEmphasis();
          }
        });
        loadFeedbackFromStorage();
        updateExplanationEmphasis();
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
    // Store raw data for programmatic access but keep hidden from end users
    resultOutput.textContent = JSON.stringify(data, null, 2);
    resultOutput.classList.add("hidden");
    resultOutput.hidden = true;
  }

  function renderResultMeta(data) {
    if (!resultMeta) {
      return;
    }
    const flags = data.hitl_flags || {};
    const metadata = data.consensus_metadata || {};
    const metaLines = [
      `รหัสอ้างอิง: ${isEmptyValue(data.request_id) ? "-" : data.request_id}`,
      `ปีที่ดู: ${data.target_year}`,
      `ดัชนีความสอดคล้อง: ${(metadata.consensus_score ?? "").toString()}`,
      `สถานะ: ${flags.uncertain_birth_time ? "วิเคราะห์ฐาน 3 เสา" : "สมบูรณ์"}`,
    ];

    // Keep result-meta populated but hidden from end users
    resultMeta.textContent = metaLines.join(" | ");
    resultMeta.classList.add("hidden");
    resultMeta.hidden = true;

    // Build hitl alert text but keep hidden from main view
    let hitlText = "";
    if (flags.required_human_review || (metadata.arbitration_status || "").includes("CONFLICT") || flags.uncertain_birth_time) {
      if (flags.uncertain_birth_time) {
        hitlText = "📋 การวิเคราะห์ฐานพลังงาน 3 เสา (กรณีไม่ระบุเวลาเกิด): ระบบคำนวณจากเสาปี เดือน และวัน พร้อมแสดงช่วงคะแนนความผันแปร (Min–Max) เพื่อรักษาความเที่ยงตรงทางสถิติสูงสุด";
      } else {
        hitlText = "📋 การวิเคราะห์สถิติพหุศาสตร์: ระบบประมวลผลข้อมูลร่วมจากสถิติสุริยยาตร์ โป๊ยหยี่ และจื่อเวย พร้อมแสดงช่วงคะแนนความผันแปร เพื่อรักษาความเที่ยงตรงสูงสุด";
      }
      hitlAlert.textContent = hitlText;
    }
    // Always keep hitl-alert hidden from end users
    hitlAlert.classList.add("hidden");
    hitlAlert.hidden = true;

    // Mirror all technical metadata into the collapsible drawer for experts
    if (drawerMetaMirror) {
      drawerMetaMirror.innerHTML = "";
      metaLines.forEach((line) => {
        const p = makeNode("p", { className: "drawer-meta-line" }, line);
        drawerMetaMirror.appendChild(p);
      });
      if (hitlText) {
        drawerMetaMirror.appendChild(makeNode("p", { className: "drawer-meta-line drawer-meta-hitl" }, hitlText));
      }
    }

    // Show the calculation drawer (collapsed) so experts can expand it
    if (calculationDrawer) {
      calculationDrawer.classList.remove("technical-hidden");
    }
  }

  function renderBaZiCalculationDrawer(data) {
    if (!drawerBaziMirror) {
      return;
    }
    drawerBaziMirror.innerHTML = "";

    const baziChart = data.bazi_chart || data.baziChart || data.bazi;
    if (!baziChart || typeof baziChart !== "object") {
      drawerBaziMirror.classList.add("hidden");
      return;
    }
    drawerBaziMirror.classList.remove("hidden");

    const tenGods = data.bazi_ten_gods || data.ten_gods || baziChart.ten_gods || {};
    const shenSha = data.bazi_shen_sha || data.shen_sha || baziChart.shen_sha || {};
    const hitlFlags = data.hitl_flags || {};
    const isUnknownHour = Boolean(
      baziChart.unknown_hour ||
      hitlFlags.uncertain_birth_time ||
      (state.lastPayload && state.lastPayload.unknown_hour)
    );

    const sectionHeader = makeNode("div", { className: "drawer-bazi-header" });
    const title = makeNode("h4", { className: "drawer-bazi-title" }, "🔮 ผังดวงโป๊ยหยี่ 4 เสาหลัก (BaZi Four Pillars)");
    const subtitle = makeNode(
      "span",
      { className: "drawer-bazi-subtitle" },
      "พลังงานธาตุ ดิถี เทพสิบประการ (Ten Gods) และดาวมงคล/อวมงคล (Shen Sha)"
    );
    sectionHeader.appendChild(title);
    sectionHeader.appendChild(subtitle);
    drawerBaziMirror.appendChild(sectionHeader);

    const grid = makeNode("div", { className: "bazi-pillar-grid" });

    const PILLAR_CONFIG = [
      { key: "year", nameTh: "เสาปี", nameEn: "Year", isDayMaster: false },
      { key: "month", nameTh: "เสาเดือน", nameEn: "Month", isDayMaster: false },
      { key: "day", nameTh: "เสาวัน (ดิถี)", nameEn: "Day", isDayMaster: true },
      { key: "hour", nameTh: "เสาเวลา", nameEn: "Hour", isDayMaster: false },
    ];

    PILLAR_CONFIG.forEach(({ key, nameTh, nameEn, isDayMaster }) => {
      const isThisHourUnknown = key === "hour" && isUnknownHour;
      const cardClass = [
        "bazi-pillar-card",
        isDayMaster ? "is-day-master" : "",
        isThisHourUnknown ? "is-unknown" : "",
      ].filter(Boolean).join(" ");

      const card = makeNode("div", { className: cardClass });

      const cardHeader = makeNode("div", { className: "bazi-pillar-header" });
      cardHeader.appendChild(makeNode("span", { className: "bazi-pillar-name" }, nameTh));
      cardHeader.appendChild(makeNode("span", { className: "bazi-pillar-sub" }, nameEn));
      card.appendChild(cardHeader);

      if (isThisHourUnknown) {
        const unknownMsg = makeNode(
          "div",
          { className: "bazi-char-block is-unknown-block" },
          "ไม่ระบุเวลาเกิด (วิเคราะห์ฐาน 3 เสา)"
        );
        card.appendChild(unknownMsg);
        grid.appendChild(card);
        return;
      }

      // Stem (ราศีบน)
      const stemChar =
        baziChart[`${key}_stem`] ||
        (baziChart.pillars && baziChart.pillars[key] && baziChart.pillars[key].stem) ||
        (baziChart[key] && (baziChart[key].stem || baziChart[key].char)) ||
        "-";
      const stemElement = baziChart[`${key}_element`] || "";
      const stemGod = tenGods.stems ? (tenGods.stems[key] || tenGods.stems[`${key}_stem`]) : null;

      const stemBlock = makeNode("div", { className: "bazi-char-block" });
      const stemRow = makeNode("div", { className: "bazi-char-row" });
      const stemMain = makeNode("div", { className: "bazi-char-main" });
      stemMain.appendChild(makeNode("span", { className: "bazi-chinese-char" }, stemChar));
      if (stemElement) {
        stemMain.appendChild(makeNode("span", { className: "bazi-char-meta" }, stemElement));
      }
      stemRow.appendChild(stemMain);

      if (isDayMaster) {
        const dmBadge = makeNode("span", { className: "ten-god-badge ten-god-dm" }, "[日主] ดิถีตัวตน");
        stemRow.appendChild(dmBadge);
      } else if (stemGod) {
        const godZh = stemGod.zh || "";
        const godName = stemGod.th || stemGod.en || "";
        const godLabel = godZh ? `[${godZh}] ${godName}` : godName;
        if (godLabel) {
          stemRow.appendChild(makeNode("span", { className: "ten-god-badge" }, godLabel));
        }
      }
      stemBlock.appendChild(stemRow);
      card.appendChild(stemBlock);

      // Branch (ราศีล่าง)
      const branchChar =
        baziChart[`${key}_branch`] ||
        (baziChart.pillars && baziChart.pillars[key] && baziChart.pillars[key].branch) ||
        (baziChart[key] && (baziChart[key].branch || baziChart[key].name)) ||
        "-";
      const branchAnimal = baziChart[`${key}_animal`] || "";

      const branchBlock = makeNode("div", { className: "bazi-char-block" });
      const branchRow = makeNode("div", { className: "bazi-char-row" });
      const branchMain = makeNode("div", { className: "bazi-char-main" });
      branchMain.appendChild(makeNode("span", { className: "bazi-chinese-char" }, branchChar));
      if (branchAnimal) {
        branchMain.appendChild(makeNode("span", { className: "bazi-char-meta" }, branchAnimal));
      }
      branchRow.appendChild(branchMain);
      branchBlock.appendChild(branchRow);
      card.appendChild(branchBlock);

      // Hidden Stems (ราศีแฝง)
      const hsList = tenGods.hidden_stems
        ? (tenGods.hidden_stems[key] || tenGods.hidden_stems[`${key}_branch`] || [])
        : [];
      if (Array.isArray(hsList) && hsList.length > 0) {
        const hsContainer = makeNode("div", { className: "hidden-stems-container" });
        hsContainer.appendChild(makeNode("span", { className: "hidden-stems-label" }, "ราศีแฝง (Hidden Stems):"));
        hsList.forEach((hs) => {
          const hsItem = makeNode("div", { className: "hidden-stem-item" });
          const hsInfo = makeNode("div", { className: "hidden-stem-info" });
          hsInfo.appendChild(makeNode("span", { className: "bazi-hs-char" }, hs.stem || "-"));
          const godName = hs.th || hs.en || (hs.ten_god && (hs.ten_god.th || hs.ten_god.zh)) || "";
          const godZh = hs.zh || (hs.ten_god && hs.ten_god.zh) || "";
          const badgeText = godZh ? `[${godZh}] ${godName}` : godName;
          if (badgeText) {
            hsInfo.appendChild(makeNode("span", { className: "ten-god-badge ten-god-badge-sub" }, badgeText));
          }
          hsItem.appendChild(hsInfo);
          const weightPct = hs.weight !== undefined && hs.weight !== null ? `${Math.round(Number(hs.weight) * 100)}%` : "";
          if (weightPct) {
            hsItem.appendChild(makeNode("span", { className: "hidden-stem-weight" }, weightPct));
          }
          hsContainer.appendChild(hsItem);
        });
        card.appendChild(hsContainer);
      }

      // Shen Sha (ดาวจร / เทพประยุกต์)
      const pillarStars = (shenSha.pillars && Array.isArray(shenSha.pillars[key])) ? shenSha.pillars[key] : [];
      const ssContainer = makeNode("div", { className: "shen-sha-container" });
      ssContainer.appendChild(makeNode("span", { className: "shen-sha-label" }, "ดาวประจำเสา (Shen Sha):"));
      if (pillarStars.length > 0) {
        const ssList = makeNode("div", { className: "shen-sha-list" });
        pillarStars.forEach((star) => {
          const isVoid = star.code === "KONG_WANG" || star.category === "void";
          const badgeClass = `shen-sha-badge${isVoid ? " is-void" : ""}`;
          const starLabel = `[${star.zh || ""}] ${star.th || star.en || ""}`.trim();
          ssList.appendChild(makeNode("span", { className: badgeClass }, starLabel));
        });
        ssContainer.appendChild(ssList);
      } else {
        ssContainer.appendChild(makeNode("span", { className: "shen-sha-empty" }, "- ไม่มีดาวพิเศษ -"));
      }
      card.appendChild(ssContainer);

      grid.appendChild(card);
    });

    drawerBaziMirror.appendChild(grid);
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
    const notice = makeNode("p", { className: "topic-conf", role: "note" }, "ℹ️ การคำนวณฐานพลังงาน 3 เสา: กรณีไม่ระบุเวลาเกิด ระบบคำนวณจากเสาปี เดือน และวัน โดยแสดงเป็นช่วงคะแนนความผันแปร");
    resultMeta?.appendChild(notice);
  }

  async function triggerDeepSynthesis(payload, readingData) {
    const card = findById("hitl-deep-synthesis-card");
    if (!card) return;

    const flags = readingData?.hitl_flags || {};
    const isHitl = Boolean(flags.required_human_review || flags.uncertain_birth_time);
    if (!isHitl) {
      card.classList.add("hidden");
      card.hidden = true;
      return;
    }

    card.classList.remove("hidden");
    card.hidden = false;
    card.innerHTML = "";

    const heading = makeNode("h3", {}, "🔮 ผลการวิเคราะห์เชิงลึก (Deep Synthesis) โดย NotebookLM");
    card.appendChild(heading);

    const statusEl = makeNode("div", { className: "deep-synthesis-status", id: "deep-synthesis-status" }, "กำลังเชื่อมต่อฐานความรู้โครงการเพื่อสังเคราะห์ข้อมูลเพิ่มเติม...");
    card.appendChild(statusEl);

    const bodyEl = makeNode("div", { className: "deep-synthesis-body", id: "deep-synthesis-body" });
    card.appendChild(bodyEl);

    try {
      const response = await fetch("/api/v3/hitl-consult", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json().catch(() => ({}));

      if (data.status === "completed" && data.synthesis) {
        statusEl.textContent = "✅ สังเคราะห์ข้อมูลเชิงลึกเรียบร้อยแล้ว (อ้างอิงฐานความรู้ NotebookLM)";
        bodyEl.textContent = data.synthesis;
        if (data.pdf_url) {
          const pdfWrapper = makeNode("p", { style: "margin-top: 14px;" });
          pdfWrapper.appendChild(makeNode("a", {
            href: data.pdf_url,
            target: "_blank",
            rel: "noopener",
            className: "ghost-button",
          }, "📄 ดาวน์โหลดรายงานฉบับเต็ม (PDF)"));
          card.appendChild(pdfWrapper);
        }
      } else if (data.status === "in_progress") {
        statusEl.textContent = "⏳ " + (data.message || "กำลังดำเนินการสังเคราะห์ข้อมูลเชิงลึก กรุณารอสักครู่...");
      } else {
        statusEl.textContent = data.message || "ระบบวิเคราะห์เชิงลึกกำลังมีผู้ใช้งานจำนวนมาก ข้อมูลพื้นดวงหลัก 12 หมวดยังคงพร้อมใช้งานอย่างครบถ้วน";
      }
    } catch {
      statusEl.textContent = "ระบบวิเคราะห์เชิงลึกกำลังมีผู้ใช้งานจำนวนมาก ข้อมูลพื้นดวงหลัก 12 หมวดยังคงพร้อมใช้งานอย่างครบถ้วน";
    }
  }

  const PLAIN_DOMAIN_ICONS = {
    annual_overview: "🌟",
    finance: "💰",
    love: "💖",
    health: "🌿",
    family: "🏡",
    timing: "⏳",
  };

  const PLAIN_DOMAIN_ORDER = [
    "annual_overview",
    "finance",
    "love",
    "health",
    "family",
    "timing",
  ];

  function synthesizeFallbackPlainSummary(data) {
    if (data?.plain_summary && typeof data.plain_summary === "object" && Object.keys(data.plain_summary).length > 0) {
      return data.plain_summary;
    }
    const topics = Array.isArray(data?.topics) ? data.topics : [];
    if (!topics.length) return null;

    const findTopic = (id) => topics.find((t) => t.topic_id === id);
    const getScore = (score) => Math.min(10, Math.max(1, Math.round(Number(score) || 7)));

    const mapping = {
      annual_overview: {
        topic: findTopic("annual_overview") || findTopic("personal_overview_strengths"),
        title: "ภาพรวมดวงชะตา",
        defaultAdvice: "เน้นการวางแผนระยะยาวและมีสติในการดำเนินชีวิต",
      },
      finance: {
        topic: findTopic("finance"),
        title: "การเงินและโชคลาภ",
        defaultAdvice: "จัดสรรงบประมาณอย่างรอบคอบและหลีกเลี่ยงการเก็งกำไรที่ไม่แน่นอน",
      },
      love: {
        topic: findTopic("love_relationships"),
        title: "ความรักและความสัมพันธ์",
        defaultAdvice: "เปิดใจสื่อสารด้วยความเข้าใจและความจริงใจต่อคนรอบข้าง",
      },
      health: {
        topic: findTopic("health_wellbeing"),
        title: "สุขภาพและการพักผ่อน",
        defaultAdvice: "ใส่ใจการพักผ่อนให้เพียงพอและรักษาสมดุลของร่างกาย",
      },
      family: {
        topic: findTopic("family_surrounding_people"),
        title: "ครอบครัวและกัลยาณมิตร",
        defaultAdvice: "ดูแลความสัมพันธ์กับคนใกล้ชิดเพื่อเป็นพลังใจสำคัญ",
      },
      timing: {
        topic: findTopic("opportunities_caution_periods") || findTopic("twelve_month_roadmap"),
        title: "จังหวะชีวิตและโอกาส",
        defaultAdvice: "จับจังหวะเวลาที่เหมาะสมในการเริ่มสิ่งใหม่ด้วยความรอบคอบ",
      },
    };

    const result = {};
    for (const [key, conf] of Object.entries(mapping)) {
      const t = conf.topic;
      result[key] = {
        title: t?.title || conf.title,
        score: getScore(t?.score || 7),
        conversational_text: t?.summary || "จังหวะชีวิตอยู่ในเกณฑ์ที่สามารถก้าวหน้าได้ดีด้วยความตั้งใจจริง",
        action_advice: t?.guidance || conf.defaultAdvice,
      };
    }
    return result;
  }

  function renderPlainSummary(plainSummary) {
    if (!plainSummarySection || !plainSummaryContainer) return;
    if (!plainSummary || typeof plainSummary !== "object") {
      plainSummarySection.classList.add("hidden");
      plainSummarySection.hidden = true;
      plainSummaryContainer.innerHTML = "";
      return;
    }

    plainSummaryContainer.innerHTML = "";
    plainSummarySection.classList.remove("hidden");
    plainSummarySection.hidden = false;

    PLAIN_DOMAIN_ORDER.forEach((key) => {
      const domain = plainSummary[key];
      if (!domain) return;

      const card = makeNode("article", { className: "plain-summary-card", "data-domain": key });

      // Header
      const header = makeNode("div", { className: "plain-card-header" });
      const titleGroup = makeNode("div", { className: "plain-card-title-group" });
      const icon = makeNode("span", { className: "plain-card-icon" }, PLAIN_DOMAIN_ICONS[key] || "✨");
      const title = makeNode("h4", { className: "plain-card-title" }, domain.title || key);
      titleGroup.appendChild(icon);
      titleGroup.appendChild(title);

      const scoreBadge = makeNode("span", { className: "plain-card-score-badge" }, `เกณฑ์พลัง ${domain.score}/10`);
      header.appendChild(titleGroup);
      header.appendChild(scoreBadge);
      card.appendChild(header);

      // Body (Conversational text)
      const body = makeNode("p", { className: "plain-card-body" }, domain.conversational_text || "");
      card.appendChild(body);

      // Action advice
      if (domain.action_advice) {
        const advice = makeNode("div", { className: "plain-card-advice" });
        advice.innerHTML = `<strong>💡 คำแนะนำเชิงปฏิบัติ:</strong> ${domain.action_advice}`;
        card.appendChild(advice);
      }

      plainSummaryContainer.appendChild(card);
    });
  }

  function syncGenderPills() {
    if (!genderPillsContainer || !genderAtBirth) return;
    const currentVal = genderAtBirth.value || "";
    const pills = genderPillsContainer.querySelectorAll(".gender-pill");
    pills.forEach((pill) => {
      const pillVal = pill.getAttribute("data-gender") ?? "";
      const isActive = pillVal === currentVal;
      pill.setAttribute("aria-pressed", isActive ? "true" : "false");
      pill.classList.toggle("is-active", isActive);
    });
  }

  function setupGenderPills() {
    if (!genderPillsContainer || !genderAtBirth) return;
    const pills = genderPillsContainer.querySelectorAll(".gender-pill");
    pills.forEach((pill) => {
      pill.addEventListener("click", () => {
        const val = pill.getAttribute("data-gender") ?? "";
        genderAtBirth.value = val;
        syncGenderPills();
        const event = new Event("change", { bubbles: true });
        genderAtBirth.dispatchEvent(event);
      });
    });
    genderAtBirth.addEventListener("change", syncGenderPills);
    syncGenderPills();
  }

  function openFateBookModal() {
    if (!fateBookModal || !modalPromptContent) return;
    const promptText = state.lastResult?.fate_book_prompt || "ไม่พบข้อมูล Master Prompt สำหรับผังดวงนี้ กรุณาลองคำนวณใหม่อีกครั้ง";
    modalPromptContent.textContent = promptText;
    if (typeof fateBookModal.showModal === "function") {
      fateBookModal.showModal();
    } else {
      fateBookModal.setAttribute("open", "");
    }
  }

  function closeFateBookModal() {
    if (!fateBookModal) return;
    if (typeof fateBookModal.close === "function") {
      fateBookModal.close();
    } else {
      fateBookModal.removeAttribute("open");
    }
  }

  async function copyFateBookPrompt() {
    if (!modalPromptContent || !btnCopyModalPrompt) return;
    const text = modalPromptContent.textContent || "";
    let copied = false;

    if (navigator.clipboard && typeof navigator.clipboard.writeText === "function") {
      try {
        await navigator.clipboard.writeText(text);
        copied = true;
      } catch {
        copied = false;
      }
    }

    if (!copied) {
      try {
        const tempArea = document.createElement("textarea");
        tempArea.value = text;
        tempArea.style.position = "fixed";
        tempArea.style.opacity = "0";
        document.body.appendChild(tempArea);
        tempArea.select();
        copied = document.execCommand("copy");
        document.body.removeChild(tempArea);
      } catch {
        copied = false;
      }
    }

    if (copied) {
      if (copyToastMessage) {
        copyToastMessage.classList.remove("hidden");
        copyToastMessage.hidden = false;
      }
      const prevText = btnCopyModalPrompt.textContent;
      btnCopyModalPrompt.textContent = "✅ คัดลอกสำเร็จ!";
      setTimeout(() => {
        if (copyToastMessage) {
          copyToastMessage.classList.add("hidden");
          copyToastMessage.hidden = true;
        }
        btnCopyModalPrompt.textContent = prevText;
      }, 3000);
    }
  }

  function setupFateBookModal() {
    if (!btnViewFateBook || !fateBookModal) return;

    btnViewFateBook.addEventListener("click", openFateBookModal);
    btnCloseModal?.addEventListener("click", closeFateBookModal);
    btnCloseModalFooter?.addEventListener("click", closeFateBookModal);
    btnCopyModalPrompt?.addEventListener("click", copyFateBookPrompt);

    fateBookModal.addEventListener("click", (event) => {
      if (event.target === fateBookModal) {
        closeFateBookModal();
      }
    });

    fateBookModal.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        closeFateBookModal();
      }
    });
  }

  function renderResult(data) {
    state.lastResult = data;
    window.horoLiteLastPayload = state.lastPayload;
    window.horoLiteLastResult = data;
    renderResultOutputRaw(data);
    renderResultMeta(data);
    renderBaZiCalculationDrawer(data);
    renderTechnicalBasis(data);
    renderPlainSummary(synthesizeFallbackPlainSummary(data));
    renderTopics(data);
    renderUnknownHourNotice(data);

    if (!data.topics || !data.topics.length) {
      setStatus("ผลลัพธ์ว่างจาก API", "warning");
      return;
    }
    setStatus("✨ ผลวิเคราะห์ดวงชะตาของคุณพร้อมแล้ว", "success");
    if (state.feedbackByPattern && Object.keys(state.feedbackByPattern).length > 0) {
      persistFeedbackIfConsented();
    }
  }

  const IDEMPOTENCY_STORAGE_PREFIX = "horo_consult_submit_";
  const SUBMIT_COOLDOWN_SECONDS = 15;

  function getSubmitDedupKey(payload) {
    return `${payload.birth_date}_${payload.birth_time || ""}_${payload.birth_place || ""}_${payload.target_year}_${payload.display_name || ""}`;
  }

  function getRemainingSubmitCooldown(key) {
    try {
      const last = window.sessionStorage.getItem(IDEMPOTENCY_STORAGE_PREFIX + key);
      if (!last) return 0;
      const elapsedSec = (Date.now() - Number(last)) / 1000;
      const remaining = Math.ceil(SUBMIT_COOLDOWN_SECONDS - elapsedSec);
      return remaining > 0 ? remaining : 0;
    } catch {
      return 0;
    }
  }

  function recordSubmitCooldown(key) {
    try {
      window.sessionStorage.setItem(IDEMPOTENCY_STORAGE_PREFIX + key, String(Date.now()));
    } catch {
      // ignore
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
    const idempKey = getSubmitDedupKey(payload);
    const remaining = getRemainingSubmitCooldown(idempKey);
    if (remaining > 0) {
      setStatus(`กำลังดำเนินการวิเคราะห์เชิงลึก กรุณารอการแจ้งเตือนสักครู่... (${remaining} วินาที)`, "warning");
      return;
    }
    recordSubmitCooldown(idempKey);

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
      triggerDeepSynthesis(payload, data);
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
    setupGenderPills();
    setupFateBookModal();
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
