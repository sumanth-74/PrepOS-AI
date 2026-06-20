from __future__ import annotations

import re

_KEYWORD_CONCEPTS: tuple[tuple[str, str], ...] = (
    ("federalism", "polity_federalism"),
    ("basic structure", "polity_basic_structure"),
    ("article 356", "polity_article_356"),
    ("president's rule", "polity_article_356"),
    ("budget", "economy_union_budget"),
    ("economic survey", "economy_economic_survey"),
    ("gst", "economy_gst"),
    ("climate", "environment_climate_change"),
    ("scheme", "governance_welfare_schemes"),
)


def map_concepts_from_text(*, title: str, content_preview: str) -> tuple[str, ...]:
    normalized = re.sub(r"\s+", " ", f"{title} {content_preview}".lower()).strip()
    mapped: list[str] = []
    for keyword, concept_id in _KEYWORD_CONCEPTS:
        if keyword in normalized and concept_id not in mapped:
            mapped.append(concept_id)
    return tuple(mapped)
