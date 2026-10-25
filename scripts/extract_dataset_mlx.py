#!/usr/bin/env python3
"""
scripts/extract_dataset_mlx.py
================================
Dataset extraction & preparation script for fine-tuning Qwen2.5-7B
with the MLX Framework on macOS (Apple Silicon).

Pipeline
--------
1. Parse raw classical BaZi texts (project/data/raw_texts/)
2. Generate instruction-response pairs from structured charts
3. Format into MLX-compatible JSONL (ShareGPT / Alpaca format)
4. Split into train / valid sets (90/10)
5. Output to project/data/mlx_finetune/

Requirements (macOS)
---------------------
    pip install mlx mlx-lm datasets transformers

Usage
-----
    python scripts/extract_dataset_mlx.py \
        --source  project/data/raw_texts/ \
        --charts  project/data/sample_charts.json \
        --output  project/data/mlx_finetune/ \
        --model   Qwen/Qwen2.5-7B-Instruct \
        --max-tokens 2048 \
        --val-split 0.10
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("mlx-dataset")


# ---------------------------------------------------------------------------
# Template builders
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are a master computational metaphysics consultant specialising in "
    "BaZi (Four Pillars of Destiny). Provide precise, citation-backed analysis "
    "with True Solar Time adjustment. Respond in structured JSON when requested."
)


def _chart_to_instruction(chart: dict[str, Any]) -> str:
    dm = chart.get("day_master", {})
    tst = chart.get("solar_time_info", {})
    return (
        f"Analyse the BaZi chart for birth on {tst.get('input_datetime', 'unknown')} "
        f"at longitude {tst.get('longitude', 0)}°, UTC{tst.get('utc_offset_hours', 0):+.1f}. "
        f"Day Master is {dm.get('stem', '?')} ({dm.get('element', '?')}, {dm.get('polarity', '?')}). "
        f"Provide: Day Master strength assessment, favourable elements, "
        f"career/relationship insights, and life phase overview."
    )


def _chart_to_response(chart: dict[str, Any]) -> str:
    """Synthesise a structured response from chart data (used as training target)."""
    fe = chart.get("five_elements", {})
    dm = chart.get("day_master", {})
    pcts = fe.get("percentages", {})
    dom  = fe.get("dominant_element", "")
    weak = fe.get("weakest_element", "")

    pillars_str = ""
    for label, p in chart.get("pillars", {}).items():
        if p is None:
            continue
        s = p.get("stem", {})
        b = p.get("branch", {})
        pillars_str += f"  {label}: {s.get('char','?')}{b.get('char','?')} ({s.get('element','?')}/{b.get('element','?')})\n"

    response = {
        "day_master_assessment": (
            f"{dm.get('stem','?')} is a {dm.get('polarity','?')} {dm.get('element','?')} stem. "
            f"Overall chart balance: Dominant={dom} ({pcts.get(dom, 0):.1f}%), "
            f"Weakest={weak} ({pcts.get(weak, 0):.1f}%)."
        ),
        "five_elements_breakdown": pcts,
        "pillars_summary": pillars_str.strip(),
        "favourable_elements": [
            e for e in ["Wood", "Fire", "Earth", "Metal", "Water"]
            if pcts.get(e, 0) < 20.0
        ],
        "note": "True Solar Time adjusted. Consult classical texts for detailed interpretation.",
    }
    return json.dumps(response, ensure_ascii=False, indent=2)


def build_sharegpt_entry(chart: dict[str, Any]) -> dict[str, Any]:
    """Create a ShareGPT-format entry for MLX fine-tuning."""
    return {
        "conversations": [
            {"role": "system",    "value": SYSTEM_PROMPT},
            {"role": "human",     "value": _chart_to_instruction(chart)},
            {"role": "assistant", "value": _chart_to_response(chart)},
        ]
    }


# ---------------------------------------------------------------------------
# Dataset generation from raw charts
# ---------------------------------------------------------------------------

def load_charts(charts_path: Path) -> list[dict[str, Any]]:
    if not charts_path.exists():
        log.warning(f"Charts file not found: {charts_path}. Generating synthetic samples.")
        return _generate_synthetic_charts(n=200)
    with open(charts_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    log.info(f"Loaded {len(data)} charts from {charts_path}")
    return data


def _generate_synthetic_charts(n: int = 200) -> list[dict[str, Any]]:
    """
    Generate synthetic BaZi charts using the engine for demonstration.
    Replace with real anonymised chart corpus in production.
    """
    try:
        # Append project root to path
        root = Path(__file__).resolve().parents[1]
        sys.path.insert(0, str(root))
        from project.core.bazi_engine import BaZiEngine
        engine = BaZiEngine()
    except ImportError:
        log.error("Cannot import BaZiEngine; ensure project is on PYTHONPATH")
        return []

    charts = []
    random.seed(42)
    base_year  = 1960
    for i in range(n):
        year   = base_year + random.randint(0, 60)
        month  = random.randint(1, 12)
        day    = random.randint(1, 28)
        hour   = random.randint(0, 23)
        minute = random.randint(0, 59)
        lng    = random.uniform(98.0, 106.0)  # Thailand/SEA range
        utc    = 7.0
        try:
            dt  = datetime(year, month, day, hour, minute)
            res = engine.calculate(dt=dt, longitude=lng, utc_offset_hours=utc)
            charts.append(res)
        except Exception as e:
            log.debug(f"Skipping chart {i}: {e}")
    log.info(f"Generated {len(charts)} synthetic charts")
    return charts


def extract_from_texts(texts_dir: Path) -> list[dict[str, Any]]:
    """
    Parse raw .txt classical text files and create Q&A pairs.
    Each paragraph becomes an instruction-following entry.
    """
    entries = []
    if not texts_dir.exists():
        log.warning(f"Raw texts directory not found: {texts_dir}")
        return entries

    for txt_file in sorted(texts_dir.glob("*.txt")):
        source_name = txt_file.stem
        text = txt_file.read_text(encoding="utf-8")
        paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 50]
        for para in paragraphs:
            entries.append({
                "conversations": [
                    {"role": "system", "value": SYSTEM_PROMPT},
                    {
                        "role": "human",
                        "value": (
                            f"Explain the following passage from {source_name} "
                            f"in the context of BaZi analysis:\n\n{para}"
                        ),
                    },
                    {
                        "role": "assistant",
                        "value": (
                            f"This passage from {source_name} discusses: "
                            f"{para[:200]}… "
                            f"[Full analysis requires classical commentary — "
                            f"this is a placeholder for human-curated annotations.]"
                        ),
                    },
                ]
            })
    log.info(f"Extracted {len(entries)} text passage entries")
    return entries


def distill_from_rag(query: str, top_k: int = 5) -> list[Any]:
    """
    Simulate FAISS RAG retrieval of classical treatise passages
    and formatting them into fine-tuning Q&A pairs.
    """
    from project.schemas.dataset_schema_v1 import FineTuningQAPair, BenchmarkDomain
    
    # In a real scenario, this would query a FAISS vector store.
    # Here we mock the returned passages.
    passages = [
        "The Day Master represents the core self, while the Month Branch determines the primary structure.",
        "When Wood is favorable, spring brings prosperity; when unfavorable, avoid eastern travels."
    ][:top_k]
    
    qa_pairs = []
    for i, passage in enumerate(passages):
        pair = FineTuningQAPair(
            id=f"RAG-DISTILL-{i:04d}",
            domain=BenchmarkDomain.CAREER,
            system_prompt="You are a Metaphysics Master. Answer queries based on classical treatises.",
            user_query=query,
            context_chart_data={"passage_reference": passage},
            canonical_citations=["《滴天髓》"],
            ground_truth_synthesis=f"According to the classical texts: {passage}",
            reasoning_steps=["Retrieve text", "Synthesize answer"],
            actionable_recommendations=["Consider the classical advice carefully."],
            favorable_elements=["Wood"],
            unfavorable_elements=["Metal"],
            language="en"
        )
        qa_pairs.append(pair)
        
    log.info(f"Distilled {len(qa_pairs)} Q&A pairs from RAG for query: '{query}'")
    return qa_pairs


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="MLX Fine-tune Dataset Extractor")
    parser.add_argument("--source",     default="project/data/raw_texts/",    type=Path)
    parser.add_argument("--charts",     default="project/data/sample_charts.json", type=Path)
    parser.add_argument("--output",     default="project/data/mlx_finetune/", type=Path)
    parser.add_argument("--model",      default="Qwen/Qwen2.5-7B-Instruct")
    parser.add_argument("--max-tokens", default=2048, type=int)
    parser.add_argument("--val-split",  default=0.10, type=float)
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)

    # 1. Load / generate chart-based entries
    charts   = load_charts(args.charts)
    chart_entries = [build_sharegpt_entry(c) for c in charts]

    # 2. Extract classical text entries
    text_entries = extract_from_texts(args.source)

    # 3. Combine & shuffle
    all_entries = chart_entries + text_entries
    random.seed(0)
    random.shuffle(all_entries)
    log.info(f"Total entries: {len(all_entries)}")

    # 4. Split
    val_n   = max(1, int(len(all_entries) * args.val_split))
    val_set = all_entries[:val_n]
    trn_set = all_entries[val_n:]
    log.info(f"Train: {len(trn_set)} | Valid: {len(val_set)}")

    # 5. Write JSONL
    for name, dataset in [("train", trn_set), ("valid", val_set)]:
        out_path = args.output / f"{name}.jsonl"
        with open(out_path, "w", encoding="utf-8") as f:
            f.writelines(json.dumps(entry, ensure_ascii=False) + "\n" for entry in dataset)
        log.info(f"Saved {name}: {out_path}")

    # 6. Write MLX fine-tune config
    config = {
        "model":            args.model,
        "train_file":       str(args.output / "train.jsonl"),
        "valid_file":       str(args.output / "valid.jsonl"),
        "max_seq_length":   args.max_tokens,
        "num_iters":        1000,
        "learning_rate":    2e-5,
        "lora_layers":      8,
        "batch_size":       4,
        "val_batches":      25,
        "save_every":       100,
        "adapter_path":     "project/models/qwen2.5-bazi-adapter",
    }
    config_path = args.output / "mlx_config.json"
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    log.info(f"MLX config: {config_path}")

    print("\n✅ Dataset extraction complete!")
    print(f"   Train : {args.output / 'train.jsonl'}")
    print(f"   Valid : {args.output / 'valid.jsonl'}")
    print(f"   Config: {config_path}")
    print("\nNext step — fine-tune on macOS:")
    print(
        f"  mlx_lm.lora \\\n"
        f"    --model {args.model} \\\n"
        f"    --train \\\n"
        f"    --data {args.output} \\\n"
        f"    --iters 1000 \\\n"
        f"    --batch-size 4 \\\n"
        f"    --lora-layers 8 \\\n"
        f"    --adapter-path project/models/qwen2.5-bazi-adapter"
    )
    print("\nAfter training — fuse & convert to GGUF:")
    print(
        "  mlx_lm.fuse \\\n"
        "    --model Qwen/Qwen2.5-7B-Instruct \\\n"
        "    --adapter-path project/models/qwen2.5-bazi-adapter \\\n"
        "    --save-path project/models/qwen2.5-bazi-fused\n"
        "  # Then convert with llama.cpp convert_hf_to_gguf.py"
    )


if __name__ == "__main__":
    main()
