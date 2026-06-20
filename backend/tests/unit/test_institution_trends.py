from __future__ import annotations

from datetime import date

from prepos.application.institution.institution_models import (
    CohortSnapshotInput,
    InstitutionDataInput,
    MentorEffectivenessInput,
)
from prepos.application.institution.institution_trend_analyzer import analyze_institution_trends


def test_trend_analyzer_returns_readiness_and_forecast_directions() -> None:
    data = InstitutionDataInput(
        cohorts=(
            CohortSnapshotInput(
                cohort_id="upsc_cse_cohort",
                exam_id="upsc_cse",
                student_count=100,
                avg_readiness=55.0,
                avg_forecast=52.0,
                avg_effectiveness=50.0,
                risk_count=10,
                segment_counts={"at_risk": 8, "on_track": 70},
                top_risks=("federalism",),
                cohort_health_score=58.0,
                current_affairs_preparedness=50.0,
                pyq_preparedness=60.0,
                snapshot_date=date.today(),
            ),
        ),
        mentors=(
            MentorEffectivenessInput(
                mentor_id="mentor-1",
                intervention_success_rate=0.7,
                student_count=10,
                average_gain=3.5,
            ),
        ),
        concept_cohort_counts={"federalism": 1},
        previous_readiness_avg=62.0,
        current_readiness_avg=55.0,
        previous_forecast_avg=58.0,
        current_forecast_avg=52.0,
        previous_ca_avg=55.0,
        current_ca_avg=50.0,
        intervention_roi=48.0,
        pyq_gain_signal=60.0,
        total_at_risk=8,
    )
    trends, readiness_trend, forecast_trend = analyze_institution_trends(data=data, period="monthly")
    assert readiness_trend == "down"
    assert forecast_trend == "down"
    assert any(item.trend_type == "readiness" for item in trends)
    assert any(item.trend_type == "mentor_effectiveness" for item in trends)


def test_trend_calculations_are_deterministic() -> None:
    data = InstitutionDataInput(
        cohorts=(),
        mentors=(),
        concept_cohort_counts={},
        previous_readiness_avg=60.0,
        current_readiness_avg=60.0,
        previous_forecast_avg=55.0,
        current_forecast_avg=55.0,
        previous_ca_avg=50.0,
        current_ca_avg=50.0,
        intervention_roi=50.0,
        pyq_gain_signal=55.0,
        total_at_risk=0,
    )
    first = analyze_institution_trends(data=data)
    second = analyze_institution_trends(data=data)
    assert first == second
