from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse

from prepos.api.deps import get_copilot_analytics_service, get_current_context
from prepos.application.copilot.analytics_dto import CopilotAnalyticsResponse
from prepos.application.copilot.analytics_service import CopilotAnalyticsService
from prepos.core.tenancy import RoleName, TenantContext

router = APIRouter(prefix="/admin/copilot", tags=["Admin Copilot Analytics"])


def _require_admin(context: TenantContext) -> None:
    context.require_role(RoleName.INSTITUTE_ADMIN)


@router.get(
    "/analytics",
    response_model=CopilotAnalyticsResponse,
    summary="Copilot adoption and usage analytics",
)
async def get_copilot_analytics(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[CopilotAnalyticsService, Depends(get_copilot_analytics_service)],
    days: int = Query(default=30, ge=1, le=365),
) -> CopilotAnalyticsResponse:
    _require_admin(context)
    return await service.get_analytics(tenant_id=context.tenant_id, period_days=days)


@router.get(
    "/analytics/export",
    response_class=PlainTextResponse,
    summary="Export copilot query log as CSV",
)
async def export_copilot_analytics(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[CopilotAnalyticsService, Depends(get_copilot_analytics_service)],
    days: int = Query(default=30, ge=1, le=365),
) -> PlainTextResponse:
    _require_admin(context)
    csv_body = await service.export_csv(tenant_id=context.tenant_id, period_days=days)
    return PlainTextResponse(
        content=csv_body,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="copilot_queries.csv"'},
    )
