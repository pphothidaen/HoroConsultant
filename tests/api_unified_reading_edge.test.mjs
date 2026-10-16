/**
 * tests/api_unified_reading_edge.test.mjs
 *
 * TICKET-FIX-003: Contract and edge fallback test suite for Horo Lite Unified Reading.
 * Pins contract guarantees for:
 *   1. User Scenario: birth_date: 2026-10-15, unknown_hour: true, display_name: jack, target_year: 2026
 *   2. Adult Scenario: birth_date: 1990-05-15, birth_time: 10:30, unknown_hour: false
 *   3. Gateway 503 Fallback: Render Service Suspended -> seamless HTTP 200 via edge fallback
 *   4. Gateway Unreachable Fallback: upstream network error -> seamless HTTP 200 via edge fallback
 *   5. Negative Validation: birth_date in future relative to target_year -> HTTP 422 error
 *   6. Latency and deterministic performance invariant (< 300ms SLA)
 */

import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import test from "node:test";

import {
  CANONICAL_TOPIC_IDS,
  createUnifiedReading,
  requestIdFor,
} from "../api/unified_reading_engine.js";

const CANONICAL_RENDER = "https://horoconsultant-core-backend.onrender.com";
const INDEX_MODULE_URL = new URL("../api/index.js", import.meta.url).href;

function runGateway(testCase) {
  const script = `
    const testCase = JSON.parse(process.env.TEST_CASE);
    const handler = (await import(${JSON.stringify(INDEX_MODULE_URL)})).default;
    const headers = new Map();
    const response = {
      statusCode: null,
      body: undefined,
      setHeader(name, value) { headers.set(name.toLowerCase(), value); },
      getHeader(name) { return headers.get(name.toLowerCase()); },
      getHeaders() { return Object.fromEntries(headers.entries()); },
      status(code) { this.statusCode = code; return this; },
      json(body) { this.body = body; return this; },
      send(body) { this.body = Buffer.isBuffer(body) ? { bytes: body.length } : body; return this; },
      end(body) { this.body = body; return this; },
    };
    const request = {
      method: testCase.method || "POST",
      headers: testCase.headers || { "content-type": "application/json" },
      url: testCase.url || "/api/index?path=/api/v3/unified-reading",
    };
    if (testCase.body !== undefined) {
      request.body = typeof testCase.body === "string" ? testCase.body : JSON.stringify(testCase.body);
    }
    console.log = (...args) => process.stderr.write(args.join(" ") + "\\n");
    console.info = (...args) => process.stderr.write(args.join(" ") + "\\n");
    console.warn = (...args) => process.stderr.write(args.join(" ") + "\\n");
    const calls = [];
    globalThis.fetch = async (url, options) => {
      calls.push({ url, method: options.method });
      const plan = testCase.upstreams || [];
      for (const entry of plan) {
        if (entry.match && url.startsWith(entry.match)) {
          if (entry.throw) throw new Error("upstream unreachable / network failure");
          return new Response(entry.body || "Service Unavailable - Render Suspended", {
            status: entry.status || 503,
            headers: {
              "content-type": entry.contentType || "text/plain",
              "x-request-id": entry.requestId || "upstream-correlation-123",
            },
          });
        }
      }
      return new Response("ok", { status: 200, headers: { "content-type": "application/json" } });
    };
    await handler(request, response);
    process.stdout.write(JSON.stringify({
      calls,
      statusCode: response.statusCode,
      headers: response.getHeaders ? response.getHeaders() : Object.fromEntries(headers.entries()),
      body: response.body,
    }));
  `;
  const environment = { ...process.env, TEST_CASE: JSON.stringify(testCase) };
  environment.RENDER_BACKEND_URL = testCase.render === null ? "" : (testCase.render || CANONICAL_RENDER);
  const result = spawnSync(process.execPath, ["--input-type=module", "--eval", script], {
    env: environment,
    encoding: "utf8",
  });
  assert.equal(result.status, 0, `Gateway subprocess failed: ${result.stderr}`);
  return JSON.parse(result.stdout);
}

