from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from prepos.application.knowledge.citation_service import extract_citations
from prepos.application.knowledge.dto import KnowledgeSearchChunk, KnowledgeSourceSummary


def test_extract_citations_includes_article_metadata() -> None:
    chunk_id = uuid4()
    published_at = datetime(2026, 6, 1, tzinfo=UTC)
    chunks = [
        KnowledgeSearchChunk(
            chunk_id=chunk_id,
            content="Article body",
            score=0.9,
            vector_score=0.9,
            keyword_score=0.8,
            source=KnowledgeSourceSummary(
                source_id=uuid4(),
                title="PIB Release",
                source_type="pib",
                published_at=published_at,
                source_authority="pib",
            ),
            metadata={},
        )
    ]
    answer = f"The scheme was expanded recently. [{chunk_id}]"

    citations = extract_citations(answer, context_chunks=chunks)

    assert len(citations) == 1
    assert citations[0].source_title == "PIB Release"
    assert citations[0].source_type == "pib"
    assert citations[0].published_at == published_at
