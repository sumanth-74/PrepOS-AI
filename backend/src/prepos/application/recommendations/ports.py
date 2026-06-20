from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID


class RecommendationAnalyticsRepositoryPort(ABC):
    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
    async def get_metrics(
        self,
        *,
        tenant_id: UUID,
        since: datetime,
    ) -> dict[str, object]:
        raise NotImplementedError