test("User Scenario: birth_date 2026-10-15, unknown_hour true, display_name jack, target_year 2026", () => {
  const payload = {
    birth_date: "2026-10-15",
    unknown_hour: true,
    display_name: "jack",
    target_year: 2026,
  };

  const reading = createUnifiedReading(payload);

  // 1. Schema version and request ID
  assert.equal(reading.schema_version, "horo_lite_unified_reading.v1");
  assert.match(reading.request_id, /^unified-reading-[a-f0-9]{20}$/);
  assert.equal(reading.target_year, 2026);

  // 2. Exactly 12 canonical topics in exact order with 100% Thai titles
  assert.equal(reading.topics.length, 12);
  const actualTopicIds = reading.topics.map((t) => t.topic_id);
  assert.deepEqual(actualTopicIds, CANONICAL_TOPIC_IDS);
  assert.equal(reading.topics[0].title, "ภาพรวมตัวตนและจุดแข็งพื้นดวง");

  for (const topic of reading.topics) {
    assert.ok(topic.topic_id, "topic_id must be non-empty");
    assert.ok(topic.title, `Topic ${topic.topic_id} missing title`);
    assert.ok(/[\u0e00-\u0e7f]/.test(topic.title), `Topic ${topic.topic_id} title must be in Thai: ${topic.title}`);
    assert.ok(typeof topic.summary === "string" && topic.summary.length > 0, `Topic ${topic.topic_id} missing summary`);
    assert.ok(/[\u0e00-\u0e7f]/.test(topic.summary), `Topic ${topic.topic_id} summary must be in Thai: ${topic.summary}`);
    assert.ok(typeof topic.guidance === "string" && topic.guidance.length > 0, `Topic ${topic.topic_id} missing guidance`);
    assert.ok(/[\u0e00-\u0e7f]/.test(topic.guidance), `Topic ${topic.topic_id} guidance must be in Thai: ${topic.guidance}`);
    assert.ok(["HIGH", "MEDIUM", "LOW"].includes(topic.confidence), `Topic ${topic.topic_id} invalid confidence`);
    assert.ok(Array.isArray(topic.evidence_refs) && topic.evidence_refs.length > 0);
  }

  // 3. Exactly 12 monthly scores in [1, 10] with Thai evidence reasons
  assert.equal(reading.monthly_scores.length, 12);
  for (let m = 1; m <= 12; m++) {
    const item = reading.monthly_scores[m - 1];
    assert.equal(item.month, m);
    assert.ok(item.career_score >= 1 && item.career_score <= 10, `Month ${m} career_score out of range [1, 10]: ${item.career_score}`);
    assert.ok(item.finance_score >= 1 && item.finance_score <= 10, `Month ${m} finance_score out of range [1, 10]: ${item.finance_score}`);
    assert.ok(item.love_score >= 1 && item.love_score <= 10, `Month ${m} love_score out of range [1, 10]: ${item.love_score}`);

    // Score ranges must be present since unknown_hour is true
    assert.ok(Array.isArray(item.career_score_range), `Month ${m} missing career_score_range`);
    assert.ok(Array.isArray(item.finance_score_range), `Month ${m} missing finance_score_range`);
    assert.ok(Array.isArray(item.love_score_range), `Month ${m} missing love_score_range`);
    assert.equal(item.career_score_range.length, 2);
    assert.ok(item.career_score_range[0] <= item.career_score_range[1]);

    // Monthly reasons must contain Thai text (BaZi pillar, Suriyayart transit)
    assert.ok(Array.isArray(item.reasons) && item.reasons.length >= 2, `Month ${m} missing reasons`);
    assert.ok(item.reasons.some((r) => /[\u0e00-\u0e7f]/.test(r)), `Month ${m} reasons must contain Thai text: ${JSON.stringify(item.reasons)}`);
    assert.ok(item.reasons.some((r) => r.includes("สุริยยาตร์") || r.includes("เสาพลังงานเดือน")), `Month ${m} reasons must contain Thai astrological basis`);
  }

  // 4. Consensus metadata
  assert.ok(reading.consensus_metadata, "consensus_metadata missing");
  assert.ok(typeof reading.consensus_metadata.consensus_score === "number");
  assert.ok(reading.consensus_metadata.consensus_score >= 0 && reading.consensus_metadata.consensus_score <= 1);
  assert.ok(reading.consensus_metadata.arbitration_status);
  assert.ok(Array.isArray(reading.consensus_metadata.traditions_considered));

  // 5. HITL flags
  assert.ok(reading.hitl_flags, "hitl_flags missing");
  assert.equal(reading.hitl_flags.uncertain_birth_time, true);
  assert.equal(reading.hitl_flags.required_human_review, true);

  // 6. Insufficient history reason for infant/target year birth contains Thai and preserves "insufficient history"
  assert.ok(typeof reading.insufficient_history_reason === "string");
  assert.ok(/[\u0e00-\u0e7f]/.test(reading.insufficient_history_reason), "insufficient_history_reason must contain Thai text");
  assert.match(reading.insufficient_history_reason, /insufficient history/i);
  assert.equal(reading.past_patterns.length, 0);

  // 7. LLM immutability invariants
  assert.equal(reading.llm_metadata.facts_mutable_by_llm, false);

  // 8. Plain Summary Contract (TICKET-FATE-001 / TICKET-FATE-005)
  assert.ok(reading.plain_summary && typeof reading.plain_summary === "object", "plain_summary must be an object");
  const expectedPlainKeys = ["annual_overview", "finance", "love", "health", "family", "timing"];
  const actualPlainKeys = Object.keys(reading.plain_summary);
  assert.deepEqual(actualPlainKeys.sort(), expectedPlainKeys.sort());

  const FORBIDDEN_JARGON = ["ชง", "ฮะ", "ย้งซิ้ง", "ดิถี", "ต้าอวิ้น"];

  for (const key of expectedPlainKeys) {
    const item = reading.plain_summary[key];
    assert.ok(item && typeof item === "object", `plain_summary.${key} must be an object`);
    const textToCheck = `${item.title || ""} ${item.conversational_text || ""} ${item.action_advice || ""}`;
    assert.ok(/[\u0e00-\u0e7f]/.test(textToCheck), `plain_summary.${key} must contain Thai text`);
    for (const jargon of FORBIDDEN_JARGON) {
      assert.ok(!textToCheck.includes(jargon), `plain_summary.${key} contains forbidden astrological jargon "${jargon}": ${textToCheck}`);
    }
  }

  // 9. Fate Book Master Prompt Contract (TICKET-FATE-001 / TICKET-FATE-005)
  assert.ok(typeof reading.fate_book_prompt === "string" && reading.fate_book_prompt.length > 200, "fate_book_prompt must be a non-empty string");
  assert.ok(
    reading.fate_book_prompt.includes("จื่อเวยโต่วซู่") || reading.fate_book_prompt.includes("Zi Wei Dou Shu"),
    "fate_book_prompt must include Zi Wei Dou Shu / จื่อเว่ยโต่วซู่"
  );
  assert.ok(
    reading.fate_book_prompt.includes("12 วัง") || reading.fate_book_prompt.includes("12 วังชะตา") || reading.fate_book_prompt.includes("วังชะตา"),
    "fate_book_prompt must include Zi Wei 12 Palaces"
  );
  assert.ok(
    reading.fate_book_prompt.includes("14 ดาว") || reading.fate_book_prompt.includes("14 ดาวเอก") || reading.fate_book_prompt.includes("ดาวจักรพรรดิ"),
    "fate_book_prompt must include Primary Stars"
  );
  assert.ok(
    reading.fate_book_prompt.includes("Si Hua") || reading.fate_book_prompt.includes("สี่ดาวแปลง") || reading.fate_book_prompt.includes("四化"),
    "fate_book_prompt must include Si Hua"
  );
  assert.ok(
    reading.fate_book_prompt.includes("BaZi") || reading.fate_book_prompt.includes("โป๊ยหยี่") || reading.fate_book_prompt.includes("Four Pillars"),
    "fate_book_prompt must include BaZi 4 pillars"
  );
  assert.ok(
    reading.fate_book_prompt.includes("สุริยยาตร์") || reading.fate_book_prompt.includes("Thai Astrology"),
    "fate_book_prompt must include Thai Suriyayart"
  );
  assert.ok(
    reading.fate_book_prompt.includes("True Solar Time") || reading.fate_book_prompt.includes("สุริยคติจริง"),
    "fate_book_prompt must include True Solar Time"
  );
});

