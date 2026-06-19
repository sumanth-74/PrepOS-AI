from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from prepos.domain.twin.snapshot_entities import PreparationTwin


class TwinSnapshotRepositoryPort(ABC):
    @abstractmethod
    async def upsert_snapshot(self, snapshot: PreparationTwin) -> PreparationTwin:
        raise NotImplementedError

    @abstractmethod
    async def get_snapshot(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> PreparationTwin | None:
        raise NotImplementedError

    @abstractmethod
    async def get_snapshot_for_student(
        self,
        tenant_id: UUID,
        student_id: UUID,
    ) -> PreparationTwin | None:
        raise NotImplementedError

    @abstractmethod
    async def resolve_twin_id(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> UUID | None:
        raise NotImplementedError
