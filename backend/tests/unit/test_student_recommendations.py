from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from prepos.application.copilot.handlers.student_recommendations import (
    STUDENT_RECOMMENDATION_INTENTS,
    map_student_recommendations_to_copilot_response,
)
from prepos.application.learning_graph.dto import LearningGraphWeaknessesResponse, WeaknessItemResponse
from prepos.application.recommendations.recommendation_models import ConceptRecommendation
from prepos.application.recommendations.recommendation_service import LearningRecommendationService
from prepos.application.pyq.ports import PyqStatisticRecord
from prepos.application.study_plan.dto import StudyPlanResponse
from prepos.application.twin.twin_dto import TwinDashboardResponse


def _sample_recommendation() -> ConceptRecommendation:
    return ConceptRecommendation(
        concept_id="upsc.polity_federalism",
        concept_name="Federalism",
        impact_score=8.4,
        reason_codes=["weakness", "high_pyq_frequency"],
        reasons=["Weakness score high", "Appeared in 14 PYQs"],
        estimated_readiness_gain=3.2,
        confidence="high",
    )


def test_student_recommendation_intents_cover_sprint_set() -> None:
    expected = {
        "study_next",
        "highest_score_improvement",
        "weak_concepts_priority",
        "important_topics",
        "weekly_focus",
        "pyq_priority_topics",
        "current_affairs_priority",
    }
    assert expected.issubset(STUDENT_RECOMMENDATION_INTENTS)


def test_map_student_recommendations_includes_why() -> None:
    response = map_student_recommendations_to_copilot_response(
        intent="study_next",
        recommendations=[_sample_recommendation()],
    )
    assert response.intent == "study_next"
    assert "Federalism" in response.answer
    assert "Why:" in response.answer
    assert len(response.recommendations) == 1
    assert response.recommendations[0].impact_score == 8.4


@pytest.mark.asyncio
async def test_get_recommendations_for_intent_applies_ranking() -> None:
    tenant_id = uuid4()
    student_id = uuid4()
    now = datetime.now(UTC)

    twin_read = AsyncMock()
    twin_read.get_dashboard.return_value = TwinDashboardResponse(
        readiness_score=Decimal("50"),
        gap_to_goal=Decimal("15"),
    )
    lg_read = AsyncMock()
    lg_read.get_weaknesses.return_value = LearningGraphWeaknessesResponse(
        student_id=student_id,
        weaknesses=[
            WeaknessItemResponse(
                concept_id="upsc.polity_federalism",
                mastery_score=Decimal("30"),
                importance_score=Decimal("80"),
                weakness_score=Decimal("85"),
            ),
            WeaknessItemResponse(
                concept_id="upsc.history_ancient",
                mastery_score=Decimal("45"),
                importance_score=Decimal("40"),
                weakness_score=Decimal("50"),
            ),
        ],
    )
    goal_service = AsyncMock()
    goal_service.get_goal.return_value = None
    study_plan = AsyncMock()
    study_plan.get_study_plan.return_value = StudyPlanResponse(
        daily_plan=[],
        weekly_plan=[],
    )
    twin_recs = AsyncMock()
    twin_recs.list_recommendations.return_value = []
    pyq_repo = AsyncMock()
    pyq_repo.list_statistics.return_value = [
        PyqStatisticRecord(
            exam_id="upsc_cse",
            concept_id="upsc.polity_federalism",
            pyq_count=14,
            first_appearance_year=2015,
            last_appearance_year=2024,
            frequency_score=75.0,
            trend_score=1.0,
            updated_at=now,
        )
    ]

    service = LearningRecommendationService(
        twin_read_service=twin_read,
        learning_graph_read_service=lg_read,
        goal_service=goal_service,
        study_plan_service=study_plan,
        twin_recommendation_service=twin_recs,
        pyq_repository=pyq_repo,
        analytics_repository=None,
    )

    recommendations = await service.get_recommendations_for_intent(
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id="upsc_cse",
        user_id=uuid4(),
        intent="pyq_priority_topics",
        limit=3,
    )
    assert recommendations
    assert recommendations[0].concept_id == "upsc.polity_federalism"