test("Contract Invariant: BaZi Ten Gods (Shi Shen) structural and derivation accuracy", () => {
  const reading = createUnifiedReading({
    birth_date: "1990-05-15",
    birth_time: "10:30",
    unknown_hour: false,
    birth_place: "Bangkok, Thailand",
    target_year: 2026,
  });

  assert.ok(reading.bazi_ten_gods && typeof reading.bazi_ten_gods === "object");
  assert.ok(reading.bazi_ten_gods.stems && typeof reading.bazi_ten_gods.stems === "object");
  assert.ok(reading.bazi_ten_gods.hidden_stems && typeof reading.bazi_ten_gods.hidden_stems === "object");

  for (const pillar of ["year", "month", "day", "hour"]) {
    const god = reading.bazi_ten_gods.stems[pillar];
    assert.ok(god && typeof god === "object", `Ten Gods stem ${pillar} must be an object`);
    for (const field of ["code", "zh", "th"]) {
      assert.ok(typeof god[field] === "string" && god[field].length > 0,
        `Ten Gods stem ${pillar}.${field} must be a non-empty string`);
    }

    const hiddenStems = reading.bazi_ten_gods.hidden_stems[pillar];
    assert.ok(Array.isArray(hiddenStems), `Ten Gods hidden_stems.${pillar} must be an array`);
    for (const item of hiddenStems) {
      assert.ok(typeof item.stem === "string" && item.stem.length > 0,
        `Hidden stem ${pillar} must include a stem`);
      assert.ok(typeof item.weight === "number" && item.weight > 0,
        `Hidden stem ${pillar} weight must be positive`);
      const godObj = item.god || item.ten_god;
      assert.ok(godObj && typeof godObj === "object",
        `Hidden stem ${pillar} must include a god object`);
      for (const field of ["code", "zh", "th"]) {
        assert.ok(typeof godObj[field] === "string" && godObj[field].length > 0,
          `Hidden stem ${pillar}.${field} must be a non-empty string`);
      }
    }
  }

  assert.equal(reading.bazi_ten_gods.stems.day.code, "DM");
  assert.equal(reading.bazi_ten_gods.stems.day.zh, "日主");
});

