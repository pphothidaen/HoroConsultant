(function () {
  "use strict";

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
    "อุดรธานี": { latitude: 17.4138, longitude: 102.7872, timezone: "Asia/Bangkok" }
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

  function normalizePlace(value) {
    return value.trim().toLowerCase();
  }

  function updateStatus(message, mode) {
    statusMessage.textContent = message;
    statusMessage.classList.toggle("is-error", mode === "error");
    statusMessage.classList.toggle("is-success", mode === "success");
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
    return {
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
      force_human_review: formData.get("force_human_review") === "on"
    };
  }

  async function submitReading(event) {
    event.preventDefault();
    applyPlaceDefault();
    if (!form.reportValidity()) {
      updateStatus("กรุณาตรวจสอบข้อมูลที่จำเป็นก่อนส่งคำขอ", "error");
      return;
    }

    const payload = buildPayload();
    submitButton.disabled = true;
    resultOutput.hidden = true;
    updateStatus("กำลังส่งข้อมูลไปยัง Horo Lite unified reading API...", "loading");

    try {
      const response = await fetch("/api/v3/unified-reading", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        const message = data.detail || data.message || "ไม่สามารถคำนวณผลลัพธ์ได้";
        throw new Error(Array.isArray(message) ? JSON.stringify(message) : String(message));
      }

      updateStatus("ได้รับผลลัพธ์จาก API แล้ว", "success");
      resultOutput.hidden = false;
      resultOutput.textContent = JSON.stringify(data, null, 2);
    } catch (error) {
      updateStatus(error.message || "เกิดข้อผิดพลาดระหว่างส่งคำขอ", "error");
    } finally {
      submitButton.disabled = false;
    }
  }

  function initializeDefaults() {
    targetYear.value = String(new Date().getFullYear());
    if (!birthPlace.value) {
      birthPlace.value = "Bangkok, Thailand";
    }
    applyPlaceDefault();
    syncUnknownHour();
  }

  birthPlace.addEventListener("change", applyPlaceDefault);
  birthPlace.addEventListener("blur", applyPlaceDefault);
  unknownHour.addEventListener("change", syncUnknownHour);
  form.addEventListener("submit", submitReading);
  initializeDefaults();
})();
