from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from prepos.application.learning_graph.read_services import LearningGraphReadService
from prepos.application.learning_graph.readiness import compute_readiness_from_snapshot
from prepos.application.study_plan.ports import StudyPlanRepositoryPort
from prepos.application.twin.ports import TwinRecommendationRepositoryPort
from prepos.domain.learning_graph.entities import LearningGraphReadinessSnapshot
from prepos.domain.scoring.events import PredictedScoreUpdated
from prepos.domain.scoring.exam_simulation_v1 import ExamSimulationInputs, compute_exam_simulations_v1
from prepos.domain.scoring.predicted_score_explanations_v1 import explain_predicted_score_v1
from prepos.domain.scoring.predicted_score_v1 import (
    PredictedScoreInputs,
    PreparationRisk,
    classify_preparation_risk,
    compute_predicted_score_range,
    compute_predicted_score_v1,
)
from prepos.domain.scoring.readiness_impact_v1 import compute_total_estimated_gain
from prepos.events.outbox.publisher import OutboxPublisher


@dataclass(frozen=True, slots=True)
class PredictedScoreSnapshot:
    expected_score: Decimal
    low_score: Decimal
    high_score: Decimal
    risk_level: PreparationRisk
    current_state: Decimal
    complete_recommendations: Decimal
    no_study: Decimal
    explanation: str


class PredictedScoreService:
    def __init__(
        self,
        *,
        read_service: LearningGraphReadService,
        recommendation_repo: TwinRecommendationRepositoryPort,
        study_plan_repo: StudyPlanRepositoryPort,
        outbox: OutboxPublisher,
    ) -> None:
        self._read_service = read_service
        self._recommendation_repo = recommendation_repo
        self._study_plan_repo = study_plan_repo
        self._outbox = outbox

    async def compute_predicted_score(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        current_time: datetime | None = None,
    ) -> PredictedScoreSnapshot | None:
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

        predicted = compute_predicted_score_v1(
            PredictedScoreInputs(
                readiness_score=readiness_result.overall_score,
                coverage_subscore=readiness_result.coverage_subscore,
                confidence_subscore=readiness_result.confidence_subscore,
            )
        )
        if predicted is None:
            return None

        score_range = compute_predicted_score_range(
            predicted_score=predicted,
            confidence_subscore=readiness_result.confidence_subscore,
        )
        total_estimated_gain = await self._resolve_total_estimated_gain(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
        )
        simulations = compute_exam_simulations_v1(
            ExamSimulationInputs(
                current_predicted_score=predicted,
                total_estimated_gain=total_estimated_gain,
                retention_subscore=readiness_result.retention_subscore,
            )
        )
        explanation = explain_predicted_score_v1(
            expected_score=score_range.expected_score,
            complete_recommendations_score=simulations.complete_recommendations,
            confidence_subscore=readiness_result.confidence_subscore,
        )
        return PredictedScoreSnapshot(
            expected_score=score_range.expected_score,
            low_score=score_range.low_score,
            high_score=score_range.high_score,
            risk_level=classify_preparation_risk(readiness_result.overall_score),
            current_state=simulations.current_state,
            complete_recommendations=simulations.complete_recommendations,
            no_study=simulations.no_study,
            explanation=explanation,
        )

    async def publish_predicted_score_updated(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        correlation_id: str,
        causation_id: str | None,
        current_time: datetime | None = None,
    ) -> PredictedScoreSnapshot | None:
        snapshot = await self.compute_predicted_score(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            current_time=current_time,
        )
        if snapshot is None:
            return None

        await self._outbox.enqueue_predicted_score_updated(
            PredictedScoreUpdated(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                expected_score=snapshot.expected_score,
                low_score=snapshot.low_score,
                high_score=snapshot.high_score,
                risk_level=snapshot.risk_level,
                current_state=snapshot.current_state,
                complete_recommendations=snapshot.complete_recommendations,
                no_study=snapshot.no_study,
                explanation=snapshot.explanation,
                correlation_id=correlation_id,
                causation_id=causation_id,
                occurred_at=current_time or datetime.now(UTC),
            )
        )
        return snapshot

    async def _resolve_total_estimated_gain(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> Decimal:
        plan_summary = await self._study_plan_repo.get_study_plan_summary(
            tenant_id,
            student_id,
            exam_id,
        )
        if plan_summary is not None and plan_summary.total_estimated_gain > Decimal("0"):
            return plan_summary.total_estimated_gain

        recommendation_summary = await self._recommendation_repo.get_recommendation_summary(
            tenant_id,
            student_id,
            exam_id,
            top_limit=100,
        )
        return compute_total_estimated_gain(
            tuple(item.readiness_gain for item in recommendation_summary.top_recommendations),
        )
