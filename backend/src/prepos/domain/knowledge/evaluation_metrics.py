from __future__ import annotations

import math
import re
from uuid import UUID

_CITATION_PATTERN = re.compile(
    r"\[([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\]",
    re.IGNORECASE,
)
_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def recall_at_k(relevant_ids: set[UUID], retrieved_ids: list[UUID], k: int) -> float:
    if not relevant_ids:
        return 0.0
    top_k = set(retrieved_ids[:k])
    return len(top_k & relevant_ids) / len(relevant_ids)


def precision_at_k(relevant_ids: set[UUID], retrieved_ids: list[UUID], k: int) -> float:
    top_k = retrieved_ids[:k]
    if not top_k:
        return 0.0
    hits = sum(1 for chunk_id in top_k if chunk_id in relevant_ids)
    return hits / len(top_k)


def mean_reciprocal_rank(relevant_ids: set[UUID], retrieved_ids: list[UUID]) -> float:
    for index, chunk_id in enumerate(retrieved_ids, start=1):
        if chunk_id in relevant_ids:
            return 1.0 / index
    return 0.0


def ndcg_at_k(relevant_ids: set[UUID], retrieved_ids: list[UUID], k: int) -> float:
    if not relevant_ids or k <= 0:
        return 0.0
    dcg = 0.0
    for index, chunk_id in enumerate(retrieved_ids[:k], start=1):
        if chunk_id in relevant_ids:
            dcg += 1.0 / math.log2(index + 1)
    ideal_hits = min(len(relevant_ids), k)
    idcg = sum(1.0 / math.log2(i + 1) for i in range(1, ideal_hits + 1))
    if idcg == 0:
        return 0.0
    return dcg / idcg


def split_factual_statements(answer: str) -> list[str]:
    normalized = _CITATION_PATTERN.sub("", answer).strip()
    if not normalized:
        return []
    parts = re.split(r"(?<=[.!?])\s+", normalized)
    return [part.strip() for part in parts if len(part.split()) >= 3]


def count_cited_statements(answer: str) -> int:
    factual = split_factual_statements(answer)
    if not factual:
        return 1 if _CITATION_PATTERN.search(answer) else 0
    cited = 0
    for statement in factual:
        marker = statement[: min(40, len(statement))]
        index = answer.find(marker)
        if index >= 0 and _CITATION_PATTERN.search(answer[index:]):
            cited += 1
    return cited


def citation_coverage_score(*, answer: str, citation_count: int) -> float:
    factual = split_factual_statements(answer)
    if not factual:
        return 100.0 if citation_count > 0 else 0.0
    if citation_count <= 0 or not _CITATION_PATTERN.search(answer):
        return 0.0
    cited = count_cited_statements(answer)
    coverage = (cited / len(factual)) * 100.0
    return round(min(100.0, max(0.0, coverage)), 2)


def tokenize(text: str) -> set[str]:
    return set(_TOKEN_PATTERN.findall(text.lower()))


def support_score(*, answer: str, chunk_contents: list[str]) -> float:
    answer_tokens = tokenize(_CITATION_PATTERN.sub("", answer))
    if not answer_tokens:
        return 0.0
    context_tokens: set[str] = set()
    for content in chunk_contents:
        context_tokens |= tokenize(content)
    if not context_tokens:
        return 0.0
    overlap = len(answer_tokens & context_tokens) / len(answer_tokens)
    return round(min(100.0, overlap * 100.0), 2)


def hallucination_score(
    *,
    answer: str,
    citation_coverage: float,
    support_score_value: float,
    citation_count: int,
) -> float:
    if answer.strip() == "I don't have enough indexed content to answer confidently.":
        return 0.0
    uncited_risk = max(0.0, 100.0 - citation_coverage)
    unsupported_risk = max(0.0, 100.0 - support_score_value)
    base = (uncited_risk * 0.35) + (unsupported_risk * 0.65)
    if citation_count == 0 and split_factual_statements(answer):
        base = max(base, 75.0)
    return round(min(100.0, max(0.0, base)), 2)
