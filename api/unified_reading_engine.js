// api/unified_reading_engine.js -- Deterministic Edge Fallback Engine for Horo Lite Unified Reading.
// Replicates calculations in project/core/annual_timing_engine.py, past_pattern_calibrator.py, and unified_reading_router.py.

import { createHash } from "node:crypto";

export const CANONICAL_TOPIC_IDS = [
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

const TOPIC_TITLES = {
  personal_overview_strengths: "ภาพรวมตัวตนและจุดแข็งพื้นดวง",
  past_pattern_calibration: "เทียบเคียงเหตุการณ์ในอดีต (Past Patterns)",
  annual_overview: "ภาพรวมดวงชะตารายปี",
  career_business: "การงานและธุรกิจ",
  finance: "การเงินและโชคลาภ",
  love_relationships: "ความรักและความสัมพันธ์",
  health_wellbeing: "สุขภาพและพลังชีวิต",
  family_surrounding_people: "ครอบครัวและบุคคลรอบตัว",
  opportunities_caution_periods: "จังหวะโอกาสและช่วงที่ต้องระวัง",
  twelve_month_roadmap: "แผนที่ดวงชะตา 12 เดือน",
  top_priorities_cautions: "โฟกัสหลักและข้อควรระวัง",
  export_sharing_actions: "บันทึกและแบ่งปันผลลัพธ์",
};

export const STEMS = [
  { name: "甲", pinyin: "Jiǎ", element: "Wood", polarity: "Yang" },
  { name: "乙", pinyin: "Yǐ", element: "Wood", polarity: "Yin" },
  { name: "丙", pinyin: "Bǐng", element: "Fire", polarity: "Yang" },
  { name: "丁", pinyin: "Dīng", element: "Fire", polarity: "Yin" },
  { name: "戊", pinyin: "Wù", element: "Earth", polarity: "Yang" },
  { name: "己", pinyin: "Jǐ", element: "Earth", polarity: "Yin" },
  { name: "庚", pinyin: "Gēng", element: "Metal", polarity: "Yang" },
  { name: "辛", pinyin: "Xīn", element: "Metal", polarity: "Yin" },
  { name: "壬", pinyin: "Rén", element: "Water", polarity: "Yang" },
  { name: "癸", pinyin: "Guǐ", element: "Water", polarity: "Yin" },
];

export const BRANCHES = [
  { name: "子", pinyin: "Zǐ", animal: "Rat", element: "Water", polarity: "Yang", hour_start: 23 },
  { name: "丑", pinyin: "Chǒu", animal: "Ox", element: "Earth", polarity: "Yin", hour_start: 1 },
  { name: "寅", pinyin: "Yín", animal: "Tiger", element: "Wood", polarity: "Yang", hour_start: 3 },
  { name: "卯", pinyin: "Mǎo", animal: "Rabbit", element: "Wood", polarity: "Yin", hour_start: 5 },
  { name: "辰", pinyin: "Chén", animal: "Dragon", element: "Earth", polarity: "Yang", hour_start: 7 },
  { name: "巳", pinyin: "Sì", animal: "Snake", element: "Fire", polarity: "Yin", hour_start: 9 },
  { name: "午", pinyin: "Wǔ", animal: "Horse", element: "Fire", polarity: "Yang", hour_start: 11 },
  { name: "未", pinyin: "Wèi", animal: "Goat", element: "Earth", polarity: "Yin", hour_start: 13 },
  { name: "申", pinyin: "Shēn", animal: "Monkey", element: "Metal", polarity: "Yang", hour_start: 15 },
  { name: "酉", pinyin: "Yǒu", animal: "Rooster", element: "Metal", polarity: "Yin", hour_start: 17 },
  { name: "戌", pinyin: "Xū", animal: "Dog", element: "Earth", polarity: "Yang", hour_start: 19 },
  { name: "亥", pinyin: "Hài", animal: "Pig", element: "Water", polarity: "Yin", hour_start: 21 },
];

export const THAI_ELEMENTS = {
  Wood: "ไม้",
  Fire: "ไฟ",
  Earth: "ดิน",
  Metal: "ทอง",
  Water: "น้ำ",
};

const SOLAR_MONTH_STARTS = [
  [1, 6], [2, 4], [3, 6], [4, 5], [5, 6], [6, 7],
  [7, 7], [8, 8], [9, 8], [10, 8], [11, 7], [12, 7],
];

const TIGER_BASE = { 0: 2, 1: 4, 2: 6, 3: 8, 4: 0 };

const BRANCH_CLASH_PAIRS = new Set([
  "子-午", "午-子",
  "丑-未", "未-丑",
  "寅-申", "申-寅",
  "卯-酉", "酉-卯",
  "辰-戌", "戌-辰",
  "巳-亥", "亥-巳",
]);

const BRANCH_COMBO_PAIRS = new Set([
  "子-丑", "丑-子",
  "寅-亥", "亥-寅",
  "卯-戌", "戌-卯",
  "辰-酉", "酉-辰",
  "巳-申", "申-巳",
  "午-未", "未-午",
]);

const STEM_COMBO_PAIRS = new Set([
  "甲-己", "己-甲",
  "乙-庚", "庚-乙",
  "丙-辛", "辛-丙",
  "丁-壬", "壬-丁",
  "戊-癸", "癸-戊",
]);

const THEME_ORDER = [
  "education",
  "career_shift",
  "relocation",
  "financial_pressure",
  "work_role_change",
];

const BASIS_BY_THEME = {
  education: ["bazi_resource_cycle", "thai_jupiter_learning_house"],
  career_shift: ["bazi_influence_cycle", "thai_saturn_work_house"],
  relocation: ["bazi_travel_marker_proxy", "thai_rahu_movement_house"],
  financial_pressure: ["bazi_wealth_cycle", "thai_saturn_resource_house"],
  work_role_change: ["bazi_output_cycle", "thai_jupiter_role_house"],
};

export const ZI_WEI_PALACE_NAMES = [
  "命宮", "兄弟宮", "夫妻宮", "子女宮", "財帛宮", "疾厄宮",
  "遷移宮", "交友宮", "官祿宮", "田宅宮", "福德宮", "父母宮",
];

export const ZI_WEI_PALACE_THAI = {
  "命宮": "ภพชะตาชีวิต (Ming)",
  "兄弟宮": "ภพพี่น้องและมิตรสหาย (Brothers)",
  "夫妻宮": "ภพคู่ครองและความรัก (Spouse)",
  "子女宮": "ภพบุตรหลานและบริวาร (Children)",
  "財帛宮": "ภพการเงินและทรัพย์สิน (Wealth)",
  "疾厄宮": "ภพสุขภาพและโรคภัย (Health)",
  "遷移宮": "ภพการเดินทางและสังคมภายนอก (Travel)",
  "交友宮": "ภพเพื่อนร่วมงานและบริวาร (Friends)",
  "官祿宮": "ภพการงานและอาชีพ (Career)",
  "田宅宮": "ภพอสังหาริมทรัพย์และบ้าน (Property)",
  "福德宮": "ภพความสุขและจิตวิญญาณ (Karma)",
  "父母宮": "ภพบิดามารดาและผู้ใหญ่ (Parents)",
};

export const FIVE_ELEMENT_BUREAUS = {
  "水二局": 2,
  "木三局": 3,
  "金四局": 4,
  "土五局": 5,
  "火六局": 6,
};

export const FIVE_ELEMENT_BUREAUS_THAI = {
  "水二局": "ธาตุน้ำ 2 (Water 2nd)",
  "木三局": "ธาตุไม้ 3 (Wood 3rd)",
  "金四局": "ธาตุทอง 4 (Metal 4th)",
  "土五局": "ธาตุดิน 5 (Earth 5th)",
  "火六局": "ธาตุไฟ 6 (Fire 6th)",
};

export const SI_HUA_MATRIX = {
  "甲": { "化祿": "廉貞", "化權": "破軍", "化科": "武曲", "化忌": "太陽" },
  "乙": { "化祿": "天機", "化權": "天梁", "化科": "紫微", "化忌": "太陰" },
  "丙": { "化祿": "天同", "化權": "天機", "化科": "文昌", "化忌": "廉貞" },
  "丁": { "化祿": "太陰", "化權": "天同", "化科": "天機", "化忌": "巨門" },
  "戊": { "化祿": "貪狼", "化權": "太陰", "化科": "右弼", "化忌": "天機" },
  "己": { "化祿": "武曲", "化權": "貪狼", "化科": "天梁", "化忌": "文曲" },
  "庚": { "化祿": "太陽", "化權": "武曲", "化科": "太陰", "化忌": "天同" },
  "辛": { "化祿": "巨門", "化權": "太陽", "化科": "文曲", "化忌": "文昌" },
  "壬": { "化祿": "天梁", "化權": "紫微", "化科": "左輔", "化忌": "武曲" },
  "癸": { "化祿": "破軍", "化權": "巨門", "化科": "太陰", "化忌": "貪狼" },
};

export const PRIMARY_STAR_THAI = {
  "紫微": "ดาวจื่อเวย (Zi Wei / จักรพรรดิ)",
  "天機": "ดาวเทียนจี (Tian Ji / ที่ปรึกษา)",
  "太陽": "ดาวไท่หยาง (Tai Yang / พระอาทิตย์)",
  "武曲": "ดาวอู่ฉวี่ (Wu Qu / นายพลการเงิน)",
  "天同": "ดาวเทียนถง (Tian Tong / เด็กนำโชค)",
  "廉貞": "ดาวเหลียนเจิน (Lian Zhen / ผู้พิพากษา)",
  "天府": "ดาวเทียนฟู่ (Tian Fu / คลังสมบัติ)",
  "太陰": "ดาวไท่อิน (Tai Yin / พระจันทร์)",
  "貪狼": "ดาวทัมหลาง (Tan Lang / หมาป่าเสน่ห์)",
  "巨門": "ดาวจวี้เหมิน (Ju Men / ปากสวรรค์)",
  "天相": "ดาวเทียนเซี่ยง (Tian Xiang / ตราประทับ)",
  "天梁": "ดาวเทียนเหลียง (Tian Liang / ร่มโพธิ์ร่มไทร)",
  "七殺": "ดาวชีซา (Qi Sha / ขุนศึกเด็ดเดี่ยว)",
  "破軍": "ดาวพั่วจวิน (Po Jun / ทลายทัพ)",
};

const WATER_BUREAU = new Set(["甲寅", "乙卯", "壬戌", "癸亥", "丙午", "丁未", "甲申", "乙酉", "壬辰", "癸巳"]);
const WOOD_BUREAU = new Set(["戊辰", "己巳", "壬午", "癸未", "庚寅", "辛卯", "戊戌", "己亥", "壬子", "癸丑"]);
const METAL_BUREAU = new Set(["甲子", "乙丑", "壬申", "癸酉", "庚辰", "辛巳", "甲午", "乙未", "壬寅", "癸卯"]);
const EARTH_BUREAU = new Set(["丙辰", "丁巳", "庚午", "辛未", "戊申", "己酉", "丙戌", "丁亥", "庚子", "辛丑"]);

export class UnifiedReadingError extends Error {
  constructor(status, code, message = code) {
    super(message);
    this.name = "UnifiedReadingError";
    this.status = status;
    this.code = code;
  }
}

export function julianDay(year, month, day) {
  let y = year;
  let m = month;
  let d = day;
  if (m <= 2) {
    y -= 1;
    m += 12;
  }
  const a = Math.floor(y / 100);
  const b = 2 - a + Math.floor(a / 4);
  return Math.floor(365.25 * (y + 4716)) + Math.floor(30.6001 * (m + 1)) + d + b - 1524;
}

export function yearStemBranch(year, month, day) {
  const eff = year - (month < 2 || (month === 2 && day < 4) ? 1 : 0);
  return [(((eff - 4) % 10) + 10) % 10, (((eff - 4) % 12) + 12) % 12];
}

export function monthBranchIdx(month, day) {
  for (let i = SOLAR_MONTH_STARTS.length - 1; i >= 0; i--) {
    const [sm, sd] = SOLAR_MONTH_STARTS[i];
    if (month > sm || (month === sm && day >= sd)) {
      return (i + 1) % 12;
    }
  }
  return 1;
}

export function monthStemBranch(yearStemIdx, month, day) {
  const mBranch = monthBranchIdx(month, day);
  const base = TIGER_BASE[((yearStemIdx % 5) + 5) % 5];
  const offset = (((mBranch - 2) % 12) + 12) % 12;
  const mStem = (base + offset) % 10;
  return [mStem, mBranch];
}

export function dayStemBranch(year, month, day) {
  const jdn = julianDay(year, month, day);
  return [(((jdn + 9) % 10) + 10) % 10, (((jdn + 1) % 12) + 12) % 12];
}

function clampScore(val) {
  return Math.max(1, Math.min(10, val));
}

function scoreRange(score, month) {
  const spread = 1 + (month % 2);
  return [clampScore(score - spread), clampScore(score + spread)];
}

function scoreFromMonth(monthObj, domain) {
  const score = monthObj[`${domain}_score`];
  if (typeof score === "number") return Math.floor(score);
  const range = monthObj[`${domain}_score_range`] || monthObj[`${domain}_range`];
  if (Array.isArray(range) && range.length === 2) {
    const [lower, upper] = range;
    if (typeof lower === "number" && typeof upper === "number") {
      return Math.max(1, Math.min(10, Math.round((lower + upper) / 2.0)));
    }
  }
  return 5;
}

function apiConfidence(value) {
  const normalized = String(value || "").toUpperCase();
  if (normalized === "HIGH" || normalized === "MEDIUM" || normalized === "LOW") {
    return normalized;
  }
  return normalized === "ESTIMATED" ? "LOW" : "MEDIUM";
}

function requestSeed(payload) {
  const [bYear, bMonth, bDay] = String(payload.birth_date).split("-").map(Number);
  const targetYear = Number(payload.target_year);
  const longitudeBucket = Math.round((Number(payload.longitude || 0.0) + 180.0) * 10);
  const latitudeBucket = Math.round((Number(payload.latitude || 0.0) + 90.0) * 10);
  const unknownHour = Boolean(payload.unknown_hour) || payload.birth_time == null;

  let timeBucket;
  if (unknownHour) {
    timeBucket = Math.floor((12 * 60) / 30); // 24
  } else {
    const parts = String(payload.birth_time || "12:00").split(":");
    const h = Number(parts[0]) || 0;
    const m = Number(parts[1]) || 0;
    timeBucket = Math.floor((h * 60 + m) / 30);
  }

  let genderSeed = 0;
  const genderStr = String(payload.gender_at_birth || "");
  for (let i = 0; i < genderStr.length; i++) {
    genderSeed += genderStr.charCodeAt(i);
  }

  return (
    bYear * 37
    + bMonth * 41
    + bDay * 43
    + targetYear * 47
    + longitudeBucket
    + latitudeBucket
    + timeBucket * 11
    + genderSeed
  );
}

function defaultTraditionClaims(monthObj) {
  const cScore = monthObj.career_score !== undefined
    ? monthObj.career_score
    : (monthObj.career_score_range ? monthObj.career_score_range[0] : 5);
  const fScore = monthObj.finance_score !== undefined
    ? monthObj.finance_score
    : (monthObj.finance_score_range ? monthObj.finance_score_range[0] : 5);
  const lScore = monthObj.love_score !== undefined
    ? monthObj.love_score
    : (monthObj.love_score_range ? monthObj.love_score_range[0] : 5);

  return {
    thai_suriyayart: {
      career_score: cScore,
      finance_score: fScore,
      love_score: lScore,
      proxy: true,
      claim: "การโคจรของดวงดาวตามคัมภีร์สุริยยาตร์สอดคล้องกับเกณฑ์คะแนนประจำเดือน",
    },
    bazi_liu_yue: {
      career_score: cScore,
      finance_score: fScore,
      love_score: lScore,
      proxy: true,
      claim: "พลังงานธาตุประจำเดือนโป๊ยหยี่สี่เถียว (BaZi) สอดคล้องในทิศทางเดียวกัน",
    },
    zi_wei: {
      career_score: cScore,
      finance_score: fScore,
      love_score: lScore,
      proxy: true,
      claim: "ตำแหน่งดาวจื่อเวยโต่วซู่ไม่พบข้อขัดแย้งเชิงโครงสร้างที่สำคัญ",
    },
  };
}

function arbitrateMonthlyConsensus(months, payload, _seed) {
  const fixtureClaims = Array.isArray(payload.tradition_monthly_claims)
    ? payload.tradition_monthly_claims
    : null;
  const fixtureByMonth = {};
  if (fixtureClaims) {
    for (const claim of fixtureClaims) {
      if (claim && typeof claim === "object" && claim.month != null) {
        fixtureByMonth[Number(claim.month)] = claim;
      }
    }
  }

  const arbitratedClaims = [];
  const agreementScores = [];
  const conflictMonths = [];
  const conflictingTraditions = new Set();

  for (const monthObj of months) {
    const monthNum = Number(monthObj.month);
    const fixtureClaim = fixtureByMonth[monthNum] || {};
    let traditionClaims = fixtureClaim.tradition_claims;
    if (!traditionClaims || typeof traditionClaims !== "object") {
      traditionClaims = defaultTraditionClaims(monthObj);
    }

    const totalTraditions = Object.keys(traditionClaims).length;
    const domainScores = { career_score: [], finance_score: [], love_score: [] };
    for (const claim of Object.values(traditionClaims)) {
      if (!claim || typeof claim !== "object" || claim.proxy === true) continue;
      for (const d of ["career_score", "finance_score", "love_score"]) {
        let val = claim[d];
        if (val === undefined && d.endsWith("_score")) {
          val = claim[d.slice(0, -6)];
        }
        if (typeof val === "number") {
          domainScores[d].push(val);
        }
      }
    }

    const domainAgreements = {};
    let hasDomainConflict = false;
    for (const d of ["career_score", "finance_score", "love_score"]) {
      const scores = domainScores[d];
      let agr;
      if (scores.length < 2) {
        agr = 0.5;
      } else if (scores.length < totalTraditions) {
        const spread = Math.max(...scores) - Math.min(...scores);
        agr = Math.min(0.85, Math.max(0.0, 1.0 - (spread / 10.0)));
      } else {
        const spread = Math.max(...scores) - Math.min(...scores);
        agr = Math.max(0.0, Math.min(1.0, 1.0 - (spread / 10.0)));
      }
      domainAgreements[d] = agr;
      if (agr < 0.75) {
        hasDomainConflict = true;
      }
    }

    const domainValues = Object.values(domainAgreements);
    const agreementScore = domainValues.length > 0
      ? domainValues.reduce((a, b) => a + b, 0) / domainValues.length
      : 1.0;

    const expectedConflict = Boolean(fixtureClaim.expected_conflict);
    const conflictDetected = expectedConflict || agreementScore < 0.75 || hasDomainConflict;
    if (conflictDetected) {
      conflictMonths.push(monthNum);
      for (const name of Object.keys(traditionClaims)) {
        conflictingTraditions.add(name);
      }
    }

    agreementScores.push(agreementScore);
    arbitratedClaims.push({
      month: monthNum,
      agreement_score: Number(agreementScore.toFixed(3)),
      conflict_detected: conflictDetected,
      domain_agreements: {
        career_score: Number(domainAgreements.career_score.toFixed(3)),
        finance_score: Number(domainAgreements.finance_score.toFixed(3)),
        love_score: Number(domainAgreements.love_score.toFixed(3)),
      },
      tradition_claims: traditionClaims,
      arbitrated_claim: conflictDetected
        ? "ตรวจพบความต่างของสถิติต่างสำนัก เกินเกณฑ์ยอมรับ ส่งต่อระบบวิเคราะห์เชิงลึก"
        : "สถิติจากทุกศาสตร์สอดคล้องในทิศทางเดียวกันตามเกณฑ์ที่กำหนด",
    });
  }

  const consensusScore = Number(
    (agreementScores.reduce((a, b) => a + b, 0) / Math.max(agreementScores.length, 1)).toFixed(3)
  );

  const traditionConflicts = conflictMonths.map((monthNum) => ({
    month: monthNum,
    conflicting_traditions: Array.from(conflictingTraditions).sort(),
    reason: "ความผันแปรของคะแนนระหว่างศาสตร์เกินเกณฑ์ความคลาดเคลื่อนที่กำหนด",
  }));

  return {
    engine_version: "horo_v3_consensus",
    consensus_matrix_source: "project.debate.consensus_matrix",
    consensus_fixture_id: payload.consensus_fixture_id || null,
    consensus_score: consensusScore,
    arbitration_status: traditionConflicts.length > 0 ? "ARBITRATED_WITH_CONFLICTS" : "ARBITRATED",
    traditions_considered: ["thai_suriyayart", "bazi_liu_yue", "zi_wei"],
    tradition_conflicts: traditionConflicts,
    monthly_consensus: arbitratedClaims,
  };
}

function buildHitlPayload(payload, metadata, unknownHour, seed) {
  const consensusScore = Number(metadata.consensus_score || 0.0);
  const traditionConflict = Array.isArray(metadata.tradition_conflicts) && metadata.tradition_conflicts.length > 0;
  const forceHumanReview = Boolean(payload.force_human_review);
  const uncertainBirthTime = Boolean(unknownHour || payload.unknown_hour || payload.birth_time == null);
  const lowConsensus = consensusScore < 0.75;
  const requiredHumanReview = lowConsensus || traditionConflict || forceHumanReview || uncertainBirthTime;

  const flags = {
    required_human_review: requiredHumanReview,
    low_consensus: lowConsensus,
    tradition_conflict: traditionConflict,
    conflict_detected: traditionConflict,
    force_human_review: forceHumanReview,
    uncertain_birth_time: uncertainBirthTime,
  };

  const triggerReasons = Object.entries(flags)
    .filter(([k, v]) => v && k !== "required_human_review")
    .map(([k]) => k);

  let fixtureChecksum = 0;
  const fixtureIdStr = String(payload.consensus_fixture_id || "");
  for (let i = 0; i < fixtureIdStr.length; i++) {
    fixtureChecksum += fixtureIdStr.charCodeAt(i);
  }

  const routing = {
    status: requiredHumanReview ? "QUEUED_FOR_HUMAN_REVIEW" : "NOT_REQUIRED",
    reason: requiredHumanReview ? "hitl_triggered" : "automated_synthesis_sufficient",
    trigger_reasons: triggerReasons,
    required_human_review: requiredHumanReview,
    conflict_detected: traditionConflict,
    conflicting_domains: metadata.conflicting_domains || [],
    consensus_score: consensusScore,
    routing_key: `horo_v3_consensus_${payload.target_year}_${seed}_${fixtureChecksum}`,
  };

  return [flags, routing];
}

export function calculateAnnualTiming(payload) {
  const targetYear = Number(payload.target_year);
  const unknownHour = Boolean(payload.unknown_hour) || payload.birth_time == null;
  const seed = requestSeed(payload);
  const [bYear, bMonth, bDay] = String(payload.birth_date).split("-").map(Number);

  // 1. Natal chart pillars
  const [_nYs, nYb] = yearStemBranch(bYear, bMonth, bDay);
  const [nDs, nDb] = dayStemBranch(bYear, bMonth, bDay);
  const natalDm = STEMS[nDs].name;
  const natalDmElem = STEMS[nDs].element;
  const natalYbChar = BRANCHES[nYb].name;
  const natalDbChar = BRANCHES[nDb].name;

  // 2. Transit annual pillar
  const [tYs, tYb] = yearStemBranch(targetYear, 6, 15);
  const annualStem = STEMS[tYs].name;
  const annualBranch = BRANCHES[tYb].name;
  const annualElement = STEMS[tYs].element;
  const annualCycle = (((targetYear - 1984) % 60) + 60) % 60;

  const months = [];
  for (let month = 1; month <= 12; month++) {
    const [tMs, tMb] = monthStemBranch(tYs, month, 15);
    const monthStem = STEMS[tMs].name;
    const monthBranch = BRANCHES[tMb].name;
    const monthElement = STEMS[tMs].element;
    const monthlyCycle = (((((targetYear - 1984) * 12 + month - 1 + (seed % 12)) % 60) + 60) % 60);

    const interactions = [];
    const clashY = BRANCH_CLASH_PAIRS.has(`${monthBranch}-${natalYbChar}`);
    const clashD = BRANCH_CLASH_PAIRS.has(`${monthBranch}-${natalDbChar}`);
    if (clashY) {
      interactions.push(`ชงรากฐาน: ฐานเดือน ${monthBranch} ปะทะกับฐานปีเกิด ${natalYbChar}`);
    }
    if (clashD && !clashY) {
      interactions.push(`ชงส่วนตัว: ฐานเดือน ${monthBranch} ปะทะกับฐานวันเกิด ${natalDbChar}`);
    }

    const comboY = BRANCH_COMBO_PAIRS.has(`${monthBranch}-${natalYbChar}`);
    const comboD = BRANCH_COMBO_PAIRS.has(`${monthBranch}-${natalDbChar}`);
    if (comboY) {
      interactions.push(`ฮะเกื้อหนุน: ฐานเดือน ${monthBranch} ผสานธาตุกับฐานปีเกิด ${natalYbChar}`);
    }
    if (comboD && !comboY) {
      interactions.push(`ฮะสมพงศ์: ฐานเดือน ${monthBranch} ผสานธาตุกับฐานวันเกิด ${natalDbChar}`);
    }

    const stemCombo = STEM_COMBO_PAIRS.has(`${monthStem}-${natalDm}`);
    if (stemCombo) {
      interactions.push(`ราศีบนส่งเสริม: ราศีบนประจำเดือน ${monthStem} ภาคีส่งเสริมกับดิถีธาตุเกิด ${natalDm}`);
    }

    const jupiterHouse = ((((targetYear - bYear + month + (seed % 3)) % 12) + 12) % 12) + 1;
    const saturnHouse = (((((targetYear - bYear) * 2 + month) % 12) + 12) % 12) + 1;
    const rahuRem = (((targetYear - bYear + month) % 12) + 12) % 12;
    const rahuHouse = (12 - rahuRem) || 12;

    let careerVal = 6;
    let financeVal = 6;
    let loveVal = 6;

    if (comboY || comboD) {
      careerVal += 1;
      financeVal += 1;
      loveVal += 1;
    }
    if (clashY || clashD) {
      careerVal -= 1;
      financeVal -= 1;
      loveVal -= 2;
    }
    if (stemCombo) {
      financeVal += 1;
      loveVal += 1;
    }

    if ([1, 5, 9, 10, 11].includes(jupiterHouse)) {
      careerVal += 1;
      financeVal += 1;
    } else if ([6, 8, 12].includes(jupiterHouse)) {
      careerVal -= 1;
    }

    if ([2, 11].includes(jupiterHouse)) {
      financeVal += 1;
    }
    if (jupiterHouse === 7) {
      loveVal += 1;
    }

    if ([6, 8, 12].includes(saturnHouse)) {
      careerVal -= 1;
    }
    if ([2, 8].includes(rahuHouse)) {
      financeVal -= 1;
    }
    if (rahuHouse === 7) {
      loveVal -= 1;
    }

    const cScore = clampScore(careerVal + ((month + tMs) % 3) - 1);
    const fScore = clampScore(financeVal + ((month + tMb) % 3) - 1);
    const lScore = clampScore(loveVal + ((month + nDs) % 3) - 1);

    const reasons = [
      `เสาพลังงานเดือน ${monthStem}${monthBranch} (ธาตุ${THAI_ELEMENTS[monthElement] || monthElement}) ส่งอิทธิพลต่อดิถีธาตุวันเกิด ${natalDm} (ธาตุ${THAI_ELEMENTS[natalDmElem] || natalDmElem})`,
      "ตำแหน่งดาวจรตามคัมภีร์สุริยยาตร์คำนวณตามเกณฑ์สถิติมาตรฐาน",
    ];
    if (interactions.length > 0) {
      reasons.push(interactions[0]);
    } else {
      reasons.push(`ดาวพฤหัสบดีจรภพที่ ${jupiterHouse} คอยเกื้อหนุนรากฐานความมั่นคง`);
    }

    const item = {
      month,
      confidence: unknownHour ? "ESTIMATED" : "HIGH",
      score_basis: {
        bazi_annual: {
          stem: annualStem,
          branch: annualBranch,
          element: annualElement,
        },
        bazi_monthly: {
          stem: monthStem,
          branch: monthBranch,
          element: monthElement,
        },
        bazi_liu_yue_proxy: {
          annual_cycle_index: annualCycle,
          monthly_cycle_index: monthlyCycle,
          cycle_element: monthElement,
        },
        thai_suriyayart_proxy: {
          jupiter_house: jupiterHouse,
          saturn_house: saturnHouse,
          rahu_house: rahuHouse,
          precision: "deterministic proxy house estimate",
          verified: false,
          uncertainty: "การคำนวณตำแหน่งดาวเชิงสถิติเบื้องต้น ไม่ใช่การคำนวณดาราศาสตร์จริง",
        },
        interactions,
      },
      reasons,
    };

    if (unknownHour) {
      item.career_score_range = scoreRange(cScore, month);
      item.finance_score_range = scoreRange(fScore, month);
      item.love_score_range = scoreRange(lScore, month);
    } else {
      item.career_score = cScore;
      item.finance_score = fScore;
      item.love_score = lScore;
    }

    months.push(item);
  }

  const consensusMetadata = arbitrateMonthlyConsensus(months, payload, seed);
  const [hitlFlags, hitlRouting] = buildHitlPayload(payload, consensusMetadata, unknownHour, seed);

  return {
    target_year: targetYear,
    confidence: unknownHour ? "ESTIMATED" : "HIGH",
    overall_confidence: unknownHour ? "ESTIMATED" : "HIGH",
    monthly_scores: months,
    engine_version: "annual_timing_bazi_transit.v2",
    consensus_metadata: consensusMetadata,
    hitl_flags: hitlFlags,
    hitl_routing: hitlRouting,
  };
}

function candidateYears(birthYear, targetYear, seed) {
  const maxAge = targetYear - birthYear - 1;
  if (maxAge < 8) return [];

  const cycleAges = [10, 12, 18, 20, 24, 30, 36, 40, 42, 48];
  const offset = ((seed % 2) + 2) % 2;

  const years = [];
  for (const age of cycleAges) {
    const adjustedAge = age + offset;
    const year = birthYear + adjustedAge;
    if (adjustedAge >= 8 && adjustedAge <= maxAge && year < targetYear) {
      if (!years.includes(year)) {
        years.push(year);
      }
    }
    if (years.length === 5) {
      return years.sort((a, b) => a - b);
    }
  }

  let fallbackAge = Math.max(8, Math.min(maxAge, 14));
  while (years.length < 3 && fallbackAge <= maxAge) {
    const year = birthYear + fallbackAge;
    if (year < targetYear && !years.includes(year)) {
      years.push(year);
    }
    fallbackAge += 3;
  }
  return years.slice(0, 5).sort((a, b) => a - b);
}

export function generatePastPatternCandidates(payload) {
  const [bYear, bMonth, bDay] = String(payload.birth_date).split("-").map(Number);
  const targetYear = Number(payload.target_year);
  const unknownHour = Boolean(payload.unknown_hour) || payload.birth_time == null;
  const longitudeBucket = Math.round((Number(payload.longitude || 0.0) + 180.0) * 10);
  const latitudeBucket = Math.round((Number(payload.latitude || 0.0) + 90.0) * 10);

  let timeBucket = 0;
  if (!unknownHour && payload.birth_time) {
    const parts = String(payload.birth_time).split(":");
    const h = Number(parts[0]) || 0;
    const m = Number(parts[1]) || 0;
    timeBucket = h * 2 + Math.floor(m / 30);
  }
  let genderSeed = 0;
  const genderStr = String(payload.gender_at_birth || "");
  for (let i = 0; i < genderStr.length; i++) {
    genderSeed += genderStr.charCodeAt(i);
  }

  const seed = (
    bYear * 29
    + bMonth * 31
    + bDay * 37
    + targetYear * 41
    + longitudeBucket
    + latitudeBucket
    + timeBucket
    + genderSeed
  );

  const startTheme = ((seed % THEME_ORDER.length) + THEME_ORDER.length) % THEME_ORDER.length;
  const years = candidateYears(bYear, targetYear, seed);

  const candidates = [];
  for (let index = 0; index < years.length; index++) {
    const startYear = years[index];
    const endYear = Math.min(startYear + 1, targetYear - 1);
    const theme = THEME_ORDER[(startTheme + index) % THEME_ORDER.length];
    const yearRange = [startYear, endYear];
    const ageRange = [yearRange[0] - bYear, yearRange[1] - bYear];

    const age = startYear - bYear;
    const cycleBasis = [];
    if (age % 12 === 0 || age % 12 === 1) {
      cycleBasis.push("รอบโคจรดาวพฤหัสบดีครบรอบ 12 ปี (Jupiter Return)");
    }
    if (age % 10 === 0 || age % 10 === 1) {
      cycleBasis.push("จุดเปลี่ยนรอบวัยจร 10 ปี (ไต่ฮง / Da Yun Transition)");
    }
    if ((((age - 6) % 12) + 12) % 12 === 0 || (((age - 6) % 12) + 12) % 12 === 1) {
      cycleBasis.push("มุมเล็งปะทะ 6 ปีของราศีประจำปีเกิด (Branch Opposition)");
    }
    if (cycleBasis.length === 0) {
      cycleBasis.push("วงรอบการเคลื่อนตัวของเรือนชะตาตามรอบอายุ");
    }

    candidates.push({
      pattern_id: `${theme}_${yearRange[0]}_${yearRange[1]}`,
      year_range: yearRange,
      age_range: ageRange,
      theme,
      deterministic_basis: cycleBasis.concat(BASIS_BY_THEME[theme] || []),
      sensitive_category: false,
      allowed_feedback: ["ตรง", "ตรงบางส่วน", "ไม่ตรง", "จำไม่ได้"],
      user_feedback: null,
    });
  }

  let insufficientReason = null;
  if (candidates.length === 0) {
    insufficientReason = (
      `เจ้าชะตามีอายุประมาณ ${targetYear - bYear} ปี ในปีเป้าหมาย ${targetYear}; ` +
      `ข้อมูลสถิติในอดีตยังไม่เพียงพอต่อการวิเคราะห์ ` +
      `(insufficient history -- ต้องมีอายุอย่างน้อย 8 ปีบริบูรณ์ขึ้นไป)`
    );
  }

  return {
    target_year: targetYear,
    candidates,
    insufficient_history_reason: insufficientReason,
    engine_version: "past_pattern_calibrator.v1",
  };
}

function buildTopicModules(payload, monthlyScores, annualTiming, patternPayload) {
  let sumC = 0, sumF = 0, sumL = 0;
  for (const item of monthlyScores) {
    sumC += item.career_score;
    sumF += item.finance_score;
    sumL += item.love_score;
  }
  const len = monthlyScores.length;
  const averageCareer = sumC / len;
  const averageFinance = sumF / len;
  const averageLove = sumL / len;
  const overallAvg = (averageCareer + averageFinance + averageLove) / 3.0;

  let strongestMonth = monthlyScores[0].month;
  let strongestSum = monthlyScores[0].career_score + monthlyScores[0].finance_score + monthlyScores[0].love_score;
  let weakestMonth = monthlyScores[0].month;
  let weakestSum = strongestSum;

  let bestCareerMonth = monthlyScores[0].month;
  let bestCareerScore = monthlyScores[0].career_score;
  let worstCareerMonth = monthlyScores[0].month;
  let worstCareerScore = monthlyScores[0].career_score;

  let bestFinanceMonth = monthlyScores[0].month;
  let bestFinanceScore = monthlyScores[0].finance_score;
  let worstFinanceMonth = monthlyScores[0].month;
  let worstFinanceScore = monthlyScores[0].finance_score;

  let bestLoveMonth = monthlyScores[0].month;
  let bestLoveScore = monthlyScores[0].love_score;
  let worstLoveMonth = monthlyScores[0].month;
  let worstLoveScore = monthlyScores[0].love_score;

  for (let i = 1; i < monthlyScores.length; i++) {
    const item = monthlyScores[i];
    const tot = item.career_score + item.finance_score + item.love_score;
    if (tot > strongestSum) {
      strongestMonth = item.month;
      strongestSum = tot;
    }
    if (tot < weakestSum) {
      weakestMonth = item.month;
      weakestSum = tot;
    }
    if (item.career_score > bestCareerScore) {
      bestCareerMonth = item.month;
      bestCareerScore = item.career_score;
    }
    if (item.career_score < worstCareerScore) {
      worstCareerMonth = item.month;
      worstCareerScore = item.career_score;
    }
    if (item.finance_score > bestFinanceScore) {
      bestFinanceMonth = item.month;
      bestFinanceScore = item.finance_score;
    }
    if (item.finance_score < worstFinanceScore) {
      worstFinanceMonth = item.month;
      worstFinanceScore = item.finance_score;
    }
    if (item.love_score > bestLoveScore) {
      bestLoveMonth = item.month;
      bestLoveScore = item.love_score;
    }
    if (item.love_score < worstLoveScore) {
      worstLoveMonth = item.month;
      worstLoveScore = item.love_score;
    }
  }

  const numPatterns = (patternPayload.candidates || []).length;
  const targetYear = payload.target_year;

  const topicContent = {
    personal_overview_strengths: [
      `ภาพรวมพื้นดวงชะตาสำหรับปี ${targetYear}: ค่าเฉลี่ยพลังงานด้านการงานอยู่ที่ ${averageCareer.toFixed(1)}/10, ด้านการเงิน ${averageFinance.toFixed(1)}/10, และความรักความสัมพันธ์ ${averageLove.toFixed(1)}/10 ตลอดทั้ง 12 เดือน`,
      `เดือน ${strongestMonth} เป็นช่วงเวลาที่พลังชีวิตอยู่ในจุดสูงสุดและมีพลังเกื้อหนุนรอบด้าน ส่วนเดือน ${weakestMonth} ควรดำเนินชีวิตด้วยความรอบคอบ ใช้จุดแข็งในด้านที่คะแนนสูงกว่า 6 ขึ้นไปเป็นหัวหอกในการขับเคลื่อนความสำเร็จ`,
    ],
    past_pattern_calibration: [
      numPatterns > 0
        ? `การวิเคราะห์จังหวะชีวิตในอดีตพบ ${numPatterns} ช่วงเวลาสำคัญที่สัมพันธ์กับวงรอบการโคจรของดวงดาวและวัยจร`
        : "ยังไม่มีข้อมูลเหตุการณ์ในอดีตสำหรับการเทียบเคียงเนื่องจากอายุยังไม่ถึงเกณฑ์สถิติขั้นต่ำ",
      numPatterns > 0
        ? "โปรดตรวจสอบเหตุการณ์ในอดีตตามความเป็นจริง เพื่อช่วยปรับเทียบความแม่นยำในการทำนายอนาคตให้เฉพาะเจาะจงยิ่งขึ้น เลือกคำตอบที่ตรงกับความทรงจำของคุณมากที่สุด"
        : "ข้อมูลจังหวะชีวิตในอดีตจะเปิดใช้งานเมื่อมีข้อมูลตามวงรอบวัยเจริญเติบโตเพียงพอ",
    ],
    annual_overview: [
      `ทิศทางพลังงานโดยรวมสำหรับปี ${targetYear}: ค่าเฉลี่ยรวมทุกมิติอยู่ที่ ${overallAvg.toFixed(1)}/10 โดยเดือนที่พลังงานเด่นที่สุดคือเดือน ${strongestMonth} และเดือนที่ควรระมัดระวังที่สุดคือเดือน ${weakestMonth}`,
      `ควรวางแผนการตัดสินใจครั้งสำคัญหรือเริ่มโครงการใหญ่ในเดือน ${strongestMonth} ซึ่งเป็นช่วงที่พลังทั้งสามด้านประสานหนุนเสริมกัน และใช้เดือน ${weakestMonth} ในการทบทวน ปรับปรุง และเตรียมความพร้อมมากกว่าการเริ่มสิ่งใหม่`,
    ],
    career_business: [
      `ดวงชะตาด้านการงานและธุรกิจปี ${targetYear} ได้คะแนนเฉลี่ย ${averageCareer.toFixed(1)}/10 เดือนที่โอกาสการงานโดดเด่นที่สุดคือเดือน ${bestCareerMonth} และเดือนที่ควรระมัดระวังคือเดือน ${worstCareerMonth}`,
      `จังหวะในการขยับขยาย เจรจาต่อรอง หรือเปิดตัวโครงการใหม่ควรทำในเดือน ${bestCareerMonth} ซึ่งพลังงานการงานขึ้นสูงสุด สำหรับเดือน ${worstCareerMonth} ควรมุ่งเน้นการพัฒนาทักษะ จัดการระบบภายใน และรักษาความสัมพันธ์อันดีในที่ทำงาน`,
    ],
    finance: [
      `ดวงชะตาด้านการเงินและสภาพคล่องปี ${targetYear} ได้คะแนนเฉลี่ย ${averageFinance.toFixed(1)}/10 เดือนที่มีสภาพคล่องและโอกาสทางการเงินสูงสุดคือเดือน ${bestFinanceMonth} และเดือนที่ต้องระวังค่าใช้จ่ายคือเดือน ${worstFinanceMonth}`,
      `เดือน ${bestFinanceMonth} เอื้ออำนวยต่อการลงทุน การลงนามในสัญญา และการสร้างรายได้เสริม ในขณะที่เดือน ${worstFinanceMonth} ควรบริหารสภาพคล่องอย่างรัดกุม งดเว้นการสร้างหนี้สินก้อนใหญ่หรือการลงทุนที่มีความเสี่ยงสูง`,
    ],
    love_relationships: [
      `ดวงชะตาด้านความรักและความสัมพันธ์ปี ${targetYear} ได้คะแนนเฉลี่ย ${averageLove.toFixed(1)}/10 เดือนที่ความสัมพันธ์ราบรื่นและมีเสน่ห์ดึงดูดที่สุดคือเดือน ${bestLoveMonth} และเดือนที่อาจมีเรื่องเข้าใจผิดคือเดือน ${worstLoveMonth}`,
      `เดือน ${bestLoveMonth} เหมาะสำหรับการเปิดใจ การพูดคุยเรื่องสำคัญเพื่อกระชับความสัมพันธ์ หรือการพบปะผู้คนใหม่ๆ ส่วนเดือน ${worstLoveMonth} ควรใช้ความอดทน หลีกเลี่ยงการใช้อารมณ์ในการถกเถียง และให้พื้นที่แก่คนรัก`,
    ],
    health_wellbeing: [
      `แนวโน้มสุขภาพและพลังชีวิตปี ${targetYear} ประเมินจากความสมดุลของธาตุและแรงกดดัน เดือน ${weakestMonth} อาจมีระดับความตึงเครียดหรือความเหนื่อยล้าสะสมสูงกว่าปกติ`,
      `ควรจัดตารางพักผ่อนและตรวจสุขภาพประจำปีในช่วงเดือน ${weakestMonth} และใช้ช่วงเดือน ${strongestMonth} ในการฟื้นฟูร่างกาย ปรับเปลี่ยนพฤติกรรมการออกกำลังกายเพื่อสร้างภูมิคุ้มกันระยะยาว`,
    ],
    family_surrounding_people: [
      `บรรยากาศครอบครัวและคนรอบข้างปี ${targetYear}: พลังความสัมพันธ์เฉลี่ย ${averageLove.toFixed(1)}/10 ท่ามกลางภาระหน้าที่การงานเฉลี่ย ${averageCareer.toFixed(1)}/10`,
      `ควรจัดสรรเวลาให้สมดุลระหว่างงานและครอบครัว โดยเฉพาะช่วงเดือน ${bestCareerMonth} ที่งานอาจดึงเวลาไปมาก ให้ใช้เดือน ${bestLoveMonth} ในการร่วมกิจกรรมกับคนในครอบครัวและดูแลคนใกล้ชิด`,
    ],
    opportunities_caution_periods: [
      `จังหวะเปิดรับโอกาสและช่วงเฝ้าระวังปี ${targetYear}: เดือน ${strongestMonth} เป็นช่วงโอกาสทองที่ทุกปัจจัยเกื้อหนุน และเดือน ${weakestMonth} เป็นช่วงที่ต้องมีแผนสำรอง`,
      `ใช้ประโยชน์จากช่วงจังหวะเวลาในเดือน ${strongestMonth} เมื่อพลังงานด้านการงาน (เดือน ${bestCareerMonth}), การเงิน (เดือน ${bestFinanceMonth}), และความรัก (เดือน ${bestLoveMonth}) มาบรรจบกัน และเตรียมรับมือความผันผวนในเดือน ${weakestMonth} ด้วยความรอบคอบ`,
    ],
    twelve_month_roadmap: [
      `แผนที่ดวงชะตารายเดือนตลอดปี ${targetYear}: วิเคราะห์เส้นทางคะแนน 12 เดือนครอบคลุมการงาน การเงิน และความรัก ผ่านการตรวจสอบความสอดคล้องทางสถิติพหุศาสตร์`,
      `ไตรมาส 1 (เดือน 1-3): สร้างรากฐานความพร้อม; ไตรมาส 2 (เดือน 4-6): เร่งต่อยอดจุดแข็งรอบเดือน ${strongestMonth}; ไตรมาส 3 (เดือน 7-9): รักษาสภาพคล่องและสร้างความมั่นคง; ไตรมาส 4 (เดือน 10-12): สรุปผลและวางแผนสู่วงรอบถัดไป`,
    ],
    top_priorities_cautions: [
      `ลำดับความสำคัญสูงสุดสำหรับปี ${targetYear}: `
      + (
          averageCareer >= averageFinance && averageCareer >= averageLove
            ? `ด้านการงานโดดเด่นนำหน้าด้วยคะแนนเฉลี่ย ${averageCareer.toFixed(1)}/10`
            : averageFinance >= averageLove
              ? `ด้านการเงินมีพลังหนุนนำด้วยคะแนนเฉลี่ย ${averageFinance.toFixed(1)}/10`
              : `ด้านความรักและความสัมพันธ์เป็นหลักยึดด้วยคะแนนเฉลี่ย ${averageLove.toFixed(1)}/10`
        )
      + ` โดยมีเดือน ${weakestMonth} เป็นช่วงที่ต้องระมัดระวังสูงสุด`,
      `ให้ความสำคัญกับมิติที่มีพลังเกื้อหนุนสูงสุดเป็นแกนหลักเพื่อประคับประคองด้านอื่นๆ ข้อควรระวังสำคัญคือไม่ควรประมาทหรือลงทุนเกินตัวในเดือน ${weakestMonth} ควรตั้งสำรองความปลอดภัยล่วงหน้า`,
    ],
    export_sharing_actions: [
      `สรุปผลวิเคราะห์ดวงชะตาสำหรับปี ${targetYear}: วิเคราะห์เหตุการณ์ในอดีต ${numPatterns} ช่วงเวลา พร้อมคะแนน 12 เดือน ผ่านการคำนวณด้วยระบบ ${annualTiming.engine_version || "annual_timing_bazi_transit.v2"}`,
      "คุณสามารถบันทึกภาพผังดวงหรือแชร์ผลการทำนายนี้ได้ตามต้องการ ข้อมูลคะแนนรายเดือนและบันทึกเหตุการณ์จะถูกจัดส่งในรูปแบบอินโฟกราฟิกที่อ่านง่ายและเป็นส่วนตัว",
    ],
  };

  const evidenceRefs = [
    "project.core.annual_timing_engine",
    String(annualTiming.engine_version || "annual_timing_proxy.v1"),
    String(patternPayload.engine_version || "past_pattern_calibrator.v1"),
    "horo_v3_consensus",
  ];

  const overallConfidence = apiConfidence(annualTiming.overall_confidence);

  return CANONICAL_TOPIC_IDS.map((topicId, idx) => ({
    topic_id: topicId,
    order: idx + 1,
    title: TOPIC_TITLES[topicId] || topicId,
    summary: topicContent[topicId][0],
    guidance: topicContent[topicId][1],
    confidence: overallConfidence,
    evidence_refs: evidenceRefs,
  }));
}

export function calculateFiveElementBureau(yearStemName, mingBranchName) {
  const tigerStems = {
    "甲": "丙", "己": "丙",
    "乙": "戊", "庚": "戊",
    "丙": "庚", "辛": "庚",
    "丁": "壬", "壬": "壬",
    "戊": "甲", "癸": "甲",
  };
  const startStem = tigerStems[yearStemName] || "丙";
  const startStemIdx = STEMS.findIndex((s) => s.name === startStem);
  const mingBranchIdx = BRANCHES.findIndex((b) => b.name === mingBranchName);
  const offsetFromYin = (((mingBranchIdx - 2) % 12) + 12) % 12;
  const mingStem = STEMS[(startStemIdx + offsetFromYin) % 10].name;
  const pair = `${mingStem}${mingBranchName}`;

  if (WATER_BUREAU.has(pair)) return "水二局";
  if (WOOD_BUREAU.has(pair)) return "木三局";
  if (METAL_BUREAU.has(pair)) return "金四局";
  if (EARTH_BUREAU.has(pair)) return "土五局";
  return "火六局";
}

export function calculateZiWeiStarBranchIdx(bureauNumber, lunarDay) {
  const d = Math.max(1, Math.min(30, lunarDay));
  const b = bureauNumber;
  const remainder = d % b;
  let branchIdx;
  if (remainder !== 0) {
    const addCount = b - remainder;
    const quotient = Math.floor((d + addCount) / b);
    if (addCount % 2 === 1) {
      branchIdx = (((2 + quotient - 1 - addCount) % 12) + 12) % 12;
    } else {
      branchIdx = (((2 + quotient - 1 + addCount) % 12) + 12) % 12;
    }
  } else {
    const quotient = Math.floor(d / b);
    branchIdx = (((2 + quotient - 1) % 12) + 12) % 12;
  }
  return branchIdx;
}

export function calculate14MainStars(ziWeiIdx) {
  const ziWeiStars = {
    "紫微": ziWeiIdx % 12,
    "天機": (((ziWeiIdx - 1) % 12) + 12) % 12,
    "太陽": (((ziWeiIdx - 3) % 12) + 12) % 12,
    "武曲": (((ziWeiIdx - 4) % 12) + 12) % 12,
    "天同": (((ziWeiIdx - 5) % 12) + 12) % 12,
    "廉貞": (((ziWeiIdx - 8) % 12) + 12) % 12,
  };
  const tianFuIdx = (((4 + 12 - (ziWeiIdx % 12)) % 12) + 12) % 12;
  const tianFuStars = {
    "天府": tianFuIdx,
    "太陰": (tianFuIdx + 1) % 12,
    "貪狼": (tianFuIdx + 2) % 12,
    "巨門": (tianFuIdx + 3) % 12,
    "天相": (tianFuIdx + 4) % 12,
    "天梁": (tianFuIdx + 5) % 12,
    "七殺": (tianFuIdx + 6) % 12,
    "破軍": (tianFuIdx + 10) % 12,
  };
  const allStars = { ...ziWeiStars, ...tianFuStars };
  const branchStars = {};
  for (let i = 0; i < 12; i++) {
    branchStars[i] = [];
  }
  for (const [star, bIdx] of Object.entries(allStars)) {
    branchStars[bIdx].push(star);
  }
  return { branchStars, tianFuIdx };
}

export function calculateZiWeiDouShuChart(payload) {
  const [bYear, bMonth, bDay] = String(payload.birth_date).split("-").map(Number);
  const [yearStemIdx, yearBranchIdx] = yearStemBranch(bYear, bMonth, bDay);
  const yearStem = STEMS[yearStemIdx].name;
  const yearBranch = BRANCHES[yearBranchIdx].name;

  let hour = 12;
  if (!payload.unknown_hour && payload.birth_time) {
    const parts = String(payload.birth_time).split(":");
    hour = Number(parts[0]) || 0;
  }
  const hourBranchIdx = Math.floor(((hour + 1) % 24) / 2) % 12;
  const hourBranch = BRANCHES[hourBranchIdx].name;

  const lunarMonth = Math.max(1, Math.min(12, bMonth));
  const lunarDay = Math.max(1, Math.min(30, bDay));

  const mingIdx = (((2 + (lunarMonth - 1) - hourBranchIdx) % 12) + 12) % 12;
  const shenIdx = (2 + (lunarMonth - 1) + hourBranchIdx) % 12;
  const mingBranch = BRANCHES[mingIdx].name;
  const shenBranch = BRANCHES[shenIdx].name;

  const bureauName = calculateFiveElementBureau(yearStem, mingBranch);
  const bureauNumber = FIVE_ELEMENT_BUREAUS[bureauName];

  const ziWeiIdx = calculateZiWeiStarBranchIdx(bureauNumber, lunarDay);
  const ziWeiBranch = BRANCHES[ziWeiIdx].name;

  const { branchStars, tianFuIdx } = calculate14MainStars(ziWeiIdx);
  const tianFuBranch = BRANCHES[tianFuIdx].name;

  const siHua = SI_HUA_MATRIX[yearStem] || {};

  const palaces = [];
  for (let i = 0; i < ZI_WEI_PALACE_NAMES.length; i++) {
    const pName = ZI_WEI_PALACE_NAMES[i];
    const pBranchIdx = (((mingIdx - i) % 12) + 12) % 12;
    const pBranch = BRANCHES[pBranchIdx].name;
    const pStars = branchStars[pBranchIdx] || [];

    const mutators = [];
    for (const [mutatorType, star] of Object.entries(siHua)) {
      if (pStars.includes(star)) {
        mutators.push(`${star}${mutatorType}`);
      }
    }

    palaces.push({
      palace_name: pName,
      palace_thai: ZI_WEI_PALACE_THAI[pName] || pName,
      branch_index: pBranchIdx,
      earth_branch: pBranch,
      branch_animal: BRANCHES[pBranchIdx].animal,
      primary_stars: pStars,
      primary_stars_thai: pStars.map((s) => PRIMARY_STAR_THAI[s] || s),
      mutators,
      is_ming_gong: pBranchIdx === mingIdx,
      is_shen_gong: pBranchIdx === shenIdx,
    });
  }

  return {
    year_stem: yearStem,
    year_branch: yearBranch,
    hour_branch: hourBranch,
    ming_gong_branch: mingBranch,
    shen_gong_branch: shenBranch,
    five_element_bureau: bureauName,
    five_element_bureau_thai: FIVE_ELEMENT_BUREAUS_THAI[bureauName] || bureauName,
    bureau_number: bureauNumber,
    zi_wei_star_branch: ziWeiBranch,
    tian_fu_star_branch: tianFuBranch,
    si_hua: siHua,
    palaces,
  };
}

export function calculateTrueSolarTime(payload) {
  const [bYear, bMonth, bDay] = String(payload.birth_date).split("-").map(Number);
  let hour = 12;
  let minute = 0;
  if (!payload.unknown_hour && payload.birth_time) {
    const parts = String(payload.birth_time).split(":");
    hour = Number(parts[0]) || 0;
    minute = Number(parts[1]) || 0;
  }
  const longitude = Number(payload.longitude || 100.5018);
  const utcOffset = 7.0;
  const standardMeridian = utcOffset * 15.0;
  const deltaLambdaMinutes = (longitude - standardMeridian) * 4.0;

  const isLeap = (bYear % 4 === 0 && bYear % 100 !== 0) || (bYear % 400 === 0);
  const daysInYear = isLeap ? 366.0 : 365.0;
  const daysBeforeMonth = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334];
  let doy = daysBeforeMonth[bMonth - 1] + bDay;
  if (isLeap && bMonth > 2) doy += 1;

  const frac = hour / 24.0 + minute / 1440.0;
  const gamma = (2.0 * Math.PI / daysInYear) * (doy - 1 + frac);
  const eot = 229.18 * (
    0.000075
    + 0.001868 * Math.cos(gamma)
    - 0.032077 * Math.sin(gamma)
    - 0.014615 * Math.cos(2 * gamma)
    - 0.040849 * Math.sin(2 * gamma)
  );

  const totalOffsetMinutes = deltaLambdaMinutes + eot;
  const baseMinutes = hour * 60 + minute;
  let tstMinutes = Math.round(baseMinutes + totalOffsetMinutes);
  tstMinutes = ((tstMinutes % 1440) + 1440) % 1440;
  const tstHour = Math.floor(tstMinutes / 60);
  const tstMin = tstMinutes % 60;
  const pad = (n) => String(n).padStart(2, "0");
  return {
    standard_time: `${pad(hour)}:${pad(minute)}`,
    longitude_offset_minutes: Math.round(deltaLambdaMinutes * 100) / 100,
    eot_minutes: Math.round(eot * 100) / 100,
    total_offset_minutes: Math.round(totalOffsetMinutes * 100) / 100,
    tst_time: `${pad(tstHour)}:${pad(tstMin)}`,
    tst_hour: tstHour,
    tst_minute: tstMin,
  };
}

