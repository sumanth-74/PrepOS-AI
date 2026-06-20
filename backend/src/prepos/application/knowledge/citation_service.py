from __future__ import annotations

import re
from uuid import UUID

from prepos.application.knowledge.confidence import INSUFFICIENT_EVIDENCE_ANSWER
from prepos.application.knowledge.dto import KnowledgeAskCitation, KnowledgeSearchChunk

_CITATION_PATTERN = re.compile(
    r"\[([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\]",
    re.IGNORECASE,
)


def extract_citations(
    answer: str,
    *,
    context_chunks: list[KnowledgeSearchChunk],
) -> list[KnowledgeAskCitation]:
    if answer.strip() == INSUFFICIENT_EVIDENCE_ANSWER:
        return []

    title_by_id = {
        chunk.chunk_id: (
            chunk.source.title,
            chunk.source.source_type,
            chunk.source.published_at,
            chunk.metadata.get("year"),
            chunk.metadata.get("paper"),
        )
        for chunk in context_chunks
    }
    seen: set[UUID] = set()
    citations: list[KnowledgeAskCitation] = []

    for match in _CITATION_PATTERN.finditer(answer):
        chunk_id = UUID(match.group(1))
        if chunk_id not in title_by_id or chunk_id in seen:
            continue
        seen.add(chunk_id)
        title, source_type, published_at, pyq_year_raw, pyq_paper_raw = title_by_id[chunk_id]
        pyq_year = int(pyq_year_raw) if isinstance(pyq_year_raw, int) else None
        if pyq_year is None and isinstance(pyq_year_raw, str) and pyq_year_raw.isdigit():
            pyq_year = int(pyq_year_raw)
        pyq_paper = str(pyq_paper_raw) if pyq_paper_raw is not None else None
        citations.append(
            KnowledgeAskCitation(
                chunk_id=chunk_id,
                source_title=title,
                source_type=source_type,
                published_at=published_at,
                pyq_year=pyq_year,
                pyq_paper=pyq_paper,
            )
        )
    return citations


def validate_grounded_answer(
    answer: str,
    *,
    context_chunks: list[KnowledgeSearchChunk],
) -> bool:
    normalized = answer.strip()
    if normalized == INSUFFICIENT_EVIDENCE_ANSWER:
        return True
    if not context_chunks:
        return False

    citations = extract_citations(answer, context_chunks=context_chunks)
    if not citations:
        return False

    substantive = _strip_citations(normalized)
    return len(substantive.split()) >= 3


def _strip_citations(text: str) -> str:
    return _CITATION_PATTERN.sub("", text).strip()
