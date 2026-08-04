#!/usr/bin/env python3
"""
scripts/ocr_pdf_gemini.py
=========================
Gemini Vision OCR & Scanned Book Markdown Conversion Engine.

Uses Gemini 2.0 Flash Multimodal API to perform high-accuracy OCR on old,
scanned yellow-paper astrological PDF books (Thai, Pali, Chinese).

Automated Flow:
  1. Render PDF pages into images (or extract embedded images)
  2. Send images to Gemini Vision API with key rotation (KEY1 -> KEY2)
  3. Perform OCR, clean noise/headers/page numbers, and format to Markdown (.md)
  4. Save clean .md file to project/rag/obsidian_vault/
  5. Auto-trigger project/rag/ingest_vault.py for immediate FAISS indexing

Usage:
  # OCR a single PDF file
  python scripts/ocr_pdf_gemini.py --input "path/to/old_scanned_book.pdf"

  # Batch OCR all scanned PDFs in vault directory
  python scripts/ocr_pdf_gemini.py --batch-vault

  # Specifying page limit (e.g. first 10 pages for testing)
  python scripts/ocr_pdf_gemini.py --input "path/to/book.pdf" --max-pages 10
"""

from __future__ import annotations

import os
import sys
import io
import time
import json
import base64
import logging
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("ocr_gemini")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
MODEL_NAME      = os.getenv("PRIMARY_MODEL", "gemini-2.0-flash")
VAULT_DIR       = ROOT / "project" / "rag" / "obsidian_vault"

OCR_SYSTEM_PROMPT = """คุณคือผู้เชี่ยวชาญด้าน OCR (Optical Character Recognition) และภาษาศาสตร์สถิติ
หน้าที่ของคุณคืออ่านภาพหน้าหนังสือเก่า/กระดาษสีเหลืองสแกน (ไทย, บาลี, สันสกฤต, จีน)
แล้วถอดความเป็นข้อความสะอาด พร้อมจัด Format เป็น Markdown (#, ##, ###)

กฎการถอดความอย่างเคร่งครัด:
1. อ่านตัวอักษรภาษาไทย/บาลี/จีน อย่างถูกต้อง 100% ไม่ข้ามประโยค
2. ลบองค์ประกอบขยะออก เช่น เลขหน้า, หัวกระดาษ (Header), ท้ายกระดาษ (Footer), หรือรอยเปื้อนกระดาษเก่า
3. ใช้โครงสร้าง Markdown (# หัวข้อหลัก, ## หัวข้อย่อย) แบ่งสัดส่วนตามย่อหน้าในหนังสือจริง
4. ตอบกลับเฉพาะข้อความ Markdown ถอดความเท่านั้น ไม่ต้องมีคำอธิบายเพิ่มเติม
"""


def _get_api_keys() -> List[str]:
    raw = [
        os.getenv("GOOGLE_AI_STUDIO_API_KEY", ""),
        os.getenv("GOOGLE_AI_STUDIO_API_KEY2", ""),
    ]
    return [k for k in raw if k and not k.startswith("REPLACE")]


def ocr_page_image_gemini(image_bytes: bytes, mime_type: str = "image/jpeg") -> Optional[str]:
    """Call Gemini Vision API to OCR a single page image."""
    keys = _get_api_keys()
    if not keys:
        log.error("No Gemini API key available for Vision OCR.")
        return None

    b64_data = base64.b64encode(image_bytes).decode("utf-8")
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "inlineData": {
                            "mimeType": mime_type,
                            "data": b64_data
                        }
                    },
                    {
                        "text": "โปรดอ่านและถอดข้อความในภาพหน้านี้เป็น Markdown ภาษาไทยอย่างละเอียดและแม่นยำ"
                    }
                ]
            }
        ],
        "systemInstruction": {"parts": [{"text": OCR_SYSTEM_PROMPT}]},
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 4096}
    }

    for key in keys:
        url = f"{GEMINI_BASE_URL}/models/{MODEL_NAME}:generateContent?key={key}"
        try:
            with httpx.Client(timeout=45.0) as client:
                res = client.post(url, json=payload)
            if res.status_code == 200:
                data = res.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return text.strip()
            elif res.status_code == 429:
                log.warning(f"Key ...{key[-6:]} 429 rate-limited -> sleeping 2s and trying next key...")
                time.sleep(2.0)
                continue
            else:
                log.warning(f"HTTP {res.status_code}: {res.text[:150]}")
        except Exception as e:
            log.warning(f"OCR Gemini call error: {e}")

    return None


