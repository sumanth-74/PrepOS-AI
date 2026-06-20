from __future__ import annotations

from prepos.application.agents.models import AgentContext
from prepos.application.agents.tools.base_tool import BaseTool
from prepos.application.twin.twin_read_service import TwinReadService


class TwinTool(BaseTool):
    name = "twin"

    def __init__(self, *, service: TwinReadService) -> None:
        self._service = service

    async def execute(self, *, context: AgentContext) -> AgentResult:
        if context.student_id is None:
            return self._failure(reasoning="student_id required for twin tool.", tool_name=self.name)
        exam_id = context.exam_id or "upsc_cse"
        dashboard = await self._service.get_dashboard(
            tenant_id=context.tenant_id,
            student_id=context.student_id,
            exam_id=exam_id,
        )
        metrics = await self._service.get_metrics(
            tenant_id=context.tenant_id,
            student_id=context.student_id,
            exam_id=exam_id,
        )
        return self._success(
            data={
                "dashboard": dashboard.model_dump(mode="json"),
                "metrics": metrics.model_dump(mode="json"),
            },
            reasoning="Twin readiness dashboard and metrics loaded.",
            label="Twin",
            reference="GET /twin/dashboard",
        )
