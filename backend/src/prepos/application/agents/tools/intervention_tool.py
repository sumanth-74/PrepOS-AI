from __future__ import annotations

from prepos.application.agents.models import AgentContext
from prepos.application.agents.tools.base_tool import BaseTool
from prepos.application.interventions.intervention_service import MentorInterventionService


class InterventionTool(BaseTool):
    name = "intervention"

    def __init__(self, *, service: MentorInterventionService) -> None:
        self._service = service

    async def execute(self, *, context: AgentContext) -> AgentResult:
        if context.persona == "admin":
            dashboard = await self._service.get_admin_dashboard(tenant_id=context.tenant_id)
            return self._success(
                data=dashboard.model_dump(mode="json"),
                reasoning="Intervention admin analytics loaded.",
                label="Interventions",
                reference="GET /admin/interventions",
            )
        if context.student_id is None:
            return self._failure(reasoning="student_id required for interventions.", tool_name=self.name)
        exam_id = context.exam_id or "upsc_cse"
        student_user_id = context.student_user_id or context.user_id
        interventions = await self._service.get_student_interventions(
            tenant_id=context.tenant_id,
            student_id=context.student_id,
            student_user_id=student_user_id,
            exam_id=exam_id,
        )
        return self._success(
            data=interventions.model_dump(mode="json"),
            reasoning="Mentor intervention recommendations loaded.",
            label="Interventions",
            reference="GET /interventions/student",
        )
