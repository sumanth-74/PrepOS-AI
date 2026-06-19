from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from prepos.application.twin.behavior_profile_service import BehaviorProfileService
from prepos.application.twin.intervention_history_ports import InterventionHistoryRepositoryPort
from prepos.domain.twin.events import PersonalizationUpdated
from prepos.domain.twin.personalization_explanations_v1 import explain_personalization_summary_v1
from prepos.domain.twin.personalized_scoring_v1 import (
    PersonalizationContext,
    PersonalizationSummary,
    build_effectiveness_by_activity,
    build_personalization_context,
    build_personalization_summary,
)
from prepos.events.outbox.publisher import OutboxPublisher


@dataclass(frozen=True, slots=True)
class PersonalizationSnapshot:
    context: PersonalizationContext
    summary: PersonalizationSummary
    explanation: str


class PersonalizationService:
    def __init__(
        self,
        *,
        behavior_profile_service: BehaviorProfileService,
        history_repo: InterventionHistoryRepositoryPort,
        outbox: OutboxPublisher,
    ) -> None:
        self._behavior_profile_service = behavior_profile_service
        self._history_repo = history_repo
        self._outbox = outbox

    async def compute_personalization(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> PersonalizationSnapshot:
        profile_snapshot = await self._behavior_profile_service.compute_profile(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
        )
        outcomes = await self._history_repo.list_outcomes(tenant_id, student_id, exam_id)
        effectiveness_by_activity = build_effectiveness_by_activity(outcomes)
        context = build_personalization_context(
            profile=profile_snapshot.profile,
            effectiveness_by_activity=effectiveness_by_activity,
        )
        summary = build_personalization_summary(
            profile=profile_snapshot.profile,
            effectiveness_by_activity=effectiveness_by_activity,
        )
        explanation = explain_personalization_summary_v1(
            learning_style=summary.learning_style,
            best_activity_type=summary.best_activity_type,
        )
        return PersonalizationSnapshot(
            context=context,
            summary=summary,
            explanation=explanation,
        )

    async def publish_personalization_updated(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        correlation_id: str,
        causation_id: str | None,
        current_time: datetime | None = None,
    ) -> PersonalizationSnapshot:
        snapshot = await self.compute_personalization(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
        )
        summary = snapshot.summary
        await self._outbox.enqueue_personalization_updated(
            PersonalizationUpdated(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                learning_style=summary.learning_style,
                risk_profile=summary.risk_profile,
                top_multiplier=summary.top_multiplier,
                best_activity_type=summary.best_activity_type,
                historical_effectiveness=summary.historical_effectiveness,
                explanation=snapshot.explanation,
                correlation_id=correlation_id,
                causation_id=causation_id,
                occurred_at=current_time or datetime.now(UTC),
            )
        )
        return snapshot
