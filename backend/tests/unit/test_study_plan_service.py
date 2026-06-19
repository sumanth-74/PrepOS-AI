from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from prepos.application.study_plan.service import StudyPlanService
from prepos.domain.study_plan.entities import DailyPlanItem, StudyPlan, WeeklyPlanItem
from prepos.domain.study_plan.events import StudyPlanUpdated
from prepos.domain.study_plan.value_objects import ActivityType


@pytest.mark.asyncio
async def test_rebuild_study_plan_emits_study_plan_updated() -> None:
    tenant_id = uuid4()
    student_id = uuid4()
    exam_id = "neet"
    now = datetime(2026, 6, 18, tzinfo=UTC)
    plan = StudyPlan(
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id=exam_id,
        generated_at=now,
        daily_plan=(
            DailyPlanItem(
                concept_id="concept-a",
                activity_type=ActivityType.REVISION,
                estimated_minutes=20,
                priority_score=Decimal("80"),
                adaptive_priority=Decimal("80"),
                readiness_gain=Decimal("4"),
            ),
        ),
        weekly_plan=(
            WeeklyPlanItem(
                concept_id="concept-a",
                target_sessions=3,
                estimated_minutes=60,
                readiness_gain=Decimal("12"),
            ),
        ),
    )

    read_service = AsyncMock()
    read_service.list_rated_nodes = AsyncMock(return_value=())
    read_service.list_due_revisions = AsyncMock(return_value=())
    from types import SimpleNamespace

    read_service.get_readiness_snapshot = AsyncMock(
        return_value=SimpleNamespace(
            average_mastery=Decimal("50"),
            average_retention=Decimal("50"),
            average_confidence=Decimal("50"),
            rated_node_count=0,
            total_node_count=0,
        )
    )

    queue_repo = AsyncMock()
    queue_repo.list_due = AsyncMock(return_value=())

    study_plan_repo = AsyncMock()
    study_plan_repo.upsert_study_plan = AsyncMock(return_value=plan)

    execution_repo = AsyncMock()
    execution_repo.get_behavior_metrics = AsyncMock()

    forecast_service = AsyncMock()
    forecast_service.resolve_daily_capacity = AsyncMock(return_value=120)

    outbox = AsyncMock()
    outbox.enqueue_study_plan_updated = AsyncMock()

    service = StudyPlanService(
        read_service=read_service,
        recommendation_repo=AsyncMock(),
        queue_repo=queue_repo,
        study_plan_repo=study_plan_repo,
        execution_repo=execution_repo,
        execution_tracker=AsyncMock(),
        forecast_service=forecast_service,
        outbox=outbox,
    )

    from prepos.domain.study_plan import plan_generator_v1

    original = plan_generator_v1.generate_study_plan_v1
    plan_generator_v1.generate_study_plan_v1 = lambda inputs: plan  # type: ignore[assignment]
    try:
        await service.rebuild_study_plan(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            correlation_id="corr",
            causation_id="cause",
            current_time=now,
        )
    finally:
        plan_generator_v1.generate_study_plan_v1 = original

    outbox.enqueue_study_plan_updated.assert_awaited_once()
    event = outbox.enqueue_study_plan_updated.await_args.args[0]
    assert isinstance(event, StudyPlanUpdated)
    assert event.daily_item_count == 1
    assert event.weekly_item_count == 1
    assert event.total_estimated_gain == Decimal("12.00")
