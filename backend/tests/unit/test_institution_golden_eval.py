from __future__ import annotations

from datetime import date

from prepos.application.institution.institution_insight_engine import generate_institution_insights
from prepos.application.institution.institution_models import CohortSnapshotInput, InstitutionDataInput
from prepos.application.institution.institution_recommendation_engine import (
    generate_institution_recommendations,
)
from prepos.application.institution.institution_trend_analyzer import analyze_institution_trends


def _synthetic_institution(index: int) -> InstitutionDataInput:
    cohort_count = 2 + (index % 4)
    cohorts = tuple(
        CohortSnapshotInput(
            cohort_id=f"cohort_{index}_{cohort_idx}",
            exam_id="upsc_cse" if cohort_idx % 2 == 0 else "upsc_gs2",
            student_count=80 + cohort_idx * 10,
            avg_readiness=40.0 + (index % 30) + cohort_idx,
            avg_forecast=45.0 + (index % 25) + cohort_idx,
            avg_effectiveness=50.0 + (index % 20),
            risk_count=5 + (index % 15),
            segment_counts={
                "at_risk": 5 + (index % 10),
                "critical_risk": 2 + (index % 5),
                "on_track": 50 + (index % 20),
            },
            top_risks=(f"concept_{(index + cohort_idx) % 8}",),
            cohort_health_score=50.0 + (index % 25),
            current_affairs_preparedness=42.0 + (index % 20),
            pyq_preparedness=55.0 + (index % 15),
            snapshot_date=date.today(),
        )
        for cohort_idx in range(cohort_count)
    )
    concept_counts: dict[str, int] = {}
    for cohort in cohorts:
        for concept in cohort.top_risks:
            concept_counts[concept] = concept_counts.get(concept, 0) + 1

    total_at_risk = sum(
        cohort.segment_counts.get("at_risk", 0) + cohort.segment_counts.get("critical_risk", 0)
        for cohort in cohorts
    )
    current_readiness = sum(cohort.avg_readiness for cohort in cohorts) / len(cohorts)
    current_forecast = sum(cohort.avg_forecast for cohort in cohorts) / len(cohorts)
    current_ca = sum(cohort.current_affairs_preparedness for cohort in cohorts) / len(cohorts)
    pyq_signal = sum(cohort.pyq_preparedness for cohort in cohorts) / len(cohorts)

    return InstitutionDataInput(
        cohorts=cohorts,
        mentors=(),
        concept_cohort_counts=concept_counts,
        previous_readiness_avg=current_readiness + 3.0,
        current_readiness_avg=current_readiness,
        previous_forecast_avg=current_forecast + 2.0,
        current_forecast_avg=current_forecast,
        previous_ca_avg=current_ca + 4.0,
        current_ca_avg=current_ca,
        intervention_roi=40.0 + (index % 30),
        pyq_gain_signal=pyq_signal,
        total_at_risk=total_at_risk,
    )


def test_golden_institution_outputs_for_one_hundred_institutions() -> None:
    institutions = [_synthetic_institution(index) for index in range(100)]
    for data in institutions:
        first_insights = generate_institution_insights(data)
        second_insights = generate_institution_insights(data)
        assert first_insights == second_insights

        first_recommendations = generate_institution_recommendations(
            data=data,
            insights=first_insights,
        )
        second_recommendations = generate_institution_recommendations(
            data=data,
            insights=second_insights,
        )
        assert first_recommendations == second_recommendations
        if len(first_recommendations) >= 2:
            assert first_recommendations[0].priority_score >= first_recommendations[-1].priority_score

        first_trends = analyze_institution_trends(data=data)
        second_trends = analyze_institution_trends(data=data)
        assert first_trends == second_trends
