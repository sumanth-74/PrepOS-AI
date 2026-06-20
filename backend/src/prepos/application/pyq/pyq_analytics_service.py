from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime, timedelta
from uuid import UUID

from prepos.application.pyq.dto import PyqAnalyticsResponse


class PyqAnalyticsRepositoryPort(ABC):
    @abstractmethod
    async def record_event(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID | None,
        event_type: str,
        query_text: str,
        intent: str | None,
        citation_count: int,
        confidence: str | None,
        pyq_boost_applied: bool,
        pyq_retrieval_success: bool,
        concept_id: str | None,
        created_at: datetime,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_metrics(
        self,
        *,
        tenant_id: UUID,
        since: datetime,
    ) -> dict[str, int | float]:
        raise NotImplementedError


class PyqAnalyticsService:
    def __init__(self, *, repo: PyqAnalyticsRepositoryPort) -> None:
        self._repo = repo

    async def record_search(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID | None,
        query_text: str,
        intent: str | None,
        citation_count: int,
        confidence: str | None,
        pyq_boost_applied: bool,
        pyq_retrieval_success: bool,
        concept_id: str | None = None,
    ) -> None:
        await self._repo.record_event(
            tenant_id=tenant_id,
            user_id=user_id,
            event_type="pyq_queries",
            query_text=query_text.strip(),
            intent=intent,
            citation_count=citation_count,
            confidence=confidence,
            pyq_boost_applied=pyq_boost_applied,
            pyq_retrieval_success=pyq_retrieval_success,
            concept_id=concept_id,
            created_at=datetime.now(UTC),
        )

    async def record_revision_recommendation(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID | None,
        query_text: str,
        concept_id: str | None = None,
    ) -> None:
        await self._repo.record_event(
            tenant_id=tenant_id,
            user_id=user_id,
            event_type="pyq_revision_recommendations",
            query_text=query_text.strip(),
            intent="concept_revision_strategy",
            citation_count=0,
            confidence=None,
            pyq_boost_applied=True,
            pyq_retrieval_success=True,
            concept_id=concept_id,
            created_at=datetime.now(UTC),
        )

    async def get_analytics(
        self,
        *,
        tenant_id: UUID,
        period_days: int = 30,
    ) -> PyqAnalyticsResponse:
        period_days = max(1, min(period_days, 365))
        since = datetime.now(UTC) - timedelta(days=period_days)
        metrics = await self._repo.get_metrics(tenant_id=tenant_id, since=since)
        return PyqAnalyticsResponse(
            pyq_queries=int(metrics["pyq_queries"]),
            pyq_citation_rate=float(metrics["pyq_citation_rate"]),
            pyq_topic_frequency_avg=float(metrics["pyq_topic_frequency_avg"]),
            pyq_revision_recommendations=int(metrics["pyq_revision_recommendations"]),
        )
