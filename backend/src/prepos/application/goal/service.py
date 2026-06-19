from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from prepos.application.goal.dto import GoalResponse, GoalTrajectoryResponse, GoalMilestoneResponse, GoalUpsertRequest
from prepos.application.goal.milestone_service import MilestoneService
from prepos.application.goal.ports import GoalRepositoryPort
from prepos.application.scoring.forecast_probability_service import ForecastProbabilityService
from prepos.domain.goal.events import GoalUpdated
from prepos.events.outbox.publisher import OutboxPublisher


class GoalService:
    def __init__(
        self,
        *,
        goal_repo: GoalRepositoryPort,
        milestone_service: MilestoneService | None = None,
        forecast_probability_service: ForecastProbabilityService | None = None,
        outbox: OutboxPublisher,
    ) -> None:
        self._goal_repo = goal_repo
        self._milestone_service = milestone_service
        self._forecast_probability_service = forecast_probability_service
        self._outbox = outbox

    async def create_goal(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        request: GoalUpsertRequest,
        correlation_id: str,
        causation_id: str | None = None,
    ) -> GoalResponse:
        return await self._upsert_goal(
            tenant_id=tenant_id,
            student_id=student_id,
            request=request,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )

    async def update_goal(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        request: GoalUpsertRequest,
        correlation_id: str,
        causation_id: str | None = None,
    ) -> GoalResponse:
        return await self._upsert_goal(
            tenant_id=tenant_id,
            student_id=student_id,
            request=request,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )

    async def get_goal(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> GoalResponse | None:
        goal = await self._goal_repo.get_goal(tenant_id, student_id, exam_id)
        if goal is None:
            return None
        response = self._to_response(goal)
        updates: dict[str, object] = {}

        if self._milestone_service is not None:
            snapshot = await self._milestone_service.compute_milestones(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
            )
            if snapshot is not None:
                updates["trajectory"] = GoalTrajectoryResponse(
                    required_gain=snapshot.required_gain,
                    expected_daily_progress=snapshot.expected_daily_progress,
                    expected_weekly_progress=snapshot.expected_weekly_progress,
                )
                updates["milestones"] = [
                    GoalMilestoneResponse(
                        target_date=milestone.target_date,
                        target_readiness=milestone.target_readiness,
                        expected_score=milestone.expected_score,
                    )
                    for milestone in snapshot.milestones
                ]

        if self._forecast_probability_service is not None:
            probability = await self._forecast_probability_service.compute_forecast_probability(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
            )
            if probability is not None:
                updates["goal_probability"] = probability.goal_probability
                updates["goal_likelihood"] = probability.goal_likelihood.value

        if not updates:
            return response
        return response.model_copy(update=updates)

    async def _upsert_goal(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        request: GoalUpsertRequest,
        correlation_id: str,
        causation_id: str | None,
    ) -> GoalResponse:
        goal = await self._goal_repo.upsert_goal(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=request.exam_id,
            target_readiness_score=request.target_readiness_score,
            target_date=request.target_date,
            daily_capacity_minutes=request.daily_capacity_minutes,
        )
        await self._outbox.enqueue_goal_updated(
            GoalUpdated(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=request.exam_id,
                target_readiness_score=goal.target_readiness_score,
                target_date=goal.target_date,
                daily_capacity_minutes=goal.daily_capacity_minutes,
                correlation_id=correlation_id,
                causation_id=causation_id,
                occurred_at=datetime.now(UTC),
            )
        )
        return self._to_response(goal)

    @staticmethod
    def _to_response(goal: object) -> GoalResponse:
        from prepos.domain.goal.entities import PreparationGoal

        assert isinstance(goal, PreparationGoal)
        return GoalResponse(
            exam_id=goal.exam_id,
            target_readiness_score=goal.target_readiness_score,
            target_date=goal.target_date,
            daily_capacity_minutes=goal.daily_capacity_minutes,
            created_at=goal.created_at,
            updated_at=goal.updated_at,
        )
