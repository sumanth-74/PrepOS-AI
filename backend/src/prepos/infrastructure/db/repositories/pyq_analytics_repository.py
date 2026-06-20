from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from prepos.application.pyq.pyq_analytics_service import PyqAnalyticsRepositoryPort
from prepos.infrastructure.db.models.pyq_analytics import PyqQueryEventModel


class SqlAlchemyPyqAnalyticsRepository(PyqAnalyticsRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

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
        self._session.add(
            PyqQueryEventModel(
                id=uuid4(),
                tenant_id=tenant_id,
                user_id=user_id,
                event_type=event_type,
                query_text=query_text,
                intent=intent,
                citation_count=citation_count,
                confidence=confidence,
                pyq_boost_applied=pyq_boost_applied,
                pyq_retrieval_success=pyq_retrieval_success,
                concept_id=concept_id,
                created_at=created_at,
            )
        )
        await self._session.flush()

    async def get_metrics(
        self,
        *,
        tenant_id: UUID,
        since: datetime,
    ) -> dict[str, int | float]:
        stmt = select(PyqQueryEventModel).where(
            PyqQueryEventModel.tenant_id == tenant_id,
            PyqQueryEventModel.created_at >= since,
        )
        result = await self._session.execute(stmt)
        events = list(result.scalars())
        pyq_queries = sum(1 for event in events if event.event_type == "pyq_queries")
        revision_recs = sum(1 for event in events if event.event_type == "pyq_revision_recommendations")
        with_citations = sum(1 for event in events if event.citation_count > 0)
        citation_rate = (with_citations / pyq_queries) if pyq_queries else 0.0
        boost_usage = sum(1 for event in events if event.pyq_boost_applied)
        boost_rate = (boost_usage / pyq_queries) if pyq_queries else 0.0
        return {
            "pyq_queries": pyq_queries,
            "pyq_citation_rate": round(citation_rate, 4),
            "pyq_topic_frequency_avg": round(boost_rate, 4),
            "pyq_revision_recommendations": revision_recs,
        }
