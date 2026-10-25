#!/usr/bin/env python3
"""
scripts/harvest_hf_liked_datasets.py
====================================
Harvests, normalizes, cleans, and deduplicates all Hugging Face datasets
liked by the user (pphothidaen) into a canonical ChatML JSONL corpus.

Supports:
 - Parquet files (via pandas/pyarrow)
 - JSON / JSONL files
 - Alpaca schema (instruction, input, output)
 - ShareGPT schema (conversations / items)
 - QA schema (question, answer / prompt, response)
 - Raw reasoning & text streams

Usage:
    python scripts/harvest_hf_liked_datasets.py --output project/data/bazi_hf_curated_corpus.jsonl
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from project.core.config import Config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("hf_harvester")

HF_USERNAME = "pphothidaen"
SYSTEM_PROMPT = (
    "You are an expert BaZi (Four Pillars of Destiny) and Chinese Metaphysics consultant. "
    "Analyze charts accurately using Heavenly Stems, Earthly Branches, Ten Gods, Hidden Stems, "
    "Five Elements balance, and classical treatises (Di Tian Sui, San Ming Tong Hui, Yuan Hai Zi Ping)."
)


def fetch_liked_dataset_names(hf_token: str | None) -> list[str]:
    """Fetch liked dataset repo IDs from Hugging Face API."""
    url = f"https://huggingface.co/api/users/{HF_USERNAME}/likes"
    headers = {"Authorization": f"Bearer {hf_token}"} if hf_token else {}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            dataset_names = [
                item["repo"]["name"]
                for item in data
                if item.get("repo", {}).get("type") == "dataset"
            ]
            logger.info(f"[OK] Discovered {len(dataset_names)} liked datasets on Hugging Face for @{HF_USERNAME}")
            return dataset_names
    except Exception as e:
        logger.error(f"[ERROR] Failed to fetch user likes: {e}")
        return []


def normalize_row_to_chatml(row: dict) -> dict | None:
    """Normalize a diverse row format into standardized ChatML messages format."""
    messages = []

    # Format 1: Already has 'messages' list
    if "messages" in row and isinstance(row["messages"], list):
        msgs = row["messages"]
        if len(msgs) >= 2:
            return {"messages": msgs}

    # Format 2: ShareGPT 'conversations'
    convs = row.get("conversations") or row.get("items") or row.get("conversation")
    if isinstance(convs, list) and len(convs) >= 2:
        for c in convs:
            if isinstance(c, dict):
                r = c.get("from") or c.get("role", "")
                content = c.get("value") or c.get("content", "")
                if r in ("human", "user"):
                    role = "user"
                elif r in ("gpt", "assistant", "bot", "chat"):
                    role = "assistant"
                elif r in ("system",):
                    role = "system"
                else:
                    role = "user"
                if content:
                    messages.append({"role": role, "content": str(content).strip()})
        if len(messages) >= 2:
            if messages[0]["role"] != "system":
                messages.insert(0, {"role": "system", "content": SYSTEM_PROMPT})
            return {"messages": messages}

    # Format 3: Alpaca format (instruction, input, output)
    instruction = str(row.get("instruction") or row.get("query") or row.get("question") or row.get("prompt") or "").strip()
    inp = str(row.get("input") or row.get("context") or "").strip()
    output = str(row.get("output") or row.get("response") or row.get("answer") or row.get("solution") or "").strip()

    if instruction and output:
        user_msg = f"{instruction}\n\nContext:\n{inp}" if inp else instruction
        return {
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
                {"role": "assistant", "content": output},
            ]
        }

    # Format 4: Terminology mapping format (term, definition, meaning)
    term = str(row.get("term") or row.get("keyword") or "").strip()
    def_val = str(row.get("definition") or row.get("meaning") or row.get("explanation") or "").strip()
    if term and def_val:
        return {
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Explain the BaZi metaphysical concept of: {term}"},
                {"role": "assistant", "content": def_val},
            ]
        }

    # Format 5: Text block with delimiters
    raw_text = str(row.get("text") or "").strip()
    if "<|im_start|>" in raw_text:
        # Parse ChatML text directly
        parts = raw_text.split("<|im_start|>")
        for p in parts:
            if "<|im_end|>" in p:
                chunk = p.split("<|im_end|>")[0].strip()
                lines = chunk.split("\n", 1)
                if len(lines) == 2:
                    role, content = lines[0].strip(), lines[1].strip()
                    if role in ("system", "user", "assistant"):
                        messages.append({"role": role, "content": content})
        if len(messages) >= 2:
            return {"messages": messages}

    return None


def harvest_dataset_repo(repo_id: str, hf_token: str | None) -> list[dict]:
    """Download and extract rows from a single Hugging Face dataset repo."""
    logger.info(f"📥 Harvesting dataset: {repo_id}...")
    records = []
    
    # Try using datasets library first (handles Parquet, JSON, Arrow seamlessly)
    try:
        from datasets import load_dataset
        ds = load_dataset(repo_id, token=hf_token, trust_remote_code=False)
        for split in ds.keys():
            logger.info(f"   Processing split '{split}' with {len(ds[split])} rows...")
            for row in ds[split]:
                norm = normalize_row_to_chatml(dict(row))
                if norm:
                    records.append(norm)
        logger.info(f"   ✅ Successfully harvested {len(records)} normalized records from {repo_id}")
        return records
    except Exception as e:
        logger.warning(f"   ⚠️ load_dataset directly failed for {repo_id} ({e}). Attempting raw file download...")

    # Fallback: Raw file download via Hugging Face Hub API
    try:
        from huggingface_hub import HfApi, hf_hub_download
        api = HfApi(token=hf_token)
        files = api.list_repo_files(repo_id=repo_id, repo_type="dataset")
        for fname in files:
            if fname.endswith((".jsonl", ".json", ".parquet")):
                try:
                    fpath = hf_hub_download(repo_id=repo_id, filename=fname, repo_type="dataset", token=hf_token)
                    if fname.endswith(".jsonl"):
                        for line in Path(fpath).read_text(encoding="utf-8", errors="replace").splitlines():
                            if line.strip():
                                try:
                                    r = json.loads(line.strip())
                                    norm = normalize_row_to_chatml(r)
                                    if norm:
                                        records.append(norm)
                                except Exception:
                                    pass
                    elif fname.endswith(".json"):
                        data = json.loads(Path(fpath).read_text(encoding="utf-8", errors="replace"))
                        if isinstance(data, list):
                            for r in data:
                                if isinstance(r, dict):
                                    norm = normalize_row_to_chatml(r)
                                    if norm:
                                        records.append(norm)
                except Exception as fe:
                    logger.warning(f"   Note downloading {fname}: {fe}")
        logger.info(f"   ✅ Harvested {len(records)} records from raw files in {repo_id}")
    except Exception as e:
        logger.error(f"   ❌ Failed to harvest {repo_id}: {e}")

    return records


def main():
    parser = argparse.ArgumentParser(description="Harvest and Curate Hugging Face Liked BaZi Datasets")
    parser.add_argument("--output", type=str, default="project/data/bazi_hf_curated_corpus.jsonl", help="Output JSONL path")
    parser.add_argument("--max-per-dataset", type=int, default=5000, help="Max records per dataset to prevent imbalance")
    args = parser.parse_args()

    hf_token = Config.HF_TOKEN
    output_path = ROOT_DIR / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 75)
    print(f"🌟 HoroConsultant — Hugging Face Liked Datasets Harvester (@{HF_USERNAME})")
    print("=" * 75)

    dataset_repos = fetch_liked_dataset_names(hf_token)
    if not dataset_repos:
        logger.error("No liked datasets found or API error.")
        sys.exit(1)

    all_records = []
    seen_hashes = set()

    for idx, repo in enumerate(dataset_repos, 1):
        print(f"\n[{idx}/{len(dataset_repos)}] Checking {repo}...")
        recs = harvest_dataset_repo(repo, hf_token)
        
        # Sample limit per dataset
        if len(recs) > args.max_per_dataset:
            recs = recs[:args.max_per_dataset]

        dedup_count = 0
        for r in recs:
            # Hash conversation content
            content_str = json.dumps(r["messages"], sort_keys=True)
            h = hashlib.sha256(content_str.encode("utf-8")).hexdigest()
            if h not in seen_hashes:
                seen_hashes.add(h)
                all_records.append(r)
                dedup_count += 1
        
        logger.info(f"   + Added {dedup_count} unique records (Total accumulated: {len(all_records)})")

    # Write out curated JSONL
    with open(output_path, "w", encoding="utf-8") as f:
        for r in all_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print("\n" + "=" * 75)
    print(f"✅ Harvester Completed!")
    print(f"• Total Processed Datasets: {len(dataset_repos)}")
    print(f"• Total Unique Normalized ChatML Records: {len(all_records)}")
    print(f"• Saved Corpus File: {output_path} ({output_path.stat().st_size / 1024 / 1024:.2f} MB)")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    main()
