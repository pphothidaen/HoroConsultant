#!/usr/bin/env python3
"""Capture the canonical OpenAPI golden used by the gateway contract tests.

Regenerates ``project/tests/goldens/openapi.json`` from the live FastAPI app.

This is the canonical (and previously undocumented) regeneration path for the
golden: run it in the CI-parity environment (Python 3.12 + the pinned
``requirements.txt`` dependency set, i.e. what ``.github/workflows/ci.yml``
installs) so the committed bytes match what CI reproduces:

    HORO_ALLOW_PYTHON_FALLBACK=1 SKIP_FAISS_WARMUP=true \
        python scripts/capture_openapi_golden.py

The captured ``info.version`` embeds the current git short hash; the gateway
contract test monkeypatches ``app.version`` to the golden's value, so the
version component alone never gates the contract comparison.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

os.environ.setdefault("HORO_ALLOW_PYTHON_FALLBACK", "1")
os.environ.setdefault("SKIP_FAISS_WARMUP", "true")

from project.main import app  # noqa: E402  (import after env hardening)


def main() -> None:
    golden_path = REPO_ROOT / "project" / "tests" / "goldens" / "openapi.json"
    golden_path.write_text(
        json.dumps(app.openapi(), indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {golden_path.relative_to(REPO_ROOT)}")
    print(f"paths: {len(app.openapi()['paths'])}")


if __name__ == "__main__":
    main()