test("Contract Invariant: BaZi Shen Sha (Auxiliary Stars) structural and derivation accuracy", () => {
  const reading = createUnifiedReading({
    birth_date: "1990-05-15",
    birth_time: "10:30",
    unknown_hour: false,
    birth_place: "Bangkok, Thailand",
    target_year: 2026,
  });

  assert.ok(reading.bazi_shen_sha && typeof reading.bazi_shen_sha === "object");
  assert.ok(reading.bazi_shen_sha.pillars && typeof reading.bazi_shen_sha.pillars === "object");
  assert.ok(Array.isArray(reading.bazi_shen_sha.active_stars));
  for (const pillar of ["year", "month", "day", "hour"]) {
    assert.ok(Array.isArray(reading.bazi_shen_sha.pillars[pillar]),
      `Shen Sha pillars.${pillar} must be an array`);
  }
  assert.ok(reading.bazi_shen_sha.active_stars.length > 0,
    "Shen Sha active_stars must contain detected auxiliary stars");
  for (const star of reading.bazi_shen_sha.active_stars) {
    assert.ok(typeof star.code === "string" && star.code.length > 0,
      "Each active Shen Sha star must contain a detected star code");
  }

  const unknownHourReading = createUnifiedReading({
    birth_date: "1990-05-15",
    unknown_hour: true,
    birth_place: "Bangkok, Thailand",
    target_year: 2026,
  });
  assert.deepEqual(unknownHourReading.bazi_shen_sha.pillars.hour, []);
});

