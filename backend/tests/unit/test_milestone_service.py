from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from prepos.application.goal.milestone_service import MilestoneService
from prepos.application.goal.service import GoalService
from prepos.domain.goal.entities import PreparationGoal
from prepos.domain.goal.events import MilestoneUpdated
from prepos.domain.goal.milestones_v1 import Milestone, MilestoneStatus


@pytest.mark.asyncio
async def test_get_goal_includes_trajectory_and_milestones() -> None:
    tenant_id = uuid4()
    student_id = uuid4()
    now = datetime(2026, 6, 18, tzinfo=UTC)
    goal = PreparationGoal(
        id=uuid4(),
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id="neet",
        target_readiness_score=Decimal("85"),
        target_date=date(2026, 8, 17),
        daily_capacity_minutes=120,
        created_at=now,
        updated_at=now,
    )
    goal_repo = AsyncMock()
    goal_repo.get_goal = AsyncMock(return_value=goal)

    milestone_service = AsyncMock()
    milestone_service.compute_milestones = AsyncMock(
        return_value=type(
            "Snapshot",
            (),
            {
                "required_gain": Decimal("14.50"),
                "expected_daily_progress": Decimal("0.24"),
                "expected_weekly_progress": Decimal("1.68"),
                "milestones": (
                    Milestone(
                        target_date=date(2026, 6, 25),
                        target_readiness=Decimal("62.92"),
                        expected_score=Decimal("60.00"),
                    ),
                ),
                "milestone_status": MilestoneStatus.BEHIND,
                "current_gap": Decimal("4.92"),
                "next_milestone_date": date(2026, 6, 25),
                "next_milestone_target": Decimal("62.92"),
                "explanation": "You are 4.92 readiness points behind the current milestone.",
            },
        )()
    )

    service = GoalService(
        goal_repo=goal_repo,
        milestone_service=milestone_service,
        outbox=AsyncMock(),
    )
    response = await service.get_goal(
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id="neet",
    )

    assert response is not None
    assert response.trajectory is not None
    assert response.trajectory.expected_weekly_progress == Decimal("1.68")
    assert len(response.milestones) == 1
    assert response.milestones[0].target_readiness == Decimal("62.92")


@pytest.mark.asyncio
async def test_publish_milestone_updated_emits_event() -> None:
    tenant_id = uuid4()
    student_id = uuid4()
    now = datetime(2026, 6, 18, tzinfo=UTC)
    goal = PreparationGoal(
        id=uuid4(),
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id="neet",
        target_readiness_score=Decimal("85"),
        target_date=date(2026, 8, 17),
        daily_capacity_minutes=120,
        created_at=now,
        updated_at=now,
    )
    goal_repo = AsyncMock()
    goal_repo.get_goal = AsyncMock(return_value=goal)
    read_service = AsyncMock()
    read_service.get_readiness_snapshot = AsyncMock(
        return_value=AsyncMock(
            average_mastery=Decimal("80"),
            average_retention=Decimal("55"),
            average_confidence=Decimal("70"),
            rated_node_count=150,
            total_node_count=300,
        )
    )
    outbox = AsyncMock()
    outbox.enqueue_milestone_updated = AsyncMock()

    service = MilestoneService(
        read_service=read_service,
        goal_repo=goal_repo,
        outbox=outbox,
    )
    await service.publish_milestone_updated(
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id="neet",
        correlation_id="corr",
        causation_id="cause",
        current_time=now,
    )

    outbox.enqueue_milestone_updated.assert_awaited_once()
    event = outbox.enqueue_milestone_updated.await_args.args[0]
    assert isinstance(event, MilestoneUpdated)
    assert event.exam_id == "neet"
    assert event.expected_weekly_progress > Decimal("0")
