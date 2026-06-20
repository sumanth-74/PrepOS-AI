from __future__ import annotations

from prepos.application.agents.models import AgentContext, AgentResult
from prepos.application.agents.tools.base_tool import BaseTool
from prepos.application.memory.memory_service import CoachingMemoryService


class MemoryTool(BaseTool):
    name = "memory"

    def __init__(self, *, service: CoachingMemoryService) -> None:
        self._service = service

    async def execute(self, *, context: AgentContext) -> AgentResult:
        if context.persona == "mentor" and context.student_user_id:
            memory = await self._service.load_mentor_context(
                tenant_id=context.tenant_id,
                user_id=context.user_id,
                student_user_id=context.student_user_id,
            )
        elif context.persona == "student":
            memory = await self._service.load_student_context(
                tenant_id=context.tenant_id,
                user_id=context.user_id,
            )
        else:
            dashboard = await self._service.get_admin_dashboard(tenant_id=context.tenant_id)
            return self._success(
                data=dashboard.model_dump(mode="json"),
                reasoning="Loaded coaching memory admin dashboard.",
                label="Memory",
                reference="GET /admin/memory",
            )
        milestones = await self._service.get_milestones(
            tenant_id=context.tenant_id,
            user_id=context.student_user_id or context.user_id,
        )
        return self._success(
            data={
                "context_lines": memory.context_lines,
                "milestones": [item.model_dump(mode="json") for item in milestones.milestones],
            },
            reasoning="Coaching memory context and milestones loaded.",
            label="Memory",
            reference="GET /memory",
        )
