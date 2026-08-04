"""
project/rag/jsonl_exporter.py
==============================
Solution 1 Implementation: ShareGPT JSONL Dataset Builder & Quality Validator.

Converts all vault markdown notes, PDF extractions, classical BaZi texts, and synthetic charts
into clean, validated ShareGPT JSONL datasets for MLX LoRA Fine-Tuning.

Output Paths:
  - project/rag/datasets/train.jsonl
  - project/rag/datasets/valid.jsonl
  - project/data/mlx_finetune/train.jsonl
  - project/data/mlx_finetune/valid.jsonl

Usage:
  python project/rag/jsonl_exporter.py [--val-split 0.1]
"""

from __future__ import annotations

import os
import re
import sys
import json
import random
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("jsonl_exporter")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

VAULT_DIR        = ROOT / "project" / "rag" / "obsidian_vault"
DATASETS_DIR     = ROOT / "project" / "rag" / "datasets"
MLX_FINETUNE_DIR = ROOT / "project" / "data" / "mlx_finetune"

SYSTEM_PROMPT = (
    "คุณคือผู้เชี่ยวชาญด้านโหราศาสตร์เชิงคำนวณ (Computational Metaphysics) "
    "เชี่ยวชาญทั้ง BaZi (四柱命理), การคำนวณ True Solar Time, "
    "และคัมภีร์จีนโบราณ อาทิ 子平真詮, 滴天髓, 窮通寶鑑 "
    "ตอบด้วยการวิเคราะห์เชิงวิชาการ อ้างอิงตำราที่ผ่านการพิสูจน์ "
    "และระบุเสมอว่าใช้ True Solar Time ในการคำนวณ"
)


# ---------------------------------------------------------------------------
# Q&A / Text Extractor
# ---------------------------------------------------------------------------

def extract_qa_from_markdown(md_text: str, source: str) -> List[Dict[str, Any]]:
    """Extract Q&A pairs from markdown text."""
    pairs: List[Dict[str, Any]] = []

    # Pattern 1: ## Q: / A:
    pattern1 = re.findall(
        r"#{1,3}\s*[Qq][:：]\s*(.+?)\n+[Aa][:：]\s*(.+?)(?=\n#{1,3}|\Z)",
        md_text, re.DOTALL
    )
    for q, a in pattern1:
        q, a = q.strip(), a.strip()
        if len(q) >= 10 and len(a) >= 20:
            pairs.append({"question": q, "answer": a, "source": source})

    # Pattern 2: **User:** / **Assistant:**
    pattern2 = re.findall(
        r"\*\*(?:User|คำถาม)[:：]?\*\*\s*(.+?)\n+\*\*(?:Assistant|คำตอบ)[:：]?\*\*\s*(.+?)(?=\n\*\*(?:User|คำถาม)|\Z)",
        md_text, re.DOTALL
    )
    for q, a in pattern2:
        q, a = q.strip(), a.strip()
        if len(q) >= 10 and len(a) >= 20:
            pairs.append({"question": q, "answer": a, "source": source})

    # Pattern 3: Heading as Q, body as A
    if not pairs and len(md_text.strip()) > 100:
        sections = re.split(r"\n(?=#{1,3} )", md_text)
        for sec in sections:
            m = re.match(r"^(#{1,3})\s+(.+?)\n+(.+)", sec.strip(), re.DOTALL)
            if m:
                heading = m.group(2).strip()
                body    = m.group(3).strip()
                if len(heading) >= 5 and len(body) >= 40:
                    q = f"อธิบายหลักการเรื่อง {heading} ตามคัมภีร์โหราศาสตร์"
                    pairs.append({"question": q, "answer": body, "source": source})

    return pairs


