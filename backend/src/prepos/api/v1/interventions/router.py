from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from prepos.api.deps import get_current_context, get_mentor_intervention_service, get_student_uow
from prepos.application.interventions.intervention_models import (
    InterventionExplainResponse,
    InterventionHistoryResponse,
    InterventionRecordResponse,
    MentorInterventionQueueResponse,
    StudentInterventionResponse,
)
from prepos.application.interventions.intervention_service import MentorInterventionService
from prepos.core.exceptions import ValidationError
from prepos.core.tenancy import RoleName, TenantContext
from prepos.infrastructure.db.repositories.student_repository import SqlAlchemyStudentUnitOfWork

router = APIRouter(prefix="/interventions", tags=["Mentor Interventions"])


class GenerateInterventionRequest(BaseModel):
    exam_id: str = Field(default="upsc_cse")


@router.get("/my-history", response_model=InterventionHistoryResponse, summary="Student intervention history")
async def get_my_intervention_history(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[MentorInterventionService, Depends(get_mentor_intervention_service)],
    exam_id: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
) -> InterventionHistoryResponse:
    context.require_role(RoleName.STUDENT)
    return await service.get_student_history(
        tenant_id=context.tenant_id,
        student_user_id=context.user_id,
        exam_id=exam_id,
        limit=limit,
    )


@router.get("/queue", response_model=MentorInterventionQueueResponse, summary="Mentor intervention queue")
async def get_intervention_queue(
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[MentorInterventionService, Depends(get_mentor_intervention_service)],
    limit: int = Query(default=20, ge=1, le=100),
) -> MentorInterventionQueueResponse:
    context.require_role(RoleName.FACULTY, RoleName.INSTITUTE_ADMIN)
    return await service.get_mentor_queue(
        tenant_id=context.tenant_id,
        mentor_id=context.user_id,
        limit=limit,
    )


@router.get("/student/{student_id}", response_model=StudentInterventionResponse, summary="Student interventions")
async def get_student_interventions(
    student_id: str,
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[MentorInterventionService, Depends(get_mentor_intervention_service)],
    student_uow: Annotated[SqlAlchemyStudentUnitOfWork, Depends(get_student_uow)],
    exam_id: str = Query(default="upsc_cse"),
) -> StudentInterventionResponse:
    context.require_role(RoleName.FACULTY, RoleName.INSTITUTE_ADMIN)
    student = await student_uow.student_repo.get_by_id(context.tenant_id, UUID(student_id))
    if student is None:
        raise ValidationError("Student not found.", details={"student_id": student_id})
    return await service.get_student_interventions(
        tenant_id=context.tenant_id,
        student_id=student.id,
        student_user_id=student.user_id,
        exam_id=exam_id,
    )


@router.post("/student/{student_id}/generate", response_model=StudentInterventionResponse, summary="Generate interventions")
async def generate_student_interventions(
    student_id: str,
    body: GenerateInterventionRequest,
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[MentorInterventionService, Depends(get_mentor_intervention_service)],
    student_uow: Annotated[SqlAlchemyStudentUnitOfWork, Depends(get_student_uow)],
) -> StudentInterventionResponse:
    context.require_role(RoleName.FACULTY, RoleName.INSTITUTE_ADMIN)
    student = await student_uow.student_repo.get_by_id(context.tenant_id, UUID(student_id))
    if student is None:
        raise ValidationError("Student not found.", details={"student_id": student_id})
    try:
        return await service.generate_recommendations(
            tenant_id=context.tenant_id,
            mentor_id=context.user_id,
            student_id=student.id,
            student_user_id=student.user_id,
            exam_id=body.exam_id,
        )
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


@router.post("/{intervention_id}/execute", response_model=InterventionRecordResponse, summary="Execute intervention")
async def execute_intervention(
    intervention_id: str,
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[MentorInterventionService, Depends(get_mentor_intervention_service)],
) -> InterventionRecordResponse:
    context.require_role(RoleName.FACULTY, RoleName.INSTITUTE_ADMIN)
    try:
        return await service.execute_intervention(
            tenant_id=context.tenant_id,
            mentor_id=context.user_id,
            intervention_id=UUID(intervention_id),
        )
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


@router.post("/{intervention_id}/complete", response_model=InterventionHistoryResponse, summary="Complete intervention")
async def complete_intervention(
    intervention_id: str,
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[MentorInterventionService, Depends(get_mentor_intervention_service)],
) -> InterventionHistoryResponse:
    context.require_role(RoleName.FACULTY, RoleName.INSTITUTE_ADMIN)
    try:
        entry = await service.complete_intervention(
            tenant_id=context.tenant_id,
            mentor_id=context.user_id,
            intervention_id=UUID(intervention_id),
        )
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    return InterventionHistoryResponse(interventions=[entry], total=1)


@router.get("/{intervention_id}/explain", response_model=InterventionExplainResponse, summary="Explain intervention")
async def explain_intervention(
    intervention_id: str,
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[MentorInterventionService, Depends(get_mentor_intervention_service)],
) -> InterventionExplainResponse:
    context.require_role(RoleName.FACULTY, RoleName.INSTITUTE_ADMIN, RoleName.STUDENT)
    try:
        return await service.explain_intervention(
            tenant_id=context.tenant_id,
            intervention_id=UUID(intervention_id),
        )
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
