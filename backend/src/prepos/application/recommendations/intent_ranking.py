from __future__ import annotations

from prepos.application.recommendations.recommendation_models import ConceptRecommendation

ALL_RECOMMENDATION_INTENTS: frozenset[str] = frozenset(
    {
        "study_next",
        "highest_score_improvement",
        "weak_concepts_priority",
        "important_topics",
        "weekly_focus",
        "pyq_priority_topics",
        "current_affairs_priority",
        "student_focus_areas",
        "highest_impact_intervention",
        "high_frequency_weak_concepts",
        "current_affairs_revision",
        "student_priority_plan",
    }
)


def apply_intent_ranking(intent: str, recommendations: list[ConceptRecommendation]) -> list[ConceptRecommendation]:
    if intent in {"highest_score_improvement", "highest_impact_intervention"}:
        return sorted(
            recommendations,
            key=lambda item: (item.estimated_readiness_gain, item.impact_score),
            reverse=True,
        )

    if intent in {"weak_concepts_priority", "student_focus_areas"}:
        filtered = [item for item in recommendations if "weakness" in item.reason_codes]
        return filtered or recommendations

    if intent in {"important_topics", "pyq_priority_topics", "high_frequency_weak_concepts"}:
        filtered = [item for item in recommendations if "high_pyq_frequency" in item.reason_codes]
        if filtered:
            return sorted(filtered, key=lambda item: item.impact_score, reverse=True)
        return sorted(
            recommendations,
            key=lambda item: ("high_pyq_frequency" in item.reason_codes, item.impact_score),
            reverse=True,
        )

    if intent in {"current_affairs_priority", "current_affairs_revision"}:
        filtered = [item for item in recommendations if "current_affairs_relevant" in item.reason_codes]
        return filtered or recommendations

    return recommendations
