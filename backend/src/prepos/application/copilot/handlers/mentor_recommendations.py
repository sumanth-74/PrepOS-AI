from __future__ import annotations

from prepos.application.copilot.dto import CopilotQueryResponse, CopilotSourceResponse
from prepos.application.copilot.handlers.student_recommendations import (
    map_student_recommendations_to_copilot_response,
)
from prepos.application.recommendations.recommendation_models import ConceptRecommendation

MENTOR_RECOMMENDATION_INTENTS: frozenset[str] = frozenset(
    {
        "student_focus_areas",
        "highest_impact_intervention",
        "high_frequency_weak_concepts",
        "current_affairs_revision",
        "student_priority_plan",
    }
)

MENTOR_RECOMMENDATION_INTROS: dict[str, str] = {
    "student_focus_areas": "This student should focus on these high-impact concepts:",
    "highest_impact_intervention": "Interventions with the fastest estimated readiness improvement:",
    "high_frequency_weak_concepts": "Weak concepts with high PYQ frequency for this student:",
    "current_affairs_revision": "Current-affairs-linked weak concepts to revise with this student:",
    "student_priority_plan": "Priority plan for this student this week:",
}


def map_mentor_recommendations_to_copilot_response(
    *,
    intent: str,
    recommendations: list[ConceptRecommendation],
    intro: str | None = None,
) -> CopilotQueryResponse:
    resolved_intro = intro or MENTOR_RECOMMENDATION_INTROS.get(intent, "Personalized mentor recommendations:")
    response = map_student_recommendations_to_copilot_response(
        intent=intent,
        recommendations=recommendations,
        intro=resolved_intro,
    )
    return CopilotQueryResponse(
        intent=response.intent,
        answer=response.answer,
        recommendations=response.recommendations,
        confidence=response.confidence,
        sources=[
            *response.sources,
            CopilotSourceResponse(label="Mentor recommendations", reference="POST /recommendations/mentor"),
        ],
        student_context_used=True,
    )
