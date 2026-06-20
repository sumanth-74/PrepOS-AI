from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from prepos.api.deps import get_current_context, get_goal_forecasting_service, get_student_uow
from prepos.application.forecasting.forecast_models import (
    CustomScenarioRequest,
    ForecastExplainResponse,
    ForecastHistoryResponse,
    ForecastScenarioResponse,
    GoalForecastResponse,
)
from prepos.application.forecasting.forecast_service import GoalForecastingService
from prepos.core.exceptions import ValidationError
from prepos.core.tenancy import RoleName, TenantContext
from prepos.domain.learning_graph.exceptions import NodeNotFoundError
from prepos.infrastructure.db.repositories.student_repository import SqlAlchemyStudentUnitOfWork

router = APIRouter(prefix="/forecasting", tags=["Goal Forecasting"])


class GenerateForecastRequest(BaseModel):
    exam_id: str = Field(default="upsc_cse")


@router.post("/generate", response_model=GoalForecastResponse, summary="Generate goal forecast")
async def generate_forecast(
    body: GenerateForecastRequest,
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[GoalForecastingService, Depends(get_goal_forecasting_service)],
    student_uow: Annotated[SqlAlchemyStudentUnitOfWork, Depends(get_student_uow)],
) -> GoalForecastResponse:
    context.require_role(RoleName.STUDENT)
    student = await student_uow.student_repo.get_by_user_id(context.tenant_id, context.user_id)
    if student is None:
        raise NodeNotFoundError("Student profile not found.")
    try:
        return await service.generate_forecast(
            tenant_id=context.tenant_id,
            user_id=context.user_id,
            student_id=student.id,
            exam_id=body.exam_id,
        )
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


@router.get("/current", response_model=GoalForecastResponse, summary="Get current goal forecast")
async def get_current_forecast(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[GoalForecastingService, Depends(get_goal_forecasting_service)],
    exam_id: str = Query(default="upsc_cse"),
) -> GoalForecastResponse:
    context.require_role(RoleName.STUDENT)
    forecast = await service.get_current_forecast(
        tenant_id=context.tenant_id,
        user_id=context.user_id,
        exam_id=exam_id,
    )
    if forecast is None:
        raise ValidationError("No forecast found. Generate a forecast first.")
    return forecast


@router.get("/scenarios", response_model=list[ForecastScenarioResponse], summary="List forecast scenarios")
async def list_scenarios(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[GoalForecastingService, Depends(get_goal_forecasting_service)],
    exam_id: str = Query(default="upsc_cse"),
) -> list[ForecastScenarioResponse]:
    context.require_role(RoleName.STUDENT)
    return await service.get_scenarios(
        tenant_id=context.tenant_id,
        user_id=context.user_id,
        exam_id=exam_id,
    )


@router.post("/scenario/custom", response_model=ForecastScenarioResponse, summary="Simulate custom scenario")
async def simulate_custom_scenario(
    body: CustomScenarioRequest,
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[GoalForecastingService, Depends(get_goal_forecasting_service)],
    student_uow: Annotated[SqlAlchemyStudentUnitOfWork, Depends(get_student_uow)],
) -> ForecastScenarioResponse:
    context.require_role(RoleName.STUDENT)
    student = await student_uow.student_repo.get_by_user_id(context.tenant_id, context.user_id)
    if student is None:
        raise NodeNotFoundError("Student profile not found.")
    return await service.simulate_custom_scenario(
        tenant_id=context.tenant_id,
        user_id=context.user_id,
        student_id=student.id,
        request=body,
    )


@router.get("/explain", response_model=ForecastExplainResponse, summary="Explain current forecast")
async def explain_forecast(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[GoalForecastingService, Depends(get_goal_forecasting_service)],
    student_uow: Annotated[SqlAlchemyStudentUnitOfWork, Depends(get_student_uow)],
    exam_id: str = Query(default="upsc_cse"),
) -> ForecastExplainResponse:
    context.require_role(RoleName.STUDENT)
    student = await student_uow.student_repo.get_by_user_id(context.tenant_id, context.user_id)
    if student is None:
        raise NodeNotFoundError("Student profile not found.")
    try:
        return await service.explain_forecast(
            tenant_id=context.tenant_id,
            user_id=context.user_id,
            student_id=student.id,
            exam_id=exam_id,
        )
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


@router.get("/history", response_model=ForecastHistoryResponse, summary="Forecast history")
async def get_forecast_history(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[GoalForecastingService, Depends(get_goal_forecasting_service)],
    exam_id: str = Query(default="upsc_cse"),
    limit: int = Query(default=20, ge=1, le=100),
) -> ForecastHistoryResponse:
    context.require_role(RoleName.STUDENT)
    return await service.get_history(
        tenant_id=context.tenant_id,
        user_id=context.user_id,
        exam_id=exam_id,
        limit=limit,
    )


@router.get("/student/{student_id}", response_model=GoalForecastResponse, summary="Student forecast (mentor)")
async def get_student_forecast(
    student_id: str,
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[GoalForecastingService, Depends(get_goal_forecasting_service)],
    student_uow: Annotated[SqlAlchemyStudentUnitOfWork, Depends(get_student_uow)],
    exam_id: str = Query(default="upsc_cse"),
) -> GoalForecastResponse:
    context.require_role(RoleName.FACULTY, RoleName.INSTITUTE_ADMIN)
    student = await student_uow.student_repo.get_by_id(context.tenant_id, UUID(student_id))
    if student is None:
        raise ValidationError("Student not found.", details={"student_id": student_id})
    forecast = await service.get_current_forecast(
        tenant_id=context.tenant_id,
        user_id=student.user_id,
        exam_id=exam_id,
    )
    if forecast is None:
        raise ValidationError("No forecast found for this student.")
    return forecast


@router.post("/student/{student_id}/simulate", response_model=GoalForecastResponse, summary="Regenerate student forecast")
async def simulate_student_forecast(
    student_id: str,
    body: GenerateForecastRequest,
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[GoalForecastingService, Depends(get_goal_forecasting_service)],
    student_uow: Annotated[SqlAlchemyStudentUnitOfWork, Depends(get_student_uow)],
) -> GoalForecastResponse:
    context.require_role(RoleName.FACULTY, RoleName.INSTITUTE_ADMIN)
    student = await student_uow.student_repo.get_by_id(context.tenant_id, UUID(student_id))
    if student is None:
        raise ValidationError("Student not found.", details={"student_id": student_id})
    try:
        return await service.generate_forecast(
            tenant_id=context.tenant_id,
            user_id=student.user_id,
            student_id=student.id,
            exam_id=body.exam_id,
        )
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
