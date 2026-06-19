from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query, status

from prepos.api.deps import (
    get_current_context,
    get_student_uow,
    get_study_plan_service,
)
from prepos.application.study_plan.dto import (
    StudyPlanExecutionRequest,
    StudyPlanExecutionResponse,
    StudyPlanResponse,
)
from prepos.application.study_plan.service import StudyPlanService
from prepos.core.tenancy import RoleName, TenantContext
from prepos.domain.learning_graph.exceptions import NodeNotFoundError
from prepos.domain.study_plan.value_objects import ActivityType
from prepos.infrastructure.db.repositories.student_repository import SqlAlchemyStudentUnitOfWork

router = APIRouter(prefix="/study-plan", tags=["Study Plan"])


def _correlation_id(context: TenantContext) -> str:
    if context.correlation_id is not None:
        return context.correlation_id
    if context.request_id is not None:
        return context.request_id
    return str(uuid4())


async def _resolve_student_id(
    context: TenantContext,
    student_uow: SqlAlchemyStudentUnitOfWork,
    student_id: UUID | None,
) -> UUID:
    if student_id is not None:
        student = await student_uow.student_repo.get_by_id(context.tenant_id, student_id)
        if student is None:
            raise NodeNotFoundError(
                "Student not found.",
                details={"student_id": str(student_id)},
            )
        if RoleName.STUDENT in context.roles and student.user_id != context.user_id:
            raise NodeNotFoundError(
                "Student access denied.",
                details={"student_id": str(student_id)},
            )
        return student.id

    student = await student_uow.student_repo.get_by_user_id(context.tenant_id, context.user_id)
    if student is None:
        raise NodeNotFoundError(
            "Student profile not found.",
            details={"user_id": str(context.user_id)},
        )
    return student.id


@router.get(
    "",
    response_model=StudyPlanResponse,
    summary="Daily and weekly study plan",
)
async def get_study_plan(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[StudyPlanService, Depends(get_study_plan_service)],
    student_uow: Annotated[SqlAlchemyStudentUnitOfWork, Depends(get_student_uow)],
    student_id: UUID | None = Query(default=None),
    exam_id: str | None = Query(default=None),
) -> StudyPlanResponse:
    target_student_id = await _resolve_student_id(context, student_uow, student_id)
    return await service.get_study_plan(
        tenant_id=context.tenant_id,
        student_id=target_student_id,
        exam_id=exam_id,
    )


@router.post(
    "/items/complete",
    response_model=StudyPlanExecutionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Record completed study plan item",
)
async def complete_study_plan_item(
    body: StudyPlanExecutionRequest,
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[StudyPlanService, Depends(get_study_plan_service)],
    student_uow: Annotated[SqlAlchemyStudentUnitOfWork, Depends(get_student_uow)],
    student_id: UUID | None = Query(default=None),
) -> StudyPlanExecutionResponse:
    target_student_id = await _resolve_student_id(context, student_uow, student_id)
    completed_at = datetime.now(UTC)
    await service.record_item_completed(
        tenant_id=context.tenant_id,
        student_id=target_student_id,
        exam_id=body.exam_id,
        concept_id=body.concept_id,
        activity_type=ActivityType(body.activity_type),
        planned_minutes=body.planned_minutes,
        actual_minutes=body.actual_minutes,
        correlation_id=_correlation_id(context),
        causation_id=None,
        completed_at=completed_at,
    )
    return StudyPlanExecutionResponse(
        concept_id=body.concept_id,
        status="COMPLETED",
        completed_at=completed_at,
    )


@router.post(
    "/items/skip",
    response_model=StudyPlanExecutionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Record skipped study plan item",
)
async def skip_study_plan_item(
    body: StudyPlanExecutionRequest,
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[StudyPlanService, Depends(get_study_plan_service)],
    student_uow: Annotated[SqlAlchemyStudentUnitOfWork, Depends(get_student_uow)],
    student_id: UUID | None = Query(default=None),
) -> StudyPlanExecutionResponse:
    target_student_id = await _resolve_student_id(context, student_uow, student_id)
    completed_at = datetime.now(UTC)
    await service.record_item_skipped(
        tenant_id=context.tenant_id,
        student_id=target_student_id,
        exam_id=body.exam_id,
        concept_id=body.concept_id,
        activity_type=ActivityType(body.activity_type),
        planned_minutes=body.planned_minutes,
        actual_minutes=body.actual_minutes,
        correlation_id=_correlation_id(context),
        causation_id=None,
        completed_at=completed_at,
    )
    return StudyPlanExecutionResponse(
        concept_id=body.concept_id,
        status="SKIPPED",
        completed_at=completed_at,
    )
