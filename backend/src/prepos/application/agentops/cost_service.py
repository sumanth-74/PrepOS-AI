from __future__ import annotations

from uuid import UUID

from prepos.application.agentops.models import AgentCostDashboardResponse
from prepos.application.agentops.ports import AgentOpsRepositoryPort


class AgentCostService:
    def __init__(self, *, repository: AgentOpsRepositoryPort) -> None:
        self._repository = repository

    async def get_dashboard(self, *, tenant_id: UUID) -> AgentCostDashboardResponse:
        payload = await self._repository.get_cost_dashboard(tenant_id=tenant_id)
        return AgentCostDashboardResponse.model_validate(payload)
