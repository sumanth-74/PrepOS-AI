from __future__ import annotations

import re

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_MULTI_SPACE = re.compile(r"\s{3,}")
_ZERO_WIDTH = re.compile(r"[\u200b-\u200f\ufeff]")


def sanitize_prompt(text: str, *, max_length: int = 2000) -> str:
    cleaned = text.strip()
    cleaned = _ZERO_WIDTH.sub("", cleaned)
    cleaned = _CONTROL_CHARS.sub("", cleaned)
    cleaned = _MULTI_SPACE.sub("  ", cleaned)
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    return cleaned


def redact_for_logging(text: str, *, max_visible: int = 120) -> str:
    if len(text) <= max_visible:
        return text
    return f"{text[:max_visible]}…[{len(text)} chars]"