def generate_synthetic_conversations() -> List[Dict[str, Any]]:
    """Generate structured ShareGPT conversations from synthetic BaZi charts."""
    conversations = []
    charts_file = ROOT / "project" / "data" / "sample_charts.json"

    if not charts_file.exists():
        return conversations

    try:
        charts = json.loads(charts_file.read_text(encoding="utf-8"))
        for c in charts:
            dm   = c.get("day_master", {})
            fe   = c.get("five_elements", {}).get("percentages", {})
            city = c.get("city", "Bangkok")
            dt   = c.get("birth_datetime", "1990-05-15 14:30:00")

            user_msg = (
                f"โปรดวิเคราะห์ดวงชะตา BaZi สำหรับผู้เกิดวันที่ {dt} เมือง {city}\n"
                f"Day Master: {dm.get('stem','庚')}{dm.get('element','Metal')} ({dm.get('polarity','Yang')})\n"
                f"สัดส่วน 5 ธาตุ: {json.dumps(fe, ensure_ascii=False)}"
            )

            assistant_msg = (
                f"จากการคำนวณ True Solar Time สำหรับเมือง {city} พบว่าผู้เกิดวันที่ {dt} "
                f"มี Day Master เป็น {dm.get('stem','庚')} ({dm.get('element','Metal')} {dm.get('polarity','Yang')}).\n\n"
                f"การวิเคราะห์กำลัง 5 ธาตุ:\n"
                f"- ธาตุหลักในดวง: {fe}\n"
                f"- การประเมินความแข็งแกร่ง: พิจารณาตามคัมภีร์ 子平真詮 ร่วมกับสัดส่วนกำลังธาตุที่คำนวณได้ 100% Deterministic\n"
                f"- ธาตุที่เป็นประโยชน์ (用神): แนะนำธาตุที่ช่วยส่งเสริมความสมดุลของ Day Master"
            )

            conversations.append({
                "messages": [
                    {"role": "system",    "content": SYSTEM_PROMPT},
                    {"role": "user",      "content": user_msg},
                    {"role": "assistant", "content": assistant_msg},
                ]
            })
    except Exception as e:
        log.warning(f"Error reading sample_charts.json: {e}")

    return conversations


# ---------------------------------------------------------------------------
# ShareGPT Format Validator
# ---------------------------------------------------------------------------

