from __future__ import annotations

import re
from dataclasses import dataclass, field

ATTACK_PATTERNS: dict[str, list[re.Pattern[str]]] = {
    "ignore_instructions": [
        re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?", re.I),
        re.compile(r"disregard\s+(your\s+)?(system\s+)?prompt", re.I),
        re.compile(r"forget\s+(everything|all)\s+(you\s+)?(were\s+)?told", re.I),
    ],
    "reveal_system_prompt": [
        re.compile(r"(show|reveal|print|display|output)\s+(me\s+)?(your\s+)?(system\s+)?prompt", re.I),
        re.compile(r"what\s+(is|are)\s+your\s+(system\s+)?instructions?", re.I),
        re.compile(r"repeat\s+(your\s+)?(initial|system)\s+(prompt|instructions?)", re.I),
    ],
    "bypass_restrictions": [
        re.compile(r"bypass\s+(security|restrictions?|filters?|guardrails?)", re.I),
        re.compile(r"disable\s+(safety|content\s+filter|guardrails?)", re.I),
        re.compile(r"act\s+as\s+(if\s+)?(you\s+have\s+)?no\s+(rules|restrictions?)", re.I),
    ],
    "cross_tenant_data": [
        re.compile(r"(show|list|get|fetch)\s+(another|other|all)\s+students?", re.I),
        re.compile(r"(access|view)\s+(other|another)\s+(tenant|institute|student)", re.I),
        re.compile(r"student\s+data\s+(from|of)\s+another", re.I),
    ],
    "jailbreak": [
        re.compile(r"\bDAN\b.*\bmode\b", re.I),
        re.compile(r"developer\s+mode\s+enabled", re.I),
        re.compile(r"do\s+anything\s+now", re.I),
        re.compile(r"jailbreak", re.I),
        re.compile(r"pretend\s+you\s+(are|have)\s+no\s+(ethical|safety)\s+guidelines?", re.I),
    ],
}


@dataclass(frozen=True)
class DetectionResult:
    categories: list[str] = field(default_factory=list)
    matched_patterns: list[str] = field(default_factory=list)


def detect_prompt_injection(text: str) -> DetectionResult:
    normalized = text.strip()
    if not normalized:
        return DetectionResult()

    categories: list[str] = []
    matched: list[str] = []
    for category, patterns in ATTACK_PATTERNS.items():
        for pattern in patterns:
            if pattern.search(normalized):
                if category not in categories:
                    categories.append(category)
                matched.append(f"{category}:{pattern.pattern[:48]}")
                break
    return DetectionResult(categories=categories, matched_patterns=matched)
