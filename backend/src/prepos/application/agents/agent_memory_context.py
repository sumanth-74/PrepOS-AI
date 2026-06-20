from __future__ import annotations

from uuid import UUID

from prepos.application.memory.memory_service import CoachingMemoryService


class AgentMemoryContextBuilder:
    def __init__(self, *, memory_service: CoachingMemoryService) -> None:
        self._memory_service = memory_service

    async def build(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        persona: str,
        student_user_id: UUID | None = None,
    ) -> dict[str, object]:
        if persona == "mentor" and student_user_id:
            context = await self._memory_service.load_mentor_context(
                tenant_id=tenant_id,
                user_id=user_id,
                student_user_id=student_user_id,
            )
            target_user = student_user_id
        elif persona == "student":
            context = await self._memory_service.load_student_context(
                tenant_id=tenant_id,
                user_id=user_id,
            )
            target_user = user_id
        else:
            return {"context_lines": [], "milestones": []}

        milestones = await self._memory_service.get_milestones(tenant_id=tenant_id, user_id=target_user)
        return {
            "context_lines": list(context.context_lines),
            "milestones": [item.model_dump(mode="json") for item in milestones.milestones],
        }
