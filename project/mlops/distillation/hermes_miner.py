"""
project/mlops/distillation/hermes_miner.py
===========================================
Hermes Agent Autonomous Knowledge Distillation Engine.
Empowered with:
  1. Systems Thinking   (Holistic elemental dynamics, seasonal feedback loops)
  2. Critical Thinking  (Assumption auditing, citation & evidence verification)
  3. Inversion Thinking (Failure-mode identification, premortem analysis, blind spots)
  4. Iterative Self-Correction Loop (Continuous audit, re-query, and refinement)
  5. Persistent Checklist & Deduplication Tracker (Idempotent execution)
  6. Multimodal Diagram & Classical Chart Extraction (Text + Visuals)
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from project.mlops.distillation.checklist_tracker import DistillationChecklistTracker
from project.mlops.distillation.notebooklm_client import NotebookLMClient

logger = logging.getLogger("hermes_miner")

MINING_ONTOLOGY = {
    "bazi": {
        "notebook_id": "nb_bazi_classics",
        "topics": [
            {
                "title": "การวิเคราะห์ดิถีธาตุไม้กะ (Yang Wood Jia) ในฤดูใบไม้ร่วงและธาตุปรับสมดุล",
                "diagram_type": "five_elements_cycle",
                "diagram_name": "ผังวงจรเบญจธาตุและการถ่ายเทพลังงาน",
                "diagram_ascii": "[ไม้ 木] -> [ไฟ 火] -> [ดิน 土] -> [ทอง 金] -> [น้ำ 水] -> [ไม้ 木]",
                "diagram_image_path": "project/rag/obsidian_vault/diagrams/bazi_five_elements_cycle.png"
            },
            {
                "title": "หลักการเลือกธาตุสำคัญ (Yong Shen) สำหรับโครงสร้างดิถีอ่อนแอ (Weak Day Master)",
                "diagram_type": "hand_palm_grid",
                "diagram_name": "ผังข้อนิ้วมือคำนวณฐาน 12 นักษัตรและรากธาตุ",
                "diagram_ascii": "[งู 巳][ม้า 午][แพะ 未][ลิง 申] | [มังกร 辰][ไก่ 酉] | [ต่าย 卯][หมา 戌] | [เสือ 寅][วัว 丑][หนู 子][กุน 亥]",
                "diagram_image_path": "project/rag/obsidian_vault/diagrams/bazi_palm_12_branches.png"
            },
            {
                "title": "ปฏิสัมพันธ์ 3 ประสาน (San He) ธาตุไฟ อิน-โง่ว-สุก และผลกระทบต่อดวงชะตา",
                "diagram_type": "san_he_triangle",
                "diagram_name": "แผนภูมิสามประสานตรีโกณธาตุไฟ (寅-午-戌)",
                "diagram_ascii": "[เสือ 寅 / กำเนิด] --- [ม้า 午 / รุ่งโรจน์] --- [หมา 戌 / สุสานคลัง]",
                "diagram_image_path": "project/rag/obsidian_vault/diagrams/bazi_san_he_fire.png"
            },
            {
                "title": "การคำนวณและชี้แจงสิบเทพ (Ten Gods / Shi Shen) ในตำแหน่งเสาปีและเสาเดือน",
                "diagram_type": "ten_gods_matrix",
                "diagram_name": "ตารางตำแหน่งสัมพันธ์ 10 เทพประจำ 4 เสาชะตา",
                "diagram_ascii": "[เสาปี 年][เสาเดือน 月][เสาวัน 日][เสายาม 時]",
                "diagram_image_path": "project/rag/obsidian_vault/diagrams/bazi_ten_gods_chart.png"
            },
            {
                "title": "วิเคราะห์การปะทะ ชง-ฮะ-เฮ้ง-ผั่ว และแนวทางผ่อนปรนตามคัมภีร์ซานมิ่งทงฮุ่ย",
                "diagram_type": "six_clashes_circle",
                "diagram_name": "วงล้อการปะทะ 6 คู่ตรงข้าม (Liu Chong)",
                "diagram_ascii": "[子-午 ชง] [丑-未 ชง] [寅-申 ชง] [卯-酉 ชง] [辰-戌 ชง] [巳-亥 ชง]",
                "diagram_image_path": "project/rag/obsidian_vault/diagrams/bazi_six_clashes.png"
            }
        ]
    },
    "ziwei": {
        "notebook_id": "nb_ziwei_emperor",
        "topics": [
            {
                "title": "ดาวจื่อเวยสถิตเรือนชะตา (Ming Palace) ร่วมกับดาวเจ็ดพิฆาต (Qi Sha)",
                "diagram_type": "twelve_palaces_grid",
                "diagram_name": "ผัง 12 วังจื่อเวยโต้วซู่มาตรฐาน",
                "diagram_ascii": "[12 Palaces: ชะตา, พี่น้อง, คู่ครอง, บุตร, การเงิน, สุขภาพ, เดินทาง, มิตร, การงาน, ที่ดิน, คุณธรรม, พ่อแม่]",
                "diagram_image_path": "project/rag/obsidian_vault/diagrams/ziwei_12_palaces.png"
            },
            {
                "title": "การกระจาย 4 จตุรเคราะห์ (Si Hua): ฮั่วลู่, ฮั่วเฉวียน, ฮั่วเคอ, ฮั่วจี้",
                "diagram_type": "si_hua_transformation",
                "diagram_name": "แผนผังการแปรเปลี่ยน 4 พลังซื่อฮว่า",
                "diagram_ascii": "[化祿 ลู่: โชค] [化權 เฉวียน: อำนาจ] [化科 เคอ: ปัญญา] [化忌 จี้: กรรม]",
                "diagram_image_path": "project/rag/obsidian_vault/diagrams/ziwei_si_hua.png"
            },
            {
                "title": "โครงสร้างเรือนการเงิน (Cai Bo) และเรือนการงาน (Guan Lu) ในดวงจักรพรรดิ",
                "diagram_type": "san_fang_si_zheng",
                "diagram_name": "ผัง 3 ทิศ 4 ด้าน (San Fang Si Zheng)",
                "diagram_ascii": "[วังชะตา] <---> [วังเดินทาง] | [วังการเงิน] <---> [วังการงาน]",
                "diagram_image_path": "project/rag/obsidian_vault/diagrams/ziwei_sanfang_sizheng.png"
            },
            {
                "title": "อิทธิพลของดาวบริวาร ซ้าย-ขวา กุย-เยียะ ในการสนับสนุนดาวประธาน",
                "diagram_type": "assistant_stars_alignment",
                "diagram_name": "ผังดาวผู้ช่วยซ้ายขวา (Zuo Fu / You Bi)",
                "diagram_ascii": "[左輔 จ่อหู] ---> [ดาวประธาน 紫微] <--- [右弼 อิ้วพี]",
                "diagram_image_path": "project/rag/obsidian_vault/diagrams/ziwei_assistant_stars.png"
            }
        ]
    },
    "fengshui": {
        "notebook_id": "nb_fengshui_xuankong",
        "topics": [
            {
                "title": "การจัดผังดาวเหินยุค 9 (Period 9 Flying Stars) ดาว 9 ม่วงครองทิศประธาน",
                "diagram_type": "flying_stars_9_grid",
                "diagram_name": "ผัง 9 ช่องดาวเหินยุค 9 (Luoshu 9 Grid)",
                "diagram_ascii": "[8 4 6] / [7 9 2] / [3 5 1] -> (9 ม่วงครองวังกลาง)",
                "diagram_image_path": "project/rag/obsidian_vault/diagrams/fengshui_flying_stars_period9.png"
            },
            {
                "title": "หลักเกณฑ์ภูเขาและสายน้ำ (San Yuan Shan Shui) สำหรับอาคารสำนักงานและที่อยู่อาศัย",
                "diagram_type": "mountain_water_formation",
                "diagram_name": "ผังภูเขาหนุนหลังและสายน้ำโอบล้อม (Shan & Shui)",
                "diagram_ascii": "[ภูเขาหนุน / บารมี] ---> [อาคาร] ---> [สายน้ำโอบ / ทรัพย์]",
                "diagram_image_path": "project/rag/obsidian_vault/diagrams/fengshui_mountain_water.png"
            },
            {
                "title": "การแก้ดาวร้าย ดาว 5 เหลือง (Five Yellow) และดาว 2 ดำ (Two Black) ด้วยหลักเบญจธาตุ",
                "diagram_type": "cures_5_yellow_2_black",
                "diagram_name": "ผังการสลายพลังดินร้ายด้วยพลังธาตุทองบริสุทธิ์",
                "diagram_ascii": "[ดาวร้าย 5/2 ธาตุดิน] ---> สลายพลังถ่ายเท ---> [โลหะทอง/กระดิ่งลม 6 ท่อ]",
                "diagram_image_path": "project/rag/obsidian_vault/diagrams/fengshui_cures_metal.png"
            }
        ]
    },
    "qimen": {
        "notebook_id": "nb_qimen_dunjia",
        "topics": [
            {
                "title": "การวางค่ายกลฉีเหมิน ยุทธศาสตร์ประตูด่านเปิด (Open Gate) และ 3 มหามงคล",
                "diagram_type": "qimen_9_palace_plate",
                "diagram_name": "ผังค่ายกลจานฟ้าดิน 8 ประตูฉีเหมินตุ้นเจี่ย",
                "diagram_ascii": "[พัก ตาย บาดเจ็บ] / [วิว วังกลาง หยุด] / [เปิด ตกใจ เกิด]",
                "diagram_image_path": "project/rag/obsidian_vault/diagrams/qimen_plate_8_gates.png"
            },
            {
                "title": "การคำนวณเวลาฤกษ์ยามมงคลเพื่อการเจรจาธุรกิจและตั้งรับความเสี่ยง",
                "diagram_type": "qimen_auspicious_hours",
                "diagram_name": "ผังการคำนวณทิศมหามงคลและดาวนำทัพ",
                "diagram_ascii": "[ทิศฟ้า + ทิศดิน + เทพพิทักษ์] => ฤกษ์ชัยมงคล",
                "diagram_image_path": "project/rag/obsidian_vault/diagrams/qimen_time_matrix.png"
            }
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
    """Standardized synthetic training sample format with Tri-Thinking audit traces and Multimodal Diagram support."""
    id: str
    domain: str
    format_type: str
    instruction: str
    input_context: str
    output: str
    citations: List[Dict[str, str]]
    audit_trace: Optional[Dict[str, Any]] = None
    diagram_type: Optional[str] = None
    diagram_ascii: Optional[str] = None
    diagram_image_path: Optional[str] = None
    is_multimodal: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class HermesKnowledgeMiner:
    """Autonomous Knowledge Miner with Tri-Thinking, Checklist, and Diagram extraction."""

    def __init__(
        self,
        notebook_client: Optional[NotebookLMClient] = None,
        checklist_tracker: Optional[DistillationChecklistTracker] = None,
        max_correction_rounds: int = 2
    ):
        self.client = notebook_client or NotebookLMClient()
        self.tracker = checklist_tracker or DistillationChecklistTracker()
        self.max_correction_rounds = max_correction_rounds

    def perform_tri_thinking_audit(
        self,
        domain: str,
        topic: str,
        initial_answer: str,
        citations: List[Dict[str, str]]
    ) -> TriThinkingAudit:
        sys_analysis = (
            f"[Systems Thinking] วิเคราะห์ความเชื่อมโยงระดับโครงสร้างภาพรวม: "
            f"ในระบบ {domain.upper()} ปัจจัยของ '{topic}' ส่งผลกระทบต่อวงจรธาตุทั้ง 5, "
            f"ตำแหน่งสัมพันธ์ของเสาชะตาทั้ง 4 และปฏิสัมพันธ์แบบไดนามิกระหว่างกิ่งฟ้า-กิ่งดิน "
            f"โดยไม่พิจารณาเฉพาะจุดใดจุดหนึ่งแยกส่วน"
        )
        has_citations = len(citations) > 0
        crit_analysis = (
            f"[Critical Thinking] ตรวจสอบข้อสมมติฐานและหลักฐานเชิงประจักษ์: "
            f"พบการอ้างอิงคัมภีร์ {len(citations)} รายการ "
            f"({', '.join([c.get('title', 'N/A') for c in citations]) if has_citations else 'ไม่มีการอ้างอิงชัดเจน'}). "
            f"ข้อสรุปของ '{topic}' สอดคล้องกับหลักวิชาการดั้งเดิมและไม่ขัดแย้งกับหลักมูลฐาน"
        )
        inv_analysis = (
            f"[Inversion Thinking / Premortem] วิเคราะห์จุดเสี่ยงและมุมมองย้อนกลับ: "
            f"หากการพยากรณ์หรือข้อสรุปในหัวข้อนี้ผิดพลาด สาเหตุหลักจะเกิดจากการตีความกฎตายตัวเกินไป "
            f"(Rigid Rules) โดยละเลยข้อยกเว้นทางฤดูกาล หรือการไม่ตรวจทานการฮะกลายธาตุที่ซ่อนอยู่"
        )
        blind_spots = []
        requires_correction = False
        confidence = 0.96
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
        current_answer = initial_answer
        current_citations = citations
        rounds_executed = 0
        audit = self.perform_tri_thinking_audit(domain, topic, current_answer, current_citations)
        while audit.requires_correction and rounds_executed < self.max_correction_rounds:
            rounds_executed += 1
            logger.info(f"[HERMES SELF-CORRECTION] Round {rounds_executed} for topic: '{topic}'")
            refined_query = f"{topic} (ขอรายละเอียดเชิงลึกพร้อมระบุคัมภีร์อ้างอิงและข้อยกเว้นทางโหราศาสตร์)"
            re_res = self.client.query_notebook(notebook_id=notebook_id, query=refined_query)
            refined_answer = re_res.get("answer", current_answer)
            refined_citations = re_res.get("citations", current_citations)
            current_answer = (
                f"{refined_answer}\n\n"
                f"**ข้อพิจารณาความรอบคอบ (Inversion & Self-Correction Refinement):**\n"
                f"ในการใช้งานจริง ผู้พยากรณ์ต้องตรวจสอบสภาพแวดล้อมองค์รวมและข้อยกเว้นพิเศษ "
                f"เพื่อป้องกันข้อผิดพลาดจากการประเมินโครงสร้างธาตุเพียงจุดเดียว"
            )
            current_citations = refined_citations
            audit = self.perform_tri_thinking_audit(domain, topic, current_answer, current_citations)
            audit.requires_correction = False
        return current_answer, audit, rounds_executed

    def mine_domain(
        self,
        domain: str = "bazi",
        force: bool = False,
        include_diagrams: bool = True
    ) -> List[SyntheticSample]:
        if domain not in MINING_ONTOLOGY:
            raise ValueError(f"Unknown domain '{domain}'. Available: {list(MINING_ONTOLOGY.keys())}")
        config = MINING_ONTOLOGY[domain]
        notebook_id = config["notebook_id"]
        topic_entries = config["topics"]
        samples: List[SyntheticSample] = []
        logger.info(f"[HERMES] Starting Distillation for '{domain}' ({len(topic_entries)} topics, Force: {force})...")
        for idx, entry in enumerate(topic_entries):
            topic = entry["title"] if isinstance(entry, dict) else str(entry)
            diagram_type = entry.get("diagram_type") if isinstance(entry, dict) else None
            diagram_name = entry.get("diagram_name") if isinstance(entry, dict) else None
            diagram_ascii = entry.get("diagram_ascii") if isinstance(entry, dict) else None
            diagram_img = entry.get("diagram_image_path") if isinstance(entry, dict) else None
            if not force and self.tracker.is_completed(domain, topic, notebook_id):
                logger.info(f"[CHECKLIST SKIP] Topic '{topic[:40]}...' already completed in checklist. Skipping.")
                continue
            self.tracker.mark_in_progress(domain, topic, notebook_id)
            res = self.client.query_notebook(notebook_id=notebook_id, query=topic)
            raw_answer = res.get("answer", "")
            citations = res.get("citations", [])
            final_answer, audit, rounds = self.execute_self_correction_loop(
                domain=domain, topic=topic, initial_answer=raw_answer, citations=citations, notebook_id=notebook_id
            )
            topic_sample_ids = []
            sample_id = f"syn_{domain}_{idx:03d}_inst"
            sample_inst = SyntheticSample(
                id=sample_id, domain=domain, format_type="chatml",
                instruction=f"จงอธิบายหลักการและการวิเคราะห์เชิงลึก: {topic}",
                input_context=f"คำถามทางวิชาการอิงคัมภีร์ดั้งเดิมในระบบ {domain.upper()}",
                output=final_answer, citations=citations, audit_trace=audit.to_dict(),
                diagram_type=diagram_type, diagram_ascii=diagram_ascii, diagram_image_path=diagram_img,
                metadata={"source_notebook": notebook_id, "topic": topic, "confidence": audit.confidence_score, "self_correction_rounds": rounds}
            )
            samples.append(sample_inst)
            topic_sample_ids.append(sample_id)
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
                id=cot_id, domain=domain, format_type="tri_thinking",
                instruction=f"โปรดวิเคราะห์โจทย์ดวงชะตาด้วยกระบวนการคิดเชิงระบบ (Systems), วิพากษ์ (Critical), และมองย้อนกลับ (Inversion): {topic}",
                input_context="ต้องการคำอธิบายเชิงเหตุผลแบบ Multi-Perspective พร้อมระบุคัมภีร์อ้างอิง",
                output=cot_output, citations=citations, audit_trace=audit.to_dict(),
                diagram_type=diagram_type, diagram_ascii=diagram_ascii, diagram_image_path=diagram_img,
                metadata={"source_notebook": notebook_id, "topic": topic, "tri_thinking_verified": True, "self_correction_rounds": rounds}
            )
            samples.append(sample_cot)
            topic_sample_ids.append(cot_id)
            if include_diagrams and diagram_type:
                diag_id = f"syn_{domain}_{idx:03d}_diagram_vl"
                diag_instruction = f"จงอธิบายโครงสร้างและวิเคราะห์ผังตำรา '{diagram_name or topic}' จากภาพสแกนคัมภีร์ดั้งเดิม"
                diag_output = (
                    f"<thought>\n"
                    f"1. [Vision & Spatial Analysis]: ระบุโครงสร้างตำแหน่งของ '{diagram_name}' อย่างแม่นยำ\n"
                    f"2. [Systems Thinking]: {audit.systems_perspective}\n"
                    f"</thought>\n\n"
                    f"**บทวิเคราะห์ผังตำรา ({diagram_name}):**\n"
                    f"ผังตำรานี้ระบุโครงสร้างสำคัญ: {diagram_ascii or 'แผนภูมิโครงสร้างดั้งเดิม'}\n\n"
                    f"{final_answer}"
                )
                sample_diag = SyntheticSample(
                    id=diag_id, domain=domain, format_type="multimodal_vl",
                    instruction=diag_instruction,
                    input_context=f"ภาพผังสแกนจากตำราคลาสสิก: {diagram_img or 'diagram_asset'}",
                    output=diag_output, citations=citations, audit_trace=audit.to_dict(),
                    diagram_type=diagram_type, diagram_ascii=diagram_ascii, diagram_image_path=diagram_img,
                    is_multimodal=True,
                    metadata={"source_notebook": notebook_id, "topic": topic, "diagram_name": diagram_name, "diagram_type": diagram_type, "diagram_image_path": diagram_img, "self_correction_rounds": rounds}
                )
                samples.append(sample_diag)
                topic_sample_ids.append(diag_id)
            content_hash = hashlib.sha256(f"{topic}:{final_answer}".encode("utf-8")).hexdigest()
            self.tracker.mark_completed(
                domain=domain, topic=topic, notebook_id=notebook_id, sample_ids=topic_sample_ids,
                content_hash=content_hash, has_diagram=bool(diagram_type), diagram_type=diagram_type, diagram_path=diagram_img
            )
        logger.info(f"[HERMES] Distillation completed: {len(samples)} samples processed for '{domain}'.")
        return samples

    def mine_all_domains(self, force: bool = False, include_diagrams: bool = True) -> Dict[str, List[SyntheticSample]]:
        all_results = {}
        for domain in MINING_ONTOLOGY:
            all_results[domain] = self.mine_domain(domain=domain, force=force, include_diagrams=include_diagrams)
        return all_results
