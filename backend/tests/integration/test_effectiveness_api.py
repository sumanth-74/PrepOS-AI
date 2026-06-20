from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import AsyncClient

from prepos.application.learning_graph.dto import WeaknessItemResponse
from prepos.application.recommendations.outcomes.effectiveness_calculator import (
    calculate_actual_gain,
    calculate_effectiveness_score,
)
from prepos.application.recommendations.outcomes.outcome_service import RecommendationOutcomeService
from prepos.application.recommendations.recommendation_engine import LearningRecommendationEngine, RecommendationContext
from prepos.application.twin.twin_dto import TwinDashboardResponse


@pytest.mark.asyncio
async def test_effectiveness_openapi_paths_registered(client: AsyncClient) -> None:
    response = await client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v1/recommendations/outcomes" in paths
    assert "/api/v1/recommendations/outcomes/{concept_id}" in paths
    assert "/api/v1/recommendations/effectiveness" in paths
    assert "/api/v1/admin/recommendation-effectiveness" in paths


def test_golden_outcome_effectiveness_for_one_hundred_students() -> None:
    engine = LearningRecommendationEngine()
    now = datetime.now(UTC)
    effectiveness_scores: list[float] = []

    for index in range(100):
        readiness_before = 40.0 + index * 0.3
        predicted_gain = round(1.5 + (index % 7) * 0.5, 2)
        readiness_after = readiness_before + predicted_gain * (0.8 + (index % 5) * 0.1)
        actual_gain = calculate_actual_gain(
            readiness_before=readiness_before,
            readiness_after=readiness_after,
        )
        effectiveness = calculate_effectiveness_score(
            actual_gain=actual_gain,
            predicted_gain=predicted_gain,
        )
        effectiveness_scores.append(effectiveness)

        concept_a = f"upsc.topic_a_{index}"
        context = RecommendationContext(
            tenant_id=uuid4(),
            student_id=uuid4(),
            exam_id="upsc_cse",
            dashboard=TwinDashboardResponse(
                readiness_score=Decimal(str(readiness_before)),
                gap_to_goal=Decimal("10"),
                projected_readiness=Decimal(str(readiness_before + 5)),
            ),
            weaknesses=[
                WeaknessItemResponse(
                    concept_id=concept_a,
                    mastery_score=Decimal("30"),
                    importance_score=Decimal("70"),
                    weakness_score=Decimal(str(50 + index % 20)),
                ),
            ],
            goal=None,
            study_plan_items=[],
            twin_recommendations=[],
            pyq_statistics=[],
        )
        first = engine.generate(context=context, limit=1)
        second = engine.generate(context=context, limit=1)
        assert first == second

    assert len(effectiveness_scores) == 100
    assert all(0.0 <= score <= 3.0 for score in effectiveness_scores)
