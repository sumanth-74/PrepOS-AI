from __future__ import annotations

from prepos.application.copilot.dto import CopilotQueryResponse, CopilotRecommendationResponse, CopilotSourceResponse
from prepos.application.recommendations.recommendation_models import ConceptRecommendation

STUDENT_RECOMMENDATION_INTENTS: frozenset[str] = frozenset(
    {
        "study_next",
        "highest_score_improvement",
        "weak_concepts_priority",
        "important_topics",
        "weekly_focus",
        "pyq_priority_topics",
        "current_affairs_priority",
    }
)

STUDENT_RECOMMENDATION_INTROS: dict[str, str] = {
    "study_next": "Based on your twin readiness, weaknesses, goals, and PYQ patterns, study these next:",
    "highest_score_improvement": "These concepts offer the largest estimated readiness improvement:",
    "weak_concepts_priority": "Your highest-priority weak concepts to address:",
    "important_topics": "High-impact topics for UPSC based on weakness, PYQ frequency, and forecast:",
    "weekly_focus": "Focus areas for this week based on your study plan and readiness forecast:",
    "pyq_priority_topics": "Weak areas with the strongest PYQ signal:",
    "current_affairs_priority": "Weak concepts linked to current affairs you should revise:",
}


def to_copilot_recommendations(items: list[ConceptRecommendation]) -> list[CopilotRecommendationResponse]:
    return [
        CopilotRecommendationResponse(
            concept_id=item.concept_id,
            concept_name=item.concept_name,
            impact_score=item.impact_score,
            reason_codes=item.reason_codes,
            reasons=item.reasons,
            estimated_readiness_gain=item.estimated_readiness_gain,
            confidence=item.confidence,
        )
        for item in items
    ]


def map_student_recommendations_to_copilot_response(
    *,
    intent: str,
    recommendations: list[ConceptRecommendation],
    intro: str | None = None,
    memory_lines: list[str] | None = None,
) -> CopilotQueryResponse:
    resolved_intro = intro or STUDENT_RECOMMENDATION_INTROS.get(intent, "Personalized learning recommendations:")
    lines = [resolved_intro, ""]
    for index, item in enumerate(recommendations[:5], start=1):
        reason_text = "; ".join(item.reasons) if item.reasons else "High learning impact"
        lines.append(
            f"{index}. {item.concept_name} — impact {item.impact_score:.1f}/10, "
            f"estimated readiness gain +{item.estimated_readiness_gain:.1f}. "
            f"Why: {reason_text}."
        )
    if not recommendations:
        lines.append("Complete assessments and study activities to unlock personalized recommendations.")
    if memory_lines:
        lines.extend(["", "Coaching memory context:"])
        lines.extend(f"- {line}" for line in memory_lines[:5])

    mapped = to_copilot_recommendations(recommendations)
    return CopilotQueryResponse(
        intent=intent,
        answer="\n".join(lines),
        recommendations=mapped,
        confidence="high" if recommendations else "low",
        sources=[
            CopilotSourceResponse(label="Learning recommendations", reference="POST /recommendations/student"),
            CopilotSourceResponse(label="Twin dashboard", reference="GET /twin/dashboard"),
            CopilotSourceResponse(label="Learning graph weaknesses", reference="GET /learning-graph/weaknesses"),
        ],
    )
