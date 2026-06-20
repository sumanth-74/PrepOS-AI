from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse

from prepos.api.deps import get_current_context, get_mentor_intervention_service
from prepos.application.interventions.intervention_models import InterventionAdminResponse
from prepos.application.interventions.intervention_service import MentorInterventionService
from prepos.core.tenancy import RoleName, TenantContext

router = APIRouter(prefix="/admin/interventions", tags=["Admin Interventions"])


def _require_admin(context: TenantContext) -> None:
    context.require_role(RoleName.INSTITUTE_ADMIN)


@router.get("", response_model=InterventionAdminResponse, summary="Intervention analytics")
async def get_interventions_admin_dashboard(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[MentorInterventionService, Depends(get_mentor_intervention_service)],
) -> InterventionAdminResponse:
    _require_admin(context)
    return await service.get_admin_dashboard(tenant_id=context.tenant_id)


@router.get("/export", response_class=PlainTextResponse, summary="Export interventions CSV")
async def export_interventions_csv(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[MentorInterventionService, Depends(get_mentor_intervention_service)],
) -> PlainTextResponse:
    _require_admin(context)
    csv_content = await service.export_csv(tenant_id=context.tenant_id)
    return PlainTextResponse(content=csv_content, media_type="text/csv")
