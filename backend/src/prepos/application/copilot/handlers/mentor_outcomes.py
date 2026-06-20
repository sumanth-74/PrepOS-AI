from __future__ import annotations

from prepos.application.copilot.dto import CopilotQueryResponse, CopilotSourceResponse
from prepos.application.copilot.handlers.student_outcomes import map_student_outcomes_to_copilot_response
from prepos.application.recommendations.outcomes.outcome_analytics import OutcomeAnalyticsService
from prepos.application.recommendations.outcomes.outcome_service import RecommendationOutcomeService
from prepos.application.recommendations.recommendation_engine import format_concept_name

MENTOR_OUTCOME_INTENTS: frozenset[str] = frozenset(
    {
        "effective_interventions",
        "failed_interventions",
        "student_progress_summary",
        "improvement_drivers",
        "stagnant_concepts",
    }
)

MENTOR_OUTCOME_INTROS: dict[str, str] = {
    "effective_interventions": "Interventions that improved this student's readiness:",
    "failed_interventions": "Recommendations that underperformed for this student:",
    "student_progress_summary": "Student progress summary from recommendation outcomes:",
    "improvement_drivers": "Concepts that drove the largest readiness improvements:",
    "stagnant_concepts": "Concepts that remain weak despite recommendations:",
}


async def build_mentor_outcome_response(
    *,
    intent: str,
    outcome_service: RecommendationOutcomeService,
    analytics_service: OutcomeAnalyticsService,
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

    if intent == "effective_interventions":
        outcomes = [item for item in outcomes if item.status == "successful"]
        outcomes.sort(key=lambda item: item.effectiveness_score, reverse=True)
    elif intent == "failed_interventions":
        outcomes = [item for item in outcomes if item.status == "failed"]
        outcomes.sort(key=lambda item: item.effectiveness_score)
    elif intent == "improvement_drivers":
        outcomes.sort(key=lambda item: item.actual_gain, reverse=True)
    elif intent == "stagnant_concepts":
        outcomes = [item for item in outcomes if item.status != "successful"]
        outcomes.sort(key=lambda item: item.weakness_after or 0, reverse=True)

    response = map_student_outcomes_to_copilot_response(
        intent=intent,
        outcomes=outcomes[:limit],
        intro=MENTOR_OUTCOME_INTROS.get(intent),
    )
    return CopilotQueryResponse(
        intent=response.intent,
        answer=response.answer,
        confidence=response.confidence,
        sources=[
            *response.sources,
            CopilotSourceResponse(label="Mentor outcomes", reference="GET /recommendations/outcomes"),
        ],
        student_context_used=True,
    )
