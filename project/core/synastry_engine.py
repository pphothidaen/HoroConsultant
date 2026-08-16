"""
project/core/synastry_engine.py
===============================
Multi-Profile Computational Metaphysics Synastry & Compatibility Engine:
  - Day Master (日主) elemental generation/overcoming and stem combinations.
  - Spouse Palace (日支/夫妻宮) branch combinations, 3-harmonies, clashes, harms.
  - 5-Elements mutual deficit balancing.
  - 4-Tier Dimension scoring (Romantic, Business, Communication, Stability).
"""

from typing import Any, Dict, List, Optional
from project.core.transit_engine import (
    STEM_COMBINATIONS, BRANCH_COMBINATIONS, BRANCH_CLASHES,
    BRANCH_HARMS, STEM_ELEMENTS, BRANCH_ELEMENTS, HEAVENLY_STEMS, EARTHLY_BRANCHES
)

ELEMENT_GENERATION = {
    "Wood": "Fire",
    "Fire": "Earth",
    "Earth": "Metal",
    "Metal": "Water",
    "Water": "Wood"
}

ELEMENT_OVERCOMING = {
    "Wood": "Earth",
    "Earth": "Water",
    "Water": "Fire",
    "Fire": "Metal",
    "Metal": "Wood"
}


class SynastryEngine:
    """Calculates cross-chart BaZi synastry and compatibility dynamics."""

    @staticmethod
    def analyze_day_master_affinity(stem_a: str, stem_b: str) -> Dict[str, Any]:
        elem_a = STEM_ELEMENTS.get(stem_a, "Wood")
        elem_b = STEM_ELEMENTS.get(stem_b, "Wood")
        pair = frozenset([stem_a, stem_b])

        if pair in STEM_COMBINATIONS:
            comb = STEM_COMBINATIONS[pair]
            return {
                "type": "STEM_COMBINATION",
                "score": 30,
                "max": 30,
                "name": comb["name"],
                "element": comb["result"],
                "description": f"ดิถี {stem_a} ({elem_a}) รวมธาตุกับ {stem_b} ({elem_b}) เป็นคู่ธาตุสมพงษ์ฟ้าประทาน (天干五合) ก่อเกิดธาตุ {comb['result']}"
            }
        elif ELEMENT_GENERATION.get(elem_a) == elem_b or ELEMENT_GENERATION.get(elem_b) == elem_a:
            generator = stem_a if ELEMENT_GENERATION.get(elem_a) == elem_b else stem_b
            receiver = stem_b if generator == stem_a else stem_a
            return {
                "type": "ELEMENT_GENERATING",
                "score": 26,
                "max": 30,
                "name": f"ธาตุเกื้อหนุน ({elem_a} ➔ {elem_b})",
                "description": f"ดิถีเกื้อกูลส่งเสริมซึ่งกันและกัน ({generator} ส่งพลังหนุนนำ {receiver}) ก่อเกิดความเข้าใจและความผูกพันลึกซึ้ง"
            }
        elif elem_a == elem_b:
            return {
                "type": "SAME_ELEMENT",
                "score": 22,
                "max": 30,
                "name": f"ธาตุเดียวกัน ({elem_a} = {elem_b})",
                "description": f"ดิถีเป็นธาตุเดียวกัน มีอุปนิสัยและมุมมองคล้ายคลึงกัน เป็นคู่คิดและสหายร่วมทางที่เข้าอกเข้าใจกันได้ดี"
            }
        elif ELEMENT_OVERCOMING.get(elem_a) == elem_b or ELEMENT_OVERCOMING.get(elem_b) == elem_a:
            return {
                "type": "ELEMENT_OVERCOMING",
                "score": 14,
                "max": 30,
                "name": f"ธาตุพิฆาต/ท้าทาย ({elem_a} ⇋ {elem_b})",
                "description": f"ดิถีมีความแตกต่างและดึงดูดแบบขั้วตรงข้าม จำเป็นต้องใช้ความประนีประนอมและการสื่อสารเพื่อปรับสมดุล"
            }
        else:
            return {
                "type": "NEUTRAL",
                "score": 18,
                "max": 30,
                "name": "ธาตุสัมพันธ์เป็นกลาง",
                "description": f"ดิถี {stem_a} และ {stem_b} สัมพันธ์แบบอิสระ ไม่ขัดแย้งและไม่ผูกพันรุนแรง"
            }

    @staticmethod
    def analyze_spouse_palace_affinity(branch_a: str, branch_b: str) -> Dict[str, Any]:
        pair = frozenset([branch_a, branch_b])
        elem_a = BRANCH_ELEMENTS.get(branch_a, "Earth")
        elem_b = BRANCH_ELEMENTS.get(branch_b, "Earth")

        if pair in BRANCH_COMBINATIONS:
            comb = BRANCH_COMBINATIONS[pair]
            return {
                "type": "BRANCH_COMBINATION",
                "score": 30,
                "max": 30,
                "name": comb["name"],
                "favorable": True,
                "description": f"เรือนคู่ครอง (เสาวัน) รวมมิตรผูกสัมพันธ์ (地支六合) ({branch_a} + {branch_b}) ก่อเกิดความอบอุ่นและการดูแลเอาใจใส่เป็นเลิศ"
            }
        elif pair in BRANCH_CLASHES:
            return {
                "type": "BRANCH_CLASH",
                "score": 8,
                "max": 30,
                "name": BRANCH_CLASHES[pair],
                "favorable": False,
                "description": f"เรือนคู่ครองปะทะกัน (地支六沖) ({branch_a} 沖 {branch_b}) มักมีความคิดเห็นขัดแย้งเรื่องการใช้ชีวิตคู่ ควรฝึกการรับฟังและเว้นระยะส่วนตัว"
            }
        elif pair in BRANCH_HARMS:
            return {
                "type": "BRANCH_HARM",
                "score": 10,
                "max": 30,
                "name": BRANCH_HARMS[pair],
                "favorable": False,
                "description": f"เรือนคู่ครองเบียดเบียน (地支六害) ({branch_a} 害 {branch_b}) พึงระวังความน้อยใจหรือการสื่อสารคลาดเคลื่อน"
            }
        else:
            return {
                "type": "NEUTRAL",
                "score": 20,
                "max": 30,
                "name": f"เรือนคู่ครองสมดุล ({branch_a} & {branch_b})",
                "favorable": True,
                "description": f"เรือนคู่ครองดำเนินไปด้วยความราบรื่น ปราศจากการปะทะหรือผูกมิตรที่รุนแรงเกินไป"
            }

    @staticmethod
    def calculate_synastry(chart_a: Dict[str, Any], chart_b: Dict[str, Any]) -> Dict[str, Any]:
        """Compute holistic dual-profile synastry compatibility."""
        p_a = chart_a.get("pillars", {})
        p_b = chart_b.get("pillars", {})

        dm_a = chart_a.get("day_master", {}).get("stem") or p_a.get("day", {}).get("stem", {}).get("char", "甲")
        dm_b = chart_b.get("day_master", {}).get("stem") or p_b.get("day", {}).get("stem", {}).get("char", "己")

        br_a = p_a.get("day", {}).get("branch", {}).get("char", "子")
        br_b = p_b.get("day", {}).get("branch", {}).get("char", "丑")

        dm_affinity = SynastryEngine.analyze_day_master_affinity(dm_a, dm_b)
        spouse_affinity = SynastryEngine.analyze_spouse_palace_affinity(br_a, br_b)

        # 4-Tier Dimension Breakdown
        romantic_harmony = min(100, int((dm_affinity["score"] + spouse_affinity["score"]) * 1.6))
        business_synergy = min(100, int((dm_affinity["score"] * 1.8) + 40))
        communication_values = min(100, int((spouse_affinity["score"] * 1.7) + 45))
        longterm_stability = min(100, int((dm_affinity["score"] + spouse_affinity["score"]) * 1.55))

        composite_score = int((romantic_harmony * 0.35) + (business_synergy * 0.25) + (communication_values * 0.20) + (longterm_stability * 0.20))

        if composite_score >= 85:
            verdict = "ดวงสมพงษ์ระดับยอดเยี่ยม (Heavenly Match /  thượng đẳng)"
            grade = "A+"
        elif composite_score >= 70:
            verdict = "ดวงสมพงษ์ระดับดีมาก เกื้อหนุนราบรื่น (Highly Compatible / 大吉)"
            grade = "A"
        elif composite_score >= 55:
            verdict = "ดวงสมพงษ์ระดับปานกลาง ปรับจูนลงตัว (Moderate Harmony / 中吉)"
            grade = "B"
        else:
            verdict = "ดวงมีความท้าทาย ต้องอาศัยความเข้าใจและการประนีประนอม (Growth & Patience Needed)"
            grade = "C"

        return {
            "composite_score": composite_score,
            "grade": grade,
            "verdict": verdict,
            "person_a": {
                "day_master": dm_a,
                "day_branch": br_a,
                "pillar_day": f"{dm_a}{br_a}"
            },
            "person_b": {
                "day_master": dm_b,
                "day_branch": br_b,
                "pillar_day": f"{dm_b}{br_b}"
            },
            "day_master_affinity": dm_affinity,
            "spouse_palace_affinity": spouse_affinity,
            "dimensions": {
                "romantic_harmony": romantic_harmony,
                "business_synergy": business_synergy,
                "communication_values": communication_values,
                "longterm_stability": longterm_stability
            },
            "advice": [
                f"ความสัมพันธ์หลักได้รับพลังจาก {dm_affinity['name']}",
                f"เรือนคู่ครอง: {spouse_affinity['description']}",
                "ส่งเสริมความสัมพันธ์ด้วยการพูดคุยเปิดอกและสร้างเป้าหมายร่วมกันในระยะยาว"
            ]
        }


synastry_engine = SynastryEngine()
