from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from prepos.application.goal.service import GoalService
from prepos.application.scoring.forecast_probability_service import ForecastProbabilityService
from prepos.domain.goal.entities import PreparationGoal
from prepos.domain.scoring.events import ForecastProbabilityUpdated
from prepos.domain.scoring.forecast_probability_v1 import GoalLikelihood


@pytest.mark.asyncio
async def test_get_goal_includes_goal_probability() -> None:
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

    forecast_probability_service = AsyncMock()
    forecast_probability_service.compute_forecast_probability = AsyncMock(
        return_value=type(
            "Snapshot",
            (),
            {
                "goal_probability": Decimal("72.50"),
                "goal_likelihood": GoalLikelihood.LIKELY,
            },
        )()
    )

    service = GoalService(
        goal_repo=goal_repo,
        forecast_probability_service=forecast_probability_service,
        outbox=AsyncMock(),
    )
    response = await service.get_goal(
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id="neet",
    )

    assert response is not None
    assert response.goal_probability == Decimal("72.50")
    assert response.goal_likelihood == "LIKELY"


@pytest.mark.asyncio
async def test_publish_forecast_probability_updated_emits_event() -> None:
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
    study_plan_repo = AsyncMock()
    study_plan_repo.get_study_plan_summary = AsyncMock(
        return_value=AsyncMock(total_estimated_gain=Decimal("4.8"))
    )
    outbox = AsyncMock()
    outbox.enqueue_forecast_probability_updated = AsyncMock()

    service = ForecastProbabilityService(
        read_service=read_service,
        goal_repo=goal_repo,
        study_plan_repo=study_plan_repo,
        outbox=outbox,
    )
    await service.publish_forecast_probability_updated(
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id="neet",
        correlation_id="corr",
        causation_id="cause",
        current_time=now,
    )

    outbox.enqueue_forecast_probability_updated.assert_awaited_once()
    event = outbox.enqueue_forecast_probability_updated.await_args.args[0]
    assert isinstance(event, ForecastProbabilityUpdated)
    assert event.exam_id == "neet"
    assert event.goal_likelihood == GoalLikelihood.LIKELY