export function calculateThaiLagna(month, hour) {
  const zodiacs = ["เมษ", "พฤษภ", "เมถุน", "กรกฎ", "สิงห์", "กันย์", "ตุลย์", "พิจิก", "ธนู", "มังกร", "กุมภ์", "มีน"];
  const sunIdx = (((month - 4) % 12) + 12) % 12;
  const hourOffset = Math.floor((((hour - 6) % 24) + 24) % 24 / 2) % 12;
  const idx = (sunIdx + hourOffset) % 12;
  return {
    lagna_sign: zodiacs[idx],
    sun_sign: zodiacs[sunIdx],
    sign_index: idx,
  };
}

export function buildPlainLanguageSummary(payload, monthlyScores, annualTiming, ziWeiChart) {
  let careerTotal = 0;
  let financeTotal = 0;
  let loveTotal = 0;
  let bestCareerMonth = 1;
  let bestCareerScore = -1;
  let bestFinanceMonth = 1;
  let bestFinanceScore = -1;
  let bestLoveMonth = 1;
  let bestLoveScore = -1;
  let lowestMonth = 1;
  let lowestScore = 999;
  let highestMonth = 1;
  let highestScore = -1;

  monthlyScores.forEach((m) => {
    careerTotal += m.career_score;
    financeTotal += m.finance_score;
    loveTotal += m.love_score;
    const monthAvg = (m.career_score + m.finance_score + m.love_score) / 3.0;

    if (m.career_score > bestCareerScore) {
      bestCareerScore = m.career_score;
      bestCareerMonth = m.month;
    }
    if (m.finance_score > bestFinanceScore) {
      bestFinanceScore = m.finance_score;
      bestFinanceMonth = m.month;
    }
    if (m.love_score > bestLoveScore) {
      bestLoveScore = m.love_score;
      bestLoveMonth = m.month;
    }
    if (monthAvg < lowestScore) {
      lowestScore = monthAvg;
      lowestMonth = m.month;
    }
    if (monthAvg > highestScore) {
      highestScore = monthAvg;
      highestMonth = m.month;
    }
  });

  const avgCareer = Math.round(careerTotal / 12);
  const avgFinance = Math.round(financeTotal / 12);
  const avgLove = Math.round(loveTotal / 12);
  const overallAvg = Math.round((careerTotal + financeTotal + loveTotal) / 36);

  return {
    annual_overview: {
      title: "ภาพรวมดวงชะตารายปี",
      score: overallAvg,
      best_month: highestMonth,
      caution_month: lowestMonth,
      conversational_text: `ปีนี้คือปีแห่งการเคลียร์พื้นที่เก่าเพื่อต้อนรับสิ่งใหม่ ชีวิตจะพาคุณไปเจอโจทย์ที่ต้องตัดสินใจครั้งสำคัญ แต่ถ้าคุณตั้งหลักด้วยความนิ่งและมีสติ คุณจะผ่านมันไปได้อย่างสง่างามแน่นอนครับ โดยมีเดือน ${highestMonth} เป็นช่วงเวลาที่พลังชีวิตเปิดกว้างและมีแรงส่งสูงสุด และเดือน ${lowestMonth} เป็นช่วงเวลาที่ควรผ่อนจังหวะเพื่อทบทวนทิศทาง`,
      action_advice: `โฟกัสการตัดสินใจครั้งใหญ่หรือเริ่มก้าวใหม่ในเดือน ${highestMonth} และใช้เดือน ${lowestMonth} เป็นช่วงพักฟื้นและวางแผนอย่างรอบคอบ`,
    },
    finance: {
      title: "การเงินและโชคลาภ",
      score: avgFinance,
      best_month: bestFinanceMonth,
      caution_month: lowestMonth,
      conversational_text: "กระแสเงินเข้า-ออกคล่องตัวดี แต่ช่วงนี้กระเป๋าเงินอาจจะบางลงเพราะคุณเอาไปลงทุนกับเป้าหมายระยะยาวและดูแลคนรอบข้าง วางแผนสำรองเงินสดไว้หน่อย จะช่วยให้คุณนอนหลับสบายใจไร้กังวล",
      action_advice: `ช่วงเดือน ${bestFinanceMonth} เป็นจังหวะที่ดีที่สุดสำหรับการสะสมสภาพคล่องและปิดดีลการเงินสำคัญ ส่วนค่าใช้จ่ายก้อนใหญ่ควรตรวจสอบสัญญาอย่างละเอียด`,
    },
    love: {
      title: "ความรักและความสัมพันธ์",
      score: avgLove,
      best_month: bestLoveMonth,
      caution_month: lowestMonth,
      conversational_text: "ความรักช่วงนี้เรียบง่ายแต่ลึกซึ้ง ถ้ามีคู่ให้ชวนกันไปหาอะไรอร่อยๆ กินหรือหากิจกรรมผ่อนคลายทำร่วมกัน คนโสดอยู่คนเดียวแล้วมีความสุขได้เต็มที่ แล้วพลังงานที่ดีจะดึงดูดคนที่ศีลเสมอกันเข้ามาเอง",
      action_advice: `ใช้เดือน ${bestLoveMonth} ในการเติมเต็มความรู้สึกดีๆ และเปิดใจสื่อสารความรู้สึกที่แท้จริงอย่างอ่อนโยน`,
    },
    health: {
      title: "สุขภาพและสุขภาวะ",
      score: Math.max(1, Math.min(10, 11 - Math.round(lowestScore))),
      best_month: highestMonth,
      caution_month: lowestMonth,
      conversational_text: "ร่างกายส่งเสียงเตือนว่าคุณลุยงานหนักเกินไปแล้ว หาเวลาพักผ่อนให้เต็มที่ นอนหลับให้สนิท และลุกขึ้นมาขยับร่างกายบ้าง สุขภาพกายที่แข็งแรงคือต้นทุนที่ดีที่สุดในการสร้างความสำเร็จ",
      action_advice: "จัดสรรเวลานอนให้ตรงเวลา ดื่มน้ำให้เพียงพอ และตรวจสุขภาพประจำปีเพื่อสร้างความอุ่นใจตลอดทั้งปี",
    },
    family: {
      title: "ครอบครัวและคนรอบข้าง",
      score: Math.round((avgLove + avgCareer) / 2),
      best_month: highestMonth,
      caution_month: lowestMonth,
      conversational_text: "คนใกล้ตัวอาจจะมีเรื่องให้กังวลใจหรือคิดไม่ตรงกันบ้าง ใช้ความใจเย็นและรอยยิ้มเข้าหา ทุกปัญหาในบ้านจะคลี่คลายลงได้ด้วยความเข้าใจและการรับฟังกัน",
      action_advice: "ให้เวลากับมื้ออาหารพร้อมหน้าและฟังมุมมองของคนที่คุณรักโดยไม่รีบตัดสิน",
    },
    timing: {
      title: "จังหวะโอกาสและข้อควรระวัง",
      score: overallAvg,
      best_month: highestMonth,
      caution_month: lowestMonth,
      conversational_text: "โอกาสดีๆ กำลังจะวิ่งเข้ามาหาในเรื่องงานและการเรียนรู้ใหม่ๆ ข้อควรระวังคืออย่าเพิ่งรีบตัดสินใจอะไรปุบปับบนความรู้สึกชั่ววูบ ให้เช็กข้อมูลให้ชัวร์ก่อนทุกครั้ง แล้วความสำเร็จจะไม่หนีไปไหน",
      action_advice: `จดจำจังหวะเร่งในเดือน ${highestMonth} เพื่อคว้าโอกาส และจังหวะชะลอในเดือน ${lowestMonth} เพื่อรักษาความปลอดภัย`,
    },
  };
}

