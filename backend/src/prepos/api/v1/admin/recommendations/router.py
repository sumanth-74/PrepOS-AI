from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from prepos.api.deps import get_current_context, get_recommendation_analytics_service
from prepos.application.recommendations.recommendation_analytics_service import RecommendationAnalyticsService
from prepos.application.recommendations.recommendation_models import RecommendationAnalyticsResponse
from prepos.core.tenancy import RoleName, TenantContext

router = APIRouter(prefix="/admin/recommendations", tags=["Admin Recommendations"])


def _require_admin(context: TenantContext) -> None:
    context.require_role(RoleName.INSTITUTE_ADMIN)


@router.get("", response_model=RecommendationAnalyticsResponse, summary="Recommendation analytics")
async def get_recommendation_analytics(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[RecommendationAnalyticsService, Depends(get_recommendation_analytics_service)],
    period_days: int = Query(default=30, ge=1, le=365),
) -> RecommendationAnalyticsResponse:
    _require_admin(context)
    return await service.get_analytics(tenant_id=context.tenant_id, period_days=period_days)
