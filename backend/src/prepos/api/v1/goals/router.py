from __future__ import annotations

from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query, status

from prepos.api.deps import get_current_context, get_goal_service, get_student_uow
from prepos.application.goal.dto import GoalResponse, GoalUpsertRequest
from prepos.application.goal.service import GoalService
from prepos.core.tenancy import RoleName, TenantContext
from prepos.domain.learning_graph.exceptions import NodeNotFoundError
from prepos.infrastructure.db.repositories.student_repository import SqlAlchemyStudentUnitOfWork

router = APIRouter(prefix="/goals", tags=["Goals"])


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


@router.post(
    "",
    response_model=GoalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create or replace preparation goal",
)
async def create_goal(
    body: GoalUpsertRequest,
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[GoalService, Depends(get_goal_service)],
    student_uow: Annotated[SqlAlchemyStudentUnitOfWork, Depends(get_student_uow)],
    student_id: UUID | None = Query(default=None),
) -> GoalResponse:
    target_student_id = await _resolve_student_id(context, student_uow, student_id)
    return await service.create_goal(
        tenant_id=context.tenant_id,
        student_id=target_student_id,
        request=body,
        correlation_id=_correlation_id(context),
    )


@router.put(
    "",
    response_model=GoalResponse,
    summary="Update preparation goal",
)
async def update_goal(
    body: GoalUpsertRequest,
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[GoalService, Depends(get_goal_service)],
    student_uow: Annotated[SqlAlchemyStudentUnitOfWork, Depends(get_student_uow)],
    student_id: UUID | None = Query(default=None),
) -> GoalResponse:
    target_student_id = await _resolve_student_id(context, student_uow, student_id)
    return await service.update_goal(
        tenant_id=context.tenant_id,
        student_id=target_student_id,
        request=body,
        correlation_id=_correlation_id(context),
    )


@router.get(
    "",
    response_model=GoalResponse | None,
    summary="Get preparation goal",
)
async def get_goal(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[GoalService, Depends(get_goal_service)],
    student_uow: Annotated[SqlAlchemyStudentUnitOfWork, Depends(get_student_uow)],
    exam_id: str = Query(...),
    student_id: UUID | None = Query(default=None),
) -> GoalResponse | None:
    target_student_id = await _resolve_student_id(context, student_uow, student_id)
    return await service.get_goal(
        tenant_id=context.tenant_id,
        student_id=target_student_id,
        exam_id=exam_id,
    )
