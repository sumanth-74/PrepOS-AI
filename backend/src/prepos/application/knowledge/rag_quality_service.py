from __future__ import annotations

import csv
import io
from datetime import UTC, datetime, timedelta
from uuid import UUID

from prepos.application.knowledge.evaluation_ports import RagQualityRepositoryPort
from prepos.application.knowledge.rag_quality_dto import (
    CitationCoverageMetrics,
    FaithfulnessMetrics,
    HallucinationMetrics,
    RagQualityResponse,
    RagQualityTrendPoint,
    RetrievalQualityMetrics,
    SourceQualityItem,
    SourceQualityMetrics,
)


class RagQualityService:
    def __init__(self, *, repository: RagQualityRepositoryPort) -> None:
        self._repository = repository

    async def get_quality_dashboard(
        self,
        *,
        tenant_id: UUID,
        period_days: int = 30,
    ) -> RagQualityResponse:
        period_days = max(1, min(period_days, 365))
        since = datetime.now(UTC) - timedelta(days=period_days)
        metrics = await self._repository.get_quality_metrics(tenant_id=tenant_id, since=since)

        retrieval_raw = metrics["retrieval"]
        faithfulness_raw = metrics["faithfulness"]
        hallucination_raw = metrics["hallucination"]
        citation_raw = metrics["citation_coverage"]
        source_raw = metrics["source_quality"]
        trends_raw = metrics["trends"]

        return RagQualityResponse(
            retrieval=RetrievalQualityMetrics(**retrieval_raw),
            faithfulness=FaithfulnessMetrics(**faithfulness_raw),
            hallucination=HallucinationMetrics(**hallucination_raw),
            citation_coverage=CitationCoverageMetrics(**citation_raw),
            source_quality=SourceQualityMetrics(
                sources=[SourceQualityItem(**item) for item in source_raw],
            ),
            trends=[RagQualityTrendPoint(**point) for point in trends_raw],
        )

    async def export_csv(self, *, tenant_id: UUID, period_days: int = 30) -> str:
        period_days = max(1, min(period_days, 365))
        since = datetime.now(UTC) - timedelta(days=period_days)
        rows = await self._repository.list_answer_evaluations_for_export(tenant_id=tenant_id, since=since)
        buffer = io.StringIO()
        writer = csv.DictWriter(
            buffer,
            fieldnames=[
                "id",
                "query",
                "answer",
                "citation_count",
                "citation_coverage",
                "support_score",
                "hallucination_score",
                "confidence",
                "source_types",
                "created_at",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "id": str(row.id),
                    "query": row.query,
                    "answer": row.answer,
                    "citation_count": row.citation_count,
                    "citation_coverage": row.citation_coverage,
                    "support_score": row.support_score,
                    "hallucination_score": row.hallucination_score,
                    "confidence": row.confidence,
                    "source_types": ",".join(row.source_types),
                    "created_at": row.created_at.isoformat(),
                }
            )
        return buffer.getvalue()
