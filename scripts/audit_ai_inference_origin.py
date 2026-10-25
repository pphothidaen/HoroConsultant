#!/usr/bin/env python3
"""
scripts/audit_ai_inference_origin.py
======================================
AI Inference Origin Auditor & Classifier for QA Tester Agent.

Inspects API endpoints, responses, and UI text to definitively classify
the generation source into:
  • [REAL_AI_MODEL]      : Genuine LLM inference (dynamic vocabulary, high semantic entropy).
  • [FALLBACK_TEMPLATE]  : Static rule-based template or placeholder string substitution.
  • [HYBRID_HEURISTIC]   : Deterministic calculation engine output.

Usage:
  python3 scripts/audit_ai_inference_origin.py --endpoint https://horo-consultant-psi.vercel.app/api/v1/bazi/interpret
  python3 scripts/audit_ai_inference_origin.py --live-check
"""

import argparse
import difflib
import json
import sys
import time
from typing import Any, Dict, List, Tuple
import requests


# Target Fine-Tuned BaZi LLM on Hugging Face
TARGET_BAZI_FINE_TUNED_MODEL = "pphothidaen/qwen2.5-7b-bazi-instruct-4bit"

# Known valid AI models supported by the engine
KNOWN_VALID_AI_MODELS = [
    TARGET_BAZI_FINE_TUNED_MODEL,
    "pphothidaen/qwen2.5-7b-bazi-instruct",
    "qwen2.5-bazi",
    "qwen2.5:7b",
    "qwen2.5-coder:7b",
    "gemini-3.5-flash-lite",
    "gemini-flash-latest",
    "gemini-3.6-flash",
    "gemini-3.7-flash"
]

# Known static fallback signatures (to detect rule-based fallbacks)
KNOWN_FALLBACK_SIGNATURES = [
    "สำหรับผังดวงชะตาดิถี",
    "ช่วยหนุนนำดวงชะตาในเรื่อง",
    "คำทำนายเจาะจงมิติ",
    "ดวงชะตานี้มีดิถีวันเป็น",
    "### 🔮 การวิเคราะห์ผังดวงจีนด้านบุตรหลานและบริวาร (BaZi Children Analysis)"
]


def calculate_semantic_similarity(text1: str, text2: str) -> float:
    """Calculate character sequence similarity ratio between two texts."""
    return difflib.SequenceMatcher(None, text1, text2).ratio()


def verify_fine_tuned_model_compatibility(model_name: str) -> bool:
    """
    Verify if the model used corresponds to or is compatible with
    the fine-tuned Hugging Face model (pphothidaen/qwen2.5-7b-bazi-instruct-4bit).
    """
    if not model_name:
        return False
    m = model_name.strip().lower()
    target = TARGET_BAZI_FINE_TUNED_MODEL.lower()
    return (
        m == target
        or "qwen2.5-7b-bazi" in m
        or "qwen2.5-bazi" in m
        or any(m == valid.lower() for valid in KNOWN_VALID_AI_MODELS)
    )


def classify_inference_payload(
    data_a: Dict[str, Any],
    data_b: Dict[str, Any],
    query_a: str,
    query_b: str
) -> Dict[str, Any]:
    """
    Pure decision function that classifies inference origin based on payload response data.
    """
    text_a = data_a.get("interpretation") or data_a.get("response") or str(data_a)
    text_b = data_b.get("interpretation") or data_b.get("response") or str(data_b)

    source_a = data_a.get("source", "unknown")
    model_a = data_a.get("model_used", "unknown")

    # 1. Similarity Check
    similarity = calculate_semantic_similarity(text_a, text_b)
    variance_score = round(1.0 - similarity, 4)

    # 2. Template Signature Check
    has_signature_a = any(sig in text_a for sig in KNOWN_FALLBACK_SIGNATURES)
    has_signature_b = any(sig in text_b for sig in KNOWN_FALLBACK_SIGNATURES)

    # 3. Echo Placeholder Check (does it simply replace query in an identical frame?)
    simulated_sub = text_a.replace(query_a, query_b)
    is_echo_template = (calculate_semantic_similarity(simulated_sub, text_b) > 0.98) and query_a != query_b

    # 4. Fine-Tuned Model Recognition Check
    is_valid_model = verify_fine_tuned_model_compatibility(model_a)

    # 5. Classification Decision Logic
    if source_a == "ai_agent_llm" and not is_echo_template and variance_score > 0.05:
        classification = "REAL_AI_MODEL"
        confidence = 0.98
        reason = f"Verified live Cloud/Local LLM generation (model: {model_a}, variance: {variance_score:.2f})"
    elif is_echo_template:
        classification = "FALLBACK_TEMPLATE"
        confidence = 0.99
        reason = "Exact string substitution inside boilerplate template detected."
    elif has_signature_a and has_signature_b and similarity > 0.90:
        classification = "FALLBACK_TEMPLATE"
        confidence = 0.95
        reason = "Matched known rule-based fallback signature with low semantic variance."
    elif variance_score > 0.15:
        classification = "REAL_AI_MODEL"
        confidence = 0.85
        reason = f"High linguistic variance ({variance_score:.2f}) and custom vocabulary structure."
    else:
        classification = "HYBRID_HEURISTIC"
        confidence = 0.70
        reason = "Deterministic or cached response structure."

    return {
        "query_a": query_a,
        "query_b": query_b,
        "classification": classification,
        "confidence": confidence,
        "model_used": model_a,
        "is_fine_tuned_model_compatible": is_valid_model,
        "source": source_a,
        "semantic_similarity": round(similarity, 4),
        "variance_score": variance_score,
        "is_echo_template": is_echo_template,
        "reason": reason,
        "sample_snippet": text_a[:250].replace("\n", " ")
    }


