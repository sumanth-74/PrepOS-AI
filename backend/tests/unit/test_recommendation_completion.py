from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from prepos.application.recommendations.outcomes.effectiveness_calculator import (
    calculate_actual_gain,
    calculate_effectiveness_score,
    outcome_status,
)
from prepos.application.recommendations.outcomes.outcome_service import RecommendationOutcomeService


def test_completion_effectiveness_pipeline_is_deterministic() -> None:
    predicted_gain = 3.0
    readiness_before = 55.0
    readiness_after = 59.1
    actual_gain = calculate_actual_gain(
        readiness_before=readiness_before,
        readiness_after=readiness_after,
    )
    effectiveness = calculate_effectiveness_score(
        actual_gain=actual_gain,
        predicted_gain=predicted_gain,
    )
    status = outcome_status(effectiveness_score=effectiveness, actual_gain=actual_gain)

    assert actual_gain == 4.1
    assert effectiveness == pytest.approx(1.37, abs=0.01)
    assert status == "successful"


@pytest.mark.asyncio
async def test_completion_endpoint_triggers_outcome_evaluation() -> None:
    event_id = uuid4()
    outcome_id = uuid4()
    outcome_repo = AsyncMock()
    outcome_repo.get_latest_shown_event.return_value = {
        "id": event_id,
        "user_id": uuid4(),
        "concept_id": "upsc.polity_federalism",
        "estimated_gain": 3.0,
        "metadata_json": {
            "readiness_before": 55.0,
            "forecast_before": 60.0,
            "weakness_before": 80.0,
            "predicted_gain": 3.0,
        },
    }
    outcome_repo.outcome_exists_for_event.return_value = False
    outcome_repo.create_outcome.return_value = outcome_id
    outcome_repo.get_pending_shown_events.return_value = []

    twin_read = AsyncMock()
    twin_read.get_dashboard.return_value = AsyncMock(
        readiness_score=Decimal("59.1"),
        projected_readiness=Decimal("63.0"),
    )
    lg_read = AsyncMock()
    weakness = AsyncMock(concept_id="upsc.polity_federalism", weakness_score=Decimal("70"))
    lg_read.get_weaknesses.return_value = AsyncMock(weaknesses=[weakness])

    service = RecommendationOutcomeService(
        outcome_repository=outcome_repo,
        analytics_repository=AsyncMock(),
        twin_read_service=twin_read,
        learning_graph_read_service=lg_read,
    )

    outcome = await service.evaluate_on_completion(
        tenant_id=uuid4(),
        user_id=uuid4(),
        student_id=uuid4(),
        concept_id="upsc.polity_federalism",
        exam_id="upsc_cse",
        study_minutes=30,
    )

    assert outcome is not None
    assert outcome.predicted_gain == 3.0
    assert outcome.actual_gain == 4.1
