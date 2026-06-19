from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from prepos.application.scoring.predicted_score_service import PredictedScoreService
from prepos.domain.scoring.events import PredictedScoreUpdated
from prepos.domain.scoring.predicted_score_v1 import PreparationRisk


@pytest.mark.asyncio
async def test_compute_predicted_score_from_readiness_snapshot() -> None:
    tenant_id = uuid4()
    student_id = uuid4()
    now = datetime(2026, 6, 18, tzinfo=UTC)

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
        return_value=AsyncMock(total_estimated_gain=Decimal("7.50"))
    )
    recommendation_repo = AsyncMock()

    service = PredictedScoreService(
        read_service=read_service,
        recommendation_repo=recommendation_repo,
        study_plan_repo=study_plan_repo,
        outbox=AsyncMock(),
    )
    snapshot = await service.compute_predicted_score(
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id="neet",
        current_time=now,
    )

    assert snapshot is not None
    assert snapshot.expected_score == Decimal("64.25")
    assert snapshot.low_score == Decimal("58.25")
    assert snapshot.high_score == Decimal("70.25")
    assert snapshot.risk_level == PreparationRisk.MEDIUM
    assert snapshot.current_state == Decimal("64.25")
    assert snapshot.complete_recommendations == Decimal("71.75")
    assert snapshot.no_study == Decimal("57.50")


@pytest.mark.asyncio
async def test_publish_predicted_score_updated_emits_event() -> None:
    tenant_id = uuid4()
    student_id = uuid4()
    now = datetime(2026, 6, 18, tzinfo=UTC)

    read_service = AsyncMock()
    read_service.get_readiness_snapshot = AsyncMock(
        return_value=AsyncMock(
            average_mastery=Decimal("90"),
            average_retention=Decimal("85"),
            average_confidence=Decimal("80"),
            rated_node_count=200,
            total_node_count=400,
        )
    )
    study_plan_repo = AsyncMock()
    study_plan_repo.get_study_plan_summary = AsyncMock(return_value=None)
    recommendation_repo = AsyncMock()
    recommendation_repo.get_recommendation_summary = AsyncMock(
        return_value=AsyncMock(top_recommendations=())
    )
    outbox = AsyncMock()
    outbox.enqueue_predicted_score_updated = AsyncMock()

    service = PredictedScoreService(
        read_service=read_service,
        recommendation_repo=recommendation_repo,
        study_plan_repo=study_plan_repo,
        outbox=outbox,
    )
    await service.publish_predicted_score_updated(
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id="neet",
        correlation_id="corr",
        causation_id="cause",
        current_time=now,
    )

    outbox.enqueue_predicted_score_updated.assert_awaited_once()
    event = outbox.enqueue_predicted_score_updated.await_args.args[0]
    assert isinstance(event, PredictedScoreUpdated)
    assert event.exam_id == "neet"
    assert event.risk_level == PreparationRisk.LOW
