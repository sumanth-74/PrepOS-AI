from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from prepos.application.exam.ports import ExamCatalogUnitOfWorkPort
from prepos.application.student.dto import (
    CompleteOnboardingResponse,
    OnboardingProvisioningResponse,
    StudentProfileResponse,
    UpdateStudentGoalsRequest,
)
from prepos.application.student.ports import StudentUnitOfWorkPort
from prepos.application.student.services import OnboardingProvisioningService
from prepos.core.tenancy import RoleName, TenantContext
from prepos.domain.student.entities import Student
from prepos.domain.student.exceptions import (
    OnboardingAlreadyCompletedError,
    StudentAccessDeniedError,
    StudentNotFoundError,
    StudentProfileExistsError,
)
from prepos.domain.student.policies import StudentAccessPolicy
from prepos.domain.student.value_objects import ExperienceLevel
from prepos.events.outbox.publisher import OutboxPublisher


def _student_to_dto(student: Student) -> StudentProfileResponse:
    return StudentProfileResponse(
        id=student.id,
        tenant_id=student.tenant_id,
        user_id=student.user_id,
        target_exam=student.target_exam_id,
        target_year=student.target_year,
        daily_study_hours=student.daily_study_hours,
        experience_level=student.experience_level.value if student.experience_level else None,
        onboarding_completed=student.onboarding_completed,
        onboarding_completed_at=student.onboarding_completed_at,
    )


class CreateStudentProfileUseCase:
    def __init__(self, uow: StudentUnitOfWorkPort) -> None:
        self._uow = uow

    async def execute(self, *, context: TenantContext) -> StudentProfileResponse:
        context.require_role(RoleName.STUDENT, RoleName.INSTITUTE_ADMIN, RoleName.SUPER_ADMIN)
        existing = await self._uow.student_repo.get_by_user_id(context.tenant_id, context.user_id)
        if existing is not None:
            raise StudentProfileExistsError(
                "Student profile already exists for this user.",
                details={"user_id": str(context.user_id)},
            )

        now = datetime.now(UTC)
        student = Student(
            id=uuid4(),
            tenant_id=context.tenant_id,
            user_id=context.user_id,
            target_exam_id=None,
            target_year=None,
            daily_study_hours=None,
            experience_level=None,
            onboarding_completed=False,
            onboarding_completed_at=None,
            created_at=now,
            updated_at=now,
        )
        saved = await self._uow.student_repo.save(student)
        await self._uow.commit()
        return _student_to_dto(saved)


class GetStudentProfileUseCase:
    def __init__(self, uow: StudentUnitOfWorkPort) -> None:
        self._uow = uow

    async def execute(
        self,
        *,
        context: TenantContext,
        student_id: UUID | None = None,
        auto_create_for_me: bool = False,
    ) -> StudentProfileResponse:
        if student_id is None:
            student = await self._uow.student_repo.get_by_user_id(context.tenant_id, context.user_id)
            if student is None:
                if auto_create_for_me and (
                    RoleName.STUDENT in context.roles
                    or RoleName.SUPER_ADMIN in context.roles
                    or RoleName.INSTITUTE_ADMIN in context.roles
                ):
                    create_use_case = CreateStudentProfileUseCase(self._uow)
                    return await create_use_case.execute(context=context)
                raise StudentNotFoundError(
                    "Student profile not found.",
                    details={"user_id": str(context.user_id)},
                )
            return _student_to_dto(student)

        student = await self._uow.student_repo.get_by_id(context.tenant_id, student_id)
        if student is None:
            raise StudentNotFoundError(
                "Student not found.",
                details={"student_id": str(student_id)},
            )

        actor_roles = frozenset(role.value for role in context.roles)
        if not StudentAccessPolicy.can_view(
            actor_user_id=context.user_id,
            actor_roles=actor_roles,
            student=student,
        ):
            raise StudentAccessDeniedError(
                "Student access denied.",
                details={"student_id": str(student_id)},
            )
        return _student_to_dto(student)


