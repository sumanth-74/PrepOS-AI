from __future__ import annotations

from uuid import uuid4

from prepos.application.knowledge.confidence import (
    INSUFFICIENT_EVIDENCE_ANSWER,
    filter_relevant_chunks,
    score_confidence,
    select_prompt_chunks,
)
from prepos.application.knowledge.dto import KnowledgeSearchChunk, KnowledgeSourceSummary


def _chunk(score: float) -> KnowledgeSearchChunk:
    chunk_id = uuid4()
    return KnowledgeSearchChunk(
        chunk_id=chunk_id,
        content="Sample content",
        score=score,
        vector_score=score,
        keyword_score=score,
        source=KnowledgeSourceSummary(source_id=uuid4(), title="Polity Notes", source_type="ncert"),
        metadata={},
    )


def test_score_confidence_levels() -> None:
    assert score_confidence(0) == "low"
    assert score_confidence(1) == "low"
    assert score_confidence(2) == "medium"
    assert score_confidence(3) == "high"
    assert score_confidence(10) == "high"


def test_filter_relevant_chunks_by_score() -> None:
    chunks = [_chunk(0.9), _chunk(0.1), _chunk(0.4)]
    relevant = filter_relevant_chunks(chunks, min_score=0.15)
    assert len(relevant) == 2


def test_select_prompt_chunks_respects_limit() -> None:
    chunks = [_chunk(0.9 - index * 0.01) for index in range(10)]
    selected = select_prompt_chunks(chunks, limit=8, prompt_max=8)
    assert len(selected) == 8


def test_insufficient_evidence_constant() -> None:
    assert "don't have enough indexed content" in INSUFFICIENT_EVIDENCE_ANSWER.lower()
