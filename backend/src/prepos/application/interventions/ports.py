from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID


class InterventionRepositoryPort(Protocol):
    async def create_recommendations(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        recommendations: list[dict[str, object]],
        now: datetime,
    ) -> list[UUID]: ...

    async def create_intervention(
        self,
        *,
        tenant_id: UUID,
        mentor_id: UUID,
        student_id: UUID,
        exam_id: str,
        intervention_type: str,
        concept_id: str | None,
        reason: str,
        predicted_gain: float,
        priority_score: float,
        status: str,
        metadata_json: dict[str, object],
        now: datetime,
    ) -> UUID: ...

    async def get_intervention(
        self,
        *,
        tenant_id: UUID,
        intervention_id: UUID,
    ) -> dict[str, object] | None: ...

    async def list_student_interventions(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str | None,
        limit: int,
    ) -> list[dict[str, object]]: ...

    async def list_student_recommendations(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        limit: int,
    ) -> list[dict[str, object]]: ...

    async def list_student_history(
        self,
        *,
        tenant_id: UUID,
        student_user_id: UUID,
        exam_id: str | None,
        limit: int,
    ) -> list[dict[str, object]]: ...

    async def list_mentor_queue(
        self,
        *,
        tenant_id: UUID,
        mentor_id: UUID,
        limit: int,
    ) -> list[dict[str, object]]: ...

    async def update_intervention_status(
        self,
        *,
        tenant_id: UUID,
        intervention_id: UUID,
        status: str,
    ) -> None: ...

    async def record_effectiveness(
        self,
        *,
        intervention_id: UUID,
        readiness_before: float,
        readiness_after: float,
        actual_gain: float,
        effectiveness_score: float,
        now: datetime,
    ) -> UUID: ...

    async def get_effectiveness_history(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        limit: int,
    ) -> list[dict[str, object]]: ...

    async def get_admin_metrics(self, *, tenant_id: UUID) -> dict[str, object]: ...

    async def export_rows(self, *, tenant_id: UUID, limit: int) -> list[dict[str, object]]: ...
