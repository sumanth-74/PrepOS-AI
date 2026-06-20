from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime
from uuid import UUID


class RecommendationOutcomeRepositoryPort(ABC):
    @abstractmethod
    async def get_latest_shown_event(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        concept_id: str,
    ) -> dict[str, object] | None:
        raise NotImplementedError

    @abstractmethod
    async def get_pending_shown_events(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        as_of: datetime,
        min_age_days: int,
    ) -> list[dict[str, object]]:
        raise NotImplementedError

    @abstractmethod
    async def outcome_exists_for_event(self, *, recommendation_event_id: UUID) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def create_outcome(
        self,
        *,
        recommendation_event_id: UUID,
        tenant_id: UUID,
        user_id: UUID | None,
        student_id: UUID | None,
        concept_id: str,
        readiness_before: float | None,
        readiness_after: float | None,
        forecast_before: float | None,
        forecast_after: float | None,
        weakness_before: float | None,
        weakness_after: float | None,
        study_minutes: int,
        predicted_gain: float | None,
        actual_gain: float | None,
        effectiveness_score: float | None,
        status: str,
        created_at: datetime,
    ) -> UUID:
        raise NotImplementedError

    @abstractmethod
    async def list_outcomes(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID | None = None,
        user_id: UUID | None = None,
        concept_id: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, object]]:
        raise NotImplementedError

    @abstractmethod
    async def get_outcome_by_concept(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        concept_id: str,
    ) -> dict[str, object] | None:
        raise NotImplementedError

    @abstractmethod
    async def get_concept_effectiveness_stats(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID | None = None,
        concept_id: str | None = None,
        since: datetime | None = None,
    ) -> list[dict[str, object]]:
        raise NotImplementedError

    @abstractmethod
    async def upsert_daily_metric(
        self,
        *,
        tenant_id: UUID,
        metric_date: date,
        concept_id: str,
        predicted_gain: float,
        actual_gain: float,
        effectiveness_score: float,
        is_completion: bool,
        now: datetime,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_admin_effectiveness_metrics(
        self,
        *,
        tenant_id: UUID,
        since: datetime,
    ) -> dict[str, object]:
        raise NotImplementedError
