from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from prepos.api.deps import get_copilot_service, get_current_context, get_agent_feedback_service
from prepos.application.agentops.models import AgentFeedbackRequest
from prepos.application.copilot.dto import CopilotQueryRequest, CopilotQueryResponse
from prepos.application.copilot.service import CopilotService
from prepos.core.tenancy import TenantContext

router = APIRouter(prefix="/copilot", tags=["Copilot"])


@router.post(
    "/query",
    response_model=CopilotQueryResponse,
    summary="Deterministic copilot query (tools-only v0)",
)
async def copilot_query(
    body: CopilotQueryRequest,
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[CopilotService, Depends(get_copilot_service)],
) -> CopilotQueryResponse:
    return await service.query(context=context, request=body)


@router.post("/feedback", summary="Submit copilot agent feedback")
async def copilot_feedback(
    body: AgentFeedbackRequest,
    context: Annotated[TenantContext, Depends(get_current_context)],
    feedback_service: Annotated[object, Depends(get_agent_feedback_service)],
):
    feedback_id = await feedback_service.submit_feedback(
        tenant_id=context.tenant_id,
        user_id=context.user_id,
        request=body,
        intent="agent_orchestration",
    )
    return {"feedback_id": str(feedback_id), "status": "recorded"}
