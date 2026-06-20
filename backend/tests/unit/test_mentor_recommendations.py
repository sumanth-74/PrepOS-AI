from __future__ import annotations

import pytest

from prepos.application.copilot.handlers.mentor_recommendations import (
    MENTOR_RECOMMENDATION_INTENTS,
    map_mentor_recommendations_to_copilot_response,
)
from prepos.application.recommendations.recommendation_models import ConceptRecommendation


def test_mentor_recommendation_intents_cover_sprint_set() -> None:
    expected = {
        "student_focus_areas",
        "highest_impact_intervention",
        "high_frequency_weak_concepts",
        "current_affairs_revision",
        "student_priority_plan",
    }
    assert expected.issubset(MENTOR_RECOMMENDATION_INTENTS)


def test_map_mentor_recommendations_sets_student_context() -> None:
    response = map_mentor_recommendations_to_copilot_response(
        intent="student_focus_areas",
        recommendations=[
            ConceptRecommendation(
                concept_id="upsc.polity_federalism",
                concept_name="Federalism",
                impact_score=8.7,
                reason_codes=["weakness"],
                reasons=["Weakness score high"],
                estimated_readiness_gain=3.2,
                confidence="high",
            )
        ],
    )
    assert response.student_context_used is True
    assert "Federalism" in response.answer
    assert any(source.reference == "POST /recommendations/mentor" for source in response.sources)
