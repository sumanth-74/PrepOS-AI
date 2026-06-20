from __future__ import annotations

from prepos.application.agents.models import AgentContext
from prepos.application.agents.tools.base_tool import BaseTool
from prepos.application.knowledge.current_affairs_dto import CurrentAffairsSearchRequest
from prepos.application.knowledge.current_affairs_service import CurrentAffairsService


class CurrentAffairsTool(BaseTool):
    name = "current_affairs"

    def __init__(self, *, service: CurrentAffairsService) -> None:
        self._service = service

    async def execute(self, *, context: AgentContext) -> AgentResult:
        exam_id = context.exam_id or "upsc_cse"
        results = await self._service.search(
            tenant_id=context.tenant_id,
            request=CurrentAffairsSearchRequest(query=context.question, exam_id=exam_id, limit=5),
        )
        return self._success(
            data=results.model_dump(mode="json"),
            reasoning="Current affairs articles retrieved for agent context.",
            label="Current Affairs",
            reference="GET /current-affairs/search",
        )
