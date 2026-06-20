from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse

from prepos.api.deps import get_current_context, get_outcome_analytics_service
from prepos.application.recommendations.outcomes.outcome_analytics import OutcomeAnalyticsService
from prepos.application.recommendations.outcomes.outcome_models import RecommendationEffectivenessAdminResponse
from prepos.core.tenancy import RoleName, TenantContext

router = APIRouter(prefix="/admin/recommendation-effectiveness", tags=["Admin Recommendation Effectiveness"])


def _require_admin(context: TenantContext) -> None:
    context.require_role(RoleName.INSTITUTE_ADMIN)


@router.get("", response_model=RecommendationEffectivenessAdminResponse, summary="Recommendation effectiveness dashboard")
async def get_recommendation_effectiveness_dashboard(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[OutcomeAnalyticsService, Depends(get_outcome_analytics_service)],
    period_days: int = Query(default=30, ge=1, le=365),
) -> RecommendationEffectivenessAdminResponse:
    _require_admin(context)
    return await service.get_admin_dashboard(tenant_id=context.tenant_id, period_days=period_days)


@router.get("/export", response_class=PlainTextResponse, summary="Export recommendation effectiveness CSV")
async def export_recommendation_effectiveness(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[OutcomeAnalyticsService, Depends(get_outcome_analytics_service)],
    period_days: int = Query(default=30, ge=1, le=365),
) -> PlainTextResponse:
    _require_admin(context)
    csv_content = await service.export_csv(tenant_id=context.tenant_id, period_days=period_days)
    return PlainTextResponse(content=csv_content, media_type="text/csv")
