from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _declarations(css: str, selector: str) -> dict[str, str]:
    match = re.search(
        rf"(?m)^\s*{re.escape(selector)}\s*\{{(?P<body>[^}}]+)\}}",
        css,
    )
    assert match is not None, f"missing CSS rule for {selector}"
    declarations: dict[str, str] = {}
    for item in match.group("body").split(";"):
        if ":" not in item:
            continue
        name, value = item.split(":", 1)
        declarations[name.strip()] = value.strip()
    return declarations


def _rgb(value: str) -> tuple[float, float, float, float]:
    if value.startswith("#") and len(value) == 7:
        return tuple(int(value[index : index + 2], 16) for index in (1, 3, 5)) + (
            1.0,
        )
    match = re.fullmatch(
        r"rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([\d.]+)\s*\)",
        value,
    )
    assert match is not None, f"unsupported color: {value}"
    red, green, blue, alpha = match.groups()
    return float(red), float(green), float(blue), float(alpha)


def _composite(
    foreground: tuple[float, float, float, float],
    background: tuple[float, float, float, float],
) -> tuple[float, float, float, float]:
    alpha = foreground[3] + background[3] * (1 - foreground[3])
    channels = tuple(
        (
            foreground[index] * foreground[3]
            + background[index] * background[3] * (1 - foreground[3])
        )
        / alpha
        for index in range(3)
    )
    return channels + (alpha,)


def _luminance(color: tuple[float, float, float, float]) -> float:
    channels = []
    for raw in color[:3]:
        normalized = raw / 255
        channels.append(
            normalized / 12.92
            if normalized <= 0.04045
            else ((normalized + 0.055) / 1.055) ** 2.4
        )
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def _contrast_ratio(
    foreground: tuple[float, float, float, float],
    background: tuple[float, float, float, float],
) -> float:
    first, second = sorted(
        (_luminance(foreground), _luminance(background)), reverse=True
    )
    return (first + 0.05) / (second + 0.05)


def _styles() -> tuple[str, str]:
    source = (ROOT / "project" / "static" / "style.css").read_text(
        encoding="utf-8"
    )
    public = (ROOT / "public" / "style.css").read_text(encoding="utf-8")
    return source, public


def test_public_and_backend_styles_are_exact_mirrors() -> None:
    source, public = _styles()

    assert source == public


def test_interpretation_tabs_can_wrap_inside_narrow_cards() -> None:
    source, _public = _styles()

    assert _declarations(source, ".tab-buttons").get("flex-wrap") == "wrap"


def test_accordion_chevron_meets_wcag_aa_normal_text_contrast() -> None:
    source, _public = _styles()
    chevron = _declarations(source, ".acc-chevron")
    page = (255.0, 255.0, 255.0, 1.0)
    background = _composite(_rgb(chevron["background"]), page)
    foreground = _rgb(chevron["color"])

    assert _contrast_ratio(foreground, background) >= 4.5