class UpdateStudentGoalsUseCase:
    def __init__(self, uow: StudentUnitOfWorkPort, exam_uow: ExamCatalogUnitOfWorkPort) -> None:
        self._uow = uow
        self._exam_uow = exam_uow

    async def execute(
        self,
        *,
        context: TenantContext,
        student_id: UUID,
        request: UpdateStudentGoalsRequest,
    ) -> StudentProfileResponse:
        student = await self._uow.student_repo.get_by_id(context.tenant_id, student_id)
        if student is None:
            raise StudentNotFoundError(
                "Student not found.",
                details={"student_id": str(student_id)},
            )

        actor_roles = frozenset(role.value for role in context.roles)
        is_admin = RoleName.SUPER_ADMIN in context.roles or RoleName.INSTITUTE_ADMIN in context.roles
        if student.onboarding_completed and not is_admin:
            raise OnboardingAlreadyCompletedError(
                "Cannot update goals after onboarding is completed.",
                details={"student_id": str(student_id)},
            )

        if not StudentAccessPolicy.can_modify(
            actor_user_id=context.user_id,
            actor_roles=actor_roles,
            student=student,
        ):
            raise StudentAccessDeniedError(
                "Student access denied.",
                details={"student_id": str(student_id)},
            )

        target_exam_id = student.target_exam_id
        if request.target_exam is not None:
            from prepos.domain.exam.exceptions import ExamNotFoundError

            exam = await self._exam_uow.exam_repo.get_exam(request.target_exam)
            if exam is None:
                raise ExamNotFoundError(
                    f"Exam {request.target_exam} not found.",
                    details={"exam_id": request.target_exam},
                )
            target_exam_id = request.target_exam

        experience_level = student.experience_level
        if request.experience_level is not None:
            experience_level = ExperienceLevel(request.experience_level)

        updated = Student(
            id=student.id,
            tenant_id=student.tenant_id,
            user_id=student.user_id,
            target_exam_id=target_exam_id,
            target_year=request.target_year if request.target_year is not None else student.target_year,
            daily_study_hours=(
                request.daily_study_hours
                if request.daily_study_hours is not None
                else student.daily_study_hours
            ),
            experience_level=experience_level,
            onboarding_completed=student.onboarding_completed,
            onboarding_completed_at=student.onboarding_completed_at,
            created_at=student.created_at,
            updated_at=datetime.now(UTC),
        )
        saved = await self._uow.student_repo.save(updated)
        await self._uow.commit()
        return _student_to_dto(saved)


class CompleteOnboardingUseCase:
    def __init__(
        self,
        student_uow: StudentUnitOfWorkPort,
        exam_uow: ExamCatalogUnitOfWorkPort,
        outbox: OutboxPublisher,
    ) -> None:
        self._student_uow = student_uow
        self._exam_uow = exam_uow
        self._outbox = outbox
        self._provisioning = OnboardingProvisioningService(student_uow, exam_uow)

    async def execute(
        self,
        *,
        context: TenantContext,
        diagnostic_offered: bool = False,
    ) -> CompleteOnboardingResponse:
        context.require_role(RoleName.STUDENT, RoleName.INSTITUTE_ADMIN, RoleName.SUPER_ADMIN)

        student = await self._student_uow.student_repo.get_by_user_id(context.tenant_id, context.user_id)
        if student is None:
            raise StudentNotFoundError(
                "Student profile not found.",
                details={"user_id": str(context.user_id)},
            )

        if RoleName.STUDENT in context.roles and student.user_id != context.user_id:
            raise StudentAccessDeniedError(
                "Students may only complete their own onboarding.",
                details={"student_id": str(student.id)},
            )

        correlation_id = context.correlation_id or context.request_id or str(uuid4())
        saved_student, lg_provision, twin, event = await self._provisioning.complete_onboarding(
            student=student,
            diagnostic_offered=diagnostic_offered,
            correlation_id=correlation_id,
        )
        await self._outbox.enqueue_student_onboarding_completed(event)
        await self._student_uow.commit()

        return CompleteOnboardingResponse(
            student=_student_to_dto(saved_student),
            provisioning=OnboardingProvisioningResponse(
                learning_graph_provision_id=lg_provision.id,
                preparation_twin_id=twin.id,
                expected_node_count=lg_provision.expected_node_count,
                catalog_version=lg_provision.catalog_version,
                target_stages=list(event.target_stages),
            ),
        )
