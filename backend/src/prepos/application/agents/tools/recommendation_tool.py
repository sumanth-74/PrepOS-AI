from __future__ import annotations

from prepos.application.agents.models import AgentContext, AgentResult
from prepos.application.agents.tools.base_tool import BaseTool
from prepos.application.recommendations.recommendation_service import LearningRecommendationService


class RecommendationTool(BaseTool):
    name = "recommendation"

    def __init__(self, *, service: LearningRecommendationService) -> None:
        self._service = service

    async def execute(self, *, context: AgentContext) -> AgentResult:
        if context.student_id is None:
            return self._failure(reasoning="student_id required for recommendations.", tool_name=self.name)
        exam_id = context.exam_id or "upsc_cse"
        user_id = context.student_user_id or context.user_id
        if context.persona == "mentor":
            response = await self._service.get_mentor_recommendations(
                tenant_id=context.tenant_id,
                student_id=context.student_id,
                exam_id=exam_id,
                user_id=user_id,
            )
        else:
            response = await self._service.get_student_recommendations(
                tenant_id=context.tenant_id,
                student_id=context.student_id,
                exam_id=exam_id,
                user_id=user_id,
            )
        return self._success(
            data=response.model_dump(mode="json"),
            reasoning="Ranked learning recommendations loaded from existing engine.",
            label="Recommendations",
            reference="GET /recommendations",
        )
