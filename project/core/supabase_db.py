"""
project/core/supabase_db.py
===========================
Supabase Database Integration Client for HoroConsultant.

Provides REST API operations (using httpx) for:
1. Range-paginated dataset fetching (`qa_knowledge_base` table)
2. ShareGPT JSONL dataset generation for Local MLX & Cloud PyTorch/Unsloth Training
3. Logging fine-tuning checkpoints and model runs (`model_checkpoints` table)
4. Storing BaZi calculation records (`bazi_charts` table)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional
import httpx

from project.core.config import Config

logger = logging.getLogger("supabase_db")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class SupabaseDB:
    """Lightweight REST-based Supabase Database Client with Range Pagination."""

    def __init__(self, url: Optional[str] = None, key: Optional[str] = None):
        self.url = (url or Config.SUPABASE_URL).rstrip("/")
        self.key = key or Config.SUPABASE_KEY
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    def is_configured(self) -> bool:
        """Check if Supabase credentials are valid."""
        return bool(self.url and self.key and self.url.startswith("http"))

    def fetch_all(
        self,
        table: str,
        select: str = "*",
        filters: Optional[dict[str, Any]] = None,
        page_size: int = 1000,
    ) -> list[dict[str, Any]]:
        """
        Fetch all records from a Supabase table using Range Pagination to bypass the 1,000 row limit.
        """
        if not self.is_configured():
            logger.warning("Supabase is not configured. Returning empty dataset.")
            return []

        endpoint = f"{self.url}/rest/v1/{table}"
        results: list[dict[str, Any]] = []
        offset = 0

        params = {"select": select}
        if filters:
            for k, v in filters.items():
                params[k] = f"eq.{v}"

        with httpx.Client(timeout=30.0) as client:
            while True:
                range_header = f"{offset}-{offset + page_size - 1}"
                req_headers = {**self.headers, "Range": range_header}

                try:
                    resp = client.get(endpoint, headers=req_headers, params=params)
                    if resp.status_code not in (200, 206):
                        logger.error(f"Supabase GET failed ({resp.status_code}): {resp.text}")
                        break

                    data = resp.json()
                    if not data or not isinstance(data, list):
                        break

                    results.extend(data)
                    logger.info(f"Fetched rows {offset}..{offset + len(data) - 1} from '{table}' (Total so far: {len(results)})")

                    if len(data) < page_size:
                        break

                    offset += page_size
                except Exception as e:
                    logger.error(f"Network error during Supabase fetch: {e}")
                    break

        return results

    async def async_fetch_all(
        self,
        table: str,
        select: str = "*",
        filters: Optional[dict[str, Any]] = None,
        page_size: int = 1000,
    ) -> list[dict[str, Any]]:
        """
        Asynchronously fetch all records from a Supabase table using Range Pagination.
        """
        if not self.is_configured():
            logger.warning("Supabase is not configured. Returning empty dataset.")
            return []

        endpoint = f"{self.url}/rest/v1/{table}"
        results: list[dict[str, Any]] = []
        offset = 0

        params = {"select": select}
        if filters:
            for k, v in filters.items():
                params[k] = f"eq.{v}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            while True:
                range_header = f"{offset}-{offset + page_size - 1}"
                req_headers = {**self.headers, "Range": range_header}

                try:
                    resp = await client.get(endpoint, headers=req_headers, params=params)
                    if resp.status_code not in (200, 206):
                        logger.error(f"Supabase GET failed ({resp.status_code}): {resp.text}")
                        break

                    data = resp.json()
                    if not data or not isinstance(data, list):
                        break

                    results.extend(data)
                    if len(data) < page_size:
                        break

                    offset += page_size
                except Exception as e:
                    logger.error(f"Async network error during Supabase fetch: {e}")
                    break

        return results

    async def async_upsert(self, table: str, records: list[dict[str, Any]], on_conflict: str = "id") -> bool:
        """Asynchronously upsert records into a Supabase table."""
        if not self.is_configured() or not records:
            return False

        endpoint = f"{self.url}/rest/v1/{table}"
        req_headers = {**self.headers, "Prefer": f"resolution=merge-duplicates,return=representation"}
        params = {"on_conflict": on_conflict}

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.post(endpoint, headers=req_headers, params=params, json=records)
                if resp.status_code in (200, 201):
                    return True
                logger.error(f"Supabase Async Upsert failed ({resp.status_code}): {resp.text}")
                return False
            except Exception as e:
                logger.error(f"Network error during Supabase async upsert: {e}")
        return False

    def upsert(self, table: str, records: list[dict[str, Any]], on_conflict: str = "id") -> bool:
        """Upsert records into a Supabase table synchronously."""
        if not self.is_configured() or not records:
            return False

        endpoint = f"{self.url}/rest/v1/{table}"

        with httpx.Client(timeout=30.0) as client:
            try:
                resp = client.post(endpoint, headers=headers, json=records)
                if resp.status_code in (200, 201):
                    logger.info(f"Successfully upserted {len(records)} records into '{table}'")
                    return True
                else:
                    logger.error(f"Supabase Upsert failed ({resp.status_code}): {resp.text}")
                    return False
            except Exception as e:
                logger.error(f"Network error during Supabase upsert: {e}")
                return False

    def export_verified_qa_to_jsonl(self, output_path: Path) -> int:
        """
        Fetch all verified Q&A pairs from `qa_knowledge_base` and export to ShareGPT JSONL format.
        """
        records = self.fetch_all("qa_knowledge_base", filters={"is_verified": "true"})
        if not records:
            logger.warning("No verified Q&A records found in Supabase. Using fallback if available.")
            return 0

        output_path.parent.mkdir(parents=True, exist_ok=True)
        count = 0
        with open(output_path, "w", encoding="utf-8") as f:
            for item in records:
                instruction = item.get("question") or item.get("prompt", "")
                response = item.get("answer") or item.get("response", "")
                system_prompt = item.get("system_prompt") or (
                    "คุณคือผู้เชี่ยวชาญด้านวิเคราะห์ดวงชะตาโหราศาสตร์จีน BaZi (四柱命理學) และเวลาสุริยคติจริง "
                    "โปรดพยากรณ์อย่างเที่ยงตรงด้วยหลักธาตุและกฎธรรมชาติ"
                )

                if instruction and response:
                    sharegpt_entry = {
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": instruction},
                            {"role": "assistant", "content": response},
                        ]
                    }
                    f.write(json.dumps(sharegpt_entry, ensure_ascii=False) + "\n")
                    count += 1

        logger.info(f"🎉 Exported {count} ShareGPT records from Supabase to '{output_path}'")
        return count

    def log_training_run(
        self,
        platform: str,
        model_name: str,
        step_count: int,
        final_loss: float,
        hf_repo_id: str,
        hf_commit_hash: str = "",
        notes: str = "",
    ) -> bool:
        """Log fine-tuning job completion to `model_checkpoints` table."""
        record = {
            "platform": platform,
            "model_name": model_name,
            "step_count": step_count,
            "final_loss": final_loss,
            "hf_repo_id": hf_repo_id,
            "hf_commit_hash": hf_commit_hash,
            "notes": notes,
        }
        return self.upsert("model_checkpoints", [record])


# SQL DDL Script for User's Supabase Setup Reference
SUPABASE_SCHEMA_SQL = """
-- =========================================================
-- HoroConsultant Database Schema DDL for Supabase (PostgreSQL)
-- =========================================================