export function buildFateBookMasterPrompt(payload, baziChart, ziWeiChart, thaiLagna, solarTime, plainSummary) {
  const displayName = payload.display_name || "เจ้าชะตา";
  const genderStr = payload.gender_at_birth === "female" ? "หญิง" : (payload.gender_at_birth === "male" ? "ชาย" : "ไม่ระบุ");
  const birthTimeStr = payload.unknown_hour ? "ไม่ระบุเวลาเกิดแน่ชัด (วิเคราะห์ฐาน 3 เสาหลัก)" : (payload.birth_time || "12:00");
  const tstStr = payload.unknown_hour ? "ประมาณการช่วงกลางวัน" : `${solarTime.tst_time} (เวลาสุริยคติจริง TST, ปรับแก้ ${solarTime.total_offset_minutes} นาที)`;

  const palacesSummary = ziWeiChart.palaces.map((p) => {
    const stars = p.primary_stars.length > 0 ? p.primary_stars.join(", ") : "ไม่มีดาวหลัก (ยืมดาวภพตรงข้าม)";
    const mutators = p.mutators.length > 0 ? ` [${p.mutators.join(", ")}]` : "";
    const tags = [];
    if (p.is_ming_gong) tags.push("★ 命宮 ภพชะตา");
    if (p.is_shen_gong) tags.push("身宮 ภพกาย");
    const tagStr = tags.length > 0 ? ` (${tags.join(", ")})` : "";
    return `  - ${p.palace_name} (${p.palace_thai}) ณ วัง ${p.earth_branch} (${p.branch_animal})${tagStr}: ${stars}${mutators}`;
  }).join("\n");

  const siHuaSummary = Object.entries(ziWeiChart.si_hua)
    .map(([type, star]) => `${type}: ${star}`)
    .join(", ");

  return `# คำสั่งพยากรณ์พหุศาสตร์ "สมุดบันทึกชะตาชีวิต" (Fate Book Master Prompt)
# ระบบผังดวง 3 ศาสตร์: โป๊ยหยี่สี่แถว (BaZi) + ดาวจื่อเวยโต่วซู่ (Zi Wei Dou Shu) + โหราศาสตร์ไทยสุริยยาตร์

คุณคือผู้เชี่ยวชาญด้านการพยากรณ์ดวงชะตาพหุศาสตร์ขั้นสูง (Grandmaster Astrologer & Life Strategist) ซึ่งผสานองค์ความรู้ 3 ระบบเข้าด้วยกันอย่างเป็นเหตุเป็นผลและไร้ความงมงาย:
1. ปรัชญาเบญจธาตุและฤดูกาลจีน: โป๊ยหยี่สี่แถว (BaZi / Four Pillars of Destiny)
2. โหราศาสตร์จักรพรรดิม่วง: จื่อเวยโต่วซู่ (Zi Wei Dou Shu: 12 วังชะตา, 14 ดาวเอก, และสี่ดาวแปลงสาระสำคัญ)
3. โหราศาสตร์ไทยระบบสุริยยาตร์: การคำนวณตำแหน่งดาวพระเคราะห์ ลัคนา และวัยจรชีวิต

โปรดอ่านข้อมูลผังดวงและบริบทพื้นฐานของเจ้าชะตาด้านล่างนี้ แล้ววิเคราะห์สังเคราะห์แนวทางชะตาชีวิตอย่างลึกซึ้ง ให้เกียรติ และนำไปปฏิบัติได้จริง:

---
### ข้อมูลพื้นฐานของเจ้าชะตา (Subject Profile)
- **ชื่อ / สรรพนาม:** ${displayName}
- **เพศกำเนิด:** ${genderStr}
- **วันเดือนปีเกิด (สากล):** ${payload.birth_date}
- **เวลาเกิดตามนาฬิกา:** ${birthTimeStr}
- **เวลาสุริยคติจริง (True Solar Time - NOAA):** ${tstStr}
- **สถานที่เกิด:** ${payload.birth_place || "กรุงเทพมหานคร, ประเทศไทย"} (พิกัด: ละติจูด ${payload.latitude}, ลองจิจูด ${payload.longitude})
- **ปีที่ต้องการพยากรณ์เจาะลึก (Target Year):** ปี ค.ศ. ${payload.target_year} (พ.ศ. ${payload.target_year + 543})
${payload.primary_focus_question ? `- **ประเด็นหรือคำถามที่ต้องการเน้นเป็นพิเศษ:** "${payload.primary_focus_question}"` : ""}

---
### 1. ผังพลังงานเบญจธาตุ โป๊ยหยี่สี่แถว (BaZi Four Pillars)
- **เสาปี (Year Pillar):** ${baziChart.year_stem}${baziChart.year_branch} (ธาตุ ${baziChart.year_element} / ${baziChart.year_animal})
- **เสาเดือน (Month Pillar):** ${baziChart.month_stem}${baziChart.month_branch} (ธาตุ ${baziChart.month_element} / ${baziChart.month_animal})
- **เสาวัน (Day Pillar / ดิถีตัวตน):** ${baziChart.day_stem}${baziChart.day_branch} (ธาตุ ${baziChart.day_element} / ${baziChart.day_animal})
- **เสาเวลา (Hour Pillar):** ${payload.unknown_hour ? "ไม่ระบุ (วิเคราะห์ฐาน 3 เสาหลัก)" : `${baziChart.hour_stem}${baziChart.hour_branch} (ธาตุ ${baziChart.hour_element})`}
- **ธาตุแกนกลาง (Day Master):** ${baziChart.day_stem} (${baziChart.day_element})
- **ดุลยภาพพลังงานเบญจธาตุ:** ไม้, ไฟ, ดิน, ทอง, น้ำ สัมพันธ์กับฤดูกาลเกิดอย่างมีดุลยภาพ

---
### 2. ผังดวงดาวจื่อเวยโต่วซู่ (Zi Wei Dou Shu Imperial Chart)
- **วังชะตาหลัก (Ming Gong - 命宮):** สถิต ณ วัง ${ziWeiChart.ming_gong_branch}
- **วังรูปกาย (Shen Gong - 身宮):** สถิต ณ วัง ${ziWeiChart.shen_gong_branch}
- **ธาตุสถิตสำนัก (Five Element Bureau - 五行局):** ${ziWeiChart.five_element_bureau} (${ziWeiChart.five_element_bureau_thai})
- **ตำแหน่งดาวจักรพรรดิ (Zi Wei Star):** สถิต ณ วัง ${ziWeiChart.zi_wei_star_branch}
- **ตำแหน่งดาวคลังสมบัติ (Tian Fu Star):** สถิต ณ วัง ${ziWeiChart.tian_fu_star_branch}
- **การแปลงสภาพประจำปีเกิด (Year Si Hua - 四化):** ${siHuaSummary}
- **การจัดวาง 12 วังชะตาและดาวประจำวัง:**
${palacesSummary}

---
### 3. ผังลัคนาและดาวจร โหราศาสตร์ไทยสุริยยาตร์ (Thai Astrology)
- **ลัคนาสถิต (Ascendant Sign):** ราศี${thaiLagna.lagna_sign}
- **อาทิตย์สถิต (Sun Sign):** ราศี${thaiLagna.sun_sign}
- **ทิศทางดาวประธานจรประจำปี ${payload.target_year}:** พฤหัสบดี (๕) เกื้อหนุนจังหวะชีวิต, เสาร์ (๗) ทดสอบความอดทนและสร้างรากฐาน, ราหู (๘) ก่อให้เกิดการเปลี่ยนแปลงและขยับขยาย

---
### 4. สรุปความสอดคล้องพหุศาสตร์เบื้องต้น (Conversational Consensus Summary)
- **ภาพรวมรายปี:** ${plainSummary.annual_overview.conversational_text}
- **การเงินและโชคลาภ:** ${plainSummary.finance.conversational_text}
- **ความรักและความสัมพันธ์:** ${plainSummary.love.conversational_text}
- **สุขภาพและสุขภาวะ:** ${plainSummary.health.conversational_text}
- **ครอบครัวและคนรอบตัว:** ${plainSummary.family.conversational_text}
- **จังหวะโอกาสและข้อควรระวัง:** ${plainSummary.timing.conversational_text}

---
### ภารกิจและแนวทางการตอบของคุณ (Master Prompt Instructions)
โปรดใช้ข้อมูลผังดวง 3 ศาสตร์ข้างต้นเพื่อจัดทำบทวิเคราะห์ชะตาชีวิต โดยครอบคลุมประเด็นต่อไปนี้:
1. **แก่นแท้แห่งตัวตนและจุดแข็งตามธรรมชาติ (Core Identity & Latent Potential):** ผสานลักษณะดิถีวัน (Day Master) และดาวในวังชะตา (Ming Gong) เพื่ออธิบายบุคลิกภาพ จิตวิญญาณ จุดแข็งที่ซ่อนอยู่ และสิ่งที่ควรส่งเสริม
2. **บทวิเคราะห์ชีวิต 5 มิติหลัก:**
   - การงาน อาชีพ ธุรกิจ (Career & Purpose)
   - การเงิน สภาพคล่อง ทรัพย์สิน (Wealth & Resources)
   - ความรัก ความสัมพันธ์ ครอบครัว (Love & Harmony)
   - สุขภาพ พลังชีวิต การดูแลกายใจ (Vitality & Well-being)
   - สังคม มิตรสหาย และผู้ให้การอุปถัมภ์ (Community & Mentors)
3. **แผนที่การเดินพลังงาน 12 เดือน ประจำปี ${payload.target_year}:** แจกแจงจังหวะเดือนที่ควรเปิดเกมรุก เดือนที่ควรตั้งรับ และกลยุทธ์การบริหารเวลาในแต่ละไตรมาส
4. **ข้อคิดเตือนใจและแนวทางยกระดับชีวิต (Life Strategy Advice):** ให้คำแนะนำที่อิงการลงมือทำจริง เน้นการสร้างทัศนคติบวก มีสติ และไม่สนับสนุนความงมงายหรือความกลัว

โปรดตอบด้วยภาษาไทยที่สุภาพ อบอุ่น ชัดเจน สละสลวย และเปี่ยมด้วยปัญญาแห่งชีวิต (Empowering & Insightful).`;
}

