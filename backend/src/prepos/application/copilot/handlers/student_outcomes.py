from __future__ import annotations

from prepos.application.copilot.dto import CopilotQueryResponse, CopilotSourceResponse
from prepos.application.recommendations.outcomes.outcome_models import RecommendationOutcomeResponse
from prepos.application.recommendations.outcomes.outcome_service import RecommendationOutcomeService

STUDENT_OUTCOME_INTENTS: frozenset[str] = frozenset(
    {
        "recommendation_progress",
        "learning_progress",
        "best_improvements",
        "study_effectiveness",
        "progress_summary",
    }
)

STUDENT_OUTCOME_INTROS: dict[str, str] = {
    "recommendation_progress": "Your recommendation progress and measured outcomes:",
    "learning_progress": "Learning progress from completed recommendations:",
    "best_improvements": "Concepts where your study delivered the biggest readiness gains:",
    "study_effectiveness": "How effective your completed recommendations have been:",
    "progress_summary": "Summary of your recommendation-driven progress:",
}


def map_student_outcomes_to_copilot_response(
    *,
    intent: str,
    outcomes: list[RecommendationOutcomeResponse],
    intro: str | None = None,
) -> CopilotQueryResponse:
    resolved_intro = intro or STUDENT_OUTCOME_INTROS.get(intent, "Your recommendation outcomes:")
    lines = [resolved_intro, ""]
    if not outcomes:
        lines.append("Complete recommendations to unlock outcome tracking and effectiveness insights.")
    for index, item in enumerate(outcomes[:5], start=1):
        lines.append(
            f"{index}. {item.concept_name} — predicted +{item.predicted_gain:.1f}, "
            f"actual +{item.actual_gain:.1f}, effectiveness {item.effectiveness_score:.2f} ({item.status})."
        )
    avg_effectiveness = sum(item.effectiveness_score for item in outcomes[:5]) / len(outcomes[:5]) if outcomes else 0
    return CopilotQueryResponse(
        intent=intent,
        answer="\n".join(lines),
        confidence="high" if outcomes else "low",
        sources=[
            CopilotSourceResponse(label="Recommendation outcomes", reference="GET /recommendations/outcomes"),
            CopilotSourceResponse(label="Effectiveness metrics", reference="GET /recommendations/effectiveness"),
        ],
    )


async def build_student_outcome_response(
    *,
    intent: str,
    outcome_service: RecommendationOutcomeService,
    tenant_id,
    student_id,
    limit: int = 5,
) -> CopilotQueryResponse:
    outcome_list = await outcome_service.list_outcomes(
        tenant_id=tenant_id,
        student_id=student_id,
        limit=50,
    )
    outcomes = outcome_list.outcomes
    if intent == "best_improvements":
        outcomes = sorted(outcomes, key=lambda item: item.actual_gain, reverse=True)
    elif intent == "study_effectiveness":
        outcomes = sorted(outcomes, key=lambda item: item.effectiveness_score, reverse=True)
    elif intent in {"recommendation_progress", "learning_progress", "progress_summary"}:
        outcomes = sorted(outcomes, key=lambda item: item.created_at, reverse=True)
    return map_student_outcomes_to_copilot_response(intent=intent, outcomes=outcomes[:limit])
