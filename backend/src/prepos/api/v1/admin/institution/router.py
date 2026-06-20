from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse

from prepos.api.deps import (
    get_current_context,
    get_institution_intelligence_service,
    get_institution_outcome_service,
)
from prepos.application.institution.institution_models import (
    InstitutionDashboardResponse,
    InstitutionInsightsResponse,
    InstitutionMentorEffectivenessResponse,
    InstitutionRecommendationsResponse,
    InstitutionTrendsResponse,
)
from prepos.application.institution.institution_service import InstitutionIntelligenceService
from prepos.application.institution_outcomes.outcome_models import (
    CreateInitiativeRequest,
    InitiativeEffectivenessResponse,
    InitiativeItem,
    InitiativesResponse,
    OutcomesResponse,
    RoiResponse,
)
from prepos.application.institution_outcomes.outcome_service import InstitutionOutcomeService
from prepos.core.tenancy import RoleName, TenantContext

router = APIRouter(prefix="/admin/institution", tags=["Admin Institution Intelligence"])


def _require_admin(context: TenantContext) -> None:
    context.require_role(RoleName.INSTITUTE_ADMIN)


@router.get("", response_model=InstitutionDashboardResponse, summary="Institution intelligence dashboard")
async def get_institution_dashboard(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[InstitutionIntelligenceService, Depends(get_institution_intelligence_service)],
    refresh: bool = Query(default=False),
) -> InstitutionDashboardResponse:
    _require_admin(context)
    return await service.get_dashboard(tenant_id=context.tenant_id, refresh=refresh)


@router.get("/insights", response_model=InstitutionInsightsResponse, summary="Institution insights")
async def get_institution_insights(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[InstitutionIntelligenceService, Depends(get_institution_intelligence_service)],
    refresh: bool = Query(default=False),
) -> InstitutionInsightsResponse:
    _require_admin(context)
    return await service.get_insights(tenant_id=context.tenant_id, refresh=refresh)


@router.get(
    "/recommendations",
    response_model=InstitutionRecommendationsResponse,
    summary="Institution recommendations",
)
async def get_institution_recommendations(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[InstitutionIntelligenceService, Depends(get_institution_intelligence_service)],
    refresh: bool = Query(default=False),
) -> InstitutionRecommendationsResponse:
    _require_admin(context)
    return await service.get_recommendations(tenant_id=context.tenant_id, refresh=refresh)


@router.get("/trends", response_model=InstitutionTrendsResponse, summary="Institution trends")
async def get_institution_trends(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[InstitutionIntelligenceService, Depends(get_institution_intelligence_service)],
    period: str = Query(default="monthly"),
    refresh: bool = Query(default=False),
) -> InstitutionTrendsResponse:
    _require_admin(context)
    return await service.get_trends(tenant_id=context.tenant_id, period=period, refresh=refresh)


@router.get(
    "/mentor-effectiveness",
    response_model=InstitutionMentorEffectivenessResponse,
    summary="Institution mentor effectiveness",
)
async def get_institution_mentor_effectiveness(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[InstitutionIntelligenceService, Depends(get_institution_intelligence_service)],
) -> InstitutionMentorEffectivenessResponse:
    _require_admin(context)
    return await service.get_mentor_effectiveness(tenant_id=context.tenant_id)


@router.get("/export", response_class=PlainTextResponse, summary="Export institution intelligence CSV")
async def export_institution_csv(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[InstitutionIntelligenceService, Depends(get_institution_intelligence_service)],
) -> PlainTextResponse:
    _require_admin(context)
    return PlainTextResponse(
        content=await service.export_csv(tenant_id=context.tenant_id),
        media_type="text/csv",
    )


@router.post("/initiatives", response_model=InitiativeItem, summary="Create institution initiative")
async def create_institution_initiative(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[InstitutionOutcomeService, Depends(get_institution_outcome_service)],
    request: CreateInitiativeRequest,
) -> InitiativeItem:
    _require_admin(context)
    return await service.create_initiative(tenant_id=context.tenant_id, request=request)


@router.get("/initiatives", response_model=InitiativesResponse, summary="List institution initiatives")
async def list_institution_initiatives(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[InstitutionOutcomeService, Depends(get_institution_outcome_service)],
    status: str | None = Query(default=None),
) -> InitiativesResponse:
    _require_admin(context)
    return await service.list_initiatives(tenant_id=context.tenant_id, status=status)


@router.get("/outcomes", response_model=OutcomesResponse, summary="Institution outcomes")
async def get_institution_outcomes(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[InstitutionOutcomeService, Depends(get_institution_outcome_service)],
    refresh: bool = Query(default=False),
) -> OutcomesResponse:
    _require_admin(context)
    return await service.get_outcomes(tenant_id=context.tenant_id, refresh=refresh)


@router.get("/roi", response_model=RoiResponse, summary="Institution ROI metrics")
async def get_institution_roi(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[InstitutionOutcomeService, Depends(get_institution_outcome_service)],
    refresh: bool = Query(default=False),
) -> RoiResponse:
    _require_admin(context)
    return await service.get_roi(tenant_id=context.tenant_id, refresh=refresh)


@router.get("/roi/export", response_class=PlainTextResponse, summary="Export institution ROI CSV")
async def export_institution_roi_csv(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[InstitutionOutcomeService, Depends(get_institution_outcome_service)],
) -> PlainTextResponse:
    _require_admin(context)
    return PlainTextResponse(
        content=await service.export_roi_csv(tenant_id=context.tenant_id),
        media_type="text/csv",
    )