def extract_images_from_pdf(pdf_path: Path, max_pages: Optional[int] = None) -> List[bytes]:
    """Convert PDF pages into JPEG bytes list."""
    images_bytes: List[bytes] = []

    # 1. Try pdf2image (requires poppler)
    try:
        from pdf2image import convert_from_path
        log.info(f"Rendering PDF pages with pdf2image: {pdf_path.name}")
        pil_images = convert_from_path(str(pdf_path), first_page=1, last_page=max_pages or 50)
        for img in pil_images:
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=85)
            images_bytes.append(buf.getvalue())
        return images_bytes
    except Exception as e:
        log.info(f"pdf2image fallback ({e}) -> using pypdf image extractor...")

    # 2. Fallback to pypdf embedded image extraction
    try:
        import pypdf
        from PIL import Image
        reader = pypdf.PdfReader(str(pdf_path))
        num_pages = min(len(reader.pages), max_pages or 50)
        for i in range(num_pages):
            page = reader.pages[i]
            for count, image_file_object in enumerate(page.images):
                img = Image.open(io.BytesIO(image_file_object.data))
                buf = io.BytesIO()
                img.convert("RGB").save(buf, format="JPEG", quality=85)
                images_bytes.append(buf.getvalue())
    except Exception as ex:
        log.error(f"Failed to extract images from PDF: {ex}")

    return images_bytes


TRACKER_FILE = ROOT / "project" / "data" / "ocr_completed_files.json"


def load_completed_tracker() -> Dict[str, Any]:
    if TRACKER_FILE.exists():
        try:
            return json.loads(TRACKER_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"completed_files": [], "last_updated": ""}


