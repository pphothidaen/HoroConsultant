from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _expanded_accordion_max_height(css: str) -> int | None:
    match = re.search(
        r"(?m)^\s*\.accordion-card-body\s*\{(?P<body>[^}]+)\}",
        css,
    )
    assert match is not None
    property_match = re.search(
        r"(?m)^\s*max-height\s*:\s*(?P<value>none|\d+px)\s*;",
        match.group("body"),
    )
    assert property_match is not None
    value = property_match.group("value")
    return None if value == "none" else int(value.removesuffix("px"))


def test_expanded_accordion_does_not_clip_long_mobile_results() -> None:
    source = (ROOT / "project" / "static" / "style.css").read_text(
        encoding="utf-8"
    )
    public = (ROOT / "public" / "style.css").read_text(encoding="utf-8")
    maximum = _expanded_accordion_max_height(source)

    assert source == public
    assert maximum is None or maximum >= 10_000
