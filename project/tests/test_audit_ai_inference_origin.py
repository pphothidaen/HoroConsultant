"""
project/tests/test_audit_ai_inference_origin.py
=================================================
Pytest Suite for AI Inference Origin & Anti-Template Auditor.

Validates that:
  1. Fine-tuned BaZi Model `pphothidaen/qwen2.5-7b-bazi-instruct-4bit` on Hugging Face
     is correctly recognized and verified.
  2. Genuine AI LLM inference outputs are classified as `REAL_AI_MODEL`.
  3. Echo templates & static fallback strings are classified as `FALLBACK_TEMPLATE`.
  4. Semantic similarity and linguistic variance calculations are exact.
  5. Mocked network auditor calls handle both successful and error responses properly.
"""

from unittest.mock import MagicMock, patch
import pytest

from scripts.audit_ai_inference_origin import (
    KNOWN_VALID_AI_MODELS,
    TARGET_BAZI_FINE_TUNED_MODEL,
    calculate_semantic_similarity,
    classify_inference_payload,
    verify_fine_tuned_model_compatibility,
    audit_query_pair
)


class TestFineTunedModelCompatibility:
    """Test suite for fine-tuned Hugging Face BaZi model detection."""

    def test_target_hf_model_constant(self):
        assert TARGET_BAZI_FINE_TUNED_MODEL == "pphothidaen/qwen2.5-7b-bazi-instruct-4bit"
        assert TARGET_BAZI_FINE_TUNED_MODEL in KNOWN_VALID_AI_MODELS

    def test_exact_hf_model_name_recognition(self):
        assert verify_fine_tuned_model_compatibility("pphothidaen/qwen2.5-7b-bazi-instruct-4bit") is True
        assert verify_fine_tuned_model_compatibility("PPHOTHIDAEN/QWEN2.5-7B-BAZI-INSTRUCT-4BIT") is True

    def test_fine_tuned_alias_recognition(self):
        assert verify_fine_tuned_model_compatibility("qwen2.5-bazi") is True
        assert verify_fine_tuned_model_compatibility("qwen2.5:7b") is True
        assert verify_fine_tuned_model_compatibility("pphothidaen/qwen2.5-7b-bazi-instruct") is True

    def test_cloud_gemini_models_recognition(self):
        assert verify_fine_tuned_model_compatibility("gemini-3.5-flash-lite") is True
        assert verify_fine_tuned_model_compatibility("gemini-3.6-flash") is True
        assert verify_fine_tuned_model_compatibility("gemini-3.7-flash") is True
        assert verify_fine_tuned_model_compatibility("gemini-flash-latest") is True

    def test_invalid_or_empty_model_recognition(self):
        assert verify_fine_tuned_model_compatibility("") is False
        assert verify_fine_tuned_model_compatibility(None) is False
        assert verify_fine_tuned_model_compatibility("unknown-random-model-xyz") is False


