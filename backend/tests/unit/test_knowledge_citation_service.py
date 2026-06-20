from __future__ import annotations

from uuid import uuid4

from prepos.application.knowledge.citation_service import (
    extract_citations,
    validate_grounded_answer,
)
from prepos.application.knowledge.confidence import INSUFFICIENT_EVIDENCE_ANSWER
from prepos.application.knowledge.dto import KnowledgeSearchChunk, KnowledgeSourceSummary


def _chunk(title: str = "Polity Notes") -> KnowledgeSearchChunk:
    chunk_id = uuid4()
    return KnowledgeSearchChunk(
        chunk_id=chunk_id,
        content="Doctrine content",
        score=0.9,
        vector_score=0.9,
        keyword_score=0.8,
        source=KnowledgeSourceSummary(source_id=uuid4(), title=title, source_type="ncert"),
        metadata={},
    )


def test_extract_citations_parses_chunk_ids() -> None:
    chunk = _chunk()
    answer = f"The basic structure doctrine was established in a landmark case. [{chunk.chunk_id}]"
    citations = extract_citations(answer, context_chunks=[chunk])
    assert len(citations) == 1
    assert citations[0].chunk_id == chunk.chunk_id
    assert citations[0].source_title == "Polity Notes"


def test_extract_citations_ignores_unknown_ids() -> None:
    chunk = _chunk()
    unknown = uuid4()
    answer = f"Claim one [{unknown}] and claim two [{chunk.chunk_id}]"
    citations = extract_citations(answer, context_chunks=[chunk])
    assert len(citations) == 1
    assert citations[0].chunk_id == chunk.chunk_id


def test_validate_grounded_answer_requires_citations_for_substantive_text() -> None:
    chunk = _chunk()
    valid = f"This doctrine limits Parliament. [{chunk.chunk_id}]"
    invalid = "This doctrine limits Parliament without any citation."
    assert validate_grounded_answer(valid, context_chunks=[chunk]) is True
    assert validate_grounded_answer(invalid, context_chunks=[chunk]) is False
    assert validate_grounded_answer(INSUFFICIENT_EVIDENCE_ANSWER, context_chunks=[chunk]) is True
