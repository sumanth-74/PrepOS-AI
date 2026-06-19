from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from prepos.application.study_plan.ports import StudyBehaviorSummary, StudyPlanExecutionRepositoryPort
from prepos.domain.study_plan.behavior_metrics_v1 import StudyBehaviorMetrics, compute_study_behavior_metrics
from prepos.domain.study_plan.entities import StudyPlanExecutionRecord
from prepos.domain.study_plan.value_objects import ActivityType, ExecutionStatus
from prepos.infrastructure.db.models.study_plan_execution import StudentStudyPlanExecutionModel


def _map_row(row: StudentStudyPlanExecutionModel) -> StudyPlanExecutionRecord:
    return StudyPlanExecutionRecord(
        id=row.id,
        tenant_id=row.tenant_id,
        student_id=row.student_id,
        exam_id=row.exam_id,
        concept_id=row.concept_id,
        activity_type=ActivityType(row.activity_type),
        planned_minutes=row.planned_minutes,
        actual_minutes=row.actual_minutes,
        status=ExecutionStatus(row.status),
        completed_at=row.completed_at,
    )


class SqlAlchemyStudyPlanExecutionRepository(StudyPlanExecutionRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def insert_execution(self, record: StudyPlanExecutionRecord) -> StudyPlanExecutionRecord:
        now = datetime.now(UTC)
        row = StudentStudyPlanExecutionModel(
            id=record.id or uuid4(),
            tenant_id=record.tenant_id,
            student_id=record.student_id,
            exam_id=record.exam_id,
            concept_id=record.concept_id,
            activity_type=record.activity_type.value,
            planned_minutes=record.planned_minutes,
            actual_minutes=record.actual_minutes,
            status=record.status.value,
            completed_at=record.completed_at,
            created_at=now,
            updated_at=now,
        )
        self._session.add(row)
        await self._session.flush()
        return _map_row(row)

    async def list_executions(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> tuple[StudyPlanExecutionRecord, ...]:
        result = await self._session.execute(
            select(StudentStudyPlanExecutionModel)
            .where(
                StudentStudyPlanExecutionModel.tenant_id == tenant_id,
                StudentStudyPlanExecutionModel.student_id == student_id,
                StudentStudyPlanExecutionModel.exam_id == exam_id,
            )
            .order_by(StudentStudyPlanExecutionModel.completed_at.asc())
        )
        return tuple(_map_row(row) for row in result.scalars().all())

    async def get_behavior_metrics(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> StudyBehaviorMetrics:
        records = await self.list_executions(tenant_id, student_id, exam_id)
        return compute_study_behavior_metrics(records)

    async def get_behavior_summary(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> StudyBehaviorSummary:
        metrics = await self.get_behavior_metrics(tenant_id, student_id, exam_id)
        return StudyBehaviorSummary(
            completion_rate=metrics.completion_rate,
            skip_rate=metrics.skip_rate,
            average_minutes_variance=metrics.average_minutes_variance,
        )
