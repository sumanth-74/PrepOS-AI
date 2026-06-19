from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from prepos.application.study_plan.ports import StudyPlanExecutionRepositoryPort
from prepos.application.twin.intervention_history_ports import InterventionHistoryRepositoryPort
from prepos.domain.twin.behavior_profile_explanations_v1 import explain_behavior_profile_v1
from prepos.domain.twin.behavior_profile_v1 import BehaviorProfile, BehaviorProfileInputs, build_behavior_profile_v1
from prepos.domain.twin.events import BehaviorProfileUpdated
from prepos.events.outbox.publisher import OutboxPublisher


@dataclass(frozen=True, slots=True)
class BehaviorProfileSnapshot:
    profile: BehaviorProfile
    explanation: str


class BehaviorProfileService:
    def __init__(
        self,
        *,
        execution_repo: StudyPlanExecutionRepositoryPort,
        history_repo: InterventionHistoryRepositoryPort,
        outbox: OutboxPublisher,
    ) -> None:
        self._execution_repo = execution_repo
        self._history_repo = history_repo
        self._outbox = outbox

    async def compute_profile(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> BehaviorProfileSnapshot:
        executions = await self._execution_repo.list_executions(tenant_id, student_id, exam_id)
        outcomes = await self._history_repo.list_outcomes(tenant_id, student_id, exam_id)
        effectiveness_by_type = await self._history_repo.get_average_effectiveness_by_type(
            tenant_id,
            student_id,
            exam_id,
        )
        profile = build_behavior_profile_v1(
            BehaviorProfileInputs(
                executions=executions,
                intervention_outcomes=outcomes,
                effectiveness_by_type=effectiveness_by_type,
            )
        )
        explanation = explain_behavior_profile_v1(
            learning_style=profile.learning_style,
            risk_profile=profile.risk_profile,
            consistency_score=profile.consistency_score,
            revision_adherence_score=profile.revision_adherence_score,
        )
        return BehaviorProfileSnapshot(profile=profile, explanation=explanation)

    async def publish_behavior_profile_updated(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        correlation_id: str,
        causation_id: str | None,
        current_time: datetime | None = None,
    ) -> BehaviorProfileSnapshot:
        snapshot = await self.compute_profile(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
        )
        profile = snapshot.profile
        await self._outbox.enqueue_behavior_profile_updated(
            BehaviorProfileUpdated(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                consistency_score=profile.consistency_score,
                discipline_score=profile.discipline_score,
                revision_adherence_score=profile.revision_adherence_score,
                weakness_recovery_score=profile.weakness_recovery_score,
                engagement_score=profile.engagement_score,
                learning_style=profile.learning_style,
                risk_profile=profile.risk_profile,
                explanation=snapshot.explanation,
                correlation_id=correlation_id,
                causation_id=causation_id,
                occurred_at=current_time or datetime.now(UTC),
            )
        )
        return snapshot
