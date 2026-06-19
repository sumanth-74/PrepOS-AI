from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from prepos.application.goal.milestone_service import MilestoneService
from prepos.application.goal.ports import GoalRepositoryPort
from prepos.application.learning_graph.read_services import LearningGraphReadService
from prepos.application.learning_graph.readiness import compute_readiness_from_snapshot
from prepos.application.revision_queue.ports import RevisionQueueRepositoryPort
from prepos.application.scoring.forecast_probability_service import ForecastProbabilityService
from prepos.application.study_plan.ports import StudyPlanExecutionRepositoryPort, StudyPlanRepositoryPort
from prepos.domain.goal.trajectory_v1 import compute_goal_trajectory_v1
from prepos.domain.learning_graph.entities import LearningGraphReadinessSnapshot
from prepos.domain.scoring.readiness_forecast_v1 import compute_days_remaining
from prepos.application.twin.personalization_service import PersonalizationService
from prepos.domain.twin.decision_engine_v1 import TwinDecision, TwinDecisionInputs, select_twin_decision_v1
from prepos.domain.twin.events import TwinDecisionUpdated
from prepos.events.outbox.publisher import OutboxPublisher


@dataclass(frozen=True, slots=True)
class TwinDecisionSnapshot:
    decision: TwinDecision


class TwinDecisionService:
    def __init__(
        self,
        *,
        read_service: LearningGraphReadService,
        goal_repo: GoalRepositoryPort,
        study_plan_repo: StudyPlanRepositoryPort,
        execution_repo: StudyPlanExecutionRepositoryPort,
        queue_repo: RevisionQueueRepositoryPort,
        forecast_probability_service: ForecastProbabilityService,
        milestone_service: MilestoneService,
        outbox: OutboxPublisher,
        personalization_service: PersonalizationService | None = None,
    ) -> None:
        self._read_service = read_service
        self._goal_repo = goal_repo
        self._study_plan_repo = study_plan_repo
        self._execution_repo = execution_repo
        self._queue_repo = queue_repo
        self._forecast_probability_service = forecast_probability_service
        self._milestone_service = milestone_service
        self._outbox = outbox
        self._personalization_service = personalization_service

    async def compute_decision(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        current_time: datetime | None = None,
    ) -> TwinDecisionSnapshot | None:
        goal = await self._goal_repo.get_goal(tenant_id, student_id, exam_id)
        if goal is None:
            return None

        now = current_time or datetime.now(UTC)
        snapshot_response = await self._read_service.get_readiness_snapshot(
            tenant_id=tenant_id,
            student_id=student_id,
            current_time=now,
        )
        lg_snapshot = LearningGraphReadinessSnapshot(
            average_mastery=snapshot_response.average_mastery,
            average_retention=snapshot_response.average_retention,
            average_confidence=snapshot_response.average_confidence,
            rated_node_count=snapshot_response.rated_node_count,
            total_node_count=snapshot_response.total_node_count,
        )
        readiness_result, _ = compute_readiness_from_snapshot(lg_snapshot)
        current_readiness = readiness_result.overall_score or Decimal("0")

        total_estimated_gain = Decimal("0")
        plan_summary = await self._study_plan_repo.get_study_plan_summary(
            tenant_id,
            student_id,
            exam_id,
        )
        if plan_summary is not None:
            total_estimated_gain = plan_summary.total_estimated_gain

        days_remaining = compute_days_remaining(target_date=goal.target_date, current_time=now)
        trajectory = compute_goal_trajectory_v1(
            current_readiness=current_readiness,
            target_readiness=goal.target_readiness_score,
            days_remaining=days_remaining,
        )

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

        behavior = await self._execution_repo.get_behavior_metrics(
            tenant_id,
            student_id,
            exam_id,
        )
        due_revision_count = await self._queue_repo.count_due(
            tenant_id,
            student_id,
            exam_id=exam_id,
        )
        high_risk_concept_count = await self._queue_repo.count_high_risk(
            tenant_id,
            student_id,
            exam_id=exam_id,
        )

        learning_style = None
        risk_profile = None
        if self._personalization_service is not None:
            personalization = await self._personalization_service.compute_personalization(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
            )
            learning_style = personalization.summary.learning_style
            risk_profile = personalization.summary.risk_profile

        decision = select_twin_decision_v1(
            TwinDecisionInputs(
                due_revision_count=due_revision_count,
                high_risk_concept_count=high_risk_concept_count,
                coverage_subscore=readiness_result.coverage_subscore,
                completion_rate=behavior.completion_rate,
                goal_probability=goal_probability,
                milestone_status=milestone_status,
                retention_subscore=readiness_result.retention_subscore,
                total_estimated_gain=total_estimated_gain,
                required_gain=trajectory.required_gain,
                learning_style=learning_style,
                risk_profile=risk_profile,
            )
        )
        return TwinDecisionSnapshot(decision=decision)

    async def publish_twin_decision_updated(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        correlation_id: str,
        causation_id: str | None,
        current_time: datetime | None = None,
    ) -> TwinDecisionSnapshot | None:
        snapshot = await self.compute_decision(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            current_time=current_time,
        )
        if snapshot is None:
            return None

        decision = snapshot.decision
        await self._outbox.enqueue_twin_decision_updated(
            TwinDecisionUpdated(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                decision_type=decision.decision_type,
                decision_score=decision.decision_score,
                expected_readiness_gain=decision.expected_readiness_gain,
                expected_score_gain=decision.expected_score_gain,
                explanation=decision.explanation,
                correlation_id=correlation_id,
                causation_id=causation_id,
                occurred_at=current_time or datetime.now(UTC),
            )
        )
        return snapshot
