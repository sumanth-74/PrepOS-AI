from __future__ import annotations

from uuid import UUID

from prepos.application.agents.agent_marketplace import AgentMarketplace, CAPABILITY_CATALOG
from prepos.application.agents.models import AgentAdminDashboardResponse, AgentCapability, AgentHealthStatus
from prepos.application.agents.ports import AgentRepositoryPort
from prepos.application.agents.registry import ToolRegistry


class AgentAnalyticsService:
    def __init__(
        self,
        *,
        repository: AgentRepositoryPort,
        tool_registry: ToolRegistry | None = None,
    ) -> None:
        self._repository = repository
        self._marketplace = AgentMarketplace(tool_registry=tool_registry) if tool_registry else None

    async def get_dashboard(self, *, tenant_id: UUID) -> AgentAdminDashboardResponse:
        metrics = await self._repository.get_admin_metrics(tenant_id=tenant_id)
        health = await self._repository.get_agent_health(tenant_id=tenant_id)
        registered_agents = [item.model_dump(mode="json") for item in CAPABILITY_CATALOG]
        return AgentAdminDashboardResponse(
            **metrics,
            registered_agents=registered_agents,
            agent_health=[AgentHealthStatus.model_validate(item) for item in health],
        )

    async def list_capabilities(self) -> list[AgentCapability]:
        return list(CAPABILITY_CATALOG)

    async def export_csv(self, *, tenant_id: UUID) -> str:
        rows = await self._repository.export_executions(tenant_id=tenant_id, limit=2000)
        lines = ["execution_id,agent_type,persona,confidence,success,execution_time_ms,created_at"]
        for row in rows:
            lines.append(
                f"{row['execution_id']},{row['agent_type']},{row['persona']},"
                f"{row['confidence']},{row['success']},{row['execution_time_ms']},{row['created_at']}"
            )
        return "\n".join(lines) + "\n"
