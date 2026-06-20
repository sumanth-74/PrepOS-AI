from __future__ import annotations

from dataclasses import replace
from uuid import UUID

from prepos.application.cohort.cohort_intelligence_engine import aggregate_cohort_metrics, build_segment_distribution
from prepos.application.cohort.cohort_models import StudentCohortInput
from prepos.application.cohort.cohort_risk_engine import build_risk_items
from prepos.application.cohort.cohort_segmentation_engine import segment_student


def _synthetic_student(index: int) -> StudentCohortInput:
    readiness = 35.0 + (index % 50)
    forecast = 40.0 + (index % 45)
    return StudentCohortInput(
        student_id=UUID(int=index),
        exam_id="upsc_cse",
        readiness=readiness,
        forecast_probability=forecast,
        projected_readiness=readiness + 3.0,
        on_track=forecast >= 60 and readiness >= 55,
        goal_attainment=forecast,
        planning_adherence=40.0 + (index % 40),
        recommendation_effectiveness=45.0 + (index % 35),
        intervention_effectiveness=40.0 + (index % 50),
        intervention_count=index % 4,
        readiness_delta=-2.0 + (index % 7),
        weekly_progress=0.5 + (index % 5) * 0.4,
        consistency_score=35.0 + (index % 40),
        pyq_preparedness=40.0 + (index % 30),
        current_affairs_preparedness=42.0 + (index % 28),
        negative_drivers=(f"concept_{index % 12}",),
        failed_intervention_count=1 if index % 13 == 0 else 0,
    )


def test_golden_cohort_segmentation_for_one_thousand_students() -> None:
    students = [_synthetic_student(index) for index in range(1000)]
    first_distribution = build_segment_distribution(students)
    second_distribution = build_segment_distribution(students)
    assert first_distribution == second_distribution
    assert sum(first_distribution.values()) == 1000

    first_metrics = aggregate_cohort_metrics(students)
    second_metrics = aggregate_cohort_metrics(students)
    assert first_metrics == second_metrics

    first_risks = build_risk_items(students, limit=50)
    second_risks = build_risk_items(students, limit=50)
    assert first_risks == second_risks
    if len(first_risks) >= 2:
        assert first_risks[0]["risk_score"] >= first_risks[-1]["risk_score"]

    low = _synthetic_student(0)
    high = replace(
        low,
        readiness=low.readiness + 20,
        forecast_probability=low.forecast_probability + 20,
        on_track=True,
        failed_intervention_count=0,
    )
    assert segment_student(high).risk_score <= segment_student(low).risk_score
