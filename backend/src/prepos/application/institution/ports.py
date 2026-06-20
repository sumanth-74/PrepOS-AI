from __future__ import annotations

from datetime import datetime
from uuid import UUID


class InstitutionRepositoryPort:
    async def load_institution_data(self, *, tenant_id: UUID) -> dict[str, object]:
        raise NotImplementedError

    async def save_insights(
        self,
        *,
        tenant_id: UUID,
        insights: list[dict[str, object]],
        now: datetime,
    ) -> None:
        raise NotImplementedError

    async def save_recommendations(
        self,
        *,
        tenant_id: UUID,
        recommendations: list[dict[str, object]],
        now: datetime,
    ) -> None:
        raise NotImplementedError

    async def save_trends(
        self,
        *,
        tenant_id: UUID,
        trends: list[dict[str, object]],
        now: datetime,
    ) -> None:
        raise NotImplementedError

    async def record_event(
        self,
        *,
        tenant_id: UUID,
        event_type: str,
        metadata_json: dict[str, object],
        now: datetime,
    ) -> UUID:
        raise NotImplementedError

    async def list_insights(
        self,
        *,
        tenant_id: UUID,
        limit: int,
    ) -> list[dict[str, object]]:
        raise NotImplementedError

    async def list_recommendations(
        self,
        *,
        tenant_id: UUID,
        limit: int,
    ) -> list[dict[str, object]]:
        raise NotImplementedError

    async def list_trends(
        self,
        *,
        tenant_id: UUID,
        period: str | None,
        limit: int,
    ) -> list[dict[str, object]]:
        raise NotImplementedError

    async def get_admin_metrics(self, *, tenant_id: UUID) -> dict[str, object]:
        raise NotImplementedError

    async def export_rows(self, *, tenant_id: UUID, limit: int) -> list[dict[str, object]]:
        raise NotImplementedError
