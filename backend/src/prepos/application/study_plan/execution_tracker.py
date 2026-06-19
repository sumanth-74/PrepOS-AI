from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from prepos.application.study_plan.ports import StudyPlanExecutionRepositoryPort
from prepos.domain.study_plan.entities import StudyPlanExecutionRecord
from prepos.domain.study_plan.events import (
    StudyBehaviorUpdated,
    StudyPlanItemCompleted,
    StudyPlanItemSkipped,
)
from prepos.domain.study_plan.value_objects import ActivityType, ExecutionStatus
from prepos.events.outbox.publisher import OutboxPublisher


class StudyPlanExecutionTracker:
    """Persists study plan execution and emits behavior update events."""

    def __init__(
        self,
        *,
        execution_repo: StudyPlanExecutionRepositoryPort,
        outbox: OutboxPublisher,
    ) -> None:
        self._execution_repo = execution_repo
        self._outbox = outbox

    async def request_item_completed(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        concept_id: str,
        activity_type: ActivityType,
        planned_minutes: int,
        actual_minutes: int,
        completed_at: datetime,
        correlation_id: str,
        causation_id: str | None,
    ) -> None:
        await self._outbox.enqueue_study_plan_item_completed(
            StudyPlanItemCompleted(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                concept_id=concept_id,
                activity_type=activity_type,
                planned_minutes=planned_minutes,
                actual_minutes=actual_minutes,
                completed_at=completed_at,
                correlation_id=correlation_id,
                causation_id=causation_id,
                occurred_at=datetime.now(UTC),
            )
        )

    async def request_item_skipped(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        concept_id: str,
        activity_type: ActivityType,
        planned_minutes: int,
        actual_minutes: int,
        completed_at: datetime,
        correlation_id: str,
        causation_id: str | None,
    ) -> None:
        await self._outbox.enqueue_study_plan_item_skipped(
            StudyPlanItemSkipped(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                concept_id=concept_id,
                activity_type=activity_type,
                planned_minutes=planned_minutes,
                actual_minutes=actual_minutes,
                completed_at=completed_at,
                correlation_id=correlation_id,
                causation_id=causation_id,
                occurred_at=datetime.now(UTC),
            )
        )

    async def handle_item_completed(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        concept_id: str,
        activity_type: ActivityType,
        planned_minutes: int,
        actual_minutes: int,
        completed_at: datetime,
        correlation_id: str,
        causation_id: str | None,
    ) -> StudyPlanExecutionRecord:
        record = StudyPlanExecutionRecord(
            id=uuid4(),
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            concept_id=concept_id,
            activity_type=activity_type,
            planned_minutes=planned_minutes,
            actual_minutes=actual_minutes,
            status=ExecutionStatus.COMPLETED,
            completed_at=completed_at,
        )
        persisted = await self._execution_repo.insert_execution(record)
        await self._emit_behavior_updated(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )
        return persisted

    async def handle_item_skipped(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        concept_id: str,
        activity_type: ActivityType,
        planned_minutes: int,
        actual_minutes: int,
        completed_at: datetime,
        correlation_id: str,
        causation_id: str | None,
    ) -> StudyPlanExecutionRecord:
        record = StudyPlanExecutionRecord(
            id=uuid4(),
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            concept_id=concept_id,
            activity_type=activity_type,
            planned_minutes=planned_minutes,
            actual_minutes=actual_minutes,
            status=ExecutionStatus.SKIPPED,
            completed_at=completed_at,
        )
        persisted = await self._execution_repo.insert_execution(record)
        await self._emit_behavior_updated(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )
        return persisted

    async def _emit_behavior_updated(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        correlation_id: str,
        causation_id: str | None,
    ) -> None:
        summary = await self._execution_repo.get_behavior_summary(tenant_id, student_id, exam_id)
        await self._outbox.enqueue_study_behavior_updated(
            StudyBehaviorUpdated(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                completion_rate=summary.completion_rate,
                skip_rate=summary.skip_rate,
                average_minutes_variance=summary.average_minutes_variance,
                correlation_id=correlation_id,
                causation_id=causation_id,
                occurred_at=datetime.now(UTC),
            )
        )
