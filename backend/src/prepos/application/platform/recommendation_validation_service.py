from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from prepos.application.security.ports import PlatformMaturityRepositoryPort
from prepos.core.logging import get_logger

logger = get_logger(__name__)


class RecommendationValidationService:
    """Tracks recommendation lifecycle vs control population (P11.10)."""

    def __init__(self, *, repository: PlatformMaturityRepositoryPort) -> None:
        self._repository = repository

    async def record_event(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        event_type: str,
        recommendation_id: UUID | None = None,
        predicted_gain: float | None = None,
        actual_gain: float | None = None,
        is_control: bool = False,
        metadata: dict | None = None,
    ) -> UUID:
        event_id = await self._repository.save_recommendation_validation_event(
            tenant_id=tenant_id,
            student_id=student_id,
            recommendation_id=recommendation_id,
            event_type=event_type,
            predicted_gain=predicted_gain,
            actual_gain=actual_gain,
            is_control=is_control,
            metadata=metadata or {},
            now=datetime.now(UTC),
        )
        logger.info(
            "recommendation_validation_recorded",
            event_id=str(event_id),
            event_type=event_type,
            tenant_id=str(tenant_id),
        )
        return event_id

    async def get_dashboard(self, *, tenant_id: UUID | None = None, days: int = 90) -> dict:
        return await self._repository.get_recommendation_validation_dashboard(
            tenant_id=tenant_id,
            days=days,
        )
