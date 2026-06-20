from __future__ import annotations

from datetime import date, datetime
from typing import Protocol
from uuid import UUID


class PlanningRepositoryPort(Protocol):
    async def archive_active_plans(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        exam_id: str,
        now: datetime,
    ) -> None: ...

    async def create_plan_version(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        student_id: UUID,
        exam_id: str,
        generated_at: datetime,
        valid_from: date,
        valid_to: date,
        readiness_snapshot: float | None,
        forecast_snapshot: float | None,
        status: str,
        now: datetime,
    ) -> UUID: ...

    async def create_plan_items(
        self,
        *,
        plan_id: UUID,
        items: list[dict[str, object]],
        now: datetime,
    ) -> list[UUID]: ...

    async def create_revision(
        self,
        *,
        plan_id: UUID,
        concept_id: str,
        revision_reason: str,
        old_priority: float | None,
        new_priority: float | None,
        now: datetime,
    ) -> UUID: ...

    async def get_current_plan(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        exam_id: str,
    ) -> dict[str, object] | None: ...

    async def list_plan_history(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        exam_id: str,
        limit: int,
    ) -> list[dict[str, object]]: ...

    async def get_plan_item(
        self,
        *,
        tenant_id: UUID,
        item_id: UUID,
    ) -> dict[str, object] | None: ...

    async def mark_item_completed(
        self,
        *,
        tenant_id: UUID,
        item_id: UUID,
        now: datetime,
    ) -> dict[str, object] | None: ...

    async def list_revisions(
        self,
        *,
        plan_id: UUID,
        limit: int,
    ) -> list[dict[str, object]]: ...

    async def record_event(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID | None,
        student_id: UUID | None,
        plan_id: UUID | None,
        item_id: UUID | None,
        concept_id: str | None,
        event_type: str,
        priority_score: float | None,
        estimated_gain: float | None,
        metadata_json: dict[str, object],
        created_at: datetime,
    ) -> UUID: ...

    async def get_admin_metrics(self, *, tenant_id: UUID) -> dict[str, object]: ...

    async def export_rows(self, *, tenant_id: UUID, limit: int) -> list[dict[str, object]]: ...
