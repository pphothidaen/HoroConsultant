"""Deterministic cross-language oracle and complete-calculation benchmark.

This is test support only. The authoritative implementation remains
project.core.bazi_engine.BaZiEngine.
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
import time
from datetime import datetime, timedelta
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from project.core.bazi_engine import BaZiEngine  # noqa: E402
from project.core import fast_math  # noqa: E402

# This process is the independent Python oracle even when a native wheel is
# installed. All accelerated dispatch must be disabled before the first chart.
fast_math.RUST_AVAILABLE = False
fast_math.PYTHON_FALLBACK_ALLOWED = True


def valid_cases(seed: int, count: int):
    rng = random.Random(seed)
    start = datetime(1901, 1, 1)
    available_days = (datetime(2099, 12, 31) - start).days
    for index in range(count):
        date = start + timedelta(days=rng.randrange(available_days + 1))
        yield {
            "year": date.year,
            "month": date.month,
            "day": date.day,
            "hour": rng.randrange(24),
            "minute": rng.randrange(60),
            "second": rng.randrange(60),
            "longitude": round(rng.uniform(-180.0, 180.0), 6),
            "utc_offset_hours": rng.choice(
                [-12.0, -9.5, -8.0, -5.0, 0.0, 3.5, 5.5, 5.75, 7.0, 8.0, 9.5, 12.0, 13.0, 14.0]
            ),
            "unknown_hour": index % 97 == 0,
        }


def calculate(engine: BaZiEngine, case: dict) -> dict:
    dt = datetime(
        case["year"],
        case["month"],
        case["day"],
        case["hour"],
        case["minute"],
        case["second"],
    )
    chart = dict(
        engine.calculate(
            dt,
            case["longitude"],
            case["utc_offset_hours"],
            case["unknown_hour"],
        )
    )
    chart.pop("calculation_timestamp", None)
    return chart


def emit_cases(seed: int, count: int) -> None:
    engine = BaZiEngine()
    for case in valid_cases(seed, count):
        print(
            json.dumps(
                {"input": case, "chart": calculate(engine, case)},
                ensure_ascii=False,
                separators=(",", ":"),
            )
        )


def percentile_95(samples: list[int]) -> int:
    return sorted(samples)[int(0.95 * (len(samples) - 1))]


def benchmark(count: int) -> None:
    engine = BaZiEngine()
    requests = [line.strip() for line in sys.stdin if line.strip()]
    if len(requests) != count:
        raise ValueError(f"expected {count} requests on stdin, received {len(requests)}")
    for payload in requests[:20]:
        case = json.loads(payload)
        json.dumps(calculate(engine, case), ensure_ascii=False, separators=(",", ":"))

    wall_samples: list[int] = []
    cpu_start = time.process_time_ns()
    for payload in requests:
        start = time.perf_counter_ns()
        case = json.loads(payload)
        json.dumps(calculate(engine, case), ensure_ascii=False, separators=(",", ":"))
        wall_samples.append(time.perf_counter_ns() - start)
    cpu_elapsed = time.process_time_ns() - cpu_start
    print(
        json.dumps(
            {
                "count": count,
                "p95_ns": percentile_95(wall_samples),
                "cpu_per_request_ns": cpu_elapsed / count,
                "median_ns": statistics.median(wall_samples),
            },
            separators=(",", ":"),
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=0xBA21_2026)
    parser.add_argument("--count", type=int, required=True)
    parser.add_argument("--benchmark", action="store_true")
    args = parser.parse_args()
    if args.benchmark:
        benchmark(args.count)
    else:
        emit_cases(args.seed, args.count)


if __name__ == "__main__":
    main()
