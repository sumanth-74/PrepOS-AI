from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from prepos.application.memory.ports import MemoryRepositoryPort
from prepos.infrastructure.db.models.copilot_memory import CopilotMemoryModel


class SqlAlchemyMemoryRepository(MemoryRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

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
        stmt = select(CopilotMemoryModel).where(
            CopilotMemoryModel.tenant_id == tenant_id,
            CopilotMemoryModel.user_id == user_id,
            CopilotMemoryModel.memory_key == memory_key,
        )
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing is None:
            memory_id = uuid4()
            self._session.add(
                CopilotMemoryModel(
                    id=memory_id,
                    tenant_id=tenant_id,
                    user_id=user_id,
                    persona=persona,
                    memory_type=memory_type,
                    memory_key=memory_key,
                    memory_value=memory_value,
                    created_at=now,
                    updated_at=now,
                )
            )
            await self._session.flush()
            return memory_id

        existing.memory_type = memory_type
        existing.persona = persona
        existing.memory_value = memory_value
        existing.updated_at = now
        await self._session.flush()
        return existing.id

    async def list_memories(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        persona: str | None = None,
        memory_type: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, object]]:
        filters = [
            CopilotMemoryModel.tenant_id == tenant_id,
            CopilotMemoryModel.user_id == user_id,
        ]
        if persona is not None:
            filters.append(CopilotMemoryModel.persona == persona)
        if memory_type is not None:
            filters.append(CopilotMemoryModel.memory_type == memory_type)
        stmt = (
            select(CopilotMemoryModel)
            .where(and_(*filters))
            .order_by(CopilotMemoryModel.updated_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [_to_dict(row) for row in result.scalars()]

    async def delete_user_memories(self, *, tenant_id: UUID, user_id: UUID) -> int:
        stmt = select(CopilotMemoryModel).where(
            CopilotMemoryModel.tenant_id == tenant_id,
            CopilotMemoryModel.user_id == user_id,
        )
        result = await self._session.execute(stmt)
        rows = list(result.scalars())
        for row in rows:
            await self._session.delete(row)
        await self._session.flush()
        return len(rows)

    async def get_admin_metrics(self, *, tenant_id: UUID) -> dict[str, object]:
        stmt = select(CopilotMemoryModel).where(CopilotMemoryModel.tenant_id == tenant_id)
        result = await self._session.execute(stmt)
        rows = list(result.scalars())
        type_counts: dict[str, int] = {}
        milestone_count = 0
        for row in rows:
            type_counts[row.memory_type] = type_counts.get(row.memory_type, 0) + 1
            if row.memory_type == "progress_milestones":
                milestone_count += 1
        top_types = [
            {"memory_type": memory_type, "count": count}
            for memory_type, count in sorted(type_counts.items(), key=lambda item: item[1], reverse=True)[:10]
        ]
        return {
            "total_memories": len(rows),
            "milestone_count": milestone_count,
            "top_memory_types": top_types,
        }


def _to_dict(row: CopilotMemoryModel) -> dict[str, object]:
    return {
        "id": row.id,
        "tenant_id": row.tenant_id,
        "user_id": row.user_id,
        "persona": row.persona,
        "memory_type": row.memory_type,
        "memory_key": row.memory_key,
        "memory_value": dict(row.memory_value or {}),
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }
