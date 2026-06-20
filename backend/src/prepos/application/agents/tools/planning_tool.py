from __future__ import annotations

from prepos.application.agents.models import AgentContext
from prepos.application.agents.tools.base_tool import BaseTool
from prepos.application.planning.planning_service import AdaptivePlanningService


class PlanningTool(BaseTool):
    name = "planning"

    def __init__(self, *, service: AdaptivePlanningService) -> None:
        self._service = service

    async def execute(self, *, context: AgentContext) -> AgentResult:
        if context.student_id is None:
            if context.persona == "admin":
                dashboard = await self._service.get_admin_dashboard(tenant_id=context.tenant_id)
                return self._success(
                    data=dashboard.model_dump(mode="json"),
                    reasoning="Loaded planning admin dashboard.",
                    label="Planning",
                    reference="GET /admin/planning",
                )
            return self._failure(reasoning="student_id required for planning tool.", tool_name=self.name)
        exam_id = context.exam_id or "upsc_cse"
        user_id = context.student_user_id or context.user_id
        plan = await self._service.get_current_plan(
            tenant_id=context.tenant_id,
            user_id=user_id,
            exam_id=exam_id,
        )
        if plan is None:
            return self._failure(reasoning="No adaptive plan available.", tool_name=self.name)
        return self._success(
            data=plan.model_dump(mode="json"),
            reasoning="Current adaptive study plan loaded.",
            label="Planning",
            reference="GET /planning/current",
        )
