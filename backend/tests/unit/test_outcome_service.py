from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from prepos.application.recommendations.outcomes.outcome_service import RecommendationOutcomeService
from prepos.application.twin.twin_dto import TwinDashboardResponse


@pytest.mark.asyncio
async def test_evaluate_on_completion_creates_outcome() -> None:
    tenant_id = uuid4()
    student_id = uuid4()
    user_id = uuid4()
    event_id = uuid4()
    concept_id = "upsc.polity_federalism"

    outcome_repo = AsyncMock()
    outcome_repo.get_latest_shown_event.return_value = {
        "id": event_id,
        "user_id": user_id,
        "concept_id": concept_id,
        "estimated_gain": 3.0,
        "metadata_json": {
            "readiness_before": 55.0,
            "forecast_before": 60.0,
            "weakness_before": 80.0,
            "predicted_gain": 3.0,
            "exam_id": "upsc_cse",
        },
    }
    outcome_repo.outcome_exists_for_event.return_value = False
    outcome_repo.create_outcome.return_value = uuid4()

    twin_read = AsyncMock()
    twin_read.get_dashboard.return_value = TwinDashboardResponse(
        readiness_score=Decimal("59.1"),
        projected_readiness=Decimal("63.0"),
    )
    from prepos.application.learning_graph.dto import LearningGraphWeaknessesResponse, WeaknessItemResponse

    lg_read = AsyncMock()
    lg_read.get_weaknesses.return_value = LearningGraphWeaknessesResponse(
        student_id=student_id,
        weaknesses=[
            WeaknessItemResponse(
                concept_id=concept_id,
                mastery_score=Decimal("30"),
                importance_score=Decimal("80"),
                weakness_score=Decimal("70"),
            )
        ],
    )

    service = RecommendationOutcomeService(
        outcome_repository=outcome_repo,
        analytics_repository=AsyncMock(),
        twin_read_service=twin_read,
        learning_graph_read_service=lg_read,
    )

    outcome = await service.evaluate_on_completion(
        tenant_id=tenant_id,
        user_id=user_id,
        student_id=student_id,
        concept_id=concept_id,
        exam_id="upsc_cse",
        study_minutes=45,
    )

    assert outcome is not None
    assert outcome.actual_gain == pytest.approx(4.1)
    assert outcome.effectiveness_score == pytest.approx(1.37, abs=0.01)
    assert outcome.status == "successful"
    outcome_repo.create_outcome.assert_awaited_once()


@pytest.mark.asyncio
async def test_evaluate_on_completion_skips_duplicate_outcome() -> None:
    outcome_repo = AsyncMock()
    outcome_repo.get_latest_shown_event.return_value = {"id": uuid4(), "metadata_json": {}}
    outcome_repo.outcome_exists_for_event.return_value = True

    service = RecommendationOutcomeService(
        outcome_repository=outcome_repo,
        analytics_repository=None,
        twin_read_service=AsyncMock(),
        learning_graph_read_service=AsyncMock(),
    )

    outcome = await service.evaluate_on_completion(
        tenant_id=uuid4(),
        user_id=uuid4(),
        student_id=uuid4(),
        concept_id="upsc.polity_federalism",
        exam_id="upsc_cse",
    )
    assert outcome is None
    outcome_repo.create_outcome.assert_not_called()
