"""
project/core/source_summarizer.py
===================================
Knowledge Source Summary Engine.

Reads knowledge_catalog.json and the FAISS vector store to generate
per-source summaries, coverage reports, and fine-tune ready JSONL fragments.

Usage
-----
    # Generate summary report
    python project/core/source_summarizer.py --report

    # Export gray-zone question list (for admin panel)
    python project/core/source_summarizer.py --export-grayzone

    # Build fine-tune JSONL from answered gray-zone items
    python project/core/source_summarizer.py --build-finetune
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("source_summarizer")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

CATALOG_PATH       = ROOT / "project" / "data" / "knowledge_catalog.json"
GRAYZONE_DB_PATH   = ROOT / "project" / "data" / "grayzone_answers.json"
FINETUNE_OUT_PATH  = ROOT / "project" / "rag" / "datasets"
SUMMARY_OUT_PATH   = ROOT / "project" / "data" / "source_summaries.json"

SYSTEM_PROMPT_MAP = {
    "chinese_metaphysics": (
        "คุณคือผู้เชี่ยวชาญด้านอภิปรัชญาเชิงคำนวณ (Computational Metaphysics) "
        "เชี่ยวชาญทั้ง BaZi (四柱命理), ปรัชญาจีน, คัมภีร์โบราณ "
        "อาทิ 子平真詮, 滴天髓, 窮通寶鑑, 淵海子平, 三命通會 "
        "ตอบด้วยการวิเคราะห์เชิงวิชาการ อ้างอิงตำราที่ผ่านการพิสูจน์ "
        "และระบุเสมอว่าใช้ True Solar Time ในการคำนวณ"
    ),
    "vedic_astrology": (
        "คุณคือผู้เชี่ยวชาญด้านโหราศาสตร์เวท (Jyotish Shastra) "
        "เชี่ยวชาญใน BPHS, Jaimini Sutras, Phaladeepika, Saravali, Brihat Jataka, Uttara Kalamrita "
        "ตอบด้วยภาษาวิชาการ อ้างอิงบทและข้อของตำราต้นฉบับ "
        "พร้อมอธิบายในบริบทของระบบ Parashari และ Jaimini"
    ),
    "thai_astrology": (
        "คุณคือผู้เชี่ยวชาญด้านโหราศาสตร์ไทยและตำราโบราณ "
        "เชี่ยวชาญในคัมภีร์สุริยยาตร์, มานัต, ดวงพิชัยสงคราม, "
        "โหราศาสตร์ไทยมาตรฐาน, โหงวเฮ้ง, และตำราไสยเวทท้องถิ่น "
        "ตอบด้วยความเคารพต่อวัฒนธรรม อธิบายทั้งเชิงประวัติศาสตร์และการประยุกต์ใช้"
    ),
    "astrophysics_math": (
        "คุณคือผู้เชี่ยวชาญด้านดาราศาสตร์ฟิสิกส์เชิงคำนวณ "
        "เชี่ยวชาญใน Swiss Ephemeris, JPL DE440, ICRF3, IAU 2006, IERS Bulletin, "
        "Time Series Analysis และ NARDL Model "
        "ตอบด้วยความถูกต้องทางวิทยาศาสตร์ แสดงสูตรคณิตศาสตร์และ Margin of Error ±σ"
    ),
    "western_scientific": (
        "คุณคือผู้เชี่ยวชาญด้านทฤษฎีโหราศาสตร์ตะวันตกและการวิพากษ์เชิงวิทยาศาสตร์ "
        "เชี่ยวชาญใน Hellenistic Astrology, Gauquelin Mars Effect, Genovese (2014), "
        "และ Multiple Hypotheses Testing "
        "ตอบด้วยมุมมองที่สมดุลระหว่างประเพณีกับหลักฐานเชิงประจักษ์"
    ),
}

DEFAULT_SYSTEM_PROMPT = (
    "คุณคือผู้เชี่ยวชาญด้านโหราศาสตร์เชิงคำนวณ (Computational Metaphysics) "
    "เชี่ยวชาญทั้ง BaZi, Vedic Astrology, โหราศาสตร์ไทย และดาราศาสตร์ฟิสิกส์ "
    "ตอบด้วยการวิเคราะห์เชิงวิชาการ อ้างอิงตำราต้นฉบับ"
)


# ---------------------------------------------------------------------------
# Catalog Loader
# ---------------------------------------------------------------------------

def load_catalog() -> dict[str, Any]:
    """Load the knowledge catalog JSON."""
    if not CATALOG_PATH.exists():
        log.error(f"Catalog not found: {CATALOG_PATH}")
        return {}
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def load_grayzone_answers() -> dict[str, Any]:
    """Load answered gray-zone Q&A database."""
    if not GRAYZONE_DB_PATH.exists():
        return {"answers": {}}
    return json.loads(GRAYZONE_DB_PATH.read_text(encoding="utf-8"))


def save_grayzone_answers(data: dict[str, Any]) -> None:
    """Save gray-zone answers back to disk."""
    GRAYZONE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    GRAYZONE_DB_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Source Iterator
# ---------------------------------------------------------------------------

def iter_all_sources(catalog: dict[str, Any]):
    """Iterate over every source in the catalog, yielding (category_key, source_dict)."""
    for cat_key, cat_val in catalog.get("categories", {}).items():
        # Direct sources list
        if "sources" in cat_val:
            for src in cat_val["sources"]:
                yield cat_key, src
        # Subcategories
        if "subcategories" in cat_val:
            for _sub_key, sub_val in cat_val["subcategories"].items():
                if "sources" in sub_val:
                    for src in sub_val["sources"]:
                        yield cat_key, src


# ---------------------------------------------------------------------------
# Summary Report Generator
# ---------------------------------------------------------------------------

def generate_summary_report(catalog: dict[str, Any]) -> dict[str, Any]:
    """
    Build a per-source summary report showing:
    - Coverage status
    - Gray-zone count
    - Fine-tune readiness
    """
    report: dict[str, Any] = {
        "report_version": "2.0.0",
        "generated_at": __import__("datetime").datetime.now().isoformat(),
        "overall_stats": {},
        "by_category": {},
        "gray_zone_summary": [],
        "action_required": [],
    }

    total_sources = 0
    total_chunks = 0
    gray_zone_questions_total = 0
    finetune_ready_total = 0

    for cat_key, src in iter_all_sources(catalog):
        total_sources += 1
        total_chunks += src.get("vector_chunks", 0)

        if src.get("finetune_ready"):
            finetune_ready_total += 1

        gz_qs = src.get("gray_zone_questions", [])
        if gz_qs:
            gray_zone_questions_total += len(gz_qs)
            report["gray_zone_summary"].append({
                "id":          src["id"],
                "title":       src["title_th"],
                "category":    cat_key,
                "coverage_pct": src.get("coverage_pct", 0),
                "question_count": len(gz_qs),
                "questions":   gz_qs,
            })

        # Action required
        if src.get("coverage_status") in ("missing", "partial") and src.get("gray_zone"):
            report["action_required"].append({
                "id":     src["id"],
                "title":  src["title_th"],
                "status": src.get("coverage_status"),
                "coverage_pct": src.get("coverage_pct", 0),
                "unanswered_questions": len(gz_qs),
            })

        # Per-category
        if cat_key not in report["by_category"]:
            report["by_category"][cat_key] = {
                "sources": 0,
                "ingested_complete": 0,
                "partial": 0,
                "missing": 0,
                "total_chunks": 0,
                "gray_zone_questions": 0,
            }
        r = report["by_category"][cat_key]
        r["sources"] += 1
        r["total_chunks"] += src.get("vector_chunks", 0)
        r["gray_zone_questions"] += len(gz_qs)
        status = src.get("coverage_status", "missing")
        if status in ("ingested", "integrated"):
            r["ingested_complete"] += 1
        elif status == "partial":
            r["partial"] += 1
        else:
            r["missing"] += 1

    report["overall_stats"] = {
        "total_sources":            total_sources,
        "total_vector_chunks":      total_chunks,
        "finetune_ready":           finetune_ready_total,
        "gray_zone_sources":        len(report["gray_zone_summary"]),
        "gray_zone_questions_total": gray_zone_questions_total,
        "completion_pct":           round(finetune_ready_total / max(total_sources, 1) * 100, 1),
    }

    return report


# ---------------------------------------------------------------------------
# Gray-Zone Q&A → Fine-Tune JSONL
# ---------------------------------------------------------------------------

def build_finetune_from_grayzone(
    catalog: dict[str, Any],
    answers_db: dict[str, Any],
    output_dir: Path = FINETUNE_OUT_PATH,
) -> dict[str, Any]:
    """
    Build a fine-tune JSONL from answered gray-zone questions.
    Only includes questions that have been answered in grayzone_answers.json.
    """
    answers = answers_db.get("answers", {})
    entries: list[dict[str, Any]] = []
    skipped = 0
    included = 0

    for cat_key, src in iter_all_sources(catalog):
        system_prompt = SYSTEM_PROMPT_MAP.get(cat_key, DEFAULT_SYSTEM_PROMPT)
        gz_qs = src.get("gray_zone_questions", [])
        src_id = src["id"]

        for q in gz_qs:
            answer_key = f"{src_id}::{q}"
            if answer_key in answers:
                answer_data = answers[answer_key]
                answer_text = (
                    answer_data.get("answer", "")
                    if isinstance(answer_data, dict)
                    else str(answer_data)
                )
                if answer_text.strip():
                    entries.append({
                        "messages": [
                            {"role": "system",    "content": system_prompt},
                            {"role": "user",      "content": q},
                            {"role": "assistant", "content": answer_text.strip()},
                        ],
                        "_meta": {
                            "source_id":    src_id,
                            "source_title": src.get("title_th", ""),
                            "category":     cat_key,
                            "is_grayzone":  True,
                        }
                    })
                    included += 1
            else:
                skipped += 1

    if entries:
        output_dir.mkdir(parents=True, exist_ok=True)
        gz_path = output_dir / "grayzone_finetune.jsonl"
        gz_meta_path = output_dir / "grayzone_finetune_with_metadata.jsonl"
        with open(gz_path, "w", encoding="utf-8") as f:
            for e in entries:
                f.write(json.dumps({"messages": e["messages"]}, ensure_ascii=False) + "\n")
        with open(gz_meta_path, "w", encoding="utf-8") as f_meta:
            for e in entries:
                f_meta.write(json.dumps(e, ensure_ascii=False) + "\n")
        log.info(f"✅ Exported {included} gray-zone Q&A entries → {gz_path}")

        # Also sync to Supabase DB if configured
        try:
            from project.core.supabase_db import SupabaseDB
            sdb = SupabaseDB()
            if sdb.is_configured():
                db_records = []
                for entry in entries:
                    msgs = entry["messages"]
                    user_q = next((m["content"] for m in msgs if m["role"] == "user"), "")
                    assistant_a = next((m["content"] for m in msgs if m["role"] == "assistant"), "")
                    src_info = entry.get("_meta", {}).get("source_id", "GrayZone")
                    if user_q and assistant_a:
                        db_records.append({
                            "question": user_q,
                            "answer": assistant_a,
                            "source_book": f"GrayZone:{src_info}",
                            "is_verified": True,
                        })
                if db_records:
                    sdb.upsert("qa_knowledge_base", db_records)
                    log.info(f"☁️ Synced {len(db_records)} Gray-Zone records to Supabase DB `qa_knowledge_base`")
        except Exception as e:
            log.warning(f"⚠️ Supabase sync note: {e}")
    else:
        log.warning("⚠️  No answered gray-zone questions found. Use admin panel to add answers.")

    return {
        "status":   "success" if entries else "empty",
        "included": included,
        "skipped":  skipped,
        "output":   str(output_dir / "grayzone_finetune.jsonl") if entries else None,
        "metadata_output": str(output_dir / "grayzone_finetune_with_metadata.jsonl") if entries else None,
    }


# ---------------------------------------------------------------------------
# Merge All Fine-Tune Datasets
# ---------------------------------------------------------------------------

def merge_all_finetune_datasets(output_dir: Path = FINETUNE_OUT_PATH) -> dict[str, Any]:
    """
    Merge train.jsonl + grayzone_finetune.jsonl into combined_train.jsonl.
    This is the dataset ready for External AI fine-tuning.
    """
    import random
    combined: list[dict] = []

    for fname in ["train.jsonl", "grayzone_finetune.jsonl"]:
        p = output_dir / fname
        if p.exists():
            with open(p, encoding="utf-8") as f:
                lines = [json.loads(l) for l in f if l.strip()]
            combined.extend(lines)
            log.info(f"  Loaded {len(lines)} entries from {fname}")

    if not combined:
        log.warning("No entries to merge.")
        return {"status": "empty", "total": 0}

    random.seed(42)
    random.shuffle(combined)

    out_path = output_dir / "combined_train.jsonl"
    with open(out_path, "w", encoding="utf-8") as f:
        f.writelines(json.dumps(entry, ensure_ascii=False) + "\n" for entry in combined)

    log.info(f"✅ Merged {len(combined)} entries → {out_path}")
    return {
        "status": "success",
        "total":  len(combined),
        "output": str(out_path),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Knowledge Source Summarizer")
    parser.add_argument("--report",          action="store_true", help="Generate summary report")
    parser.add_argument("--export-grayzone", action="store_true", help="Export gray-zone question list")
    parser.add_argument("--build-finetune",  action="store_true", help="Build fine-tune JSONL from answered gray-zone")
    parser.add_argument("--merge",           action="store_true", help="Merge all fine-tune datasets")
    args = parser.parse_args()

    catalog = load_catalog()
    if not catalog:
        log.error("Failed to load catalog. Exiting.")
        sys.exit(1)

    if args.report:
        report = generate_summary_report(catalog)
        SUMMARY_OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        SUMMARY_OUT_PATH.write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        log.info(f"📊 Summary Report → {SUMMARY_OUT_PATH}")
        stats = report["overall_stats"]
        print("\n" + "=" * 65)
        print("  KNOWLEDGE SOURCE CATALOG SUMMARY")
        print("=" * 65)
        print(f"  Total Sources         : {stats['total_sources']}")
        print(f"  Total Vector Chunks   : {stats['total_vector_chunks']}")
        print(f"  Fine-Tune Ready       : {stats['finetune_ready']}")
        print(f"  Gray-Zone Sources     : {stats['gray_zone_sources']}")
        print(f"  Gray-Zone Questions   : {stats['gray_zone_questions_total']}")
        print(f"  Completion            : {stats['completion_pct']}%")
        print("=" * 65)

    if args.export_grayzone:
        report = generate_summary_report(catalog)
        gz_list_path = ROOT / "project" / "data" / "grayzone_questions.json"
        gz_list_path.write_text(
            json.dumps(report["gray_zone_summary"], ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        log.info(f"📋 Gray-Zone Question List → {gz_list_path}")

    if args.build_finetune:
        answers_db = load_grayzone_answers()
        result = build_finetune_from_grayzone(catalog, answers_db)
        print(f"\n  Fine-Tune Build Result: {json.dumps(result, ensure_ascii=False, indent=2)}")

    if args.merge:
        result = merge_all_finetune_datasets()
        print(f"\n  Merge Result: {json.dumps(result, ensure_ascii=False, indent=2)}")

    if not any([args.report, args.export_grayzone, args.build_finetune, args.merge]):
        parser.print_help()


if __name__ == "__main__":
    main()
