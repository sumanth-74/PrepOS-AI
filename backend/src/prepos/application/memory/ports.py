from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID


class MemoryRepositoryPort(ABC):
    @abstractmethod
    async def upsert_memory(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        persona: str,
        memory_type: str,
        memory_key: str,
        memory_value: dict[str, object],
        now: datetime,
    ) -> UUID:
        raise NotImplementedError

    @abstractmethod
    async def list_memories(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        persona: str | None = None,
        memory_type: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, object]]:
        raise NotImplementedError

    @abstractmethod
    async def delete_user_memories(self, *, tenant_id: UUID, user_id: UUID) -> int:
        raise NotImplementedError

    @abstractmethod
    async def get_admin_metrics(self, *, tenant_id: UUID) -> dict[str, object]:
        raise NotImplementedError