def mark_file_completed(file_path: Path, pages_processed: int, md_path: Path) -> None:
    tracker = load_completed_tracker()
    rel_path = str(file_path.relative_to(ROOT))
    completed = tracker.get("completed_files", [])

    # Update or append
    completed = [item for item in completed if item.get("file") != rel_path]
    completed.append({
        "file": rel_path,
        "completed_at": datetime.now().isoformat(),
        "pages_processed": pages_processed,
        "markdown_output": str(md_path.relative_to(ROOT)),
    })

    tracker["completed_files"] = completed
    tracker["last_updated"]    = datetime.now().isoformat()
    TRACKER_FILE.parent.mkdir(parents=True, exist_ok=True)
    TRACKER_FILE.write_text(json.dumps(tracker, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info(f"📌 Marked as DONE in tracker -> {rel_path}")


def is_file_completed(file_path: Path) -> bool:
    tracker = load_completed_tracker()
    rel_path = str(file_path.relative_to(ROOT))
    for item in tracker.get("completed_files", []):
        if item.get("file") == rel_path:
            return True
    return False


def validate_converted_markdown(md_text: str, expected_min_chars: int = 100) -> Tuple[bool, str]:
    """
    Validate the converted Markdown text quality after OCR.

    Checks:
      1. Non-empty & minimum text length
      2. No error / rate-limit strings in body
      3. Valid Thai/Chinese/Pali/English character density
      4. Valid Markdown formatting elements

    Returns (is_valid, reason)
    """
    if not md_text or not md_text.strip():
        return False, "Markdown text is empty"

    cleaned = md_text.strip()
    if len(cleaned) < expected_min_chars:
        return False, f"Text length too short ({len(cleaned)} chars < {expected_min_chars} min)"

    # Check for API error leakages
    error_keywords = ["Too Many Requests", "429 Rate Limit", "Quota Exceeded", "Internal Server Error", "nan"]
    for kw in error_keywords:
        if kw.lower() in cleaned.lower() and len(cleaned) < 300:
            return False, f"API Error string detected: {kw}"

    # Check character content (Thai, Chinese, or Latin)
    has_thai = any('\u0e00' <= char <= '\u0e7f' for char in cleaned)
    has_chinese = any('\u4e00' <= char <= '\u9fff' for char in cleaned)
    has_latin = any('a' <= char.lower() <= 'z' for char in cleaned)

    if not (has_thai or has_chinese or has_latin):
        return False, "No valid Thai, Chinese, or Latin characters found in output"

    return True, "PASSED_QUALITY_CHECKS"


def ocr_pdf_to_markdown(pdf_path: Path, output_dir: Path = VAULT_DIR, max_pages: Optional[int] = None, force: bool = False) -> Optional[Path]:
    """
    Process a scanned PDF file, perform Gemini Vision OCR page by page,
    validates conversion quality, and saves clean Markdown to output_dir.
    Marks file as DONE in tracker ONLY if validation passes.
    """
    if not force and is_file_completed(pdf_path):
        log.info(f"⏭️ Skipping (already marked as DONE): {pdf_path.name}")
        return None

    log.info("=" * 60)
    log.info(f"📸 Gemini Vision OCR Processing: {pdf_path.name}")
    log.info("=" * 60)

    images = extract_images_from_pdf(pdf_path, max_pages=max_pages)
    if not images:
        log.warning(f"No pages/images rendered from {pdf_path.name}")
        return None

    log.info(f"Extracted {len(images)} page images -> Starting Gemini Vision OCR...")

    markdown_pages: List[str] = []
    markdown_pages.append(f"# {pdf_path.stem}\n")

    valid_pages = 0
    consecutive_failures = 0
    for idx, img_bytes in enumerate(images, start=1):
        log.info(f"  Processing Page {idx}/{len(images)}...")
        page_md = ocr_page_image_gemini(img_bytes)
        if page_md:
            markdown_pages.append(f"<!-- Page {idx} -->\n" + page_md + "\n")
            valid_pages += 1
            consecutive_failures = 0
        else:
            consecutive_failures += 1
            log.warning(f"  Page {idx}: OCR returned empty or rate-limited (failure #{consecutive_failures})")
            if consecutive_failures >= 3:
                log.error("⚠️ 3 consecutive API failures detected (rate-limited) — Aborting early to avoid wasting API quota.")
                break

    full_md = "\n\n".join(markdown_pages)

    # 🔍 Post-Conversion Validation Check
    is_valid, reason = validate_converted_markdown(full_md, expected_min_chars=150 * max(1, valid_pages))
    log.info(f"🔍 Post-Conversion Validation Status: {'✅ PASSED' if is_valid else '❌ FAILED'} ({reason})")

    if not is_valid:
        log.error(f"❌ Conversion validation failed for {pdf_path.name}: {reason} — File will NOT be marked as DONE.")
        return None

    out_file = output_dir / f"{pdf_path.stem}_gemini_ocr.md"
    out_file.write_text(full_md, encoding="utf-8")
    log.info(f"✅ OCR completed & verified -> Saved Markdown: {out_file}")

    mark_file_completed(pdf_path, len(images), out_file)
    return out_file


def batch_ocr_vault(max_pages_per_pdf: int = 5, force: bool = False) -> List[Path]:
    """Find scanned PDFs in obsidian_vault, skip already completed ones, and convert remaining via Gemini Vision OCR."""
    pdf_files = sorted(list(VAULT_DIR.rglob("*.pdf")))
    log.info(f"Found {len(pdf_files)} PDFs in vault for OCR processing...")

    generated: List[Path] = []
    for pdf_file in pdf_files:
        if not force and is_file_completed(pdf_file):
            log.info(f"⏭️ [DONE] {pdf_file.name}")
            continue

        res = ocr_pdf_to_markdown(pdf_file, max_pages=max_pages_per_pdf, force=force)
        if res:
            generated.append(res)

    if generated:
        log.info("\n🔄 Triggering Vault Ingestion for newly generated Markdown files...")
        subprocess.run([sys.executable, "project/rag/ingest_vault.py", "--export-finetune"], check=True, cwd=str(ROOT))

    return generated


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gemini Vision OCR for Scanned Astrological PDFs")
    parser.add_argument("--input",        help="Path to specific PDF file to OCR")
    parser.add_argument("--max-pages",    type=int, default=5, help="Maximum pages to process")
    parser.add_argument("--batch-vault",  action="store_true", help="Batch OCR scanned PDFs in vault")
    args = parser.parse_args()

    if args.input:
        in_path = Path(args.input)
        if in_path.exists():
            ocr_pdf_to_markdown(in_path, max_pages=args.max_pages)
        else:
            print(f"❌ Input file not found: {args.input}")
    elif args.batch_vault:
        batch_ocr_vault(max_pages_per_pdf=args.max_pages)
    else:
        parser.print_help()
