from __future__ import annotations

from datetime import date, datetime
from typing import Protocol
from uuid import UUID


class ForecastingRepositoryPort(Protocol):
    async def create_forecast(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        student_id: UUID,
        goal_id: UUID,
        exam_id: str,
        forecast_date: date,
        target_date: date,
        current_readiness: float,
        projected_readiness: float,
        target_readiness: float,
        probability_of_success: float,
        forecast_status: str,
        top_drivers: list[str],
        metadata_json: dict[str, object],
        now: datetime,
    ) -> UUID: ...

    async def create_scenarios(
        self,
        *,
        forecast_id: UUID,
        scenarios: list[dict[str, object]],
        now: datetime,
    ) -> list[UUID]: ...

    async def get_current_forecast(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        exam_id: str,
    ) -> dict[str, object] | None: ...

    async def list_scenarios(self, *, forecast_id: UUID) -> list[dict[str, object]]: ...

    async def list_forecast_history(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        exam_id: str,
        limit: int,
    ) -> list[dict[str, object]]: ...

    async def record_event(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID | None,
        student_id: UUID | None,
        forecast_id: UUID | None,
        scenario_id: UUID | None,
        event_type: str,
        metadata_json: dict[str, object],
        created_at: datetime,
    ) -> UUID: ...

    async def get_admin_metrics(self, *, tenant_id: UUID) -> dict[str, object]: ...

    async def export_rows(self, *, tenant_id: UUID, limit: int) -> list[dict[str, object]]: ...
