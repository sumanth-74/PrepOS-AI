from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class QueryEvaluationRecord:
    id: UUID
    tenant_id: UUID
    query: str
    source_type: str | None
    retrieved_chunk_ids: tuple[str, ...]
    relevant_chunk_ids: tuple[str, ...]
    recall_at_5: float
    recall_at_8: float
    precision_at_5: float
    precision_at_8: float
    mrr: float
    ndcg: float
    created_at: datetime


@dataclass(frozen=True, slots=True)
class AnswerEvaluationRecord:
    id: UUID
    tenant_id: UUID
    query: str
    answer: str
    citation_count: int
    citation_coverage: float
    support_score: float
    hallucination_score: float
    confidence: str
    source_types: tuple[str, ...]
    query_evaluation_id: UUID | None
    created_at: datetime


class RagQualityRepositoryPort(ABC):
    @abstractmethod
    async def save_query_evaluation(
        self,
        *,
        tenant_id: UUID,
        query: str,
        source_type: str | None,
        retrieved_chunk_ids: list[str],
        relevant_chunk_ids: list[str],
        recall_at_5: float,
        recall_at_8: float,
        precision_at_5: float,
        precision_at_8: float,
        mrr: float,
        ndcg: float,
        created_at: datetime,
    ) -> QueryEvaluationRecord:
        raise NotImplementedError

    @abstractmethod
    async def save_answer_evaluation(
        self,
        *,
        tenant_id: UUID,
        query: str,
        answer: str,
        citation_count: int,
        citation_coverage: float,
        support_score: float,
        hallucination_score: float,
        confidence: str,
        source_types: list[str],
        query_evaluation_id: UUID | None,
        created_at: datetime,
    ) -> AnswerEvaluationRecord:
        raise NotImplementedError

    @abstractmethod
    async def get_quality_metrics(
        self,
        *,
        tenant_id: UUID,
        since: datetime,
    ) -> dict[str, object]:
        raise NotImplementedError

    @abstractmethod
    async def list_answer_evaluations_for_export(
        self,
        *,
        tenant_id: UUID,
        since: datetime,
    ) -> list[AnswerEvaluationRecord]:
        raise NotImplementedError
