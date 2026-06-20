from __future__ import annotations

from prepos.application.agents.models import AgentContext
from prepos.application.agents.tools.base_tool import BaseTool
from prepos.application.cohort.cohort_service import CohortIntelligenceService


class CohortTool(BaseTool):
    name = "cohort"

    def __init__(self, *, service: CohortIntelligenceService) -> None:
        self._service = service

    async def execute(self, *, context: AgentContext) -> AgentResult:
        exam_id = context.exam_id or "upsc_cse"
        if context.persona == "admin":
            dashboard = await self._service.get_admin_dashboard(tenant_id=context.tenant_id)
            return self._success(
                data=dashboard.model_dump(mode="json"),
                reasoning="Cohort admin dashboard loaded.",
                label="Cohort",
                reference="GET /admin/cohort",
            )
        summary = await self._service.get_cohort_summary(
            tenant_id=context.tenant_id,
            exam_id=exam_id,
        )
        risks = await self._service.get_cohort_risks(
            tenant_id=context.tenant_id,
            exam_id=exam_id,
        )
        return self._success(
            data={"summary": summary.model_dump(mode="json"), "risks": risks.model_dump(mode="json")},
            reasoning="Cohort summary and risks loaded.",
            label="Cohort",
            reference="GET /cohort/summary",
        )
