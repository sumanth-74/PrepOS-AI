from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

from prepos.application.goal.ports import GoalRepositoryPort
from prepos.application.learning_graph.read_services import LearningGraphReadService
from prepos.application.learning_graph.readiness import compute_readiness_from_snapshot
from prepos.domain.goal.events import MilestoneUpdated
from prepos.domain.goal.milestone_explanations_v1 import explain_milestone_status_v1
from prepos.domain.goal.milestones_v1 import (
    Milestone,
    MilestoneGenerationInputs,
    MilestoneStatus,
    compute_milestone_status_v1,
    generate_milestones_v1,
    resolve_next_milestone,
)
from prepos.domain.goal.trajectory_v1 import GoalTrajectoryResult, compute_goal_trajectory_v1
from prepos.domain.learning_graph.entities import LearningGraphReadinessSnapshot
from prepos.domain.scoring.readiness_forecast_v1 import compute_days_remaining
from prepos.events.outbox.publisher import OutboxPublisher


@dataclass(frozen=True, slots=True)
class MilestoneSnapshot:
    required_gain: Decimal
    expected_daily_progress: Decimal
    expected_weekly_progress: Decimal
    milestones: tuple[Milestone, ...]
    milestone_status: MilestoneStatus
    current_gap: Decimal
    next_milestone_date: date | None
    next_milestone_target: Decimal | None
    explanation: str


class MilestoneService:
    def __init__(
        self,
        *,
        read_service: LearningGraphReadService,
        goal_repo: GoalRepositoryPort,
        outbox: OutboxPublisher,
    ) -> None:
        self._read_service = read_service
        self._goal_repo = goal_repo
        self._outbox = outbox

    async def compute_milestones(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        current_time: datetime | None = None,
    ) -> MilestoneSnapshot | None:
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
        days_remaining = compute_days_remaining(target_date=goal.target_date, current_time=now)

        trajectory = compute_goal_trajectory_v1(
            current_readiness=current_readiness,
            target_readiness=goal.target_readiness_score,
            days_remaining=days_remaining,
        )
        milestones = generate_milestones_v1(
            MilestoneGenerationInputs(
                current_readiness=current_readiness,
                target_readiness=goal.target_readiness_score,
                target_date=goal.target_date,
                current_time=now,
                coverage_subscore=readiness_result.coverage_subscore,
                confidence_subscore=readiness_result.confidence_subscore,
            )
        )
        status_result = compute_milestone_status_v1(
            actual_readiness=current_readiness,
            milestones=milestones,
            current_time=now,
        )
        next_milestone = resolve_next_milestone(milestones, current_time=now)
        explanation = explain_milestone_status_v1(
            status=status_result.status,
            current_gap=status_result.current_gap,
        )
        return MilestoneSnapshot(
            required_gain=trajectory.required_gain,
            expected_daily_progress=trajectory.expected_daily_progress,
            expected_weekly_progress=trajectory.expected_weekly_progress,
            milestones=milestones,
            milestone_status=status_result.status,
            current_gap=status_result.current_gap,
            next_milestone_date=next_milestone.target_date if next_milestone is not None else None,
            next_milestone_target=(
                next_milestone.target_readiness if next_milestone is not None else None
            ),
            explanation=explanation,
        )

    async def publish_milestone_updated(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        correlation_id: str,
        causation_id: str | None,
        current_time: datetime | None = None,
    ) -> MilestoneSnapshot | None:
        snapshot = await self.compute_milestones(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            current_time=current_time,
        )
        if snapshot is None:
            return None

        await self._outbox.enqueue_milestone_updated(
            MilestoneUpdated(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                required_gain=snapshot.required_gain,
                expected_daily_progress=snapshot.expected_daily_progress,
                expected_weekly_progress=snapshot.expected_weekly_progress,
                milestones=_serialize_milestones(snapshot.milestones),
                milestone_status=snapshot.milestone_status,
                current_gap=snapshot.current_gap,
                next_milestone_date=snapshot.next_milestone_date,
                next_milestone_target=snapshot.next_milestone_target,
                explanation=snapshot.explanation,
                correlation_id=correlation_id,
                causation_id=causation_id,
                occurred_at=current_time or datetime.now(UTC),
            )
        )
        return snapshot


def _serialize_milestones(milestones: tuple[Milestone, ...]) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "target_date": milestone.target_date.isoformat(),
            "target_readiness": float(milestone.target_readiness),
            "expected_score": float(milestone.expected_score),
        }
        for milestone in milestones
    )


def milestone_snapshot_to_trajectory(snapshot: MilestoneSnapshot) -> GoalTrajectoryResult:
    return GoalTrajectoryResult(
        required_gain=snapshot.required_gain,
        expected_daily_progress=snapshot.expected_daily_progress,
        expected_weekly_progress=snapshot.expected_weekly_progress,
    )
