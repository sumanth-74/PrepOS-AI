from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from prepos.application.security.ports import PlatformMaturityRepositoryPort
from prepos.core.logging import get_logger

logger = get_logger(__name__)


class ForecastAccuracyService:
    """Measures predicted vs actual readiness using existing forecast data (P11.9)."""

    def __init__(self, *, repository: PlatformMaturityRepositoryPort) -> None:
        self._repository = repository

    async def record_accuracy(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        predicted_readiness: float,
        actual_readiness: float,
        forecast_id: UUID | None = None,
    ) -> UUID:
        event_id = await self._repository.save_forecast_accuracy_event(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            predicted_readiness=predicted_readiness,
            actual_readiness=actual_readiness,
            forecast_id=forecast_id,
            now=datetime.now(UTC),
        )
        logger.info(
            "forecast_accuracy_recorded",
            event_id=str(event_id),
            tenant_id=str(tenant_id),
            absolute_error=abs(predicted_readiness - actual_readiness),
        )
        return event_id

    async def get_dashboard(self, *, tenant_id: UUID | None = None, days: int = 90) -> dict:
        return await self._repository.get_forecast_accuracy_dashboard(tenant_id=tenant_id, days=days)
