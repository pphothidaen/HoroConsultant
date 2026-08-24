"""Contract tests for deterministic engine -> Horo v3.0 claim adapters."""

from datetime import datetime
import os
import sys
from uuid import UUID

import pytest


RUNTIMES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "TDD-HORO-v3.0", "05_AGENT_PROMPTS_AND_RUNTIMES")
sys.path.insert(0, os.path.abspath(RUNTIMES_DIR))

from project.core.bazi_engine import BaZiEngine
from project.core.liu_ren_engine import LiuRenEngine
from project.core.liu_yao_engine import LiuYaoEngine
from project.core.mian_xiang_engine import MianXiangEngine
from project.core.qi_men_engine import QiMenEngine
from project.core.qi_zheng_engine import QiZhengSiYuEngine
from project.core.tai_yi_engine import TaiYiEngine
from project.core.xuan_kong_engine import XuanKongEngine
from project.core.ze_ji_engine import ZeJiEngine
from project.core.zi_wei_engine import ZiWeiEngine
from project.core.v3_engine_adapter import (
    adapt_bazi_to_claims,
    adapt_daliuren_to_claims,
    adapt_liuyao_to_claims,
    adapt_mianxiang_to_claims,
    adapt_qimen_to_claims,
    adapt_qizheng_to_claims,
    adapt_taiyi_to_claims,
    adapt_xuankong_to_claims,
    adapt_zeji_to_claims,
    adapt_ziwei_to_claims,
)

from runtimes.claim_validator import ClaimValidator


ADAPTER_CASES = [
    ("bazi", lambda: BaZiEngine().calculate(datetime(1990, 5, 15, 14), 103.8, 7.0, include_dayun=False)),
    ("ziwei", lambda: ZiWeiEngine().calculate_chart(1990, 5, 15, 14)),
    ("qimen", lambda: QiMenEngine().calculate_chart(2026, 8, 7, 14)),
    ("zeji", lambda: ZeJiEngine().check_suitability("午", "申", "寅", "子")),
    ("xuankong", lambda: XuanKongEngine().calculate_chart(180.0, period=9)),
    ("daliuren", lambda: LiuRenEngine().calculate_chart("甲", "子", "正月", "午")),
    ("liuyao", lambda: LiuYaoEngine().calculate([6, 7, 8, 9, 7, 8])),
    ("taiyi", lambda: TaiYiEngine().calculate(2026, 8, 15, 12)),
    ("qizheng", lambda: QiZhengSiYuEngine().calculate(1990, 5, 15, 14, 100.493, 13.7563)),
    ("mianxiang", lambda: MianXiangEngine().calculate({"face_shape": "oval", "forehead": "wide", "nose": "high"}, birth_year=1990)),
]

ADAPTER_METADATA = {
    "bazi": ("@Horo_BaZi_Node", "ming_xue_bazi", "滴天髓", "BAZI-STRENGTH-001"),
    "ziwei": ("@Horo_ZiWei_Node", "ming_xue_ziwei", "紫微斗数全书", "ZIWEI-PALACE-001"),
    "qimen": ("@Horo_QiMen_Node", "san_shi_qi_men", "烟波钓叟歌", "QIMEN-FORMATION-001"),
    "zeji": ("@Horo_ZeJi_Node", "ze_ji_xue", "协纪辨方书", "ZEJI-VETO-001"),
    "xuankong": ("@Horo_FengShui_Node", "xiang_xue_feng_shui", "沈氏玄空学", "XUANKONG-PERIOD-009"),
    "daliuren": ("@Horo_DaLiuRen_Node", "san_shi_da_liu_ren", "六壬大全", "DALIUREN-GENERAL-001"),
    "liuyao": ("@Horo_BuShi_Node", "bu_shi_liu_yao", "卜筮正宗", "LIUYAO-YONGSHEN-001"),
    "taiyi": ("@Horo_TaiYi_Node", "san_shi_tai_yi", "太乙金镜式经", "TAIYI-MACRO-001"),
    "qizheng": ("@Horo_QiZheng_Node", "ming_xue_qi_zheng", "果老星宗", "QIZHENG-PLANET-001"),
    "mianxiang": ("@Horo_MianXiang_Node", "xiang_xue_mian_xiang", "麻衣神相", "MIANXIANG-PALACE-001"),
}


@pytest.mark.parametrize("name, build_result", ADAPTER_CASES)
def test_adapter_emission_passes_claim_validator(name, build_result):
    adapter = {
        "bazi": adapt_bazi_to_claims,
        "ziwei": adapt_ziwei_to_claims,
        "qimen": adapt_qimen_to_claims,
        "zeji": adapt_zeji_to_claims,
        "xuankong": adapt_xuankong_to_claims,
        "daliuren": adapt_daliuren_to_claims,
        "liuyao": adapt_liuyao_to_claims,
        "taiyi": adapt_taiyi_to_claims,
        "qizheng": adapt_qizheng_to_claims,
        "mianxiang": adapt_mianxiang_to_claims,
    }[name]
    payload = adapter(build_result(), session_id="12345678-1234-4234-8234-123456789abc")

    valid, violations = ClaimValidator.validate_emission_payload(payload)
    assert valid, violations
    assert payload["claims"]
    assert payload["session_id"] == "12345678-1234-4234-8234-123456789abc"


@pytest.mark.parametrize("name, build_result", ADAPTER_CASES)
def test_adapter_emission_has_contract_metadata(name, build_result):
    adapter = {
        "bazi": adapt_bazi_to_claims,
        "ziwei": adapt_ziwei_to_claims,
        "qimen": adapt_qimen_to_claims,
        "zeji": adapt_zeji_to_claims,
        "xuankong": adapt_xuankong_to_claims,
        "daliuren": adapt_daliuren_to_claims,
        "liuyao": adapt_liuyao_to_claims,
        "taiyi": adapt_taiyi_to_claims,
        "qizheng": adapt_qizheng_to_claims,
        "mianxiang": adapt_mianxiang_to_claims,
    }[name]
    payload = adapter(build_result())
    claim = payload["claims"][0]
    trace = claim["epistemic_trace"]

    UUID(payload["session_id"])
    assert datetime.fromisoformat(payload["emitted_at_utc"].replace("Z", "+00:00")).tzinfo is not None
    assert len(payload["input_state_hash"]) == 64
    assert trace["derived_from_calc_hash"] == payload["input_state_hash"]
    assert len(claim["claim_id"]) == 64
    assert set(claim["confidence_vector"]) == {
        "calculation_integrity",
        "rule_match_strength",
        "source_support",
        "interpretation_stability",
        "cross_agent_agreement",
    }
    node_id, domain, source, rule_id = ADAPTER_METADATA[name]
    assert (payload["node_id"], payload["tradition_domain"]) == (node_id, domain)
    assert trace["source_corpus"] == source
    assert trace["applied_rule_id"] == rule_id


def test_adapters_reject_non_mapping_engine_results():
    with pytest.raises(TypeError):
        adapt_bazi_to_claims(["not", "a", "result"])
