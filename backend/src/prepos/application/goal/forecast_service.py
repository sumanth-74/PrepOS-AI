from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from prepos.application.goal.ports import GoalRepositoryPort
from prepos.application.learning_graph.read_services import LearningGraphReadService
from prepos.application.learning_graph.readiness import compute_readiness_from_snapshot
from prepos.application.study_plan.ports import StudyPlanRepositoryPort
from prepos.domain.goal.adaptive_capacity_v1 import compute_adaptive_capacity_v1
from prepos.domain.goal.events import ForecastUpdated
from prepos.domain.goal.forecast_explanations_v1 import explain_forecast_v1
from prepos.domain.learning_graph.entities import LearningGraphReadinessSnapshot
from prepos.domain.scoring.readiness_forecast_v1 import ReadinessForecastInputs, compute_readiness_forecast_v1
from prepos.domain.study_plan.plan_generator_v1 import DEFAULT_DAILY_MINUTES
from prepos.events.outbox.publisher import OutboxPublisher


@dataclass(frozen=True, slots=True)
class ForecastSnapshot:
    target_readiness_score: Decimal
    target_date: object
    current_readiness: Decimal
    projected_readiness: Decimal
    gap_to_goal: Decimal
    on_track: bool
    days_remaining: int
    adaptive_capacity_minutes: int
    explanation: str


class ForecastService:
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

    async def compute_forecast(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        current_time: datetime | None = None,
    ) -> ForecastSnapshot | None:
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
        adaptive_capacity = compute_adaptive_capacity_v1(
            base_capacity_minutes=goal.daily_capacity_minutes,
            gap_to_goal=forecast.gap_to_goal,
            on_track=forecast.on_track,
        )
        explanation = explain_forecast_v1(
            projected_readiness=forecast.projected_readiness,
            target_readiness_score=goal.target_readiness_score,
            on_track=forecast.on_track,
            gap_to_goal=forecast.gap_to_goal,
            base_capacity_minutes=goal.daily_capacity_minutes,
            adaptive_capacity_minutes=adaptive_capacity,
        )
        return ForecastSnapshot(
            target_readiness_score=goal.target_readiness_score,
            target_date=goal.target_date,
            current_readiness=forecast.current_readiness,
            projected_readiness=forecast.projected_readiness,
            gap_to_goal=forecast.gap_to_goal,
            on_track=forecast.on_track,
            days_remaining=forecast.days_remaining,
            adaptive_capacity_minutes=adaptive_capacity,
            explanation=explanation,
        )

    async def publish_forecast_updated(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        correlation_id: str,
        causation_id: str | None,
        current_time: datetime | None = None,
    ) -> ForecastSnapshot | None:
        snapshot = await self.compute_forecast(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            current_time=current_time,
        )
        if snapshot is None:
            return None

        from datetime import date

        assert isinstance(snapshot.target_date, date)
        await self._outbox.enqueue_forecast_updated(
            ForecastUpdated(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                target_readiness_score=snapshot.target_readiness_score,
                target_date=snapshot.target_date,
                current_readiness=snapshot.current_readiness,
                projected_readiness=snapshot.projected_readiness,
                gap_to_goal=snapshot.gap_to_goal,
                on_track=snapshot.on_track,
                days_remaining=snapshot.days_remaining,
                adaptive_capacity_minutes=snapshot.adaptive_capacity_minutes,
                explanation=snapshot.explanation,
                correlation_id=correlation_id,
                causation_id=causation_id,
                occurred_at=current_time or datetime.now(UTC),
            )
        )
        return snapshot

    async def resolve_daily_capacity(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        current_time: datetime | None = None,
    ) -> int:
        snapshot = await self.compute_forecast(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            current_time=current_time,
        )
        if snapshot is None:
            return DEFAULT_DAILY_MINUTES
        return snapshot.adaptive_capacity_minutes
