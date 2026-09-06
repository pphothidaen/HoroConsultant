(function () {
  "use strict";

  const CANVAS_WIDTH = 1080;
  const STORY_HEIGHT = 1920;
  const BASE_MARGIN = 48;
  const BASE_LINE_HEIGHT = 30;
  const BASE_FONT = '18px "Noto Sans Thai", "Prompt", "Kanit", sans-serif';
  const BODY_FONT = '16px "Noto Sans Thai", "Prompt", "Kanit", sans-serif';
  const SMALL_FONT = '14px "Noto Sans Thai", "Prompt", "Kanit", sans-serif';
  const TITLE_FONT = '700 28px "Noto Sans Thai", "Prompt", "Kanit", sans-serif';
  const SUBTITLE_FONT = '600 18px "Noto Sans Thai", "Prompt", "Kanit", sans-serif';
  const PAGE_BG = "#f8fafc";
  const SURFACE_BG = "#ffffff";
  const TEXT_PRIMARY = "#0f172a";
  const TEXT_SECONDARY = "#334155";

  const DEFAULT_COPY_TEXT = "ข้อมูลวัน/เวลาเกิดซ่อนเพื่อความเป็นส่วนตัว";

  const MONTH_LABEL = [
    "มกราคม",
    "กุมภาพันธ์",
    "มีนาคม",
    "เมษายน",
    "พฤษภาคม",
    "มิถุนายน",
    "กรกฎาคม",
    "สิงหาคม",
    "กันยายน",
    "ตุลาคม",
    "พฤศจิกายน",
    "ธันวาคม",
  ];

  function sanitizeText(value) {
    if (value === null || value === undefined) {
      return "-";
    }
    return String(value).trim() || "-";
  }

  function getRequestPayload() {
    return (
      window.horoLiteLastPayload ||
      window.horoLiteLastRequest ||
      window.horoLitePayload ||
      {}
    );
  }

  function clamp(value, min, max) {
    if (typeof value !== "number" || Number.isNaN(value)) {
      return min;
    }
    return Math.min(max, Math.max(min, value));
  }

  function wrapText(ctx, text, maxWidth) {
    const safeText = sanitizeText(text);
    if (safeText === "-" || !safeText.length || maxWidth <= 0) {
      return [safeText];
    }
    const words = safeText.split(/\s+/);
    const lines = [];
    let line = "";
    words.forEach((word) => {
      const candidate = line ? `${line} ${word}` : word;
      if (ctx.measureText(candidate).width <= maxWidth) {
        line = candidate;
      } else {
        if (line) {
          lines.push(line);
          line = word;
        } else {
          lines.push(word);
          line = "";
        }
      }
    });
    if (line) {
      lines.push(line);
    }
    return lines.length ? lines : [safeText];
  }

  function normalizeConfidence(confidence) {
    const value = String(confidence || "MEDIUM").toUpperCase();
    if (value === "HIGH") {
      return "สูง";
    }
    if (value === "LOW") {
      return "ต่ำ";
    }
    return "ปานกลาง";
  }

  function orderedTopics(result) {
    const topics = Array.isArray(result?.topics) ? [...result.topics] : [];
    return topics.sort(
      (a, b) => Number(a?.order || 0) - Number(b?.order || 0),
    );
  }

  function buildTopicLine(topic) {
    if (!topic) {
      return [];
    }
    const lines = [];
    const title = sanitizeText(topic.title || topic.topic_id || "-");
    const summary = sanitizeText(topic.summary || "");
    const guidance = sanitizeText(topic.guidance || "");
    const confidence = normalizeConfidence(topic.confidence);
    const topicId = sanitizeText(topic.topic_id || "");
    const evidenceRefs = Array.isArray(topic.evidence_refs)
      ? topic.evidence_refs
      : [];

    lines.push(`- ${title}`);
    lines.push(`  ความมั่นใจ: ${confidence}`);
    if (topicId === "personal_overview_strengths" || topicId === "annual_overview") {
      lines.push(`  โฟกัส: ${summary}`);
    } else {
      lines.push(`  สรุป: ${summary}`);
    }
    if (guidance) {
      lines.push(`  คำแนะนำ: ${guidance}`);
    }
    if (evidenceRefs.length) {
      lines.push(`  แหล่งอ้างอิง: ${evidenceRefs.join(", ")}`);
    }

    return lines;
  }

  function buildPastPatternLines(topics) {
    const lines = [];
    const patterns = Array.isArray(topics?.past_patterns)
      ? topics.past_patterns
      : [];
    if (!patterns.length) {
      return lines;
    }
    lines.push("ประวัติย้อนหลังที่อาจช่วยไตร่ตรอง:");
    patterns.forEach((pattern, index) => {
      const theme = sanitizeText(pattern.theme || "theme");
      const years = `${pattern.year_range?.[0] || "-"}`;
      const yearTo = pattern.year_range?.[1];
      const ageFrom = pattern.age_range?.[0];
      const ageTo = pattern.age_range?.[1];
      const yearRange = yearTo ? `${years}-${sanitizeText(yearTo)}` : years;
      const ageRange = ageFrom && ageTo ? `${sanitizeText(ageFrom)}-${sanitizeText(ageTo)} ปี` : "-";
      lines.push(`${index + 1}. ${theme} (${yearRange}) / อายุ ${ageRange}`);
    });
    return lines;
  }

  function buildMonthlyRoadmapLines(topics) {
    const monthly = Array.isArray(topics?.monthly_scores) ? topics.monthly_scores : [];
    if (!monthly.length) {
      return [];
    }
    const rows = [
      "แนวโน้มรายเดือน (12 เดือน) - รูปแบบคะแนน (งาน/การเงิน/รัก)",
    ];
    const orderedMonths = [...monthly].sort((a, b) => Number(a.month || 0) - Number(b.month || 0));
    orderedMonths.forEach((item, index) => {
      const monthNo = sanitizeText(item.month || index + 1);
      const monthText = MONTH_LABEL[clamp(Number(item.month || 1) - 1, 0, 11)] || `เดือน ${monthNo}`;
      const career = item.career_score ?? item.career_range?.[0] ?? "-";
      const finance = item.finance_score ?? item.finance_range?.[0] ?? "-";
      const love = item.love_score ?? item.love_range?.[0] ?? "-";
      rows.push(`  ${monthText}: ${career}/${finance}/${love}`);
    });
    return rows;
  }

  function gatherExportText(result, options = {}) {
    const includeBirthDetails = Boolean(options.includeBirthDetails);
    const payload = getRequestPayload();
    const lines = [];
    const targetYear = sanitizeText(result?.target_year || "-");
    const schemaVersion = sanitizeText(result?.schema_version || "horo_lite_unified_reading.v1");
    const requestId = sanitizeText(result?.request_id || "-");
    const consensus = Number(result?.consensus_metadata?.consensus_score ?? 0);
    const routing = sanitizeText(result?.hitl_routing?.status || "N/A");
    const requiredHitl = Boolean(result?.hitl_flags?.required_human_review);
    const topics = orderedTopics(result);

    lines.push("Horo Lite Summary");
    lines.push(`เวอร์ชันข้อมูล: ${schemaVersion}`);
    lines.push(`ปีที่ตีความ: ${targetYear}`);
    lines.push(`รหัสผลลัพธ์: ${requestId}`);
    lines.push(`Consensus: ${(Number.isFinite(consensus) ? consensus.toFixed(2) : String(consensus || "-"))}`);
    lines.push(`HITL: ${routing}${requiredHitl ? " (ต้องรีวิว)" : ""}`);
    lines.push("");

    if (includeBirthDetails && payload && (payload.birth_date || payload.birth_time || payload.birth_place || payload.location)) {
      lines.push(`วันเกิด: ${sanitizeText(payload.birth_date || "-")}`);
      lines.push(`เวลาเกิด: ${sanitizeText(payload.birth_time || "-")}`);
      lines.push(`สถานที่เกิด: ${sanitizeText(payload.birth_place || payload.location || "-")}`);
      lines.push(`โซนเวลา: ${sanitizeText(payload.timezone || "-")}`);
      lines.push("");
    } else {
      lines.push(DEFAULT_COPY_TEXT);
      lines.push("");
    }

    topics.forEach((topic) => {
      const topicLines = buildTopicLine(topic);
      lines.push(...topicLines);
      lines.push("");
    });

    lines.push(...buildPastPatternLines(result));
    if (buildPastPatternLines(result).length) {
      lines.push("");
    }
    const roadmap = buildMonthlyRoadmapLines(result);
    if (roadmap.length) {
      lines.push(...roadmap);
      lines.push("");
    }

    return lines;
  }

  function drawCanvas(canvas, result, options = {}) {
    const includeBirthDetails = Boolean(options.includeBirthDetails);
    const lines = gatherExportText(result, { includeBirthDetails });
    const ctx = canvas.getContext("2d");
    if (!ctx) {
      throw new Error("Canvas context not available");
    }

    const width = Number(canvas.width);
    const height = Number(canvas.height);
    const margin = BASE_MARGIN;

    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = PAGE_BG;
    ctx.fillRect(0, 0, width, height);

    const insetX = width - margin * 2;
    const insetY = height - margin * 2;
    const cardBg = SURFACE_BG;
    ctx.fillStyle = cardBg;
    ctx.beginPath();
    ctx.roundRect(margin, margin, insetX, insetY, 14);
    ctx.fill();

    let y = margin + 36;
    const maxWidth = width - margin * 2 - 20;
    const lineHeight = BASE_LINE_HEIGHT;

    function addWrapped(text, font, color, indent = 0) {
      ctx.fillStyle = color;
      ctx.font = font;
      const x = margin + 18 + indent;
      const effectiveWidth = Math.max(120, maxWidth - indent);
      const wrapped = wrapText(ctx, text, effectiveWidth);
      wrapped.forEach((segment) => {
        if (y > height - 28) {
          return;
        }
        ctx.fillText(segment, x, y);
        y += lineHeight;
      });
    }

    addWrapped("Horo Lite | รายงานภาพ", TITLE_FONT, TEXT_PRIMARY, 0);
    addWrapped(`รายงานสังเคราะห์ 12 โมดูล`, SUBTITLE_FONT, TEXT_SECONDARY, 0);
    y += 14;
    lines.forEach((line) => {
      const font = line && line.startsWith("  ") ? SMALL_FONT : BASE_FONT;
      const color = line.startsWith("  ") || line.startsWith("- ")
        ? TEXT_SECONDARY
        : line.match(/^Horo Lite Summary|^- |^1\.|^2\.|^3\.|^4\.|^5\.|^6\.|^7\.|^8\.|^9\.|^10\./)
        ? TEXT_PRIMARY
        : TEXT_PRIMARY;
      addWrapped(line, font, color, line.startsWith("  ") ? 20 : 0);
      if (line === "") {
        y += 2;
      }
    });

    if (y > height - 24) {
      return;
    }
    ctx.fillStyle = TEXT_SECONDARY;
    ctx.font = SMALL_FONT;
    ctx.fillText("สร้างจาก Horo Lite • สร้างภาพสรุปเพื่อการแชร์อย่างระมัดระวัง", margin + 14, height - 22);
  }

  function estimateCanvasHeight(result, options = {}) {
    const lines = gatherExportText(result, { includeBirthDetails: Boolean(options.includeBirthDetails) });
    const maxLineCount = lines.length + 6;
    const estimatedHeight = 120 + maxLineCount * BASE_LINE_HEIGHT;
    return clamp(estimatedHeight, 1400, 4200);
  }

  function createCanvas(width, height) {
    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    return canvas;
  }

  function triggerDownload(canvas, filename) {
    return new Promise((resolve, reject) => {
      if (typeof canvas.toBlob === "function") {
        canvas.toBlob((blob) => {
          if (!blob) {
            reject(new Error("ไม่สามารถสร้างไฟล์ PNG ได้"));
            return;
          }
          const url = URL.createObjectURL(blob);
          const anchor = document.createElement("a");
          anchor.href = url;
          anchor.download = filename;
          document.body.appendChild(anchor);
          anchor.click();
          anchor.remove();
          setTimeout(() => URL.revokeObjectURL(url), 750);
          resolve({ filename, width: canvas.width, height: canvas.height });
        }, "image/png");
        return;
      }

      const fallback = canvas.toDataURL("image/png");
      const anchor = document.createElement("a");
      anchor.href = fallback;
      anchor.download = filename;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      resolve({ filename, width: canvas.width, height: canvas.height });
    });
  }

  function buildFilename(prefix, result) {
    const year = sanitizeText(result?.target_year || new Date().getFullYear());
    const now = new Date();
    const safeTs = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, "0")}${String(now.getDate()).padStart(2, "0")}_${String(now.getHours()).padStart(2, "0")}${String(now.getMinutes()).padStart(2, "0")}${String(now.getSeconds()).padStart(2, "0")}`;
    return `${prefix}-${year}-${safeTs}.png`;
  }

  async function exportFullPng(result, options = {}) {
    if (!result) {
      throw new Error("Missing result for full export.");
    }
    const includeBirthDetails = Boolean(options.includeBirthDetails);
    const height = estimateCanvasHeight(result, { includeBirthDetails });
    const canvas = createCanvas(CANVAS_WIDTH, height);
    drawCanvas(canvas, result, { includeBirthDetails });
    return triggerDownload(canvas, buildFilename("horo-lite-full", result));
  }

  async function exportStoryPng(result, options = {}) {
    if (!result) {
      throw new Error("Missing result for story export.");
    }
    const includeBirthDetails = Boolean(options.includeBirthDetails);
    const canvas = createCanvas(CANVAS_WIDTH, STORY_HEIGHT);
    const lines = gatherExportText(result, { includeBirthDetails });
    const contentHeight = Math.max(800, 120 + lines.length * BASE_LINE_HEIGHT);
    const requiredHeight = Math.max(contentHeight + 120, 120);
    const ctx = canvas.getContext("2d");
    if (!ctx) {
      throw new Error("Canvas context not available");
    }
    const tempCanvas = document.createElement("canvas");
    tempCanvas.width = CANVAS_WIDTH;
    tempCanvas.height = Math.round(requiredHeight);
    drawCanvas(tempCanvas, result, { includeBirthDetails });
    const sourceHeight = Math.min(STORY_HEIGHT, tempCanvas.height);
    ctx.drawImage(
      tempCanvas,
      0,
      0,
      CANVAS_WIDTH,
      sourceHeight,
      0,
      0,
      CANVAS_WIDTH,
      sourceHeight,
    );
    if (sourceHeight < STORY_HEIGHT) {
      const fillHeight = STORY_HEIGHT - sourceHeight;
      ctx.fillStyle = PAGE_BG;
      ctx.fillRect(0, sourceHeight, CANVAS_WIDTH, fillHeight);
    }
    return triggerDownload(canvas, buildFilename("horo-lite-story", result));
  }

  async function copySocialSummary(result, options = {}) {
    if (!result) {
      throw new Error("Missing result for social copy.");
    }
    const includeBirthDetails = Boolean(options.includeBirthDetails);
    const lines = gatherExportText(result, { includeBirthDetails });
    const text = lines.join("\n");
    if (navigator.clipboard && typeof navigator.clipboard.writeText === "function") {
      await navigator.clipboard.writeText(text);
      return { copied: true, text };
    }
    const tempArea = document.createElement("textarea");
    tempArea.value = text;
    tempArea.setAttribute("readonly", "1");
    tempArea.style.position = "fixed";
    tempArea.style.left = "-9999px";
    document.body.appendChild(tempArea);
    tempArea.select();
    let copied = false;
    try {
      copied = document.execCommand("copy");
    } finally {
      tempArea.remove();
    }
    return { copied, text };
  }

  function renderPrintableSummary(result, options = {}) {
    const includeBirthDetails = Boolean(options.includeBirthDetails);
    const lines = gatherExportText(result, { includeBirthDetails });
    const safeEscaped = lines
      .map((line) => line.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"))
      .join("<br/>");
    return `
      <!doctype html>
      <html lang="th">
        <head>
          <meta charset="utf-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1" />
          <title>Horo Lite Print Report</title>
          <link rel="stylesheet" href="/export_modal.css" />
          <style>
            body { margin: 0; background: #fff; color: #0f172a; }
            .horo-lite-print { padding: 20px; }
            .horo-lite-print pre { white-space: pre-wrap; line-height: 1.4; }
            .horo-lite-print-header { font-family: "Noto Sans Thai","Prompt","Kanit",sans-serif; font-weight: 700; font-size: 28px; margin: 0 0 10px 0; }
          </style>
        </head>
        <body>
          <main class="horo-lite-print">
            <h1 class="horo-lite-print-header">Horo Lite — รายงานพิมพ์</h1>
            <p>ผลลัพธ์นี้ใช้เพื่อการอ่านสรุปและแบ่งปันอย่างมีความรับผิดชอบ</p>
            <pre>${safeEscaped}</pre>
            <script>
              window.addEventListener("load", function () {
                requestAnimationFrame(() => window.print());
              });
            </script>
          </main>
        </body>
      </html>
    `;
  }

  async function printResult(result, options = {}) {
    if (!result) {
      throw new Error("Missing result for print.");
    }
    const includeBirthDetails = Boolean(options.includeBirthDetails);
    const win = window.open("", "_blank", "noopener,noreferrer");
    if (!win) {
      throw new Error("ไม่สามารถเปิดหน้าต่างพิมพ์ได้");
    }
    win.document.open();
    win.document.write(renderPrintableSummary(result, { includeBirthDetails }));
    win.document.close();
    return true;
  }

  window.horoLiteExport = {
    exportFullPng,
    exportStoryPng,
    copySocialSummary,
    printResult,
  };
})();
