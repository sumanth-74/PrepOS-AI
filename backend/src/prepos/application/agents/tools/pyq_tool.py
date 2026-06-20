from __future__ import annotations

from prepos.application.agents.models import AgentContext
from prepos.application.agents.tools.base_tool import BaseTool
from prepos.application.pyq.pyq_service import PyqService


class PyqTool(BaseTool):
    name = "pyq"

    def __init__(self, *, service: PyqService) -> None:
        self._service = service

    async def execute(self, *, context: AgentContext) -> AgentResult:
        exam_id = context.exam_id or "upsc_cse"
        coverage = await self._service.get_coverage(tenant_id=context.tenant_id, exam_id=exam_id)
        trends = await self._service.get_trends(
            tenant_id=context.tenant_id,
            exam_id=exam_id,
        )
        return self._success(
            data={
                "coverage": coverage.model_dump(mode="json"),
                "trends": trends.model_dump(mode="json"),
            },
            reasoning="PYQ coverage and trends loaded from PYQ intelligence service.",
            label="PYQ",
            reference="GET /pyq/coverage",
        )
