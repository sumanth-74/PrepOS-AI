from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from prepos.application.learning_graph.read_services import LearningGraphReadService
from prepos.application.learning_graph.readiness import compute_readiness_from_snapshot
from prepos.application.scoring.predicted_score_service import PredictedScoreService
from prepos.application.study_plan.ports import StudyPlanExecutionRepositoryPort
from prepos.application.twin.intervention_history_ports import InterventionHistoryRepositoryPort
from prepos.application.twin.projection_ports import TwinProjectionRepositoryPort
from prepos.domain.learning_graph.entities import LearningGraphReadinessSnapshot
from prepos.domain.twin.events import InterventionOutcomeCalculated
from prepos.domain.twin.intervention_outcome_v1 import (
    InterventionOutcome,
    InterventionOutcomeInputs,
    compute_intervention_outcome_v1,
)
from prepos.domain.twin.intervention_types_v1 import TwinInterventionType
from prepos.domain.twin.twin_payload_v1 import extract_baseline_metrics
from prepos.events.outbox.publisher import OutboxPublisher


@dataclass(frozen=True, slots=True)
class InterventionOutcomeSnapshot:
    outcome: InterventionOutcome


class InterventionOutcomeService:
    def __init__(
        self,
        *,
        read_service: LearningGraphReadService,
        predicted_score_service: PredictedScoreService,
        execution_repo: StudyPlanExecutionRepositoryPort,
        projection_repo: TwinProjectionRepositoryPort,
        history_repo: InterventionHistoryRepositoryPort,
        outbox: OutboxPublisher,
    ) -> None:
        self._read_service = read_service
        self._predicted_score_service = predicted_score_service
        self._execution_repo = execution_repo
        self._projection_repo = projection_repo
        self._history_repo = history_repo
        self._outbox = outbox

    async def compute_outcome(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        current_time: datetime | None = None,
    ) -> InterventionOutcomeSnapshot | None:
        twin = await self._projection_repo.get_projection(tenant_id, student_id, exam_id)
        if twin is None or twin.intervention_type is None:
            return None

        baseline = twin.twin_payload.get("intervention_baseline")
        if not isinstance(baseline, dict):
            return None
        baseline_type = baseline.get("intervention_type")
        if baseline_type is not None and str(baseline_type) != twin.intervention_type:
            return None

        now = current_time or datetime.now(UTC)
        readiness_before, predicted_before, completion_before = extract_baseline_metrics(
            twin.twin_payload,
            readiness_score=twin.readiness_score,
        )

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
        readiness_after = readiness_result.overall_score or Decimal("0")

        predicted_snapshot = await self._predicted_score_service.compute_predicted_score(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            current_time=now,
        )
        predicted_after = (
            predicted_snapshot.expected_score if predicted_snapshot is not None else Decimal("0")
        )

        behavior = await self._execution_repo.get_behavior_metrics(
            tenant_id,
            student_id,
            exam_id,
        )
        completion_after = behavior.completion_rate

        outcome = compute_intervention_outcome_v1(
            InterventionOutcomeInputs(
                intervention_type=TwinInterventionType(twin.intervention_type),
                readiness_before=readiness_before,
                readiness_after=readiness_after,
                predicted_score_before=predicted_before,
                predicted_score_after=predicted_after,
                completion_rate_before=completion_before,
                completion_rate_after=completion_after,
            )
        )
        return InterventionOutcomeSnapshot(outcome=outcome)

    async def publish_intervention_outcome_calculated(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        correlation_id: str,
        causation_id: str | None,
        current_time: datetime | None = None,
    ) -> InterventionOutcomeSnapshot | None:
        snapshot = await self.compute_outcome(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            current_time=current_time,
        )
        if snapshot is None:
            return None

        now = current_time or datetime.now(UTC)
        outcome = snapshot.outcome
        await self._history_repo.save_outcome(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            intervention_type=outcome.intervention_type.value,
            effectiveness_score=outcome.effectiveness_score,
            readiness_delta=outcome.readiness_delta,
            predicted_score_delta=outcome.predicted_score_delta,
            completion_delta=outcome.completion_delta,
            outcome_status=outcome.outcome_status.value,
            created_at=now,
        )
        await self._outbox.enqueue_intervention_outcome_calculated(
            InterventionOutcomeCalculated(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                intervention_type=outcome.intervention_type,
                effectiveness_score=outcome.effectiveness_score,
                readiness_delta=outcome.readiness_delta,
                predicted_score_delta=outcome.predicted_score_delta,
                completion_delta=outcome.completion_delta,
                outcome_status=outcome.outcome_status,
                correlation_id=correlation_id,
                causation_id=causation_id,
                occurred_at=now,
            )
        )
        return snapshot