test("Contract Invariant: Fate Book Master Prompt dynamic BaZi synthesis", () => {
  const reading = createUnifiedReading({
    birth_date: "1990-05-15",
    birth_time: "10:30",
    unknown_hour: false,
    birth_place: "Bangkok, Thailand",
    target_year: 2026,
  });
  const prompt = reading.fate_book_prompt;

  assert.ok(typeof prompt === "string");
  assert.ok(prompt.includes("### 1.1 พลังงานสิบเทวดาและดาวเสริมชะตา (BaZi Energy & Auxiliary Stars)"));
  assert.ok(prompt.includes("Ten Gods"));
  for (const star of reading.bazi_shen_sha.active_stars) {
    assert.ok(prompt.includes(star.en) || prompt.includes(star.zh) || prompt.includes(star.code),
      `Fate Book prompt must include active Shen Sha star ${star.code}`);
  }
});

test("Adult Scenario: birth_date 1990-05-15, birth_time 10:30, unknown_hour false", () => {
  const payload = {
    birth_date: "1990-05-15",
    birth_time: "10:30",
    unknown_hour: false,
    birth_place: "Bangkok, Thailand",
    target_year: 2026,
  };

  const reading = createUnifiedReading(payload);

  // 1. Past patterns: 3-5 non-sensitive candidates
  assert.ok(reading.past_patterns.length >= 3 && reading.past_patterns.length <= 5,
    `Expected 3-5 candidates, got ${reading.past_patterns.length}`);

  const allowedThemes = new Set([
    "education",
    "career_shift",
    "relocation",
    "financial_pressure",
    "work_role_change",
  ]);

  for (const candidate of reading.past_patterns) {
    assert.ok(candidate.pattern_id, "Candidate pattern_id missing");
    assert.ok(allowedThemes.has(candidate.theme), `Unexpected candidate theme: ${candidate.theme}`);
    assert.equal(candidate.sensitive_category, false, "Candidate marked sensitive");
    assert.ok(Array.isArray(candidate.year_range) && candidate.year_range.length === 2);
    assert.ok(Array.isArray(candidate.age_range) && candidate.age_range.length === 2);
    assert.deepEqual(candidate.allowed_feedback, ["ตรง", "ตรงบางส่วน", "ไม่ตรง", "จำไม่ได้"]);
  }

  // 2. No score ranges when unknown_hour is false
  for (const item of reading.monthly_scores) {
    assert.equal(item.career_score_range, null);
    assert.equal(item.finance_score_range, null);
    assert.equal(item.love_score_range, null);
  }

  // 3. Insufficient history reason is null for adult
  assert.equal(reading.insufficient_history_reason, null);

  // 4. HITL uncertain_birth_time flag is false
  assert.equal(reading.hitl_flags.uncertain_birth_time, false);
});

test("Gateway 503 Fallback: upstream Render 503 triggers seamless edge fallback with x-fallback-edge header", () => {
  const result = runGateway({
    method: "POST",
    url: "/api/index?path=/api/v3/unified-reading",
    body: {
      birth_date: "2026-10-15",
      unknown_hour: true,
      display_name: "jack",
      target_year: 2026,
    },
    upstreams: [
      { match: CANONICAL_RENDER, status: 503, body: "Service Temporarily Suspended" },
    ],
  });

  assert.equal(result.statusCode, 200, `Expected HTTP 200 from fallback, got ${result.statusCode}`);
  assert.equal(result.headers["x-fallback-edge"], "unified-reading-v1");
  assert.ok(result.headers["x-request-id"]);

  const body = result.body;
  assert.equal(body.schema_version, "horo_lite_unified_reading.v1");
  assert.equal(body.topics.length, 12);
  const topicIds = body.topics.map((t) => t.topic_id);
  assert.deepEqual(topicIds, CANONICAL_TOPIC_IDS);
  assert.equal(body.monthly_scores.length, 12);
  assert.equal(result.calls.length, 1);
  assert.equal(result.calls[0].url, `${CANONICAL_RENDER}/api/v3/unified-reading`);
});

