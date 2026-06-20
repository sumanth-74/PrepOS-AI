from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from prepos.api.deps import (
    get_agent_evaluation_service,
    get_agent_health_service,
    get_current_context,
)
from prepos.application.agentops.models import (
    AgentBenchmarkRecord,
    AgentBenchmarkRunRequest,
    AgentHealthDetailResponse,
    AgentHealthLeaderboardResponse,
)
from prepos.core.tenancy import RoleName, TenantContext

router = APIRouter(prefix="/admin/agents", tags=["Admin Agent Health"])


def _require_admin(context: TenantContext) -> None:
    context.require_role(RoleName.INSTITUTE_ADMIN)


@router.get("/health", response_model=AgentHealthLeaderboardResponse)
async def get_agent_health_leaderboard(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[object, Depends(get_agent_health_service)],
) -> AgentHealthLeaderboardResponse:
    _require_admin(context)
    return await service.get_leaderboard(tenant_id=context.tenant_id)


@router.get("/{agent_type}/health", response_model=AgentHealthDetailResponse)
async def get_single_agent_health(
    agent_type: str,
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[object, Depends(get_agent_health_service)],
) -> AgentHealthDetailResponse:
    _require_admin(context)
    detail = await service.get_agent_health(tenant_id=context.tenant_id, agent_type=agent_type)
    if detail is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Agent health not found.")
    return detail


benchmark_router = APIRouter(prefix="/admin/agent-benchmarks", tags=["Admin Agent Benchmarks"])


@benchmark_router.get("", response_model=list[AgentBenchmarkRecord])
async def list_benchmarks(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[object, Depends(get_agent_evaluation_service)],
) -> list[AgentBenchmarkRecord]:
    _require_admin(context)
    return await service.list_benchmarks(tenant_id=context.tenant_id)


@benchmark_router.post("/run", response_model=AgentBenchmarkRecord)
async def run_benchmark(
    body: AgentBenchmarkRunRequest,
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[object, Depends(get_agent_evaluation_service)],
) -> AgentBenchmarkRecord:
    _require_admin(context)
    return await service.run_benchmark(tenant_id=context.tenant_id, request=body)
