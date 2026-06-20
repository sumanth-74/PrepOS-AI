from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse

from prepos.api.deps import get_current_context, get_goal_forecasting_service
from prepos.application.forecasting.forecast_models import ForecastAdminResponse
from prepos.application.forecasting.forecast_service import GoalForecastingService
from prepos.core.tenancy import RoleName, TenantContext

router = APIRouter(prefix="/admin/forecasting", tags=["Admin Goal Forecasting"])


def _require_admin(context: TenantContext) -> None:
    context.require_role(RoleName.INSTITUTE_ADMIN)


@router.get("", response_model=ForecastAdminResponse, summary="Goal forecasting analytics")
async def get_forecasting_admin_dashboard(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[GoalForecastingService, Depends(get_goal_forecasting_service)],
) -> ForecastAdminResponse:
    _require_admin(context)
    return await service.get_admin_dashboard(tenant_id=context.tenant_id)


@router.get("/export", response_class=PlainTextResponse, summary="Export forecasting CSV")
async def export_forecasting_csv(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[GoalForecastingService, Depends(get_goal_forecasting_service)],
) -> PlainTextResponse:
    _require_admin(context)
    csv_content = await service.export_csv(tenant_id=context.tenant_id)
    return PlainTextResponse(content=csv_content, media_type="text/csv")
