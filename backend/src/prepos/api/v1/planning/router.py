from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from prepos.api.deps import get_adaptive_planning_service, get_current_context, get_student_uow
from prepos.application.planning.planning_models import (
    AdaptivePlanResponse,
    PlanCompletionResponse,
    PlanExplainResponse,
    PlanHistoryResponse,
    PlanRevisionResponse,
)
from prepos.application.planning.planning_service import AdaptivePlanningService
from prepos.core.exceptions import ValidationError
from prepos.core.tenancy import RoleName, TenantContext
from prepos.domain.learning_graph.exceptions import NodeNotFoundError
from prepos.infrastructure.db.repositories.student_repository import SqlAlchemyStudentUnitOfWork

router = APIRouter(prefix="/planning", tags=["Adaptive Planning"])


class GeneratePlanRequest(BaseModel):
    exam_id: str = Field(default="upsc_cse")
    daily_minutes: int | None = Field(default=None, ge=20, le=480)


@router.post("/generate", response_model=AdaptivePlanResponse, summary="Generate adaptive weekly plan")
async def generate_plan(
    body: GeneratePlanRequest,
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[AdaptivePlanningService, Depends(get_adaptive_planning_service)],
    student_uow: Annotated[SqlAlchemyStudentUnitOfWork, Depends(get_student_uow)],
) -> AdaptivePlanResponse:
    context.require_role(RoleName.STUDENT)
    student = await student_uow.student_repo.get_by_user_id(context.tenant_id, context.user_id)
    if student is None:
        raise NodeNotFoundError("Student profile not found.")
    return await service.generate_plan(
        tenant_id=context.tenant_id,
        user_id=context.user_id,
        student_id=student.id,
        exam_id=body.exam_id,
        daily_minutes=body.daily_minutes,
    )


@router.get("/current", response_model=AdaptivePlanResponse, summary="Get current adaptive plan")
async def get_current_plan(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[AdaptivePlanningService, Depends(get_adaptive_planning_service)],
    exam_id: str = Query(default="upsc_cse"),
) -> AdaptivePlanResponse:
    context.require_role(RoleName.STUDENT)
    plan = await service.get_current_plan(
        tenant_id=context.tenant_id,
        user_id=context.user_id,
        exam_id=exam_id,
    )
    if plan is None:
        raise ValidationError("No active plan found. Generate a plan first.")
    return plan


@router.get("/history", response_model=PlanHistoryResponse, summary="Plan generation history")
async def get_plan_history(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[AdaptivePlanningService, Depends(get_adaptive_planning_service)],
    exam_id: str = Query(default="upsc_cse"),
    limit: int = Query(default=20, ge=1, le=100),
) -> PlanHistoryResponse:
    context.require_role(RoleName.STUDENT)
    return await service.get_plan_history(
        tenant_id=context.tenant_id,
        user_id=context.user_id,
        exam_id=exam_id,
        limit=limit,
    )


@router.post("/item/{item_id}/complete", response_model=PlanCompletionResponse, summary="Complete plan item")
async def complete_plan_item(
    item_id: str,
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[AdaptivePlanningService, Depends(get_adaptive_planning_service)],
) -> PlanCompletionResponse:
    context.require_role(RoleName.STUDENT)
    try:
        return await service.complete_item(
            tenant_id=context.tenant_id,
            user_id=context.user_id,
            item_id=UUID(item_id),
        )
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


@router.get("/explain/{concept_id}", response_model=PlanExplainResponse, summary="Explain plan priority for concept")
async def explain_plan_concept(
    concept_id: str,
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[AdaptivePlanningService, Depends(get_adaptive_planning_service)],
    student_uow: Annotated[SqlAlchemyStudentUnitOfWork, Depends(get_student_uow)],
    exam_id: str = Query(default="upsc_cse"),
) -> PlanExplainResponse:
    context.require_role(RoleName.STUDENT)
    student = await student_uow.student_repo.get_by_user_id(context.tenant_id, context.user_id)
    if student is None:
        raise NodeNotFoundError("Student profile not found.")
    return await service.explain_concept(
        tenant_id=context.tenant_id,
        user_id=context.user_id,
        student_id=student.id,
        exam_id=exam_id,
        concept_id=concept_id,
    )


@router.get("/revisions", response_model=list[PlanRevisionResponse], summary="Plan revision history")
async def list_plan_revisions(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[AdaptivePlanningService, Depends(get_adaptive_planning_service)],
    exam_id: str = Query(default="upsc_cse"),
) -> list[PlanRevisionResponse]:
    context.require_role(RoleName.STUDENT)
    return await service.list_revisions(
        tenant_id=context.tenant_id,
        user_id=context.user_id,
        exam_id=exam_id,
    )


@router.get(
    "/student/{student_id}",
    response_model=AdaptivePlanResponse,
    summary="Get student adaptive plan (mentor)",
)
async def get_student_plan_for_mentor(
    student_id: str,
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[AdaptivePlanningService, Depends(get_adaptive_planning_service)],
    student_uow: Annotated[SqlAlchemyStudentUnitOfWork, Depends(get_student_uow)],
    exam_id: str = Query(default="upsc_cse"),
) -> AdaptivePlanResponse:
    context.require_role(RoleName.FACULTY, RoleName.INSTITUTE_ADMIN)
    student = await student_uow.student_repo.get_by_id(context.tenant_id, UUID(student_id))
    if student is None:
        raise ValidationError("Student not found.", details={"student_id": student_id})
    plan = await service.get_current_plan(
        tenant_id=context.tenant_id,
        user_id=student.user_id,
        exam_id=exam_id,
    )
    if plan is None:
        raise ValidationError("No active plan found for this student.")
    return plan


@router.post(
    "/student/{student_id}/regenerate",
    response_model=AdaptivePlanResponse,
    summary="Regenerate student adaptive plan (mentor)",
)
async def regenerate_student_plan(
    student_id: str,
    body: GeneratePlanRequest,
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[AdaptivePlanningService, Depends(get_adaptive_planning_service)],
    student_uow: Annotated[SqlAlchemyStudentUnitOfWork, Depends(get_student_uow)],
) -> AdaptivePlanResponse:
    context.require_role(RoleName.FACULTY, RoleName.INSTITUTE_ADMIN)
    student = await student_uow.student_repo.get_by_id(context.tenant_id, UUID(student_id))
    if student is None:
        raise ValidationError("Student not found.", details={"student_id": student_id})
    return await service.generate_plan(
        tenant_id=context.tenant_id,
        user_id=student.user_id,
        student_id=student.id,
        exam_id=body.exam_id,
        daily_minutes=body.daily_minutes,
    )
