from __future__ import annotations

from uuid import UUID

import pytest

from prepos.application.cohort.cohort_intelligence_engine import (
    aggregate_cohort_metrics,
    build_segment_distribution,
    top_cohort_risk_concepts,
)
from prepos.application.cohort.cohort_models import StudentCohortInput
from prepos.application.cohort.cohort_risk_engine import build_risk_items, count_at_risk
from prepos.application.cohort.cohort_segmentation_engine import compute_risk_score, segment_student
from prepos.application.cohort.cohort_trend_service import compute_concept_trends, compute_macro_trends


def _student(
    index: int,
    *,
    readiness: float = 55.0,
    forecast_probability: float = 60.0,
    on_track: bool = True,
) -> StudentCohortInput:
    return StudentCohortInput(
        student_id=UUID(int=index + 1),
        exam_id="upsc_cse",
        readiness=readiness,
        forecast_probability=forecast_probability,
        projected_readiness=readiness + 5,
        on_track=on_track,
        goal_attainment=forecast_probability,
        planning_adherence=65.0,
        recommendation_effectiveness=60.0,
        intervention_effectiveness=55.0,
        intervention_count=1,
        readiness_delta=1.5,
        weekly_progress=2.0,
        consistency_score=50.0,
        pyq_preparedness=58.0,
        current_affairs_preparedness=62.0,
        negative_drivers=("polity_federalism",) if index % 3 == 0 else ("polity_parliament",),
        failed_intervention_count=1 if index % 11 == 0 else 0,
    )


def test_critical_risk_segment_rule() -> None:
    student = _student(1, readiness=35.0, forecast_probability=45.0, on_track=False)
    result = segment_student(student)
    assert result.segment_type == "critical_risk"


def test_risk_score_is_bounded() -> None:
    student = _student(2, readiness=30.0, forecast_probability=40.0, on_track=False)
    score, factors = compute_risk_score(student)
    assert 0 <= score <= 100
    assert factors


def test_segment_distribution_counts_all_students() -> None:
    students = [_student(i, readiness=50 + (i % 20), forecast_probability=55 + (i % 15)) for i in range(10)]
    distribution = build_segment_distribution(students)
    assert sum(distribution.values()) == len(students)


def test_cohort_metrics_health_score() -> None:
    students = [_student(i, readiness=70.0, forecast_probability=75.0) for i in range(5)]
    metrics = aggregate_cohort_metrics(students)
    assert metrics.cohort_health_score > 0
    assert metrics.average_readiness == pytest.approx(70.0)


def test_trend_engine_macro_directions() -> None:
    readiness_trend, forecast_trend, growth = compute_macro_trends(
        current_avg_readiness=65.0,
        current_avg_forecast=70.0,
        previous_avg_readiness=62.0,
        previous_avg_forecast=68.0,
        current_count=100,
        previous_count=95,
    )
    assert readiness_trend == "improving"
    assert forecast_trend == "improving"
    assert growth > 0


def test_risk_items_sorted_descending() -> None:
    students = [
        _student(1, readiness=35.0, forecast_probability=40.0, on_track=False),
        _student(2, readiness=75.0, forecast_probability=80.0, on_track=True),
    ]
    risks = build_risk_items(students)
    if len(risks) >= 2:
        assert risks[0]["risk_score"] >= risks[1]["risk_score"]
    assert count_at_risk(students) >= 1


def test_concept_trends_generated() -> None:
    students = [_student(i) for i in range(5)]
    trends = compute_concept_trends(
        students=students,
        previous_avg_readiness=50.0,
        current_avg_readiness=55.0,
    )
    assert trends
    assert top_cohort_risk_concepts(students)
