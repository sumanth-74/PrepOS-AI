from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from prepos.application.knowledge.current_affairs_analytics_service import (
    CurrentAffairsAnalyticsRepositoryPort,
)
from prepos.infrastructure.db.models.current_affairs_analytics import CurrentAffairsQueryEventModel


class SqlAlchemyCurrentAffairsAnalyticsRepository(CurrentAffairsAnalyticsRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

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
        row = CurrentAffairsQueryEventModel(
            id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            event_type=event_type,
            query_text=query_text,
            citation_count=citation_count,
            confidence=confidence,
            recency_boost_applied=recency_boost_applied,
            recency_retrieval_success=recency_retrieval_success,
            created_at=created_at,
        )
        self._session.add(row)
        await self._session.flush()

    async def get_metrics(
        self,
        *,
        tenant_id: UUID,
        since: datetime,
    ) -> dict[str, int | float]:
        base_filters = (
            CurrentAffairsQueryEventModel.tenant_id == tenant_id,
            CurrentAffairsQueryEventModel.created_at >= since,
        )
        total_stmt = select(func.count()).select_from(CurrentAffairsQueryEventModel).where(*base_filters)
        total = int((await self._session.execute(total_stmt)).scalar_one())

        citation_stmt = select(func.count()).select_from(CurrentAffairsQueryEventModel).where(
            *base_filters,
            CurrentAffairsQueryEventModel.citation_count > 0,
        )
        citation_count = int((await self._session.execute(citation_stmt)).scalar_one())

        recency_success_stmt = select(func.count()).select_from(CurrentAffairsQueryEventModel).where(
            *base_filters,
            CurrentAffairsQueryEventModel.recency_retrieval_success.is_(True),
        )
        recency_success = int((await self._session.execute(recency_success_stmt)).scalar_one())

        recency_boost_stmt = select(func.count()).select_from(CurrentAffairsQueryEventModel).where(
            *base_filters,
            CurrentAffairsQueryEventModel.recency_boost_applied.is_(True),
        )
        recency_boost = int((await self._session.execute(recency_boost_stmt)).scalar_one())

        return {
            "current_affairs_qna_count": total,
            "article_citation_usage_count": citation_count,
            "article_citation_usage_rate": (citation_count / total) if total > 0 else 0.0,
            "recency_retrieval_success_rate": (recency_success / total) if total > 0 else 0.0,
            "recency_boost_usage_rate": (recency_boost / total) if total > 0 else 0.0,
        }
