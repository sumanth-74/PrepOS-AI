from __future__ import annotations

from datetime import date

from prepos.application.institution.institution_insight_engine import generate_institution_insights
from prepos.application.institution.institution_models import (
    CohortSnapshotInput,
    InstitutionDataInput,
    MentorEffectivenessInput,
)


def _cohort(
    *,
    cohort_id: str,
    exam_id: str = "upsc_cse",
    readiness: float = 55.0,
    forecast: float = 58.0,
    risk_count: int = 10,
    at_risk: int = 8,
    critical: int = 2,
    top_risks: tuple[str, ...] = ("federalism",),
) -> CohortSnapshotInput:
    return CohortSnapshotInput(
        cohort_id=cohort_id,
        exam_id=exam_id,
        student_count=100,
        avg_readiness=readiness,
        avg_forecast=forecast,
        avg_effectiveness=60.0,
        risk_count=risk_count,
        segment_counts={"at_risk": at_risk, "critical_risk": critical, "on_track": 70},
        top_risks=top_risks,
        cohort_health_score=62.0,
        current_affairs_preparedness=50.0,
        pyq_preparedness=65.0,
        snapshot_date=date.today(),
    )


def test_concept_weakness_insight_requires_multiple_cohorts() -> None:
    data = InstitutionDataInput(
        cohorts=(
            _cohort(cohort_id="a", top_risks=("federalism",)),
            _cohort(cohort_id="b", top_risks=("federalism",)),
            _cohort(cohort_id="c", top_risks=("federalism",)),
        ),
        mentors=(),
        concept_cohort_counts={"federalism": 3},
        previous_readiness_avg=None,
        current_readiness_avg=55.0,
        previous_forecast_avg=None,
        current_forecast_avg=58.0,
        previous_ca_avg=None,
        current_ca_avg=50.0,
        intervention_roi=55.0,
        pyq_gain_signal=65.0,
        total_at_risk=30,
    )
    insights = generate_institution_insights(data)
    assert any(item.insight_type == "concept_weakness" for item in insights)
    weakness = next(item for item in insights if item.insight_type == "concept_weakness")
    assert "3 cohorts" in weakness.title
    assert weakness.calculation
    assert weakness.evidence


def test_readiness_drop_insight_is_deterministic() -> None:
    data = InstitutionDataInput(
        cohorts=(_cohort(cohort_id="a"),),
        mentors=(),
        concept_cohort_counts={},
        previous_readiness_avg=65.0,
        current_readiness_avg=55.0,
        previous_forecast_avg=60.0,
        current_forecast_avg=58.0,
        previous_ca_avg=58.0,
        current_ca_avg=50.0,
        intervention_roi=55.0,
        pyq_gain_signal=65.0,
        total_at_risk=10,
    )
    first = generate_institution_insights(data)
    second = generate_institution_insights(data)
    assert first == second
    assert any(item.insight_type == "readiness_drop" for item in first)


def test_mentor_outperformance_insight() -> None:
    data = InstitutionDataInput(
        cohorts=(_cohort(cohort_id="a"),),
        mentors=(
            MentorEffectivenessInput(
                mentor_id="mentor-a",
                intervention_success_rate=0.85,
                student_count=20,
                average_gain=4.5,
            ),
            MentorEffectivenessInput(
                mentor_id="mentor-b",
                intervention_success_rate=0.55,
                student_count=15,
                average_gain=2.0,
            ),
        ),
        concept_cohort_counts={},
        previous_readiness_avg=None,
        current_readiness_avg=55.0,
        previous_forecast_avg=None,
        current_forecast_avg=58.0,
        previous_ca_avg=None,
        current_ca_avg=50.0,
        intervention_roi=55.0,
        pyq_gain_signal=65.0,
        total_at_risk=10,
    )
    insights = generate_institution_insights(data)
    assert any(item.insight_type == "mentor_outperformance" for item in insights)
