from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse

from prepos.api.deps import get_adaptive_planning_service, get_current_context
from prepos.application.planning.planning_models import PlanningAdminResponse
from prepos.application.planning.planning_service import AdaptivePlanningService
from prepos.core.tenancy import RoleName, TenantContext

router = APIRouter(prefix="/admin/planning", tags=["Admin Adaptive Planning"])


def _require_admin(context: TenantContext) -> None:
    context.require_role(RoleName.INSTITUTE_ADMIN)


@router.get("", response_model=PlanningAdminResponse, summary="Adaptive planning analytics")
async def get_planning_admin_dashboard(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[AdaptivePlanningService, Depends(get_adaptive_planning_service)],
) -> PlanningAdminResponse:
    _require_admin(context)
    return await service.get_admin_dashboard(tenant_id=context.tenant_id)


@router.get("/export", response_class=PlainTextResponse, summary="Export planning CSV")
async def export_planning_csv(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[AdaptivePlanningService, Depends(get_adaptive_planning_service)],
) -> PlainTextResponse:
    _require_admin(context)
    csv_content = await service.export_csv(tenant_id=context.tenant_id)
    return PlainTextResponse(content=csv_content, media_type="text/csv")
