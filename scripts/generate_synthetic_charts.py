#!/usr/bin/env python3
"""
scripts/generate_synthetic_charts.py
======================================
Generate a large set of synthetic BaZi charts using the engine
and save them to project/data/sample_charts.json for MLX training.
"""
import json
import random
import sys
from datetime import datetime
from pathlib import Path

# ensure project root on path
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

from project.core.bazi_engine import BaZiEngine


def main(n=500, seed=42):
    engine = BaZiEngine()
    random.seed(seed)
    charts = []
    skipped = 0

    # Coordinates: Bangkok (100.49, 7.0), Singapore (103.82, 8.0), Taipei (121.56, 8.0)
    locations = [
        (100.4930,  7.0, "Bangkok"),
        (103.8198,  8.0, "Singapore"),
        (121.5654,  8.0, "Taipei"),
        (114.1095,  8.0, "Hong Kong"),
        (116.4074,  8.0, "Beijing"),
        (139.6917,  9.0, "Tokyo"),
        ( -0.1278,  0.0, "London"),
        (-74.0060, -5.0, "New York"),
    ]

    for i in range(n):
        lng, utc, city = random.choice(locations)
        year   = random.randint(1940, 2010)
        month  = random.randint(1, 12)
        day    = random.randint(1, 28)
        hour   = random.randint(0, 23)
        minute = random.randint(0, 59)

        try:
            dt  = datetime(year, month, day, hour, minute)
            res = engine.calculate(dt=dt, longitude=lng, utc_offset_hours=utc)
            res["_meta"] = {"city": city, "index": i}
            charts.append(res)
        except Exception:
            skipped += 1

    out = root / "project" / "data" / "sample_charts.json"
    out.write_text(json.dumps(charts, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✅ Generated {len(charts)} charts ({skipped} skipped) → {out}")

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--n",    type=int, default=500, help="Number of charts")
    p.add_argument("--seed", type=int, default=42)
    a = p.parse_args()
    main(a.n, a.seed)
