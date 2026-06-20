from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse

from prepos.api.deps import get_cohort_intelligence_service, get_current_context
from prepos.application.cohort.cohort_models import (
    CohortAdminResponse,
    CohortRisksResponse,
    CohortSegmentsResponse,
    CohortSummaryResponse,
    CohortTrendsResponse,
)
from prepos.application.cohort.cohort_service import CohortIntelligenceService
from prepos.core.tenancy import RoleName, TenantContext

router = APIRouter(prefix="/admin/cohort", tags=["Admin Cohort Intelligence"])


def _require_admin(context: TenantContext) -> None:
    context.require_role(RoleName.INSTITUTE_ADMIN)


@router.get("", response_model=CohortAdminResponse, summary="Institution cohort analytics")
async def get_admin_cohort_dashboard(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[CohortIntelligenceService, Depends(get_cohort_intelligence_service)],
) -> CohortAdminResponse:
    _require_admin(context)
    return await service.get_admin_dashboard(tenant_id=context.tenant_id)


@router.get("/export", response_class=PlainTextResponse, summary="Export cohort CSV")
async def export_cohort_csv(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[CohortIntelligenceService, Depends(get_cohort_intelligence_service)],
) -> PlainTextResponse:
    _require_admin(context)
    return PlainTextResponse(
        content=await service.export_csv(tenant_id=context.tenant_id),
        media_type="text/csv",
    )


@router.get("/segments", response_model=CohortSegmentsResponse, summary="Admin segment distribution")
async def get_admin_cohort_segments(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[CohortIntelligenceService, Depends(get_cohort_intelligence_service)],
    exam_id: str = Query(default="upsc_cse"),
    cohort_id: str | None = Query(default=None),
) -> CohortSegmentsResponse:
    _require_admin(context)
    return await service.get_cohort_segments(
        tenant_id=context.tenant_id,
        exam_id=exam_id,
        cohort_id=cohort_id,
    )


@router.get("/trends", response_model=CohortTrendsResponse, summary="Admin cohort trends")
async def get_admin_cohort_trends(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[CohortIntelligenceService, Depends(get_cohort_intelligence_service)],
    exam_id: str = Query(default="upsc_cse"),
    cohort_id: str | None = Query(default=None),
    period: str = Query(default="monthly"),
) -> CohortTrendsResponse:
    _require_admin(context)
    return await service.get_cohort_trends(
        tenant_id=context.tenant_id,
        exam_id=exam_id,
        cohort_id=cohort_id,
        period=period,
    )


@router.get("/risks", response_model=CohortRisksResponse, summary="Admin cohort risks")
async def get_admin_cohort_risks(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[CohortIntelligenceService, Depends(get_cohort_intelligence_service)],
    exam_id: str = Query(default="upsc_cse"),
    cohort_id: str | None = Query(default=None),
) -> CohortRisksResponse:
    _require_admin(context)
    return await service.get_cohort_risks(
        tenant_id=context.tenant_id,
        exam_id=exam_id,
        cohort_id=cohort_id,
    )


@router.get("/summary", response_model=CohortSummaryResponse, summary="Admin cohort summary")
async def get_admin_cohort_summary(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[CohortIntelligenceService, Depends(get_cohort_intelligence_service)],
    exam_id: str = Query(default="upsc_cse"),
    refresh: bool = Query(default=True),
) -> CohortSummaryResponse:
    _require_admin(context)
    return await service.get_cohort_summary(
        tenant_id=context.tenant_id,
        exam_id=exam_id,
        refresh=refresh,
    )