def audit_query_pair(
    endpoint: str,
    query_a: str,
    query_b: str,
    birth_datetime: str = "1990-05-15 14:30:00"
) -> Dict[str, Any]:
    """
    Send two variant queries to the endpoint and analyze response metadata and semantic variance.
    """
    payload_a = {
        "birth_datetime": birth_datetime,
        "query": query_a,
        "longitude": 100.493,
        "utc_offset_hours": 7
    }
    payload_b = {
        "birth_datetime": birth_datetime,
        "query": query_b,
        "longitude": 100.493,
        "utc_offset_hours": 7
    }

    t0 = time.monotonic()
    resp_a = requests.post(endpoint, json=payload_a, timeout=15)
    lat_a = round((time.monotonic() - t0) * 1000)

    t0 = time.monotonic()
    resp_b = requests.post(endpoint, json=payload_b, timeout=15)
    lat_b = round((time.monotonic() - t0) * 1000)

    if resp_a.status_code != 200 or resp_b.status_code != 200:
        return {
            "status": "ERROR",
            "http_status_a": resp_a.status_code,
            "http_status_b": resp_b.status_code,
            "classification": "UNREACHABLE",
            "confidence": 0.0,
            "reason": f"HTTP status A={resp_a.status_code}, B={resp_b.status_code}"
        }

    data_a = resp_a.json()
    data_b = resp_b.json()
    res = classify_inference_payload(data_a, data_b, query_a, query_b)
    res["latency_ms"] = (lat_a + lat_b) // 2
    return res


def run_full_audit(endpoint: str) -> bool:
    print("=" * 75)
    print("🔍 AI INFERENCE ORIGIN & ANTI-TEMPLATE AUDITOR (QA SKILL)")
    print(f"   Target Endpoint: {endpoint}")
    print("=" * 75)

    test_pairs = [
        ("ลูกเป็นอย่างไร", "ในอนาคตลูกจะมีแววทำงานด้านไหน"),
        ("ปี 2026 ควรเปิดร้านอาหารดีไหม", "ควรลงทุนเปิดสาขาธุรกิจใหม่ปี 2026 ไหม"),
        ("เรื่องความรักปีนี้จะเจอคู่ไหม", "ลักษณะเนื้อคู่และคนที่เข้ามาในปีนี้เป็นอย่างไร"),
        ("การเงินและโชคลาภปีนี้", "ควรบริหารการเงินและกระจายความเสี่ยงอย่างไรในปีนี้")
    ]

    all_real_ai = True
    results = []

    for idx, (qa, qb) in enumerate(test_pairs, 1):
        print(f"\n[AUDIT {idx}] Testing Domain Query Pair:")
        print(f"  • Query A: '{qa}'")
        print(f"  • Query B: '{qb}'")

        res = audit_query_pair(endpoint, qa, qb)
        results.append(res)

        tag = "🟢 PASS (Real AI)" if res["classification"] == "REAL_AI_MODEL" else "🔴 FAIL (Fallback/Template)"
        print(f"  Result: {tag}")
        print(f"  Classification : {res['classification']} (Confidence: {res['confidence']*100:.1f}%)")
        print(f"  Model & Source : {res.get('model_used')} | {res.get('source')}")
        print(f"  Variance Score : {res['variance_score']} (Similarity: {res['semantic_similarity']})")
        print(f"  Reason         : {res['reason']}")
        print(f"  Snippet        : {res['sample_snippet']}...")

        if res["classification"] != "REAL_AI_MODEL":
            all_real_ai = False

    print("\n" + "=" * 75)
    print("📊 AI INFERENCE AUDIT SUMMARY")
    print("=" * 75)
    print(f"Overall Status: {'✅ 100% GENUINE AI MODEL INFERENCE' if all_real_ai else '⚠️ FALLBACK OR TEMPLATE DETECTED'}")
    print("=" * 75)
    return all_real_ai


def main():
    parser = argparse.ArgumentParser(description="Audit whether API responses originate from Real AI or Fallback Template")
    parser.add_argument("--endpoint", default="https://horo-consultant-psi.vercel.app/api/v1/bazi/interpret", help="Target API endpoint")
    parser.add_argument("--live-check", action="store_true", help="Run audit against live production gateway")
    args = parser.parse_args()

    endpoint = args.endpoint
    if args.live_check:
        endpoint = "https://horo-consultant-psi.vercel.app/api/v1/bazi/interpret"

    success = run_full_audit(endpoint)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
