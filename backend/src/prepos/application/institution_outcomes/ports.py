from __future__ import annotations

from datetime import datetime
from uuid import UUID


class InstitutionOutcomeRepositoryPort:
    async def load_cohort_snapshot_metrics(self, *, tenant_id: UUID) -> dict[str, object]:
        raise NotImplementedError

    async def create_initiative(
        self,
        *,
        tenant_id: UUID,
        payload: dict[str, object],
        now: datetime,
    ) -> dict[str, object]:
        raise NotImplementedError

    async def list_initiatives(
        self,
        *,
        tenant_id: UUID,
        status: str | None,
        limit: int,
    ) -> list[dict[str, object]]:
        raise NotImplementedError

    async def get_initiative(
        self,
        *,
        tenant_id: UUID,
        initiative_id: UUID,
    ) -> dict[str, object] | None:
        raise NotImplementedError

    async def update_initiative_outcomes(
        self,
        *,
        tenant_id: UUID,
        initiative_id: UUID,
        actual_outcomes: dict[str, object],
        now: datetime,
    ) -> None:
        raise NotImplementedError

    async def save_outcomes(
        self,
        *,
        tenant_id: UUID,
        outcomes: list[dict[str, object]],
        now: datetime,
    ) -> None:
        raise NotImplementedError

    async def save_roi_metrics(
        self,
        *,
        tenant_id: UUID,
        metrics: list[dict[str, object]],
        now: datetime,
    ) -> None:
        raise NotImplementedError

    async def save_effectiveness(
        self,
        *,
        tenant_id: UUID,
        rows: list[dict[str, object]],
        now: datetime,
    ) -> None:
        raise NotImplementedError

    async def list_outcomes(
        self,
        *,
        tenant_id: UUID,
        limit: int,
    ) -> list[dict[str, object]]:
        raise NotImplementedError

    async def list_roi_metrics(
        self,
        *,
        tenant_id: UUID,
        limit: int,
    ) -> list[dict[str, object]]:
        raise NotImplementedError

    async def list_effectiveness(
        self,
        *,
        tenant_id: UUID,
        limit: int,
    ) -> list[dict[str, object]]:
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

    async def export_roi_rows(self, *, tenant_id: UUID, limit: int) -> list[dict[str, object]]:
        raise NotImplementedError
