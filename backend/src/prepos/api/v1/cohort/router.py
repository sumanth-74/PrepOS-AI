from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from prepos.api.deps import get_cohort_intelligence_service, get_current_context
from prepos.application.cohort.cohort_models import (
    CohortRisksResponse,
    CohortSegmentsResponse,
    CohortStudentsResponse,
    CohortSummaryResponse,
    CohortTrendsResponse,
)
from prepos.application.cohort.cohort_service import CohortIntelligenceService
from prepos.core.tenancy import RoleName, TenantContext

router = APIRouter(prefix="/cohort", tags=["Cohort Intelligence"])


@router.get("/students", response_model=CohortStudentsResponse, summary="Cohort students with segments")
async def get_cohort_students(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[CohortIntelligenceService, Depends(get_cohort_intelligence_service)],
    exam_id: str = Query(default="upsc_cse"),
    cohort_id: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> CohortStudentsResponse:
    context.require_role(RoleName.FACULTY, RoleName.INSTITUTE_ADMIN)
    return await service.get_cohort_students(
        tenant_id=context.tenant_id,
        exam_id=exam_id,
        cohort_id=cohort_id,
        limit=limit,
    )


@router.get("/segments", response_model=CohortSegmentsResponse, summary="Cohort segment distribution")
async def get_cohort_segments(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[CohortIntelligenceService, Depends(get_cohort_intelligence_service)],
    exam_id: str = Query(default="upsc_cse"),
    cohort_id: str | None = Query(default=None),
    segment_type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> CohortSegmentsResponse:
    context.require_role(RoleName.FACULTY, RoleName.INSTITUTE_ADMIN)
    return await service.get_cohort_segments(
        tenant_id=context.tenant_id,
        exam_id=exam_id,
        cohort_id=cohort_id,
        segment_type=segment_type,
        limit=limit,
    )


@router.get("/risks", response_model=CohortRisksResponse, summary="Cohort risk dashboard")
async def get_cohort_risks(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[CohortIntelligenceService, Depends(get_cohort_intelligence_service)],
    exam_id: str = Query(default="upsc_cse"),
    cohort_id: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
) -> CohortRisksResponse:
    context.require_role(RoleName.FACULTY, RoleName.INSTITUTE_ADMIN)
    return await service.get_cohort_risks(
        tenant_id=context.tenant_id,
        exam_id=exam_id,
        cohort_id=cohort_id,
        limit=limit,
    )


@router.get("/trends", response_model=CohortTrendsResponse, summary="Cohort trends")
async def get_cohort_trends(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[CohortIntelligenceService, Depends(get_cohort_intelligence_service)],
    exam_id: str = Query(default="upsc_cse"),
    cohort_id: str | None = Query(default=None),
    period: str = Query(default="weekly"),
) -> CohortTrendsResponse:
    context.require_role(RoleName.FACULTY, RoleName.INSTITUTE_ADMIN)
    return await service.get_cohort_trends(
        tenant_id=context.tenant_id,
        exam_id=exam_id,
        cohort_id=cohort_id,
        period=period,
    )


@router.get("/summary", response_model=CohortSummaryResponse, summary="Cohort summary")
async def get_cohort_summary(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[CohortIntelligenceService, Depends(get_cohort_intelligence_service)],
    exam_id: str = Query(default="upsc_cse"),
    cohort_id: str | None = Query(default=None),
    refresh: bool = Query(default=False),
) -> CohortSummaryResponse:
    context.require_role(RoleName.FACULTY, RoleName.INSTITUTE_ADMIN)
    return await service.get_cohort_summary(
        tenant_id=context.tenant_id,
        exam_id=exam_id,
        cohort_id=cohort_id,
        refresh=refresh,
    )
