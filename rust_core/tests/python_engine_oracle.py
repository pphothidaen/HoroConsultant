"""Stream deterministic Python-oracle charts for the Rust parity gate."""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from project.core.iching_engine import IChingEngine
from project.core.liu_ren_engine import LiuRenEngine
from project.core.numerology_engine import NumerologyEngine
from project.core.observability import ObservabilityManager
from project.core.qi_men_engine import QiMenEngine
from project.core.thai_vedic_engine import ThaiVedicEngine
from project.core.xuan_kong_engine import XuanKongEngine
from project.core.ze_ji_engine import ZeJiEngine
from project.core.zi_wei_engine import ZiWeiEngine


BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
MONTH_GENERALS = ["正月", "二月", "三月", "四月", "五月", "六月", "七月", "八月", "九月", "十月", "十一月", "十二月"]


def clean(chart: dict) -> dict:
    result = dict(chart)
    result.pop("calculation_timestamp", None)
    return result


def stream(count: int, seed: int) -> None:
    rng = random.Random(seed)
    engines = {
        "ziwei": ZiWeiEngine(),
        "qimen": QiMenEngine(),
        "xuankong": XuanKongEngine(),
        "thai_vedic": ThaiVedicEngine(),
        "iching": IChingEngine(),
        "liuren": LiuRenEngine(),
        "zeji": ZeJiEngine(),
        "numerology": NumerologyEngine(),
    }
    for index in range(count):
        engine = index % 9
        if engine == 0:
            payload = {
                "year": rng.randint(1900, 2100), "month": rng.randint(1, 12),
                "day": rng.randint(1, 30), "hour": rng.randint(0, 23),
                "gender": rng.choice(["male", "female"]),
            }
            chart = engines["ziwei"].calculate_chart(**payload)
            name = "ziwei"
        elif engine == 1:
            payload = {
                "year": rng.randint(1900, 2100), "month": rng.randint(1, 12),
                "day": rng.randint(1, 28), "hour": rng.randint(0, 23),
            }
            chart = engines["qimen"].calculate_chart(**payload)
            name = "qimen"
        elif engine == 2:
            payload = {"facing_degree": rng.randrange(360_000_000) / 1_000_000, "period": rng.choice([8, 9])}
            chart = engines["xuankong"].calculate_chart(**payload)
            name = "xuankong"
        elif engine == 3:
            payload = {
                "year": rng.randint(1900, 2100), "month": rng.randint(1, 12),
                "day": rng.randint(1, 28), "hour": rng.randint(0, 23),
                "day_of_week": rng.randint(0, 7),
            }
            chart = engines["thai_vedic"].calculate_chart(**payload)
            name = "thai_vedic"
        elif engine == 4:
            payload = {"day_stem": rng.choice(STEMS), "lines": [rng.choice([6, 7, 8, 9]) for _ in range(6)]}
            chart = engines["iching"].calculate_liu_yao(**payload)
            name = "iching"
        elif engine == 5:
            payload = {
                "day_stem": rng.choice(STEMS), "day_branch": rng.choice(BRANCHES),
                "month_general": rng.choice(MONTH_GENERALS), "hour_branch": rng.choice(BRANCHES),
            }
            chart = engines["liuren"].calculate_chart(**payload)
            name = "liuren"
        elif engine == 6:
            payload = {
                "year_branch": rng.choice(BRANCHES), "month_branch": rng.choice(BRANCHES),
                "day_branch": rng.choice(BRANCHES),
                "user_birth_branch": rng.choice(BRANCHES + [None]),
            }
            chart = engines["zeji"].check_suitability(**payload)
            name = "zeji"
        elif engine == 7:
            payload = {
                "day_num": rng.randint(-20, 40), "lunar_month": rng.randint(-20, 40),
                "year_zodiac_num": rng.randint(-20, 40),
            }
            chart = engines["numerology"].calculate_satta_lek(**payload)
            name = "satta_lek"
        else:
            alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZกขคฆงจฉชซญดตถทธนบปผพภมยรลวศษสหอฮะาิีุูเแโใไ"
            payload = {"text": "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 24)))}
            chart = engines["numerology"].score_text_or_number(**payload)
            name = "numerology_score"
        print(json.dumps({"engine": name, "input": payload, "chart": clean(chart)}, ensure_ascii=False, separators=(",", ":")))


def percentile_95(samples: list[int]) -> int:
    samples.sort()
    return samples[(len(samples) - 1) * 95 // 100]


def benchmark(count: int) -> None:
    ziwei = ZiWeiEngine()
    qimen = QiMenEngine()
    xuankong = XuanKongEngine()
    thai = ThaiVedicEngine()
    iching = IChingEngine()
    liuren = LiuRenEngine()
    zeji = ZeJiEngine()
    numerology = NumerologyEngine()
    requests: dict[str, list[str]] = {
        "ziwei": [json.dumps({"year": 1900 + i % 201, "month": 1 + i % 12, "day": 1 + i % 28, "hour": i % 24, "gender": "male"}) for i in range(count)],
        "qimen": [json.dumps({"year": 1900 + i % 201, "month": 1 + i % 12, "day": 1 + i % 28, "hour": i % 24}) for i in range(count)],
        "xuankong": [json.dumps({"facing_degree": (i * 1_000_003 % 360_000_000) / 1_000_000, "period": 9}) for i in range(count)],
        "thai_vedic": [json.dumps({"year": 1900 + i % 201, "month": 1 + i % 12, "day": 1 + i % 28, "hour": i % 24, "day_of_week": i % 8}) for i in range(count)],
        "iching": [json.dumps({"day_stem": STEMS[i % 10], "lines": [6 + (i + offset) % 4 for offset in range(6)]}, ensure_ascii=False) for i in range(count)],
        "liuren": [json.dumps({"day_stem": STEMS[i % 10], "day_branch": BRANCHES[i % 12], "month_general": MONTH_GENERALS[i % 12], "hour_branch": BRANCHES[(i * 5) % 12]}, ensure_ascii=False) for i in range(count)],
        "zeji": [json.dumps({"year_branch": BRANCHES[i % 12], "month_branch": BRANCHES[(i * 3) % 12], "day_branch": BRANCHES[(i * 7) % 12], "user_birth_branch": BRANCHES[(i * 11) % 12]}, ensure_ascii=False) for i in range(count)],
        "numerology": [json.dumps({"day_num": 1 + i % 31, "lunar_month": 1 + i % 12, "year_zodiac_num": 1 + i % 12}) for i in range(count)],
    }

    def calculate(engine: str, payload_text: str) -> bytes:
        payload = json.loads(payload_text)
        if engine == "ziwei":
            chart = ziwei.calculate_chart(**payload)
        elif engine == "qimen":
            chart = qimen.calculate_chart(**payload)
        elif engine == "xuankong":
            chart = xuankong.calculate_chart(**payload)
        elif engine == "thai_vedic":
            chart = thai.calculate_chart(**payload)
        elif engine == "iching":
            chart = iching.calculate_liu_yao(**payload)
        elif engine == "liuren":
            chart = liuren.calculate_chart(**payload)
        elif engine == "zeji":
            chart = zeji.check_suitability(**payload)
        else:
            chart = numerology.calculate_satta_lek(**payload)
        return json.dumps(chart, ensure_ascii=False, separators=(",", ":")).encode()

    result = {}
    for engine, payloads in requests.items():
        for payload in payloads[:20]:
            calculate(engine, payload)
        cpu_start = time.process_time_ns()
        wall_samples = []
        for payload in payloads:
            started = time.perf_counter_ns()
            calculate(engine, payload)
            wall_samples.append(time.perf_counter_ns() - started)
        cpu_per_request = (time.process_time_ns() - cpu_start) / count
        result[engine] = {"p95_ns": percentile_95(wall_samples), "cpu_per_request_ns": cpu_per_request}
    metrics = ObservabilityManager()
    for index in range(20):
        metrics.record_request("GET", f"/api/{index % 4}", 200, 0.001)
        metrics.generate_metrics_text()
    cpu_start = time.process_time_ns()
    wall_samples = []
    for index in range(count):
        started = time.perf_counter_ns()
        metrics.record_request("GET", f"/api/{index % 4}", 200, 0.001)
        metrics.generate_metrics_text()
        wall_samples.append(time.perf_counter_ns() - started)
    result["metrics"] = {
        "p95_ns": percentile_95(wall_samples),
        "cpu_per_request_ns": (time.process_time_ns() - cpu_start) / count,
    }
    print(json.dumps(result, separators=(",", ":")))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=4_271_909)
    parser.add_argument("--benchmark", action="store_true")
    args = parser.parse_args()
    if args.benchmark:
        benchmark(args.count)
    else:
        stream(args.count, args.seed)
