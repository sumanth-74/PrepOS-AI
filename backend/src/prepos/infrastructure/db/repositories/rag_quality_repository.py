from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from prepos.application.knowledge.evaluation_ports import (
    AnswerEvaluationRecord,
    QueryEvaluationRecord,
    RagQualityRepositoryPort,
)
from prepos.infrastructure.db.models.rag_quality import (
    KnowledgeAnswerEvaluationModel,
    KnowledgeQueryEvaluationModel,
)

_CONFIDENCE_SCORES = {"high": 1.0, "medium": 0.66, "low": 0.33}
_SOURCE_TYPES = (
    "knowledge",
    "ncert",
    "current_affairs",
    "pib",
    "prs",
    "pyq",
    "government_scheme",
    "budget",
    "economic_survey",
    "book",
    "syllabus",
    "mentor_note",
    "upload",
)


class SqlAlchemyRagQualityRepository(RagQualityRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

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
        model = KnowledgeQueryEvaluationModel(
            id=uuid4(),
            tenant_id=tenant_id,
            query=query,
            source_type=source_type,
            retrieved_chunk_ids=retrieved_chunk_ids,
            relevant_chunk_ids=relevant_chunk_ids,
            recall_at_5=recall_at_5,
            recall_at_8=recall_at_8,
            precision_at_5=precision_at_5,
            precision_at_8=precision_at_8,
            mrr=mrr,
            ndcg=ndcg,
            created_at=created_at,
        )
        self._session.add(model)
        await self._session.flush()
        return _to_query_record(model)

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
        model = KnowledgeAnswerEvaluationModel(
            id=uuid4(),
            tenant_id=tenant_id,
            query=query,
            answer=answer,
            citation_count=citation_count,
            citation_coverage=citation_coverage,
            support_score=support_score,
            hallucination_score=hallucination_score,
            confidence=confidence,
            source_types=source_types,
            query_evaluation_id=query_evaluation_id,
            created_at=created_at,
        )
        self._session.add(model)
        await self._session.flush()
        return _to_answer_record(model)

    async def get_quality_metrics(
        self,
        *,
        tenant_id: UUID,
        since: datetime,
    ) -> dict[str, object]:
        query_stmt = select(KnowledgeQueryEvaluationModel).where(
            KnowledgeQueryEvaluationModel.tenant_id == tenant_id,
            KnowledgeQueryEvaluationModel.created_at >= since,
        )
        answer_stmt = select(KnowledgeAnswerEvaluationModel).where(
            KnowledgeAnswerEvaluationModel.tenant_id == tenant_id,
            KnowledgeAnswerEvaluationModel.created_at >= since,
        )
        query_rows = list((await self._session.execute(query_stmt)).scalars())
        answer_rows = list((await self._session.execute(answer_stmt)).scalars())

        retrieval = {
            "recall_at_5": _avg([float(row.recall_at_5) for row in query_rows]),
            "recall_at_8": _avg([float(row.recall_at_8) for row in query_rows]),
            "precision_at_5": _avg([float(row.precision_at_5) for row in query_rows]),
            "precision_at_8": _avg([float(row.precision_at_8) for row in query_rows]),
            "mrr": _avg([float(row.mrr) for row in query_rows]),
            "ndcg": _avg([float(row.ndcg) for row in query_rows]),
            "evaluation_count": len(query_rows),
        }
        faithfulness = {
            "avg_support_score": _avg([float(row.support_score) for row in answer_rows]),
            "avg_citation_coverage": _avg([float(row.citation_coverage) for row in answer_rows]),
            "evaluation_count": len(answer_rows),
        }
        hallucination_values = [float(row.hallucination_score) for row in answer_rows]
        hallucination = {
            "avg_hallucination_score": _avg(hallucination_values),
            "high_hallucination_rate": _rate(hallucination_values, threshold=60.0),
            "evaluation_count": len(answer_rows),
        }
        citation_coverage = {
            "avg_citation_coverage": _avg([float(row.citation_coverage) for row in answer_rows]),
            "avg_citation_count": _avg([float(row.citation_count) for row in answer_rows]),
            "evaluation_count": len(answer_rows),
        }
        source_quality = _aggregate_source_quality(answer_rows)
        trends = _aggregate_trends(answer_rows)
        return {
            "retrieval": retrieval,
            "faithfulness": faithfulness,
            "hallucination": hallucination,
            "citation_coverage": citation_coverage,
            "source_quality": source_quality,
            "trends": trends,
        }

    async def list_answer_evaluations_for_export(
        self,
        *,
        tenant_id: UUID,
        since: datetime,
    ) -> list[AnswerEvaluationRecord]:
        stmt = (
            select(KnowledgeAnswerEvaluationModel)
            .where(
                KnowledgeAnswerEvaluationModel.tenant_id == tenant_id,
                KnowledgeAnswerEvaluationModel.created_at >= since,
            )
            .order_by(KnowledgeAnswerEvaluationModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [_to_answer_record(row) for row in result.scalars()]


def _aggregate_source_quality(rows: list[KnowledgeAnswerEvaluationModel]) -> list[dict[str, object]]:
    by_source: dict[str, list[KnowledgeAnswerEvaluationModel]] = {source: [] for source in _SOURCE_TYPES}
    for row in rows:
        for source_type in row.source_types or []:
            normalized = str(source_type).lower()
            if normalized not in by_source:
                by_source[normalized] = []
            by_source[normalized].append(row)
        if not row.source_types:
            by_source.setdefault("knowledge", []).append(row)

    items: list[dict[str, object]] = []
    for source_type, source_rows in by_source.items():
        if not source_rows:
            continue
        items.append(
            {
                "source_type": source_type,
                "query_count": len(source_rows),
                "citation_count": sum(row.citation_count for row in source_rows),
                "avg_confidence_score": round(
                    _avg([_CONFIDENCE_SCORES.get(row.confidence, 0.33) for row in source_rows]) * 100,
                    2,
                ),
                "avg_support_score": _avg([float(row.support_score) for row in source_rows]),
                "avg_hallucination_score": _avg([float(row.hallucination_score) for row in source_rows]),
            }
        )
    items.sort(key=lambda item: int(item["query_count"]), reverse=True)
    return items


def _aggregate_trends(rows: list[KnowledgeAnswerEvaluationModel]) -> list[dict[str, object]]:
    buckets: dict[str, list[KnowledgeAnswerEvaluationModel]] = {}
    for row in rows:
        day = row.created_at.astimezone(UTC).date().isoformat()
        buckets.setdefault(day, []).append(row)
    trend_points: list[dict[str, object]] = []
    for day in sorted(buckets.keys())[-14:]:
        day_rows = buckets[day]
        trend_points.append(
            {
                "date": day,
                "avg_support_score": _avg([float(row.support_score) for row in day_rows]),
                "avg_hallucination_score": _avg([float(row.hallucination_score) for row in day_rows]),
                "avg_citation_coverage": _avg([float(row.citation_coverage) for row in day_rows]),
            }
        )
    return trend_points


def _avg(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 4)


def _rate(values: list[float], *, threshold: float) -> float:
    if not values:
        return 0.0
    hits = sum(1 for value in values if value >= threshold)
    return round(hits / len(values), 4)


def _to_query_record(model: KnowledgeQueryEvaluationModel) -> QueryEvaluationRecord:
    return QueryEvaluationRecord(
        id=model.id,
        tenant_id=model.tenant_id,
        query=model.query,
        source_type=model.source_type,
        retrieved_chunk_ids=tuple(str(item) for item in (model.retrieved_chunk_ids or [])),
        relevant_chunk_ids=tuple(str(item) for item in (model.relevant_chunk_ids or [])),
        recall_at_5=float(model.recall_at_5),
        recall_at_8=float(model.recall_at_8),
        precision_at_5=float(model.precision_at_5),
        precision_at_8=float(model.precision_at_8),
        mrr=float(model.mrr),
        ndcg=float(model.ndcg),
        created_at=model.created_at,
    )


def _to_answer_record(model: KnowledgeAnswerEvaluationModel) -> AnswerEvaluationRecord:
    return AnswerEvaluationRecord(
        id=model.id,
        tenant_id=model.tenant_id,
        query=model.query,
        answer=model.answer,
        citation_count=model.citation_count,
        citation_coverage=float(model.citation_coverage),
        support_score=float(model.support_score),
        hallucination_score=float(model.hallucination_score),
        confidence=model.confidence,
        source_types=tuple(str(item) for item in (model.source_types or [])),
        query_evaluation_id=model.query_evaluation_id,
        created_at=model.created_at,
    )