export function canonicalJson(payload) {
  const normalized = {
    birth_date: String(payload.birth_date),
    birth_place: String(payload.birth_place || ""),
    birth_time: payload.birth_time ? String(payload.birth_time) : null,
    display_name: payload.display_name ? String(payload.display_name) : null,
    force_human_review: Boolean(payload.force_human_review),
    gender_at_birth: payload.gender_at_birth ? String(payload.gender_at_birth) : null,
    latitude: Number(payload.latitude),
    locale: String(payload.locale || "th-TH"),
    longitude: Number(payload.longitude),
    primary_focus_question: payload.primary_focus_question ? String(payload.primary_focus_question) : null,
    target_year: Number(payload.target_year),
    timezone: String(payload.timezone || "UTC"),
    unknown_hour: Boolean(payload.unknown_hour),
  };
  return JSON.stringify(normalized);
}

export function requestIdFor(payload) {
  const digest = createHash("sha256").update(canonicalJson(payload), "utf8").digest("hex").slice(0, 20);
  return `unified-reading-${digest}`;
}

export function createUnifiedReading(rawPayload) {
  let payload = rawPayload;
  if (Buffer.isBuffer(payload)) {
    try {
      payload = JSON.parse(payload.toString("utf8"));
    } catch {
      throw new UnifiedReadingError(400, "invalid_request_body", "Request body must be valid JSON");
    }
  } else if (typeof payload === "string") {
    try {
      payload = JSON.parse(payload);
    } catch {
      throw new UnifiedReadingError(400, "invalid_request_body", "Request body must be valid JSON");
    }
  }

  if (!payload || typeof payload !== "object") {
    throw new UnifiedReadingError(422, "invalid_request_data", "Missing request body");
  }

  if (!payload.birth_date || payload.target_year === undefined || payload.target_year === null) {
    throw new UnifiedReadingError(422, "invalid_request_data", "birth_date and target_year are required");
  }

  const birthDateStr = String(payload.birth_date);
  const dateMatch = birthDateStr.match(/^(\d{4})-(\d{1,2})-(\d{1,2})/);
  if (!dateMatch) {
    throw new UnifiedReadingError(422, "invalid_date_range", "Invalid birth_date format");
  }
  const birthYear = parseInt(dateMatch[1], 10);
  const targetYear = parseInt(payload.target_year, 10);

  if (!Number.isFinite(targetYear) || targetYear < 1900 || targetYear > 2200) {
    throw new UnifiedReadingError(422, "invalid_target_year", "target_year must be between 1900 and 2200");
  }
  if (birthYear > targetYear) {
    throw new UnifiedReadingError(422, "invalid_date_range", `birth_date year (${birthYear}) must not be after target_year (${targetYear})`);
  }

  const normalizedPayload = {
    birth_date: birthDateStr,
    birth_time: payload.birth_time ? String(payload.birth_time) : null,
    unknown_hour: Boolean(payload.unknown_hour),
    birth_place: String(payload.birth_place || ""),
    latitude: Number(payload.latitude || 0.0),
    longitude: Number(payload.longitude || 0.0),
    timezone: String(payload.timezone || "UTC"),
    gender_at_birth: payload.gender_at_birth ? String(payload.gender_at_birth) : null,
    target_year: targetYear,
    locale: String(payload.locale || "th-TH"),
    display_name: payload.display_name ? String(payload.display_name) : null,
    primary_focus_question: payload.primary_focus_question ? String(payload.primary_focus_question) : null,
    force_human_review: Boolean(payload.force_human_review),
    tradition_monthly_claims: payload.tradition_monthly_claims || null,
    consensus_fixture_id: payload.consensus_fixture_id || null,
  };

  const annualTiming = calculateAnnualTiming(normalizedPayload);
  const patternPayload = generatePastPatternCandidates(normalizedPayload);

  const monthlyScores = annualTiming.monthly_scores.map((rawMonth) => {
    const cScore = scoreFromMonth(rawMonth, "career");
    const fScore = scoreFromMonth(rawMonth, "finance");
    const lScore = scoreFromMonth(rawMonth, "love");
    const item = {
      month: Number(rawMonth.month),
      career_score: cScore,
      finance_score: fScore,
      love_score: lScore,
      confidence: apiConfidence(rawMonth.confidence),
      score_basis: rawMonth.score_basis || {},
      reasons: rawMonth.reasons || ["มีหลักฐานสถิติการโคจรของดวงดาวประจำปีรองรับ"],
    };
    for (const domain of ["career", "finance", "love"]) {
      const range = rawMonth[`${domain}_score_range`];
      if (Array.isArray(range) && range.length === 2) {
        item[`${domain}_score_range`] = [Number(range[0]), Number(range[1])];
      } else {
        item[`${domain}_score_range`] = null;
      }
    }
    return item;
  });

  const topics = buildTopicModules(normalizedPayload, monthlyScores, annualTiming, patternPayload);

  const candidates = patternPayload.candidates || [];
  let insufficientReason = null;
  if (candidates.length === 0) {
    const ageAtTarget = targetYear - birthYear;
    insufficientReason = (
      `เจ้าชะตามีอายุประมาณ ${ageAtTarget} ปี ในปีเป้าหมาย ${targetYear}; ` +
      `ข้อมูลสถิติในอดีตยังไม่เพียงพอต่อการวิเคราะห์ ` +
      `(insufficient history -- ต้องมีอายุอย่างน้อย 8 ปีบริบูรณ์ขึ้นไป)`
    );
  }

  const requestId = requestIdFor(normalizedPayload);

  const [bYear, bMonth, bDay] = birthDateStr.split("-").map(Number);
  const [yearStemIdx, yearBranchIdx] = yearStemBranch(bYear, bMonth, bDay);
  const [monthStemIdx, monthBranchIdx] = monthStemBranch(yearStemIdx, bMonth, bDay);
  const [dayStemIdx, dayBranchIdx] = dayStemBranch(bYear, bMonth, bDay);

  let hourVal = 12;
  if (!normalizedPayload.unknown_hour && normalizedPayload.birth_time) {
    const parts = String(normalizedPayload.birth_time).split(":");
    hourVal = Number(parts[0]) || 0;
  }
  const hourBranchIdx = Math.floor(((hourVal + 1) % 24) / 2) % 12;
  const ratBase = [0, 2, 4, 6, 8][dayStemIdx % 5];
  const hourStemIdx = (ratBase + hourBranchIdx) % 10;

  const baziChart = {
    year_stem: STEMS[yearStemIdx].name,
    year_branch: BRANCHES[yearBranchIdx].name,
    year_element: THAI_ELEMENTS[STEMS[yearStemIdx].element] || STEMS[yearStemIdx].element,
    year_animal: BRANCHES[yearBranchIdx].animal,
    month_stem: STEMS[monthStemIdx].name,
    month_branch: BRANCHES[monthBranchIdx].name,
    month_element: THAI_ELEMENTS[STEMS[monthStemIdx].element] || STEMS[monthStemIdx].element,
    month_animal: BRANCHES[monthBranchIdx].animal,
    day_stem: STEMS[dayStemIdx].name,
    day_branch: BRANCHES[dayBranchIdx].name,
    day_element: THAI_ELEMENTS[STEMS[dayStemIdx].element] || STEMS[dayStemIdx].element,
    day_animal: BRANCHES[dayBranchIdx].animal,
    hour_stem: STEMS[hourStemIdx].name,
    hour_branch: BRANCHES[hourBranchIdx].name,
    hour_element: THAI_ELEMENTS[STEMS[hourStemIdx].element] || STEMS[hourStemIdx].element,
  };

  const ziWeiChart = calculateZiWeiDouShuChart(normalizedPayload);
  const solarTime = calculateTrueSolarTime(normalizedPayload);
  const thaiLagna = calculateThaiLagna(bMonth, hourVal);
  const plainSummary = buildPlainLanguageSummary(normalizedPayload, monthlyScores, annualTiming, ziWeiChart);
  const fateBookPrompt = buildFateBookMasterPrompt(normalizedPayload, baziChart, ziWeiChart, thaiLagna, solarTime, plainSummary);

  return {
    schema_version: "horo_lite_unified_reading.v1",
    request_id: requestId,
    target_year: targetYear,
    topics,
    monthly_scores: monthlyScores,
    past_patterns: candidates,
    insufficient_history_reason: insufficientReason,
    consensus_metadata: annualTiming.consensus_metadata,
    hitl_flags: annualTiming.hitl_flags,
    hitl_routing: annualTiming.hitl_routing,
    llm_metadata: {
      source: "deterministic_copy_transformer",
      model_used: null,
      translation_requested: false,
      translation_enabled_by_env: false,
      facts_mutable_by_llm: false,
      network_call_performed: false,
      deterministic_facts_source: "project.core.annual_timing_engine",
    },
    plain_summary: plainSummary,
    fate_book_prompt: fateBookPrompt,
    zi_wei: ziWeiChart,
  };
}
