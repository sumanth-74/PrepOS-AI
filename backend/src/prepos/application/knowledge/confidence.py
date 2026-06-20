from __future__ import annotations

from typing import Literal

from prepos.application.knowledge.dto import KnowledgeSearchChunk

ConfidenceLevel = Literal["high", "medium", "low"]

INSUFFICIENT_EVIDENCE_ANSWER = (
    "I don't have enough indexed content to answer confidently."
)


def filter_relevant_chunks(
    chunks: list[KnowledgeSearchChunk],
    *,
    min_score: float,
) -> list[KnowledgeSearchChunk]:
    return [chunk for chunk in chunks if chunk.score >= min_score]


def select_prompt_chunks(
    chunks: list[KnowledgeSearchChunk],
    *,
    limit: int,
    prompt_max: int = 8,
) -> list[KnowledgeSearchChunk]:
    if not chunks:
        return []
    capped_limit = max(1, min(limit, prompt_max))
    return chunks[:capped_limit]


def score_confidence(relevant_chunk_count: int) -> ConfidenceLevel:
    if relevant_chunk_count >= 3:
        return "high"
    if relevant_chunk_count == 2:
        return "medium"
    return "low"
