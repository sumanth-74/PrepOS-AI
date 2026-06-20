from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile

from prepos.api.deps import (
    get_current_context,
    get_pyq_analytics_service,
    get_pyq_service,
)
from prepos.application.pyq.dto import (
    CreatePyqUploadRequest,
    PyqAnalyticsResponse,
    PyqCoverageResponse,
    PyqIndexingMetricsResponse,
    PyqMappingReviewItem,
    PyqQuestionResponse,
    PyqSearchRequest,
    PyqSearchResponse,
    PyqTrendsResponse,
    PyqUploadResponse,
)
from prepos.application.pyq.pyq_analytics_service import PyqAnalyticsService
from prepos.application.pyq.pyq_service import PyqService
from prepos.core.tenancy import RoleName, TenantContext

router = APIRouter(prefix="/pyq", tags=["PYQ"])


def _require_admin(context: TenantContext) -> None:
    context.require_role(RoleName.INSTITUTE_ADMIN)


@router.post("/search", response_model=PyqSearchResponse, summary="Search PYQ indexed content")
async def search_pyq(
    request: PyqSearchRequest,
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[PyqService, Depends(get_pyq_service)],
    analytics_service: Annotated[PyqAnalyticsService, Depends(get_pyq_analytics_service)],
) -> PyqSearchResponse:
    response = await service.search(tenant_id=context.tenant_id, request=request)
    pyq_success = any(chunk.source.source_type == "pyq" for chunk in response.chunks)
    await analytics_service.record_search(
        tenant_id=context.tenant_id,
        user_id=context.user_id,
        query_text=request.query,
        intent=None,
        citation_count=0,
        confidence=None,
        pyq_boost_applied=response.pyq_boost_applied,
        pyq_retrieval_success=pyq_success,
        concept_id=request.concept_ids[0] if request.concept_ids else None,
    )
    return response


@router.get("/trends", response_model=PyqTrendsResponse, summary="PYQ concept trends")
async def get_pyq_trends(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[PyqService, Depends(get_pyq_service)],
    exam_id: str = Query(default="upsc_cse"),
    limit: int = Query(default=20, ge=1, le=100),
) -> PyqTrendsResponse:
    return await service.get_trends(tenant_id=context.tenant_id, exam_id=exam_id, limit=limit)


@router.get(
    "/metrics/indexing",
    response_model=PyqIndexingMetricsResponse,
    summary="PYQ indexing metrics (admin)",
)
async def get_pyq_indexing_metrics(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[PyqService, Depends(get_pyq_service)],
) -> PyqIndexingMetricsResponse:
    _require_admin(context)
    return await service.get_indexing_metrics(tenant_id=context.tenant_id)


@router.get(
    "/metrics/analytics",
    response_model=PyqAnalyticsResponse,
    summary="PYQ Q&A analytics (admin)",
)
async def get_pyq_analytics(
    context: Annotated[TenantContext, Depends(get_current_context)],
    analytics_service: Annotated[PyqAnalyticsService, Depends(get_pyq_analytics_service)],
    period_days: int = Query(default=30, ge=1, le=365),
) -> PyqAnalyticsResponse:
    _require_admin(context)
    return await analytics_service.get_analytics(tenant_id=context.tenant_id, period_days=period_days)


@router.get(
    "/coverage",
    response_model=PyqCoverageResponse,
    summary="PYQ concept coverage (admin)",
)
async def get_pyq_coverage(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[PyqService, Depends(get_pyq_service)],
    exam_id: str = Query(default="upsc_cse"),
) -> PyqCoverageResponse:
    _require_admin(context)
    return await service.get_coverage(tenant_id=context.tenant_id, exam_id=exam_id)


@router.get(
    "/mappings/review",
    response_model=list[PyqMappingReviewItem],
    summary="PYQ mapping review queue (admin)",
)
async def list_pyq_mapping_review(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[PyqService, Depends(get_pyq_service)],
    exam_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[PyqMappingReviewItem]:
    _require_admin(context)
    return await service.list_mapping_review(
        tenant_id=context.tenant_id,
        exam_id=exam_id,
        limit=limit,
    )


@router.post(
    "/upload",
    response_model=PyqUploadResponse,
    summary="Upload and index PYQ questions (admin)",
)
async def upload_pyq(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[PyqService, Depends(get_pyq_service)],
    exam_id: Annotated[str, Form()],
    title: Annotated[str, Form()],
    file: UploadFile = File(...),
    catalog_version: Annotated[str | None, Form()] = None,
) -> PyqUploadResponse:
    _require_admin(context)
    file_bytes = await file.read()
    request = CreatePyqUploadRequest(
        exam_id=exam_id,
        title=title,
        catalog_version=catalog_version,
    )
    result = await service.upload(
        tenant_id=context.tenant_id,
        request=request,
        file_name=file.filename or "pyq.json",
        mime_type=file.content_type,
        file_bytes=file_bytes,
    )
    assert isinstance(result, PyqUploadResponse)
    return result


@router.get("/{question_id}", response_model=PyqQuestionResponse, summary="Get PYQ question")
async def get_pyq_question(
    question_id: UUID,
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[PyqService, Depends(get_pyq_service)],
) -> PyqQuestionResponse:
    return await service.get_question(tenant_id=context.tenant_id, question_id=question_id)
