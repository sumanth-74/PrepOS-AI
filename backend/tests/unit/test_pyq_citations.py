from __future__ import annotations

from uuid import uuid4

from prepos.application.knowledge.citation_service import extract_citations
from prepos.application.knowledge.dto import KnowledgeSearchChunk, KnowledgeSourceSummary


def test_extract_citations_includes_pyq_year_and_paper() -> None:
    chunk_id = uuid4()
    chunks = [
        KnowledgeSearchChunk(
            chunk_id=chunk_id,
            content="PYQ body",
            score=0.9,
            vector_score=0.9,
            keyword_score=0.8,
            source=KnowledgeSourceSummary(
                source_id=uuid4(),
                title="UPSC PYQ 2021",
                source_type="pyq",
            ),
            metadata={"year": 2021, "paper": "GS2"},
        )
    ]
    answer = f"Article 356 appeared in UPSC 2021 GS2. [{chunk_id}]"

    citations = extract_citations(answer, context_chunks=chunks)

    assert len(citations) == 1
    assert citations[0].source_type == "pyq"
    assert citations[0].pyq_year == 2021
    assert citations[0].pyq_paper == "GS2"
