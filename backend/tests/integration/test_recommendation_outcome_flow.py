from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from prepos.application.recommendations.outcomes.outcome_service import RecommendationOutcomeService
from prepos.application.twin.twin_dto import TwinDashboardResponse


@pytest.mark.asyncio
async def test_outcome_flow_on_readiness_change_after_seven_days() -> None:
    tenant_id = uuid4()
    student_id = uuid4()
    concept_id = "upsc.polity_federalism"
    event_id = uuid4()

    outcome_repo = AsyncMock()
    shown_event = {
        "id": event_id,
        "user_id": uuid4(),
        "concept_id": concept_id,
        "estimated_gain": 2.0,
        "metadata_json": {
            "readiness_before": 50.0,
            "forecast_before": 55.0,
            "weakness_before": 75.0,
            "predicted_gain": 2.0,
            "exam_id": "upsc_cse",
        },
        "created_at": datetime.now(UTC) - timedelta(days=8),
    }
    outcome_repo.get_pending_shown_events.return_value = [shown_event]
    outcome_repo.get_latest_shown_event.return_value = shown_event
    outcome_repo.outcome_exists_for_event.return_value = False
    outcome_repo.create_outcome.return_value = uuid4()

    twin_read = AsyncMock()
    twin_read.get_dashboard.return_value = TwinDashboardResponse(
        readiness_score=Decimal("53.5"),
        projected_readiness=Decimal("58.0"),
    )
    from prepos.application.learning_graph.dto import LearningGraphWeaknessesResponse, WeaknessItemResponse

    lg_read = AsyncMock()
    lg_read.get_weaknesses.return_value = LearningGraphWeaknessesResponse(
        student_id=student_id,
        weaknesses=[
            WeaknessItemResponse(
                concept_id=concept_id,
                mastery_score=Decimal("35"),
                importance_score=Decimal("70"),
                weakness_score=Decimal("65"),
            )
        ],
    )

    service = RecommendationOutcomeService(
        outcome_repository=outcome_repo,
        analytics_repository=None,
        twin_read_service=twin_read,
        learning_graph_read_service=lg_read,
    )

    outcomes = await service.evaluate_pending(
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id="upsc_cse",
    )

    assert len(outcomes) == 1
    assert outcomes[0].actual_gain == pytest.approx(3.5)
    assert outcomes[0].effectiveness_score == pytest.approx(1.75)
