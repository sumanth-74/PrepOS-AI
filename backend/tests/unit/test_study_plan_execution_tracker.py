from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from prepos.application.study_plan.execution_tracker import StudyPlanExecutionTracker
from prepos.application.study_plan.ports import StudyBehaviorSummary
from prepos.domain.study_plan.events import StudyBehaviorUpdated, StudyPlanItemCompleted
from prepos.domain.study_plan.value_objects import ActivityType


@pytest.mark.asyncio
async def test_execution_tracker_persists_and_emits_behavior_updated() -> None:
    tenant_id = uuid4()
    student_id = uuid4()
    now = datetime(2026, 6, 18, tzinfo=UTC)
    execution_repo = AsyncMock()
    execution_repo.insert_execution = AsyncMock(side_effect=lambda record: record)
    execution_repo.get_behavior_summary = AsyncMock(
        return_value=StudyBehaviorSummary(
            completion_rate=Decimal("1.0000"),
            skip_rate=Decimal("0.0000"),
            average_minutes_variance=Decimal("0.1000"),
        )
    )
    outbox = AsyncMock()
    outbox.enqueue_study_behavior_updated = AsyncMock()

    tracker = StudyPlanExecutionTracker(execution_repo=execution_repo, outbox=outbox)
    await tracker.handle_item_completed(
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id="neet",
        concept_id="concept-a",
        activity_type=ActivityType.REVISION,
        planned_minutes=20,
        actual_minutes=25,
        completed_at=now,
        correlation_id="corr",
        causation_id="cause",
    )

    execution_repo.insert_execution.assert_awaited_once()
    outbox.enqueue_study_behavior_updated.assert_awaited_once()
    event = outbox.enqueue_study_behavior_updated.await_args.args[0]
    assert isinstance(event, StudyBehaviorUpdated)
    assert event.completion_rate == Decimal("1.0000")


@pytest.mark.asyncio
async def test_request_item_completed_enqueues_event() -> None:
    outbox = AsyncMock()
    outbox.enqueue_study_plan_item_completed = AsyncMock()
    tracker = StudyPlanExecutionTracker(execution_repo=AsyncMock(), outbox=outbox)
    now = datetime(2026, 6, 18, tzinfo=UTC)

    await tracker.request_item_completed(
        tenant_id=uuid4(),
        student_id=uuid4(),
        exam_id="neet",
        concept_id="concept-a",
        activity_type=ActivityType.REVISION,
        planned_minutes=20,
        actual_minutes=18,
        completed_at=now,
        correlation_id="corr",
        causation_id=None,
    )

    outbox.enqueue_study_plan_item_completed.assert_awaited_once()
    event = outbox.enqueue_study_plan_item_completed.await_args.args[0]
    assert isinstance(event, StudyPlanItemCompleted)
