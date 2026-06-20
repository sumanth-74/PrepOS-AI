from __future__ import annotations

from datetime import date

from prepos.application.institution.institution_insight_engine import generate_institution_insights
from prepos.application.institution.institution_models import CohortSnapshotInput, InstitutionDataInput
from prepos.application.institution.institution_recommendation_engine import (
    generate_institution_recommendations,
)


def _base_data() -> InstitutionDataInput:
    return InstitutionDataInput(
        cohorts=(
            CohortSnapshotInput(
                cohort_id="upsc_cse_cohort",
                exam_id="upsc_cse",
                student_count=120,
                avg_readiness=52.0,
                avg_forecast=50.0,
                avg_effectiveness=48.0,
                risk_count=35,
                segment_counts={"at_risk": 20, "critical_risk": 15, "on_track": 70},
                top_risks=("federalism", "parliament"),
                cohort_health_score=50.0,
                current_affairs_preparedness=45.0,
                pyq_preparedness=55.0,
                snapshot_date=date.today(),
            ),
        ),
        mentors=(),
        concept_cohort_counts={"federalism": 2, "parliament": 2},
        previous_readiness_avg=62.0,
        current_readiness_avg=52.0,
        previous_forecast_avg=58.0,
        current_forecast_avg=50.0,
        previous_ca_avg=55.0,
        current_ca_avg=45.0,
        intervention_roi=40.0,
        pyq_gain_signal=65.0,
        total_at_risk=35,
    )


def test_recommendations_include_intervention_program_for_at_risk_volume() -> None:
    data = _base_data()
    insights = generate_institution_insights(data)
    recommendations = generate_institution_recommendations(data=data, insights=insights)
    types = {item.recommendation_type for item in recommendations}
    assert "launch_intervention_program" in types
    assert "review_intervention_strategy" in types
    assert recommendations[0].priority_score >= recommendations[-1].priority_score


def test_recommendation_ranking_is_stable() -> None:
    data = _base_data()
    insights = generate_institution_insights(data)
    first = generate_institution_recommendations(data=data, insights=insights)
    second = generate_institution_recommendations(data=data, insights=insights)
    assert first == second
