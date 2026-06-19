from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from prepos.application.goal.ports import GoalRepositoryPort
from prepos.application.learning_graph.read_services import LearningGraphReadService
from prepos.application.learning_graph.readiness import compute_readiness_from_snapshot
from prepos.application.study_plan.ports import StudyPlanRepositoryPort
from prepos.domain.learning_graph.entities import LearningGraphReadinessSnapshot
from prepos.domain.scoring.events import ForecastProbabilityUpdated
from prepos.domain.scoring.forecast_explanations_v1 import explain_forecast_probability_v1
from prepos.domain.scoring.forecast_probability_v1 import (
    ForecastProbabilityInputs,
    ForecastScenarioInputs,
    GoalLikelihood,
    classify_goal_likelihood,
    compute_forecast_scenarios_v1,
    compute_goal_probability_v1,
    compute_predicted_score_distribution,
)
from prepos.domain.scoring.predicted_score_v1 import PredictedScoreInputs, compute_predicted_score_v1
from prepos.domain.scoring.readiness_forecast_v1 import ReadinessForecastInputs, compute_readiness_forecast_v1
from prepos.events.outbox.publisher import OutboxPublisher


@dataclass(frozen=True, slots=True)
class ForecastProbabilitySnapshot:
    goal_probability: Decimal
    goal_likelihood: GoalLikelihood
    best_case: Decimal
    expected: Decimal
    worst_case: Decimal
    optimistic_score: Decimal
    expected_score: Decimal
    pessimistic_score: Decimal
    explanation: str


class ForecastProbabilityService:
    def __init__(
        self,
        *,
        read_service: LearningGraphReadService,
        goal_repo: GoalRepositoryPort,
        study_plan_repo: StudyPlanRepositoryPort,
        outbox: OutboxPublisher,
    ) -> None:
        self._read_service = read_service
        self._goal_repo = goal_repo
        self._study_plan_repo = study_plan_repo
        self._outbox = outbox

    async def compute_forecast_probability(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        current_time: datetime | None = None,
    ) -> ForecastProbabilitySnapshot | None:
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

        forecast = compute_readiness_forecast_v1(
            ReadinessForecastInputs(
                current_readiness=current_readiness,
                total_estimated_gain=total_estimated_gain,
                target_readiness_score=goal.target_readiness_score,
                target_date=goal.target_date,
                current_time=now,
            )
        )
        goal_probability = compute_goal_probability_v1(
            ForecastProbabilityInputs(
                current_readiness=forecast.current_readiness,
                projected_readiness=forecast.projected_readiness,
                confidence_subscore=readiness_result.confidence_subscore,
                days_remaining=forecast.days_remaining,
            )
        )
        scenarios = compute_forecast_scenarios_v1(
            ForecastScenarioInputs(
                projected_readiness=forecast.projected_readiness,
                total_estimated_gain=total_estimated_gain,
                retention_subscore=readiness_result.retention_subscore,
            )
        )
        predicted = compute_predicted_score_v1(
            PredictedScoreInputs(
                readiness_score=readiness_result.overall_score,
                coverage_subscore=readiness_result.coverage_subscore,
                confidence_subscore=readiness_result.confidence_subscore,
            )
        )
        expected_score = predicted if predicted is not None else current_readiness
        score_distribution = compute_predicted_score_distribution(
            expected_score=expected_score,
            confidence_subscore=readiness_result.confidence_subscore,
        )
        explanation = explain_forecast_probability_v1(
            goal_probability=goal_probability,
            confidence_subscore=readiness_result.confidence_subscore,
            total_estimated_gain=total_estimated_gain,
        )
        return ForecastProbabilitySnapshot(
            goal_probability=goal_probability,
            goal_likelihood=classify_goal_likelihood(goal_probability),
            best_case=scenarios.best_case,
            expected=scenarios.expected,
            worst_case=scenarios.worst_case,
            optimistic_score=score_distribution.optimistic_score,
            expected_score=score_distribution.expected_score,
            pessimistic_score=score_distribution.pessimistic_score,
            explanation=explanation,
        )

    async def publish_forecast_probability_updated(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        correlation_id: str,
        causation_id: str | None,
        current_time: datetime | None = None,
    ) -> ForecastProbabilitySnapshot | None:
        snapshot = await self.compute_forecast_probability(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            current_time=current_time,
        )
        if snapshot is None:
            return None

        await self._outbox.enqueue_forecast_probability_updated(
            ForecastProbabilityUpdated(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                goal_probability=snapshot.goal_probability,
                goal_likelihood=snapshot.goal_likelihood,
                best_case=snapshot.best_case,
                expected=snapshot.expected,
                worst_case=snapshot.worst_case,
                optimistic_score=snapshot.optimistic_score,
                expected_score=snapshot.expected_score,
                pessimistic_score=snapshot.pessimistic_score,
                explanation=snapshot.explanation,
                correlation_id=correlation_id,
                causation_id=causation_id,
                occurred_at=current_time or datetime.now(UTC),
            )
        )
        return snapshot
