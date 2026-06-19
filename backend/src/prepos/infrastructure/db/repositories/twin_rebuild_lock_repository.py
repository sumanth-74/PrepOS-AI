from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from prepos.application.twin.rebuild_lock_ports import TwinRebuildLockPort
from prepos.infrastructure.db.models.twin_rebuild_lock import TwinRebuildLockModel


class SqlAlchemyTwinRebuildLockRepository(TwinRebuildLockPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def try_acquire_lock(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        *,
        correlation_id: str,
        ttl_seconds: int = 60,
    ) -> bool:
        now = datetime.now(UTC)
        expires_at = now + timedelta(seconds=ttl_seconds)
        result = await self._session.execute(
            select(TwinRebuildLockModel).where(
                TwinRebuildLockModel.tenant_id == tenant_id,
                TwinRebuildLockModel.student_id == student_id,
                TwinRebuildLockModel.exam_id == exam_id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing is not None and existing.expires_at > now:
            return False

        if existing is None:
            self._session.add(
                TwinRebuildLockModel(
                    tenant_id=tenant_id,
                    student_id=student_id,
                    exam_id=exam_id,
                    correlation_id=correlation_id,
                    created_at=now,
                    expires_at=expires_at,
                )
            )
        else:
            existing.correlation_id = correlation_id
            existing.created_at = now
            existing.expires_at = expires_at

        await self._session.flush()
        return True