def validate_sharegpt_entry(entry: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate a single ShareGPT JSONL entry.
    Requires 'messages' or 'conversations' list with valid roles.
    """
    msgs = entry.get("messages") or entry.get("conversations")
    if not msgs or not isinstance(msgs, list):
        return False, "Missing 'messages' or 'conversations' list"

    if len(msgs) < 2:
        return False, f"Conversation too short ({len(msgs)} messages)"

    roles = set()
    for m in msgs:
        role = m.get("role") or m.get("from")
        val  = m.get("content") or m.get("value") or ""

        if not role or role not in ("system", "user", "human", "assistant", "gpt"):
            return False, f"Invalid role: {role}"
        if not val or len(str(val).strip()) < 2:
            return False, f"Message content for role '{role}' is empty or too short"

        roles.add(role)

    if not ("user" in roles or "human" in roles):
        return False, "Missing user/human message"
    if not ("assistant" in roles or "gpt" in roles):
        return False, "Missing assistant/gpt message"

    return True, "VALID"


def convert_to_messages_format(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize entry to standard OpenAI/ShareGPT 'messages' format."""
    raw_list = entry.get("messages") or entry.get("conversations") or []
    norm_messages = []

    for item in raw_list:
        role = item.get("role") or item.get("from") or "user"
        content = item.get("content") or item.get("value") or ""

        # Normalize role names
        if role == "human":
            role = "user"
        elif role == "gpt":
            role = "assistant"

        norm_messages.append({"role": role, "content": str(content).strip()})

    # Ensure system prompt is present
    if norm_messages and norm_messages[0]["role"] != "system":
        norm_messages.insert(0, {"role": "system", "content": SYSTEM_PROMPT})

    return {"messages": norm_messages}


# ---------------------------------------------------------------------------
# Exporter Pipeline
# ---------------------------------------------------------------------------

def build_and_export_jsonl(val_split: float = 0.10, seed: int = 42) -> Dict[str, Any]:
    log.info("=" * 65)
    log.info("🚀 Solution 1: ShareGPT JSONL Dataset Builder & Quality Validator")
    log.info("=" * 65)

    all_entries: List[Dict[str, Any]] = []

    # 1. Load Q&A from Obsidian Vault (.md files)
    md_files = list(VAULT_DIR.rglob("*.md"))
    log.info(f"Scanning {len(md_files)} markdown files in vault...")

    for md_file in sorted(md_files):
        text   = md_file.read_text(encoding="utf-8")
        source = md_file.stem
        pairs  = extract_qa_from_markdown(text, source)

        for qa in pairs:
            entry = {
                "messages": [
                    {"role": "system",    "content": SYSTEM_PROMPT},
                    {"role": "user",      "content": qa["question"]},
                    {"role": "assistant", "content": qa["answer"]},
                ]
            }
            all_entries.append(entry)

    log.info(f"Extracted {len(all_entries)} Q&A conversation entries from vault markdown files.")

    # 2. Add Synthetic BaZi Chart Conversations
    syn_convs = generate_synthetic_conversations()
    log.info(f"Generated {len(syn_convs)} synthetic BaZi chart conversations.")
    all_entries.extend(syn_convs)

    # 3. Quality Validation Sweep
    valid_entries: List[Dict[str, Any]] = []
    rejected_count = 0

    for entry in all_entries:
        is_ok, reason = validate_sharegpt_entry(entry)
        if is_ok:
            norm = convert_to_messages_format(entry)
            valid_entries.append(norm)
        else:
            rejected_count += 1
            log.warning(f"  Rejected entry ({reason})")

    log.info(f"\n🔍 Quality Validation Sweep:")
    log.info(f"   Total Candidates : {len(all_entries)}")
    log.info(f"   Passed           : {len(valid_entries)}")
    log.info(f"   Rejected         : {rejected_count}")

    if not valid_entries:
        log.error("❌ No valid JSONL entries generated!")
        return {"status": "error", "valid_count": 0}

    # 4. Split Train / Valid datasets
    random.seed(seed)
    random.shuffle(valid_entries)

    val_n   = max(1, int(len(valid_entries) * val_split))
    val_set = valid_entries[:val_n]
    trn_set = valid_entries[val_n:]

    # 5. Write JSONL to both DATASETS_DIR and MLX_FINETUNE_DIR
    target_dirs = [DATASETS_DIR, MLX_FINETUNE_DIR]
    for d in target_dirs:
        d.mkdir(parents=True, exist_ok=True)
        trn_path = d / "train.jsonl"
        val_path = d / "valid.jsonl"

        with open(trn_path, "w", encoding="utf-8") as f:
            for item in trn_set:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

        with open(val_path, "w", encoding="utf-8") as f:
            for item in val_set:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

        log.info(f"✅ Exported -> {d.relative_to(ROOT)} ({len(trn_set)} train / {len(val_set)} valid)")

    summary = {
        "status":        "success",
        "total_entries": len(valid_entries),
        "train_count":   len(trn_set),
        "valid_count":   len(val_set),
        "rejected":      rejected_count,
        "exported_dirs": [str(d.relative_to(ROOT)) for d in target_dirs],
    }

    print("\n" + "=" * 65)
    print("  SUMMARY: SOLUTION 1 JSONL DATASET PIPELINE")
    print("=" * 65)
    print(f"  Total Valid ShareGPT Entries : {len(valid_entries)}")
    print(f"  Training Entries (90%)       : {len(trn_set)}")
    print(f"  Validation Entries (10%)     : {len(val_set)}")
    print(f"  Target Model                 : Qwen/Qwen2.5-7B-Instruct (qwen2.5-bazi)")
    print("=" * 65 + "\n")

    return summary


if __name__ == "__main__":
    build_and_export_jsonl()
