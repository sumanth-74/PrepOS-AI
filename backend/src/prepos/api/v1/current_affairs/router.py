from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile

from prepos.api.deps import (
    get_current_affairs_analytics_service,
    get_current_affairs_service,
    get_current_context,
)
from prepos.application.knowledge.current_affairs_analytics_service import CurrentAffairsAnalyticsService
from prepos.application.knowledge.current_affairs_dto import (
    CreateCurrentAffairsArticleRequest,
    CurrentAffairsAnalyticsResponse,
    CurrentAffairsArticleListResponse,
    CurrentAffairsArticleResponse,
    CurrentAffairsIndexingMetricsResponse,
    CurrentAffairsSearchRequest,
    CurrentAffairsSearchResponse,
)
from prepos.application.knowledge.current_affairs_service import CurrentAffairsService
from prepos.core.tenancy import RoleName, TenantContext

router = APIRouter(prefix="/current-affairs", tags=["Current Affairs"])


def _require_admin(context: TenantContext) -> None:
    context.require_role(RoleName.INSTITUTE_ADMIN)


@router.get("", response_model=CurrentAffairsArticleListResponse, summary="List current affairs articles")
async def list_current_affairs(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[CurrentAffairsService, Depends(get_current_affairs_service)],
    exam_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> CurrentAffairsArticleListResponse:
    return await service.list_articles(
        tenant_id=context.tenant_id,
        exam_id=exam_id,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/metrics/indexing",
    response_model=CurrentAffairsIndexingMetricsResponse,
    summary="Current affairs indexing metrics (admin)",
)
async def get_current_affairs_indexing_metrics(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[CurrentAffairsService, Depends(get_current_affairs_service)],
) -> CurrentAffairsIndexingMetricsResponse:
    _require_admin(context)
    return await service.get_indexing_metrics(tenant_id=context.tenant_id)


@router.get(
    "/metrics/analytics",
    response_model=CurrentAffairsAnalyticsResponse,
    summary="Current affairs Q&A analytics (admin)",
)
async def get_current_affairs_analytics(
    context: Annotated[TenantContext, Depends(get_current_context)],
    analytics_service: Annotated[
        CurrentAffairsAnalyticsService,
        Depends(get_current_affairs_analytics_service),
    ],
    period_days: int = Query(default=30, ge=1, le=365),
) -> CurrentAffairsAnalyticsResponse:
    _require_admin(context)
    return await analytics_service.get_analytics(
        tenant_id=context.tenant_id,
        period_days=period_days,
    )


@router.post("/search", response_model=CurrentAffairsSearchResponse, summary="Search current affairs content")
async def search_current_affairs(
    request: CurrentAffairsSearchRequest,
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[CurrentAffairsService, Depends(get_current_affairs_service)],
    analytics_service: Annotated[
        CurrentAffairsAnalyticsService,
        Depends(get_current_affairs_analytics_service),
    ],
) -> CurrentAffairsSearchResponse:
    response = await service.search(tenant_id=context.tenant_id, request=request)
    recency_success = any(chunk.source.published_at is not None for chunk in response.chunks)
    await analytics_service.record_search(
        tenant_id=context.tenant_id,
        user_id=context.user_id,
        query_text=request.query,
        citation_count=0,
        confidence=None,
        recency_boost_applied=request.prefer_recency,
        recency_retrieval_success=recency_success,
    )
    return response


@router.post(
    "/upload",
    response_model=CurrentAffairsArticleResponse,
    summary="Upload and index a current affairs article (admin)",
)
async def upload_current_affairs_article(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[CurrentAffairsService, Depends(get_current_affairs_service)],
    exam_id: Annotated[str, Form()],
    source_type: Annotated[str, Form()],
    title: Annotated[str, Form()],
    file: UploadFile = File(...),
    published_at: Annotated[str | None, Form()] = None,
    source_authority: Annotated[str | None, Form()] = None,
    exam_stage: Annotated[str | None, Form()] = None,
    importance: Annotated[str | None, Form()] = None,
    catalog_version: Annotated[str | None, Form()] = None,
    subject_id: Annotated[str | None, Form()] = None,
    topic_id: Annotated[str | None, Form()] = None,
    concept_ids: Annotated[str | None, Form()] = None,
) -> CurrentAffairsArticleResponse:
    _require_admin(context)
    file_bytes = await file.read()
    parsed_concept_ids = [item.strip() for item in (concept_ids or "").split(",") if item.strip()]
    parsed_published_at = None
    if published_at:
        from datetime import datetime

        parsed_published_at = datetime.fromisoformat(published_at.replace("Z", "+00:00"))

    request = CreateCurrentAffairsArticleRequest(
        exam_id=exam_id,
        source_type=source_type,
        title=title,
        published_at=parsed_published_at,
        source_authority=source_authority,
        exam_stage=exam_stage,
        importance=importance,
        catalog_version=catalog_version,
        subject_id=subject_id,
        topic_id=topic_id,
        concept_ids=parsed_concept_ids,
    )
    return await service.upload_article(
        tenant_id=context.tenant_id,
        request=request,
        file_name=file.filename or "article.txt",
        mime_type=file.content_type,
        file_bytes=file_bytes,
    )


@router.get("/{article_id}", response_model=CurrentAffairsArticleResponse, summary="Get current affairs article")
async def get_current_affairs_article(
    article_id: UUID,
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[CurrentAffairsService, Depends(get_current_affairs_service)],
) -> CurrentAffairsArticleResponse:
    return await service.get_article(tenant_id=context.tenant_id, article_id=article_id)
