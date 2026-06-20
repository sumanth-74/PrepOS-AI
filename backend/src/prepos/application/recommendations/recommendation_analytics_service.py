from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import structlog

from prepos.application.recommendations.ports import RecommendationAnalyticsRepositoryPort
from prepos.application.recommendations.recommendation_models import RecommendationAnalyticsResponse

logger = structlog.get_logger(__name__)


class RecommendationAnalyticsService:
    def __init__(self, *, repository: RecommendationAnalyticsRepositoryPort) -> None:
        self._repository = repository

    async def record_clicked(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID | None,
        student_id: UUID,
        concept_id: str,
        impact_score: float | None = None,
        estimated_gain: float | None = None,
    ) -> None:
        await self._repository.record_event(
            tenant_id=tenant_id,
            user_id=user_id,
            student_id=student_id,
            event_type="recommendation_clicked",
            concept_id=concept_id,
            impact_score=impact_score,
            estimated_gain=estimated_gain,
            readiness_gain_after=None,
            metadata_json={},
            created_at=datetime.now(UTC),
        )
        logger.info(
            "recommendation_viewed",
            tenant_id=str(tenant_id),
            user_id=str(user_id) if user_id else None,
            concept_id=concept_id,
            impact_score=impact_score,
            estimated_gain=estimated_gain,
        )

    async def record_completed(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID | None,
        student_id: UUID,
        concept_id: str,
        readiness_gain_after: float | None = None,
    ) -> None:
        await self._repository.record_event(
            tenant_id=tenant_id,
            user_id=user_id,
            student_id=student_id,
            event_type="recommendation_completed",
            concept_id=concept_id,
            impact_score=None,
            estimated_gain=None,
            readiness_gain_after=readiness_gain_after,
            metadata_json={},
            created_at=datetime.now(UTC),
        )
        logger.info(
            "recommendation_completed",
            tenant_id=str(tenant_id),
            user_id=str(user_id) if user_id else None,
            concept_id=concept_id,
            readiness_gain_after=readiness_gain_after,
        )

    async def get_analytics(
        self,
        *,
        tenant_id: UUID,
        period_days: int = 30,
    ) -> RecommendationAnalyticsResponse:
        period_days = max(1, min(period_days, 365))
        since = datetime.now(UTC) - timedelta(days=period_days)
        metrics = await self._repository.get_metrics(tenant_id=tenant_id, since=since)
        logger.info(
            "recommendation_effectiveness_calculated",
            tenant_id=str(tenant_id),
            period_days=period_days,
            recommendation_effectiveness=metrics["recommendation_effectiveness"],
        )
        return RecommendationAnalyticsResponse(
            recommendation_acceptance_rate=float(metrics["recommendation_acceptance_rate"]),
            completion_rate=float(metrics["completion_rate"]),
            average_readiness_gain=float(metrics["average_readiness_gain"]),
            top_recommended_concepts=list(metrics["top_recommended_concepts"]),
            recommendation_effectiveness=float(metrics["recommendation_effectiveness"]),
        )
