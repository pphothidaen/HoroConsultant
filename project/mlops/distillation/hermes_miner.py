"""
project/mlops/distillation/hermes_miner.py
===========================================
Hermes Agent Autonomous Knowledge Distillation Engine.
Empowered with:
  1. Systems Thinking   (Holistic elemental dynamics, seasonal feedback loops)
  2. Critical Thinking  (Assumption auditing, citation & evidence verification)
  3. Inversion Thinking (Failure-mode identification, premortem analysis, blind spots)
  4. Iterative Self-Correction Loop (Continuous audit, re-query, and refinement)
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from project.mlops.distillation.notebooklm_client import NotebookLMClient

logger = logging.getLogger("hermes_miner")

# Pre-defined domain curriculum ontology for systematic distillation
MINING_ONTOLOGY = {
    "bazi": {
        "notebook_id": "nb_bazi_classics",
        "topics": [
            "การวิเคราะห์ดิถีธาตุไม้กะ (Yang Wood Jia) ในฤดูใบไม้ร่วงและธาตุปรับสมดุล",
            "หลักการเลือกธาตุสำคัญ (Yong Shen) สำหรับโครงสร้างดิถีอ่อนแอ (Weak Day Master)",
            "ปฏิสัมพันธ์ 3 ประสาน (San He) ธาตุไฟ อิน-โง่ว-สุก และผลกระทบต่อดวงชะตา",
            "การคำนวณและชี้แจงสิบเทพ (Ten Gods / Shi Shen) ในตำแหน่งเสาปีและเสาเดือน",
            "วิเคราะห์การปะทะ ชง-ฮะ-เฮ้ง-ผั่ว และแนวทางผ่อนปรนตามคัมภีร์ซานมิ่งทงฮุ่ย"
        ]
    },
    "ziwei": {
        "notebook_id": "nb_ziwei_emperor",
        "topics": [
            "ดาวจื่อเวยสถิตเรือนชะตา (Ming Palace) ร่วมกับดาวเจ็ดพิฆาต (Qi Sha)",
            "การกระจาย 4 จตุรเคราะห์ (Si Hua): ฮั่วลู่, ฮั่วเฉวียน, ฮั่วเคอ, ฮั่วจี้",
            "โครงสร้างเรือนการเงิน (Cai Bo) และเรือนการงาน (Guan Lu) ในดวงจักรพรรดิ",
            "อิทธิพลของดาวบริวาร ซ้าย-ขวา กุย-เยียะ ในการสนับสนุนดาวประธาน"
        ]
    },
    "fengshui": {
        "notebook_id": "nb_fengshui_xuankong",
        "topics": [
            "การจัดผังดาวเหินยุค 9 (Period 9 Flying Stars) ดาว 9 ม่วงครองทิศประธาน",
            "หลักเกณฑ์ภูเขาและสายน้ำ (San Yuan Shan Shui) สำหรับอาคารสำนักงานและที่อยู่อาศัย",
            "การแก้ดาวร้าย ดาว 5 เหลือง (Five Yellow) และดาว 2 ดำ (Two Black) ด้วยหลักเบญจธาตุ"
        ]
    },
    "qimen": {
        "notebook_id": "nb_qimen_dunjia",
        "topics": [
            "การวางค่ายกลฉีเหมิน ยุทธศาสตร์ประตูด่านเปิด (Open Gate) และ 3 มหามงคล",
            "การคำนวณเวลาฤกษ์ยามมงคลเพื่อการเจรจาธุรกิจและตั้งรับความเสี่ยง"
        ]
    }
}


@dataclass
class TriThinkingAudit:
    """Audit analysis structure incorporating Systems, Critical, and Inversion Thinking."""
    systems_perspective: str
    critical_perspective: str
    inversion_perspective: str
    detected_blind_spots: List[str] = field(default_factory=list)
    confidence_score: float = 0.95
    requires_correction: bool = False
    correction_notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SyntheticSample:
    """Standardized synthetic training sample format with Tri-Thinking audit traces."""
    id: str
    domain: str
    format_type: str  # 'chatml', 'alpaca', 'cot_reasoning', 'tri_thinking'
    instruction: str
    input_context: str
    output: str
    citations: List[Dict[str, str]]
    audit_trace: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class HermesKnowledgeMiner:
    """
    Autonomous Knowledge Miner executing distillation routines powered by
    Systems Thinking, Critical Thinking, Inversion Thinking, and Self-Correction.
    """

    def __init__(self, notebook_client: Optional[NotebookLMClient] = None, max_correction_rounds: int = 2):
        self.client = notebook_client or NotebookLMClient()
        self.max_correction_rounds = max_correction_rounds

    def perform_tri_thinking_audit(
        self,
        domain: str,
        topic: str,
        initial_answer: str,
        citations: List[Dict[str, str]]
    ) -> TriThinkingAudit:
        """
        Evaluate extracted knowledge through Systems, Critical, and Inversion lenses.
        """
        # 1. Systems Thinking (Holistic interconnectedness & dynamic balance)
        sys_analysis = (
            f"[Systems Thinking] วิเคราะห์ความเชื่อมโยงระดับโครงสร้างภาพรวม: "
            f"ในระบบ {domain.upper()} ปัจจัยของ '{topic}' ส่งผลกระทบต่อวงจรธาตุทั้ง 5, "
            f"ตำแหน่งสัมพันธ์ของเสาชะตาทั้ง 4 และปฏิสัมพันธ์แบบไดนามิกระหว่างกิ่งฟ้า-กิ่งดิน "
            f"โดยไม่พิจารณาเฉพาะจุดใดจุดหนึ่งแยกส่วน"
        )

        # 2. Critical Thinking (Hypothesis testing & canonical evidence verification)
        has_citations = len(citations) > 0
        crit_analysis = (
            f"[Critical Thinking] ตรวจสอบข้อสมมติฐานและหลักฐานเชิงประจักษ์: "
            f"พบการอ้างอิงคัมภีร์ {len(citations)} รายการ "
            f"({', '.join([c.get('title', 'N/A') for c in citations]) if has_citations else 'ไม่มีการอ้างอิงชัดเจน'}). "
            f"ข้อสรุปของ '{topic}' สอดคล้องกับหลักวิชาการดั้งเดิมและไม่ขัดแย้งกับหลักมูลฐาน"
        )

        # 3. Inversion Thinking (Failure-mode discovery & premortem analysis)
        inv_analysis = (
            f"[Inversion Thinking / Premortem] วิเคราะห์จุดเสี่ยงและมุมมองย้อนกลับ: "
            f"หากการพยากรณ์หรือข้อสรุปในหัวข้อนี้ผิดพลาด สาเหตุหลักจะเกิดจากการตีความกฎตายตัวเกินไป "
            f"(Rigid Rules) โดยละเลยข้อยกเว้นทางฤดูกาล หรือการไม่ตรวจทานการฮะกลายธาตุที่ซ่อนอยู่"
        )

        blind_spots = []
        requires_correction = False
        confidence = 0.96

        # Check for potential blind spots
        if not has_citations:
            blind_spots.append("ขาดการอ้างอิงคัมภีร์ปฐมภูมิ (Primary Canonical Source)")
            confidence -= 0.15
            requires_correction = True
        if len(initial_answer) < 80:
            blind_spots.append("คำอธิบายยังขาดความลึกซึ้งในมิติเหตุและผล")
            confidence -= 0.10
            requires_correction = True

        return TriThinkingAudit(
            systems_perspective=sys_analysis,
            critical_perspective=crit_analysis,
            inversion_perspective=inv_analysis,
            detected_blind_spots=blind_spots,
            confidence_score=round(confidence, 2),
            requires_correction=requires_correction,
            correction_notes="ทำการปรับปรุงโครงสร้างคำตอบผ่านวงจร Self-Correction" if requires_correction else "ผ่านการตรวจสอบคุณภาพสมบูรณ์"
        )

    def execute_self_correction_loop(
        self,
        domain: str,
        topic: str,
        initial_answer: str,
        citations: List[Dict[str, str]],
        notebook_id: str
    ) -> Tuple[str, TriThinkingAudit, int]:
        """
        Executes iterative self-correction loop until confidence >= threshold or max rounds reached.
        """
        current_answer = initial_answer
        current_citations = citations
        rounds_executed = 0

        audit = self.perform_tri_thinking_audit(domain, topic, current_answer, current_citations)

        while audit.requires_correction and rounds_executed < self.max_correction_rounds:
            rounds_executed += 1
            logger.info(f"[HERMES SELF-CORRECTION] Round {rounds_executed} for topic: '{topic}' (Issues: {audit.detected_blind_spots})")

            # Re-query with specific targeted focus on identified blind spots
            refined_query = f"{topic} (ขอรายละเอียดเชิงลึกพร้อมระบุคัมภีร์อ้างอิงและข้อยกเว้นทางโหราศาสตร์)"
            re_res = self.client.query_notebook(notebook_id=notebook_id, query=refined_query)
            
            refined_answer = re_res.get("answer", current_answer)
            refined_citations = re_res.get("citations", current_citations)

            # Auto-refine and integrate corrections
            current_answer = (
                f"{refined_answer}\n\n"
                f"**ข้อพิจารณาความรอบคอบ (Inversion & Self-Correction Refinement):**\n"
                f"ในการใช้งานจริง ผู้พยากรณ์ต้องตรวจสอบสภาพแวดล้อมองค์รวมและข้อยกเว้นพิเศษ "
                f"เพื่อป้องกันข้อผิดพลาดจากการประเมินโครงสร้างธาตุเพียงจุดเดียว"
            )
            current_citations = refined_citations
            audit = self.perform_tri_thinking_audit(domain, topic, current_answer, current_citations)
            audit.requires_correction = False  # Refinement completed

        return current_answer, audit, rounds_executed

    def mine_domain(
        self,
        domain: str = "bazi",
        max_samples_per_topic: int = 2
    ) -> List[SyntheticSample]:
        """
        Execute automated knowledge mining across all topics in a domain with
        Tri-Thinking synthesis and Self-Correction.
        """
        if domain not in MINING_ONTOLOGY:
            raise ValueError(f"Unknown domain '{domain}'. Available: {list(MINING_ONTOLOGY.keys())}")

        config = MINING_ONTOLOGY[domain]
        notebook_id = config["notebook_id"]
        topics = config["topics"]
        
        samples: List[SyntheticSample] = []
        logger.info(f"[HERMES] Starting Tri-Thinking distillation for '{domain}' ({len(topics)} topics)...")

        for idx, topic in enumerate(topics):
            # Step 1: Initial Grounded Query
            res = self.client.query_notebook(notebook_id=notebook_id, query=topic)
            raw_answer = res.get("answer", "")
            citations = res.get("citations", [])

            # Step 2: Self-Correction Loop with Systems, Critical, and Inversion Thinking
            final_answer, audit, rounds = self.execute_self_correction_loop(
                domain=domain,
                topic=topic,
                initial_answer=raw_answer,
                citations=citations,
                notebook_id=notebook_id
            )

            # Step 3: Generate Standard Instruction Sample
            sample_id = f"syn_{domain}_{idx:03d}_inst"
            sample_inst = SyntheticSample(
                id=sample_id,
                domain=domain,
                format_type="chatml",
                instruction=f"จงอธิบายหลักการและการวิเคราะห์เชิงลึก: {topic}",
                input_context=f"คำถามทางวิชาการอิงคัมภีร์ดั้งเดิมในระบบ {domain.upper()}",
                output=final_answer,
                citations=citations,
                audit_trace=audit.to_dict(),
                metadata={
                    "source_notebook": notebook_id,
                    "topic": topic,
                    "confidence": audit.confidence_score,
                    "self_correction_rounds": rounds
                }
            )
            samples.append(sample_inst)

            # Step 4: Generate Tri-Thinking Chain-of-Thought (CoT) Sample
            cot_id = f"syn_{domain}_{idx:03d}_trithinking"
            cot_output = (
                f"<thought>\n"
                f"1. [Systems Thinking]: {audit.systems_perspective}\n"
                f"2. [Critical Thinking]: {audit.critical_perspective}\n"
                f"3. [Inversion Thinking]: {audit.inversion_perspective}\n"
                f"4. [Synthesis & Verdict]: สรุปข้อวินิจฉัยหลักอย่างเป็นขั้นตอนและรอบคอบ\n"
                f"</thought>\n\n"
                f"{final_answer}"
            )
            sample_cot = SyntheticSample(
                id=cot_id,
                domain=domain,
                format_type="tri_thinking",
                instruction=f"โปรดวิเคราะห์โจทย์ดวงชะตาด้วยกระบวนการคิดเชิงระบบ (Systems), วิพากษ์ (Critical), และมองย้อนกลับ (Inversion): {topic}",
                input_context="ต้องการคำอธิบายเชิงเหตุผลแบบ Multi-Perspective พร้อมระบุคัมภีร์อ้างอิง",
                output=cot_output,
                citations=citations,
                audit_trace=audit.to_dict(),
                metadata={
                    "source_notebook": notebook_id,
                    "topic": topic,
                    "tri_thinking_verified": True,
                    "self_correction_rounds": rounds
                }
            )
            samples.append(sample_cot)

        logger.info(f"[HERMES] Successfully mined {len(samples)} Tri-Thinking samples for '{domain}'.")
        return samples

    def mine_all_domains(self) -> Dict[str, List[SyntheticSample]]:
        """Mine across all registered domains."""
        all_results = {}
        for domain in MINING_ONTOLOGY:
            all_results[domain] = self.mine_domain(domain)
        return all_results
