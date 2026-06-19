from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from prepos.domain.learning_graph.events import (
    AssessmentCompleted,
    PYQDataChanged,
    RevisionCompleted,
    StudySessionLogged,
)
from prepos.events.outbox.publisher import OutboxPublisher


class LearningGraphActivityService:
    """Publishes learning-graph ingress events to the outbox for handler processing."""

    def __init__(self, *, outbox: OutboxPublisher) -> None:
        self._outbox = outbox

    async def publish_assessment_completed(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        concept_id: str,
        mcq_correct: bool,
        self_confidence: Decimal | None,
        correlation_id: str,
        causation_id: str | None,
        current_time: datetime | None = None,
    ) -> None:
        now = current_time or datetime.now(UTC)
        await self._outbox.enqueue_assessment_completed(
            AssessmentCompleted(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                concept_id=concept_id,
                mcq_correct=mcq_correct,
                self_confidence=float(self_confidence) if self_confidence is not None else None,
                correlation_id=correlation_id,
                causation_id=causation_id,
                occurred_at=now,
            )
        )

    async def publish_revision_completed(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        concept_id: str,
        recall_grade: str,
        correlation_id: str,
        causation_id: str | None,
        current_time: datetime | None = None,
    ) -> None:
        now = current_time or datetime.now(UTC)
        await self._outbox.enqueue_revision_completed(
            RevisionCompleted(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                concept_id=concept_id,
                recall_grade=recall_grade,
                correlation_id=correlation_id,
                causation_id=causation_id,
                occurred_at=now,
            )
        )

    async def publish_study_session_logged(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        concept_id: str,
        engaged_minutes: int,
        correlation_id: str,
        causation_id: str | None,
        current_time: datetime | None = None,
    ) -> None:
        now = current_time or datetime.now(UTC)
        await self._outbox.enqueue_study_session_logged(
            StudySessionLogged(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                concept_id=concept_id,
                engaged_minutes=engaged_minutes,
                correlation_id=correlation_id,
                causation_id=causation_id,
                occurred_at=now,
            )
        )

    async def publish_pyq_data_changed(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        concept_id: str,
        global_importance: Decimal,
        correlation_id: str,
        causation_id: str | None,
        current_time: datetime | None = None,
    ) -> None:
        now = current_time or datetime.now(UTC)
        await self._outbox.enqueue_pyq_data_changed(
            PYQDataChanged(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                concept_id=concept_id,
                global_importance=float(global_importance),
                correlation_id=correlation_id,
                causation_id=causation_id,
                occurred_at=now,
            )
        )
