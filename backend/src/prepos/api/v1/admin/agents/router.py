from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse

from prepos.api.deps import get_agent_analytics_service, get_current_context
from prepos.application.agents.agent_analytics import AgentAnalyticsService
from prepos.application.agents.models import AgentAdminDashboardResponse, AgentCapability
from prepos.core.tenancy import RoleName, TenantContext

router = APIRouter(prefix="/admin/agents", tags=["Admin Agent Orchestration"])


def _require_admin(context: TenantContext) -> None:
    context.require_role(RoleName.INSTITUTE_ADMIN)


@router.get("", response_model=AgentAdminDashboardResponse, summary="Agent orchestration dashboard")
async def get_agent_dashboard(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[AgentAnalyticsService, Depends(get_agent_analytics_service)],
) -> AgentAdminDashboardResponse:
    _require_admin(context)
    return await service.get_dashboard(tenant_id=context.tenant_id)


@router.get("/export", response_class=PlainTextResponse, summary="Export agent executions CSV")
async def export_agent_executions(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[AgentAnalyticsService, Depends(get_agent_analytics_service)],
) -> PlainTextResponse:
    _require_admin(context)
    return PlainTextResponse(content=await service.export_csv(tenant_id=context.tenant_id), media_type="text/csv")


@router.get("/marketplace", response_model=list[AgentCapability], summary="Registered agent capabilities")
async def list_agent_marketplace(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[AgentAnalyticsService, Depends(get_agent_analytics_service)],
) -> list[AgentCapability]:
    _require_admin(context)
    return await service.list_capabilities()
