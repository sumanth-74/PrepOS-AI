from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from prepos.application.agentops.models import AgentHealthLeaderboardResponse, ExperimentRecord, PromptRecord
from prepos.application.agentops.ports import AgentOpsRepositoryPort


class AgentHealthService:
    def __init__(self, *, repository: AgentOpsRepositoryPort) -> None:
        self._repository = repository

    async def get_leaderboard(self, *, tenant_id: UUID) -> AgentHealthLeaderboardResponse:
        agents = await self._repository.get_agent_health_details(tenant_id=tenant_id)
        return AgentHealthLeaderboardResponse(agents=agents, generated_at=datetime.now(UTC))

    async def get_agent_health(self, *, tenant_id: UUID, agent_type: str):
        agents = await self._repository.get_agent_health_details(tenant_id=tenant_id)
        for agent in agents:
            if agent.agent_type == agent_type:
                return agent
        return None


class AgentExperimentService:
    def __init__(self, *, repository: AgentOpsRepositoryPort) -> None:
        self._repository = repository

    async def list_experiments(self, *, tenant_id: UUID | None = None) -> list[ExperimentRecord]:
        return await self._repository.list_experiments(tenant_id=tenant_id)


class PromptRegistryService:
    def __init__(self, *, repository: AgentOpsRepositoryPort) -> None:
        self._repository = repository

    async def list_prompts(self, *, tenant_id: UUID | None = None) -> list[PromptRecord]:
        return await self._repository.list_prompts(tenant_id=tenant_id)
