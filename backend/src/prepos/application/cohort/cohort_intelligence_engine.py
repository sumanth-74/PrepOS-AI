from __future__ import annotations

from prepos.application.cohort.cohort_models import CohortMetrics, StudentCohortInput
from prepos.application.cohort.cohort_segmentation_engine import segment_student
from prepos.application.recommendations.recommendation_engine import format_concept_name


def aggregate_cohort_metrics(students: list[StudentCohortInput]) -> CohortMetrics:
    if not students:
        return CohortMetrics(
            average_readiness=0.0,
            average_forecast=0.0,
            average_gain=0.0,
            goal_attainment_rate=0.0,
            recommendation_effectiveness=0.0,
            planning_adherence=0.0,
            mentor_intervention_success=0.0,
            pyq_preparedness=0.0,
            current_affairs_preparedness=0.0,
            cohort_health_score=0.0,
        )

    count = len(students)
    avg_readiness = sum(item.readiness for item in students) / count
    avg_forecast = sum(item.forecast_probability for item in students) / count
    avg_gain = sum(item.readiness_delta for item in students) / count
    goal_attainment = sum(1 for item in students if item.goal_attainment >= 70) / count
    rec_effectiveness = sum(item.recommendation_effectiveness for item in students) / count
    adherence = sum(item.planning_adherence for item in students) / count
    intervention_success = sum(item.intervention_effectiveness for item in students) / count
    pyq = sum(item.pyq_preparedness for item in students) / count
    ca = sum(item.current_affairs_preparedness for item in students) / count

    health = (
        avg_readiness * 0.30
        + avg_forecast * 0.25
        + rec_effectiveness * 0.15
        + adherence * 0.15
        + intervention_success * 0.10
        + pyq * 0.05
    )

    return CohortMetrics(
        average_readiness=round(avg_readiness, 2),
        average_forecast=round(avg_forecast, 2),
        average_gain=round(avg_gain, 2),
        goal_attainment_rate=round(goal_attainment, 4),
        recommendation_effectiveness=round(rec_effectiveness, 2),
        planning_adherence=round(adherence, 2),
        mentor_intervention_success=round(intervention_success, 2),
        pyq_preparedness=round(pyq, 2),
        current_affairs_preparedness=round(ca, 2),
        cohort_health_score=round(min(100.0, health), 2),
    )


def build_segment_distribution(students: list[StudentCohortInput]) -> dict[str, int]:
    distribution: dict[str, int] = {}
    for item in students:
        result = segment_student(item)
        distribution[result.segment_type] = distribution.get(result.segment_type, 0) + 1
    return distribution


def top_cohort_risk_concepts(students: list[StudentCohortInput], limit: int = 5) -> list[str]:
    counts: dict[str, int] = {}
    for item in students:
        for concept in item.negative_drivers:
            counts[concept] = counts.get(concept, 0) + 1
    ranked = sorted(counts.items(), key=lambda pair: pair[1], reverse=True)
    return [format_concept_name(concept) for concept, _ in ranked[:limit]]
