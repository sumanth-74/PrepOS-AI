from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from prepos.application.memory.memory_builder import MemoryBuilder
from prepos.application.memory.memory_context import (
    MemoryContext,
    MemoryContextBuilder,
    memories_to_timeline,
)
from prepos.application.memory.memory_models import (
    LearningTimelineResponse,
    MemoryAdminResponse,
    MemoryListResponse,
    MemoryRebuildResponse,
    MemoryRecordResponse,
    MilestoneListResponse,
)
from prepos.application.memory.ports import MemoryRepositoryPort

logger = structlog.get_logger(__name__)


class CoachingMemoryService:
    def __init__(
        self,
        *,
        repository: MemoryRepositoryPort,
        session: AsyncSession,
        context_builder: MemoryContextBuilder | None = None,
    ) -> None:
        self._repository = repository
        self._session = session
        self._context_builder = context_builder or MemoryContextBuilder()
        self._last_rebuild_at: str | None = None

    async def list_memories(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        persona: str | None = None,
        memory_type: str | None = None,
        limit: int = 50,
    ) -> MemoryListResponse:
        rows = await self._repository.list_memories(
            tenant_id=tenant_id,
            user_id=user_id,
            persona=persona,
            memory_type=memory_type,
            limit=limit,
        )
        memories = [_map_memory(row) for row in rows]
        return MemoryListResponse(memories=memories, total=len(memories))

    async def get_milestones(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        limit: int = 20,
    ) -> MilestoneListResponse:
        response = await self.list_memories(
            tenant_id=tenant_id,
            user_id=user_id,
            memory_type="progress_milestones",
            limit=limit,
        )
        return MilestoneListResponse(milestones=response.memories, total=response.total)

    async def load_student_context(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
    ) -> MemoryContext:
        memories = await self.list_memories(
            tenant_id=tenant_id,
            user_id=user_id,
            persona="student",
            limit=50,
        )
        context = self._context_builder.build_student_context(memories=memories.memories)
        logger.info(
            "memory_context_loaded",
            tenant_id=str(tenant_id),
            user_id=str(user_id),
            memory_type="student",
            memory_key=f"student:{user_id}",
            memory_hits=len(context.context_lines),
        )
        return context

    async def load_mentor_context(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        student_user_id: UUID,
    ) -> MemoryContext:
        memories = await self.list_memories(
            tenant_id=tenant_id,
            user_id=student_user_id,
            persona="mentor",
            limit=100,
        )
        context = self._context_builder.build_mentor_context(memories=memories.memories)
        logger.info(
            "memory_context_loaded",
            tenant_id=str(tenant_id),
            user_id=str(user_id),
            memory_type="mentor",
            memory_key=f"mentor:{student_user_id}",
            memory_hits=len(context.context_lines),
        )
        return context

    async def rebuild_memories(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        persona: str,
        student_id: UUID,
    ) -> MemoryRebuildResponse:
        logger.info(
            "memory_rebuild_started",
            tenant_id=str(tenant_id),
            user_id=str(user_id),
            memory_type="rebuild",
            memory_key=f"user:{user_id}",
        )
        await self._repository.delete_user_memories(tenant_id=tenant_id, user_id=user_id)
        builder = MemoryBuilder(session=self._session)
        built = await builder.build_for_user(
            tenant_id=tenant_id,
            user_id=user_id,
            persona=persona,
            student_id=student_id,
        )
        now = datetime.now(UTC)
        milestone_count = 0
        for record in built:
            await self._repository.upsert_memory(
                tenant_id=tenant_id,
                user_id=user_id,
                persona=str(record["persona"]),
                memory_type=str(record["memory_type"]),
                memory_key=str(record["memory_key"]),
                memory_value=dict(record["memory_value"]),  # type: ignore[arg-type]
                now=now,
            )
            logger.info(
                "memory_created",
                tenant_id=str(tenant_id),
                user_id=str(user_id),
                memory_type=str(record["memory_type"]),
                memory_key=str(record["memory_key"]),
            )
            if record["memory_type"] == "progress_milestones":
                milestone_count += 1

        self._last_rebuild_at = now.isoformat()
        logger.info(
            "memory_rebuild_completed",
            tenant_id=str(tenant_id),
            user_id=str(user_id),
            memory_type="rebuild",
            memory_key=f"user:{user_id}",
            memories_created=len(built),
            milestones_detected=milestone_count,
        )
        return MemoryRebuildResponse(
            status="completed",
            memories_created=len(built),
            milestones_detected=milestone_count,
        )

    async def get_admin_dashboard(self, *, tenant_id: UUID) -> MemoryAdminResponse:
        metrics = await self._repository.get_admin_metrics(tenant_id=tenant_id)
        return MemoryAdminResponse(
            total_memories=int(metrics["total_memories"]),
            memory_growth_last_30_days=int(metrics["total_memories"]),
            top_memory_types=list(metrics["top_memory_types"]),
            milestone_count=int(metrics["milestone_count"]),
            last_rebuild_at=self._last_rebuild_at,
        )

    async def export_csv(self, *, tenant_id: UUID, user_id: UUID | None = None) -> str:
        if user_id is None:
            return "memory_type,memory_key,count\n"
        memories = await self.list_memories(tenant_id=tenant_id, user_id=user_id, limit=500)
        lines = ["memory_type,memory_key,updated_at"]
        for item in memories.memories:
            lines.append(f"{item.memory_type},{item.memory_key},{item.updated_at.isoformat()}")
        return "\n".join(lines) + "\n"


def _map_memory(row: dict[str, object]) -> MemoryRecordResponse:
    return MemoryRecordResponse(
        id=row["id"],  # type: ignore[arg-type]
        tenant_id=row["tenant_id"],  # type: ignore[arg-type]
        user_id=row["user_id"],  # type: ignore[arg-type]
        persona=str(row["persona"]),
        memory_type=str(row["memory_type"]),
        memory_key=str(row["memory_key"]),
        memory_value=dict(row["memory_value"]),  # type: ignore[arg-type]
        created_at=row["created_at"],  # type: ignore[arg-type]
        updated_at=row["updated_at"],  # type: ignore[arg-type]
    )


class LearningTimelineService:
    def __init__(self, *, memory_service: CoachingMemoryService) -> None:
        self._memory_service = memory_service

    async def get_timeline(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        persona: str,
        limit: int = 100,
    ) -> LearningTimelineResponse:
        memories = await self._memory_service.list_memories(
            tenant_id=tenant_id,
            user_id=user_id,
            persona=persona,
            limit=limit,
        )
        events = memories_to_timeline(memories.memories)
        return LearningTimelineResponse(events=events, total=len(events))
