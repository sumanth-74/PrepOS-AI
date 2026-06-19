from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from prepos.application.student.ports import (
    LearningGraphProvisionRepositoryPort,
    PreparationTwinProvisionRepositoryPort,
    StudentRepositoryPort,
    StudentUnitOfWorkPort,
)
from prepos.domain.student.entities import LearningGraphProvision, PreparationTwinProvision, Student
from prepos.domain.student.value_objects import ExperienceLevel, ProvisionStatus, TwinStatus
from prepos.infrastructure.db.models.student import (
    LearningGraphProvisionModel,
    PreparationTwinModel,
    StudentModel,
)


def _map_student(row: StudentModel) -> Student:
    return Student(
        id=row.id,
        tenant_id=row.tenant_id,
        user_id=row.user_id,
        target_exam_id=row.target_exam_id,
        target_year=row.target_year,
        daily_study_hours=row.daily_study_hours,
        experience_level=ExperienceLevel(row.experience_level) if row.experience_level else None,
        onboarding_completed=row.onboarding_completed,
        onboarding_completed_at=row.onboarding_completed_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _map_lg_provision(row: LearningGraphProvisionModel) -> LearningGraphProvision:
    return LearningGraphProvision(
        id=row.id,
        tenant_id=row.tenant_id,
        student_id=row.student_id,
        exam_id=row.exam_id,
        catalog_version=row.catalog_version,
        status=ProvisionStatus(row.status),
        expected_node_count=row.expected_node_count,
        provisioned_node_count=row.provisioned_node_count,
        provisioned_at=row.provisioned_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _map_twin(row: PreparationTwinModel) -> PreparationTwinProvision:
    return PreparationTwinProvision(
        id=row.id,
        tenant_id=row.tenant_id,
        student_id=row.student_id,
        exam_id=row.exam_id,
        status=TwinStatus(row.status),
        academic_profile=dict(row.academic_profile),
        behavioral_profile=dict(row.behavioral_profile),
        prediction_profile=dict(row.prediction_profile),
        metadata=dict(row.metadata_json),
        projection_version=row.projection_version,
        row_version=row.row_version,
        last_rebuilt_at=row.last_rebuilt_at,
        last_event_id_processed=row.last_event_id_processed,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlAlchemyStudentRepository(StudentRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, tenant_id: UUID, student_id: UUID) -> Student | None:
        result = await self._session.execute(
            select(StudentModel).where(
                StudentModel.tenant_id == tenant_id,
                StudentModel.id == student_id,
            )
        )
        row = result.scalar_one_or_none()
        return _map_student(row) if row else None

    async def get_by_user_id(self, tenant_id: UUID, user_id: UUID) -> Student | None:
        result = await self._session.execute(
            select(StudentModel).where(
                StudentModel.tenant_id == tenant_id,
                StudentModel.user_id == user_id,
            )
        )
        row = result.scalar_one_or_none()
        return _map_student(row) if row else None

    async def save(self, student: Student) -> Student:
        row = await self._session.get(StudentModel, student.id)
        if row is None:
            row = StudentModel(
                id=student.id,
                tenant_id=student.tenant_id,
                user_id=student.user_id,
                target_exam_id=student.target_exam_id,
                target_year=student.target_year,
                daily_study_hours=student.daily_study_hours,
                experience_level=student.experience_level.value if student.experience_level else None,
                onboarding_completed=student.onboarding_completed,
                onboarding_completed_at=student.onboarding_completed_at,
            )
            self._session.add(row)
        else:
            row.target_exam_id = student.target_exam_id
            row.target_year = student.target_year
            row.daily_study_hours = student.daily_study_hours
            row.experience_level = student.experience_level.value if student.experience_level else None
            row.onboarding_completed = student.onboarding_completed
            row.onboarding_completed_at = student.onboarding_completed_at
        await self._session.flush()
        return _map_student(row)


class SqlAlchemyLearningGraphProvisionRepository(LearningGraphProvisionRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_student(self, tenant_id: UUID, student_id: UUID) -> LearningGraphProvision | None:
        result = await self._session.execute(
            select(LearningGraphProvisionModel).where(
                LearningGraphProvisionModel.tenant_id == tenant_id,
                LearningGraphProvisionModel.student_id == student_id,
            )
        )
        row = result.scalar_one_or_none()
        return _map_lg_provision(row) if row else None

    async def save(self, provision: LearningGraphProvision) -> LearningGraphProvision:
        row = await self._session.get(LearningGraphProvisionModel, provision.id)
        if row is None:
            row = LearningGraphProvisionModel(
                id=provision.id,
                tenant_id=provision.tenant_id,
                student_id=provision.student_id,
                exam_id=provision.exam_id,
                catalog_version=provision.catalog_version,
                status=provision.status.value,
                expected_node_count=provision.expected_node_count,
                provisioned_node_count=provision.provisioned_node_count,
                provisioned_at=provision.provisioned_at,
            )
            self._session.add(row)
        else:
            row.status = provision.status.value
            row.expected_node_count = provision.expected_node_count
            row.provisioned_node_count = provision.provisioned_node_count
            row.provisioned_at = provision.provisioned_at
        await self._session.flush()
        return _map_lg_provision(row)


class SqlAlchemyPreparationTwinProvisionRepository(PreparationTwinProvisionRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_student_exam(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> PreparationTwinProvision | None:
        result = await self._session.execute(
            select(PreparationTwinModel).where(
                PreparationTwinModel.tenant_id == tenant_id,
                PreparationTwinModel.student_id == student_id,
                PreparationTwinModel.exam_id == exam_id,
            )
        )
        row = result.scalar_one_or_none()
        return _map_twin(row) if row else None

    async def save(self, twin: PreparationTwinProvision) -> PreparationTwinProvision:
        row = await self._session.get(PreparationTwinModel, twin.id)
        if row is None:
            row = PreparationTwinModel(
                id=twin.id,
                tenant_id=twin.tenant_id,
                student_id=twin.student_id,
                exam_id=twin.exam_id,
                status=twin.status.value,
                academic_profile=twin.academic_profile,
                behavioral_profile=twin.behavioral_profile,
                prediction_profile=twin.prediction_profile,
                metadata_json=twin.metadata,
                projection_version=twin.projection_version,
                row_version=twin.row_version,
                last_rebuilt_at=twin.last_rebuilt_at,
                last_event_id_processed=twin.last_event_id_processed,
            )
            self._session.add(row)
        else:
            row.status = twin.status.value
            row.academic_profile = twin.academic_profile
            row.behavioral_profile = twin.behavioral_profile
            row.prediction_profile = twin.prediction_profile
            row.metadata_json = twin.metadata
            row.projection_version = twin.projection_version
            row.row_version = twin.row_version
            row.last_rebuilt_at = twin.last_rebuilt_at
            row.last_event_id_processed = twin.last_event_id_processed
        await self._session.flush()
        return _map_twin(row)


class SqlAlchemyStudentUnitOfWork(StudentUnitOfWorkPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.student_repo = SqlAlchemyStudentRepository(session)
        self.learning_graph_provision_repo = SqlAlchemyLearningGraphProvisionRepository(session)
        self.preparation_twin_repo = SqlAlchemyPreparationTwinProvisionRepository(session)

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
