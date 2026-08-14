"""
project/core/question_focus_router.py — Question-Focused Answering Router
==========================================================================
Routes user questions to domain-specific answering strategies, ensuring
AI interpretations directly address the user's specific question rather
than providing generic natal chart overviews.

Source: plans/question_forecast_alignment_spec.md

6 Domain Categories:
  1. Career & Business (การงาน/ธุรกิจ)
  2. Finance & Wealth (การเงิน/โชคลาภ)
  3. Love & Marriage (ความรัก/คู่ครอง)
  4. Health & Longevity (สุขภาพ/อายุขัย)
  5. Family & Offspring (ครอบครัว/บุตร)
  6. Luck Cycles & Date Selection (วงจรโชค/ฤกษ์ยาม)
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("question_focus_router")

# ---------------------------------------------------------------------------
# Domain Classification Keywords
# ---------------------------------------------------------------------------

DOMAIN_KEYWORDS: Dict[str, List[str]] = {
    "career": [
        # Chinese astrological terms
        "官星", "七殺", "正官", "偏官", "官祿", "遷徙", "開門", "生門",
        # Thai/English terms
        "เปลี่ยนงาน", "ย้ายสายงาน", "เปิดธุรกิจ", "เลื่อนตำแหน่ง", "ย้ายงาน", "เปิดกิจการ",
        "งาน", "อาชีพ", "ธุรกิจ", "ตกงาน", "สัมภาษณ์งาน", "หัวหน้า",
        "career", "job", "business", "promotion", "work", "profession",
        "startup", "company", "resign", "employ",
    ],
    "finance": [
        # Chinese
        "偏財", "正財", "劫財", "財帛", "比肩", "財星",
        # Thai/English
        "โชคลาภ", "ลาภลอย", "การเงิน", "ทรัพย์สิน", "หนี้สิน", "ลงทุน", "หุ้น",
        "เงิน", "ลาภ", "ทรัพย์", "กำไร", "ขาดทุน",
        "money", "finance", "wealth", "invest", "stock", "lottery",
        "income", "debt", "profit", "loss", "windfall",
    ],
    "love": [
        # Chinese
        "夫妻", "妻財", "桃花", "咸池", "紅鸞", "天喜", "六合", "三合",
        # Thai/English
        "ความรัก", "คู่ครอง", "แต่งงาน", "ดวงสมพงษ์", "หุ้นส่วน", "คบหา", "เนื้อคู่",
        "รัก", "สมพงษ์", "แฟน", "หย่าร้าง",
        "love", "marriage", "relationship", "partner", "spouse", "dating",
        "compatibility", "wedding", "divorce",
    ],
    "health": [
        # Chinese
        "疾厄", "傷官", "七殺攻身", "五行失衡",
        # Thai/English
        "เจ็บป่วย", "อุบัติเหตุ", "สุขภาพ", "ผ่าตัด", "เลือดตกยางออก", "โรคประจำตัว",
        "โรค", "อายุ", "โรงพยาบาล",
        "health", "illness", "accident", "disease", "surgery", "mental",
        "hospital", "doctor", "organ", "longevity",
    ],
    "family": [
        # Chinese
        "子女", "父母", "食傷", "食神", "傷官", "兄弟", "奴僕",
        # Thai/English
        "มีลูก", "มีบุตร", "ครอบครัว", "พ่อแม่", "พี่น้อง", "บุตรบริวาร",
        "ลูก", "บุตร",
        "child", "children", "family", "parent", "sibling", "offspring",
        "pregnancy", "fertility",
    ],
    "timing": [
        # Chinese
        "擇吉", "建除", "飛星", "大運", "流年", "節氣", "吉日", "吉時",
        # Thai/English
        "ฤกษ์ยาม", "วันมงคล", "ฤกษ์ดี", "เลือกวัน", "ยามมงคล", "วันดี", "ฤกษ์",
        "ช่วงเวลา", "วันไหน", "เหมาะแก่การ", "เซ็นสัญญา", "ออกรถ", "ขึ้นบ้านใหม่",
        "timing", "auspicious date", "lucky day", "best date", "date selection", "when",
    ],

}


# ---------------------------------------------------------------------------
# Domain-Specific Analysis Guides (Multi-Engine Focus Directives)
# ---------------------------------------------------------------------------

DOMAIN_ANALYSIS_GUIDES: Dict[str, Dict[str, str]] = {
    "career": {
        "bazi": "Focus on Officer Star (官星/正官) vs Seven Killings (七殺) strength. "
                "Analyze Wealth Star (財星) for business potential vs Officer Star for employment. "
                "Identify the Useful God (用神) for career direction.",
        "ziwei": "Examine Career Palace (官祿宮) and Migration Palace (遷徙宮). "
                 "Check for transformation powers (化權/化忌) affecting career.",
        "qimen": "Assess Open Door (開門) for career stability and Life Door (生門) for business ventures.",
        "guidance": "MUST compare 'employed/career change' vs 'self-employment/business' directly. "
                    "Specify auspicious months and months to avoid. "
                    "Provide 3 actionable strategic recommendations.",
    },
    "finance": {
        "bazi": "Analyze Indirect Wealth (偏財) for speculative/windfall gains vs Direct Wealth (正財) "
                "for earned income. Check Robbery Star (劫財) for financial leakage points.",
        "ziwei": "Examine Wealth Palace (財帛宮) and Siblings Palace (兄弟宮/奴僕宮) for "
                 "partner/friend financial drain risks.",
        "uranian": "Check Jupiter/Kronos/Cupido influence points vs Hades/Vulkanus for "
                   "investment timing and risk assessment.",
        "guidance": "MUST distinguish speculative wealth from earned wealth. "
                    "Identify specific financial leakage points in the chart. "
                    "Recommend asset conversion strategies aligned with the Useful God element.",
    },
    "love": {
        "bazi": "Examine Day Pillar (日柱/夫妻宮) Branch Interactions: "
                "Harmony (六合/三合) vs Clash (六沖/相害) between partners.",
        "ziwei": "Check Spouse Palace (夫妻宮) and Servants Palace (奴僕宮/事業宮) for partnership.",
        "iching": "Assess hexagram Five Relatives (五親): Wife-Wealth (妻財) and Siblings (兄弟).",
        "guidance": "MUST provide a Compatibility Index with specific strengths and conflict risks. "
                    "Clarify contractual/partnership caution points. "
                    "Offer relationship management advice based on astrological psychology.",
    },
    "health": {
        "bazi": "Map Five Elements imbalance to organ groups: "
                "Wood=liver/gallbladder, Fire=heart/small-intestine, Earth=spleen/stomach, "
                "Metal=lungs/large-intestine, Water=kidneys/bladder. "
                "Check for clash/punishment patterns indicating accident risk.",
        "ziwei": "Examine Health Palace (疾厄宮) for chronic conditions and acute risks.",
        "guidance": "MUST identify specific organ groups at risk and high-risk months. "
                    "Recommend preventive health strategies and element-balancing practices. "
                    "Include both physical and mental health assessment.",
    },
    "family": {
        "bazi": "Analyze Eating God (食神) and Hurting Officer (傷官) for offspring prospects. "
                "Check Parent Stars and Sibling Stars strength.",
        "ziwei": "Examine Children Palace (子女宮) and Parents Palace (父母宮). "
                 "Check for transformation powers affecting family harmony.",
        "guidance": "MUST address specific family relationship dynamics. "
                    "Provide fertility/offspring timing insights where relevant. "
                    "Recommend family harmony enhancement strategies.",
    },
    "timing": {
        "zeji": "Calculate daily Duty Officers (建除十二神) and Day Clash (歲破/暗沖) analysis. "
                "Identify suitable activities for the selected date.",
        "qimen": "Assess door/star/spirit combinations for optimal timing windows.",
        "xuankong": "Check Flying Stars period alignment for spatial-temporal harmony.",
        "guidance": "MUST provide specific date recommendations with reasoning. "
                    "Include both auspicious and inauspicious periods. "
                    "Cross-reference multiple timing systems for consensus.",
    },
}

# Classical text citation references per domain
DOMAIN_CITATIONS: Dict[str, List[str]] = {
    "career":  ["滴天髓 (Di Tian Sui)", "子平真詮 (Zi Ping Zhen Quan)"],
    "finance": ["滴天髓 (Di Tian Sui)", "淵海子平 (Yuan Hai Zi Ping)"],
    "love":    ["三命通會 (San Ming Tong Hui)", "紫微斗數全書 (Zi Wei Dou Shu Quan Shu)"],
    "health":  ["滴天髓 (Di Tian Sui)", "子平真詮 (Zi Ping Zhen Quan)"],
    "family":  ["紫微斗數全書 (Zi Wei Dou Shu Quan Shu)", "三命通會 (San Ming Tong Hui)"],
    "timing":  ["協紀辨方書 (Xie Ji Bian Fang Shu)", "煙波釣叟歌 (Yan Bo Diao Sou Ge)"],
}


class QuestionFocusRouter:
    """
    Routes user questions to domain-specific answering strategies.

    Ensures AI interpretations directly answer the user's specific question
    rather than providing generic natal chart overviews. Implements the
    6-Domain Question Benchmark from question_forecast_alignment_spec.md.
    """

    def __init__(self):
        self._keyword_cache: Dict[str, set] = {
            domain: set(kw.lower() for kw in keywords)
            for domain, keywords in DOMAIN_KEYWORDS.items()
        }

    def classify_question(self, query: str) -> Tuple[str, float]:
        """
        Classify a user question into one of 6 domain categories.

        Returns:
            Tuple of (category_name, confidence_score).
            If no domain matches clearly, returns ("general", 0.0).
        """
        if not query or not query.strip():
            return ("general", 0.0)

        query_lower = query.lower()
        scores: Dict[str, int] = {}

        for domain, keywords in DOMAIN_KEYWORDS.items():
            score = 0
            for kw in keywords:
                if kw.lower() in query_lower:
                    # Chinese characters get higher weight (more specific)
                    char_factor = 3 if any("\u4e00" <= c <= "\u9fff" for c in kw) else (2 if any("\u0e01" <= c <= "\u0e5b" for c in kw) else 1)
                    score += len(kw) * char_factor

            if score > 0:
                scores[domain] = score


        if not scores:
            return ("general", 0.0)

        # Find the domain with highest score
        best_domain = max(scores, key=scores.get)  # type: ignore[arg-type]
        total_score = sum(scores.values())
        confidence = scores[best_domain] / max(total_score, 1)

        return (best_domain, round(confidence, 3))

    def get_analysis_guide(self, category: str) -> Dict[str, str]:
        """
        Get domain-specific analysis directives for each engine.

        Returns a dict mapping engine names to their analysis focus instructions.
        """
        if category in DOMAIN_ANALYSIS_GUIDES:
            return DOMAIN_ANALYSIS_GUIDES[category]
        return {"guidance": "Provide a comprehensive natal chart overview with balanced analysis."}

    def get_citation_references(self, category: str) -> List[str]:
        """Get recommended classical text citations for the identified domain."""
        return DOMAIN_CITATIONS.get(category, [
            "滴天髓 (Di Tian Sui)",
            "子平真詮 (Zi Ping Zhen Quan)",
        ])

    def build_focused_prompt(
        self,
        category: str,
        chart_data: Dict[str, Any],
        query: str,
        language: str = "th",
    ) -> str:
        """
        Build a domain-focused prompt ensuring direct, non-generic answers.

        Args:
            category: Classified question domain (career/finance/love/etc.)
            chart_data: Calculated astrological chart data dict
            query: Original user question
            language: Response language ('th' for Thai, 'en' for English, 'zh' for Chinese)

        Returns:
            A structured prompt string with domain-specific analysis directives.
        """
        guide = self.get_analysis_guide(category)
        citations = self.get_citation_references(category)

        # Extract key chart info for context
        day_master = chart_data.get("day_master", {})
        five_elements = chart_data.get("five_elements", {})
        pillars = chart_data.get("pillars", {})

        dm_stem = day_master.get("stem", "N/A")
        dm_element = day_master.get("element", "N/A")
        dominant = five_elements.get("dominant_element", "N/A")
        weakest = five_elements.get("weakest_element", "N/A")

        lang_instruction = {
            "th": "ตอบเป็นภาษาไทย ใช้ศัพท์โหราศาสตร์จีนในวงเล็บ",
            "en": "Respond in English with Chinese astrological terms in parentheses",
            "zh": "用中文回答，附上泰语解释",
        }.get(language, "ตอบเป็นภาษาไทย ใช้ศัพท์โหราศาสตร์จีนในวงเล็บ")

        # Build engine-specific analysis sections
        analysis_sections = []
        for engine_name, directive in guide.items():
            if engine_name != "guidance":
                analysis_sections.append(f"**{engine_name.upper()} Analysis Focus:**\n{directive}")

        guidance = guide.get("guidance", "")
        citations_str = ", ".join(citations)

        prompt = f"""## FOCUSED ASTROLOGICAL CONSULTATION

