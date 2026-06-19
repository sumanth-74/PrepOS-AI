from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from prepos.application.exam.ports import ExamCatalogUnitOfWorkPort
from prepos.application.student.ports import StudentUnitOfWorkPort
from prepos.domain.exam.exceptions import ExamNotFoundError
from prepos.domain.exam.value_objects import CatalogStatus
from prepos.domain.student.entities import LearningGraphProvision, PreparationTwinProvision, Student
from prepos.domain.student.events import StudentOnboardingCompleted
from prepos.domain.student.exceptions import OnboardingValidationError
from prepos.domain.student.policies import OnboardingCompletionPolicy
from prepos.domain.student.value_objects import ProvisionStatus, TwinStatus


class OnboardingProvisioningService:
    DEFAULT_PREDICTION_PROFILE: dict[str, object] = {"readiness": None}
    PROJECTION_VERSION = "twin_projection_v1"

    def __init__(
        self,
        student_uow: StudentUnitOfWorkPort,
        exam_uow: ExamCatalogUnitOfWorkPort,
    ) -> None:
        self._student_uow = student_uow
        self._exam_uow = exam_uow

    async def derive_target_stages(self, exam_id: str) -> tuple[str, ...]:
        tracks = await self._exam_uow.exam_repo.list_tracks(exam_id)
        active_stages = sorted({track.stage for track in tracks if track.status == CatalogStatus.ACTIVE})
        if active_stages:
            return tuple(active_stages)
        return ("prelims", "mains")

    async def complete_onboarding(
        self,
        *,
        student: Student,
        diagnostic_offered: bool,
        correlation_id: str,
    ) -> tuple[Student, LearningGraphProvision, PreparationTwinProvision, StudentOnboardingCompleted]:
        OnboardingCompletionPolicy.validate_ready_for_completion(student)
        assert student.target_exam_id is not None

        exam = await self._exam_uow.exam_repo.get_exam(student.target_exam_id)
        if exam is None:
            raise ExamNotFoundError(
                f"Exam {student.target_exam_id} not found.",
                details={"exam_id": student.target_exam_id},
            )

        catalog_version_row = await self._exam_uow.catalog_version_repo.get_latest_published(student.target_exam_id)
        if catalog_version_row is None:
            raise OnboardingValidationError(
                "No published catalog version found for target exam.",
                details={"exam_id": student.target_exam_id},
            )

        expected_node_count = await self._exam_uow.concept_repo.count_active_by_exam(student.target_exam_id)
        if expected_node_count <= 0:
            raise OnboardingValidationError(
                "Target exam has no active concepts to provision.",
                details={"exam_id": student.target_exam_id},
            )

        existing_lg = await self._student_uow.learning_graph_provision_repo.get_by_student(
            student.tenant_id,
            student.id,
        )
        if existing_lg is not None:
            raise OnboardingValidationError(
                "Learning graph provision already exists for student.",
                details={"student_id": str(student.id)},
            )

        existing_twin = await self._student_uow.preparation_twin_repo.get_by_student_exam(
            student.tenant_id,
            student.id,
            student.target_exam_id,
        )
        if existing_twin is not None:
            raise OnboardingValidationError(
                "Preparation twin already exists for student.",
                details={"student_id": str(student.id), "exam_id": student.target_exam_id},
            )

        now = datetime.now(UTC)
        target_stages = await self.derive_target_stages(student.target_exam_id)

        completed_student = Student(
            id=student.id,
            tenant_id=student.tenant_id,
            user_id=student.user_id,
            target_exam_id=student.target_exam_id,
            target_year=student.target_year,
            daily_study_hours=student.daily_study_hours,
            experience_level=student.experience_level,
            onboarding_completed=True,
            onboarding_completed_at=now,
            created_at=student.created_at,
            updated_at=now,
        )
        saved_student = await self._student_uow.student_repo.save(completed_student)

        lg_provision = LearningGraphProvision(
            id=uuid4(),
            tenant_id=student.tenant_id,
            student_id=student.id,
            exam_id=student.target_exam_id,
            catalog_version=catalog_version_row.version,
            status=ProvisionStatus.PROVISIONED,
            expected_node_count=expected_node_count,
            provisioned_node_count=0,
            provisioned_at=now,
            created_at=now,
            updated_at=now,
        )
        saved_lg = await self._student_uow.learning_graph_provision_repo.save(lg_provision)

        twin = PreparationTwinProvision(
            id=uuid4(),
            tenant_id=student.tenant_id,
            student_id=student.id,
            exam_id=student.target_exam_id,
            status=TwinStatus.PROVISIONED,
            academic_profile={},
            behavioral_profile={},
            prediction_profile=dict(self.DEFAULT_PREDICTION_PROFILE),
            metadata={
                "scoring_versions": {},
                "catalog_version_bound": catalog_version_row.version,
                "rebuild_causation_id": None,
            },
            projection_version=self.PROJECTION_VERSION,
            row_version=1,
            last_rebuilt_at=now,
            last_event_id_processed=None,
            created_at=now,
            updated_at=now,
        )
        saved_twin = await self._student_uow.preparation_twin_repo.save(twin)

        event = StudentOnboardingCompleted(
            student_id=student.id,
            user_id=student.user_id,
            tenant_id=student.tenant_id,
            exam_id=student.target_exam_id,
            diagnostic_offered=diagnostic_offered,
            target_stages=target_stages,
            catalog_version=catalog_version_row.version,
            occurred_at=now,
            correlation_id=correlation_id,
        )
        return saved_student, saved_lg, saved_twin, event