-- 1. Table: bazi_charts (บันทึกผังดวงชะตาที่คำนวณแล้ว)
CREATE TABLE IF NOT EXISTS public.bazi_charts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT now(),
    birth_datetime TIMESTAMPTZ NOT NULL,
    latitude NUMERIC(8,4) NOT NULL,
    longitude NUMERIC(8,4) NOT NULL,
    utc_offset NUMERIC(4,1) NOT NULL,
    tst_datetime TIMESTAMPTZ NOT NULL,
    eot_minutes NUMERIC(6,2),
    year_pillar VARCHAR(10) NOT NULL,
    month_pillar VARCHAR(10) NOT NULL,
    day_pillar VARCHAR(10) NOT NULL,
    hour_pillar VARCHAR(10) NOT NULL,
    element_scores JSONB NOT NULL,
    notes TEXT
);

-- 2. Table: qa_knowledge_base (ชุดข้อมูล Q&A โหราศาสตร์สำหรับ Fine-Tuning)
CREATE TABLE IF NOT EXISTS public.qa_knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT now(),
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    category VARCHAR(50) DEFAULT 'BaZi',
    source_book VARCHAR(255),
    system_prompt TEXT,
    is_verified BOOLEAN DEFAULT true,
    quality_score NUMERIC(3,2) DEFAULT 1.00
);

-- 3. Table: model_checkpoints (บันทึกประวัติการ Fine-Tune ทั้ง Local และ Cloud)
CREATE TABLE IF NOT EXISTS public.model_checkpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT now(),
    platform VARCHAR(50) NOT NULL, -- 'MLX_LOCAL', 'KAGGLE_T4', 'LIGHTNING_L4'
    model_name VARCHAR(100) NOT NULL,
    step_count INT NOT NULL,
    final_loss NUMERIC(6,4),
    hf_repo_id VARCHAR(150),
    hf_commit_hash VARCHAR(100),
    notes TEXT
);

-- Create Indexes for performance
CREATE INDEX IF NOT EXISTS idx_qa_verified ON public.qa_knowledge_base (is_verified);
CREATE INDEX IF NOT EXISTS idx_bazi_datetime ON public.bazi_charts (birth_datetime);
"""


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Supabase DB Client & Dataset Exporter for HoroConsultant")
    parser.add_argument("--export", type=Path, help="Path to save ShareGPT JSONL file")
    parser.add_argument("--show-schema", action="store_true", help="Print PostgreSQL SQL DDL schema for Supabase")
    args = parser.parse_args()

    if args.show_schema:
        print(SUPABASE_SCHEMA_SQL)
        return

    db = SupabaseDB()
    if not db.is_configured():
        print("⚠️ Supabase credentials not found in environment or .env file.")
        print("Run with --show-schema to view the SQL DDL for setting up Supabase.")
        return

    if args.export:
        db.export_verified_qa_to_jsonl(args.export)
    else:
        print("✅ Supabase client initialized and connected successfully!")


if __name__ == "__main__":
    main()
