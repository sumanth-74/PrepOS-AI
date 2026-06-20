from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse

from prepos.api.deps import (
    get_agent_approval_service,
    get_agent_cost_service,
    get_agent_evaluation_service,
    get_agent_feedback_service,
    get_agent_health_service,
    get_agent_trace_service,
    get_current_context,
)
from prepos.application.agentops.models import (
    AgentCostDashboardResponse,
    AgentEvaluationDashboardResponse,
    AgentFeedbackAnalyticsResponse,
    AgentFeedbackRequest,
    AgentHealthLeaderboardResponse,
    AgentTraceListResponse,
    AgentTraceRecord,
    ApprovalDecisionRequest,
    PendingActionListResponse,
    PendingActionRecord,
)
from prepos.core.tenancy import RoleName, TenantContext

traces_router = APIRouter(prefix="/admin/agent-traces", tags=["Admin Agent Traces"])
evaluation_router = APIRouter(prefix="/admin/agent-evaluation", tags=["Admin Agent Evaluation"])
costs_router = APIRouter(prefix="/admin/agent-costs", tags=["Admin Agent Costs"])
approvals_router = APIRouter(prefix="/admin/approvals", tags=["Admin Agent Approvals"])


def _require_admin(context: TenantContext) -> None:
    context.require_role(RoleName.INSTITUTE_ADMIN)


@traces_router.get("", response_model=AgentTraceListResponse)
async def list_agent_traces(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[object, Depends(get_agent_trace_service)],
    limit: int = 50,
    offset: int = 0,
) -> AgentTraceListResponse:
    _require_admin(context)
    items, total = await service.list_traces(tenant_id=context.tenant_id, limit=limit, offset=offset)
    return AgentTraceListResponse(items=items, total=total)


@traces_router.get("/{trace_id}", response_model=AgentTraceRecord)
async def get_agent_trace(
    trace_id: UUID,
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[object, Depends(get_agent_trace_service)],
) -> AgentTraceRecord:
    _require_admin(context)
    trace = await service.get_trace(tenant_id=context.tenant_id, trace_id=trace_id)
    if trace is None:
        raise HTTPException(status_code=404, detail="Trace not found.")
    return trace


@traces_router.get("/{trace_id}/export")
async def export_agent_trace(
    trace_id: UUID,
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[object, Depends(get_agent_trace_service)],
):
    _require_admin(context)
    payload = await service.export_trace(tenant_id=context.tenant_id, trace_id=trace_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="Trace not found.")
    return JSONResponse(content=payload)


@evaluation_router.get("", response_model=AgentEvaluationDashboardResponse)
async def get_agent_evaluation_dashboard(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[object, Depends(get_agent_evaluation_service)],
) -> AgentEvaluationDashboardResponse:
    _require_admin(context)
    return await service.get_dashboard(tenant_id=context.tenant_id)


@costs_router.get("", response_model=AgentCostDashboardResponse)
async def get_agent_cost_dashboard(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[object, Depends(get_agent_cost_service)],
) -> AgentCostDashboardResponse:
    _require_admin(context)
    return await service.get_dashboard(tenant_id=context.tenant_id)


@approvals_router.get("", response_model=PendingActionListResponse)
async def list_pending_actions(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[object, Depends(get_agent_approval_service)],
    status: str | None = "pending",
) -> PendingActionListResponse:
    context.require_role(RoleName.FACULTY, RoleName.INSTITUTE_ADMIN)
    return await service.list_actions(tenant_id=context.tenant_id, status=status)


@approvals_router.post("/{action_id}/approve", response_model=PendingActionRecord)
async def approve_action(
    action_id: UUID,
    body: ApprovalDecisionRequest,
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[object, Depends(get_agent_approval_service)],
) -> PendingActionRecord:
    context.require_role(RoleName.FACULTY, RoleName.INSTITUTE_ADMIN)
    record = await service.approve(
        tenant_id=context.tenant_id,
        action_id=action_id,
        reviewer_id=context.user_id,
        review_note=body.review_note,
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Action not found.")
    return record


@approvals_router.post("/{action_id}/reject", response_model=PendingActionRecord)
async def reject_action(
    action_id: UUID,
    body: ApprovalDecisionRequest,
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[object, Depends(get_agent_approval_service)],
) -> PendingActionRecord:
    context.require_role(RoleName.FACULTY, RoleName.INSTITUTE_ADMIN)
    record = await service.reject(
        tenant_id=context.tenant_id,
        action_id=action_id,
        reviewer_id=context.user_id,
        review_note=body.review_note,
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Action not found.")
    return record
