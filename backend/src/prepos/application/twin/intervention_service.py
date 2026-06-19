from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from prepos.application.goal.milestone_service import MilestoneService
from prepos.application.revision_queue.ports import RevisionQueueRepositoryPort
from prepos.application.scoring.forecast_probability_service import ForecastProbabilityService
from prepos.application.study_plan.ports import StudyPlanRepositoryPort
from prepos.application.twin.decision_service import TwinDecisionService
from prepos.application.twin.personalization_service import PersonalizationService
from prepos.domain.twin.events import TwinInterventionUpdated
from prepos.domain.twin.interventions_v1 import TwinIntervention, TwinInterventionInputs, build_twin_intervention_v1
from prepos.events.outbox.publisher import OutboxPublisher


@dataclass(frozen=True, slots=True)
class TwinInterventionSnapshot:
    intervention: TwinIntervention


class TwinInterventionService:
    def __init__(
        self,
        *,
        decision_service: TwinDecisionService,
        study_plan_repo: StudyPlanRepositoryPort,
        queue_repo: RevisionQueueRepositoryPort,
        forecast_probability_service: ForecastProbabilityService,
        milestone_service: MilestoneService,
        outbox: OutboxPublisher,
        personalization_service: PersonalizationService | None = None,
    ) -> None:
        self._decision_service = decision_service
        self._study_plan_repo = study_plan_repo
        self._queue_repo = queue_repo
        self._forecast_probability_service = forecast_probability_service
        self._milestone_service = milestone_service
        self._outbox = outbox
        self._personalization_service = personalization_service

    async def compute_intervention(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        current_time: datetime | None = None,
    ) -> TwinInterventionSnapshot | None:
        decision_snapshot = await self._decision_service.compute_decision(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            current_time=current_time,
        )
        if decision_snapshot is None:
            return None

        now = current_time or datetime.now(UTC)
        probability_snapshot = await self._forecast_probability_service.compute_forecast_probability(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            current_time=now,
        )
        goal_probability = (
            probability_snapshot.goal_probability if probability_snapshot is not None else None
        )

        milestone_snapshot = await self._milestone_service.compute_milestones(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            current_time=now,
        )
        milestone_status = (
            milestone_snapshot.milestone_status if milestone_snapshot is not None else None
        )

        due_revision_count = await self._queue_repo.count_due(
            tenant_id,
            student_id,
            exam_id=exam_id,
        )

        daily_plan_count = 0
        plan_summary = await self._study_plan_repo.get_study_plan_summary(
            tenant_id,
            student_id,
            exam_id,
        )
        if plan_summary is not None:
            daily_plan_count = plan_summary.daily_item_count

        personalization = None
        if self._personalization_service is not None:
            snapshot = await self._personalization_service.compute_personalization(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
            )
            personalization = snapshot.context

        intervention = build_twin_intervention_v1(
            TwinInterventionInputs(
                decision=decision_snapshot.decision,
                goal_probability=goal_probability,
                milestone_status=milestone_status,
                due_revision_count=due_revision_count,
                daily_plan_count=daily_plan_count,
                personalization=personalization,
            )
        )
        return TwinInterventionSnapshot(intervention=intervention)

    async def publish_twin_intervention_updated(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        correlation_id: str,
        causation_id: str | None,
        current_time: datetime | None = None,
    ) -> TwinInterventionSnapshot | None:
        snapshot = await self.compute_intervention(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            current_time=current_time,
        )
        if snapshot is None:
            return None

        intervention = snapshot.intervention
        await self._outbox.enqueue_twin_intervention_updated(
            TwinInterventionUpdated(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                intervention_type=intervention.intervention_type,
                intervention_score=intervention.intervention_score,
                urgency=intervention.urgency,
                expected_readiness_gain=intervention.expected_readiness_gain,
                title=intervention.title,
                description=intervention.description,
                correlation_id=correlation_id,
                causation_id=causation_id,
                occurred_at=current_time or datetime.now(UTC),
            )
        )
        return snapshot