test("Gateway Unreachable Fallback: upstream network error triggers seamless edge fallback", () => {
  const result = runGateway({
    method: "POST",
    url: "/api/index?path=/api/v3/unified-reading",
    body: {
      birth_date: "1990-05-15",
      birth_time: "10:30",
      unknown_hour: false,
      target_year: 2026,
    },
    upstreams: [
      { match: CANONICAL_RENDER, throw: true },
    ],
  });

  assert.equal(result.statusCode, 200, `Expected HTTP 200 from fallback on network error, got ${result.statusCode}`);
  assert.equal(result.headers["x-fallback-edge"], "unified-reading-v1");

  const body = result.body;
  assert.equal(body.schema_version, "horo_lite_unified_reading.v1");
  assert.equal(body.topics.length, 12);
  assert.ok(body.past_patterns.length >= 3);
});

test("Negative Validation: birth_date year in future relative to target_year rejects with 422", () => {
  // Direct engine call
  assert.throws(
    () => {
      createUnifiedReading({
        birth_date: "2030-01-01",
        target_year: 2026,
      });
    },
    (err) => {
      assert.equal(err.status, 422);
      assert.equal(err.code, "invalid_date_range");
      assert.match(err.message, /must not be after target_year/);
      return true;
    },
  );

  // Gateway invocation fallback
  const result = runGateway({
    method: "POST",
    url: "/api/index?path=/api/v3/unified-reading",
    body: {
      birth_date: "2030-01-01",
      target_year: 2026,
    },
    upstreams: [
      { match: CANONICAL_RENDER, status: 503 },
    ],
  });

  assert.equal(result.statusCode, 422);
  assert.equal(result.body.status, "error");
  assert.equal(result.body.code, "invalid_date_range");
});

test("Negative Validation: missing required fields or invalid JSON rejects cleanly", () => {
  // Missing birth_date
  assert.throws(
    () => createUnifiedReading({ target_year: 2026 }),
    (err) => err.status === 422 && err.code === "invalid_request_data",
  );

  // Invalid target_year
  assert.throws(
    () => createUnifiedReading({ birth_date: "1990-01-01", target_year: 1850 }),
    (err) => err.status === 422 && err.code === "invalid_target_year",
  );

  // Malformed JSON string
  assert.throws(
    () => createUnifiedReading("{ invalid json"),
    (err) => err.status === 400 && err.code === "invalid_request_body",
  );
});

test("Latency SLA: deterministic edge calculation executes well under 300ms SLA", () => {
  const payload = {
    birth_date: "2026-10-15",
    unknown_hour: true,
    display_name: "jack",
    target_year: 2026,
  };

  // Warmup
  createUnifiedReading(payload);

  const iterations = 20;
  const t0 = performance.now();
  for (let i = 0; i < iterations; i++) {
    createUnifiedReading(payload);
  }
  const t1 = performance.now();
  const avgMs = (t1 - t0) / iterations;

  assert.ok(avgMs < 50, `Average edge engine latency ${avgMs.toFixed(2)}ms exceeded SLA bound of 50ms (contract SLA < 300ms)`);
});

test("HITL Consult endpoint: /api/v3/hitl-consult returns HTTP 200 with polite non-5xx status", () => {
  const result = runGateway({
    method: "POST",
    url: "/api/index?path=/api/v3/hitl-consult",
    body: {
      birth_date: "2026-10-15",
      unknown_hour: true,
      display_name: "jack",
      target_year: 2026,
    },
    upstreams: [],
  });

  assert.equal(result.statusCode, 200, `Expected HTTP 200 from /api/v3/hitl-consult, got ${result.statusCode}`);
  assert.ok(result.body && typeof result.body === "object");
  assert.ok(
    ["unavailable", "in_progress", "completed", "disabled"].includes(result.body.status),
    `Unexpected status: ${result.body.status}`,
  );
  assert.notEqual(result.statusCode, 500);
  assert.notEqual(result.statusCode, 502);
  assert.notEqual(result.statusCode, 503);
  assert.notEqual(result.statusCode, 504);
});

