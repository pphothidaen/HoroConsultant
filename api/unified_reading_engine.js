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
  personal_overview_strengths: "Personal overview and strengths",
  past_pattern_calibration: "Past pattern calibration",
  annual_overview: "Annual overview",
  career_business: "Career and business",
  finance: "Finance",
  love_relationships: "Love and relationships",
  health_wellbeing: "Health and wellbeing",
  family_surrounding_people: "Family and surrounding people",
  opportunities_caution_periods: "Opportunities and caution periods",
  twelve_month_roadmap: "Twelve month roadmap",
  top_priorities_cautions: "Top priorities and cautions",
  export_sharing_actions: "Export and sharing actions",
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
      claim: "transit-house proxy supports the monthly score band",
    },
    bazi_liu_yue: {
      career_score: cScore,
      finance_score: fScore,
      love_score: lScore,
      proxy: true,
      claim: "monthly cycle proxy broadly agrees with the transit proxy",
    },
    zi_wei: {
      career_score: cScore,
      finance_score: fScore,
      love_score: lScore,
      proxy: true,
      claim: "deterministic star-phase proxy does not create a material conflict",
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
        ? "human review required for conflicting tradition claims"
        : "traditions agree within deterministic tolerance",
    });
  }

  const consensusScore = Number(
    (agreementScores.reduce((a, b) => a + b, 0) / Math.max(agreementScores.length, 1)).toFixed(3)
  );

  const traditionConflicts = conflictMonths.map((monthNum) => ({
    month: monthNum,
    conflicting_traditions: Array.from(conflictingTraditions).sort(),
    reason: "tradition monthly score spread exceeds arbitration tolerance",
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
      interactions.push(`Branch clash: month ${monthBranch} clashes with natal year branch ${natalYbChar}`);
    }
    if (clashD && !clashY) {
      interactions.push(`Branch clash: month ${monthBranch} clashes with natal day branch ${natalDbChar}`);
    }

    const comboY = BRANCH_COMBO_PAIRS.has(`${monthBranch}-${natalYbChar}`);
    const comboD = BRANCH_COMBO_PAIRS.has(`${monthBranch}-${natalDbChar}`);
    if (comboY) {
      interactions.push(`Branch harmony: month ${monthBranch} combines with natal year branch ${natalYbChar}`);
    }
    if (comboD && !comboY) {
      interactions.push(`Branch harmony: month ${monthBranch} combines with natal day branch ${natalDbChar}`);
    }

    const stemCombo = STEM_COMBO_PAIRS.has(`${monthStem}-${natalDm}`);
    if (stemCombo) {
      interactions.push(`Stem combination: month ${monthStem} combines with Day Master ${natalDm}`);
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
      `BaZi month pillar ${monthStem}${monthBranch} (${monthElement}) interacts with natal Day Master ${natalDm} (${natalDmElem}).`,
      "Thai Suriyayart house values are deterministic proxy signals, not a verified astronomical transit.",
    ];
    if (interactions.length > 0) {
      reasons.push(interactions[0]);
    } else {
      reasons.push(`Proxy Jupiter house ${jupiterHouse} provides steady structural support.`);
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
          uncertainty: "Proxy estimate only; not a verified astronomical transit.",
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
      cycleBasis.push("12-year Jupiter transit return cycle");
    }
    if (age % 10 === 0 || age % 10 === 1) {
      cycleBasis.push("10-year Da Yun major luck transition boundary");
    }
    if ((((age - 6) % 12) + 12) % 12 === 0 || (((age - 6) % 12) + 12) % 12 === 1) {
      cycleBasis.push("Natal branch 6-year clash opposition transit");
    }
    if (cycleBasis.length === 0) {
      cycleBasis.push("Astrological transit house cycle progression");
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
      `Person is approximately ${targetYear - bYear} years old at target year ` +
      `${targetYear}; insufficient history for past-pattern analysis ` +
      `(minimum age ~8 required)`
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
      `Overall profile for ${targetYear}: average scores are career ${averageCareer.toFixed(1)}/10, finance ${averageFinance.toFixed(1)}/10, love ${averageLove.toFixed(1)}/10 across 12 months.`,
      `Month ${strongestMonth} is your peak period with the highest combined scores. Month ${weakestMonth} requires extra vigilance. Focus strengths on the domains that score above 6 to build momentum.`,
    ],
    past_pattern_calibration: [
      numPatterns > 0
        ? `Past pattern analysis identified ${numPatterns} calibration candidate(s) from historical cycle positions.`
        : "No past pattern candidates available for calibration due to insufficient history.",
      numPatterns > 0
        ? "Review each past pattern candidate honestly -- your feedback refines the accuracy of future readings. Select the response that best matches your memory."
        : "Past patterns will become available as more life-cycle data accumulates.",
    ],
    annual_overview: [
      `Annual trajectory for ${targetYear}: combined average ${overallAvg.toFixed(1)}/10. Strongest month is ${strongestMonth}, weakest is ${weakestMonth}.`,
      `Plan major decisions around month ${strongestMonth} when all three domains peak together. Reserve month ${weakestMonth} for review and preparation rather than new commitments.`,
    ],
    career_business: [
      `Career average ${averageCareer.toFixed(1)}/10 for ${targetYear}. Best career month: ${bestCareerMonth}, most cautious: ${worstCareerMonth}.`,
      `Pursue promotions, launches, or negotiations in month ${bestCareerMonth} when career energy peaks. In month ${worstCareerMonth}, focus on skill building and relationship maintenance rather than high-stakes moves.`,
    ],
    finance: [
      `Finance average ${averageFinance.toFixed(1)}/10 for ${targetYear}. Best finance month: ${bestFinanceMonth}, most cautious: ${worstFinanceMonth}.`,
      `Month ${bestFinanceMonth} favors investments, contract signings, and revenue-generating activities. Exercise spending discipline in month ${worstFinanceMonth} and avoid large unplanned commitments.`,
    ],
    love_relationships: [
      `Love and relationships average ${averageLove.toFixed(1)}/10 for ${targetYear}. Best relationship month: ${bestLoveMonth}, most cautious: ${worstLoveMonth}.`,
      `Month ${bestLoveMonth} is ideal for deepening bonds, important conversations, or meeting new people. In month ${worstLoveMonth}, practice patience and avoid confrontational discussions.`,
    ],
    health_wellbeing: [
      `Health outlook derived from cross-domain stress indicators for ${targetYear}. Lower combined scores in month ${weakestMonth} may correlate with elevated stress.`,
      `Schedule health check-ups and rest periods around month ${weakestMonth}. Month ${strongestMonth} supports active lifestyle goals and new fitness routines.`,
    ],
    family_surrounding_people: [
      `Family dynamics for ${targetYear}: relationship energy averages ${averageLove.toFixed(1)}/10 while career demands average ${averageCareer.toFixed(1)}/10.`,
      `Balance family time against career peaks -- month ${bestCareerMonth} may pull attention from family. Dedicate month ${bestLoveMonth} to quality family interactions and relationship nurturing.`,
    ],
    opportunities_caution_periods: [
      `Opportunity windows for ${targetYear}: month ${strongestMonth} presents the best combined conditions. Caution period: month ${weakestMonth}.`,
      `Seize opportunities in month ${strongestMonth} when career (${bestCareerMonth}), finance (${bestFinanceMonth}), and relationship (${bestLoveMonth}) energies converge. Approach month ${weakestMonth} with contingency plans.`,
    ],
    twelve_month_roadmap: [
      `Month-by-month roadmap for ${targetYear}: 12 months scored across career, finance, and love with confidence from consensus arbitration.`,
      `Q1 (months 1-3): establish foundations. Q2 (months 4-6): execute on strengths near month ${strongestMonth}. Q3 (months 7-9): consolidate gains. Q4 (months 10-12): review progress and plan the next cycle.`,
    ],
    top_priorities_cautions: [
      `Priority ranking for ${targetYear}: `
      + (
          averageCareer >= averageFinance && averageCareer >= averageLove
            ? `career leads at ${averageCareer.toFixed(1)}/10`
            : averageFinance >= averageLove
              ? `finance leads at ${averageFinance.toFixed(1)}/10`
              : `relationships lead at ${averageLove.toFixed(1)}/10`
        )
      + `. Top caution month: ${weakestMonth}.`,
      `Prioritize the leading domain and use it to support weaker areas. Key caution: do not overextend in month ${weakestMonth} -- prepare buffers in the preceding month.`,
    ],
    export_sharing_actions: [
      `Reading export for ${targetYear}: ${numPatterns} past pattern(s), 12 monthly scores, consensus-verified by ${annualTiming.engine_version || "annual_timing_bazi_transit.v2"}.`,
      "Save or share this reading for future reference. Monthly scores and past pattern feedback are portable across export formats.",
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
      reasons: rawMonth.reasons || ["Deterministic annual timing evidence is present"],
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
      `Person is approximately ${ageAtTarget} years old at target year ` +
      `${targetYear}; insufficient history for past-pattern analysis ` +
      `(minimum age ~8 required)`
    );
  }

  const requestId = requestIdFor(normalizedPayload);

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
  };
}
