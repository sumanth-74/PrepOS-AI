from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from prepos.application.agentops.models import AgentFeedbackAnalyticsResponse, AgentFeedbackRequest
from prepos.application.agentops.ports import AgentOpsRepositoryPort


class AgentFeedbackService:
    def __init__(self, *, repository: AgentOpsRepositoryPort) -> None:
        self._repository = repository

    async def submit_feedback(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        request: AgentFeedbackRequest,
        agent_type: str | None = None,
        intent: str | None = None,
    ) -> UUID:
        return await self._repository.save_feedback(
            tenant_id=tenant_id,
            user_id=user_id,
            request=request,
            agent_type=agent_type,
            intent=intent,
            now=datetime.now(UTC),
        )

    async def get_analytics(self, *, tenant_id: UUID) -> AgentFeedbackAnalyticsResponse:
        return await self._repository.get_feedback_analytics(tenant_id=tenant_id)
