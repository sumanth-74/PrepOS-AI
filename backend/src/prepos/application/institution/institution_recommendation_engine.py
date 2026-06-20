from __future__ import annotations

from prepos.application.institution.institution_models import (
    InstitutionDataInput,
    InstitutionInsightItem,
    InstitutionRecommendationItem,
)

INSTITUTION_RECOMMENDATION_ENGINE_V1 = "institution_recommendation_engine_v1"


def generate_institution_recommendations(
    *,
    data: InstitutionDataInput,
    insights: list[InstitutionInsightItem],
) -> list[InstitutionRecommendationItem]:
    recommendations: list[InstitutionRecommendationItem] = []
    insight_types = {item.insight_type for item in insights}

    if "concept_weakness" in insight_types:
        weak = [item for item in insights if item.insight_type == "concept_weakness"]
        affected_cohorts = [cohort.cohort_id for cohort in data.cohorts if cohort.risk_count > 0][:5]
        recommendations.append(
            InstitutionRecommendationItem(
                recommendation_type="review_weak_concepts",
                title="Review weak concepts across cohorts",
                expected_impact=8.0,
                affected_students=data.total_at_risk,
                affected_cohorts=affected_cohorts,
                explanation=(
                    f"{len(weak)} concept weakness signals detected institution-wide. "
                    "Schedule targeted revision sessions for the top weak concepts."
                ),
                priority_score=_priority(
                    severity_weight=85,
                    affected_students=data.total_at_risk,
                    expected_impact=8.0,
                ),
            )
        )
        recommendations.append(
            InstitutionRecommendationItem(
                recommendation_type="create_revision_campaign",
                title="Create revision campaign for weak concepts",
                expected_impact=10.0,
                affected_students=data.total_at_risk,
                affected_cohorts=affected_cohorts,
                explanation=(
                    "Launch a structured revision campaign covering concepts flagged in "
                    "multiple cohorts."
                ),
                priority_score=_priority(
                    severity_weight=80,
                    affected_students=data.total_at_risk,
                    expected_impact=10.0,
                ),
            )
        )

    if "current_affairs_drop" in insight_types:
        recommendations.append(
            InstitutionRecommendationItem(
                recommendation_type="increase_current_affairs_sessions",
                title="Increase current affairs sessions",
                expected_impact=6.0,
                affected_students=sum(cohort.student_count for cohort in data.cohorts),
                affected_cohorts=[cohort.cohort_id for cohort in data.cohorts],
                explanation=(
                    "Current affairs preparedness dropped month-over-month. "
                    "Add weekly CA review blocks to study plans."
                ),
                priority_score=_priority(
                    severity_weight=75,
                    affected_students=sum(cohort.student_count for cohort in data.cohorts),
                    expected_impact=6.0,
                ),
            )
        )

    if data.total_at_risk >= 10 or "cohort_risk_spike" in insight_types:
        recommendations.append(
            InstitutionRecommendationItem(
                recommendation_type="launch_intervention_program",
                title="Launch intervention program for at-risk students",
                expected_impact=12.0,
                affected_students=data.total_at_risk,
                affected_cohorts=[
                    cohort.cohort_id
                    for cohort in data.cohorts
                    if cohort.segment_counts.get("at_risk", 0)
                    + cohort.segment_counts.get("critical_risk", 0)
                    > 0
                ],
                explanation=(
                    f"{data.total_at_risk} students flagged at risk institution-wide. "
                    "Deploy mentor intervention sprints with tracked effectiveness."
                ),
                priority_score=_priority(
                    severity_weight=90,
                    affected_students=data.total_at_risk,
                    expected_impact=12.0,
                ),
            )
        )
        recommendations.append(
            InstitutionRecommendationItem(
                recommendation_type="assign_mentor_capacity",
                title="Assign additional mentor capacity",
                expected_impact=9.0,
                affected_students=data.total_at_risk,
                affected_cohorts=[cohort.cohort_id for cohort in data.cohorts if cohort.risk_count > 5],
                explanation=(
                    "High at-risk volume requires additional mentor bandwidth for "
                    "timely interventions."
                ),
                priority_score=_priority(
                    severity_weight=88,
                    affected_students=data.total_at_risk,
                    expected_impact=9.0,
                ),
            )
        )

    if "intervention_underperformance" in insight_types:
        recommendations.append(
            InstitutionRecommendationItem(
                recommendation_type="review_intervention_strategy",
                title="Review intervention strategy and ROI",
                expected_impact=7.0,
                affected_students=sum(cohort.student_count for cohort in data.cohorts),
                affected_cohorts=[cohort.cohort_id for cohort in data.cohorts],
                explanation=(
                    f"Intervention ROI at {data.intervention_roi:.1f}% is below the "
                    f"{45.0:.0f}% target. Audit intervention types and mentor assignments."
                ),
                priority_score=_priority(
                    severity_weight=70,
                    affected_students=sum(cohort.student_count for cohort in data.cohorts),
                    expected_impact=7.0,
                ),
            )
        )

    return sorted(recommendations, key=lambda item: item.priority_score, reverse=True)


def _priority(*, severity_weight: float, affected_students: int, expected_impact: float) -> float:
    student_factor = min(100.0, affected_students * 0.5)
    return round(severity_weight * 0.5 + student_factor * 0.3 + expected_impact * 2.0, 2)
