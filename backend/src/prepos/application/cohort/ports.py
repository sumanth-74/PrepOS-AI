from __future__ import annotations

from datetime import date, datetime
from typing import Protocol
from uuid import UUID


class CohortRepositoryPort(Protocol):
    async def list_cohort_student_rows(
        self,
        *,
        tenant_id: UUID,
        exam_id: str,
    ) -> list[dict[str, object]]: ...

    async def save_snapshot(
        self,
        *,
        tenant_id: UUID,
        cohort_id: str,
        exam_id: str,
        snapshot_date: date,
        student_count: int,
        avg_readiness: float,
        avg_forecast: float,
        avg_effectiveness: float,
        risk_count: int,
        segment_counts: dict[str, int],
        metadata_json: dict[str, object],
        now: datetime,
    ) -> UUID: ...

    async def save_segments(
        self,
        *,
        tenant_id: UUID,
        cohort_id: str,
        segments: list[dict[str, object]],
        now: datetime,
    ) -> None: ...

    async def save_trends(
        self,
        *,
        tenant_id: UUID,
        cohort_id: str,
        trends: list[dict[str, object]],
        now: datetime,
    ) -> None: ...

    async def record_event(
        self,
        *,
        tenant_id: UUID,
        cohort_id: str | None,
        event_type: str,
        metadata_json: dict[str, object],
        now: datetime,
    ) -> UUID: ...

    async def get_latest_snapshot(
        self,
        *,
        tenant_id: UUID,
        cohort_id: str,
    ) -> dict[str, object] | None: ...

    async def get_previous_snapshot(
        self,
        *,
        tenant_id: UUID,
        cohort_id: str,
        before_date: date,
    ) -> dict[str, object] | None: ...

    async def list_segments(
        self,
        *,
        tenant_id: UUID,
        cohort_id: str,
        segment_type: str | None,
        limit: int,
    ) -> list[dict[str, object]]: ...

    async def list_trends(
        self,
        *,
        tenant_id: UUID,
        cohort_id: str,
        period: str | None,
        limit: int,
    ) -> list[dict[str, object]]: ...

    async def get_admin_metrics(self, *, tenant_id: UUID) -> dict[str, object]: ...

    async def export_rows(self, *, tenant_id: UUID, limit: int) -> list[dict[str, object]]: ...
