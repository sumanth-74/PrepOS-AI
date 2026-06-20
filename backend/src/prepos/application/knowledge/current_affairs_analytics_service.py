from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime, timedelta
from uuid import UUID

from prepos.application.knowledge.current_affairs_dto import CurrentAffairsAnalyticsResponse


class CurrentAffairsAnalyticsRepositoryPort(ABC):
    @abstractmethod
    async def record_event(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID | None,
        event_type: str,
        query_text: str,
        citation_count: int,
        confidence: str | None,
        recency_boost_applied: bool,
        recency_retrieval_success: bool,
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


class CurrentAffairsAnalyticsService:
    def __init__(self, *, repo: CurrentAffairsAnalyticsRepositoryPort) -> None:
        self._repo = repo

    async def record_search(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID | None,
        query_text: str,
        citation_count: int,
        confidence: str | None,
        recency_boost_applied: bool,
        recency_retrieval_success: bool,
    ) -> None:
        await self._repo.record_event(
            tenant_id=tenant_id,
            user_id=user_id,
            event_type="current_affairs_qna",
            query_text=query_text.strip(),
            citation_count=citation_count,
            confidence=confidence,
            recency_boost_applied=recency_boost_applied,
            recency_retrieval_success=recency_retrieval_success,
            created_at=datetime.now(UTC),
        )

    async def get_analytics(
        self,
        *,
        tenant_id: UUID,
        period_days: int = 30,
    ) -> CurrentAffairsAnalyticsResponse:
        period_days = max(1, min(period_days, 365))
        since = datetime.now(UTC) - timedelta(days=period_days)
        metrics = await self._repo.get_metrics(tenant_id=tenant_id, since=since)
        return CurrentAffairsAnalyticsResponse(
            current_affairs_qna_count=int(metrics["current_affairs_qna_count"]),
            article_citation_usage_count=int(metrics["article_citation_usage_count"]),
            article_citation_usage_rate=float(metrics["article_citation_usage_rate"]),
            recency_retrieval_success_rate=float(metrics["recency_retrieval_success_rate"]),
            recency_boost_usage_rate=float(metrics["recency_boost_usage_rate"]),
        )
