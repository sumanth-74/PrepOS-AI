from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse

from prepos.api.deps import get_current_context, get_rag_quality_service
from prepos.application.knowledge.rag_quality_dto import RagQualityResponse
from prepos.application.knowledge.rag_quality_service import RagQualityService
from prepos.core.tenancy import RoleName, TenantContext

router = APIRouter(prefix="/admin/rag-quality", tags=["Admin RAG Quality"])


def _require_admin(context: TenantContext) -> None:
    context.require_role(RoleName.INSTITUTE_ADMIN)


@router.get("", response_model=RagQualityResponse, summary="RAG quality monitoring dashboard")
async def get_rag_quality(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[RagQualityService, Depends(get_rag_quality_service)],
    period_days: int = Query(default=30, ge=1, le=365),
) -> RagQualityResponse:
    _require_admin(context)
    return await service.get_quality_dashboard(tenant_id=context.tenant_id, period_days=period_days)


@router.get("/export", response_class=PlainTextResponse, summary="Export RAG quality evaluations as CSV")
async def export_rag_quality(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[RagQualityService, Depends(get_rag_quality_service)],
    period_days: int = Query(default=30, ge=1, le=365),
) -> PlainTextResponse:
    _require_admin(context)
    csv_body = await service.export_csv(tenant_id=context.tenant_id, period_days=period_days)
    return PlainTextResponse(
        content=csv_body,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="rag_quality_evaluations.csv"'},
    )