class TestInferenceOriginClassification:
    """Test suite for classifying responses into Real AI vs Fallback Template."""

    def test_classify_real_ai_fine_tuned_hf_model(self):
        data_a = {
            "source": "ai_agent_llm",
            "model_used": "pphothidaen/qwen2.5-7b-bazi-instruct-4bit",
            "interpretation": (
                "คารวะเจ้าของดวงชะตา ตามหลักคัมภีร์ จื่อผิงเจินเฉวียน (子平真詮) "
                "ผังดวงชะตาดิถี 庚 มีดาวบุตรหลานเป็นธาตุน้ำ (食神/傷官) ซึ่งสถิตในเสายาม "
                "บ่งบอกว่าบุตรหลานมีสติปัญญาเฉลียวฉลาด มีปฏิภาณไหวพริบยอดเยี่ยม"
            )
        }
        data_b = {
            "source": "ai_agent_llm",
            "model_used": "pphothidaen/qwen2.5-7b-bazi-instruct-4bit",
            "interpretation": (
                "ในมิติด้านการงานและอาชีพในอนาคตของบุตรหลาน ดาวสติปัญญาธาตุน้ำผสานธาตุไม้ "
                "ส่งผลให้มีความถนัดในสายงานที่ต้องใช้การวางแผน การสื่อสารระหว่างประเทศ "
                "หรือเทคโนโลยีสมัยใหม่ เมื่อได้รับการสนับสนุนที่ถูกต้องจะก้าวหน้าอย่างรวดเร็ว"
            )
        }

        result = classify_inference_payload(
            data_a, data_b,
            query_a="ลูกเป็นอย่างไร",
            query_b="ในอนาคตลูกจะมีแววทำงานด้านไหน"
        )

        assert result["classification"] == "REAL_AI_MODEL"
        assert result["confidence"] >= 0.95
        assert result["model_used"] == "pphothidaen/qwen2.5-7b-bazi-instruct-4bit"
        assert result["is_fine_tuned_model_compatible"] is True
        assert result["is_echo_template"] is False
        assert result["variance_score"] > 0.10

    def test_classify_real_ai_cloud_gemini(self):
        data_a = {
            "source": "ai_agent_llm",
            "model_used": "gemini-3.5-flash-lite",
            "interpretation": "ดวงชะตาดิถีทอง 庚 ปี 2026 เป็นปีม้าไฟ 丙午 มีเกณฑ์ดาวการงานและชื่อเสียงส่งเสริม"
        }
        data_b = {
            "source": "ai_agent_llm",
            "model_used": "gemini-3.5-flash-lite",
            "interpretation": "การขยายสาขาธุรกิจใหม่ในปี 2026 ต้องระมัดระวังเรื่องสภาพคล่องและความเสี่ยงด้านคู่แข่ง"
        }

        result = classify_inference_payload(
            data_a, data_b,
            query_a="ปี 2026 ควรเปิดร้านอาหารดีไหม",
            query_b="ควรลงทุนเปิดสาขาธุรกิจใหม่ปี 2026 ไหม"
        )

        assert result["classification"] == "REAL_AI_MODEL"
        assert result["model_used"] == "gemini-3.5-flash-lite"
        assert result["is_fine_tuned_model_compatible"] is True

    def test_classify_echo_template_fallback_detected(self):
        template_base = (
            "### 🔮 การวิเคราะห์ผังดวงจีน\n"
            "- ดิถี: 庚 (Metal)\n"
            "ตามตำแหน่งดาว 4 เสาหลัก การวิเคราะห์ประเด็นเรื่อง '{query}' "
            "สำหรับดิถี 庚 มีพลังธาตุส่งเสริมจากธาตุให้คุณหลัก ช่วยหนุนนำดวงชะตาในเรื่อง '{query}' ให้ราบรื่น"
        )
        data_a = {
            "source": "unknown",
            "model_used": "none",
            "interpretation": template_base.format(query="ลูกเป็นอย่างไร")
        }
        data_b = {
            "source": "unknown",
            "model_used": "none",
            "interpretation": template_base.format(query="การงานปีนี้")
        }

        result = classify_inference_payload(
            data_a, data_b,
            query_a="ลูกเป็นอย่างไร",
            query_b="การงานปีนี้"
        )

        assert result["classification"] == "FALLBACK_TEMPLATE"
        assert result["is_echo_template"] is True
        assert result["confidence"] >= 0.95

    def test_classify_known_static_signature_fallback(self):
        data_a = {
            "source": "fallback",
            "model_used": "none",
            "interpretation": (
                "### 🔮 การวิเคราะห์ผังดวงจีนด้านบุตรหลานและบริวาร (BaZi Children Analysis)\n"
                "- สำหรับผังดวงชะตาดิถี 庚 (Metal) ช่วยหนุนนำดวงชะตาในเรื่องบุตรหลาน"
            )
        }
        data_b = {
            "source": "fallback",
            "model_used": "none",
            "interpretation": (
                "### 🔮 การวิเคราะห์ผังดวงจีนด้านบุตรหลานและบริวาร (BaZi Children Analysis)\n"
                "- สำหรับผังดวงชะตาดิถี 庚 (Metal) ช่วยหนุนนำดวงชะตาในเรื่องการศึกษาบุตรหลาน"
            )
        }

        result = classify_inference_payload(
            data_a, data_b,
            query_a="ลูกเป็นอย่างไร",
            query_b="การศึกษาลูก"
        )

        assert result["classification"] == "FALLBACK_TEMPLATE"
        assert result["confidence"] >= 0.90


class TestSemanticSimilarity:
    """Test suite for semantic similarity and variance scoring."""

    def test_identical_texts_variance_zero(self):
        text = "การทำนายดวงจีน 4 เสาหลัก"
        similarity = calculate_semantic_similarity(text, text)
        assert similarity == 1.0

    def test_divergent_texts_variance_positive(self):
        text1 = "การวิเคราะห์มิติบุตรหลานและดาวสติปัญญา"
        text2 = "แนวทางการลงทุนธุรกิจร้านอาหารในปี 2026"
        similarity = calculate_semantic_similarity(text1, text2)
        variance = 1.0 - similarity
        assert variance > 0.50


class TestAuditQueryPairNetwork:
    """Test suite for audit_query_pair with network mocks."""

    @patch("requests.post")
    def test_audit_query_pair_success_with_hf_model(self, mock_post):
        mock_resp_a = MagicMock()
        mock_resp_a.status_code = 200
        mock_resp_a.json.return_value = {
            "source": "ai_agent_llm",
            "model_used": "pphothidaen/qwen2.5-7b-bazi-instruct-4bit",
            "interpretation": "บุตรหลานมีดาวสติปัญญาธาตุน้ำ สถิตในเสายามกำเนิด"
        }

        mock_resp_b = MagicMock()
        mock_resp_b.status_code = 200
        mock_resp_b.json.return_value = {
            "source": "ai_agent_llm",
            "model_used": "pphothidaen/qwen2.5-7b-bazi-instruct-4bit",
            "interpretation": "เส้นทางอาชีพของบุตรหลานมีโอกาสในสายงานเทคโนโลยีและการเงิน"
        }

        mock_post.side_effect = [mock_resp_a, mock_resp_b]

        result = audit_query_pair(
            endpoint="http://localhost:8000/api/v1/bazi/interpret",
            query_a="ลูกเป็นอย่างไร",
            query_b="อาชีพของลูก"
        )

        assert result["classification"] == "REAL_AI_MODEL"
        assert result["model_used"] == "pphothidaen/qwen2.5-7b-bazi-instruct-4bit"
        assert result["is_fine_tuned_model_compatible"] is True
        assert "latency_ms" in result

    @patch("requests.post")
    def test_audit_query_pair_http_error(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 502
        mock_post.return_value = mock_resp

        result = audit_query_pair(
            endpoint="http://localhost:8000/api/v1/bazi/interpret",
            query_a="ลูกเป็นอย่างไร",
            query_b="อาชีพของลูก"
        )

        assert result["classification"] == "UNREACHABLE"
        assert result["status"] == "ERROR"
        assert result["http_status_a"] == 502
