from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import AsyncClient

from prepos.application.learning_graph.dto import WeaknessItemResponse
from prepos.application.pyq.ports import PyqStatisticRecord
from prepos.application.recommendations.recommendation_engine import LearningRecommendationEngine, RecommendationContext
from prepos.application.twin.twin_dto import TwinDashboardResponse


@pytest.mark.asyncio
async def test_recommendation_openapi_paths_registered(client: AsyncClient) -> None:
    response = await client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v1/recommendations/student" in paths
    assert "/api/v1/recommendations/mentor" in paths
    assert "/api/v1/recommendations/explain/{concept_id}" in paths
    assert "/api/v1/admin/recommendations" in paths


@pytest.mark.asyncio
async def test_student_recommendations_requires_auth(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/recommendations/student",
        json={"exam_id": "upsc_cse", "limit": 5},
    )
    assert response.status_code == 401


def test_golden_recommendation_ranking_stable_for_fifty_students() -> None:
    engine = LearningRecommendationEngine()
    now = datetime.now(UTC)
    snapshots: list[list[tuple[str, float]]] = []

    for index in range(50):
        concept_a = f"upsc.topic_a_{index}"
        concept_b = f"upsc.topic_b_{index}"
        weakness_a = 50 + (index % 20)
        weakness_b = 40 + (index % 15)
        pyq_a = 5 + (index % 10)
        pyq_b = 2 + (index % 5)

        context = RecommendationContext(
            tenant_id=uuid4(),
            student_id=uuid4(),
            exam_id="upsc_cse",
            dashboard=TwinDashboardResponse(
                readiness_score=Decimal(str(40 + index)),
                gap_to_goal=Decimal(str(10 + (index % 8))),
            ),
            weaknesses=[
                WeaknessItemResponse(
                    concept_id=concept_a,
                    mastery_score=Decimal("30"),
                    importance_score=Decimal("70"),
                    weakness_score=Decimal(str(weakness_a)),
                ),
                WeaknessItemResponse(
                    concept_id=concept_b,
                    mastery_score=Decimal("35"),
                    importance_score=Decimal("60"),
                    weakness_score=Decimal(str(weakness_b)),
                ),
            ],
            goal=None,
            study_plan_items=[],
            twin_recommendations=[],
            pyq_statistics=[
                PyqStatisticRecord(
                    exam_id="upsc_cse",
                    concept_id=concept_a,
                    pyq_count=pyq_a,
                    first_appearance_year=2015,
                    last_appearance_year=2024,
                    frequency_score=float(40 + (index % 30)),
                    trend_score=1.0,
                    updated_at=now,
                ),
                PyqStatisticRecord(
                    exam_id="upsc_cse",
                    concept_id=concept_b,
                    pyq_count=pyq_b,
                    first_appearance_year=2016,
                    last_appearance_year=2022,
                    frequency_score=float(20 + (index % 20)),
                    trend_score=0.5,
                    updated_at=now,
                ),
            ],
        )

        first = engine.generate(context=context, limit=2)
        second = engine.generate(context=context, limit=2)
        assert first == second
        snapshots.append([(item.concept_id, item.impact_score) for item in first])

    assert len(snapshots) == 50
    assert all(snapshot[0][1] >= snapshot[1][1] for snapshot in snapshots if len(snapshot) == 2)
