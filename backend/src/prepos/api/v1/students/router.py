from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from prepos.api.deps import (
    get_current_context,
    get_exam_uow,
    get_outbox,
    get_student_uow,
)
from prepos.application.student.dto import (
    CompleteOnboardingRequest,
    CompleteOnboardingResponse,
    StudentProfileResponse,
    UpdateStudentGoalsRequest,
)
from prepos.application.student.use_cases import (
    CompleteOnboardingUseCase,
    GetStudentProfileUseCase,
    UpdateStudentGoalsUseCase,
)
from prepos.core.tenancy import TenantContext
from prepos.events.outbox.publisher import OutboxPublisher
from prepos.infrastructure.db.repositories.exam_repository import SqlAlchemyExamCatalogUnitOfWork
from prepos.infrastructure.db.repositories.student_repository import SqlAlchemyStudentUnitOfWork

router = APIRouter(prefix="/students", tags=["Students"])


def get_get_student_profile_use_case(
    uow: Annotated[SqlAlchemyStudentUnitOfWork, Depends(get_student_uow)],
) -> GetStudentProfileUseCase:
    return GetStudentProfileUseCase(uow)


def get_update_student_goals_use_case(
    student_uow: Annotated[SqlAlchemyStudentUnitOfWork, Depends(get_student_uow)],
    exam_uow: Annotated[SqlAlchemyExamCatalogUnitOfWork, Depends(get_exam_uow)],
) -> UpdateStudentGoalsUseCase:
    return UpdateStudentGoalsUseCase(student_uow, exam_uow)


def get_complete_onboarding_use_case(
    student_uow: Annotated[SqlAlchemyStudentUnitOfWork, Depends(get_student_uow)],
    exam_uow: Annotated[SqlAlchemyExamCatalogUnitOfWork, Depends(get_exam_uow)],
    outbox: Annotated[OutboxPublisher, Depends(get_outbox)],
) -> CompleteOnboardingUseCase:
    return CompleteOnboardingUseCase(student_uow, exam_uow, outbox)


@router.get("/me", response_model=StudentProfileResponse, summary="Get current student profile")
async def get_my_profile(
    context: Annotated[TenantContext, Depends(get_current_context)],
    use_case: Annotated[GetStudentProfileUseCase, Depends(get_get_student_profile_use_case)],
) -> StudentProfileResponse:
    return await use_case.execute(context=context, auto_create_for_me=True)


@router.get("/{student_id}", response_model=StudentProfileResponse, summary="Get student profile by ID")
async def get_student_profile(
    student_id: UUID,
    context: Annotated[TenantContext, Depends(get_current_context)],
    use_case: Annotated[GetStudentProfileUseCase, Depends(get_get_student_profile_use_case)],
) -> StudentProfileResponse:
    return await use_case.execute(context=context, student_id=student_id)


@router.patch("/{student_id}", response_model=StudentProfileResponse, summary="Update student goals")
async def update_student_goals(
    student_id: UUID,
    body: UpdateStudentGoalsRequest,
    context: Annotated[TenantContext, Depends(get_current_context)],
    use_case: Annotated[UpdateStudentGoalsUseCase, Depends(get_update_student_goals_use_case)],
) -> StudentProfileResponse:
    return await use_case.execute(context=context, student_id=student_id, request=body)


@router.post(
    "/onboarding/complete",
    response_model=CompleteOnboardingResponse,
    summary="Complete student onboarding and provision shells",
)
async def complete_onboarding(
    body: CompleteOnboardingRequest,
    context: Annotated[TenantContext, Depends(get_current_context)],
    use_case: Annotated[CompleteOnboardingUseCase, Depends(get_complete_onboarding_use_case)],
) -> CompleteOnboardingResponse:
    return await use_case.execute(context=context, diagnostic_offered=body.diagnostic_offered)
