from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from prepos.application.twin.intervention_history_ports import InterventionHistoryRepositoryPort
from prepos.application.twin.projection_ports import TwinProjectionRepositoryPort
from prepos.domain.scoring.common import round_score
from prepos.domain.twin.events import InterventionOptimizationUpdated
from prepos.domain.twin.intervention_optimizer_v1 import (
    compute_optimized_intervention_score_v1,
    select_best_intervention_type,
)
from prepos.events.outbox.publisher import OutboxPublisher


@dataclass(frozen=True, slots=True)
class InterventionOptimizationSnapshot:
    best_intervention: str
    historical_effectiveness: Decimal
    last_effectiveness_score: Decimal
    outcome_status: str
    optimized_intervention_score: Decimal


class InterventionOptimizationService:
    def __init__(
        self,
        *,
        projection_repo: TwinProjectionRepositoryPort,
        history_repo: InterventionHistoryRepositoryPort,
        outbox: OutboxPublisher,
    ) -> None:
        self._projection_repo = projection_repo
        self._history_repo = history_repo
        self._outbox = outbox

    async def compute_optimization(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> InterventionOptimizationSnapshot | None:
        twin = await self._projection_repo.get_projection(tenant_id, student_id, exam_id)
        if twin is None or twin.intervention_type is None or twin.intervention_score is None:
            return None

        latest = await self._history_repo.get_latest_outcome(tenant_id, student_id, exam_id)
        if latest is None:
            return None

        averages = await self._history_repo.get_average_effectiveness_by_type(
            tenant_id,
            student_id,
            exam_id,
        )
        best = select_best_intervention_type(averages)
        if best is None:
            return None

        best_intervention, historical_effectiveness = best
        optimized_score = compute_optimized_intervention_score_v1(
            intervention_score=twin.intervention_score,
            historical_effectiveness=historical_effectiveness,
        )
        return InterventionOptimizationSnapshot(
            best_intervention=best_intervention,
            historical_effectiveness=round_score(historical_effectiveness),
            last_effectiveness_score=latest.effectiveness_score,
            outcome_status=latest.outcome_status,
            optimized_intervention_score=optimized_score,
        )

    async def publish_intervention_optimization_updated(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        correlation_id: str,
        causation_id: str | None,
        current_time: datetime | None = None,
    ) -> InterventionOptimizationSnapshot | None:
        snapshot = await self.compute_optimization(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
        )
        if snapshot is None:
            return None

        await self._outbox.enqueue_intervention_optimization_updated(
            InterventionOptimizationUpdated(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                best_intervention=snapshot.best_intervention,
                historical_effectiveness=snapshot.historical_effectiveness,
                last_effectiveness_score=snapshot.last_effectiveness_score,
                outcome_status=snapshot.outcome_status,
                optimized_intervention_score=snapshot.optimized_intervention_score,
                correlation_id=correlation_id,
                causation_id=causation_id,
                occurred_at=current_time or datetime.now(UTC),
            )
        )
        return snapshot
