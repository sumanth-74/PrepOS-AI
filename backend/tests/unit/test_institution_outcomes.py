from __future__ import annotations

from uuid import UUID, uuid4

from prepos.application.institution_outcomes.initiative_effectiveness import evaluate_initiative_effectiveness
from prepos.application.institution_outcomes.outcome_engine import measure_outcome
from prepos.application.institution_outcomes.outcome_models import InitiativeInput, MetricSnapshot
from prepos.application.institution_outcomes.roi_engine import calculate_roi_from_outcome


def _initiative(*, before: MetricSnapshot, after: MetricSnapshot) -> InitiativeInput:
    return InitiativeInput(
        initiative_id=uuid4(),
        initiative_type="revision_campaign",
        title="Revision campaign",
        status="active",
        affected_students=100,
        affected_cohorts=("upsc_cse_cohort",),
        before=before,
        after=after,
        expected_readiness_gain=6.0,
        expected_forecast_gain=4.0,
        expected_cohort_health_gain=5.0,
        expected_risk_reduction=8,
    )


def test_outcome_engine_measures_before_after_and_variance() -> None:
    initiative = _initiative(
        before=MetricSnapshot(readiness=50.0, forecast=48.0, cohort_health=52.0, risk_count=30),
        after=MetricSnapshot(readiness=58.0, forecast=54.0, cohort_health=57.0, risk_count=22),
    )
    outcome = measure_outcome(initiative=initiative)
    assert outcome.readiness_gain == 8.0
    assert outcome.forecast_gain == 6.0
    assert outcome.cohort_health_gain == 5.0
    assert outcome.risk_reduction == 8.0
    assert outcome.actual_gain > 0
    assert outcome.variance == round(outcome.actual_gain - outcome.expected_gain, 2)


def test_outcome_measurement_is_deterministic() -> None:
    initiative = _initiative(
        before=MetricSnapshot(readiness=55.0, forecast=50.0, cohort_health=54.0, risk_count=20),
        after=MetricSnapshot(readiness=60.0, forecast=53.0, cohort_health=58.0, risk_count=15),
    )
    assert measure_outcome(initiative=initiative) == measure_outcome(initiative=initiative)


def test_outcome_links_to_initiative_id() -> None:
    initiative = _initiative(
        before=MetricSnapshot(readiness=40.0, forecast=45.0, cohort_health=42.0, risk_count=40),
        after=MetricSnapshot(readiness=45.0, forecast=48.0, cohort_health=46.0, risk_count=35),
    )
    outcome = measure_outcome(initiative=initiative)
    assert outcome.initiative_id == initiative.initiative_id
    roi = calculate_roi_from_outcome(outcome=outcome, initiative_type=initiative.initiative_type, title=initiative.title)
    effectiveness = evaluate_initiative_effectiveness(initiative=initiative, outcome=outcome)
    assert 0 <= roi.roi_score <= 100
    assert effectiveness.status in {"succeeded", "failed", "partial"}
