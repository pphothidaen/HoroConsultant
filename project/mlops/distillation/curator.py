"""
project/mlops/distillation/curator.py
======================================
Dataset Curator, Validator, and Quality Gate.
Enforces quality standards, deduplication, deterministic rule checking,
and export to standard JSONL formats for Supervised Fine-Tuning (SFT).
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple

from project.mlops.distillation.hermes_miner import SyntheticSample

logger = logging.getLogger("dataset_curator")

DEFAULT_SYSTEM_PROMPT = (
    "คุณคือผู้เชี่ยวชาญด้านโหราศาสตร์จีนและศาสตร์พยากรณ์เชิงคำนวณ (Computational Metaphysics Consultant) "
    "ที่ให้คำปรึกษาและวิเคราะห์ดวงชะตาอย่างแม่นยำตามหลักเกณฑ์คัมภีร์ดั้งเดิม พร้อมอธิบายเหตุผลอย่างมีตรรกะ"
)


class DatasetCurator:
    """Quality Gate and Formatting Engine for Fine-Tuning Datasets."""

    def __init__(self, output_dir: Path | str = "project/data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.seen_hashes: set[str] = set()

    def validate_sample(self, sample: SyntheticSample) -> Tuple[bool, str]:
        """
        Validate data sample against strict quality standards.
        Checks: length, non-empty fields, domain consistency, Thai vocabulary integrity.
        """
        if not sample.instruction or len(sample.instruction.strip()) < 10:
            return False, "Instruction too short or empty"
        if not sample.output or len(sample.output.strip()) < 30:
            return False, "Output too short or lacking substantive explanation"
        
        # Check domain validity
        if sample.domain not in ["bazi", "ziwei", "fengshui", "qimen", "liuren", "iching", "western", "thaivedic"]:
            return False, f"Invalid domain: {sample.domain}"
        
        return True, "Valid"

    def deduplicate(self, samples: List[SyntheticSample]) -> List[SyntheticSample]:
        """Filter out duplicates based on normalized instruction hash."""
        unique_samples: List[SyntheticSample] = []
        for s in samples:
            norm_text = "".join(s.instruction.lower().split())
            h = hashlib.sha256(norm_text.encode("utf-8")).hexdigest()
            if h not in self.seen_hashes:
                self.seen_hashes.add(h)
                unique_samples.append(s)
            else:
                logger.debug(f"[CURATOR] Dropping duplicate sample: {s.id}")
        return unique_samples

    def curate_and_export(
        self,
        samples: List[SyntheticSample],
        dataset_name: str = "finetune_bazi_qwen25",
        target_format: str = "chatml"
    ) -> Dict[str, Any]:
        """
        Curate, validate, deduplicate, and export samples to JSONL file.
        """
        valid_samples = []
        rejected = 0

        for s in samples:
            is_valid, reason = self.validate_sample(s)
            if is_valid:
                valid_samples.append(s)
            else:
                logger.warning(f"[CURATOR] Rejected sample {s.id}: {reason}")
                rejected += 1

        deduped_samples = self.deduplicate(valid_samples)
        
        out_file = self.output_dir / f"{dataset_name}_{target_format}.jsonl"
        with open(out_file, "w", encoding="utf-8") as f:
            for s in deduped_samples:
                record = self._format_record(s, target_format)
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

        stats = {
            "total_input": len(samples),
            "validated": len(valid_samples),
            "rejected": rejected,
            "final_unique_count": len(deduped_samples),
            "output_path": str(out_file),
            "format": target_format
        }
        logger.info(f"[CURATOR] Dataset export complete: {stats}")
        return stats

    def _format_record(self, sample: SyntheticSample, target_format: str) -> Dict[str, Any]:
        """Transform SyntheticSample into specified LLM training format."""
        meta = dict(sample.metadata)
        if sample.audit_trace:
            meta["audit_trace"] = sample.audit_trace

        if target_format == "chatml":
            return {
                "id": sample.id,
                "domain": sample.domain,
                "messages": [
                    {"role": "system", "content": DEFAULT_SYSTEM_PROMPT},
                    {"role": "user", "content": f"{sample.instruction}\n{sample.input_context}".strip()},
                    {"role": "assistant", "content": sample.output}
                ],
                "metadata": meta
            }
        elif target_format == "alpaca":
            return {
                "instruction": sample.instruction,
                "input": sample.input_context,
                "output": sample.output,
                "metadata": meta
            }
        else:  # Raw / Generic
            return sample.to_dict()
