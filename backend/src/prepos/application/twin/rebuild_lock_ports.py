from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

DEFAULT_TWIN_REBUILD_LOCK_TTL_SECONDS = 60


class TwinRebuildLockPort(ABC):
    @abstractmethod
    async def try_acquire_lock(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        *,
        correlation_id: str,
        ttl_seconds: int = DEFAULT_TWIN_REBUILD_LOCK_TTL_SECONDS,
    ) -> bool:
        raise NotImplementedError