### User Question (คำถามผู้ใช้):
{query}

### Question Domain: {category.upper()}
### Language: {lang_instruction}

### Chart Context:
- Day Master (日主): {dm_stem} ({dm_element})
- Dominant Element: {dominant}
- Weakest Element: {weakest}
- Five Elements: {five_elements.get('percentages', {})}

### CRITICAL DIRECTIVE — Direct Focused Answering:
{guidance}

### Multi-Engine Analysis Directives:
{chr(10).join(analysis_sections)}

### Citation Requirements:
Reference classical texts: {citations_str}
Provide 3 actionable recommendations based on the analysis.

### FORBIDDEN:
- Do NOT provide a generic natal chart overview that ignores the specific question.
- Do NOT give vague, non-committal answers. Be direct and specific.
- Do NOT modify or recalculate the deterministic chart data provided above.
"""
        return prompt

    def enrich_response_metadata(
        self,
        category: str,
        confidence: float,
        response_text: str,
    ) -> Dict[str, Any]:
        """
        Enrich the AI response with question-focus metadata.

        Returns metadata dict for inclusion in API response.
        """
        guide = self.get_analysis_guide(category)
        citations = self.get_citation_references(category)

        # Check if response contains expected citations
        citation_hits = sum(1 for c in citations if c.split("(")[0].strip() in response_text)

        return {
            "question_focus": {
                "category": category,
                "confidence": confidence,
                "engines_consulted": [k for k in guide.keys() if k != "guidance"],
                "citation_coverage": f"{citation_hits}/{len(citations)}",
                "citations_expected": citations,
            }
        }


# Global singleton
question_focus_router = QuestionFocusRouter()

