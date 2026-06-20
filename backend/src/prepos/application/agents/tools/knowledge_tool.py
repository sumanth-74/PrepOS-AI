from __future__ import annotations

from prepos.application.agents.models import AgentContext
from prepos.application.agents.tools.base_tool import BaseTool
from prepos.application.knowledge.dto import KnowledgeAskRequest
from prepos.application.knowledge.knowledge_agent_service import KnowledgeAgentService


class KnowledgeTool(BaseTool):
    name = "knowledge"

    def __init__(self, *, service: KnowledgeAgentService) -> None:
        self._service = service

    async def execute(self, *, context: AgentContext) -> AgentResult:
        exam_id = context.exam_id or "upsc_cse"
        response = await self._service.ask(
            tenant_id=context.tenant_id,
            request=KnowledgeAskRequest(query=context.question, exam_id=exam_id),
        )
        return self._success(
            data=response.model_dump(mode="json"),
            reasoning="Knowledge agent RAG response retrieved.",
            label="Knowledge",
            reference="POST /knowledge/ask",
            confidence=response.confidence or "medium",
        )
