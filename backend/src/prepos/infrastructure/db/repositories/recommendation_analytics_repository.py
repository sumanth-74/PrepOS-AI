from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from prepos.application.recommendations.ports import RecommendationAnalyticsRepositoryPort
from prepos.infrastructure.db.models.recommendation_analytics import RecommendationEventModel


class SqlAlchemyRecommendationAnalyticsRepository(RecommendationAnalyticsRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record_event(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID | None,
        student_id: UUID | None,
        event_type: str,
        concept_id: str | None,
        impact_score: float | None,
        estimated_gain: float | None,
        readiness_gain_after: float | None,
        metadata_json: dict[str, object],
        created_at: datetime,
    ) -> None:
        self._session.add(
            RecommendationEventModel(
                id=uuid4(),
                tenant_id=tenant_id,
                user_id=user_id,
                student_id=student_id,
                event_type=event_type,
                concept_id=concept_id,
                impact_score=impact_score,
                estimated_gain=estimated_gain,
                readiness_gain_after=readiness_gain_after,
                metadata_json=metadata_json,
                created_at=created_at,
            )
        )
        await self._session.flush()

    async def get_metrics(
        self,
        *,
        tenant_id: UUID,
        since: datetime,
    ) -> dict[str, object]:
        stmt = select(RecommendationEventModel).where(
            RecommendationEventModel.tenant_id == tenant_id,
            RecommendationEventModel.created_at >= since,
        )
        result = await self._session.execute(stmt)
        events = list(result.scalars())

        shown = [event for event in events if event.event_type == "recommendation_shown"]
        clicked = [
            event
            for event in events
            if event.event_type in {"recommendation_clicked", "recommendation_viewed"}
        ]
        completed = [event for event in events if event.event_type == "recommendation_completed"]

        acceptance_rate = (len(clicked) / len(shown)) if shown else 0.0
        completion_rate = (len(completed) / len(shown)) if shown else 0.0
        gains = [float(event.readiness_gain_after) for event in completed if event.readiness_gain_after is not None]
        average_gain = sum(gains) / len(gains) if gains else 0.0

        concept_counts: dict[str, int] = {}
        for event in shown:
            if event.concept_id:
                concept_counts[event.concept_id] = concept_counts.get(event.concept_id, 0) + 1
        top_concepts = [
            {"concept_id": concept_id, "count": count}
            for concept_id, count in sorted(concept_counts.items(), key=lambda item: item[1], reverse=True)[:10]
        ]

        effectiveness = round((acceptance_rate * 0.4) + (completion_rate * 0.6), 4)

        return {
            "recommendation_acceptance_rate": round(acceptance_rate, 4),
            "completion_rate": round(completion_rate, 4),
            "average_readiness_gain": round(average_gain, 2),
            "top_recommended_concepts": top_concepts,
            "recommendation_effectiveness": effectiveness,
        }
