from __future__ import annotations

from uuid import uuid4

import pytest

from prepos.application.knowledge.evaluation_service import KnowledgeEvaluationService
from prepos.application.knowledge.dto import KnowledgeSearchChunk, KnowledgeSourceSummary


class InMemoryRagQualityRepository:
    def __init__(self) -> None:
        self.query_rows: list[dict[str, object]] = []
        self.answer_rows: list[dict[str, object]] = []

    async def save_query_evaluation(self, **kwargs: object) -> object:
        from prepos.application.knowledge.evaluation_ports import QueryEvaluationRecord
        from datetime import UTC, datetime

        record = QueryEvaluationRecord(
            id=uuid4(),
            tenant_id=kwargs["tenant_id"],  # type: ignore[arg-type]
            query=str(kwargs["query"]),
            source_type=kwargs.get("source_type"),  # type: ignore[arg-type]
            retrieved_chunk_ids=tuple(kwargs["retrieved_chunk_ids"]),  # type: ignore[arg-type]
            relevant_chunk_ids=tuple(kwargs["relevant_chunk_ids"]),  # type: ignore[arg-type]
            recall_at_5=float(kwargs["recall_at_5"]),  # type: ignore[arg-type]
            recall_at_8=float(kwargs["recall_at_8"]),  # type: ignore[arg-type]
            precision_at_5=float(kwargs["precision_at_5"]),  # type: ignore[arg-type]
            precision_at_8=float(kwargs["precision_at_8"]),  # type: ignore[arg-type]
            mrr=float(kwargs["mrr"]),  # type: ignore[arg-type]
            ndcg=float(kwargs["ndcg"]),  # type: ignore[arg-type]
            created_at=kwargs.get("created_at") or datetime.now(UTC),  # type: ignore[arg-type]
        )
        self.query_rows.append(kwargs)
        return record

    async def save_answer_evaluation(self, **kwargs: object) -> object:
        from prepos.application.knowledge.evaluation_ports import AnswerEvaluationRecord
        from datetime import UTC, datetime

        record = AnswerEvaluationRecord(
            id=uuid4(),
            tenant_id=kwargs["tenant_id"],  # type: ignore[arg-type]
            query=str(kwargs["query"]),
            answer=str(kwargs["answer"]),
            citation_count=int(kwargs["citation_count"]),  # type: ignore[arg-type]
            citation_coverage=float(kwargs["citation_coverage"]),  # type: ignore[arg-type]
            support_score=float(kwargs["support_score"]),  # type: ignore[arg-type]
            hallucination_score=float(kwargs["hallucination_score"]),  # type: ignore[arg-type]
            confidence=str(kwargs["confidence"]),
            source_types=tuple(kwargs["source_types"]),  # type: ignore[arg-type]
            query_evaluation_id=kwargs.get("query_evaluation_id"),  # type: ignore[arg-type]
            created_at=kwargs.get("created_at") or datetime.now(UTC),  # type: ignore[arg-type]
        )
        self.answer_rows.append(kwargs)
        return record

    async def get_quality_metrics(self, *, tenant_id: object, since: object) -> dict[str, object]:
        del tenant_id, since
        return {
            "retrieval": {
                "recall_at_5": 1.0,
                "recall_at_8": 1.0,
                "precision_at_5": 1.0,
                "precision_at_8": 1.0,
                "mrr": 1.0,
                "ndcg": 1.0,
                "evaluation_count": len(self.query_rows),
            },
            "faithfulness": {
                "avg_support_score": 80.0,
                "avg_citation_coverage": 100.0,
                "evaluation_count": len(self.answer_rows),
            },
            "hallucination": {
                "avg_hallucination_score": 5.0,
                "high_hallucination_rate": 0.0,
                "evaluation_count": len(self.answer_rows),
            },
            "citation_coverage": {
                "avg_citation_coverage": 100.0,
                "avg_citation_count": 1.0,
                "evaluation_count": len(self.answer_rows),
            },
            "source_quality": [],
            "trends": [],
        }

    async def list_answer_evaluations_for_export(self, *, tenant_id: object, since: object) -> list[object]:
        del tenant_id, since
        return []


def _chunk(content: str, source_type: str = "ncert") -> KnowledgeSearchChunk:
    return KnowledgeSearchChunk(
        chunk_id=uuid4(),
        content=content,
        score=0.9,
        vector_score=0.9,
        keyword_score=0.8,
        source=KnowledgeSourceSummary(source_id=uuid4(), title="Notes", source_type=source_type),
        metadata={},
    )


@pytest.mark.asyncio
async def test_evaluation_service_persists_retrieval_and_answer_metrics() -> None:
    repo = InMemoryRagQualityRepository()
    service = KnowledgeEvaluationService(repository=repo)  # type: ignore[arg-type]
    chunk = _chunk("Federalism divides powers between centre and states in India.")
    chunk_id = chunk.chunk_id
    answer = f"Federalism divides powers between centre and states. [{chunk_id}]"

    scores = await service.evaluate_answer(
        tenant_id=uuid4(),
        query="Explain federalism",
        answer=answer,
        confidence="high",
        citation_count=1,
        retrieved_chunks=[chunk],
        relevant_chunks=[chunk],
        source_types=["ncert"],
    )

    assert repo.query_rows
    assert repo.answer_rows
    assert scores["citation_coverage"] == 100.0
    assert scores["support_score"] >= 50.0
    assert scores["hallucination_score"] <= 30.0
