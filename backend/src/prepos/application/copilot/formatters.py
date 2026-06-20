from __future__ import annotations

from decimal import Decimal


def format_score(value: Decimal | float | int | None) -> str:
    if value is None:
        return "n/a"
    normalized = float(value)
    text = f"{normalized:.2f}".rstrip("0").rstrip(".")
    return text or "0"


def format_optional_text(value: str | None, *, fallback: str = "Not available") -> str:
    if value is None or not value.strip():
        return fallback
    return value.strip()
