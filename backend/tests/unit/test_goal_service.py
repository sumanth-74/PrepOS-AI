from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from prepos.application.goal.service import GoalService
from prepos.domain.goal.entities import PreparationGoal
from prepos.domain.goal.events import GoalUpdated


@pytest.mark.asyncio
async def test_create_goal_emits_goal_updated() -> None:
    tenant_id = uuid4()
    student_id = uuid4()
    now = datetime(2026, 6, 18, tzinfo=UTC)
    goal = PreparationGoal(
        id=uuid4(),
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id="neet",
        target_readiness_score=Decimal("85"),
        target_date=date(2026, 9, 1),
        daily_capacity_minutes=120,
        created_at=now,
        updated_at=now,
    )
    goal_repo = AsyncMock()
    goal_repo.upsert_goal = AsyncMock(return_value=goal)
    outbox = AsyncMock()
    outbox.enqueue_goal_updated = AsyncMock()

    service = GoalService(goal_repo=goal_repo, outbox=outbox)
    from prepos.application.goal.dto import GoalUpsertRequest

    response = await service.create_goal(
        tenant_id=tenant_id,
        student_id=student_id,
        request=GoalUpsertRequest(
            exam_id="neet",
            target_readiness_score=Decimal("85"),
            target_date=date(2026, 9, 1),
            daily_capacity_minutes=120,
        ),
        correlation_id="corr",
    )

    assert response.exam_id == "neet"
    outbox.enqueue_goal_updated.assert_awaited_once()
    event = outbox.enqueue_goal_updated.await_args.args[0]
    assert isinstance(event, GoalUpdated)


@pytest.mark.asyncio
async def test_get_goal_returns_none_when_missing() -> None:
    goal_repo = AsyncMock()
    goal_repo.get_goal = AsyncMock(return_value=None)
    service = GoalService(goal_repo=goal_repo, outbox=AsyncMock())

    result = await service.get_goal(
        tenant_id=uuid4(),
        student_id=uuid4(),
        exam_id="neet",
    )
    assert result is None
