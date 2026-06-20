from __future__ import annotations

from prepos.domain.knowledge.concept_mapping import map_concepts_from_text


def test_map_concepts_from_title_and_preview() -> None:
    concepts = map_concepts_from_text(
        title="Article 356 and President's Rule",
        content_preview="Discussion of constitutional provisions and federalism.",
    )
    assert "polity_article_356" in concepts
    assert "polity_federalism" in concepts
